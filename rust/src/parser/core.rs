use indexmap::IndexMap;
use std::collections::VecDeque;

use crate::ir::ToonValue;
use crate::lexer::ToonLexer;
use crate::tokens::{Token, TokenType};

pub struct ToonParser<'a> {
    token_stream: ToonLexer<'a>,
    buffer: VecDeque<Token>,
    recursion_depth: usize,
    max_recursion_depth: usize,
}

type ParseResult<T> = Result<T, String>;

impl<'a> ToonParser<'a> {
    pub fn new(lexer: ToonLexer<'a>) -> Self {
        ToonParser {
            token_stream: lexer,
            buffer: VecDeque::new(),
            recursion_depth: 0,
            max_recursion_depth: 100,
        }
    }

    fn enter_recursion(&mut self) -> ParseResult<()> {
        self.recursion_depth += 1;
        if self.recursion_depth > self.max_recursion_depth {
            return Err(format!(
                "Maximum recursion depth ({}) exceeded",
                self.max_recursion_depth
            ));
        }
        Ok(())
    }

    fn exit_recursion(&mut self) {
        if self.recursion_depth > 0 {
            self.recursion_depth -= 1;
        }
    }

    fn fill_buffer(&mut self, count: usize) -> ParseResult<()> {
        while self.buffer.len() < count {
            if let Some(token_res) = self.token_stream.next() {
                match token_res {
                    Ok(t) => self.buffer.push_back(t),
                    Err(e) => return Err(format!("Lexer error: {}", e)),
                }
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

    pub fn current(&mut self) -> ParseResult<&Token> {
        self.fill_buffer(1)?;
        self.buffer
            .front()
            .ok_or_else(|| "Unexpected end of token stream".to_string())
    }

    pub fn advance(&mut self) -> ParseResult<Token> {
        self.fill_buffer(1)?;
        self.buffer
            .pop_front()
            .ok_or_else(|| "Unexpected end of token stream".to_string())
    }

    pub fn peek_next(&mut self) -> ParseResult<Option<&Token>> {
        self.fill_buffer(2)?;
        Ok(self.buffer.get(1))
    }

    pub fn parse_root(&mut self) -> ParseResult<ToonValue> {
        // Consume leading Newline or Comment tokens
        while self.current()?.token_type == TokenType::Newline
            || self.current()?.token_type == TokenType::Comment
        {
            self.advance()?;
        }

        if self.current()?.token_type == TokenType::Eof {
            return Ok(ToonValue::Dict(IndexMap::new()));
        }

        let t = self.current()?.token_type.clone();
        let result = match t {
            TokenType::ArrayStart => self.parse_array_header_and_content(),
            TokenType::BraceStart => self.parse_inline_object(),
            TokenType::Dash => self.parse_list_content(),
            TokenType::Identifier(_) | TokenType::String(_) => {
                // Peek next to decide if key-value or primitive
                let is_kv_start = if let Some(peeked) = self.peek_next()? {
                    matches!(peeked.token_type, TokenType::Colon | TokenType::ArrayStart)
                } else {
                    false
                };

                if is_kv_start {
                    self.parse_object_indented()
                } else {
                    self.parse_value()
                }
            }
            TokenType::Indent => {
                self.advance()?; // Consume the Indent token
                self.parse_object_indented()
            }
            TokenType::Integer(_)
            | TokenType::Float(_)
            | TokenType::Boolean(_)
            | TokenType::Null => self.parse_value(),
            _ => return Err(format!("Unexpected root token: {:?}", t)),
        }?;

        // Consume trailing tokens
        while self.current()?.token_type == TokenType::Newline
            || self.current()?.token_type == TokenType::Dedent
            || self.current()?.token_type == TokenType::Comment
        {
            if self.current()?.token_type == TokenType::Eof {
                break;
            }
            self.advance()?;
        }

        if self.current()?.token_type != TokenType::Eof {
            let t = self.current()?.clone();
            return Err(format!(
                "Extra tokens found after root element at line {} column {}. Token: {:?}",
                t.line, t.column, t.token_type
            ));
        }

        Ok(result)
    }

    pub fn parse_value(&mut self) -> ParseResult<ToonValue> {
        self.enter_recursion()?;
        let result = self._parse_value_core();
        self.exit_recursion();
        result
    }

    fn _parse_value_core(&mut self) -> ParseResult<ToonValue> {
        // Consume leading Newline or Comment tokens
        while self.current()?.token_type == TokenType::Newline
            || self.current()?.token_type == TokenType::Comment
        {
            self.advance()?;
        }

        let token = self.current()?.clone();

        match token.token_type {
            TokenType::Integer(i) => {
                self.advance()?;
                Ok(ToonValue::Integer(i))
            }
            TokenType::Float(f) => {
                self.advance()?;
                Ok(ToonValue::Float(f))
            }
            TokenType::Boolean(b) => {
                self.advance()?;
                Ok(ToonValue::Boolean(b))
            }
            TokenType::Null => {
                self.advance()?;
                Ok(ToonValue::Null)
            }
            TokenType::Identifier(_) | TokenType::String(_) => {
                let next_is_colon = if let Some(peeked) = self.peek_next()? {
                    peeked.token_type == TokenType::Colon
                } else {
                    false
                };

                if next_is_colon {
                    self.parse_implicit_inline_object()
                } else {
                    let token = self.current()?.clone();
                    let s = match token.token_type {
                        TokenType::Identifier(ref s) | TokenType::String(ref s) => s.clone(),
                        _ => unreachable!(),
                    };
                    self.advance()?;
                    Ok(ToonValue::String(s))
                }
            }
            TokenType::ArrayStart => self.parse_array_header_and_content(),
            TokenType::BraceStart => {
                // Peek ahead to determine if it's an inline object with indented content
                let mut peek_offset = 1;
                let is_indented = loop {
                    self.fill_buffer(peek_offset + 1)?;
                    if peek_offset >= self.buffer.len() {
                        break false;
                    }
                    let t = self.buffer[peek_offset].token_type.clone();
                    if t == TokenType::Newline {
                        peek_offset += 1;
                        continue;
                    }
                    if t == TokenType::Comment {
                        peek_offset += 1;
                        continue;
                    }
                    if t == TokenType::Indent {
                        break true;
                    }
                    break false;
                };

                if is_indented {
                    self.advance()?; // Consume the BraceStart
                                     // Consume Newline and Indent, which will be handled by parse_object_indented
                    while self.current()?.token_type == TokenType::Newline
                        || self.current()?.token_type == TokenType::Comment
                    {
                        self.advance()?;
                    }
                    if self.current()?.token_type == TokenType::Indent {
                        self.advance()?; // Consume Indent
                        self.parse_object_indented()
                    } else {
                        self.parse_inline_object()
                    }
                } else {
                    self.parse_inline_object()
                }
            }
            TokenType::Indent => {
                self.advance()?;
                while self.current()?.token_type == TokenType::Newline
                    || self.current()?.token_type == TokenType::Comment
                {
                    self.advance()?;
                }

                if self.current()?.token_type == TokenType::Dash {
                    self.parse_list_content()
                } else {
                    self.parse_object_indented()
                }
            }
            TokenType::Dash => self.parse_list_content(),
            _ => Err(format!("Unexpected token in value: {:?}", token.token_type)),
        }
    }

    pub(crate) fn parse_implicit_inline_object(&mut self) -> ParseResult<ToonValue> {
        let mut dict = IndexMap::new();

        // 1. Parse inline fields
        loop {
            let token = self.current()?.clone();
            match token.token_type {
                TokenType::Newline | TokenType::Eof | TokenType::Dedent | TokenType::Comment => {
                    break;
                }
                TokenType::Comma => {
                    self.advance()?;
                }
                TokenType::Identifier(_) | TokenType::String(_) => {
                    let (k, v) = self.parse_kv_pair()?;
                    dict.insert(k, v);
                }
                _ => {
                    return Err(format!(
                        "Unexpected token in implicit inline object: {:?}",
                        token.token_type
                    ))
                }
            }
        }

        // 2. Check for continued fields on next lines (indented)
        let mut peek_offset = 0;
        loop {
            self.fill_buffer(peek_offset + 1)?;
            if peek_offset >= self.buffer.len() {
                break;
            }

            let t = self.buffer[peek_offset].token_type.clone();

            if matches!(t, TokenType::Newline | TokenType::Comment) {
                peek_offset += 1;
                continue;
            }

            if matches!(t, TokenType::Indent) {
                // Yes, continuation!
                for _ in 0..peek_offset {
                    self.advance()?;
                }
                self.advance()?; // Consume Indent

                // Parse indented fields
                loop {
                    while self.current()?.token_type == TokenType::Newline
                        || self.current()?.token_type == TokenType::Comment
                    {
                        self.advance()?;
                    }

                    match self.current()?.token_type {
                        TokenType::Dedent => {
                            self.advance()?;
                            break;
                        }
                        TokenType::Eof => break,
                        _ => {
                            let (k, v) = self.parse_kv_pair()?;
                            dict.insert(k, v);
                        }
                    }
                }
            }
            break;
        }

        Ok(ToonValue::Dict(dict))
    }

    pub(crate) fn parse_array_header_and_content(&mut self) -> ParseResult<ToonValue> {
        let (length, fields) = self.parse_array_header()?;

        // Determine if it's List or Tabular based on Newline following ':'
        if self.current()?.token_type == TokenType::Newline {
            self.advance()?;
            while self.current()?.token_type == TokenType::Comment {
                self.advance()?;
            }
            if let Some(f) = fields {
                self.parse_tabular_content(length, f)
            } else {
                self.parse_list_content()
            }
        } else {
            self.parse_inline_array_content(length, fields)
        }
    }

    fn parse_array_header(&mut self) -> ParseResult<(Option<usize>, Option<Vec<String>>)> {
        self.advance()?; // skip [

        while self.current()?.token_type == TokenType::Newline
            || self.current()?.token_type == TokenType::Comment
        {
            self.advance()?;
        }

        let mut length: Option<usize> = None;
        let mut fields: Option<Vec<String>> = None;

        let token = self.current()?.clone();
        match token.token_type {
            TokenType::Integer(i) => {
                length = Some(i as usize);
                self.advance()?;
            }
            TokenType::Star => {
                length = None;
                self.advance()?;
            }
            TokenType::Identifier(ref s) => {
                fields = Some(vec![s.clone()]);
                self.advance()?;
            }
            _ => return Err("Expected integer for array length or implicit schema".to_string()),
        }

        // optional delimiter
        if self.current()?.token_type == TokenType::Pipe {
            self.advance()?;
        }

        while self.current()?.token_type == TokenType::Newline
            || self.current()?.token_type == TokenType::Comment
        {
            self.advance()?;
        }

        if self.current()?.token_type != TokenType::ArrayEnd {
            let t = self.current()?;
            return Err(format!(
                "Expected ']' after array length, found {:?} at line {} col {}",
                t.token_type, t.line, t.column
            ));
        }
        self.advance()?;

        while self.current()?.token_type == TokenType::Newline
            || self.current()?.token_type == TokenType::Comment
        {
            self.advance()?;
        }

        // Capture potential fields {fields}
        if self.current()?.token_type == TokenType::BraceStart {
            self.advance()?;
            let mut captured_fields = Vec::new();
            loop {
                while self.current()?.token_type == TokenType::Newline
                    || self.current()?.token_type == TokenType::Comment
                {
                    self.advance()?;
                }

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
                    _ => return Err("Expected field name or '}'".to_string()),
                }
            }
            fields = Some(captured_fields);
        }

        while self.current()?.token_type == TokenType::Newline
            || self.current()?.token_type == TokenType::Comment
        {
            self.advance()?;
        }

        // Expect :
        if self.current()?.token_type != TokenType::Colon {
            let t = self.current()?;
            return Err(format!(
                "Expected ':' after array header, found {:?} at line {} col {}",
                t.token_type, t.line, t.column
            ));
        }
        self.advance()?;

        Ok((length, fields))
    }

    fn parse_inline_array_content(
        &mut self,
        length: Option<usize>,
        fields: Option<Vec<String>>,
    ) -> ParseResult<ToonValue> {
        let mut list = Vec::new();

        if let Some(len) = length {
            for _ in 0..len {
                if self.current()?.token_type == TokenType::Comma {
                    self.advance()?;
                }
                while self.current()?.token_type == TokenType::Newline
                    || self.current()?.token_type == TokenType::Comment
                {
                    self.advance()?;
                }
                let val = self.parse_value()?;
                list.push(val);
            }
        } else {
            // Length unknown, parse until end of inline list
            loop {
                match self.current()?.token_type {
                    TokenType::Newline
                    | TokenType::Comment
                    | TokenType::Eof
                    | TokenType::Dedent => break,
                    TokenType::Comma => {
                        self.advance()?;
                    }
                    _ => {}
                }
                match self.current()?.token_type {
                    TokenType::Newline
                    | TokenType::Comment
                    | TokenType::Eof
                    | TokenType::Dedent => break,
                    _ => {}
                }

                let val = self.parse_value()?;
                list.push(val);
            }
        }

        if let Some(f) = fields {
            if f.len() == 1 {
                let key = &f[0];
                let wrapped: Vec<ToonValue> = list
                    .into_iter()
                    .map(|v| {
                        let mut d = IndexMap::new();
                        d.insert(key.clone(), v);
                        ToonValue::Dict(d)
                    })
                    .collect();
                Ok(ToonValue::List(wrapped))
            } else {
                Ok(ToonValue::List(list))
            }
        } else {
            Ok(ToonValue::List(list))
        }
    }

    pub(crate) fn parse_tabular_content(
        &mut self,
        length: Option<usize>,
        fields: Vec<String>,
    ) -> ParseResult<ToonValue> {
        let mut list = if let Some(len) = length {
            Vec::with_capacity(len)
        } else {
            Vec::new()
        };

        // Skip leading newlines/comments before checking for block indentation
        while self.current()?.token_type == TokenType::Newline
            || self.current()?.token_type == TokenType::Comment
        {
            self.advance()?;
        }

        let mut has_indent = false;
        let mut block_indent_level = 0;
        if self.current()?.token_type == TokenType::Indent {
            has_indent = true;
            block_indent_level = self.current()?.indent_level;
            self.advance()?;
        }

        let mut count = 0;
        loop {
            if let Some(len) = length {
                if count >= len {
                    break;
                }
            }

            while self.current()?.token_type == TokenType::Newline
                || self.current()?.token_type == TokenType::Comment
            {
                self.advance()?;
            }

            // Termination check for indefinite length
            if length.is_none() {
                let t_type = self.current()?.token_type.clone();
                if t_type == TokenType::Eof {
                    break;
                }
                if t_type == TokenType::Dedent
                    && has_indent
                    && self.current()?.indent_level < block_indent_level
                {
                    break;
                }
            }

            let mut row_dict = IndexMap::new();
            for (i, field) in fields.iter().enumerate() {
                if i > 0 && self.current()?.token_type == TokenType::Comma {
                    self.advance()?;
                }

                while self.current()?.token_type == TokenType::Newline
                    || self.current()?.token_type == TokenType::Comment
                {
                    self.advance()?;
                }

                let token_type = self.current()?.token_type.clone();
                match token_type {
                    TokenType::Dedent | TokenType::Eof | TokenType::Comma | TokenType::Newline => {
                        row_dict.insert(field.clone(), ToonValue::Null);
                    }
                    _ => {
                        let val = self.parse_value()?;
                        row_dict.insert(field.clone(), val);
                    }
                }
            }
            list.push(ToonValue::Dict(row_dict));
            count += 1;

            // Consume remaining tokens on this row until newline/eof/dedent
            loop {
                let t = self.current()?.token_type.clone();
                if matches!(t, TokenType::Newline | TokenType::Eof | TokenType::Dedent) {
                    break;
                }
                self.advance()?;
            }
        }

        if has_indent {
            while self.current()?.token_type == TokenType::Newline
                || self.current()?.token_type == TokenType::Comment
            {
                self.advance()?;
            }
            if self.current()?.token_type == TokenType::Dedent {
                self.advance()?;
            }
        }

        Ok(ToonValue::List(list))
    }

    pub(crate) fn parse_list_content(&mut self) -> ParseResult<ToonValue> {
        let mut list = Vec::new();

        while self.current()?.token_type == TokenType::Newline
            || self.current()?.token_type == TokenType::Comment
        {
            self.advance()?;
        }

        let mut list_indent_level = self.current()?.indent_level;
        let mut has_indent = false;

        if self.current()?.token_type == TokenType::Indent {
            has_indent = true;
            self.advance()?;
            list_indent_level = self.current()?.indent_level;
        }

        loop {
            while self.current()?.token_type == TokenType::Newline
                || self.current()?.token_type == TokenType::Indent
                || self.current()?.token_type == TokenType::Comment
            {
                self.advance()?;
            }

            let token = self.current()?.clone();
            match token.token_type {
                TokenType::Dash => {
                    self.advance()?;
                    while self.current()?.token_type == TokenType::Newline
                        || self.current()?.token_type == TokenType::Comment
                    {
                        self.advance()?;
                    }
                    let val = self.parse_value()?;
                    list.push(val);
                }
                TokenType::Dedent => {
                    if token.indent_level < list_indent_level {
                        break;
                    }
                    self.advance()?;
                }
                TokenType::Eof => break,
                _ => {
                    return Err(format!(
                        "Expected '-' or end of list, got {:?}",
                        token.token_type
                    ))
                }
            }
        }

        if has_indent {
            while self.current()?.token_type == TokenType::Newline
                || self.current()?.token_type == TokenType::Comment
            {
                self.advance()?;
            }
            if self.current()?.token_type == TokenType::Dedent {
                self.advance()?;
            }
        }

        Ok(ToonValue::List(list))
    }

    pub(crate) fn parse_object_indented(&mut self) -> ParseResult<ToonValue> {
        let mut dict = IndexMap::new();
        let start_indent_level = self.current()?.indent_level;

        loop {
            while self.current()?.token_type == TokenType::Newline
                || self.current()?.token_type == TokenType::Comment
            {
                self.advance()?;
            }

            let token = self.current()?.clone();
            match token.token_type {
                TokenType::Identifier(_) | TokenType::String(_) => {
                    let (k, v) = self.parse_kv_pair()?;
                    dict.insert(k, v);
                }
                TokenType::Dedent => {
                    if token.indent_level < start_indent_level {
                        break;
                    }
                    self.advance()?;
                }
                TokenType::Eof => break,
                _ => {
                    return Err(format!(
                        "Expected key, Dedent or EOF, got {:?}",
                        token.token_type
                    ))
                }
            }
        }
        Ok(ToonValue::Dict(dict))
    }

    pub(crate) fn parse_inline_object(&mut self) -> ParseResult<ToonValue> {
        self.advance()?;
        let mut dict = IndexMap::new();

        loop {
            while self.current()?.token_type == TokenType::Newline
                || self.current()?.token_type == TokenType::Comment
            {
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
                    let (k, v) = self.parse_kv_pair()?;
                    dict.insert(k, v);
                }
                _ => {
                    return Err(format!(
                        "Expected key, ',' or '}}', got {:?}",
                        token.token_type
                    ))
                }
            }
        }
        Ok(ToonValue::Dict(dict))
    }

    pub(crate) fn parse_kv_pair(&mut self) -> ParseResult<(String, ToonValue)> {
        let key_str = match self.current()?.token_type.clone() {
            TokenType::Identifier(s) | TokenType::String(s) => {
                self.advance()?;
                s
            }
            _ => return Err("Expected identifier or string as key".to_string()),
        };

        while self.current()?.token_type == TokenType::Newline
            || self.current()?.token_type == TokenType::Comment
        {
            self.advance()?;
        }

        if self.current()?.token_type == TokenType::ArrayStart {
            let val = self.parse_array_header_and_content()?;
            while self.current()?.token_type == TokenType::Newline
                || self.current()?.token_type == TokenType::Comment
            {
                self.advance()?;
            }
            return Ok((key_str, val));
        }

        while self.current()?.token_type == TokenType::Newline
            || self.current()?.token_type == TokenType::Comment
        {
            self.advance()?;
        }

        if self.current()?.token_type != TokenType::Colon {
            return Err("Expected colon after key".to_string());
        }
        self.advance()?;

        while self.current()?.token_type == TokenType::Newline
            || self.current()?.token_type == TokenType::Comment
        {
            self.advance()?;
        }

        let val = self.parse_value()?;
        Ok((key_str, val))
    }
}
