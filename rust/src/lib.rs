use indexmap::IndexMap;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyAny, PyDict, PyList, PyString};
use rayon::prelude::*;

// For buffered token stream
use std::collections::VecDeque;

// --- Data Structures ---

#[derive(Debug, PartialEq, Clone)]
enum TokenType {
    Indent,
    Dedent,
    Newline,
    Eof,
    String(String),
    Integer(i64),
    Float(f64),
    Boolean(bool),
    Null,
    Colon,      // :
    Comma,      // ,
    Dash,       // -
    ArrayStart, // [
    ArrayEnd,   // ]
    BraceStart, // {
    BraceEnd,   // }
    Identifier(String),
}

#[derive(Debug, Clone)]
struct Token {
    token_type: TokenType,
    line: usize,
    column: usize,
    indent_level: usize,
}

// --- Intermediate Representation for Parallel Encoding ---

#[derive(Debug, PartialEq, Clone)]
enum ToonValue {
    Null,
    Boolean(bool),
    Integer(i64),
    Float(f64),
    String(String),
    List(Vec<ToonValue>),
    Dict(IndexMap<String, ToonValue>),
}

impl ToonValue {
    fn encode(&self, indent_level: usize, indent_size: usize) -> String {
        match self {
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
                    let v_str = v.encode(indent_level + 1, indent_size);
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
                        ToonValue::Dict(_) => {}
                        _ => {
                            is_tabular = false;
                        }
                    }
                    match item {
                        ToonValue::Dict(_) | ToonValue::List(_) => {
                            all_primitive = false;
                        }
                        _ => {}
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
                                    _ => {}
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
                                            row_vals.push(v.encode(0, 0));
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
                    let parts: Vec<String> =
                        list.par_iter().map(|item| item.encode(0, 0)).collect();

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
                            let val_str = item.encode(indent_level + 2, indent_size);
                            if val_str.starts_with('\n') {
                                format!("{}  -\n{}", item_indent, val_str)
                            } else {
                                format!("{}  - {}", item_indent, val_str)
                            }
                        })
                        .collect();

                    let mut list_lines = Vec::new();
                    list_lines.push(format!("[{}]:", len));
                    list_lines.extend(encoded_items);
                    list_lines.join("\n")
                }
            }
        }
    }
}

// --- Conversion from Python to IR ---

fn to_toon_value(obj: &Bound<'_, PyAny>) -> PyResult<ToonValue> {
    if obj.is_none() {
        Ok(ToonValue::Null)
    } else if let Ok(b) = obj.extract::<bool>() {
        Ok(ToonValue::Boolean(b))
    } else if let Ok(i) = obj.extract::<i64>() {
        Ok(ToonValue::Integer(i))
    } else if let Ok(f) = obj.extract::<f64>() {
        Ok(ToonValue::Float(f))
    } else if let Ok(s) = obj.extract::<String>() {
        Ok(ToonValue::String(s))
    } else if let Ok(dict) = obj.downcast::<PyDict>() {
        let mut map = IndexMap::new();
        for (k, v) in dict {
            let k_str = k.extract::<String>()?;
            let v_val = to_toon_value(&v)?;
            map.insert(k_str, v_val);
        }
        Ok(ToonValue::Dict(map))
    } else if let Ok(list) = obj.downcast::<PyList>() {
        let mut vec = Vec::with_capacity(list.len());
        for item in list {
            vec.push(to_toon_value(&item)?);
        }
        Ok(ToonValue::List(vec))
    } else if let Ok(py_str) = obj.downcast::<PyString>() {
        // Only accept *actual* Python string objects here.
        Ok(ToonValue::String(py_str.to_str()?.to_string()))
    } else {
        Err(PyValueError::new_err("Unsupported type for TOON encoding"))
    }
}

// --- Lexer ---

struct ToonLexer<'a> {
    lines: std::str::Lines<'a>,
    current_line_chars: std::iter::Peekable<std::str::Chars<'a>>,
    current_line_str: &'a str,
    current_line_idx: usize,
    current_column: usize,
    current_indent_level: usize,
    indent_size: usize,
    pending_dedents: usize,
    eof_reached: bool,
}

impl<'a> ToonLexer<'a> {
    fn new(text: &'a str, indent_size: usize) -> Self {
        let mut lines = text.lines();
        let first_line = lines.next().unwrap_or("");

        ToonLexer {
            lines,
            current_line_chars: first_line.chars().peekable(),
            current_line_str: first_line,
            current_line_idx: 0,
            current_column: 0,
            current_indent_level: 0,
            indent_size,
            pending_dedents: 0,
            eof_reached: text.is_empty(),
        }
    }

