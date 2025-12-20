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

from synth_lab.research_prfaq.models import setup_logging
from synth_lab.research_prfaq.generator import generate_prfaq_markdown, save_prfaq_markdown, load_prfaq_markdown

app = typer.Typer()
console = Console()


@app.command()
def generate(
    batch_id: str = typer.Argument(..., help="Research batch ID"),
    output_dir: str = typer.Option("output/reports", "--output-dir", "-o", help="Output directory for PR-FAQ"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed logging"),
):
    """Generate PR-FAQ Markdown from research batch report.

    Reads batch summary from output/reports/{batch_id}.md
    and generates a PR-FAQ document in Markdown format following Amazon's Working Backwards framework.

    Example:
        synthlab research-prfaq generate batch_compra-amazon_20251218_164204
    """
    # Setup logging
    if verbose:
        setup_logging()

    try:
        console.print(f"[cyan]Loading research batch:[/cyan] {batch_id}")

        # Generate PR-FAQ Markdown
        console.print("[cyan]Generating PR-FAQ Markdown with OpenAI API...[/cyan]")
        prfaq_markdown = generate_prfaq_markdown(batch_id, data_dir=output_dir)

        console.print(f"[green]✓[/green] Generated PR-FAQ ({len(prfaq_markdown)} characters)")

        # Save to Markdown file
        output_path = save_prfaq_markdown(prfaq_markdown, batch_id, output_dir=output_dir)

        console.print(f"[green]✓[/green] Saved PR-FAQ to: {output_path}")

        # Display preview of PR-FAQ (first 800 chars)
        console.print("\n[bold]PR-FAQ Preview:[/bold]")
        preview_text = prfaq_markdown[:800] + "..." if len(prfaq_markdown) > 800 else prfaq_markdown
        console.print(Panel(
            Markdown(preview_text),
            border_style="green",
            title="Generated PR-FAQ (Preview)"
        ))

        # Count sections
        sections_count = {
            "Press Release": "✓" if "Press Release" in prfaq_markdown else "✗",
            "External FAQs": "✓" if "External FAQs" in prfaq_markdown else "✗",
            "Internal FAQs": "✓" if "Internal FAQs" in prfaq_markdown else "✗"
        }

        table = Table(title="PR-FAQ Structure")
        table.add_column("Section", style="cyan")
        table.add_column("Status", style="green")

        for section, status in sections_count.items():
            table.add_row(section, status)

        console.print(table)

        console.print(f"\n[green]✓ PR-FAQ generation complete![/green]")
        console.print(f"[cyan]View full document:[/cyan] {output_path}")

    except FileNotFoundError as e:
        console.print(f"[red]✗ Error:[/red] {str(e)}")
        console.print(f"[yellow]Tip:[/yellow] Ensure batch report exists at {output_dir}/{batch_id}.md")
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
    format: str = typer.Option("pdf", "--format", "-f", help="Export format: pdf, html (MD already exists)"),
    output_dir: str = typer.Option("output/reports", "--output-dir", "-o", help="Base output directory"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed logging"),
):
    """Export PR-FAQ to PDF or HTML format.

    Exports an existing PR-FAQ Markdown document to PDF or HTML for different use cases:
    - pdf: Professional presentations and email distribution
    - html: Internal documentation and interactive consumption

    Note: The Markdown version is already saved as {batch_id}_prfaq.md

    Example:
        synthlab research-prfaq export batch_compra-amazon_20251218_164204 --format pdf
        synthlab research-prfaq export batch_compra-amazon_20251218_164204 --format html
    """
    # Setup logging
    if verbose:
        setup_logging()

    # Normalize format aliases
    format_map = {
        "pdf": "pdf",
        "html": "html",
        "htm": "html"
    }

    if format.lower() not in format_map:
        console.print(f"[red]✗ Invalid format:[/red] {format}")
        console.print(f"[yellow]Valid formats:[/yellow] pdf, html")
        console.print(f"[yellow]Note:[/yellow] Markdown is already available as {batch_id}_prfaq.md")
        raise typer.Exit(code=1)

    export_format = format_map[format.lower()]

    try:
        # Load PR-FAQ Markdown
        console.print(f"[cyan]Loading PR-FAQ Markdown:[/cyan] {batch_id}")
        prfaq_markdown = load_prfaq_markdown(batch_id, output_dir=output_dir)

        console.print(f"[green]✓[/green] Loaded PR-FAQ Markdown ({len(prfaq_markdown)} characters)")

        # Create exports directory
        from pathlib import Path
        exports_dir = Path(output_dir) / f"{batch_id}_exports"
        exports_dir.mkdir(parents=True, exist_ok=True)

        # Export based on format
        console.print(f"[cyan]Exporting to {export_format.upper()} format...[/cyan]")

        if export_format == "pdf":
            # PDF export will need to parse MD or we keep current implementation
            # For now, show message that PDF export needs implementation
            console.print(f"[yellow]Note:[/yellow] PDF export from Markdown not yet implemented")
            console.print(f"[yellow]Current workaround:[/yellow] Use pandoc or similar tool to convert {batch_id}_prfaq.md to PDF")
            raise typer.Exit(code=1)
        elif export_format == "html":
            # HTML export will need to parse MD or we keep current implementation
            console.print(f"[yellow]Note:[/yellow] HTML export from Markdown not yet implemented")
            console.print(f"[yellow]Current workaround:[/yellow] Use markdown processor to convert {batch_id}_prfaq.md to HTML")
            raise typer.Exit(code=1)

    except FileNotFoundError as e:
        console.print(f"[red]✗ Error:[/red] {str(e)}")
        console.print(f"[yellow]Tip:[/yellow] Ensure PR-FAQ Markdown exists at {output_dir}/{batch_id}_prfaq.md")
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
