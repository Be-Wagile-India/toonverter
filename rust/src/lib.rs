use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyDict;

mod batch;
mod conversion;
mod encoder;
mod ir;
mod lexer;
mod parser;
mod serde_toon;
mod tokens;

use batch::{batch_convert_directory, batch_convert_json, batch_convert_toon};
use conversion::{to_py_object, to_toon_value};
use encoder::encode_toon_root;
use lexer::ToonLexer;
use parser::ToonParser;

#[pyfunction]
fn decode_toon(py: Python, text: &str) -> PyResult<PyObject> {
    if text.trim().is_empty() {
        return Ok(PyDict::new_bound(py).into_py(py));
    }

    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);

    match parser.parse_root() {
        Ok(tv) => to_py_object(py, &tv),
        Err(e) => Err(PyValueError::new_err(e)),
    }
}

#[pyfunction]
fn encode_toon(_py: Python, obj: Bound<'_, PyAny>) -> PyResult<String> {
    let ir = to_toon_value(&obj)?;
    Ok(encode_toon_root(&ir))
}

/// Batch convert JSON files.
#[pyfunction]
#[pyo3(signature = (paths, output_dir=None))]
fn convert_json_batch(
    paths: Vec<String>,
    output_dir: Option<String>,
) -> PyResult<Vec<(String, String, bool)>> {
    Ok(batch_convert_json(paths, output_dir))
}

/// Batch convert TOON files to JSON.
#[pyfunction]
#[pyo3(signature = (paths, output_dir=None))]
fn convert_toon_batch(
    paths: Vec<String>,
    output_dir: Option<String>,
) -> PyResult<Vec<(String, String, bool)>> {
    Ok(batch_convert_toon(paths, output_dir))
}

/// Batch convert JSON files in a directory.
#[pyfunction]
#[pyo3(signature = (dir_path, recursive=false, output_dir=None))]
fn convert_json_directory(
    dir_path: String,
    recursive: bool,
    output_dir: Option<String>,
) -> PyResult<Vec<(String, String, bool)>> {
    Ok(batch_convert_directory(dir_path, recursive, output_dir))
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
