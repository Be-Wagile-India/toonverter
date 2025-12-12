use indexmap::IndexMap;
use std::collections::VecDeque;

use crate::ir::ToonValue;
use crate::lexer::ToonLexer;
use crate::tokens::{Token, TokenType};

pub struct ToonParser<'a> {
    token_stream: ToonLexer<'a>,
    buffer: VecDeque<Token>,
}

type ParseResult<T> = Result<T, String>;

impl<'a> ToonParser<'a> {
    pub fn new(lexer: ToonLexer<'a>) -> Self {
        ToonParser {
            token_stream: lexer,
            buffer: VecDeque::new(),
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
        // Handle empty input if checked before, but lexer handles it.
        // If EOF immediately?
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
                let next_is_colon = if let Some(peeked) = self.peek_next()? {
                    peeked.token_type == TokenType::Colon
                } else {
                    false
                };

                if next_is_colon {
                    self.parse_object_indented()
                } else {
                    self.parse_value()
                }
            }
            TokenType::Indent => self.parse_object_indented(),
            TokenType::Integer(_)
            | TokenType::Float(_)
            | TokenType::Boolean(_)
            | TokenType::Null => self.parse_value(),
            _ => return Err(format!("Unexpected root token: {:?}", t)),
        }?;

        // Consume trailing
        while self.current()?.token_type == TokenType::Newline
            || self.current()?.token_type == TokenType::Dedent
        {
            self.advance()?;
        }

        if self.current()?.token_type != TokenType::Eof {
            let t = self.current()?.clone();
            return Err(format!(
                "Extra tokens found after root element at line {} column {}",
                t.line, t.column
            ));
        }

