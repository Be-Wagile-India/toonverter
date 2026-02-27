# TOON Converter CLI Usage Guide

This guide provides examples for using the `toonverter` command-line interface.

## Global Options

*   `--version`: Show the version and exit.
*   `--help`: Show this message and exit.

## Commands

### 1. `toonverter convert`

Convert data between various formats (JSON, TOON, YAML, etc.). Supports streaming for large files.

**Usage:**

```bash
toonverter convert <SOURCE_FILE> <TARGET_FILE> --from <FROM_FORMAT> --to <TO_FORMAT> [OPTIONS]
```

**Options:**

*   `--from <FROM_FORMAT>`: Source format (e.g., `json`, `toon`, `yaml`). (Required)
*   `--to <TO_FORMAT>`: Target format (e.g., `toon`, `json`, `yaml`). (Required)
*   `--compact`: Use compact encoding (no indentation).
*   `--stream`: Use streaming (low memory) processing. Ideal for large JSONL/NDJSON files.

**Examples:**

*   **Convert a JSON file to TOON:**
    ```bash
    toonverter convert data.json data.toon --from json --to toon
    ```
*   **Convert a TOON file to YAML with compact encoding:**
    ```bash
    toonverter convert config.toon config.yaml --from toon --to yaml --compact
    ```
*   **Convert a large JSONL file to another JSONL using streaming:**
    ```bash
    toonverter convert large_data.jsonl processed.jsonl --from jsonl --to jsonl --stream --compact
    ```

### 2. `toonverter encode`

Encode data from an input file to TOON format.

**Usage:**

```bash
toonverter encode <INPUT_FILE> [OPTIONS]
```

**Options:**

*   `-o, --output <OUTPUT_FILE>`: Output file for the encoded TOON. If not provided, prints to stdout.
*   `--compact`: Use compact TOON encoding (no indentation).

**Examples:**

*   **Encode a JSON file to TOON, print to stdout:**
    ```bash
    toonverter encode data.json
    ```
*   **Encode a YAML file to compact TOON, save to file:**
    ```bash
    toonverter encode config.yaml -o config.toon --compact
    ```

### 3. `toonverter decode`

Decode data from a TOON file to another format.

**Usage:**

```bash
toonverter decode <INPUT_FILE> [OPTIONS]
```

**Options:**

*   `-o, --output <OUTPUT_FILE>`: Output file for the decoded data. If not provided, prints to stdout.
*   `-f, --format <FORMAT>`: Output format (default: `json`).

**Examples:**

*   **Decode a TOON file to JSON, print to stdout:**
    ```bash
    toonverter decode data.toon
    ```
*   **Decode a TOON file to YAML, save to file:**
    ```bash
    toonverter decode config.toon -o config.yaml --format yaml
    ```

### 4. `toonverter analyze`

Analyze token usage across different formats for a given input file.

**Usage:**

```bash
toonverter analyze <INPUT_FILE> [OPTIONS]
```

**Options:**

*   `-c, --compare <FORMATS>`: Formats to compare (can be specified multiple times, default: `json`, `yaml`, `toon`).
*   `-m, --model <MODEL>`: Model for token counting (default: `gpt-4`).

**Examples:**

*   **Analyze a JSON file with default comparisons:**
    ```bash
    toonverter analyze data.json
    ```
*   **Analyze a TOON file, comparing only JSON and TOON, using a specific model:**
    ```bash
    toonverter analyze stats.toon --compare json --compare toon --model gpt-3.5-turbo
    ```

### 5. `toonverter formats`

List all supported formats by the `toonverter` library.

**Usage:**

```bash
toonverter formats
```

**Example:**

```bash
toonverter formats
```

### 6. `toonverter infer`

Infer schema from a data file and output it as a JSON schema.

**Usage:**

```bash
toonverter infer <INPUT_FILE> [OPTIONS]
```

**Options:**

*   `-o, --output <OUTPUT_FILE>`: Output file for the schema (JSON format). If not provided, prints to stdout.

**Examples:**

*   **Infer schema from a JSON file, print to stdout:**
    ```bash
    toonverter infer data.json
    ```
*   **Infer schema from a JSONL file, save to file:**
    ```bash
    toonverter infer large_data.jsonl -o large_data_schema.json
    ```

### 7. `toonverter validate`

Validate a data file against a TOON Schema.

**Usage:**

```bash
toonverter validate <INPUT_FILE> [OPTIONS]
```

**Options:**

*   `-s, --schema <SCHEMA_FILE>`: Path to the schema file (JSON format). (Required)
*   `--strict`: Enable strict validation (forbids extra fields).

**Examples:**

*   **Validate a JSON file against a schema:**
    ```bash
    toonverter validate user_data.json --schema user_schema.json
    ```
*   **Validate with strict mode enabled:**
    ```bash
    toonverter validate product.json --schema product_schema.json --strict
    ```

### 8. `toonverter diff`

Compare two data files and report their structural differences.

**Usage:**

```bash
toonverter diff <FILE1> <FILE2> [OPTIONS]
```

**Options:**

*   `--format <FORMAT>`: Output format for the diff (choices: `text`, `json`, `rich`, default: `rich`).

