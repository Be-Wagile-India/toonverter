"""Command-line interface for TOON Converter."""

import sys
from pathlib import Path

import click

from toonverter.core.exceptions import ToonConverterError


@click.group()
@click.version_option()
def cli() -> None:
    """TOON Converter - Token-Optimized Object Notation for LLMs."""


@cli.command()
@click.argument("source", type=click.Path(exists=True))
@click.argument("target", type=click.Path())
@click.option("--from", "from_format", required=True, help="Source format")
@click.option("--to", "to_format", required=True, help="Target format")
@click.option("--compact", is_flag=True, help="Use compact encoding")
@click.option("--stream", is_flag=True, help="Use streaming (low memory) processing")
def convert(
    source: str, target: str, from_format: str, to_format: str, compact: bool, stream: bool
) -> None:
    """Convert data between formats."""
    import toonverter as toon

    try:
        # Check if streaming is requested or implicitly suitable
        is_streamable_source = from_format in ("json", "jsonl", "ndjson")
        is_streamable_target = to_format in ("json", "jsonl", "ndjson")

        if stream and not (is_streamable_source and is_streamable_target):
            click.echo(
                "Warning: Streaming requested but formats may not fully support it. Attempting...",
                err=True,
            )

        if stream or (is_streamable_source and is_streamable_target):
            # Use streaming path
            try:
                try:
                    from rich.progress import Progress, SpinnerColumn, TextColumn

                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        transient=True,
                    ) as progress:
                        task = progress.add_task(
                            description=f"Streaming {source} → {target}", total=None
                        )

                        def update_progress(n: int) -> None:
                            progress.update(
                                task,
                                advance=n,
                                description=f"Streaming {source} → {target} ({progress.tasks[0].completed} items)",
                            )

                        toon.convert_stream(
                            source,
                            target,
                            from_format,
                            to_format,
                            compact=compact,
                            progress_callback=update_progress,
                        )
                except ImportError:
                    # Fallback if rich is not available
                    toon.convert_stream(source, target, from_format, to_format, compact=compact)

                click.echo(f"✓ Converted {source} → {target} (streamed)")
                return
            except NotImplementedError:
                # Fallback if stream not implemented for some combo
                if stream:
                    raise
                # else continue to normal convert

        # Standard conversion
        try:
            from rich.progress import Progress, SpinnerColumn, TextColumn

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(description=f"Converting {source} → {target}", total=None)
                result = toon.convert(source, target, from_format, to_format, compact=compact)
        except ImportError:
            result = toon.convert(source, target, from_format, to_format, compact=compact)

        if result.success:
            click.echo(f"✓ Converted {source} → {target}")
            if result.source_tokens and result.target_tokens:
                click.echo(f"  Tokens: {result.source_tokens} → {result.target_tokens}")
                if result.savings_percentage:
                    click.echo(f"  Savings: {result.savings_percentage:.1f}%")
        else:
            click.echo(f"✗ Conversion failed: {result.error}", err=True)
            sys.exit(1)
    except ToonConverterError as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Unexpected Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file")
@click.option("--compact", is_flag=True, help="Use compact encoding")
def encode(input_file: str, output: str | None, compact: bool) -> None:
    """Encode data to TOON format."""
    import toonverter as toon

    try:
        # Detect input format from extension
        ext = Path(input_file).suffix[1:]
        data = toon.load(input_file, format=ext if ext else "json")

        # Encode to TOON
        toon_str = toon.encode(data, to_format="toon", compact=compact)

        if output:
            toon.save(data, output, format="toon", compact=compact)
            click.echo(f"✓ Encoded to {output}")
        else:
            click.echo(toon_str)
    except ToonConverterError as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Unexpected Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file")
