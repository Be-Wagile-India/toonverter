use crate::tokens::{Token, TokenType};

pub struct ToonLexer<'a> {
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
    pub fn new(text: &'a str, indent_size: usize) -> Self {
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

    fn detect_indentation(&self) -> Result<usize, String> {
        let mut spaces = 0;
        for c in self.current_line_str.chars() {
            if c == ' ' {
                spaces += 1;
            } else if c == '\t' {
                return Err("Tabs are not allowed for indentation".to_string());
            } else {
                break;
            }
        }
        Ok(spaces / self.indent_size)
    }

    fn scan_string(&mut self, _start_col: usize) -> Result<TokenType, String> {
        let mut s = String::new();
        let mut escaped = false;
        loop {
            let c = match self.next_char() {
                Some(ch) => ch,
                None => return Err("Unterminated quoted string".to_string()),
            };
            if escaped {
                match c {
                    '\\' => s.push('\\'),
                    '"' => s.push('"'),
                    'n' => s.push('\n'),
                    'r' => s.push('\r'),
                    't' => s.push('\t'),
                    other => return Err(format!("Invalid escape character: {}", other)),
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

    fn next_token(&mut self) -> Result<Option<Token>, String> {
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

            // Only handle indentation for non-comment lines
            if !trimmed.starts_with('#') {
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
            '|' => TokenType::Pipe,
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
            '#' => {
                // Consume the rest of the line as a comment
                while let Some(&next_c) = self.peek_char() {
                    if next_c == '\n' {
                        break;
                    }
                    self.next_char();
                }
                TokenType::Comment
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
    type Item = Result<Token, String>;

    fn next(&mut self) -> Option<Self::Item> {
        self.next_token().transpose()
    }
}
