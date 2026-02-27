use super::core::{batch_convert_directory, batch_convert_json, batch_convert_toon};
use std::fs;
use std::io::Write;
use tempfile::{NamedTempFile, TempDir};

#[test]
fn test_batch_memory_success() {
    let mut file = NamedTempFile::new().unwrap();
    write!(file, "{{\"key\": \"value\"}}").unwrap();
    let path = file.path().to_str().unwrap().to_string();

    let results = batch_convert_json(vec![path.clone()], None, 2, ",");
    assert_eq!(results.len(), 1);
    let (p, content, _is_err) = &results[0];
    assert_eq!(p, &path);
    assert!(content.contains("key: value"));
}

#[test]
fn test_batch_toon_to_json() {
    let mut file = NamedTempFile::new().unwrap();
    write!(file, "key: value").unwrap();
    let path = file.path().to_str().unwrap().to_string();

    let results = batch_convert_toon(vec![path.clone()], None, 2);
    assert_eq!(results.len(), 1);
    let (_, content, is_err) = &results[0];
    assert!(!is_err);
    assert!(content.contains("\"key\": \"value\""));
}

#[test]
fn test_batch_disk_success() {
    let mut file = NamedTempFile::new().unwrap();
    write!(file, "[1, 2]").unwrap();
    let path = file.path().to_str().unwrap().to_string();

    let out_dir = TempDir::new().unwrap();
    let out_dir_str = out_dir.path().to_str().unwrap().to_string();

    let results = batch_convert_json(vec![path.clone()], Some(out_dir_str.clone()), 2, ",");

    let (p, out_path, is_err) = &results[0];
    assert_eq!(p, &path);
    assert!(!is_err);

    let saved_content = fs::read_to_string(out_path).unwrap();
    assert!(saved_content.contains("[2]:"));
}

#[test]
fn test_batch_error_handling() {
    let results = batch_convert_json(vec!["non_existent_file.json".to_string()], None, 2, ",");
    let (_, msg, is_err) = &results[0];
    assert!(is_err);
    assert!(msg.contains("IO Error"));
}

#[test]
fn test_batch_toon_to_json_disk() {
    let mut file = NamedTempFile::new().unwrap();
    write!(file, "key: value").unwrap();
    let path = file.path().to_str().unwrap().to_string();

    let out_dir = TempDir::new().unwrap();
    let out_dir_str = out_dir.path().to_str().unwrap().to_string();

    let results = batch_convert_toon(vec![path.clone()], Some(out_dir_str.clone()), 2);

    let (p, out_path, is_err) = &results[0];
    assert_eq!(p, &path);
    assert!(!is_err);

    let saved_content = fs::read_to_string(out_path).unwrap();
    assert!(saved_content.contains("\"key\": \"value\""));
}

#[test]
fn test_batch_toon_error_handling() {
    let results = batch_convert_toon(vec!["non_existent_file.toon".to_string()], None, 2);
    let (_, msg, is_err) = &results[0];
    assert!(is_err);
    assert!(msg.contains("IO Error"));
}

#[test]
fn test_batch_toon_parse_error() {
    let mut file = NamedTempFile::new().unwrap();
    write!(file, "key: [unclosed").unwrap();
    let path = file.path().to_str().unwrap().to_string();

    let results = batch_convert_toon(vec![path.clone()], None, 2);
    let (_, msg, is_err) = &results[0];
    assert!(is_err);
    assert!(msg.contains("Parse Error"));
}

#[test]
fn test_batch_json_parse_error() {
    let mut file = NamedTempFile::new().unwrap();
    write!(file, "{{key: unquoted}}").unwrap(); // Invalid JSON
    let path = file.path().to_str().unwrap().to_string();
    let results = batch_convert_json(vec![path.clone()], None, 2, ",");
    let (_, msg, is_err) = &results[0];
    assert!(is_err);
    assert!(msg.contains("JSON Parse Error"));
}