@click.option("--format", "-f", default="json", help="Output format")
def decode(input_file: str, output: str | None, format: str) -> None:
    """Decode TOON format to other formats."""
    import toonverter as toon

    try:
        data = toon.load(input_file, format="toon")

        if output:
            toon.save(data, output, format=format)
            click.echo(f"✓ Decoded to {output}")
        else:
            encoded = toon.encode(data, to_format=format)
            click.echo(encoded)
    except ToonConverterError as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Unexpected Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--compare",
    "-c",
    multiple=True,
    default=["json", "yaml", "toon"],
    help="Formats to compare",
)
@click.option("--model", "-m", default="gpt-4", help="Model for token counting")
def analyze(input_file: str, compare: tuple[str, ...], model: str) -> None:
    """Analyze token usage across formats."""
    import toonverter as toon

    try:
        # Load data
        ext = Path(input_file).suffix[1:]
        data = toon.load(input_file, format=ext if ext else "json")

        # Analyze
        report = toon.analyze(data, compare_formats=list(compare))

        # Display report
        from toonverter.analysis import format_report

        click.echo(format_report(report, format="text", detailed=False))
    except ToonConverterError as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Unexpected Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def formats() -> None:
    """List supported formats."""
    import toonverter as toon

    click.echo("Supported formats:")
    for fmt in toon.list_formats():
        click.echo(f"  • {fmt}")


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file for schema (JSON)")
def infer(input_file: str, output: str | None) -> None:
    """Infer schema from data file.

    Analyzes the input data and generates a TOON Schema description.
    This schema can be used for validation and documentation.
    """
    import json

    import toonverter as toon
    from toonverter.schema import SchemaField, SchemaInferrer

    try:
        # Infer schema
        inferrer = SchemaInferrer()

        # Streaming path for JSON/JSONL (memory efficient)
        ext = Path(input_file).suffix.lower()

        # Try to stream if format supports it (json, jsonl, ndjson)
        # We can just try load_stream and if it fails (not supported), fall back
        is_streamable = ext in (".json", ".jsonl", ".ndjson")

        if is_streamable:
            stream = toon.load_stream(input_file)

            try:
                from rich.progress import Progress, SpinnerColumn, TextColumn

                # Wrap stream with progress tracking
                def tracking_stream():
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        transient=True,
                    ) as progress:
                        task = progress.add_task(
                            description=f"Inferring schema from {input_file}", total=None
                        )
                        for item in stream:
                            yield item
                            progress.update(
                                task,
                                advance=1,
                                description=f"Inferring schema from {input_file} ({progress.tasks[0].completed} items)",
                            )

                item_schema = inferrer.infer_from_stream(tracking_stream())
            except ImportError:
                item_schema = inferrer.infer_from_stream(stream)

            # Wrap in array to match file structure (List of Items) for standard streaming use case
            schema = SchemaField(type="array", items=item_schema)
        else:
            # Standard load for other formats
            try:
                from rich.progress import Progress, SpinnerColumn, TextColumn

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    transient=True,
                ) as progress:
                    progress.add_task(description=f"Inferring schema from {input_file}", total=None)
                    data = toon.load(input_file, format=ext[1:] if ext else "json")
                    schema = inferrer.infer(data)
            except ImportError:
                data = toon.load(input_file, format=ext[1:] if ext else "json")
                schema = inferrer.infer(data)

        schema_dict = schema.to_dict()

        if output:
            with Path(output).open("w") as f:
                json.dump(schema_dict, f, indent=2)
            click.echo(f"✓ Schema saved to {output}")
        else:
            click.echo(json.dumps(schema_dict, indent=2))

    except ToonConverterError as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Unexpected Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--schema", "-s", type=click.Path(exists=True), required=True, help="Schema file (JSON)"
)
@click.option("--strict", is_flag=True, help="Strict validation (no extra fields)")
def validate(input_file: str, schema: str, strict: bool) -> None:
    """Validate data against a TOON Schema.

    Checks if the input data conforms to the structure defined in the schema file.
    """
    import json

    import toonverter as toon
    from toonverter.schema import SchemaField, SchemaValidator

    try:
        # Load data
        ext = Path(input_file).suffix[1:]
        data = toon.load(input_file, format=ext if ext else "json")

        # Load schema
        with Path(schema).open() as f:
            schema_dict = json.load(f)
        schema_def = SchemaField.from_dict(schema_dict)

        # Validate
        validator = SchemaValidator()
        errors = validator.validate(data, schema_def, strict=strict)

        if errors:
            click.echo(f"✗ Validation failed with {len(errors)} errors:", err=True)
            for error in errors:
                click.echo(f"  - {error}", err=True)
            sys.exit(1)
        else:
            click.echo(f"✓ Data is valid against schema {schema}")

    except ToonConverterError as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Unexpected Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("file1", type=click.Path(exists=True))
