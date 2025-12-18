use std::fs;
use std::io::Write;

use _toonverter_core::batch::core::{convert_single_json_to_toon, convert_single_toon_to_json};

#[test]
fn test_convert_single_json_to_toon_no_ext() {
    let tmp_dir = tempfile::tempdir().unwrap();
    let input_path = tmp_dir.path().join("testfile");
    fs::write(&input_path, r#"{"key": "value"}"#).unwrap();

    let output_dir_str = tmp_dir.path().to_str().unwrap();
    let (_, output_filename, is_err) =
        convert_single_json_to_toon(input_path.to_str().unwrap(), Some(output_dir_str), 2, ",");

    assert!(!is_err);
    assert!(output_filename.ends_with("testfile.toon"));

    let expected_output_path = tmp_dir.path().join("testfile.toon");
    assert!(expected_output_path.exists());
}

#[test]
fn test_convert_single_toon_to_json_no_ext() {
    let tmp_dir = tempfile::tempdir().unwrap();
    let input_path = tmp_dir.path().join("testfile");
    fs::write(&input_path, "key: value").unwrap();

    let output_dir_str = tmp_dir.path().to_str().unwrap();
    let (_, output_filename, is_err) =
        convert_single_toon_to_json(input_path.to_str().unwrap(), Some(output_dir_str), 2);

    assert!(!is_err);
    assert!(output_filename.ends_with("testfile.json"));

    let expected_output_path = tmp_dir.path().join("testfile.json");
    assert!(expected_output_path.exists());
}

#[test]
fn test_convert_toon_to_json_file_not_found() {
    let non_existent_path = "non_existent.toon";
    let (path, error_msg, is_err) = convert_single_toon_to_json(non_existent_path, None, 2);
    assert!(is_err);
    assert_eq!(path, non_existent_path);
    assert!(error_msg.contains("IO Error"));
}

#[test]
fn test_convert_json_to_toon_invalid_json() {
    let tmp_dir = tempfile::tempdir().unwrap();
    let input_path = tmp_dir.path().join("invalid.json");
    fs::write(&input_path, "{ \"key\": \"value\"").unwrap(); // Malformed JSON

    let (path, error_msg, is_err) =
        convert_single_json_to_toon(input_path.to_str().unwrap(), None, 2, ",");
    assert!(is_err);
    assert_eq!(path, input_path.to_str().unwrap());
    assert!(error_msg.contains("JSON Parse Error"));
}

#[test]
fn test_convert_json_to_toon_file_not_found() {
    let non_existent_path = "non_existent.json";
    let (path, error_msg, is_err) = convert_single_json_to_toon(non_existent_path, None, 2, ",");
    assert!(is_err);
    assert_eq!(path, non_existent_path);
    assert!(error_msg.contains("IO Error"));
}

#[test]
fn test_convert_single_toon_to_json_invalid_utf8() {
    let tmp_dir = tempfile::tempdir().unwrap();
    let input_path = tmp_dir.path().join("invalid.toon");
    let mut file = fs::File::create(&input_path).unwrap();
    file.write_all(b"key: value\xc3\x28").unwrap(); // Invalid UTF-8 sequence

    let (_, error_msg, is_err) = convert_single_toon_to_json(input_path.to_str().unwrap(), None, 2);

    assert!(is_err);
    assert!(error_msg.contains("UTF-8 Error"));
}

#[test]
fn test_convert_single_toon_to_json_invalid_toon_syntax() {
    let tmp_dir = tempfile::tempdir().unwrap();
    let input_path = tmp_dir.path().join("malformed.toon");
    fs::write(&input_path, "key: [unclosed_array").unwrap(); // Malformed TOON

    let (_, error_msg, is_err) = convert_single_toon_to_json(input_path.to_str().unwrap(), None, 2);

    assert!(is_err);
    assert!(error_msg.contains("Parse Error"));
}

#[test]
fn test_convert_single_json_to_toon_write_error() {
    let tmp_dir = tempfile::tempdir().unwrap();
    let input_path = tmp_dir.path().join("test.json");
    fs::write(&input_path, r#"{"key": "value"}"#).unwrap();

    let non_writable_dir = tmp_dir.path().join("non_writable");
    // Attempt to use a non-existent directory as output dir.
    // fs::File::create will fail if the parent directory doesn't exist.
    // Or, more explicitly, try to write to '/' for permissions error (but that's outside tmp).
    // Let's ensure the output_dir exists but its subpath is invalid.
    let output_dir_str = non_writable_dir.to_str().unwrap();

    // Simulate write error by passing a path that cannot be created
    let (_, error_msg, is_err) =
        convert_single_json_to_toon(input_path.to_str().unwrap(), Some(output_dir_str), 2, ",");

    assert!(is_err);
    assert!(error_msg.contains("Write Error"));
}

#[test]
fn test_convert_single_toon_to_json_write_error() {
    let tmp_dir = tempfile::tempdir().unwrap();
    let input_path = tmp_dir.path().join("test.toon");
    fs::write(&input_path, "key: value").unwrap();

    let non_writable_dir = tmp_dir.path().join("non_writable");
    let output_dir_str = non_writable_dir.to_str().unwrap();

    // Simulate write error by passing a path that cannot be created
    let (_, error_msg, is_err) =
        convert_single_toon_to_json(input_path.to_str().unwrap(), Some(output_dir_str), 2);

    assert!(is_err);
    assert!(error_msg.contains("Write Error"));
}
