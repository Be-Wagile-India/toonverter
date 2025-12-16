use rayon::prelude::*;

use crate::ir::ToonValue;

pub fn encode_toon_root(value: &ToonValue, indent_size: usize, delimiter: &str) -> String {
    if let ToonValue::Dict(map) = value {
        if map.is_empty() {
            return "".to_string();
        }
        let mut lines = Vec::new();
        for (k, v) in map {
            let v_str = encode_toon_value(v, 0, indent_size, delimiter);
            // Optimization: Array Key Syntax (key[N]: ...)
            if let ToonValue::List(_) = v {
                if v_str.starts_with('[') {
                    lines.push(format!("{}{}", k, v_str));
                    continue;
                }
            }

            if v_str.starts_with('\n') {
                lines.push(format!("{}:{}", k, v_str));
            } else {
                lines.push(format!("{}: {}", k, v_str));
            }
        }
        lines.join("\n")
    } else {
        let s = encode_toon_value(value, 0, indent_size, delimiter);
        s.trim_start_matches('\n').to_string()
    }
}

fn encode_toon_value_inline(value: &ToonValue, delimiter: &str) -> String {
    match value {
        ToonValue::Dict(map) => {
            if map.is_empty() {
                return "{}".to_string();
            }
            let items: Vec<String> = map
                .iter()
                .map(|(k, v)| format!("{}: {}", k, encode_toon_value_inline(v, delimiter)))
                .collect();
            // Inline objects always use comma separator according to spec example "{a: 1, b: 2}"
            format!("{{{}}}", items.join(", "))
        }
        ToonValue::List(list) => {
            let len = list.len();
            if list.is_empty() {
                // Determine delimiter char for empty array header if needed, but [0]: is standard
                let delimiter_char = if delimiter == "," { "" } else { delimiter };
                return format!("[{}]{}:", len, delimiter_char);
            }
            let items: Vec<String> = list
                .iter()
                .map(|v| encode_toon_value_inline(v, delimiter))
                .collect();

            let delimiter_char = if delimiter == "," { "" } else { delimiter };
            format!("[{}]{}: {}", len, delimiter_char, items.join(delimiter))
        }
        _ => encode_toon_value(value, 0, 0, delimiter),
    }
}

