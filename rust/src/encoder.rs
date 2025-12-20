use rayon::prelude::*;
use std::fmt::Write;

use crate::ir::ToonValue;

#[derive(Clone, Debug)]
pub struct ToonEncodeOptions {
    pub indent_size: usize,
    pub delimiter: String,
}

impl Default for ToonEncodeOptions {
    fn default() -> Self {
        Self {
            indent_size: 2,
            delimiter: ",".to_string(),
        }
    }
}

pub struct ToonEncoderRequest<'a> {
    pub value: &'a ToonValue,
    pub options: &'a ToonEncodeOptions,
}

pub struct ToonEncoderResponse {
    pub toon_string: String,
}

struct ToonWriter<'a> {
    buf: &'a mut String,
    options: &'a ToonEncodeOptions,
    indent_level: usize,
}

fn format_dict_entry(
    k: &str,
    v: &ToonValue,
    indent_level: usize,
    options: &ToonEncodeOptions,
) -> Result<String, std::fmt::Error> {
    let mut entry_buf = String::new();
    let mut temp_val_buf = String::new();

    let target_level = if let ToonValue::List(_) = v {
        indent_level
    } else {
        indent_level + 1
    };

    {
        let mut sub_writer = ToonWriter::new(&mut temp_val_buf, options);
        sub_writer.with_indent(target_level, |w| w.encode_value(v))?;
    }

    // Indentation helper
    let write_indent = |buf: &mut String, lvl: usize| {
        for _ in 0..(lvl * options.indent_size) {
            buf.push(' ');
        }
    };

    if let ToonValue::List(_) = v {
        if temp_val_buf.starts_with('[') {
            write_indent(&mut entry_buf, indent_level);
            write!(entry_buf, "{}{}", k, temp_val_buf)?;
            return Ok(entry_buf);
        }
    }

    write_indent(&mut entry_buf, indent_level);
    write!(entry_buf, "{}:", k)?;

    if temp_val_buf.starts_with('\n') || temp_val_buf.starts_with(' ') {
        if !temp_val_buf.starts_with('\n') {
            entry_buf.push('\n');
        }
        entry_buf.push_str(&temp_val_buf);
    } else {
        entry_buf.push(' ');
        entry_buf.push_str(&temp_val_buf);
    }

    Ok(entry_buf)
}

