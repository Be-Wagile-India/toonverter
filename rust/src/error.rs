use pyo3::exceptions::{PyRuntimeError, PyTypeError, PyValueError};
use pyo3::prelude::*;
use std::fmt;

#[derive(Debug)]
pub enum ToonError {
    Io(std::io::Error),
    Fmt(std::fmt::Error),
    Json(serde_json::Error),
    Syntax(String),
    Type(String),
    RecursionLimit(String),
}

impl fmt::Display for ToonError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ToonError::Io(e) => write!(f, "IO Error: {}", e),
            ToonError::Fmt(e) => write!(f, "Format Error: {}", e),
            ToonError::Json(e) => write!(f, "JSON Error: {}", e),
            ToonError::Syntax(msg) => write!(f, "Syntax Error: {}", msg),
            ToonError::Type(msg) => write!(f, "Type Error: {}", msg),
            ToonError::RecursionLimit(msg) => write!(f, "Recursion Limit: {}", msg),
        }
    }
}

impl std::error::Error for ToonError {}

impl From<std::io::Error> for ToonError {
    fn from(err: std::io::Error) -> Self {
        ToonError::Io(err)
    }
}

impl From<std::fmt::Error> for ToonError {
    fn from(err: std::fmt::Error) -> Self {
        ToonError::Fmt(err)
    }
}

impl From<serde_json::Error> for ToonError {
    fn from(err: serde_json::Error) -> Self {
        ToonError::Json(err)
    }
}

impl From<String> for ToonError {
    fn from(msg: String) -> Self {
        ToonError::Syntax(msg)
    }
}

impl From<&str> for ToonError {
    fn from(msg: &str) -> Self {
        ToonError::Syntax(msg.to_string())
    }
}

impl From<ToonError> for PyErr {
    fn from(err: ToonError) -> PyErr {
        match err {
            ToonError::Io(e) => PyRuntimeError::new_err(e.to_string()),
            ToonError::Fmt(e) => PyRuntimeError::new_err(e.to_string()),
            ToonError::Json(e) => PyValueError::new_err(e.to_string()),
            ToonError::Syntax(msg) => PyValueError::new_err(msg),
            ToonError::Type(msg) => PyTypeError::new_err(msg),
            ToonError::RecursionLimit(msg) => PyRuntimeError::new_err(msg),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io;

    #[test]
    fn test_display_io() {
        let err = ToonError::from(io::Error::new(io::ErrorKind::Other, "io error"));
        assert_eq!(format!("{}", err), "IO Error: io error");
    }

    #[test]
    fn test_display_fmt() {
        let err = ToonError::from(std::fmt::Error);
        assert_eq!(
            format!("{}", err),
            "Format Error: an error occurred when formatting an argument"
        );
    }

    #[test]
    fn test_display_json() {
        let json_err = serde_json::from_str::<serde_json::Value>("{invalid").unwrap_err();
        let err = ToonError::from(json_err);
        assert!(format!("{}", err).starts_with("JSON Error: key must be a string"));
    }

    #[test]
    fn test_display_syntax() {
        let err = ToonError::from("syntax error".to_string());
        assert_eq!(format!("{}", err), "Syntax Error: syntax error");

        let err_str = ToonError::from("syntax error str");
        assert_eq!(format!("{}", err_str), "Syntax Error: syntax error str");
    }

    #[test]
    fn test_display_type() {
        let err = ToonError::Type("type error".to_string());
        assert_eq!(format!("{}", err), "Type Error: type error");
    }

    #[test]
    fn test_display_recursion() {
        let err = ToonError::RecursionLimit("recursion limit".to_string());
        assert_eq!(format!("{}", err), "Recursion Limit: recursion limit");
    }

    #[test]
    fn test_from_impls() {
        let _ = ToonError::from(io::Error::new(io::ErrorKind::Other, "e"));
        let _ = ToonError::from(std::fmt::Error);
        let _ = ToonError::from(serde_json::from_str::<serde_json::Value>("{").unwrap_err());
        let _ = ToonError::from("string".to_string());
        let _ = ToonError::from("str");
    }
}
