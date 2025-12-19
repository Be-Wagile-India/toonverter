use indexmap::IndexMap;
use num_bigint::BigInt;
use pyo3::exceptions::{PyRecursionError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyString, PyTuple};

use crate::ir::ToonValue;

pub fn to_toon_value(
    obj: &Bound<'_, PyAny>,
    recursion_depth_limit: Option<usize>,
) -> PyResult<ToonValue> {
    let limit = recursion_depth_limit.unwrap_or(200);
    to_toon_value_recursive(obj, 0, limit)
}

fn to_toon_value_recursive(
    obj: &Bound<'_, PyAny>,
    depth: usize,
    limit: usize,
) -> PyResult<ToonValue> {
    if depth > limit {
        return Err(PyRecursionError::new_err(
            "Maximum recursion depth exceeded during TOON conversion",
        ));
    }

    if obj.is_none() {
        Ok(ToonValue::Null)
    } else if let Ok(b) = obj.extract::<bool>() {
        Ok(ToonValue::Boolean(b))
    } else if let Ok(i) = obj.extract::<i64>() {
        Ok(ToonValue::Integer(i))
    } else if let Ok(bi) = obj.extract::<BigInt>() {
        // Fallback for integers larger than i64
        Ok(ToonValue::BigInteger(bi))
    } else if let Ok(f) = obj.extract::<f64>() {
        Ok(ToonValue::Float(f))
    } else if let Ok(s) = obj.extract::<String>() {
        Ok(ToonValue::String(s))
    } else if let Ok(dict) = obj.downcast::<PyDict>() {
        let mut map = IndexMap::new();
        for (k, v) in dict {
            let k_str = k.extract::<String>()?;
            let v_val = to_toon_value_recursive(&v, depth + 1, limit)?;
            map.insert(k_str, v_val);
        }
        Ok(ToonValue::Dict(map))
    } else if let Ok(list) = obj.downcast::<PyList>() {
        let mut vec = Vec::with_capacity(list.len());
        for item in list {
            vec.push(to_toon_value_recursive(&item, depth + 1, limit)?);
        }
        Ok(ToonValue::List(vec))
    } else if let Ok(tuple) = obj.downcast::<PyTuple>() {
        let mut vec = Vec::with_capacity(tuple.len());
        for item in tuple {
            vec.push(to_toon_value_recursive(&item, depth + 1, limit)?);
        }
        Ok(ToonValue::List(vec))
    } else {
        Err(PyValueError::new_err("Unsupported type for TOON encoding"))
    }
}

