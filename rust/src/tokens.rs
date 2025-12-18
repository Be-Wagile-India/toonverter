#[derive(Debug, PartialEq, Clone)]
pub enum TokenType {
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
    Pipe,       // |
    Comment,    // #
    ArrayStart, // [
    ArrayEnd,   // ]
    BraceStart, // {
    BraceEnd,   // }
    Identifier(String),
}

#[derive(Debug, Clone)]
pub struct Token {
    pub token_type: TokenType,
    pub line: usize,
    pub column: usize,
    pub indent_level: usize,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_token_creation() {
        let t = Token {
            token_type: TokenType::Indent,
            line: 1,
            column: 0,
            indent_level: 1,
        };
        assert_eq!(t.token_type, TokenType::Indent);
        assert_eq!(t.line, 1);
        assert_eq!(t.column, 0);
        assert_eq!(t.indent_level, 1);
    }

    #[test]
    fn test_token_type_equality() {
        assert_eq!(TokenType::Indent, TokenType::Indent);
        assert_ne!(TokenType::Indent, TokenType::Dedent);
        assert_eq!(
            TokenType::String("foo".to_string()),
            TokenType::String("foo".to_string())
        );
    }
}