    fn peek_char(&mut self) -> Option<&char> {
        self.current_line_chars.peek()
    }

    fn next_char(&mut self) -> Option<char> {
        if let Some(c) = self.current_line_chars.next() {
            self.current_column += 1;
            Some(c)
        } else if let Some(next_line) = self.lines.next() {
            self.current_line_idx += 1;
            self.current_column = 0;
            self.current_line_str = next_line;
            self.current_line_chars = next_line.chars().peekable();
            Some('\n')
        } else {
            self.eof_reached = true;
            None
        }
    }

    fn consume_whitespace(&mut self) {
        while let Some(&c) = self.peek_char() {
            if c == ' ' || c == '\t' {
                self.next_char();
            } else {
                break;
            }
        }
    }

    fn detect_indentation(&self) -> PyResult<usize> {
        let mut spaces = 0;
        for c in self.current_line_str.chars() {
            if c == ' ' {
                spaces += 1;
            } else if c == '\t' {
                return Err(PyValueError::new_err(
                    "Tabs are not allowed for indentation",
                ));
            } else {
                break;
            }
        }
        Ok(spaces / self.indent_size)
    }

    fn scan_string(&mut self, _start_col: usize) -> PyResult<TokenType> {
        // Simple owned-string scanner that handles escapes
        let mut s = String::new();
        let mut escaped = false;
        loop {
            let c = match self.next_char() {
                Some(ch) => ch,
                None => return Err(PyValueError::new_err("Unterminated quoted string")),
            };
            if escaped {
                match c {
                    '\\' => s.push('\\'),
                    '"' => s.push('"'),
                    'n' => s.push('\n'),
                    'r' => s.push('\r'),
                    't' => s.push('\t'),
                    other => {
                        return Err(PyValueError::new_err(format!(
                            "Invalid escape character: {}",
                            other
                        )))
                    }
                }
                escaped = false;
            } else if c == '\\' {
                escaped = true;
            } else if c == '"' {
                return Ok(TokenType::String(s));
            } else {
                s.push(c);
            }
        }
    }

    fn scan_identifier_or_number(&mut self, first_char: char) -> TokenType {
        let mut s = String::new();
        s.push(first_char);

        while let Some(&c) = self.peek_char() {
            if c == ':'
                || c == ','
                || c == '['
                || c == ']'
                || c == '{'
                || c == '}'
                || c == ' '
                || c == '\t'
                || c == '\n'
            {
                break;
            }
            s.push(self.next_char().unwrap());
        }

        match s.as_str() {
            "true" => TokenType::Boolean(true),
            "false" => TokenType::Boolean(false),
            "null" => TokenType::Null,
            _ => {
                if let Ok(i) = s.parse::<i64>() {
                    TokenType::Integer(i)
                } else if let Ok(f) = s.parse::<f64>() {
                    TokenType::Float(f)
                } else {
                    TokenType::Identifier(s)
                }
            }
        }
    }

    fn next_token(&mut self) -> PyResult<Option<Token>> {
        if self.pending_dedents > 0 {
            self.pending_dedents -= 1;
            self.current_indent_level -= 1;
            return Ok(Some(Token {
                token_type: TokenType::Dedent,
                line: self.current_line_idx,
                column: 0,
                indent_level: self.current_indent_level,
            }));
        }

        if self.eof_reached {
            if self.current_indent_level > 0 {
                self.pending_dedents = self.current_indent_level - 1;
                self.current_indent_level -= 1;
                return Ok(Some(Token {
                    token_type: TokenType::Dedent,
                    line: self.current_line_idx,
                    column: 0,
                    indent_level: self.current_indent_level,
                }));
            }
            return Ok(None);
        }

        if self.current_column == 0 {
            let trimmed = self.current_line_str.trim_start();
            if trimmed.is_empty() {
                self.next_char();
                return self.next_token();
            }

            let new_indent = self.detect_indentation()?;
            if new_indent > self.current_indent_level {
                self.current_indent_level += 1;
                return Ok(Some(Token {
                    token_type: TokenType::Indent,
                    line: self.current_line_idx,
                    column: 0,
                    indent_level: self.current_indent_level,
                }));
            } else if new_indent < self.current_indent_level {
                self.pending_dedents = self.current_indent_level - new_indent - 1;
                self.current_indent_level -= 1;
                return Ok(Some(Token {
                    token_type: TokenType::Dedent,
                    line: self.current_line_idx,
                    column: 0,
                    indent_level: self.current_indent_level,
                }));
            }
            self.consume_whitespace();
        }

        self.consume_whitespace();

        let c = if let Some(&c) = self.peek_char() {
            if c == '\n' {
                self.next_char();
                return Ok(Some(Token {
                    token_type: TokenType::Newline,
                    line: self.current_line_idx,
                    column: self.current_column,
                    indent_level: self.current_indent_level,
                }));
            }
            self.next_char().unwrap()
        } else {
            match self.next_char() {
                Some(c) => {
                    if c == '\n' {
                        return Ok(Some(Token {
                            token_type: TokenType::Newline,
                            line: self.current_line_idx,
                            column: self.current_column,
                            indent_level: self.current_indent_level,
                        }));
                    }
                    c
                }
                None => {
                    self.eof_reached = true;
                    return self.next_token();
                }
            }
        };

        let start_col = self.current_column;

        let token_type = match c {
            ':' => TokenType::Colon,
            ',' => TokenType::Comma,
            '[' => TokenType::ArrayStart,
            ']' => TokenType::ArrayEnd,
            '{' => TokenType::BraceStart,
            '}' => TokenType::BraceEnd,
            '-' => {
                if let Some(&next_c) = self.peek_char() {
                    if next_c.is_ascii_digit() {
                        self.scan_identifier_or_number('-')
                    } else {
                        TokenType::Dash
                    }
                } else {
                    TokenType::Dash
                }
            }
            '"' => self.scan_string(start_col)?,
            _ => self.scan_identifier_or_number(c),
        };

        Ok(Some(Token {
            token_type,
            line: self.current_line_idx,
            column: start_col,
            indent_level: self.current_indent_level,
        }))
    }
}

