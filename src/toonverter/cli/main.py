"""Command-line interface for TOON Converter."""

import sys
from pathlib import Path

import click


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
def convert(source: str, target: str, from_format: str, to_format: str, compact: bool) -> None:
    """Convert data between formats."""
    import toonverter as toon

    try:
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
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
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
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
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
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
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
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
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
    from toonverter.schema import SchemaInferrer

    try:
        # Load data
        ext = Path(input_file).suffix[1:]
        data = toon.load(input_file, format=ext if ext else "json")

        # Infer schema
        inferrer = SchemaInferrer()
        # TODO: Support streaming inference for large files
        schema = inferrer.infer(data)
        schema_dict = schema.to_dict()

        if output:
            with Path(output).open("w") as f:
                json.dump(schema_dict, f, indent=2)
            click.echo(f"✓ Schema saved to {output}")
        else:
            click.echo(json.dumps(schema_dict, indent=2))

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
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

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
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
    from toonverter.diff import DiffFormatter

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

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
