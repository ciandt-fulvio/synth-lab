"""Command-line interface for PR-FAQ generation.

Provides 5 commands for PR-FAQ workflow:
- generate: Create PR-FAQ from research batch report
- edit: Modify existing PR-FAQ document
- export: Export PR-FAQ to multiple formats
- list: Show all generated PR-FAQs
- history: View PR-FAQ version history

Third-party documentation:
- Typer: https://typer.tiangolo.com/

Sample usage:
    synthlab research-prfaq generate --batch-id batch_001
    synthlab research-prfaq edit --prfaq-id batch_001
    synthlab research-prfaq export --prfaq-id batch_001 --format pdf
    synthlab research-prfaq list
    synthlab research-prfaq history --batch-id batch_001
"""

import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from synth_lab.research_prfaq.models import setup_logging, parse_batch_summary
from synth_lab.research_prfaq.generator import generate_prfaq, save_prfaq_json, load_prfaq_json

app = typer.Typer()
console = Console()


@app.command()
def generate(
    batch_id: str = typer.Argument(..., help="Research batch ID"),
    output_dir: str = typer.Option("data/outputs/prfaq", "--output-dir", "-o", help="Output directory for PR-FAQ"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed logging"),
):
    """Generate PR-FAQ from research batch report.

    Reads batch summary from data/transcripts/{batch_id}/batch_summary.json
    and generates a PR-FAQ document using hybrid chain-of-thought + structured output.

    Example:
        synthlab research-prfaq generate test_batch_001
    """
    # Setup logging
    if verbose:
        setup_logging()

    try:
        console.print(f"[cyan]Loading research batch:[/cyan] {batch_id}")

        # Parse batch summary
        report = parse_batch_summary(batch_id)

        console.print(f"[green]✓[/green] Parsed batch summary: {len(report.sections)} sections found")

        # Generate PR-FAQ
        console.print("[cyan]Generating PR-FAQ with OpenAI API...[/cyan]")
        prfaq = generate_prfaq(report)

        console.print(f"[green]✓[/green] Generated PR-FAQ with {len(prfaq.faq)} FAQ items")
        console.print(f"[cyan]Confidence score:[/cyan] {prfaq.confidence_score:.2%}")

        # Save to JSON
        output_path = save_prfaq_json(prfaq, output_dir=output_dir)

        console.print(f"[green]✓[/green] Saved PR-FAQ to: {output_path}")

        # Display summary
        console.print("\n[bold]Press Release Summary:[/bold]")
        console.print(Panel(
            f"[bold]{prfaq.press_release.headline}[/bold]\n\n"
            f"{prfaq.press_release.one_liner}",
            border_style="green"
        ))

        # Display FAQ count by segment
        segments = {}
        for item in prfaq.faq:
            segments[item.customer_segment] = segments.get(item.customer_segment, 0) + 1

        table = Table(title="FAQ Items by Customer Segment")
        table.add_column("Customer Segment", style="cyan")
        table.add_column("Count", justify="right", style="green")

        for segment, count in sorted(segments.items()):
            table.add_row(segment, str(count))

        console.print(table)

        console.print(f"\n[green]✓ PR-FAQ generation complete![/green]")

    except FileNotFoundError as e:
        console.print(f"[red]✗ Error:[/red] {str(e)}")
        console.print(f"[yellow]Tip:[/yellow] Ensure batch summary exists at data/transcripts/{batch_id}/batch_summary.json")
        raise typer.Exit(code=1)

    except ValueError as e:
        console.print(f"[red]✗ Validation error:[/red] {str(e)}")
        raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"[red]✗ Unexpected error:[/red] {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(code=1)


@app.command()
def edit(
    prfaq_id: str = typer.Argument(..., help="PR-FAQ document ID"),
):
    """Edit existing PR-FAQ document."""
    # Stub implementation - Phase 4
    raise NotImplementedError("edit command is implemented in Phase 4")


@app.command()
def export(
    prfaq_id: str = typer.Argument(..., help="PR-FAQ document ID"),
    format: str = typer.Option("pdf", "--format", "-f", help="Export format: pdf, markdown, html"),
):
    """Export PR-FAQ to specified format."""
    # Stub implementation - Phase 5
    raise NotImplementedError("export command is implemented in Phase 5")


@app.command()
def list(
    batch_id: Optional[str] = typer.Option(None, "--batch-id", help="Filter by batch ID"),
):
    """List all generated PR-FAQs."""
    # Stub implementation - Phase 6
    raise NotImplementedError("list command is implemented in Phase 6")


@app.command()
def history(
    batch_id: str = typer.Argument(..., help="Research batch ID"),
    format: str = typer.Option("table", "--format", "-f", help="Output format: table, json"),
):
    """Show PR-FAQ version history and changes."""
    # Stub implementation - Phase 6
    raise NotImplementedError("history command is implemented in Phase 6")


if __name__ == "__main__":
    app()