@click.argument("file2", type=click.Path(exists=True))
@click.option(
    "--format", type=click.Choice(["text", "json", "rich"]), default="rich", help="Output format"
)
def diff(file1: str, file2: str, format: str) -> None:
    """Compare two data files (TOON, JSON, etc.).

    Computes structural difference between two files.
    """
    import toonverter as toon
    from toonverter.differ import DiffFormatter

    try:
        # Load files
        ext1 = Path(file1).suffix[1:]
        data1 = toon.load(file1, format=ext1 if ext1 else "json")

        ext2 = Path(file2).suffix[1:]
        data2 = toon.load(file2, format=ext2 if ext2 else "json")

        # Compute diff
        result = toon.diff(data1, data2)

        # Format output
        formatter = DiffFormatter()

        if format == "json":
            click.echo(formatter.format_json(result))
        elif format == "text":
            click.echo(formatter.format_text(result))
        else:  # rich
            formatter.print_rich(result)

        if not result.match:
            sys.exit(1)

    except ToonConverterError as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Unexpected Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), required=True, help="Output file")
def compress(input_file: str, output: str) -> None:
    """Compress data using Smart Dictionary Compression."""
    import json

    import toonverter as toon

    try:
        # Load
        ext = Path(input_file).suffix[1:]
        data = toon.load(input_file, format=ext if ext else "json")

        # Compress
        compressed = toon.compress(data)

        # Save (always as JSON/TOON compatible structure)
        with Path(output).open("w") as f:
            json.dump(compressed, f, separators=(",", ":"))

        click.echo(f"✓ Compressed to {output}")

    except ToonConverterError as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Unexpected Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), required=True, help="Output file")
def decompress(input_file: str, output: str) -> None:
    """Decompress SDC data."""
    import json

    import toonverter as toon

    try:
        # Load raw JSON structure
        with Path(input_file).open() as f:
            compressed = json.load(f)

        # Decompress
        data = toon.decompress(compressed)

        # Save
        ext = Path(output).suffix[1:]
        toon.save(data, output, format=ext if ext else "json")

        click.echo(f"✓ Decompressed to {output}")

    except ToonConverterError as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Unexpected Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file")
