use pyo3::prelude::*;
use std::fmt;

#[derive(Debug)]
pub enum ToonverterError {
    InvalidInput(String),
    UnsupportedFormat(String),
    ProcessingError(String),
    InternalError(String),
}

impl fmt::Display for ToonverterError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            ToonverterError::InvalidInput(msg) => write!(f, "Invalid Input: {}", msg),
            ToonverterError::UnsupportedFormat(msg) => write!(f, "Unsupported Format: {}", msg),
            ToonverterError::ProcessingError(msg) => write!(f, "Processing Error: {}", msg),
            ToonverterError::InternalError(msg) => write!(f, "Internal Error: {}", msg),
        }
    }
}

impl std::error::Error for ToonverterError {}

// Map standard errors to Contract variants
impl From<std::io::Error> for ToonverterError {
    fn from(err: std::io::Error) -> Self {
        ToonverterError::ProcessingError(format!("IO Error: {}", err))
    }
}

impl From<std::fmt::Error> for ToonverterError {
    fn from(err: std::fmt::Error) -> Self {
        ToonverterError::ProcessingError(format!("Formatting Error: {}", err))
    }
}

impl From<serde_json::Error> for ToonverterError {
    fn from(err: serde_json::Error) -> Self {
        ToonverterError::InvalidInput(format!("JSON Error: {}", err))
    }
}

impl From<String> for ToonverterError {
    fn from(msg: String) -> Self {
        ToonverterError::ProcessingError(msg)
    }
}

impl From<&str> for ToonverterError {
    fn from(msg: &str) -> Self {
        ToonverterError::ProcessingError(msg.to_string())
    }
}

// FFI Boundary: Convert Rust Contract Error to Python Exception
impl From<ToonverterError> for PyErr {
    fn from(err: ToonverterError) -> PyErr {
        Python::with_gil(|py| {
            let exceptions = match py.import_bound("toonverter.core.exceptions") {
                Ok(module) => module,
                Err(e) => return e,
            };

            let exception_name = match err {
                ToonverterError::InvalidInput(_) => "ValidationError",
                ToonverterError::UnsupportedFormat(_) => "FormatNotSupportedError",
                ToonverterError::ProcessingError(_) => "ProcessingError",
                ToonverterError::InternalError(_) => "InternalError",
            };

            match exceptions.getattr(exception_name) {
                Ok(exc_class) => {
                    let msg = err.to_string();
                    match exc_class.call1((msg,)) {
                        Ok(exc_instance) => PyErr::from_value_bound(exc_instance),
                        Err(e) => e,
                    }
                }
                Err(e) => e,
            }
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_error_display() {
        let err = ToonverterError::InvalidInput("invalid input".to_string());
        assert_eq!(format!("{}", err), "Invalid Input: invalid input");

        let err = ToonverterError::UnsupportedFormat("bad format".to_string());
        assert_eq!(format!("{}", err), "Unsupported Format: bad format");

        let err = ToonverterError::ProcessingError("proc error".to_string());
        assert_eq!(format!("{}", err), "Processing Error: proc error");

        let err = ToonverterError::InternalError("internal error".to_string());
        assert_eq!(format!("{}", err), "Internal Error: internal error");
    }

    #[test]
    fn test_from_io_error() {
        let io_err = std::io::Error::new(std::io::ErrorKind::Other, "io failure");
        let err: ToonverterError = io_err.into();
        match err {
            ToonverterError::ProcessingError(msg) => assert!(msg.contains("IO Error: io failure")),
            _ => panic!("Expected ProcessingError"),
        }
    }

    #[test]
    fn test_from_fmt_error() {
        let fmt_err = std::fmt::Error;
        let err: ToonverterError = fmt_err.into();
        match err {
            ToonverterError::ProcessingError(msg) => assert!(msg.contains("Formatting Error")),
            _ => panic!("Expected ProcessingError"),
        }
    }

    #[test]
    fn test_from_json_error() {
        // Create a serde_json error
        let json_err = serde_json::from_str::<serde_json::Value>("{").unwrap_err();
        let err: ToonverterError = json_err.into();
        match err {
            ToonverterError::InvalidInput(msg) => assert!(msg.contains("JSON Error")),
            _ => panic!("Expected InvalidInput"),
        }
    }

    #[test]
    fn test_from_string() {
        let err: ToonverterError = "error msg".into();
        match err {
            ToonverterError::ProcessingError(msg) => assert_eq!(msg, "error msg"),
            _ => panic!("Expected ProcessingError"),
        }

        let err: ToonverterError = String::from("string error").into();
        match err {
            ToonverterError::ProcessingError(msg) => assert_eq!(msg, "string error"),
            _ => panic!("Expected ProcessingError"),
        }
    }
}
