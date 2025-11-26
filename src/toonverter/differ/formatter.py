"""Formatter for ToonDiff results."""

import json

from .models import ChangeType, DiffResult


try:
    from rich.console import Console
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class DiffFormatter:
    """Formats DiffResult for display."""

    def format_text(self, result: DiffResult) -> str:
        """Format as plain text."""
        if result.match:
            return "✓ No differences found."

        lines = ["Differences found:"]
        for change in result.changes:
            if change.type == ChangeType.ADD:
                lines.append(f"+ {change.path}: {change.new_value}")
            elif change.type == ChangeType.REMOVE:
                lines.append(f"- {change.path}: {change.old_value}")
            elif change.type == ChangeType.CHANGE:
                lines.append(f"~ {change.path}: {change.old_value} -> {change.new_value}")
            elif change.type == ChangeType.TYPE_CHANGE:
                lines.append(
                    f"! {change.path}: Type changed from {change.old_value} to {change.new_value}"
                )
        return "\n".join(lines)

    def format_json(self, result: DiffResult) -> str:
        """Format as JSON."""
        return json.dumps(result.to_dict(), indent=2)

    def print_rich(self, result: DiffResult) -> None:
        """Print formatted output to console using Rich."""
        if not RICH_AVAILABLE:
            print(self.format_text(result))  # noqa: T201
            return

        console = Console()

        if result.match:
            console.print("[bold green]✓ No differences found.[/bold green]")
            return

        table = Table(title="Differences Detected", show_lines=True)
        table.add_column("Type", style="bold")
        table.add_column("Path", style="cyan")
        table.add_column("Old Value", style="red")
        table.add_column("New Value", style="green")

        for change in result.changes:
            change_type = Text(change.type.value.upper())
            if change.type == ChangeType.ADD:
                change_type.stylize("green")
                old_val = "-"
                new_val = str(change.new_value)
            elif change.type == ChangeType.REMOVE:
                change_type.stylize("red")
                old_val = str(change.old_value)
                new_val = "-"
            elif change.type == ChangeType.CHANGE:
                change_type.stylize("yellow")
                old_val = str(change.old_value)
                new_val = str(change.new_value)
            else:  # TYPE_CHANGE
                change_type.stylize("magenta")
                old_val = f"Type: {change.old_value}"
                new_val = f"Type: {change.new_value}"

            table.add_row(change_type, change.path, old_val, new_val)

        console.print(table)
