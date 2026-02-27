use super::ser::Serializer;
use serde::Serialize;

fn to_toon<T: Serialize>(value: &T) -> String {
    let mut buffer = Vec::new();
    let mut serializer = Serializer::new(&mut buffer, 2, ",");
    value.serialize(&mut serializer).unwrap();
    String::from_utf8(buffer).unwrap()
}

#[test]
fn test_serialize_primitives() {
    assert_eq!(to_toon(&true), "true");
    assert_eq!(to_toon(&123), "123");
    assert_eq!(to_toon(&12.34), "12.34");
    assert_eq!(to_toon(&"hello"), "hello");
    assert_eq!(to_toon(&"hello world"), "\"hello world\"");
}

#[test]
fn test_serialize_option() {
    let none: Option<i32> = None;
    let some: Option<i32> = Some(123);
    assert_eq!(to_toon(&none), "null");
    assert_eq!(to_toon(&some), "123");
}

#[test]
fn test_serialize_list() {
    let list = vec![1, 2, 3];
    // [3]:
    //   - 1
    //   - 2
    //   - 3
    let expected = "[3]:\n  - 1\n  - 2\n  - 3";
    assert_eq!(to_toon(&list), expected);
}

#[test]
fn test_serialize_struct() {
    #[derive(Serialize)]
    struct MyStruct {
        a: i32,
        b: String,
    }
    let s = MyStruct {
        a: 1,
        b: "foo".to_string(),
    };
    // a: 1
    // b: foo
    let output = to_toon(&s);
    assert!(output.contains("a: 1"));
    assert!(output.contains("b: foo"));
}

#[test]
fn test_serialize_nested() {
    #[derive(Serialize)]
    struct Nested {
        inner: Vec<i32>,
    }
    let n = Nested { inner: vec![1, 2] };

    let output = to_toon(&n);
    // inner: [2]:\n  - 1\n  - 2
    let expected = "inner: [2]:\n  - 1\n  - 2";
    assert_eq!(output, expected);
}

#[test]
fn test_serialize_bytes() {
    let bytes = b"abc";
    let output = to_toon(&bytes);
    // [3]:\n  - 97\n  - 98\n  - 99
    assert_eq!(output, "[3]:\n  - 97\n  - 98\n  - 99");
}

#[test]
fn test_serialize_tuple() {
    let t = (1, "a");
    let output = to_toon(&t);
    // [2]:\n  - 1\n  - a
    assert_eq!(output, "[2]:\n  - 1\n  - a");
}

#[test]
fn test_serialize_unit_variant() {
    #[derive(Serialize)]
    enum E {
        A,
        B,
    }
    assert_eq!(to_toon(&E::A), "A");
    assert_eq!(to_toon(&E::B), "B");
}

#[test]
fn test_serialize_tuple_variant() {
    #[derive(Serialize)]
    enum E {
        A(i32, i32),
    }
    let output = to_toon(&E::A(1, 2));
    // \n  A: [2]:\n  - 1\n  - 2
    // Since we are at root, newline at start might depend on impl.
    // serialize_tuple_variant writes newline first.
    assert_eq!(output, "\nA: [2]:\n  - 1\n  - 2");
}

#[test]
fn test_serialize_all_types() {
    #[derive(Serialize)]
    struct AllTypes {
        i8: i8,
        i16: i16,
        i32: i32,
        u8: u8,
        u16: u16,
        u32: u32,
        u64: u64,
        f32: f32,
        c: char,
    }
    let s = AllTypes {
        i8: -8,
        i16: -16,
        i32: -32,
        u8: 8,
        u16: 16,
        u32: 32,
        u64: 64,
        f32: 32.5,
        c: 'x',
    };
    let output = to_toon(&s);
    assert!(output.contains("i8: -8"));
    assert!(output.contains("i16: -16"));
    assert!(output.contains("i32: -32"));
    assert!(output.contains("u8: 8"));
    assert!(output.contains("u16: 16"));
    assert!(output.contains("u32: 32"));
    assert!(output.contains("u64: 64"));
    assert!(output.contains("f32: 32.5"));
    assert!(output.contains("c: x"));
}

#[test]
fn test_serialize_unit_struct() {
    #[derive(Serialize)]
    struct Unit;
    assert_eq!(to_toon(&Unit), "null");
}

#[test]
fn test_serialize_newtype_struct() {
    #[derive(Serialize)]
    struct NewType(i32);
    assert_eq!(to_toon(&NewType(42)), "42");
}

#[test]
fn test_serialize_str_special_cases() {
    // is_reserved
    assert_eq!(to_toon(&"true"), "\"true\"");
    assert_eq!(to_toon(&"false"), "\"false\"");
    assert_eq!(to_toon(&"null"), "\"null\"");

    // is_number
    assert_eq!(to_toon(&"123"), "\"123\"");
    assert_eq!(to_toon(&"3.14"), "\"3.14\"");

    // has_special_chars (already covered space in primitives test)
    assert_eq!(to_toon(&"key:value"), "\"key:value\"");
    assert_eq!(to_toon(&"multi\nline"), "\"multi\\nline\"");
    assert_eq!(to_toon(&"[list]"), "\"[list]\"");
    assert_eq!(to_toon(&"{dict}"), "\"{dict}\"");
    assert_eq!(to_toon(&",comma"), "\",comma\"");

    // is_empty
    assert_eq!(to_toon(&""), "\"\"");
}

#[test]
fn test_serialize_f64_special_values() {
    assert_eq!(to_toon(&f64::NAN), "null");
    assert_eq!(to_toon(&f64::INFINITY), "null");
    assert_eq!(to_toon(&-0.0f64), "0");
}

#[test]
fn test_error_io_display() {
    let io_error = std::io::Error::new(std::io::ErrorKind::BrokenPipe, "Broken pipe message");
    let error = super::ser::Error::Io(io_error);
    assert!(format!("{}", error).contains("IO Error: Broken pipe message"));
}

#[test]
fn test_error_message_display() {
    let error = super::ser::Error::Message("Custom error message".to_string());
    assert_eq!(format!("{}", error), "Custom error message");
}

#[test]
fn test_serialize_newtype_variant() {
    #[derive(Serialize)]
    enum E {
        N(i32),
    }
    // \n  N: 42
    assert_eq!(to_toon(&E::N(42)), "\nN: 42");
}
