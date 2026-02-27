use super::core::ToonLexer;
use crate::tokens::TokenType;

fn get_tokens(text: &str) -> Vec<TokenType> {
    let mut lexer = ToonLexer::new(text, 2);
    let mut tokens = Vec::new();
    while let Some(token_res) = lexer.next() {
        match token_res {
            Ok(token) => tokens.push(token.token_type),
            Err(e) => panic!("Lexer error: {}", e),
        }
    }
    tokens
}

#[test]
fn test_lexer_empty() {
    let tokens = get_tokens("");
    assert!(tokens.is_empty());
}

#[test]
fn test_lexer_primitives() {
    let tokens = get_tokens("true false null 123 12.34 \"hello\"");
    assert_eq!(
        tokens,
        vec![
            TokenType::Boolean(true),
            TokenType::Boolean(false),
            TokenType::Null,
            TokenType::Integer(123),
            TokenType::Float(12.34),
            TokenType::String("hello".to_string())
        ]
    );
}

#[test]
fn test_lexer_indentation() {
    let text = "root:\n  child: value";
    let tokens = get_tokens(text);
    assert_eq!(
        tokens,
        vec![
            TokenType::Identifier("root".to_string()),
            TokenType::Colon,
            TokenType::Newline,
            TokenType::Indent,
            TokenType::Identifier("child".to_string()),
            TokenType::Colon,
            TokenType::Identifier("value".to_string()),
            TokenType::Dedent
        ]
    );
}

#[test]
fn test_lexer_error_tabs() {
    // Double backslash to write single backslash in file
    let text = "\tkey: val";
    let mut lexer = ToonLexer::new(text, 2);
    let err = lexer.next().unwrap().unwrap_err();
    assert!(err.contains("Tabs are not allowed"));
}

#[test]
fn test_lexer_error_unterminated_string() {
    // Double backslash quote
    let text = "\"hello";
    let mut lexer = ToonLexer::new(text, 2);
    let err = lexer.next().unwrap().unwrap_err();
    assert!(err.contains("Unterminated quoted string"));
}

#[test]
fn test_lexer_error_invalid_indentation() {
    let text = "root:\n   child: val"; // 3 spaces, indent size 2
    let mut lexer = ToonLexer::new(text, 2);
    // First line tokens ok
    assert!(lexer.next().unwrap().is_ok()); // root
    assert!(lexer.next().unwrap().is_ok()); // :
    assert!(lexer.next().unwrap().is_ok()); // \n
                                            // Next token should be error
    let err = lexer.next().unwrap().unwrap_err();
    assert!(err.contains("Indentation error"));
}

#[test]
fn test_lexer_all_tokens() {
    let text = "[]{},:- -123 # comment";
    let tokens = get_tokens(text);
    assert_eq!(
        tokens,
        vec![
            TokenType::ArrayStart,
            TokenType::ArrayEnd,
            TokenType::BraceStart,
            TokenType::BraceEnd,
            TokenType::Comma,
            TokenType::Colon,
            TokenType::Dash,
            TokenType::Integer(-123),
            TokenType::Comment,
        ]
    );
}

#[test]
fn test_lexer_escapes() {
    let text = r#""\n\t\r\"\\""#;
    let tokens = get_tokens(text);
    assert_eq!(tokens, vec![TokenType::String("\n\t\r\"\\".to_string())]);
}

#[test]
fn test_lexer_invalid_escape() {
    let text = r#""\z""#;
    let mut lexer = ToonLexer::new(text, 2);
    let err = lexer.next().unwrap().unwrap_err();
    assert!(err.contains("Invalid escape character"));
}

#[test]
fn test_lexer_multiple_dedents() {
    let text = "root:\n  child:\n    grand: val\nnext: val";
    let tokens = get_tokens(text);
    let expected = vec![
        TokenType::Identifier("root".to_string()),
        TokenType::Colon,
        TokenType::Newline,
        TokenType::Indent,
        TokenType::Identifier("child".to_string()),
        TokenType::Colon,
        TokenType::Newline,
        TokenType::Indent,
        TokenType::Identifier("grand".to_string()),
        TokenType::Colon,
        TokenType::Identifier("val".to_string()),
        TokenType::Newline,
        TokenType::Dedent,
        TokenType::Dedent,
        TokenType::Identifier("next".to_string()),
        TokenType::Colon,
        TokenType::Identifier("val".to_string()),
    ];
    assert_eq!(tokens, expected);
}

#[test]
fn test_lexer_eof_no_pending_dedents() {
    let mut lexer = ToonLexer::new("", 2);
    let token = lexer.next();
    assert!(token.is_none());
}

#[test]
fn test_lexer_comments_and_empty_lines() {
    let text = "\n  \n# comment\n  # indented comment\nkey: val";
    let tokens = get_tokens(text);
    let expected = vec![
        TokenType::Newline,
        TokenType::Comment,
        TokenType::Newline,
        TokenType::Comment,
        TokenType::Newline,
        TokenType::Identifier("key".to_string()),
        TokenType::Colon,
        TokenType::Identifier("val".to_string()),
    ];
    assert_eq!(tokens, expected);
}