impl<'a> Iterator for ToonLexer<'a> {
    type Item = PyResult<Token>;

    fn next(&mut self) -> Option<Self::Item> {
        self.next_token().transpose()
    }
}

// --- Parser ---

struct ToonParser<'py, 'a> {
    py: Python<'py>,
    token_stream: ToonLexer<'a>,
    buffer: VecDeque<Token>,
}

impl<'py, 'a> ToonParser<'py, 'a> {
    fn new(py: Python<'py>, lexer: ToonLexer<'a>) -> Self {
        ToonParser {
            py,
            token_stream: lexer,
            buffer: VecDeque::new(),
        }
    }

    fn fill_buffer(&mut self, count: usize) -> PyResult<()> {
        while self.buffer.len() < count {
            if let Some(token_res) = self.token_stream.next() {
                self.buffer.push_back(token_res?);
            } else {
                if self.buffer.is_empty() {
                    self.buffer.push_back(Token {
                        token_type: TokenType::Eof,
                        line: 0,
                        column: 0,
                        indent_level: 0,
                    });
                }
                break; // EOF
            }
        }
        Ok(())
    }

    fn current(&mut self) -> PyResult<&Token> {
        self.fill_buffer(1)?;
        self.buffer
            .front()
            .ok_or_else(|| PyValueError::new_err("Unexpected end of token stream"))
    }

    fn advance(&mut self) -> PyResult<Token> {
        self.fill_buffer(1)?;
        self.buffer
            .pop_front()
            .ok_or_else(|| PyValueError::new_err("Unexpected end of token stream"))
    }

    fn peek_next(&mut self) -> PyResult<Option<&Token>> {
        self.fill_buffer(2)?;
        Ok(self.buffer.get(1))
    }

    fn parse_value(&mut self) -> PyResult<PyObject> {
        let token = self.current()?.clone();

        match token.token_type {
            TokenType::String(ref s) => {
                self.advance()?;
                Ok(PyString::new_bound(self.py, s).into_py(self.py))
            }
            TokenType::Integer(i) => {
                self.advance()?;
                Ok(i.into_py(self.py))
            }
            TokenType::Float(f) => {
                self.advance()?;
                Ok(f.into_py(self.py))
            }
            TokenType::Boolean(b) => {
                self.advance()?;
                Ok(b.into_py(self.py))
            }
            TokenType::Null => {
                self.advance()?;
                Ok(self.py.None())
            }
            TokenType::Identifier(ref s) => {
                self.advance()?;
                Ok(PyString::new_bound(self.py, s).into_py(self.py))
            }
            TokenType::ArrayStart => self.parse_array_header_and_content(),
            TokenType::BraceStart => self.parse_inline_object(),
            TokenType::Indent => {
                self.advance()?; // Consume the Indent token
                self.parse_object_indented()
            }
            TokenType::Dash => self.parse_list_content(),
            _ => Err(PyValueError::new_err(format!(
                "Unexpected token in value: {:?}",
                token.token_type
            ))),
        }
    }

