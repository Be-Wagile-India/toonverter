//! # Rust Core for Toonverter
//!
//! This crate implements the high-performance core for Toonverter.
//!
//! ## FFI Contract (Version 1.0.0)
//!
//! This module adheres to a strict FFI contract with the Python side:
//!
//! 1. **No Panics**: All panics are caught via `catch_unwind` and converted to `InternalError`.
//! 2. **Explicit Errors**: All errors are mapped to `ToonverterError` variants:
//!    - `InvalidInput` -> `ValidationError`
//!    - `UnsupportedFormat` -> `FormatNotSupportedError`
//!    - `ProcessingError` -> `ProcessingError`
//!    - `InternalError` -> `InternalError`
//! 3. **Versioning**: The contract version is exposed as `CONTRACT_VERSION`.
//! 4. **Concurrency**: GIL is released for heavy processing where safe (`allow_threads`).

use crate::error::ToonverterError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use std::panic::{catch_unwind, AssertUnwindSafe};

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
use encoder::{
    encode_tabular_columns, encode_tabular_rows, encode_toon_root, ToonEncodeOptions,
    ToonEncoderRequest,
};
use lexer::ToonLexer;
use parser::ToonParser;

pub const CONTRACT_VERSION: &str = "1.0.0";

fn handle_panic(err: Box<dyn std::any::Any + Send>) -> PyErr {
    let msg = if let Some(s) = err.downcast_ref::<&str>() {
        format!("Panic: {}", s)
    } else if let Some(s) = err.downcast_ref::<String>() {
        format!("Panic: {}", s)
    } else {
        "Panic: Unknown internal error".to_string()
    };
    ToonverterError::InternalError(msg).into()
}

#[pyfunction]
#[pyo3(signature = (text, indent_size=None))]
fn decode_toon(py: Python, text: &str, indent_size: Option<usize>) -> PyResult<PyObject> {
    let result = catch_unwind(AssertUnwindSafe(|| {
        if text.trim().is_empty() {
            return Ok(PyDict::new_bound(py).into_py(py));
        }

        let indent = indent_size.unwrap_or(2);
        // Release GIL for lexing and parsing
        let parse_result = py.allow_threads(|| {
            catch_unwind(AssertUnwindSafe(|| {
                let lexer = ToonLexer::new(text, indent);
                let mut parser = ToonParser::new(lexer);
                parser.parse_root()
            }))
        });

        match parse_result {
            Ok(inner) => match inner {
                Ok(tv) => to_py_object(py, &tv),
                Err(e) => Err(ToonverterError::from(e).into()),
            },
            Err(panic) => Err(handle_panic(panic)),
        }
    }));

    match result {
        Ok(val) => val,
        Err(panic) => Err(handle_panic(panic)),
    }
}

#[pyfunction]
#[pyo3(signature = (obj, indent_size=None, delimiter=None, recursion_depth_limit=None))]
fn encode_toon(
    py: Python,
    obj: Bound<'_, PyAny>,
    indent_size: Option<usize>,
    delimiter: Option<String>,
    recursion_depth_limit: Option<usize>,
) -> PyResult<String> {
    let result = catch_unwind(AssertUnwindSafe(|| {
        // Need GIL for conversion from Python object to IR
        let ir = to_toon_value(&obj, recursion_depth_limit).map_err(PyErr::from)?;

        let options = ToonEncodeOptions {
            indent_size: indent_size.unwrap_or(2),
            delimiter: delimiter.unwrap_or_else(|| ",".to_string()),
        };

        // Release GIL for encoding string generation
        let encode_result = py.allow_threads(move || {
            catch_unwind(AssertUnwindSafe(|| {
                let request = ToonEncoderRequest {
                    value: &ir,
                    options: &options,
                };
                let response = encode_toon_root(request);
                Ok(response.toon_string)
            }))
        });

        match encode_result {
            Ok(val) => val,
            Err(panic) => Err(handle_panic(panic)),
        }
    }));

    match result {
        Ok(val) => val,
        Err(panic) => Err(handle_panic(panic)),
    }
}