impl<'a> ToonWriter<'a> {
    fn new(buf: &'a mut String, options: &'a ToonEncodeOptions) -> Self {
        Self {
            buf,
            options,
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
        for _ in 0..(level * self.options.indent_size) {
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
                let delimiter_char = if self.options.delimiter == "," {
                    ""
                } else {
                    &self.options.delimiter
                };

                write!(self.buf, "[{}]{}:", len, delimiter_char)?;
                if !list.is_empty() {
                    write!(self.buf, " ")?;
                    let mut first_item = true;
                    for v in list {
                        if !first_item {
                            write!(self.buf, "{}", self.options.delimiter)?;
                        }
                        first_item = false;
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
                    || s.contains(&self.options.delimiter);

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

                if map.len() > 1000 {
                    let indent_level = self.indent_level;
                    let options = self.options.clone();

                    let items: Vec<String> = map
                        .par_iter()
                        .map(|(k, v)| {
                            format_dict_entry(k, v, indent_level, &options)
                                .expect("Failed to encode dict entry")
                        })
                        .collect();

                    for (i, item) in items.iter().enumerate() {
                        if i > 0 {
                            self.buf.push('\n');
                        }
                        self.buf.push_str(item);
                    }
                } else {
                    let mut first_item = true;
                    for (k, v) in map {
                        if !first_item {
                            self.buf.push('\n');
                        }
                        first_item = false;
                        let item_str = format_dict_entry(k, v, self.indent_level, self.options)?;
                        self.buf.push_str(&item_str);
                    }
                }
            }
            ToonValue::List(list) => {
                let len = list.len();
                let mut is_tabular = true;
                let mut keys: Option<Vec<String>> = None;

                for item in list.iter() {
                    match item {
                        ToonValue::Dict(_) => {} // Continue checking
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
                        let delimiter_char = if self.options.delimiter == "," {
                            ""
                        } else {
                            &self.options.delimiter
                        };

                        write!(
                            self.buf,
                            "[{}]{}{{{}}}:",
                            len,
                            delimiter_char,
                            fields.join(&self.options.delimiter)
                        )?;
                        self.buf.push('\n');

                        // Capture needed values for closure
                        let indent_level = self.indent_level;
                        let options = self.options.clone();

                        let rows: Vec<String> = list
                            .par_iter()
                            .map(|item| {
                                let mut row_buf = String::new();
                                // Manual indent writing since we are in a closure
                                for _ in 0..((indent_level + 1) * options.indent_size) {
                                    row_buf.push(' ');
                                }

                                if let ToonValue::Dict(d) = item {
                                    let mut first_field = true;
                                    for f in &fields {
                                        if !first_field {
                                            row_buf.push_str(&options.delimiter);
                                        }
                                        first_field = false;
                                        if let Some(v) = d.get(f) {
                                            // Create temporary writer for inline value
                                            let mut w = ToonWriter::new(&mut row_buf, &options);
                                            w.encode_inline(v)
                                                .expect("Failed to write inline value");
                                        } else {
                                            row_buf.push_str("null");
                                        }
                                    }
                                    row_buf
                                } else {
                                    String::new() // Should not happen if is_tabular is true
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
                        let delimiter_char = if self.options.delimiter == "," {
                            ""
                        } else {
                            &self.options.delimiter
                        };
                        write!(self.buf, "[{}]{}:", len, delimiter_char)?;
                        if !list.is_empty() {
                            self.buf.push(' ');
                            let mut first_item = true;
                            for item in list {
                                if !first_item {
                                    write!(self.buf, "{}", self.options.delimiter)?;
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

pub fn encode_toon_root(request: ToonEncoderRequest) -> ToonEncoderResponse {
    let mut buf = String::with_capacity(4096);
    {
        let mut writer = ToonWriter::new(&mut buf, request.options);
        writer
            .encode_value(request.value)
            .expect("Failed to write to string buffer");
    }

    if let ToonValue::Dict(_) = request.value {
        if buf.starts_with('\n') {
            buf.remove(0);
        }
    }
    ToonEncoderResponse {
        toon_string: buf.trim_end().to_string(),
    }
}

pub fn encode_tabular_columns(
    count: usize,
    columns: Vec<String>,
    data: Vec<Vec<ToonValue>>,
    indent_size: usize,
    delimiter: &str,
) -> String {
    if count == 0 {
        return "[0]:".to_string();
    }
    let mut buf = String::with_capacity(count * columns.len() * 10);
    let delimiter_char = if delimiter == "," { "" } else { delimiter };

    write!(
        buf,
        "[{}]{}{{{}}}:",
        count,
        delimiter_char,
        columns.join(delimiter)
    )
    .unwrap();
    buf.push('\n');

    // Create a temporary options struct for the writers
    // This function still takes primitives for FFI simplicity, but uses the struct internally for writers
    let options = ToonEncodeOptions {
        indent_size,
        delimiter: delimiter.to_string(),
    };

    let indent_str = " ".repeat(indent_size);

    // Parallel processing for large datasets
    if count > 1000 {
        let rows: Vec<String> = (0..count)
            .into_par_iter()
            .map(|i| {
                let mut row_buf = String::new();
                row_buf.push_str(&indent_str);
                let mut first_col = true;
                for col in &data {
                    if !first_col {
                        row_buf.push_str(delimiter);
                    }
                    first_col = false;
                    let val = &col[i];
                    // Temporary writer for value
                    let mut temp_val = String::new();
                    let mut writer = ToonWriter::new(&mut temp_val, &options);
                    writer.encode_inline(val).unwrap();
                    row_buf.push_str(&temp_val);
                }
                row_buf
            })
            .collect();

        for row in rows {
            buf.push_str(&row);
            buf.push('\n');
        }
    } else {
        let mut col_iters: Vec<_> = data.iter().map(|c| c.iter()).collect();
        for _ in 0..count {
            buf.push_str(&indent_str);
            let mut first_col = true;
            for iter in &mut col_iters {
                if !first_col {
                    buf.push_str(delimiter);
                }
                first_col = false;
                let val = iter.next().expect("Data length mismatch");
                let mut writer = ToonWriter::new(&mut buf, &options);
                writer.encode_inline(val).unwrap();
            }
            buf.push('\n');
        }
    }

    buf.trim_end().to_string()
}

pub fn encode_tabular_rows(
    count: usize,
    columns: Vec<String>,
    rows: Vec<Vec<ToonValue>>,
    indent_size: usize,
    delimiter: &str,
) -> String {
    if count == 0 {
        return "[0]:".to_string();
    }
    let mut buf = String::with_capacity(count * columns.len() * 10);
    let delimiter_char = if delimiter == "," { "" } else { delimiter };

    write!(
        buf,
        "[{}]{}{{{}}}:",
        count,
        delimiter_char,
        columns.join(delimiter)
    )
    .unwrap();
    buf.push('\n');

    let options = ToonEncodeOptions {
        indent_size,
        delimiter: delimiter.to_string(),
    };

    let indent_str = " ".repeat(indent_size);

    if count > 1000 {
        let encoded_rows: Vec<String> = rows
            .par_iter()
            .map(|row| {
                let mut row_buf = String::new();
                row_buf.push_str(&indent_str);
                let mut first_col = true;
                for val in row {
                    if !first_col {
                        row_buf.push_str(delimiter);
                    }
                    first_col = false;
                    let mut temp_val = String::new();
                    let mut writer = ToonWriter::new(&mut temp_val, &options);
                    writer.encode_inline(val).unwrap();
                    row_buf.push_str(&temp_val);
                }
                // Handle missing columns with nulls if row is short (though usually it matches)
                for _ in 0..(columns.len().saturating_sub(row.len())) {
                    if !first_col {
                        row_buf.push_str(delimiter);
                    }
                    row_buf.push_str("null");
                }
                row_buf
            })
            .collect();

        for r in encoded_rows {
            buf.push_str(&r);
            buf.push('\n');
        }
    } else {
        for row in rows {
            buf.push_str(&indent_str);
            let mut first_col = true;
            for val in &row {
                if !first_col {
                    buf.push_str(delimiter);
                }
                first_col = false;
                let mut writer = ToonWriter::new(&mut buf, &options);
                writer.encode_inline(val).unwrap();
            }
            for _ in 0..(columns.len().saturating_sub(row.len())) {
                if !first_col {
                    buf.push_str(delimiter);
                }
                buf.push_str("null");
            }
            buf.push('\n');
        }
    }

    buf.trim_end().to_string()
}

#[cfg(test)]
mod tests {
    use super::*;
    use indexmap::IndexMap;
    use num_bigint::BigInt;

    fn get_test_options(indent_size: usize, delimiter: &str) -> ToonEncodeOptions {
        ToonEncodeOptions {
            indent_size,
            delimiter: delimiter.to_string(),
        }
    }

    fn encode_test_value(value: &ToonValue, indent_size: usize, delimiter: &str) -> String {
        let mut buf = String::new();
        let options = get_test_options(indent_size, delimiter);
        {
            let mut writer = ToonWriter::new(&mut buf, &options);
            writer
                .encode_value(value)
                .expect("Failed to encode for test");
        }
        buf.trim_end().to_string()
    }

    fn encode_inline_test(value: &ToonValue, delimiter: &str) -> String {
        let mut buf = String::new();
        let options = get_test_options(2, delimiter);
        {
            let mut writer = ToonWriter::new(&mut buf, &options);
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
        let options = get_test_options(2, ",");
        let request = ToonEncoderRequest {
            value: &tv,
            options: &options,
        };
        let output = encode_toon_root(request);
        assert_eq!(output.toon_string, "key: value");
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

    #[test]
    fn test_encode_large_dict_parallel() {
        let mut map = IndexMap::new();
        // Create enough items to trigger parallelism (> 1000)
        for i in 0..1500 {
            map.insert(format!("key_{}", i), ToonValue::Integer(i));
        }
        let tv = ToonValue::Dict(map);

        // Encode
        let output = encode_test_value(&tv, 2, ",");

        // Verify output structure
        // It should contain all keys. Since IndexMap preserves order, we can check a few.
        assert!(output.contains("key_0: 0"));
        assert!(output.contains("key_1499: 1499"));

        // Count lines to ensure we have all items
        let line_count = output.lines().count();
        assert_eq!(line_count, 1500);
    }

    #[test]
    fn test_encode_tabular_columns_small() {
        let columns = vec!["a".to_string(), "b".to_string()];
        let data = vec![
            vec![ToonValue::Integer(1), ToonValue::Integer(2)],
            vec![ToonValue::Integer(3), ToonValue::Integer(4)],
        ];
        let output = encode_tabular_columns(2, columns, data, 2, ",");
        assert_eq!(output, "[2]{a,b}:\n  1,3\n  2,4");
    }

    #[test]
    fn test_encode_tabular_columns_large_parallel() {
        let count = 1500;
        let columns = vec!["id".to_string(), "val".to_string()];
        let col1 = (0..count).map(|i| ToonValue::Integer(i as i64)).collect();
        let col2 = (0..count)
            .map(|i| ToonValue::String(format!("v{}", i)))
            .collect();
        let data = vec![col1, col2];

        let output = encode_tabular_columns(count, columns, data, 2, ",");
        assert!(output.starts_with("[1500]{id,val}:\n"));
        assert!(output.contains("  0,v0\n"));
        assert!(output.contains("  1499,v1499"));
        assert_eq!(output.lines().count(), count + 1);
    }

    #[test]
    fn test_encode_tabular_rows_small() {
        let columns = vec!["a".to_string(), "b".to_string()];
        let rows = vec![
            vec![ToonValue::Integer(1), ToonValue::Integer(2)],
            vec![ToonValue::Integer(3), ToonValue::Integer(4)],
        ];
        let output = encode_tabular_rows(2, columns, rows, 2, ",");
        assert_eq!(output, "[2]{a,b}:\n  1,2\n  3,4");
    }

    #[test]
    fn test_encode_tabular_rows_large_parallel() {
        let count = 1500;
        let columns = vec!["a".to_string(), "b".to_string()];
        let rows = (0..count)
            .map(|i| vec![ToonValue::Integer(i as i64), ToonValue::Integer(i as i64)])
            .collect();

        let output = encode_tabular_rows(count, columns, rows, 2, ",");
        assert!(output.starts_with("[1500]{a,b}:\n"));
        assert!(output.contains("  0,0\n"));
        assert!(output.contains("  1499,1499"));
        assert_eq!(output.lines().count(), count + 1);
    }

    #[test]
    fn test_encode_tabular_rows_mismatch_padding() {
        let columns = vec!["a".to_string(), "b".to_string()];
        // Row 2 only has one element
        let rows = vec![
            vec![ToonValue::Integer(1), ToonValue::Integer(2)],
            vec![ToonValue::Integer(3)],
        ];
        let output = encode_tabular_rows(2, columns, rows, 2, ",");
        assert_eq!(output, "[2]{a,b}:\n  1,2\n  3,null");
    }

    #[test]
    fn test_encode_tabular_empty() {
        let columns = vec!["a".to_string()];
        let output = encode_tabular_columns(0, columns.clone(), vec![], 2, ",");
        assert_eq!(output, "[0]:");

        let output_rows = encode_tabular_rows(0, columns, vec![], 2, ",");
        assert_eq!(output_rows, "[0]:");
    }
}