    fn parse_array_header_and_content(&mut self) -> PyResult<PyObject> {
        self.advance()?; // skip [

        // Parse length
        let len_token = self.current()?.clone();
        let length = match len_token.token_type {
            TokenType::Integer(i) => i as usize,
            _ => return Err(PyValueError::new_err("Expected integer for array length")),
        };
        self.advance()?; // consumed length

        // optional delimiter skipped if any (not used currently)
        if self.current()?.token_type == TokenType::Identifier(String::from("|")) {
            self.advance()?;
        }

        if self.current()?.token_type != TokenType::ArrayEnd {
            return Err(PyValueError::new_err("Expected ] after array length"));
        }
        self.advance()?; // skip ]

        // Capture potential fields {fields} or inline header
        let mut fields: Option<Vec<String>> = None;
        if self.current()?.token_type == TokenType::BraceStart {
            self.advance()?; // skip {
            let mut captured_fields = Vec::new();
            loop {
                let token = self.current()?.clone();
                match token.token_type {
                    TokenType::BraceEnd => {
                        self.advance()?;
                        break;
                    }
                    TokenType::Identifier(ref s) | TokenType::String(ref s) => {
                        captured_fields.push(s.clone());
                        self.advance()?;
                    }
                    TokenType::Comma => {
                        self.advance()?;
                    }
                    _ => return Err(PyValueError::new_err("Expected field name or '}'")),
                }
            }
            fields = Some(captured_fields);
        } else {
            // compact header before colon: field1,field2 :
            if matches!(
                self.current()?.token_type,
                TokenType::Identifier(_) | TokenType::String(_)
            ) {
                let mut captured_fields = Vec::new();
                while self.current()?.token_type != TokenType::Colon
                    && self.current()?.token_type != TokenType::Newline
                    && self.current()?.token_type != TokenType::Eof
                {
                    let token = self.current()?.clone();
                    match token.token_type {
                        TokenType::Identifier(s) | TokenType::String(s) => {
                            captured_fields.push(s);
                            self.advance()?;
                        }
                        TokenType::Comma => {
                            self.advance()?;
                        }
                        _ => {
                            return Err(PyValueError::new_err(
                                "Expected field name, ',' or ':' for compact tabular header",
                            ))
                        }
                    }
                }
                if !captured_fields.is_empty() {
                    fields = Some(captured_fields);
                }
            }
        }

        // Expect :
        if self.current()?.token_type != TokenType::Colon {
            return Err(PyValueError::new_err("Expected : after array header"));
        }
        self.advance()?; // skip :

        // Check form
        if self.current()?.token_type == TokenType::Newline {
            self.advance()?; // skip newline
            if let Some(f) = fields {
                self.parse_tabular_content(length, f)
            } else {
                self.parse_list_content()
            }
        } else {
            // Inline form
            let list = PyList::empty_bound(self.py);
            for _ in 0..length {
                // Skip comma if present
                if self.current()?.token_type == TokenType::Comma {
                    self.advance()?;
                }

                let val = self.parse_value()?;
                list.append(val)?;
            }
            Ok(list.into_py(self.py))
        }
    }

    fn parse_tabular_content(&mut self, length: usize, fields: Vec<String>) -> PyResult<PyObject> {
        let list = PyList::empty_bound(self.py);

        // Consume Indent if present
        if self.current()?.token_type == TokenType::Indent {
            self.advance()?;
        }

        for _ in 0..length {
            // Skip newlines
            while self.current()?.token_type == TokenType::Newline {
                self.advance()?;
            }

            // Check for end of block (Dedent)
            if self.current()?.token_type == TokenType::Dedent {
                break;
            }

            let row_dict = PyDict::new_bound(self.py);
            for field in &fields {
                // Skip comma
                if self.current()?.token_type == TokenType::Comma {
                    self.advance()?;
                }

                let val = self.parse_value()?;
                row_dict.set_item(field, val)?;
            }
            list.append(row_dict)?;
        }

        // Consume Dedent if present
        if self.current()?.token_type == TokenType::Dedent {
            self.advance()?;
        }

        Ok(list.into_py(self.py))
    }

