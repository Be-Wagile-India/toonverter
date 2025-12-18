use rayon::prelude::*;
use std::fmt::Write;

use crate::ir::ToonValue;

struct ToonWriter<'a> {
    buf: &'a mut String,
    indent_size: usize,
    delimiter: &'a str,
    indent_level: usize,
}

impl<'a> ToonWriter<'a> {
    fn new(buf: &'a mut String, indent_size: usize, delimiter: &'a str) -> Self {
        Self {
            buf,
            indent_size,
            delimiter,
            indent_level: 0,
        }
    }

    fn with_indent<F>(&mut self, level: usize, f: F) -> std::fmt::Result
    where
        F: FnOnce(&mut Self) -> std::fmt::Result,
    {
        let prev_level = self.indent_level;
        self.indent_level = level;
        let res = f(self);
        self.indent_level = prev_level;
        res
    }

    fn write_indent(&mut self, level: usize) {
        for _ in 0..(level * self.indent_size) {
            self.buf.push(' ');
        }
    }

    fn encode_inline(&mut self, value: &ToonValue) -> std::fmt::Result {
        match value {
            ToonValue::Dict(map) => {
                if map.is_empty() {
                    write!(self.buf, "{{}}")?;
                    return Ok(());
                }
                write!(self.buf, "{{")?;
                let mut first = true;
                for (k, v) in map {
                    if !first {
                        write!(self.buf, ", ")?;
                    }
                    first = false;
                    write!(self.buf, "{}: ", k)?;
                    self.encode_inline(v)?;
                }
                write!(self.buf, "}}")?;
            }
            ToonValue::List(list) => {
                let len = list.len();
                let delimiter_char = if self.delimiter == "," {
                    ""
                } else {
                    self.delimiter
                };

                write!(self.buf, "[{}]{}:", len, delimiter_char)?;
                if !list.is_empty() {
                    write!(self.buf, " ")?;
                    let mut first = true;
                    for v in list {
                        if !first {
                            write!(self.buf, "{}", self.delimiter)?;
                        }
                        first = false;
                        self.encode_inline(v)?;
                    }
                }
            }
            _ => {
                // For primitive types, reuse encode_value but with 0 indent context
                // We must be careful not to write newlines or indentation here.
                // encode_value writes primitives directly without indent/newlines usually.
                self.encode_value(value)?;
            }
        }
        Ok(())
    }

