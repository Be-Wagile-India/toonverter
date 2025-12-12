use rayon::prelude::*;

use crate::ir::ToonValue;

pub fn encode_toon_root(value: &ToonValue) -> String {
    if let ToonValue::Dict(map) = value {
        if map.is_empty() {
            return "".to_string();
        }
        let mut lines = Vec::new();
        for (k, v) in map {
            let v_str = encode_toon_value(v, 0, 2);
            if v_str.starts_with('\n') {
                lines.push(format!("{}:{}", k, v_str));
            } else {
                lines.push(format!("{}: {}", k, v_str));
            }
        }
        lines.join("\n")
    } else {
        let s = encode_toon_value(value, 0, 2);
        s.trim_start_matches('\n').to_string()
    }
}

pub fn encode_toon_value(value: &ToonValue, indent_level: usize, indent_size: usize) -> String {
    match value {
        ToonValue::Null => "null".to_string(),
        ToonValue::Boolean(b) => {
            if *b {
                "true".to_string()
            } else {
                "false".to_string()
            }
        }
        ToonValue::Integer(i) => i.to_string(),
        ToonValue::Float(f) => {
            if f.is_nan() || f.is_infinite() {
                "null".to_string()
            } else if *f == 0.0 && f.is_sign_negative() {
                "0".to_string()
            } else {
                f.to_string()
            }
        }
        ToonValue::String(s) => {
            let is_reserved = matches!(s.as_str(), "true" | "false" | "null");
            let is_number = s.parse::<f64>().is_ok();
            let has_special_chars = s
                .chars()
                .any(|c| matches!(c, ':' | ' ' | '\n' | '[' | ']' | '{' | '}' | ','))
                || s.is_empty();

            if is_reserved || is_number || has_special_chars {
                format!("{:?}", s)
            } else {
                s.clone()
            }
        }
        ToonValue::Dict(map) => {
            if map.is_empty() {
                return "{}".to_string();
            }
            let mut lines = Vec::new();
            lines.push("".to_string()); // Start with newline

            for (k, v) in map {
                let v_str = encode_toon_value(v, indent_level + 1, indent_size);
                let next_indent = " ".repeat((indent_level + 1) * indent_size);

                if v_str.starts_with('\n') {
                    lines.push(format!("{}{}:{}", next_indent, k, v_str));
                } else {
                    lines.push(format!("{}{}: {}", next_indent, k, v_str));
                }
            }
            lines.join("\n")
        }
        ToonValue::List(list) => {
            let len = list.len();

            // Detect Tabular
            let mut is_tabular = true;
            let mut keys: Option<Vec<String>> = None;
            let mut all_primitive = true;

            for item in list {
                match item {
                    ToonValue::Dict(_) => {} // Continue if it's a Dict
                    _ => {
                        is_tabular = false;
                    }
                }
                match item {
                    ToonValue::Dict(_) | ToonValue::List(_) => {
                        all_primitive = false;
                    }
                    _ => {} // Primitive types are fine
                }
            }

            if is_tabular && !list.is_empty() {
                // Check consistent keys and primitive values inside dicts
                for item in list {
                    if let ToonValue::Dict(d) = item {
                        for v in d.values() {
                            match v {
                                ToonValue::Dict(_) | ToonValue::List(_) => {
                                    is_tabular = false;
                                    break;
                                }
                                _ => {} // Primitive values are fine
                            }
                        }
                        if !is_tabular {
                            break;
                        }

                        let mut current_keys: Vec<String> = d.keys().cloned().collect();
                        current_keys.sort();
                        if let Some(ref prev_keys) = keys {
                            if prev_keys != &current_keys {
                                is_tabular = false;
                                break;
                            }
                        } else {
                            keys = Some(current_keys);
                        }
                    }
                }
            } else {
                is_tabular = false;
            }

            if is_tabular && !list.is_empty() {
                // Tabular Encoding
                if let ToonValue::Dict(first_dict) = &list[0] {
                    let fields: Vec<String> = first_dict.keys().cloned().collect();

                    // header like: [3]{a,b,c}:
                    let header = format!("[{}]{{{}}}:", len, fields.join(","));
                    let row_indent = " ".repeat((indent_level + 1) * indent_size);

                    // Parallelize row processing
                    let rows: Vec<String> = list
                        .par_iter()
                        .map(|item| {
                            if let ToonValue::Dict(d) = item {
                                let mut row_vals = Vec::new();
                                for f in &fields {
                                    if let Some(v) = d.get(f) {
                                        row_vals.push(encode_toon_value(v, 0, 0));
                                    } else {
                                        row_vals.push("null".to_string());
                                    }
                                }
                                format!("{}{}", row_indent, row_vals.join(","))
                            } else {
                                String::new() // Should not happen
                            }
                        })
                        .collect();

                    let mut result = Vec::new();
                    result.push(header);
                    result.extend(rows);
                    return result.join("\n");
                }
            }

            if all_primitive {
                // Parallelize primitive formatting
                let parts: Vec<String> = list
                    .par_iter()
                    .map(|item| encode_toon_value(item, 0, 0))
                    .collect();

                let values = parts.join(",");
                if values.is_empty() {
                    format!("[{}]:", len)
                } else {
                    format!("[{}]: {}", len, values)
                }
            } else {
                // Regular list
                let item_indent = " ".repeat((indent_level + 1) * indent_size);

                // Parallelize item encoding
                let encoded_items: Vec<String> = list
                    .par_iter()
                    .map(|item| {
                        let val_str = encode_toon_value(item, indent_level + 2, indent_size);
                        if val_str.starts_with('\n') {
                            format!("{}  -\n{}", item_indent, val_str)
                        } else {
                            format!("{}  - {}", item_indent, val_str)
                        }
                    })
                    .collect();

                let mut list_lines = Vec::new();
                list_lines.push(format!(
                    "[{}] :
",
                    len
                ));
                list_lines.extend(encoded_items);
                list_lines.join("\n")
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use indexmap::IndexMap;

    #[test]
    fn test_encode_null() {
        let tv = ToonValue::Null;
        assert_eq!(encode_toon_value(&tv, 0, 2), "null");
    }

    #[test]
    fn test_encode_boolean() {
        let tv_true = ToonValue::Boolean(true);
        let tv_false = ToonValue::Boolean(false);
        assert_eq!(encode_toon_value(&tv_true, 0, 2), "true");
        assert_eq!(encode_toon_value(&tv_false, 0, 2), "false");
    }

    #[test]
    fn test_encode_integer() {
        let tv = ToonValue::Integer(123);
        assert_eq!(encode_toon_value(&tv, 0, 2), "123");
    }

    #[test]
    fn test_encode_float() {
        let tv = ToonValue::Float(123.45);
        assert_eq!(encode_toon_value(&tv, 0, 2), "123.45");
    }

    #[test]
    fn test_encode_float_nan() {
        let tv = ToonValue::Float(f64::NAN);
        assert_eq!(encode_toon_value(&tv, 0, 2), "null");
    }

    #[test]
    fn test_encode_float_infinity() {
        let tv_pos = ToonValue::Float(f64::INFINITY);
        let tv_neg = ToonValue::Float(f64::NEG_INFINITY);
        assert_eq!(encode_toon_value(&tv_pos, 0, 2), "null");
        assert_eq!(encode_toon_value(&tv_neg, 0, 2), "null");
    }

    #[test]
    fn test_encode_float_negative_zero() {
        let tv = ToonValue::Float(-0.0);
        assert_eq!(encode_toon_value(&tv, 0, 2), "0");
    }

    #[test]
    fn test_encode_string_simple() {
        let tv = ToonValue::String("hello".to_string());
        assert_eq!(encode_toon_value(&tv, 0, 2), "hello");
    }

    #[test]
    fn test_encode_string_needs_quoting_space() {
        let tv = ToonValue::String("hello world".to_string());
        assert_eq!(encode_toon_value(&tv, 0, 2), "\"hello world\"");
    }

    #[test]
    fn test_encode_string_needs_quoting_reserved() {
        let tv = ToonValue::String("true".to_string());
        assert_eq!(encode_toon_value(&tv, 0, 2), "\"true\"");
    }

    #[test]
    fn test_encode_string_needs_quoting_number() {
        let tv = ToonValue::String("123".to_string());
        assert_eq!(encode_toon_value(&tv, 0, 2), "\"123\"");
    }

    #[test]
    fn test_encode_dict_empty() {
        let tv = ToonValue::Dict(IndexMap::new());
        assert_eq!(encode_toon_value(&tv, 0, 2), "{}");
    }

    #[test]
    fn test_encode_dict_simple() {
        let mut map = IndexMap::new();
        map.insert("name".to_string(), ToonValue::String("Alice".to_string()));
        map.insert("age".to_string(), ToonValue::Integer(30));
        let tv = ToonValue::Dict(map);
        assert_eq!(encode_toon_value(&tv, 0, 2), "\n  name: Alice\n  age: 30");
    }

    #[test]
    fn test_encode_list_empty() {
        let tv = ToonValue::List(vec![]);
        assert_eq!(encode_toon_value(&tv, 0, 2), "[0]:");
    }

    #[test]
    fn test_encode_list_primitives() {
        let tv = ToonValue::List(vec![
            ToonValue::Integer(1),
            ToonValue::String("two".to_string()),
            ToonValue::Boolean(true),
        ]);
        assert_eq!(encode_toon_value(&tv, 0, 2), "[3]: 1,two,true");
    }
}