    fn parse_list_content(&mut self) -> PyResult<PyObject> {
        let list = PyList::empty_bound(self.py);

        // Capture indent level
        let mut list_indent_level = self.current()?.indent_level;

        // Consume Indent if present
        if self.current()?.token_type == TokenType::Indent {
            list_indent_level = self.current()?.indent_level;
            self.advance()?;
        }

        loop {
            // Skip newlines and indents (to handle extra indentation levels)
            while self.current()?.token_type == TokenType::Newline
                || self.current()?.token_type == TokenType::Indent
            {
                self.advance()?;
            }

            let token = self.current()?.clone();
            match token.token_type {
                TokenType::Dash => {
                    self.advance()?; // consume Dash
                                     // Skip newlines after Dash
                    while self.current()?.token_type == TokenType::Newline {
                        self.advance()?;
                    }
                    let val = self.parse_value()?;
                    list.append(val)?;
                }
                TokenType::Dedent => {
                    if token.indent_level < list_indent_level {
                        break;
                    }
                    self.advance()?;
                }
                TokenType::Eof => break,
                _ => {
                    return Err(PyValueError::new_err(format!(
                        "Expected '-' or end of list, got {:?}",
                        token.token_type
                    )))
                }
            }
        }
        Ok(list.into_py(self.py))
    }

    fn parse_object_indented(&mut self) -> PyResult<PyObject> {
        let dict = PyDict::new_bound(self.py);
        let start_indent_level = self.current()?.indent_level;

        loop {
            while self.current()?.token_type == TokenType::Newline {
                self.advance()?;
            }

            let token = self.current()?.clone();
            match token.token_type {
                TokenType::Identifier(_) | TokenType::String(_) => {
                    self.parse_kv_pair(&dict)?;
                }
                TokenType::Dedent => {
                    if token.indent_level < start_indent_level {
                        break;
                    }
                    self.advance()?; // Consume dedent that closes this block
                }
                TokenType::Eof => break,
                _ => {
                    return Err(PyValueError::new_err(format!(
                        "Expected key, Dedent or EOF, got {:?}",
                        token.token_type
                    )))
                }
            }
        }
        Ok(dict.into_py(self.py))
    }

    fn parse_inline_object(&mut self) -> PyResult<PyObject> {
        self.advance()?; // skip {
        let dict = PyDict::new_bound(self.py);

        loop {
            while self.current()?.token_type == TokenType::Newline {
                self.advance()?;
            }

            let token = self.current()?.clone();
            match token.token_type {
                TokenType::BraceEnd => {
                    self.advance()?;
                    break;
                }
                TokenType::Comma => {
                    self.advance()?;
                }
                TokenType::Identifier(_) | TokenType::String(_) => {
                    self.parse_kv_pair(&dict)?;
                }
                _ => {
                    return Err(PyValueError::new_err(format!(
                        "Expected key, ',' or '}}', got {:?}",
                        token.token_type
                    )))
                }
            }
        }
        Ok(dict.into_py(self.py))
    }

    fn parse_kv_pair(&mut self, dict: &Bound<'py, PyDict>) -> PyResult<()> {
        let key_obj = match self.current()?.token_type.clone() {
            TokenType::Identifier(s) | TokenType::String(s) => {
                let obj = PyString::new_bound(self.py, &s);
                self.advance()?;
                obj
            }
            _ => return Err(PyValueError::new_err("Expected key")),
        };

        if self.current()?.token_type == TokenType::ArrayStart {
            let val = self.parse_array_header_and_content()?;
            dict.set_item(key_obj, val)?;

            while self.current()?.token_type == TokenType::Newline {
                self.advance()?;
            }
            return Ok(());
        }

        if self.current()?.token_type != TokenType::Colon {
            return Err(PyValueError::new_err("Expected colon after key"));
        }
        self.advance()?; // skip :

        while self.current()?.token_type == TokenType::Newline {
            self.advance()?;
        }

        let val = self.parse_value()?;
        dict.set_item(key_obj, val)?;
        Ok(())
    }
}

// --- Encoder (Legacy Sequential kept for reference) ---

