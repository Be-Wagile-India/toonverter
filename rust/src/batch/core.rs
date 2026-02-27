use rayon::prelude::*;
use serde::Serialize;
use std::fs;
use std::io;
use std::path::Path;
use walkdir::WalkDir;

use crate::lexer::ToonLexer;
use crate::parser::ToonParser;
use crate::serde_toon::Serializer as ToonSerializer;

/// Result of a batch operation: (Original Path, Success/Error Message, Is Error)
pub type BatchResult = (String, String, bool);

pub fn convert_single_json_to_toon(
    path: &str,
    output_dir: Option<&str>,
    indent_size: usize,
    delimiter: &str,
) -> BatchResult {
    let file = match fs::File::open(path) {
        Ok(f) => f,
        Err(e) => return (path.to_string(), format!("IO Error: {}", e), true),
    };

    // Mmap
    let mmap = unsafe {
        match memmap2::MmapOptions::new().map(&file) {
            Ok(m) => m,
            Err(e) => return (path.to_string(), format!("Mmap Error: {}", e), true),
        }
    };

    // Parse JSON
    let json_val: serde_json::Value = match serde_json::from_slice(&mmap) {
        Ok(v) => v,
        Err(e) => return (path.to_string(), format!("JSON Parse Error: {}", e), true),
    };

    if let Some(out_dir) = output_dir {
        let filename = Path::new(path)
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("unknown.json");

        let new_filename = if filename.ends_with(".json") {
            filename.replace(".json", ".toon")
        } else {
            format!("{}.toon", filename)
        };

        let dest_path = Path::new(out_dir).join(new_filename);
        let outfile = match fs::File::create(&dest_path) {
            Ok(f) => f,
            Err(e) => return (path.to_string(), format!("Write Error: {}", e), true),
        };
        let mut writer = io::BufWriter::new(outfile);

        let mut serializer = ToonSerializer::new(&mut writer, indent_size, delimiter);
        match json_val.serialize(&mut serializer) {
            Ok(_) => (
                path.to_string(),
                dest_path.to_string_lossy().to_string(),
                false,
            ),
            Err(e) => (path.to_string(), format!("Serialize Error: {}", e), true),
        }
    } else {
        // Memory
        let mut buffer = Vec::new();
        let mut serializer = ToonSerializer::new(&mut buffer, indent_size, delimiter);
        match json_val.serialize(&mut serializer) {
            Ok(_) => {
                let s = String::from_utf8_lossy(&buffer).to_string();
                (path.to_string(), s, false)
            }
            Err(e) => (path.to_string(), format!("Serialize Error: {}", e), true),
        }
    }
}

pub fn convert_single_toon_to_json(
    path: &str,
    output_dir: Option<&str>,
    indent_size: usize,
) -> BatchResult {
    let file = match fs::File::open(path) {
        Ok(f) => f,
        Err(e) => return (path.to_string(), format!("IO Error: {}", e), true),
    };

    let mmap = unsafe {
        match memmap2::MmapOptions::new().map(&file) {
            Ok(m) => m,
            Err(e) => return (path.to_string(), format!("Mmap Error: {}", e), true),
        }
    };

    let content_str = match std::str::from_utf8(&mmap) {
        Ok(s) => s,
        Err(e) => return (path.to_string(), format!("UTF-8 Error: {}", e), true),
    };

    let lexer = ToonLexer::new(content_str, indent_size);
    let mut parser = ToonParser::new(lexer);

    let toon_val = match parser.parse_root() {
        Ok(v) => v,
        Err(e) => return (path.to_string(), format!("Parse Error: {}", e), true),
    };

    if let Some(out_dir) = output_dir {
        let filename = Path::new(path)
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("unknown.toon");

        let new_filename = if filename.ends_with(".toon") {
            filename.replace(".toon", ".json")
        } else {
            format!("{}.json", filename)
        };

        let dest_path = Path::new(out_dir).join(new_filename);
        let outfile = match fs::File::create(&dest_path) {
            Ok(f) => f,
            Err(e) => return (path.to_string(), format!("Write Error: {}", e), true),
        };
        let writer = io::BufWriter::new(outfile);

        match serde_json::to_writer_pretty(writer, &toon_val) {
            Ok(_) => (
                path.to_string(),
                dest_path.to_string_lossy().to_string(),
                false,
            ),
            Err(e) => (
                path.to_string(),
                format!("JSON Serialize Error: {}", e),
                true,
            ),
        }
    } else {
        match serde_json::to_string_pretty(&toon_val) {
            Ok(s) => (path.to_string(), s, false),
            Err(e) => (
                path.to_string(),
                format!("JSON Serialize Error: {}", e),
                true,
            ),
        }
    }
}

pub fn batch_convert_json(
    paths: Vec<String>,
    output_dir: Option<String>,
    indent_size: usize,
    delimiter: &str,
) -> Vec<BatchResult> {
    paths
        .par_iter()
        .map(|path| {
            convert_single_json_to_toon(path, output_dir.as_deref(), indent_size, delimiter)
        })
        .collect()
}

pub fn batch_convert_toon(
    paths: Vec<String>,
    output_dir: Option<String>,
    indent_size: usize,
) -> Vec<BatchResult> {
    paths
        .par_iter()
        .map(|path| convert_single_toon_to_json(path, output_dir.as_deref(), indent_size))
        .collect()
}

pub fn batch_convert_directory(
    dir_path: String,
    recursive: bool,
    output_dir: Option<String>,
    indent_size: usize,
    delimiter: &str,
) -> Vec<BatchResult> {
    let walker = WalkDir::new(dir_path)
        .follow_links(true)
        .max_depth(if recursive { usize::MAX } else { 1 });

    let paths: Vec<String> = walker
        .into_iter()
        .filter_map(|e| e.ok())
        .filter(|e| e.file_type().is_file())
        .filter(|e| e.path().extension().is_some_and(|ext| ext == "json"))
        .map(|e| e.path().to_string_lossy().to_string())
        .collect();

    paths
        .par_iter()
        .map(|path| {
            convert_single_json_to_toon(path, output_dir.as_deref(), indent_size, delimiter)
        })
        .collect()
}