#[test]
fn test_batch_extension_handling() {
    let mut file = NamedTempFile::new().unwrap();
    write!(file, "{{\"a\": 1}}").unwrap();
    file.flush().unwrap();
    let temp_dir = TempDir::new().unwrap();
    // Copy content to a .txt file in temp dir
    let path = temp_dir.path().join("data.txt");
    fs::copy(file.path(), &path).unwrap();
    let path_str = path.to_string_lossy().to_string();

    let out_dir = TempDir::new().unwrap();
    let out_dir_str = out_dir.path().to_string_lossy().to_string();

    let results = batch_convert_json(vec![path_str.clone()], Some(out_dir_str.clone()), 2, ",");
    let (_, out_path, is_err) = &results[0];
    assert!(!is_err);
    assert!(out_path.ends_with("data.txt.toon"));
}

#[test]
fn test_batch_directory_options() {
    let temp_dir = TempDir::new().unwrap();
    fs::write(temp_dir.path().join("root.json"), "{{\"a\": 1}}").unwrap();
    fs::write(temp_dir.path().join("root.txt"), "ignored").unwrap();
    let sub_dir = temp_dir.path().join("subdir");
    fs::create_dir(&sub_dir).unwrap();
    fs::write(sub_dir.join("sub.json"), "{{\"b\": 2}}").unwrap();

    let path_str = temp_dir.path().to_string_lossy().to_string();

    let results = batch_convert_directory(path_str.clone(), false, None, 2, ",");
    assert_eq!(results.len(), 1);
    assert!(results[0].0.ends_with("root.json"));

    let results_rec = batch_convert_directory(path_str, true, None, 2, ",");
    assert_eq!(results_rec.len(), 2);
}

#[test]
fn test_batch_utf8_error() {
    let mut file = NamedTempFile::new().unwrap();
    file.write_all(&[0x80, 0x81]).unwrap(); // Invalid UTF-8
    let path = file.path().to_str().unwrap().to_string();

    let results = batch_convert_toon(vec![path], None, 2);
    let (_, msg, is_err) = &results[0];
    assert!(is_err);
    assert!(msg.contains("UTF-8 Error"));
}

#[test]
fn test_batch_mmap_error() {
    let temp_dir = TempDir::new().unwrap();
    let path = temp_dir.path().to_string_lossy().to_string();

    let results = batch_convert_json(vec![path.clone()], None, 2, ",");
    let (_, msg, is_err) = &results[0];
    assert!(is_err);
    assert!(msg.contains("Mmap Error"));

    let results_toon = batch_convert_toon(vec![path], None, 2);
    let (_, msg_toon, is_err_toon) = &results_toon[0];
    assert!(is_err_toon);
    assert!(msg_toon.contains("Mmap Error"));
}

#[test]
fn test_batch_json_write_error() {
    let mut file = NamedTempFile::new().unwrap();
    write!(file, "{{\"key\": \"value\"}}").unwrap();
    let path = file.path().to_str().unwrap().to_string();

    let temp_dir = TempDir::new().unwrap();
    let output_dir_str = temp_dir
        .path()
        .join("does_not_exist")
        .to_str()
        .unwrap()
        .to_string();

    let results = batch_convert_json(vec![path], Some(output_dir_str), 2, ",");
    let (_, msg, is_err) = &results[0];
    assert!(is_err);
    assert!(msg.contains("Write Error"));
}

#[test]
fn test_batch_toon_write_error() {
    let mut file = NamedTempFile::new().unwrap();
    write!(file, "key: value").unwrap();
    let path = file.path().to_str().unwrap().to_string();

    let temp_dir = TempDir::new().unwrap();
    let output_dir_str = temp_dir
        .path()
        .join("does_not_exist")
        .to_str()
        .unwrap()
        .to_string();

    let results = batch_convert_toon(vec![path], Some(output_dir_str), 2);
    let (_, msg, is_err) = &results[0];
    assert!(is_err);
    assert!(msg.contains("Write Error"));
}