pub fn encode_toon_value(
    value: &ToonValue,
    indent_level: usize,
    indent_size: usize,
    delimiter: &str,
) -> String {
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
                || s.is_empty()
                || s.contains(delimiter);

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
            lines.push("".to_string());

            for (k, v) in map {
                let v_str = encode_toon_value(v, indent_level + 1, indent_size, delimiter);
                let next_indent = " ".repeat((indent_level + 1) * indent_size);

                // Optimization: Array Key Syntax (key[N]: ...)
                if let ToonValue::List(_) = v {
                    if v_str.starts_with('[') {
                        lines.push(format!("{}{}{}", next_indent, k, v_str));
                        continue;
                    }
                }

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

            let mut is_tabular = true;
            let mut keys: Option<Vec<String>> = None;
            // Removed all_primitive check for tabular eligibility
            // We now support nested structures in tabular data via inline encoding

            for item in list {
                match item {
                    ToonValue::Dict(_) => {} // Continue if it's a Dict
                    _ => {
                        is_tabular = false;
                        break; // Optimization: early exit
                    }
                }
            }

            if is_tabular && !list.is_empty() {
                // Check consistent keys
                for item in list {
                    if let ToonValue::Dict(d) = item {
                        // Removed check for nested values inside dict

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

                    let delimiter_char = if delimiter == "," { "" } else { delimiter };

                    let header =
                        format!("[{}]{}{{{}}}:", len, delimiter_char, fields.join(delimiter));
                    let row_indent = " ".repeat((indent_level + 1) * indent_size);

                    // Parallelize row processing
                    let rows: Vec<String> = list
                        .par_iter()
                        .map(|item| {
                            if let ToonValue::Dict(d) = item {
                                let mut row_vals = Vec::new();
                                for f in &fields {
                                    if let Some(v) = d.get(f) {
                                        // Use inline encoding for tabular values
                                        row_vals.push(encode_toon_value_inline(v, delimiter));
                                    } else {
                                        row_vals.push("null".to_string());
                                    }
                                }
                                format!("{}{}", row_indent, row_vals.join(delimiter))
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

            // Check if we can use inline array format [N]: v1, v2
            // We use inline if all items are "simple" enough or list is short?
            // For now, let's stick to primitives for inline arrays to avoid complex nesting unless explicit
            // But user asked for "inline encoding of nested structs".
            // Let's check if all items are primitives for legacy compatibility/readability preference,
            // OR if we want to force inline for everything?
            // Original code: checked all_primitive.
            // Let's relax it: if it's NOT tabular (dicts with same keys), we can still try inline array
            // if items are not too complex?
            // For safety and diff minimization, I'll keep the "all_primitive" check for the *compact array* form [N]: ...
            // But wait, the prompt implies "flattening or inline encoding ... to regain advantage".
            // If I have a list of dicts that are NOT uniform (so not tabular),
            // e.g. [{"a":1}, {"b":2}].
            // Standard:
            // [2]:
            //   - a: 1
            //   - b: 2
            // Inline: [2]: {a: 1}, {b: 2}
            // Inline is much more compact.
            // I will calculate `all_inline_safe` instead of `all_primitive`.
            // Effectively, we can always encode inline using `encode_toon_value_inline`.
            // But readability suffers for large objects.
            // I'll stick to modifying Tabular logic as requested ("Nested Tabular Data").
            // For regular lists, I'll keep existing behavior (primitive -> inline, complex -> multiline list).

            let all_primitive = list
                .iter()
                .all(|item| !matches!(item, ToonValue::Dict(_) | ToonValue::List(_)));

            if all_primitive {
                // Parallelize primitive formatting
                let parts: Vec<String> = list
                    .par_iter()
                    .map(|item| encode_toon_value(item, 0, 0, delimiter))
                    .collect();

                let values = parts.join(delimiter);

                let delimiter_char = if delimiter == "," { "" } else { delimiter };

                if values.is_empty() {
                    format!("[{}]{}:", len, delimiter_char)
                } else {
                    format!("[{}]{}: {}", len, delimiter_char, values)
                }
            } else {
                // Regular list
                let item_indent = " ".repeat((indent_level + 1) * indent_size);

                // Parallelize item encoding
                let encoded_items: Vec<String> = list
                    .par_iter()
                    .map(|item| {
                        let val_str =
                            encode_toon_value(item, indent_level + 2, indent_size, delimiter);
                        if val_str.starts_with('\n') {
                            format!("{}  -\n{}", item_indent, val_str)
                        } else {
                            format!("{}  - {}", item_indent, val_str)
                        }
                    })
                    .collect();

                let mut list_lines = Vec::new();
                list_lines.push(format!("[{}] :", len));
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
        assert_eq!(encode_toon_value(&tv, 0, 2, ","), "null");
    }

    #[test]
    fn test_encode_boolean() {
        let tv_true = ToonValue::Boolean(true);
        let tv_false = ToonValue::Boolean(false);
        assert_eq!(encode_toon_value(&tv_true, 0, 2, ","), "true");
        assert_eq!(encode_toon_value(&tv_false, 0, 2, ","), "false");
    }

    #[test]
    fn test_encode_integer() {
        let tv = ToonValue::Integer(123);
        assert_eq!(encode_toon_value(&tv, 0, 2, ","), "123");
    }

    #[test]
    fn test_encode_float() {
        let tv = ToonValue::Float(123.45);
        assert_eq!(encode_toon_value(&tv, 0, 2, ","), "123.45");
    }

    #[test]
    fn test_encode_float_nan() {
        let tv = ToonValue::Float(f64::NAN);
        assert_eq!(encode_toon_value(&tv, 0, 2, ","), "null");
    }

    #[test]
    fn test_encode_float_infinity() {
        let tv_pos = ToonValue::Float(f64::INFINITY);
        let tv_neg = ToonValue::Float(f64::NEG_INFINITY);
        assert_eq!(encode_toon_value(&tv_pos, 0, 2, ","), "null");
        assert_eq!(encode_toon_value(&tv_neg, 0, 2, ","), "null");
    }

    #[test]
    fn test_encode_float_negative_zero() {
        let tv = ToonValue::Float(-0.0);
        assert_eq!(encode_toon_value(&tv, 0, 2, ","), "0");
    }

    #[test]
    fn test_encode_string_simple() {
        let tv = ToonValue::String("hello".to_string());
        assert_eq!(encode_toon_value(&tv, 0, 2, ","), "hello");
    }

    #[test]
    fn test_encode_string_needs_quoting_space() {
        let tv = ToonValue::String("hello world".to_string());
        assert_eq!(encode_toon_value(&tv, 0, 2, ","), "\"hello world\"");
    }

    #[test]
    fn test_encode_string_needs_quoting_reserved() {
        let tv = ToonValue::String("true".to_string());
        assert_eq!(encode_toon_value(&tv, 0, 2, ","), "\"true\"");
    }

    #[test]
    fn test_encode_string_needs_quoting_number() {
        let tv = ToonValue::String("123".to_string());
        assert_eq!(encode_toon_value(&tv, 0, 2, ","), "\"123\"");
    }

    #[test]

    fn test_encode_dict_empty() {
        let tv = ToonValue::Dict(IndexMap::new());

        assert_eq!(encode_toon_value(&tv, 0, 2, ","), "{}");
    }

    #[test]
    fn test_encode_dict_simple() {
        let mut map = IndexMap::new();
        map.insert("name".to_string(), ToonValue::String("Alice".to_string()));
        map.insert("age".to_string(), ToonValue::Integer(30));
        let tv = ToonValue::Dict(map);
        assert_eq!(
            encode_toon_value(&tv, 0, 2, ","),
            "\n  name: Alice\n  age: 30"
        );
    }

    #[test]
    fn test_encode_list_empty() {
        let tv = ToonValue::List(vec![]);
        assert_eq!(encode_toon_value(&tv, 0, 2, ","), "[0]:");
    }

    #[test]
    fn test_encode_list_primitives() {
        let tv = ToonValue::List(vec![
            ToonValue::Integer(1),
            ToonValue::String("two".to_string()),
            ToonValue::Boolean(true),
        ]);
        assert_eq!(encode_toon_value(&tv, 0, 2, ","), "[3]: 1,two,true");
    }

    #[test]
    fn test_encode_tabular() {
        let mut row1 = IndexMap::new();
        row1.insert("a".to_string(), ToonValue::Integer(1));
        row1.insert("b".to_string(), ToonValue::Integer(2));

        let mut row2 = IndexMap::new();
        row2.insert("a".to_string(), ToonValue::Integer(3));
        row2.insert("b".to_string(), ToonValue::Integer(4));

        let tv = ToonValue::List(vec![ToonValue::Dict(row1), ToonValue::Dict(row2)]);
        // Keys should be sorted in encoding: a, b
        let output = encode_toon_value(&tv, 0, 2, ",");
        assert!(output.starts_with("[2]{a,b}:"));
        assert!(output.contains("  1,2"));
        assert!(output.contains("  3,4"));
    }

    #[test]
    fn test_encode_regular_list() {
        // List of lists
        let tv = ToonValue::List(vec![
            ToonValue::List(vec![ToonValue::Integer(1)]),
            ToonValue::List(vec![ToonValue::Integer(2)]),
        ]);
        let output = encode_toon_value(&tv, 0, 2, ",");
        assert!(output.starts_with("[2] :"));
        assert!(output.contains("  -"));
        assert!(output.contains("[1]: 1"));
    }

    #[test]
    fn test_encode_array_key_optimization() {
        let mut map = IndexMap::new();
        map.insert(
            "data".to_string(),
            ToonValue::List(vec![ToonValue::Integer(1), ToonValue::Integer(2)]),
        );
        let tv = ToonValue::Dict(map);
        let output = encode_toon_value(&tv, 0, 2, ",");
        // Expect "  data[2]: 1,2" instead of "  data: [2]: 1,2"
        assert!(output.contains("  data[2]: 1,2"));
    }

    #[test]
    fn test_encode_string_special_chars() {
        let chars = vec![":", "[", "]", "{", "}", ","];
        for c in chars {
            let tv = ToonValue::String(c.to_string());
            let output = encode_toon_value(&tv, 0, 2, ",");
            assert_eq!(output, format!("\"{}\"", c));
        }
    }

    #[test]
    fn test_encode_toon_root() {
        let mut map = IndexMap::new();
        map.insert("key".to_string(), ToonValue::String("value".to_string()));
        let tv = ToonValue::Dict(map);
        let output = encode_toon_root(&tv, 2, ",");
        assert_eq!(output, "key: value"); // Root dict has no leading newline and no indent
    }
}
