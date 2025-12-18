use super::core::ToonParser;
use crate::ir::ToonValue;
use crate::lexer::ToonLexer;
use indexmap::IndexMap;

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
    assert!(result.unwrap_err().contains("Expected ']'"));
}

#[test]
fn test_parse_tabular_header_and_content() {
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
        // Check second row dict
        if let ToonValue::Dict(d) = &list[1] {
            assert_eq!(d.get("a"), Some(&ToonValue::Integer(3)));
            assert_eq!(d.get("b"), Some(&ToonValue::Integer(4)));
        } else {
            panic!("Row 2 not dict");
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

#[test]
fn test_parse_root_unexpected_token_error() {
    let text = "{a: 1}\n- item"; // Valid inline object followed by dash (not valid at root level after object)
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_root();
    assert!(result.is_err());
    assert!(result
        .unwrap_err()
        .contains("Extra tokens found after root element"));
}

#[test]
fn test_parse_value_unexpected_token_error() {
    let text = "key: [invalid"; // Error in parse_array_header_and_content will bubble up
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_value();
    assert!(result.is_err());
    assert!(result
        .unwrap_err()
        .contains("Expected ']' after array length"));
}

#[test]
fn test_parse_array_header_implicit_schema() {
    let text = "[abc]: 1,2,3";
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_array_header_and_content().unwrap(); // Expect success
    if let ToonValue::List(list) = result {
        assert_eq!(list.len(), 3); // Expected 3 elements
        let mut expected_d1 = IndexMap::new();
        expected_d1.insert("abc".to_string(), ToonValue::Integer(1));
        assert_eq!(&list[0], &ToonValue::Dict(expected_d1));

        let mut expected_d2 = IndexMap::new();
        expected_d2.insert("abc".to_string(), ToonValue::Integer(2));
        assert_eq!(&list[1], &ToonValue::Dict(expected_d2));

        let mut expected_d3 = IndexMap::new();
        expected_d3.insert("abc".to_string(), ToonValue::Integer(3));
        assert_eq!(&list[2], &ToonValue::Dict(expected_d3));
    } else {
        panic!("Expected List");
    }
}

#[test]
fn test_parse_array_header_expected_bracket_error() {
    let text = "[3: 1,2,3";
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_array_header_and_content();
    assert!(result.is_err());
    assert!(result
        .unwrap_err()
        .contains("Expected ']' after array length, found Colon at line 0 col 3"));
}

#[test]
fn test_parse_array_header_expected_colon_error() {
    let text = "[3] 1,2,3";
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_array_header_and_content();
    assert!(result.is_err());
    assert!(result
        .unwrap_err()
        .contains("Expected ':' after array header, found Integer(1) at line 0 col 5"));
}

#[test]
fn test_parse_tabular_header_empty_fields() {
    let text = "[1]{}:\n  \n"; // Correct input to signify tabular array with 1 empty row
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_array_header_and_content().unwrap();
    // It should parse successfully as a List with one empty row
    if let ToonValue::List(list) = result {
        assert_eq!(list.len(), 1);
        if let ToonValue::Dict(d) = &list[0] {
            assert!(d.is_empty());
        } else {
            panic!("Expected dict in list");
        }
    } else {
        panic!("Expected list");
    }
}

#[test]
fn test_parse_list_content_unexpected_token_error() {
    let text = "- item1\n  invalid"; // 'invalid' is not '-'
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_list_content();
    assert!(result.is_err());
    assert!(result.unwrap_err().contains("Expected '-' or end of list"));
}

#[test]
fn test_parse_object_indented_expected_key_error() {
    let text = "root:\n  : value"; // Missing key
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_object_indented();
    assert!(result.is_err());
    assert!(result.unwrap_err().contains("Expected key"));
}

#[test]
fn test_parse_object_indented_expected_colon_error() {
    let text = "root:\n  key value"; // Missing colon
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_object_indented();
    assert!(result.is_err());
    assert!(result.unwrap_err().contains("Expected colon after key"));
}

#[test]
fn test_parse_inline_object_expected_key_error() {
    let text = "{a: 1, :}"; // Missing key
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_inline_object();
    assert!(result.is_err());
    assert!(result.unwrap_err().contains("Expected key"));
}

#[test]
fn test_parse_kv_pair_expected_key_error() {
    let text = ": value"; // Starts with colon
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_kv_pair(); // No arguments
    assert!(result.is_err());
    assert!(result
        .unwrap_err()
        .contains("Expected identifier or string as key"));
}

#[test]
fn test_parse_root_empty_dict() {
    let text = "";
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_root().unwrap();
    match result {
        ToonValue::Dict(d) => assert!(d.is_empty()),
        _ => panic!("Expected empty dict"),
    }
}

#[test]
fn test_parse_root_array_inline() {
    let text = "[3]: 1,2,3";
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_root().unwrap();
    assert_eq!(
        result,
        ToonValue::List(vec![
            ToonValue::Integer(1),
            ToonValue::Integer(2),
            ToonValue::Integer(3)
        ])
    );
}

#[test]
fn test_parse_root_array_list() {
    let text = "[2]:\n  - item1\n  - item2";
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_root().unwrap();
    assert_eq!(
        result,
        ToonValue::List(vec![
            ToonValue::String("item1".to_string()),
            ToonValue::String("item2".to_string())
        ])
    );
}

#[test]
fn test_parse_root_object_indented() {
    let text = "root:\n  key: value";
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_root().unwrap();
    let mut expected_nested = IndexMap::new();
    expected_nested.insert("key".to_string(), ToonValue::String("value".to_string()));
    let mut root_dict = IndexMap::new();
    root_dict.insert("root".to_string(), ToonValue::Dict(expected_nested));
    assert_eq!(result, ToonValue::Dict(root_dict));
}

#[test]
fn test_parse_value_nested_object_via_indent() {
    let text = "key:\n  nested: value";
    // We're testing parse_value, which for 'key:' should lead to parse_object_indented
    // The parser state needs to be advanced correctly to simulate parsing 'key:' and then the indented object.
    // The easiest way is to wrap it in a root dict and parse the root.
    let text_root = format!("root: {}\n", text); // Create a root object to test parsing
    let lexer_root = ToonLexer::new(&text_root, 2);
    let mut parser_root = ToonParser::new(lexer_root);
    let parsed_root = parser_root.parse_root().unwrap();

    let mut expected_nested = IndexMap::new();
    expected_nested.insert("nested".to_string(), ToonValue::String("value".to_string()));
    let mut expected_key = IndexMap::new();
    expected_key.insert("key".to_string(), ToonValue::Dict(expected_nested));
    let mut expected_root = IndexMap::new();
    expected_root.insert("root".to_string(), ToonValue::Dict(expected_key));
    assert_eq!(parsed_root, ToonValue::Dict(expected_root));
}

#[test]
fn test_parse_value_dash_list() {
    let text = "- item1\n- item2";
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_value().unwrap();
    assert_eq!(
        result,
        ToonValue::List(vec![
            ToonValue::String("item1".to_string()),
            ToonValue::String("item2".to_string())
        ])
    );
}

#[test]
fn test_parse_array_header_tabular_with_data() {
    let text = "[2]{a,b}:\n  1,2\n  3,4";
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_array_header_and_content().unwrap();
    if let ToonValue::List(list) = result {
        assert_eq!(list.len(), 2);
        if let ToonValue::Dict(d1) = &list[0] {
            assert_eq!(d1.get("a"), Some(&ToonValue::Integer(1)));
            assert_eq!(d1.get("b"), Some(&ToonValue::Integer(2)));
        } else {
            panic!("Expected Dict");
        }
        if let ToonValue::Dict(d2) = &list[1] {
            assert_eq!(d2.get("a"), Some(&ToonValue::Integer(3)));
            assert_eq!(d2.get("b"), Some(&ToonValue::Integer(4)));
        } else {
            panic!("Expected Dict");
        }
    } else {
        panic!("Expected List");
    }
}



#[test]
fn test_parse_value_object_with_indent() {
    let text = "{\n  key: value\n}";
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_value().unwrap();
    let mut expected = IndexMap::new();
    expected.insert("key".to_string(), ToonValue::String("value".to_string()));
    assert_eq!(result, ToonValue::Dict(expected));
}

#[test]
fn test_parse_root_simple_object() {
    let text = "name: Alice";
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_root().unwrap();
    let mut expected = IndexMap::new();
    expected.insert("name".to_string(), ToonValue::String("Alice".to_string()));
    assert_eq!(result, ToonValue::Dict(expected));
}

#[test]
fn test_parse_value_inline_object() {
    let text = "{key1: val1, key2: val2}";
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_value().unwrap();
    let mut expected = IndexMap::new();
    expected.insert("key1".to_string(), ToonValue::String("val1".to_string()));
    expected.insert("key2".to_string(), ToonValue::String("val2".to_string()));
    assert_eq!(result, ToonValue::Dict(expected));
}



#[test]
fn test_parse_array_header_compact_unexpected_token() {
    let text = "[1] field1, 1: val"; // Unexpected number inside compact header fields
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_array_header_and_content();
    assert!(result.is_err());
    assert!(result
        .unwrap_err()
        .contains("Expected ':' after array header, found Identifier(\"field1\") at line 0 col 5"));
}

#[test]
fn test_parse_array_header_single_field_trailing_comma() {
    let text = "[1]{a,}:\n  \n"; // Correct input to signify tabular array with 1 empty row and field 'a'
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_array_header_and_content().unwrap(); // Expect success
    if let ToonValue::List(list) = result {
        assert_eq!(list.len(), 1); // One row (from length 1)
        if let ToonValue::Dict(d) = &list[0] {
            assert_eq!(d.get("a"), Some(&ToonValue::Null)); // 'a' with null value as no data
        } else {
            panic!("Expected Dict");
        }
    } else {
        panic!("Expected List");
    }
}

#[test]
fn test_parse_tabular_content_indent_level_mismatch() {
    let text = "[1]{a}:\n    1"; // Too much indent
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_array_header_and_content();
    assert!(result.is_err());
    assert!(result.unwrap_err().contains("Expected key, Dedent or EOF"));
}

#[test]
fn test_parse_implicit_inline_object_eof() {
    let text = "key: val"; // EOF immediately after val
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_value().unwrap();
    if let ToonValue::Dict(d) = result {
        assert_eq!(d.get("key"), Some(&ToonValue::String("val".to_string())));
    } else {
        panic!("Expected Dict");
    }
}

#[test]
fn test_parse_tabular_explicit_null() {
    let text = "[1]{a}:\n  null";
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_array_header_and_content().unwrap();
    if let ToonValue::List(list) = result {
        if let ToonValue::Dict(d) = &list[0] {
            assert_eq!(d.get("a"), Some(&ToonValue::Null));
        } else {
            panic!("Expected Dict");
        }
    }
}

#[test]
fn test_parse_array_header_unexpected_delimiter() {
    let text = "[1 | 2] : 1"; // 2 is unexpected after delimiter | (expected ])
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_array_header_and_content();
    assert!(result.is_err());
    assert!(result
        .unwrap_err()
        .contains("Expected ']' after array length"));
}

#[test]
fn test_parse_array_header_missing_colon_compact() {
    let text = "[1]a,b 1,2"; // '1' is Integer, not allowed in header
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_array_header_and_content();
    assert!(result.is_err());
    assert!(result
        .unwrap_err()
        .contains("Expected ':' after array header, found Identifier(\"a\") at line 0 col 4"));
}

#[test]
fn test_parse_lexer_error() {
    let text = "key: \"unterminated";
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_root();
    assert!(result.is_err());
    assert!(result.unwrap_err().contains("Lexer error"));
}

#[test]
fn test_peek_next_error() {
    let text = "key \"unterminated";
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_root();
    assert!(result.is_err());
    assert!(result.unwrap_err().contains("Lexer error"));
}

#[test]
fn test_parse_array_header_explicit_fields_error() {
    let text = "[1]{:}: 1"; // Colon inside explicit fields
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_array_header_and_content();
    assert!(result.is_err());
    let err_msg = result.unwrap_err();
    assert!(err_msg.contains("Expected field name or '}'"));
}





#[test]
fn test_parse_root_comments_newlines() {
    let text = "\n# comment\n\nkey: val";
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_root().unwrap();
    if let ToonValue::Dict(d) = result {
        assert_eq!(d.get("key"), Some(&ToonValue::String("val".to_string())));
    } else {
        panic!("Expected Dict");
    }
}

#[test]
fn test_parse_root_indented_start() {
    let text = "  key: val"; // Starts with indentation
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_root().unwrap();
    if let ToonValue::Dict(d) = result {
        assert_eq!(d.get("key"), Some(&ToonValue::String("val".to_string())));
    } else {
        panic!("Expected Dict");
    }
}

#[test]
fn test_parse_array_header_with_delimiter() {
    let text = "[3 |]: 1,2,3";
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_array_header_and_content().unwrap();
    assert_eq!(
        result,
        ToonValue::List(vec![
            ToonValue::Integer(1),
            ToonValue::Integer(2),
            ToonValue::Integer(3)
        ])
    );
}

#[test]
fn test_parse_kv_pair_array_value() {
    let text = "key: [3]: 1,2,3";
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let mut dict = IndexMap::new();
    let (key, value) = parser.parse_kv_pair().unwrap();
    dict.insert(key, value);
    assert_eq!(
        dict.get("key"),
        Some(&ToonValue::List(vec![
            ToonValue::Integer(1),
            ToonValue::Integer(2),
            ToonValue::Integer(3)
        ]))
    );
}

#[test]
fn test_parse_value_bracestart_fallback_to_inline() {
    let text = "{\n  # This is a comment\n  key: val\n}";
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_value().unwrap();
    let mut expected = IndexMap::new();
    expected.insert("key".to_string(), ToonValue::String("val".to_string()));
    assert_eq!(result, ToonValue::Dict(expected));
}

#[test]
fn test_parse_implicit_inline_object_continuation() {
    let text = "key1: val1, key2: val2\n  key3: val3";
    // For implicit inline object to be parsed, it usually needs context like being a value or root?
    // In parse_value, Identifier triggers peek for colon.
    // "key1: ..." is start of object.
    // But parse_value handles "key1: ..." via parse_implicit_inline_object IF next is colon.
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_value().unwrap();

    if let ToonValue::Dict(d) = result {
        assert_eq!(d.get("key1"), Some(&ToonValue::String("val1".to_string())));
        assert_eq!(d.get("key2"), Some(&ToonValue::String("val2".to_string())));
        assert_eq!(d.get("key3"), Some(&ToonValue::String("val3".to_string())));
    } else {
        panic!("Expected Dict");
    }
}

#[test]
fn test_parse_array_implicit_schema_inline_no_length() {
    let text = "[abc]: 1, 2";
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_root().unwrap(); // Parsing as root
    if let ToonValue::List(list) = result {
        assert_eq!(list.len(), 2);
        if let ToonValue::Dict(d1) = &list[0] {
            assert_eq!(d1.get("abc"), Some(&ToonValue::Integer(1)));
        }
        if let ToonValue::Dict(d2) = &list[1] {
            assert_eq!(d2.get("abc"), Some(&ToonValue::Integer(2)));
        }
    } else {
        panic!("Expected List");
    }
}

#[test]
fn test_parse_tabular_short_row() {
    // Use double comma to force Null for the 3rd field 'c'
    // Row 1: 1 (a), 2 (b), Null (c)
    // Row 2: 3 (a), Null (b), Null (c)
    let text = "[2]{a,b,c}:\n  1, 2,,\n  3";
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_array_header_and_content().unwrap();

    if let ToonValue::List(list) = result {
        // Row 1: 1, 2, Null
        if let ToonValue::Dict(d1) = &list[0] {
            assert_eq!(d1.get("a"), Some(&ToonValue::Integer(1)));
            assert_eq!(d1.get("b"), Some(&ToonValue::Integer(2)));
            assert_eq!(d1.get("c"), Some(&ToonValue::Null));
        }
        // Row 2: 3, Null, Null
        if let ToonValue::Dict(d2) = &list[1] {
            assert_eq!(d2.get("a"), Some(&ToonValue::Integer(3)));
            assert_eq!(d2.get("b"), Some(&ToonValue::Null));
            assert_eq!(d2.get("c"), Some(&ToonValue::Null));
        }
    }
}

#[test]
fn test_parse_root_extra_tokens_after_value() {
    // Use inline object so parsing finishes clearly, leaving 'extra' as noise
    let text = "{key: val} extra";
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_root();
    assert!(result.is_err());
    assert!(result.unwrap_err().contains("Extra tokens found"));
}



#[test]
fn test_parse_array_implicit_schema_override() {
    let text = "[abc]{def}: 1, 2";
    let lexer = ToonLexer::new(text, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_root().unwrap();
    
    if let ToonValue::List(list) = result {
        assert_eq!(list.len(), 2);
        if let ToonValue::Dict(d1) = &list[0] {
            assert_eq!(d1.get("def"), Some(&ToonValue::Integer(1)));
            assert_eq!(d1.get("abc"), None);
        }
        if let ToonValue::Dict(d2) = &list[1] {
            assert_eq!(d2.get("def"), Some(&ToonValue::Integer(2)));
        }
    } else {
        panic!("Expected List");
    }
}

#[test]
fn test_parse_nested_list_indentation() {
    let text_nested = "-\n  - sub1\n  - sub2"; 
    let lexer = ToonLexer::new(text_nested, 2);
    let mut parser = ToonParser::new(lexer);
    let result = parser.parse_root().unwrap();
    
    if let ToonValue::List(l) = result {
        assert_eq!(l.len(), 1); 
        if let ToonValue::List(sub) = &l[0] {
            assert_eq!(sub.len(), 2);
            assert_eq!(sub[0], ToonValue::String("sub1".to_string()));
            assert_eq!(sub[1], ToonValue::String("sub2".to_string()));
        } else {
             panic!("Expected sublist, got {:?}", l[0]);
        }
    }
}

#[test]
fn test_parse_primitives() {
    let text_float = "3.14";
    let mut parser = ToonParser::new(ToonLexer::new(text_float, 2));
    assert_eq!(parser.parse_value().unwrap(), ToonValue::Float(3.14));

    let text_bool = "true";
    let mut parser = ToonParser::new(ToonLexer::new(text_bool, 2));
    assert_eq!(parser.parse_value().unwrap(), ToonValue::Boolean(true));

    let text_null = "null";
    let mut parser = ToonParser::new(ToonLexer::new(text_null, 2));
    assert_eq!(parser.parse_value().unwrap(), ToonValue::Null);
}