@click.option("--model", default="all-MiniLM-L6-v2", help="Embedding model name")
@click.option("--threshold", default=0.9, help="Similarity threshold (0.0-1.0)")
@click.option("--language-key", default="language_code", help="Language key for content")
def deduplicate(
    input_file: str,
    output: str | None,
    model: str,
    threshold: float,
    language_key: str,
) -> None:
    """Deduplicate data using semantic analysis.

    Detects and eliminates semantically duplicate items within lists.
    """
    import json

    import toonverter as toon

    try:
        # Load data
        ext = Path(input_file).suffix[1:]
        data = toon.load(input_file, format=ext if ext else "json")

        # Deduplicate
        optimized = toon.deduplicate(
            data,
            model_name=model,
            threshold=threshold,
            language_key=language_key,
        )

        if output:
            # Save using original format if possible
            toon.save(optimized, output, format=ext if ext else "json")
            click.echo(f"✓ Deduplicated data saved to {output}")
        else:
            # Print to stdout
            click.echo(json.dumps(optimized, indent=2, default=str))

    except ToonConverterError as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Unexpected Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("schema_files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option("--output", "-o", type=click.Path(), help="Output file for merged schema")
def schema_merge(schema_files: tuple[str, ...], output: str | None) -> None:
    """Merge multiple TOON schemas into one.

    Combines multiple schema files, widening types where necessary.
    Useful for building a unified schema from multiple data samples.
    """
    import json

    from toonverter.schema import SchemaField

    try:
        if len(schema_files) < 2:
            click.echo("Warning: Merging less than 2 files is just copying.", err=True)

        merged: SchemaField | None = None

        for sf in schema_files:
            with Path(sf).open() as f:
                schema_dict = json.load(f)
            schema = SchemaField.from_dict(schema_dict)

            merged = schema if merged is None else merged.merge(schema)

        if merged is None:
            click.echo("No schemas provided", err=True)
            sys.exit(1)

        result = merged.to_dict()

        if output:
            with Path(output).open("w") as f:
                json.dump(result, f, indent=2)
            click.echo(f"✓ Merged schema saved to {output}")
        else:
            click.echo(json.dumps(result, indent=2))

    except ToonConverterError as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Unexpected Error: {e}", err=True)
        sys.exit(1)


@cli.command("batch-convert-json")
@click.argument("input_files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(file_okay=False, writable=True),
    help="Output directory for converted files. If not provided, output will be printed to stdout.",
)
def batch_convert_json_cmd(input_files: tuple[str, ...], output_dir: str | None) -> None:
    """Convert multiple JSON files to TOON using Rust batch processing."""
    import toonverter as toon

    try:
        results = toon.convert_json_batch(list(input_files), output_dir)
        _report_batch_results(results, "JSON", "TOON", output_dir)
    except NotImplementedError as e:
        click.echo(f"✗ Error: {e}. Ensure Rust extension is available and enabled.", err=True)
        sys.exit(1)
    except ToonConverterError as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Unexpected Error: {e}", err=True)
        sys.exit(1)


@cli.command("batch-convert-toon")
@click.argument("input_files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(file_okay=False, writable=True),
    help="Output directory for converted files. If not provided, output will be printed to stdout.",
)
def batch_convert_toon_cmd(input_files: tuple[str, ...], output_dir: str | None) -> None:
    """Convert multiple TOON files to JSON using Rust batch processing."""
    import toonverter as toon

    try:
        results = toon.convert_toon_batch(list(input_files), output_dir)
        _report_batch_results(results, "TOON", "JSON", output_dir)
    except NotImplementedError as e:
        click.echo(f"✗ Error: {e}. Ensure Rust extension is available and enabled.", err=True)
        sys.exit(1)
    except ToonConverterError as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Unexpected Error: {e}", err=True)
        sys.exit(1)


@cli.command("convert-dir-json")
@click.argument("input_dir", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--recursive",
    "-r",
    is_flag=True,
    help="Recursively process files in subdirectories.",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(file_okay=False, writable=True),
    help="Output directory for converted files. If not provided, converted files will be placed next to original.",
)
def convert_dir_json_cmd(input_dir: str, recursive: bool, output_dir: str | None) -> None:
    """Convert all JSON files in a directory to TOON using Rust batch processing."""
    import toonverter as toon

    try:
        results = toon.convert_json_directory(input_dir, recursive, output_dir)
        _report_batch_results(results, "JSON", "TOON", output_dir)
    except NotImplementedError as e:
        click.echo(f"✗ Error: {e}. Ensure Rust extension is available and enabled.", err=True)
        sys.exit(1)
    except ToonConverterError as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Unexpected Error: {e}", err=True)
        sys.exit(1)


def _report_batch_results(
    results: list[tuple[str, str, bool]],
    from_fmt: str,
    to_fmt: str,
    output_dir: str | None,
) -> None:
    """Helper to report results of batch conversion."""
    success_count = 0
    error_count = 0
    for path, content_or_error, is_error in results:
        if is_error:
            click.echo(f"✗ Failed to convert {path}: {content_or_error}", err=True)
            error_count += 1
        else:
            if output_dir:
                click.echo(f"✓ Converted {path} to {output_dir}/{Path(path).stem}.{to_fmt.lower()}")
            else:
                # Assuming content_or_error is the converted string if no output_dir
                click.echo(f"--- {path} ---\n{content_or_error}\n--- End {path} ---")
            success_count += 1

    click.echo(f"\nSummary: {success_count} succeeded, {error_count} failed.")
    if error_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    cli()