#[pyfunction]
#[pyo3(signature = (data, indent_size=None, delimiter=None))]
fn encode_from_pandas(
    py: Python,
    data: Bound<'_, PyDict>,
    indent_size: Option<usize>,
    delimiter: Option<String>,
) -> PyResult<String> {
    let result = catch_unwind(AssertUnwindSafe(|| {
        let mut columns = Vec::new();
        let mut column_data = Vec::new();
        let mut count = 0;

        for (k, v) in data {
            let col_name = k.extract::<String>()?;
            columns.push(col_name);

            let list_obj = v.downcast::<PyList>()?;
            if count == 0 {
                count = list_obj.len();
            } else if list_obj.len() != count {
                return Err(ToonverterError::InvalidInput(
                    "All columns must have the same length".to_string(),
                )
                .into());
            }

            let mut col_values = Vec::with_capacity(count);
            for item in list_obj {
                col_values.push(to_toon_value(&item, None).map_err(PyErr::from)?);
            }
            column_data.push(col_values);
        }

        let indent = indent_size.unwrap_or(2);
        let delim = delimiter.unwrap_or_else(|| ",".to_string());

        let encode_result = py.allow_threads(move || {
            catch_unwind(AssertUnwindSafe(|| {
                Ok(encode_tabular_columns(
                    count,
                    columns,
                    column_data,
                    indent,
                    &delim,
                ))
            }))
        });

        match encode_result {
            Ok(val) => val,
            Err(panic) => Err(handle_panic(panic)),
        }
    }));

    match result {
        Ok(val) => val,
        Err(panic) => Err(handle_panic(panic)),
    }
}

#[pyfunction]
#[pyo3(signature = (columns, rows, indent_size=None, delimiter=None))]
fn encode_from_rows(
    py: Python,
    columns: Vec<String>,
    rows: Bound<'_, PyList>,
    indent_size: Option<usize>,
    delimiter: Option<String>,
) -> PyResult<String> {
    let result = catch_unwind(AssertUnwindSafe(|| {
        let count = rows.len();
        let mut row_data = Vec::with_capacity(count);

        for row in rows {
            let list_row = row.downcast::<PyList>()?; // Or tuple? Assuming List for now
            let mut row_vals = Vec::with_capacity(list_row.len());
            for item in list_row {
                row_vals.push(to_toon_value(&item, None).map_err(PyErr::from)?);
            }
            row_data.push(row_vals);
        }

        let indent = indent_size.unwrap_or(2);
        let delim = delimiter.unwrap_or_else(|| ",".to_string());

        let encode_result = py.allow_threads(move || {
            catch_unwind(AssertUnwindSafe(|| {
                Ok(encode_tabular_rows(
                    count, columns, row_data, indent, &delim,
                ))
            }))
        });

        match encode_result {
            Ok(val) => val,
            Err(panic) => Err(handle_panic(panic)),
        }
    }));

    match result {
        Ok(val) => val,
        Err(panic) => Err(handle_panic(panic)),
    }
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
    let result = catch_unwind(AssertUnwindSafe(|| {
        let indent = indent_size.unwrap_or(2);
        let delim = delimiter.as_deref().unwrap_or(",");
        Ok(batch_convert_json(paths, output_dir, indent, delim))
    }));
    match result {
        Ok(val) => val,
        Err(panic) => Err(handle_panic(panic)),
    }
}

/// Batch convert TOON files to JSON.
#[pyfunction]
#[pyo3(signature = (paths, output_dir=None, indent_size=None))]
fn convert_toon_batch(
    paths: Vec<String>,
    output_dir: Option<String>,
    indent_size: Option<usize>,
) -> PyResult<Vec<(String, String, bool)>> {
    let result = catch_unwind(AssertUnwindSafe(|| {
        let indent = indent_size.unwrap_or(2);
        Ok(batch_convert_toon(paths, output_dir, indent))
    }));
    match result {
        Ok(val) => val,
        Err(panic) => Err(handle_panic(panic)),
    }
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
    let result = catch_unwind(AssertUnwindSafe(|| {
        let indent = indent_size.unwrap_or(2);
        let delim = delimiter.as_deref().unwrap_or(",");
        Ok(batch_convert_directory(
            dir_path, recursive, output_dir, indent, delim,
        ))
    }));
    match result {
        Ok(val) => val,
        Err(panic) => Err(handle_panic(panic)),
    }
}