#[allow(dead_code)]
fn encode_value(
    _py: Python,
    obj: &Bound<'_, PyAny>,
    indent_level: usize,
    indent_size: usize,
) -> PyResult<String> {
    // Legacy encoder left as optional fallback. Kept but marked unused to silence warning.
    if obj.is_none() {
        return Ok("null".to_string());
    } else if let Ok(b) = obj.extract::<bool>() {
        return Ok(if b {
            "true".to_string()
        } else {
            "false".to_string()
        });
    } else if let Ok(i) = obj.extract::<i64>() {
        return Ok(i.to_string());
    } else if let Ok(f) = obj.extract::<f64>() {
        if f.is_nan() || f.is_infinite() {
            return Ok("null".to_string());
        }
        if f == 0.0 && f.is_sign_negative() {
            return Ok("0".to_string());
        }
        return Ok(f.to_string());
    } else if let Ok(s) = obj.extract::<String>() {
        let is_reserved = matches!(s.as_str(), "true" | "false" | "null");
        let is_number = s.parse::<f64>().is_ok();
        let has_special_chars = s
            .chars()
            .any(|c| matches!(c, ':' | ' ' | '\n' | '[' | ']' | '{' | '}' | ','))
            || s.is_empty();

        if is_reserved || is_number || has_special_chars {
            return Ok(format!("{:?}", s));
        } else {
            return Ok(s);
        }
    } else if let Ok(dict) = obj.downcast::<PyDict>() {
        if dict.is_empty() {
            return Ok("{}".to_string());
        }
        let mut lines = Vec::new();
        lines.push("".to_string()); // Start with newline
        for (k, v) in dict {
            let k_str = k.extract::<String>()?;
            let v_str = encode_value(_py, &v, indent_level + 1, indent_size)?;
            let next_indent = " ".repeat((indent_level + 1) * indent_size);

            if v_str.starts_with('\n') {
                lines.push(format!("{}{}:{}", next_indent, k_str, v_str));
            } else {
                lines.push(format!("{}{}: {}", next_indent, k_str, v_str));
            }
        }
        return Ok(lines.join("\n"));
    } else if let Ok(list) = obj.downcast::<PyList>() {
        let len = list.len();

        let mut is_tabular = true;
        let mut keys: Option<Vec<String>> = None;
        let mut all_primitive = true;

        for item in list {
            if item.downcast::<PyDict>().is_err() {
                is_tabular = false;
            }
            if item.downcast::<PyDict>().is_ok() || item.downcast::<PyList>().is_ok() {
                all_primitive = false;
            }
        }

        if is_tabular && !list.is_empty() {
            for item in list {
                if let Ok(d) = item.downcast::<PyDict>() {
                    for v in d.values() {
                        if v.downcast::<PyDict>().is_ok() || v.downcast::<PyList>().is_ok() {
                            is_tabular = false;
                            break;
                        }
                    }
                    if !is_tabular {
                        break;
                    }

                    let mut current_keys: Vec<String> = Vec::new();
                    for k in d.keys() {
                        if let Ok(s) = k.extract::<String>() {
                            current_keys.push(s);
                        } else {
                            is_tabular = false;
                            break;
                        }
                    }
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
            let first_item = list.get_item(0)?;
            let first_dict = first_item.downcast::<PyDict>()?;
            let fields: Vec<String> = first_dict
                .keys()
                .iter()
                .map(|k| k.extract::<String>().unwrap())
                .collect();

            let mut lines = Vec::new();
            lines.push(format!("[{}]{{{}}}:", len, fields.join(",")));
            let row_indent = " ".repeat((indent_level + 1) * indent_size);

            for item in list {
                let d = item.downcast::<PyDict>()?;
                let mut row_vals = Vec::new();
                for f in &fields {
                    let v = d
                        .get_item(f)?
                        .ok_or_else(|| PyValueError::new_err("Missing key"))?;
                    row_vals.push(encode_value(_py, &v, 0, 0)?);
                }
                lines.push(format!("{}{}", row_indent, row_vals.join(",")));
            }
            return Ok(lines.join("\n"));
        }

        if all_primitive {
            let mut parts = Vec::new();
            for item in list {
                parts.push(encode_value(_py, &item, 0, 0)?);
            }
            let values = parts.join(",");
            if values.is_empty() {
                return Ok(format!("[{}]:", len));
            }
            return Ok(format!("[{}]: {}", len, values));
        } else {
            let mut list_lines = Vec::new();
            list_lines.push(format!("[{}]:", len));
            let item_indent = " ".repeat((indent_level + 1) * indent_size);

            for item in list {
                let val_str = encode_value(_py, &item, indent_level + 2, indent_size)?;
                if val_str.starts_with('\n') {
                    list_lines.push(format!("{}  -", item_indent));
                    list_lines.push(val_str);
                } else {
                    list_lines.push(format!("{}  - {}", item_indent, val_str));
                }
            }
            return Ok(list_lines.join("\n"));
        }
    }

    Ok("".to_string())
}

#[pyfunction]
fn decode_toon(py: Python, text: &str) -> PyResult<PyObject> {
    if text.trim().is_empty() {
        return Ok(PyDict::new_bound(py).into_py(py));
    }

    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(py, lexer);

    let t = parser.current()?.token_type.clone();
    let result = match t {
        TokenType::ArrayStart => parser.parse_array_header_and_content(),
        TokenType::BraceStart => parser.parse_inline_object(),
        TokenType::Dash => parser.parse_list_content(),
        TokenType::Identifier(_) | TokenType::String(_) => {
            // Need to peek the second token to determine if it's a key for an object or a primitive.
            let next_token_is_colon = if let Some(peeked_token) = parser.peek_next()? {
                peeked_token.token_type == TokenType::Colon
            } else {
                false
            };

            if next_token_is_colon {
                parser.parse_object_indented()
            } else {
                parser.parse_value()
            }
        }
        TokenType::Indent => parser.parse_object_indented(),
        TokenType::Integer(_) | TokenType::Float(_) | TokenType::Boolean(_) | TokenType::Null => {
            parser.parse_value()
        }
        _ => Err(PyValueError::new_err(format!(
            "Unexpected root token: {:?}",
            t
        ))),
    }?;

    // Consume trailing Dedents/Newlines
    while parser.current()?.token_type == TokenType::Newline
        || parser.current()?.token_type == TokenType::Dedent
    {
        parser.advance()?;
    }

    if parser.current()?.token_type != TokenType::Eof {
        let current_token = parser.current()?.clone(); // Clone to fix E0499
        return Err(PyValueError::new_err(format!(
            "Extra tokens found after root element at line {} column {}",
            current_token.line, current_token.column
        )));
    }

    Ok(result)
}

#[pyfunction]
fn encode_toon(_py: Python, obj: Bound<'_, PyAny>) -> PyResult<String> {
    let ir = to_toon_value(&obj)?;

    // Special handling for Root Object (Dict) to avoid double indentation
    if let ToonValue::Dict(map) = &ir {
        if map.is_empty() {
            return Ok("".to_string());
        }
        let mut lines = Vec::new();
        for (k, v) in map {
            // Pass 0 indent level. Content keys will be at level 1 (2 spaces).
            let v_str = v.encode(0, 2);

            if v_str.starts_with('\n') {
                lines.push(format!("{}:{}", k, v_str));
            } else {
                lines.push(format!("{}: {}", k, v_str));
            }
        }
        return Ok(lines.join("\n"));
    }

    // For non-dict root
    let s = ir.encode(0, 2);
    Ok(s.trim_start_matches('\n').to_string())
}

#[pymodule]
fn _toonverter_core(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(decode_toon, m)?)?;
    m.add_function(wrap_pyfunction!(encode_toon, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use once_cell::sync::Lazy;

    // Ensure Python interpreter is prepared before tests run (since auto-initialize is disabled).
    static INITIALIZED: Lazy<()> = Lazy::new(|| {
        pyo3::prepare_freethreaded_python();
    });

    #[test]
    fn test_toon_value_encode_null() {
        let tv = ToonValue::Null;
        assert_eq!(tv.encode(0, 2), "null");
    }

    #[test]
    fn test_toon_value_encode_boolean() {
        let tv_true = ToonValue::Boolean(true);
        let tv_false = ToonValue::Boolean(false);
        assert_eq!(tv_true.encode(0, 2), "true");
        assert_eq!(tv_false.encode(0, 2), "false");
    }

    #[test]
    fn test_toon_value_encode_integer() {
        let tv = ToonValue::Integer(123);
        assert_eq!(tv.encode(0, 2), "123");
    }

    #[test]
    fn test_toon_value_encode_float() {
        let tv = ToonValue::Float(123.45);
        assert_eq!(tv.encode(0, 2), "123.45");
    }

    #[test]
    fn test_toon_value_encode_float_nan() {
        let tv = ToonValue::Float(f64::NAN);
        assert_eq!(tv.encode(0, 2), "null");
    }

    #[test]
    fn test_toon_value_encode_float_infinity() {
        let tv_pos = ToonValue::Float(f64::INFINITY);
        let tv_neg = ToonValue::Float(f64::NEG_INFINITY);
        assert_eq!(tv_pos.encode(0, 2), "null");
        assert_eq!(tv_neg.encode(0, 2), "null");
    }

    #[test]
    fn test_toon_value_encode_float_negative_zero() {
        let tv = ToonValue::Float(-0.0);
        assert_eq!(tv.encode(0, 2), "0");
    }

    #[test]
    fn test_toon_value_encode_string_simple() {
        let tv = ToonValue::String("hello".to_string());
        assert_eq!(tv.encode(0, 2), "hello");
    }

    #[test]
    fn test_toon_value_encode_string_needs_quoting_space() {
        let tv = ToonValue::String("hello world".to_string());
        assert_eq!(tv.encode(0, 2), "\"hello world\"");
    }

    #[test]
    fn test_toon_value_encode_string_needs_quoting_reserved() {
        let tv = ToonValue::String("true".to_string());
        assert_eq!(tv.encode(0, 2), "\"true\"");
    }

    #[test]
    fn test_toon_value_encode_string_needs_quoting_number() {
        let tv = ToonValue::String("123".to_string());
        assert_eq!(tv.encode(0, 2), "\"123\"");
    }

    #[test]
    fn test_toon_value_encode_dict_empty() {
        let tv = ToonValue::Dict(IndexMap::new());
        assert_eq!(tv.encode(0, 2), "{}");
    }

    #[test]
    fn test_toon_value_encode_dict_simple() {
        let mut map = IndexMap::new();
        map.insert("name".to_string(), ToonValue::String("Alice".to_string()));
        map.insert("age".to_string(), ToonValue::Integer(30));
        let tv = ToonValue::Dict(map);
        assert_eq!(tv.encode(0, 2), "\n  name: Alice\n  age: 30");
    }

    #[test]
    fn test_toon_value_encode_list_empty() {
        let tv = ToonValue::List(vec![]);
        assert_eq!(tv.encode(0, 2), "[0]:");
    }

    #[test]
    fn test_toon_value_encode_list_primitives() {
        let tv = ToonValue::List(vec![
            ToonValue::Integer(1),
            ToonValue::String("two".to_string()),
            ToonValue::Boolean(true),
        ]);
        assert_eq!(tv.encode(0, 2), "[3]: 1,two,true");
    }

    #[test]
    fn test_to_toon_value_null() {
        let _ = &*INITIALIZED;
        Python::with_gil(|py| {
            let py_obj = py.None();
            let tv = to_toon_value(&py_obj.into_bound(py)).unwrap();
            assert_eq!(tv, ToonValue::Null);
        });
    }

    #[test]
    fn test_to_toon_value_boolean() {
        let _ = &*INITIALIZED;
        Python::with_gil(|py| {
            let py_true = true.into_py(py);
            let py_false = false.into_py(py);
            assert_eq!(
                to_toon_value(&py_true.into_bound(py)).unwrap(),
                ToonValue::Boolean(true)
            );
            assert_eq!(
                to_toon_value(&py_false.into_bound(py)).unwrap(),
                ToonValue::Boolean(false)
            );
        });
    }

    #[test]
    fn test_to_toon_value_integer() {
        let _ = &*INITIALIZED;
        Python::with_gil(|py| {
            let py_obj: PyObject = 123.into_py(py);
            let tv = to_toon_value(&py_obj.into_bound(py)).unwrap();
            assert_eq!(tv, ToonValue::Integer(123));
        });
    }

    #[test]
    fn test_to_toon_value_float() {
        let _ = &*INITIALIZED;
        Python::with_gil(|py| {
            let py_obj: PyObject = 123.45.into_py(py);
            let tv = to_toon_value(&py_obj.into_bound(py)).unwrap();
            assert_eq!(tv, ToonValue::Float(123.45));
        });
    }

    #[test]
    fn test_to_toon_value_string() {
        let _ = &*INITIALIZED;
        Python::with_gil(|py| {
            let py_obj = PyString::new_bound(py, "hello");
            let tv = to_toon_value(&py_obj.into_any()).unwrap();
            assert_eq!(tv, ToonValue::String("hello".to_string()));
        });
    }

    #[test]
    fn test_to_toon_value_dict() {
        let _ = &*INITIALIZED;
        Python::with_gil(|py| {
            let dict = PyDict::new_bound(py);
            dict.set_item("name", PyString::new_bound(py, "Alice"))
                .unwrap();
            dict.set_item("age", 30.into_py(py)).unwrap();
            let tv = to_toon_value(&dict.into_any()).unwrap();

            let mut expected_map = IndexMap::new();
            expected_map.insert("name".to_string(), ToonValue::String("Alice".to_string()));
            expected_map.insert("age".to_string(), ToonValue::Integer(30));
            assert_eq!(tv, ToonValue::Dict(expected_map));
        });
    }

    #[test]
    fn test_to_toon_value_list() {
        let _ = &*INITIALIZED;
        Python::with_gil(|py| {
            let list = PyList::new_bound(py, &[] as &[PyObject]);
            list.append(1.into_py(py)).unwrap();
            list.append(PyString::new_bound(py, "two")).unwrap();
            let tv = to_toon_value(&list.into_any()).unwrap();

            let expected_list = vec![ToonValue::Integer(1), ToonValue::String("two".to_string())];
            assert_eq!(tv, ToonValue::List(expected_list));
        });
    }

    #[test]
    fn test_to_toon_value_unsupported_type() {
        let _ = &*INITIALIZED;
        Python::with_gil(|py| {
            let py_obj: PyObject = py.eval_bound("object()", None, None).unwrap().into_py(py);
            let py_obj_bound = py_obj.into_bound(py);
            let err = to_toon_value(&py_obj_bound).unwrap_err();
            assert!(err
                .to_string()
                .contains("Unsupported type for TOON encoding"));
        });
    }
}