        Ok(result)
    }

    pub fn parse_value(&mut self) -> ParseResult<ToonValue> {
        let token = self.current()?.clone();

        match token.token_type {
            TokenType::String(ref s) => {
                self.advance()?;
                Ok(ToonValue::String(s.clone()))
            }
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
            TokenType::Identifier(ref s) => {
                self.advance()?;
                Ok(ToonValue::String(s.clone()))
            }
            TokenType::ArrayStart => self.parse_array_header_and_content(),
            TokenType::BraceStart => self.parse_inline_object(),
            TokenType::Indent => {
                self.advance()?;
                self.parse_object_indented()
            }
            TokenType::Dash => self.parse_list_content(),
            _ => Err(format!("Unexpected token in value: {:?}", token.token_type)),
        }
    }

    pub fn parse_array_header_and_content(&mut self) -> ParseResult<ToonValue> {
        self.advance()?; // skip [

        // Parse length
        let len_token = self.current()?.clone();
        let length = match len_token.token_type {
            TokenType::Integer(i) => i as usize,
            _ => return Err("Expected integer for array length".to_string()),
        };
        self.advance()?;

        // optional delimiter
        if let TokenType::Identifier(ref s) = self.current()?.token_type {
            if s == "|" {
                self.advance()?;
            }
        }

        if self.current()?.token_type != TokenType::ArrayEnd {
            return Err("Expected ] after array length".to_string());
        }
        self.advance()?;

        // Capture potential fields {fields} or inline header
        let mut fields: Option<Vec<String>> = None;
        if self.current()?.token_type == TokenType::BraceStart {
            self.advance()?;
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
                    _ => return Err("Expected field name or '}'".to_string()),
                }
            }
            fields = Some(captured_fields);
        } else {
            // compact header before colon: field1,field2 :
            match self.current()?.token_type {
                TokenType::Identifier(_) | TokenType::String(_) => {
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
                                return Err(
                                    "Expected field name, ',' or ':' for compact tabular header"
                                        .to_string(),
                                )
                            }
                        }
                    }
                    if !captured_fields.is_empty() {
                        fields = Some(captured_fields);
                    }
                }
                _ => {} // No fields specified
            }
        }

        // Expect :
        if self.current()?.token_type != TokenType::Colon {
            return Err("Expected : after array header".to_string());
        }
        self.advance()?;

        // Check form
        if self.current()?.token_type == TokenType::Newline {
            self.advance()?;
            if let Some(f) = fields {
                self.parse_tabular_content(length, f)
            } else {
                self.parse_list_content()
            }
        } else {
            // Inline form
            let mut list = Vec::with_capacity(length);
            for _ in 0..length {
                if self.current()?.token_type == TokenType::Comma {
                    self.advance()?;
                }
                let val = self.parse_value()?;
                list.push(val);
            }
            Ok(ToonValue::List(list))
        }
    }

    fn parse_tabular_content(
        &mut self,
        length: usize,
        fields: Vec<String>,
    ) -> ParseResult<ToonValue> {
        let mut list = Vec::with_capacity(length);

        if self.current()?.token_type == TokenType::Indent {
            self.advance()?;
        }

        for _ in 0..length {
            while self.current()?.token_type == TokenType::Newline {
                self.advance()?;
            }

            if self.current()?.token_type == TokenType::Dedent {
                break;
            }

            let mut row_dict = IndexMap::new();
            for field in &fields {
                if self.current()?.token_type == TokenType::Comma {
                    self.advance()?;
                }
                let val = self.parse_value()?;
                row_dict.insert(field.clone(), val);
            }
            list.push(ToonValue::Dict(row_dict));
        }

        if self.current()?.token_type == TokenType::Dedent {
            self.advance()?;
        }

        Ok(ToonValue::List(list))
    }

    pub fn parse_list_content(&mut self) -> ParseResult<ToonValue> {
        let mut list = Vec::new();
        let mut list_indent_level = self.current()?.indent_level;

        if self.current()?.token_type == TokenType::Indent {
            list_indent_level = self.current()?.indent_level;
            self.advance()?;
        }

        loop {
            while self.current()?.token_type == TokenType::Newline
                || self.current()?.token_type == TokenType::Indent
            {
                self.advance()?;
            }

            let token = self.current()?.clone();
            match token.token_type {
                TokenType::Dash => {
                    self.advance()?;
                    while self.current()?.token_type == TokenType::Newline {
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
        Ok(ToonValue::List(list))
    }

    pub fn parse_object_indented(&mut self) -> ParseResult<ToonValue> {
        let mut dict = IndexMap::new();
        let start_indent_level = self.current()?.indent_level;

        loop {
            while self.current()?.token_type == TokenType::Newline {
                self.advance()?;
            }

            let token = self.current()?.clone();
            match token.token_type {
                TokenType::Identifier(_) | TokenType::String(_) => {
                    self.parse_kv_pair(&mut dict)?;
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

    pub fn parse_inline_object(&mut self) -> ParseResult<ToonValue> {
        self.advance()?;
        let mut dict = IndexMap::new();

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
                    self.parse_kv_pair(&mut dict)?;
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

    fn parse_kv_pair(&mut self, dict: &mut IndexMap<String, ToonValue>) -> ParseResult<()> {
        let key_str = match self.current()?.token_type.clone() {
            TokenType::Identifier(s) | TokenType::String(s) => {
                self.advance()?;
                s
            }
            _ => return Err("Expected key".to_string()),
        };

        if self.current()?.token_type == TokenType::ArrayStart {
            let val = self.parse_array_header_and_content()?;
            dict.insert(key_str, val);

            while self.current()?.token_type == TokenType::Newline {
                self.advance()?;
            }
            return Ok(());
        }

        if self.current()?.token_type != TokenType::Colon {
            return Err("Expected colon after key".to_string());
        }
        self.advance()?;

        while self.current()?.token_type == TokenType::Newline {
            self.advance()?;
        }

        let val = self.parse_value()?;
        dict.insert(key_str, val);
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_simple_string() {
        let text = "\"hello\"";
        let lexer = ToonLexer::new(text, 2);
        let mut parser = ToonParser::new(lexer);
        let result = parser.parse_value().unwrap();
        assert_eq!(result, ToonValue::String("hello".to_string()));
    }

    #[test]
    fn test_parse_integer() {
        let text = "123";
        let lexer = ToonLexer::new(text, 2);
        let mut parser = ToonParser::new(lexer);
        let result = parser.parse_value().unwrap();
        assert_eq!(result, ToonValue::Integer(123));
    }

    #[test]
    fn test_parse_inline_dict() {
        let text = "{a: 1, b: 2}";
        let lexer = ToonLexer::new(text, 2);
        let mut parser = ToonParser::new(lexer);
        let result = parser.parse_value().unwrap();
        if let ToonValue::Dict(d) = result {
            assert_eq!(d.get("a"), Some(&ToonValue::Integer(1)));
            assert_eq!(d.get("b"), Some(&ToonValue::Integer(2)));
        } else {
            panic!("Expected Dict");
        }
    }

    #[test]
    fn test_parse_error_missing_closing_bracket() {
        let text = "[1, 2";
        let lexer = ToonLexer::new(text, 2);
        let mut parser = ToonParser::new(lexer);
        let result = parser.parse_value();
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("Expected ]"));
    }

    #[test]
    fn test_parse_tabular_header() {
        let text = "[2]{a, b}:\n  1, 2\n  3, 4";
        let lexer = ToonLexer::new(text, 2);
        let mut parser = ToonParser::new(lexer);
        let result = parser.parse_array_header_and_content().unwrap();

        if let ToonValue::List(list) = result {
            assert_eq!(list.len(), 2);
            // Check first row dict
            if let ToonValue::Dict(d) = &list[0] {
                assert_eq!(d.get("a"), Some(&ToonValue::Integer(1)));
                assert_eq!(d.get("b"), Some(&ToonValue::Integer(2)));
            } else {
                panic!("Row 1 not dict");
            }
        } else {
            panic!("Expected List");
        }
    }

    #[test]
    fn test_parse_unexpected_token() {
        let text = ":";
        let lexer = ToonLexer::new(text, 2);
        let mut parser = ToonParser::new(lexer);
        let result = parser.parse_value();
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("Unexpected token"));
    }
}