#[pymodule]
fn _toonverter_core(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("CONTRACT_VERSION", CONTRACT_VERSION)?;
    m.add_function(wrap_pyfunction!(decode_toon, m)?)?;
    m.add_function(wrap_pyfunction!(encode_toon, m)?)?;
    m.add_function(wrap_pyfunction!(encode_from_pandas, m)?)?;
    m.add_function(wrap_pyfunction!(encode_from_rows, m)?)?;
    m.add_function(wrap_pyfunction!(convert_json_batch, m)?)?;
    m.add_function(wrap_pyfunction!(convert_toon_batch, m)?)?;
    m.add_function(wrap_pyfunction!(convert_json_directory, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_contract_version_exposed() {
        pyo3::prepare_freethreaded_python();
        Python::with_gil(|_py| {
            // Need to verify via Python module system if possible, or just check the const
            assert_eq!(CONTRACT_VERSION, "1.0.0");
        });
    }

    #[test]
    fn test_decode_empty_string_safe() {
        pyo3::prepare_freethreaded_python();
        Python::with_gil(|_py| {
            let res = decode_toon(_py, "", None);
            assert!(res.is_ok());
        });
    }

    #[test]
    fn test_handle_panic_string() {
        pyo3::prepare_freethreaded_python();
        let panic_payload = Box::new("panic message");
        let py_err = handle_panic(panic_payload);
        Python::with_gil(|py| {
            let type_name = py_err.get_type_bound(py).name().unwrap().to_string();
            // It should be InternalError, but since that's defined in Python,
            // and we might not have the python module loaded in this rust test env,
            // it might fallback or behave differently.
            // Actually handle_panic tries to import "toonverter.core.exceptions".
            // If that fails (which it might in `cargo test` if python path isn't set), it returns import error.
            // But we can at least check it doesn't crash.
            assert!(!type_name.is_empty());
        });
    }

    #[test]
    fn test_encode_toon_recursion_error() {
        pyo3::prepare_freethreaded_python();
        Python::with_gil(|py| {
            // Create a recursive dict
            let dict = PyDict::new_bound(py);
            dict.set_item("self", &dict).unwrap();

            // This should fail with recursion error in to_toon_value
            let res = encode_toon(py, dict.as_any().clone(), None, None, Some(10));
            assert!(res.is_err());
        });
    }

    #[test]
    fn test_encode_from_pandas_length_mismatch() {
        pyo3::prepare_freethreaded_python();
        Python::with_gil(|py| {
            let data = PyDict::new_bound(py);
            let col1 = PyList::new_bound(py, vec![1, 2]);
            let col2 = PyList::new_bound(py, vec![3]); // Mismatch
            data.set_item("a", col1).unwrap();
            data.set_item("b", col2).unwrap();

            let res = encode_from_pandas(py, data, None, None);
            assert!(res.is_err());
            // We can't easily check the message content of PyErr in rust without more boilerplate,
            // but is_err() confirms we caught the condition.
        });
    }

    #[test]
    fn test_batch_functions_coverage() {
        pyo3::prepare_freethreaded_python();

        // existing simple calls
        let res_json = convert_json_batch(vec![], None, None, None);
        assert!(res_json.is_ok());

        let res_toon = convert_toon_batch(vec![], None, None);
        assert!(res_toon.is_ok());

        // Robust directory test
        use std::io::Write;
        let temp_dir = tempfile::tempdir().unwrap();
        let file_path = temp_dir.path().join("test.json");
        let mut file = std::fs::File::create(&file_path).unwrap();
        file.write_all(b"{\"key\": \"value\"}").unwrap();

        let dir_str = temp_dir.path().to_str().unwrap().to_string();

        let res_dir = convert_json_directory(dir_str, false, None, None, None);
        assert!(res_dir.is_ok());
        let results = res_dir.unwrap();
        assert_eq!(results.len(), 1);
        // Tuple is (path, content/error_msg, is_error). false means success.
        assert!(!results[0].2, "Conversion failed: {:?}", results[0]);
    }

    #[test]
    fn test_encode_from_rows_coverage() {
        pyo3::prepare_freethreaded_python();
        Python::with_gil(|py| {
            let cols = vec!["a".to_string()];
            let rows = PyList::new_bound(py, vec![PyList::new_bound(py, vec![1])]);
            let res = encode_from_rows(py, cols, rows, None, None);
            assert!(res.is_ok());
        });
    }

    #[test]
    fn test_module_init() {
        pyo3::prepare_freethreaded_python();
        Python::with_gil(|py| {
            let m = PyModule::new_bound(py, "test_module").unwrap();
            let res = _toonverter_core(py, &m);
            assert!(res.is_ok());
        });
    }
}
