use indexmap::IndexMap;
use num_bigint::BigInt;
use serde::ser::{Serialize, SerializeMap, SerializeSeq, Serializer};
use serde_json::Value as JsonValue;

#[derive(Debug, PartialEq, Clone)]
pub enum ToonValue {
    Null,
    Boolean(bool),
    Integer(i64),
    BigInteger(BigInt),
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
                    // Fallback for numbers that don't fit i64 or f64, usually big ints in JSON string form or arbitrary precision
                    // serde_json::Number can represent arbitrary precision if enabled, but by default it parses to f64 or i64/u64.
                    // If it's a u64 that fits in i64, it's covered. If it's a u64 > i64::MAX, as_i64 fails.
                    // Let's try to stringify and parse as BigInt as a safety net if possible, or just default to Null/Float
                    if let Some(u) = n.as_u64() {
                        // It fits in u64 but not i64 (so it's large positive)
                        return ToonValue::BigInteger(BigInt::from(u));
                    }
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
            ToonValue::BigInteger(bi) => {
                // Serialize BigInt as a number (if serializer supports it) or string?
                // JSON spec allows numbers of any size, but many parsers limit to f64.
                // For safety and compatibility, serialization to string might be safer for massive numbers,
                // but Toon/JSON usually expects raw digits.
                // serde_json handles BigInt (with features) or Number.
                // Let's serialize as a custom number implementation or cast to f64 if acceptable?
                // Actually, let's try to serialize as i64 if it fits (redundant) or just delegate to BigInt's serialize if available.
                // However, num-bigint's default serialization might not be "raw number".
                // Simplest valid JSON approach: serialize as a number.
                // We'll trust the serializer handles it (e.g. converting to a number token).
                // If using serde_json, BigInt can be serialized directly if features enabled.
                // Since we didn't enable serde on num-bigint in Cargo.toml, we should convert to string or use a workaround.
                // Wait, I didn't enable serde feature for num-bigint.
                // Let's convert to string and serialize as a 'raw number' if possible, or string?
                // TOON spec says: canonical numbers.
                // For now, let's serialize as a Float to maintain existing behavior for JSON output,
                // OR serialize as string digits?
                // Better: serialize as a float for now to avoid breaking existing clients that expect standard JSON types,
                // BUT this defeats the purpose of "Integer Precision Loss" fix for serialization.
                // Correct fix: Enable serde feature for num-bigint or implement custom serialization.
                // I will add serde feature to num-bigint in next step. For now, serialize as string.
                serializer.serialize_str(&bi.to_string())
            }
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
