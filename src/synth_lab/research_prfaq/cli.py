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
from synth_lab.research_prfaq.exporter import export_to_pdf, export_to_markdown, export_to_html

app = typer.Typer()
console = Console()


@app.command()
def generate(
    batch_id: str = typer.Argument(..., help="Research batch ID"),
    output_dir: str = typer.Option("output/reports", "--output-dir", "-o", help="Output directory for PR-FAQ"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed logging"),
):
    """Generate PR-FAQ from research batch report.

    Reads batch summary from output/reports/{batch_id}.md
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
    batch_id: str = typer.Argument(..., help="Batch ID of PR-FAQ document to export"),
    format: str = typer.Option("pdf", "--format", "-f", help="Export format: pdf, md, html"),
    output_dir: str = typer.Option("output/reports", "--output-dir", "-o", help="Base output directory"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed logging"),
):
    """Export PR-FAQ to PDF, Markdown, or HTML format.

    Exports an existing PR-FAQ document to the specified format for different use cases:
    - pdf: Professional presentations and email distribution
    - md: Git-friendly version control and wikis
    - html: Internal documentation and interactive consumption

    Example:
        synthlab research-prfaq export batch_001 --format pdf
        synthlab research-prfaq export batch_001 --format md
        synthlab research-prfaq export batch_001 --format html
    """
    # Setup logging
    if verbose:
        setup_logging()

    # Normalize format aliases
    format_map = {
        "pdf": "pdf",
        "md": "markdown",
        "markdown": "markdown",
        "html": "html",
        "htm": "html"
    }

    if format.lower() not in format_map:
        console.print(f"[red]✗ Invalid format:[/red] {format}")
        console.print(f"[yellow]Valid formats:[/yellow] pdf, md (markdown), html")
        raise typer.Exit(code=1)

    export_format = format_map[format.lower()]

    try:
        # Load PR-FAQ document
        console.print(f"[cyan]Loading PR-FAQ:[/cyan] {batch_id}")
        prfaq = load_prfaq_json(batch_id, output_dir=output_dir)

        console.print(f"[green]✓[/green] Loaded PR-FAQ: {prfaq.press_release.headline}")

        # Create exports directory
        from pathlib import Path
        exports_dir = Path(output_dir) / f"{batch_id}_exports"
        exports_dir.mkdir(parents=True, exist_ok=True)

        # Export based on format
        console.print(f"[cyan]Exporting to {export_format.upper()} format...[/cyan]")

        if export_format == "pdf":
            output_path = export_to_pdf(prfaq, exports_dir / f"{batch_id}_prfaq.pdf")
            format_icon = "📄"
        elif export_format == "markdown":
            output_path = export_to_markdown(prfaq, exports_dir / f"{batch_id}_prfaq.md")
            format_icon = "📝"
        elif export_format == "html":
            output_path = export_to_html(prfaq, exports_dir / f"{batch_id}_prfaq.html")
            format_icon = "🌐"

        # Display success message with file info
        file_size = output_path.stat().st_size
        size_kb = file_size / 1024

        console.print(f"\n[green]✓ Export complete![/green]")
        console.print(Panel(
            f"{format_icon} [bold]{export_format.upper()}[/bold] export successful\n\n"
            f"[cyan]File:[/cyan] {output_path}\n"
            f"[cyan]Size:[/cyan] {size_kb:.1f} KB\n"
            f"[cyan]Format:[/cyan] {export_format}",
            border_style="green",
            title="Export Summary"
        ))

        # Display PR-FAQ metadata
        table = Table(title="PR-FAQ Metadata")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Batch ID", prfaq.batch_id)
        table.add_row("Headline", prfaq.press_release.headline)
        table.add_row("FAQ Items", str(len(prfaq.faq)))
        table.add_row("Version", str(prfaq.version))
        table.add_row("Confidence", f"{prfaq.confidence_score:.2%}")
        table.add_row("Generated", prfaq.generated_at.strftime('%Y-%m-%d %H:%M:%S'))

        console.print(table)

    except FileNotFoundError as e:
        console.print(f"[red]✗ Error:[/red] {str(e)}")
        console.print(f"[yellow]Tip:[/yellow] Ensure PR-FAQ exists at {output_dir}/{batch_id}_prfaq.json")
        console.print(f"[yellow]Generate it first:[/yellow] synthlab research-prfaq generate {batch_id}")
        raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"[red]✗ Export failed:[/red] {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(code=1)


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
