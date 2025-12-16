use indexmap::IndexMap;
use serde::ser::{Serialize, SerializeMap, SerializeSeq, Serializer};
use serde_json::Value as JsonValue;

#[derive(Debug, PartialEq, Clone)]
pub enum ToonValue {
    Null,
    Boolean(bool),
    Integer(i64),
    Float(f64),
    String(String),
    List(Vec<ToonValue>),
    Dict(IndexMap<String, ToonValue>),
}

impl From<JsonValue> for ToonValue {
    fn from(json: JsonValue) -> Self {
        match json {
            JsonValue::Null => ToonValue::Null,
            JsonValue::Bool(b) => ToonValue::Boolean(b),
            JsonValue::Number(n) => {
                if let Some(i) = n.as_i64() {
                    ToonValue::Integer(i)
                } else if let Some(f) = n.as_f64() {
                    ToonValue::Float(f)
                } else {
                    ToonValue::Null
                }
            }
            JsonValue::String(s) => ToonValue::String(s),
            JsonValue::Array(arr) => {
                let list = arr.into_iter().map(ToonValue::from).collect();
                ToonValue::List(list)
            }
            JsonValue::Object(obj) => {
                let mut map = IndexMap::new();
                for (k, v) in obj {
                    map.insert(k, ToonValue::from(v));
                }
                ToonValue::Dict(map)
            }
        }
    }
}

impl Serialize for ToonValue {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        match self {
            ToonValue::Null => serializer.serialize_none(),
            ToonValue::Boolean(b) => serializer.serialize_bool(*b),
            ToonValue::Integer(i) => serializer.serialize_i64(*i),
            ToonValue::Float(f) => serializer.serialize_f64(*f),
            ToonValue::String(s) => serializer.serialize_str(s),
            ToonValue::List(list) => {
                let mut seq = serializer.serialize_seq(Some(list.len()))?;
                for item in list {
                    seq.serialize_element(item)?;
                }
                seq.end()
            }
            ToonValue::Dict(map) => {
                let mut m = serializer.serialize_map(Some(map.len()))?;
                for (k, v) in map {
                    m.serialize_entry(k, v)?;
                }
                m.end()
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn test_ir_equality() {
        assert_eq!(ToonValue::Null, ToonValue::Null);
        assert_ne!(ToonValue::Null, ToonValue::Boolean(false));
    }

    #[test]
    fn test_ir_nested() {
        let mut map = IndexMap::new();
        map.insert("a".to_string(), ToonValue::Integer(1));
        let dict = ToonValue::Dict(map);

        let list = ToonValue::List(vec![dict.clone()]);

        if let ToonValue::List(l) = list {
            assert_eq!(l[0], dict);
        } else {
            panic!("Expected List");
        }
    }

    #[test]
    fn test_json_conversion() {
        let json_val = json!({
            "key": "value",
            "list": [1, 2, true]
        });
        let toon_val = ToonValue::from(json_val);

        if let ToonValue::Dict(map) = toon_val {
            assert_eq!(
                map.get("key"),
                Some(&ToonValue::String("value".to_string()))
            );
            if let Some(ToonValue::List(l)) = map.get("list") {
                assert_eq!(l.len(), 3);
                assert_eq!(l[0], ToonValue::Integer(1));
            } else {
                panic!("Expected list");
            }
        } else {
            panic!("Expected Dict");
        }
    }

    #[test]

    fn test_json_conversion_large_number() {
        // Create a number too large for i64, by parsing from JSON

        let large_number_str_json = r#"{"num": 1234567890123456789012345678901234567890}"#;

        let json_val_wrapper: JsonValue = serde_json::from_str(large_number_str_json).unwrap();

        let json_val = json_val_wrapper.get("num").unwrap().clone();

        let toon_val = ToonValue::from(json_val);

        // Assert that it's a Float and has the expected approximate value

        if let ToonValue::Float(f) = toon_val {
            // Compare with a small epsilon due to potential floating point inaccuracies

            // The expected value is 1.2345678901234567e39 based on prior test output.

            let expected_f = 1.2345678901234567e39;

            let epsilon = 1.0e20; // A sufficiently large epsilon for this scale

            assert!(
                (f - expected_f).abs() < epsilon,
                "Expected float close to {}, got {}",
                expected_f,
                f
            );
        } else {
            panic!("Expected Float, got {:?}", toon_val);
        }
    }

    #[test]
    fn test_serialize_ir() {
        let mut map = IndexMap::new();
        map.insert("key".to_string(), ToonValue::String("val".to_string()));
        let dict = ToonValue::Dict(map);
        let list = ToonValue::List(vec![
            ToonValue::Integer(1),
            ToonValue::Float(2.5),
            ToonValue::Boolean(true),
            ToonValue::Null,
            dict,
        ]);

        let json_str = serde_json::to_string(&list).unwrap();
        assert_eq!(json_str, "[1,2.5,true,null,{\"key\":\"val\"}]");
    }
}
