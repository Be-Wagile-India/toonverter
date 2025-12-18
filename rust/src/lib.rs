use crate::error::ToonError;
use pyo3::prelude::*;
use pyo3::types::PyDict;

pub mod batch;
mod conversion;
pub mod encoder;
pub mod error;
pub mod ir;
pub mod lexer;
pub mod parser;
pub mod serde_toon;
pub mod tokens;

use batch::{batch_convert_directory, batch_convert_json, batch_convert_toon};
use conversion::{to_py_object, to_toon_value};
use encoder::encode_toon_root;
use lexer::ToonLexer;
use parser::ToonParser;

#[pyfunction]
#[pyo3(signature = (text, indent_size=None))]
fn decode_toon(py: Python, text: &str, indent_size: Option<usize>) -> PyResult<PyObject> {
    if text.trim().is_empty() {
        return Ok(PyDict::new_bound(py).into_py(py));
    }

    let indent = indent_size.unwrap_or(2);
    // Release GIL for lexing and parsing
    let parse_result = py.allow_threads(|| {
        let lexer = ToonLexer::new(text, indent);
        let mut parser = ToonParser::new(lexer);
        parser.parse_root()
    });

    match parse_result {
        Ok(tv) => to_py_object(py, &tv),
        Err(e) => Err(ToonError::from(e).into()),
    }
}

#[pyfunction]
#[pyo3(signature = (obj, indent_size=None, delimiter=None))]
fn encode_toon(
    py: Python,
    obj: Bound<'_, PyAny>,
    indent_size: Option<usize>,
    delimiter: Option<String>,
) -> PyResult<String> {
    // Need GIL for conversion from Python object to IR
    let ir = to_toon_value(&obj)?;

    let indent = indent_size.unwrap_or(2);
    let delim = delimiter.unwrap_or_else(|| ",".to_string());

    // Release GIL for encoding string generation
    py.allow_threads(move || Ok(encode_toon_root(&ir, indent, &delim)))
}

/// Batch convert JSON files.
#[pyfunction]
#[pyo3(signature = (paths, output_dir=None, indent_size=None, delimiter=None))]
fn convert_json_batch(
    paths: Vec<String>,
    output_dir: Option<String>,
    indent_size: Option<usize>,
    delimiter: Option<String>,
) -> PyResult<Vec<(String, String, bool)>> {
    let indent = indent_size.unwrap_or(2);
    let delim = delimiter.as_deref().unwrap_or(",");
    Ok(batch_convert_json(paths, output_dir, indent, delim))
}

/// Batch convert TOON files to JSON.
#[pyfunction]
#[pyo3(signature = (paths, output_dir=None, indent_size=None))]
fn convert_toon_batch(
    paths: Vec<String>,
    output_dir: Option<String>,
    indent_size: Option<usize>,
) -> PyResult<Vec<(String, String, bool)>> {
    let indent = indent_size.unwrap_or(2);
    Ok(batch_convert_toon(paths, output_dir, indent))
}

/// Batch convert JSON files in a directory.
#[pyfunction]
#[pyo3(signature = (dir_path, recursive=false, output_dir=None, indent_size=None, delimiter=None))]
fn convert_json_directory(
    dir_path: String,
    recursive: bool,
    output_dir: Option<String>,
    indent_size: Option<usize>,
    delimiter: Option<String>,
) -> PyResult<Vec<(String, String, bool)>> {
    let indent = indent_size.unwrap_or(2);
    let delim = delimiter.as_deref().unwrap_or(",");
    Ok(batch_convert_directory(
        dir_path, recursive, output_dir, indent, delim,
    ))
}

#[pymodule]
fn _toonverter_core(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(decode_toon, m)?)?;
    m.add_function(wrap_pyfunction!(encode_toon, m)?)?;
    m.add_function(wrap_pyfunction!(convert_json_batch, m)?)?;
    m.add_function(wrap_pyfunction!(convert_toon_batch, m)?)?;
    m.add_function(wrap_pyfunction!(convert_json_directory, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ir::ToonValue;
    use indexmap::IndexMap;

    #[test]
    fn test_internal_encode_decode_roundtrip() {
        let input_value = ToonValue::Dict(IndexMap::from([
            ("name".to_string(), ToonValue::String("Alice".to_string())),
            ("age".to_string(), ToonValue::Integer(30)),
        ]));

        let encoded = encode_toon_root(&input_value, 2, ",");
        assert_eq!(encoded, "name: Alice\nage: 30");
    }

    #[test]
    fn test_decode_toon_empty_input_internal() {
        let text = "";
        let lexer = ToonLexer::new(text, 2);
        let mut parser = ToonParser::new(lexer);
        let result = parser.parse_root().unwrap(); // This should yield an empty dict
        match result {
            ToonValue::Dict(d) => assert!(d.is_empty()),
            _ => panic!("Expected dict"),
        }
    }

    #[test]
    fn test_lib_pyfunctions() {
        pyo3::prepare_freethreaded_python();
        Python::with_gil(|py| {
            // Test decode_toon
            let res = decode_toon(py, "key: val", None);
            assert!(res.is_ok());
            let obj = res.unwrap();
            let dict = obj.downcast_bound::<PyDict>(py).unwrap();
            assert_eq!(
                dict.get_item("key")
                    .unwrap()
                    .unwrap()
                    .extract::<String>()
                    .unwrap(),
                "val"
            );

            // Test decode_toon empty
            let res_empty = decode_toon(py, "   ", None);
            assert!(res_empty.is_ok());
            let obj_empty = res_empty.unwrap();
            let dict_empty = obj_empty.downcast_bound::<PyDict>(py).unwrap();
            assert!(dict_empty.is_empty());

            // Test encode_toon
            let dict_to_encode = PyDict::new_bound(py);
            dict_to_encode.set_item("a", 1).unwrap();
            let encoded = encode_toon(py, dict_to_encode.as_any().clone(), None, None);
            assert!(encoded.is_ok());
            assert_eq!(encoded.unwrap(), "a: 1");

            // Test batch functions (smoke test mostly as logic is in batch.rs)
            // We just check they don't panic or fail immediately
            let batch_res = convert_json_batch(vec![], None, None, None);
            assert!(batch_res.is_ok());
            assert!(batch_res.unwrap().is_empty());

            let batch_toon_res = convert_toon_batch(vec![], None, None);
            assert!(batch_toon_res.is_ok());

            let batch_dir_res = convert_json_directory(".".to_string(), false, None, None, None);
            assert!(batch_dir_res.is_ok());
        })
    }

    #[test]
    fn test_lib_pyfunctions_errors() {
        pyo3::prepare_freethreaded_python();
        Python::with_gil(|py| {
            // decode_toon error
            let res = decode_toon(py, "key: [unclosed", None);
            assert!(res.is_err());

            // encode_toon error (set is not supported)
            let set = py.eval_bound("{1, 2}", None, None).unwrap();
            let res_enc = encode_toon(py, set, None, None);
            assert!(res_enc.is_err());
        });
    }
}