pub fn to_py_object(py: Python, val: &ToonValue) -> PyResult<PyObject> {
    match val {
        ToonValue::Null => Ok(py.None()),
        ToonValue::Boolean(b) => Ok(b.into_py(py)),
        ToonValue::Integer(i) => Ok(i.into_py(py)),
        ToonValue::BigInteger(bi) => Ok(bi.clone().into_py(py)),
        ToonValue::Float(f) => Ok(f.into_py(py)),
        ToonValue::String(s) => Ok(PyString::new_bound(py, s).into_py(py)),
        ToonValue::List(list) => {
            let py_list = PyList::empty_bound(py);
            for item in list {
                py_list.append(to_py_object(py, item)?)?;
            }
            Ok(py_list.into_py(py))
        }
        ToonValue::Dict(map) => {
            let py_dict = PyDict::new_bound(py);
            for (k, v) in map {
                py_dict.set_item(k, to_py_object(py, v)?)?;
            }
            Ok(py_dict.into_py(py))
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use once_cell::sync::Lazy;
    use pyo3::types::PyModule;

    static INITIALIZED: Lazy<()> = Lazy::new(|| {
        pyo3::prepare_freethreaded_python();
    });

    #[test]
    fn test_conversion_roundtrip() {
        let _ = &*INITIALIZED;
        Python::with_gil(|py| {
            // Dict
            let mut map = IndexMap::new();
            map.insert("a".to_string(), ToonValue::Integer(1));
            let tv = ToonValue::Dict(map);

            let py_obj = to_py_object(py, &tv).unwrap();
            let back = to_toon_value(py_obj.bind(py), None).unwrap();
            assert_eq!(tv, back);
        });
    }

    #[test]
    fn test_conversion_primitives() {
        let _ = &*INITIALIZED;
        Python::with_gil(|py| {
            // Null
            let tv = ToonValue::Null;
            let py_obj = to_py_object(py, &tv).unwrap();
            let back = to_toon_value(py_obj.bind(py), None).unwrap();
            assert_eq!(tv, back);

            // Boolean
            let tv = ToonValue::Boolean(true);
            let py_obj = to_py_object(py, &tv).unwrap();
            let back = to_toon_value(py_obj.bind(py), None).unwrap();
            assert_eq!(tv, back);

            // Float
            let tv = ToonValue::Float(1.23);
            let py_obj = to_py_object(py, &tv).unwrap();
            let back = to_toon_value(py_obj.bind(py), None).unwrap();
            assert_eq!(tv, back);

            // String
            let tv = ToonValue::String("hello".to_string());
            let py_obj = to_py_object(py, &tv).unwrap();
            let back = to_toon_value(py_obj.bind(py), None).unwrap();
            assert_eq!(tv, back);
        });
    }

    #[test]
    fn test_conversion_list() {
        let _ = &*INITIALIZED;
        Python::with_gil(|py| {
            let mut list = Vec::new();
            list.push(ToonValue::Integer(1));
            list.push(ToonValue::String("a".to_string()));
            let tv = ToonValue::List(list);

            let py_obj = to_py_object(py, &tv).unwrap();
            let back = to_toon_value(py_obj.bind(py), None).unwrap();
            assert_eq!(tv, back);
        });
    }

    #[test]
    fn test_conversion_error() {
        let _ = &*INITIALIZED;
        Python::with_gil(|py| {
            // Create a Python object that is not supported (e.g., a set)
            let set = py.eval_bound("{1, 2}", None, None).unwrap();
            let result = to_toon_value(&set, None);
            assert!(result.is_err());
            assert!(result.unwrap_err().to_string().contains("Unsupported type"));
        });
    }

    #[test]
    fn test_conversion_tuple_support() {
        let _ = &*INITIALIZED;
        Python::with_gil(|py| {
            let tuple_obj = py.eval_bound("(1, 2, 3)", None, None).unwrap();
            let result = to_toon_value(&tuple_obj, None).unwrap();
            assert_eq!(
                result,
                ToonValue::List(vec![
                    ToonValue::Integer(1),
                    ToonValue::Integer(2),
                    ToonValue::Integer(3)
                ])
            );
        });
    }

    #[test]
    fn test_conversion_unsupported_python_object() {
        let _ = &*INITIALIZED;
        Python::with_gil(|py| {
            // Define a simple custom Python class
            let code = "class MyCustomObject: pass";
            let module = PyModule::from_code_bound(py, code, "my_module.py", "my_module").unwrap();
            let obj_type = module.getattr("MyCustomObject").unwrap();
            let custom_obj = obj_type.call0().unwrap(); // Instantiate MyCustomObject

            let result = to_toon_value(&custom_obj, None);
            assert!(result.is_err());
            assert!(result
                .unwrap_err()
                .to_string()
                .contains("Unsupported type for TOON encoding"));
        });
    }

    #[test]
    fn test_recursion_depth_limit() {
        let _ = &*INITIALIZED;
        Python::with_gil(|py| {
            let data = PyDict::new_bound(py);
            let mut current = data.clone();
            for _ in 0..(200 + 10) {
                // Go beyond the limit
                let next_dict = PyDict::new_bound(py);
                current.set_item("a", next_dict.clone()).unwrap();
                current = next_dict;
            }

            let result = to_toon_value(&data, None);
            assert!(result.is_err());
            let err = result.unwrap_err();
            assert!(err.to_string().contains("Maximum recursion depth exceeded"));
        });
    }

    #[test]
    fn test_conversion_bigint_roundtrip() {
        let _ = &*INITIALIZED;
        Python::with_gil(|py| {
            let large_int_py = py.eval_bound("2**100", None, None).unwrap(); // Python's arbitrary precision int
            let tv = to_toon_value(&large_int_py, None).unwrap();

            if let ToonValue::BigInteger(ref bi) = tv {
                assert_eq!(bi.to_string(), "1267650600228229401496703205376");
            } else {
                panic!("Expected BigInteger, got {:?}", tv);
            }

            let py_obj = to_py_object(py, &tv).unwrap();
            let back_int: BigInt = py_obj.extract(py).unwrap();
            assert_eq!(back_int.to_string(), "1267650600228229401496703205376");
        });
    }
}