    fn encode_value(&mut self, value: &ToonValue) -> std::fmt::Result {
        match value {
            ToonValue::Null => write!(self.buf, "null")?,
            ToonValue::Boolean(b) => write!(self.buf, "{}", b)?,
            ToonValue::Integer(i) => write!(self.buf, "{}", i)?,
            ToonValue::BigInteger(bi) => write!(self.buf, "{}", bi)?,
            ToonValue::Float(f) => {
                if f.is_nan() || f.is_infinite() {
                    write!(self.buf, "null")?;
                } else if *f == 0.0 && f.is_sign_negative() {
                    write!(self.buf, "0")?;
                } else {
                    write!(self.buf, "{}", f)?;
                }
            }
            ToonValue::String(s) => {
                let is_reserved = matches!(s.as_str(), "true" | "false" | "null");
                let is_number = s.parse::<f64>().is_ok();
                let has_special_chars = s
                    .chars()
                    .any(|c| matches!(c, ':' | ' ' | '\n' | '[' | ']' | '{' | '}' | ','))
                    || s.is_empty()
                    || s.contains(self.delimiter);

                if is_reserved || is_number || has_special_chars {
                    write!(self.buf, "{:?}", s)?;
                } else {
                    self.buf.push_str(s);
                }
            }
            ToonValue::Dict(map) => {
                if map.is_empty() {
                    write!(self.buf, "{{}}")?;
                    return Ok(());
                }

                let mut first_item = true;
                for (k, v) in map {
                    if !first_item {
                        self.buf.push('\n');
                    }
                    first_item = false;

                    let mut temp_val_buf = String::new();
                    let target_level = if let ToonValue::List(_) = v {
                        self.indent_level
                    } else {
                        self.indent_level + 1
                    };

                    {
                        let mut sub_writer =
                            ToonWriter::new(&mut temp_val_buf, self.indent_size, self.delimiter);
                        sub_writer.with_indent(target_level, |w| w.encode_value(v))?;
                    }

                    if let ToonValue::List(_) = v {
                        if temp_val_buf.starts_with('[') {
                            self.write_indent(self.indent_level);
                            write!(self.buf, "{}{}", k, temp_val_buf)?;
                            continue;
                        }
                    }

                    self.write_indent(self.indent_level);
                    write!(self.buf, "{}:", k)?;

                    if temp_val_buf.starts_with('\n') || temp_val_buf.starts_with(' ') {
                        if !temp_val_buf.starts_with('\n') {
                            self.buf.push('\n');
                        }
                        self.buf.push_str(&temp_val_buf);
                    } else {
                        self.buf.push(' ');
                        self.buf.push_str(&temp_val_buf);
                    }
                }
            }
            ToonValue::List(list) => {
                let len = list.len();
                let mut is_tabular = true;
                let mut keys: Option<Vec<String>> = None;

                for item in list.iter() {
                    match item {
                        ToonValue::Dict(_) => {}
                        _ => {
                            is_tabular = false;
                            break;
                        }
                    }
                }

                if is_tabular && !list.is_empty() {
                    for item in list.iter() {
                        if let ToonValue::Dict(d) = item {
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
                    if let ToonValue::Dict(first_dict) = &list[0] {
                        let fields: Vec<String> = first_dict.keys().cloned().collect();
                        let delimiter_char = if self.delimiter == "," {
                            ""
                        } else {
                            self.delimiter
                        };

                        write!(
                            self.buf,
                            "[{}]{}{{{}}}:",
                            len,
                            delimiter_char,
                            fields.join(self.delimiter)
                        )?;
                        self.buf.push('\n');

                        // Capture needed values for closure
                        let indent_level = self.indent_level;
                        let indent_size = self.indent_size;
                        let delimiter = self.delimiter;

                        let rows: Vec<String> = list
                            .par_iter()
                            .map(|item| {
                                let mut row_buf = String::new();
                                // Manual indent writing since we are in a closure
                                for _ in 0..((indent_level + 1) * indent_size) {
                                    row_buf.push(' ');
                                }

                                if let ToonValue::Dict(d) = item {
                                    let mut first_field = true;
                                    for f in &fields {
                                        if !first_field {
                                            row_buf.push_str(delimiter);
                                        }
                                        first_field = false;
                                        if let Some(v) = d.get(f) {
                                            // Create temporary writer for inline value
                                            let mut w = ToonWriter::new(
                                                &mut row_buf,
                                                indent_size,
                                                delimiter,
                                            );
                                            w.encode_inline(v)
                                                .expect("Failed to write inline value");
                                        } else {
                                            row_buf.push_str("null");
                                        }
                                    }
                                    row_buf
                                } else {
                                    String::new()
                                }
                            })
                            .collect();
                        for row in rows {
                            self.buf.push_str(&row);
                            self.buf.push('\n');
                        }
                    }
                } else {
                    let all_primitive = list
                        .iter()
                        .all(|item| !matches!(item, ToonValue::Dict(_) | ToonValue::List(_)));

                    if all_primitive {
                        let delimiter_char = if self.delimiter == "," {
                            ""
                        } else {
                            self.delimiter
                        };
                        write!(self.buf, "[{}]{}:", len, delimiter_char)?;
                        if !list.is_empty() {
                            self.buf.push(' ');
                            let mut first_item = true;
                            for item in list {
                                if !first_item {
                                    write!(self.buf, "{}", self.delimiter)?;
                                }
                                first_item = false;
                                self.encode_value(item)?;
                            }
                        }
                    } else {
                        write!(self.buf, "[{}] :", len)?;
                        self.buf.push('\n');
                        for item in list {
                            self.write_indent(self.indent_level + 1);
                            write!(self.buf, "  - ")?;
                            self.with_indent(self.indent_level + 2, |w| w.encode_value(item))?;
                            self.buf.push('\n');
                        }
                    }
                }
            }
        }
        Ok(())
    }
}

pub fn encode_toon_root(value: &ToonValue, indent_size: usize, delimiter: &str) -> String {
    let mut buf = String::with_capacity(4096);
    {
        let mut writer = ToonWriter::new(&mut buf, indent_size, delimiter);
        writer
            .encode_value(value)
            .expect("Failed to write to string buffer");
    }

    if let ToonValue::Dict(_) = value {
        if buf.starts_with('\n') {
            buf.remove(0);
        }
    }
    buf.trim_end().to_string()
}

#[cfg(test)]
mod tests {
    use super::*;
    use indexmap::IndexMap;
    use num_bigint::BigInt;

    fn encode_test_value(value: &ToonValue, indent_size: usize, delimiter: &str) -> String {
        let mut buf = String::new();
        {
            let mut writer = ToonWriter::new(&mut buf, indent_size, delimiter);
            writer
                .encode_value(value)
                .expect("Failed to encode for test");
        }
        buf.trim_end().to_string()
    }

    fn encode_inline_test(value: &ToonValue, delimiter: &str) -> String {
        let mut buf = String::new();
        {
            let mut writer = ToonWriter::new(&mut buf, 2, delimiter);
            writer
                .encode_inline(value)
                .expect("Failed to encode inline");
        }
        buf
    }

    #[test]
    fn test_encode_inline_nested() {
        let mut child_map = IndexMap::new();
        child_map.insert("a".to_string(), ToonValue::Integer(1));
        let mut map = IndexMap::new();
        map.insert("nested".to_string(), ToonValue::Dict(child_map));
        let tv = ToonValue::Dict(map);
        assert_eq!(encode_inline_test(&tv, ","), "{nested: {a: 1}}");
    }

    #[test]
    fn test_encode_null() {
        let tv = ToonValue::Null;
        assert_eq!(encode_test_value(&tv, 2, ","), "null");
    }

    #[test]
    fn test_encode_boolean() {
        let tv_true = ToonValue::Boolean(true);
        let tv_false = ToonValue::Boolean(false);
        assert_eq!(encode_test_value(&tv_true, 2, ","), "true");
        assert_eq!(encode_test_value(&tv_false, 2, ","), "false");
    }

    #[test]
    fn test_encode_integer() {
        let tv = ToonValue::Integer(123);
        assert_eq!(encode_test_value(&tv, 2, ","), "123");
    }

    #[test]
    fn test_encode_float() {
        let tv = ToonValue::Float(123.45);
        assert_eq!(encode_test_value(&tv, 2, ","), "123.45");
    }

    #[test]
    fn test_encode_float_nan() {
        let tv = ToonValue::Float(f64::NAN);
        assert_eq!(encode_test_value(&tv, 2, ","), "null");
    }

    #[test]
    fn test_encode_float_infinity() {
        let tv_pos = ToonValue::Float(f64::INFINITY);
        let tv_neg = ToonValue::Float(f64::NEG_INFINITY);
        assert_eq!(encode_test_value(&tv_pos, 2, ","), "null");
        assert_eq!(encode_test_value(&tv_neg, 2, ","), "null");
    }

    #[test]
    fn test_encode_float_negative_zero() {
        let tv = ToonValue::Float(-0.0);
        assert_eq!(encode_test_value(&tv, 2, ","), "0");
    }

    #[test]
    fn test_encode_string_simple() {
        let tv = ToonValue::String("hello".to_string());
        assert_eq!(encode_test_value(&tv, 2, ","), "hello");
    }

    #[test]
    fn test_encode_string_needs_quoting_space() {
        let tv = ToonValue::String("hello world".to_string());
        assert_eq!(encode_test_value(&tv, 2, ","), "\"hello world\"");
    }

    #[test]
    fn test_encode_string_needs_quoting_reserved() {
        let tv = ToonValue::String("true".to_string());
        assert_eq!(encode_test_value(&tv, 2, ","), "\"true\"");
    }

    #[test]
    fn test_encode_string_needs_quoting_number() {
        let tv = ToonValue::String("123".to_string());
        assert_eq!(encode_test_value(&tv, 2, ","), "\"123\"");
    }

    #[test]
    fn test_encode_string_special_chars() {
        let chars = vec![":", "[", "]", "{", "}", ","];
        for c in chars {
            let tv = ToonValue::String(c.to_string());
            let output = encode_test_value(&tv, 2, ",");
            assert_eq!(output, format!("\"{}\"", c));
        }
    }

    #[test]
    fn test_encode_dict_empty() {
        let tv = ToonValue::Dict(IndexMap::new());
        assert_eq!(encode_test_value(&tv, 2, ","), "{}");
    }

    #[test]
    fn test_encode_dict_simple() {
        let mut map = IndexMap::new();
        map.insert("name".to_string(), ToonValue::String("Alice".to_string()));
        map.insert("age".to_string(), ToonValue::Integer(30));
        let tv = ToonValue::Dict(map);
        assert_eq!(encode_test_value(&tv, 2, ","), "name: Alice\nage: 30");
    }

    #[test]
    fn test_encode_list_empty() {
        let tv = ToonValue::List(vec![]);
        assert_eq!(encode_test_value(&tv, 2, ","), "[0]:");
    }

    #[test]
    fn test_encode_list_primitives() {
        let tv = ToonValue::List(vec![
            ToonValue::Integer(1),
            ToonValue::String("two".to_string()),
            ToonValue::Boolean(true),
        ]);
        assert_eq!(encode_test_value(&tv, 2, ","), "[3]: 1,two,true");
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
        let output = encode_test_value(&tv, 2, ",");
        assert!(output.starts_with("[2]{a,b}:\n"));
        assert!(output.contains("  1,2\n"));
        assert!(output.contains("  3,4"));
    }

    #[test]
    fn test_encode_regular_list() {
        let tv = ToonValue::List(vec![
            ToonValue::List(vec![ToonValue::Integer(1)]),
            ToonValue::List(vec![ToonValue::Integer(2)]),
        ]);
        let output = encode_test_value(&tv, 2, ",");
        assert!(output.starts_with("[2] :\n"));
        assert!(output.contains("    - [1]: 1\n"));
        assert!(output.contains("    - [1]: 2"));
    }

    #[test]
    fn test_encode_array_key_optimization() {
        let mut map = IndexMap::new();
        map.insert(
            "data".to_string(),
            ToonValue::List(vec![ToonValue::Integer(1), ToonValue::Integer(2)]),
        );
        let tv = ToonValue::Dict(map);
        let output = encode_test_value(&tv, 2, ",");
        assert_eq!(output, "data[2]: 1,2");
    }

    #[test]
    fn test_encode_toon_root() {
        let mut map = IndexMap::new();
        map.insert("key".to_string(), ToonValue::String("value".to_string()));
        let tv = ToonValue::Dict(map);
        let output = encode_toon_root(&tv, 2, ",");
        assert_eq!(output, "key: value");
    }

    #[test]
    fn test_encode_string_delimiter_clash() {
        let tv = ToonValue::String("val,ue".to_string());
        assert_eq!(encode_test_value(&tv, 2, ","), "\"val,ue\"");
    }

    #[test]
    fn test_encode_dict_nested_indent() {
        let mut inner = IndexMap::new();
        inner.insert("k".to_string(), ToonValue::Integer(1));
        let mut outer = IndexMap::new();
        outer.insert("outer".to_string(), ToonValue::Dict(inner));
        let tv = ToonValue::Dict(outer);
        let output = encode_test_value(&tv, 2, ",");
        assert_eq!(output, "outer:\n  k: 1");
    }

    #[test]
    fn test_encode_tabular_mismatched_keys() {
        let mut row1 = IndexMap::new();
        row1.insert("a".to_string(), ToonValue::Integer(1));
        let mut row2 = IndexMap::new();
        row2.insert("b".to_string(), ToonValue::Integer(2));

        let tv = ToonValue::List(vec![ToonValue::Dict(row1), ToonValue::Dict(row2)]);
        let output = encode_test_value(&tv, 2, ",");
        assert!(output.contains("a: 1"));
        assert!(output.contains("b: 2"));
    }

    #[test]
    fn test_encode_custom_delimiter() {
        let tv = ToonValue::List(vec![ToonValue::Integer(1), ToonValue::Integer(2)]);
        let output = encode_test_value(&tv, 2, "|");
        assert_eq!(output, "[2]|: 1|2");
    }

    #[test]
    fn test_encode_bigint() {
        let bi = BigInt::from(100);
        let tv = ToonValue::BigInteger(bi);
        let output = encode_test_value(&tv, 2, ",");
        assert_eq!(output, "100");
    }
}