**Examples:**

*   **Compare two JSON files, outputting plain text differences:**
    ```bash
    toonverter diff old_config.json new_config.json --format text
    ```
*   **Compare two TOON files, outputting rich differences to console:**
    ```bash
    toonverter diff v1.toon v2.toon --format rich
    ```

### 9. `toonverter compress`

Compress data using Smart Dictionary Compression (SDC).

**Usage:**

```bash
toonverter compress <INPUT_FILE> --output <OUTPUT_FILE>
```

**Options:**

*   `-o, --output <OUTPUT_FILE>`: Output file for the compressed data. (Required)

**Examples:**

*   **Compress a JSON file:**
    ```bash
    toonverter compress verbose_log.json -o compressed_log.json
    ```

### 10. `toonverter decompress`

Decompress data previously compressed with Smart Dictionary Compression (SDC).

**Usage:**

```bash
toonverter decompress <INPUT_FILE> --output <OUTPUT_FILE>
```

**Options:**

*   `-o, --output <OUTPUT_FILE>`: Output file for the decompressed data. (Required)

**Examples:**

*   **Decompress an SDC file:**
    ```bash
    toonverter decompress compressed_log.json -o decompressed_log.json
    ```

### 11. `toonverter deduplicate`

Detects and eliminates semantically duplicate items within lists in the data structure.

**Usage:**

```bash
toonverter deduplicate <INPUT_FILE> [OPTIONS]
```

**Options:**

*   `-o, --output <OUTPUT_FILE>`: Output file for the deduplicated data. If not provided, prints to stdout.
*   `--model <MODEL>`: Embedding model name (default: `all-MiniLM-L6-v2`).
*   `--threshold <THRESHOLD>`: Similarity threshold (0.0-1.0, default: 0.9).
*   `--language-key <KEY>`: Language key for content (default: `language_code`).

**Examples:**

*   **Deduplicate a list of JSON objects:**
    ```bash
    toonverter deduplicate articles.json -o unique_articles.json
    ```
*   **Deduplicate with a lower similarity threshold:**
    ```bash
    toonverter deduplicate comments.json -o filtered_comments.json --threshold 0.7
    ```

### 12. `toonverter schema-merge`

Merge multiple TOON schemas into one.

**Usage:**

```bash
toonverter schema-merge <SCHEMA_FILES>... [OPTIONS]
```

**Options:**

*   `-o, --output <OUTPUT_FILE>`: Output file for the merged schema (JSON format). If not provided, prints to stdout.

**Examples:**

*   **Merge two schema files:**
    ```bash
    toonverter schema-merge schema1.json schema2.json -o merged_schema.json
    ```
*   **Merge multiple schemas, printing to stdout:**
    ```bash
    toonverter schema-merge customer_schema.json order_schema.json
    ```

### 13. `toonverter batch-convert-json`

Convert multiple JSON files to TOON using Rust batch processing.

**Usage:**

```bash
toonverter batch-convert-json <INPUT_FILES>... [OPTIONS]
```

**Options:**

*   `-o, --output-dir <OUTPUT_DIR>`: Output directory for converted files. If not provided, output will be printed to stdout.

**Examples:**

*   **Convert several JSON files to TOON, saving in an output directory:**
    ```bash
    toonverter batch-convert-json file1.json file2.json file3.json -o converted_toon_files
    ```
*   **Convert JSON files and print TOON output to stdout (one after another):**
    ```bash
    toonverter batch-convert-json file_a.json file_b.json
    ```

### 14. `toonverter batch-convert-toon`

Convert multiple TOON files to JSON using Rust batch processing.

**Usage:**

```bash
toonverter batch-convert-toon <INPUT_FILES>... [OPTIONS]
```

**Options:**

*   `-o, --output-dir <OUTPUT_DIR>`: Output directory for converted files. If not provided, output will be printed to stdout.

**Examples:**

*   **Convert several TOON files to JSON, saving in an output directory:**
    ```bash
    toonverter batch-convert-toon doc1.toon doc2.toon -o converted_json_docs
    ```
*   **Convert TOON files and print JSON output to stdout:**
    ```bash
    toonverter batch-convert-toon item_a.toon item_b.toon
    ```

### 15. `toonverter convert-dir-json`

Convert all JSON files in a directory to TOON using Rust batch processing.

**Usage:**

```bash
toonverter convert-dir-json <INPUT_DIR> [OPTIONS]
```

**Options:**

*   `-r, --recursive`: Recursively process files in subdirectories.
*   `-o, --output-dir <OUTPUT_DIR>`: Output directory for converted files. If not provided, converted files will be placed next to original.

**Examples:**

*   **Convert all JSON files in a directory to TOON:**
    ```bash
    toonverter convert-dir-json my_json_data -o my_toon_data
    ```
*   **Recursively convert JSON files in a directory and its subdirectories:**
    ```bash
    toonverter convert-dir-json project_data -r -o converted_project_data
    ```
*   **Convert JSON files in a directory, placing TOON next to originals:**
    ```bash
    toonverter convert-dir-json data_to_convert
    ```