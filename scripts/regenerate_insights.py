#!/usr/bin/env python3
"""
Script para regenerar insights de análises quantitativas.

Permite deletar e regenerar insights individuais ou todos de uma vez.
Útil para testar melhorias nos prompts ou corrigir insights com problemas.

Usage:
    # Listar insights de um experimento
    uv run python scripts/regenerate_insights.py list exp_12345678

    # Regenerar um insight específico
    uv run python scripts/regenerate_insights.py regenerate exp_12345678 try_vs_success

    # Regenerar todos os insights
    uv run python scripts/regenerate_insights.py regenerate-all exp_12345678

    # Deletar um insight (sem regenerar)
    uv run python scripts/regenerate_insights.py delete exp_12345678 try_vs_success

References:
    - Service: src/synth_lab/services/insight_service.py
    - Router: src/synth_lab/api/routers/insights.py
    - Cache: src/synth_lab/repositories/analysis_cache_repository.py
"""

import asyncio
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Load environment variables from .env BEFORE importing synth_lab modules
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

import typer
from loguru import logger
from rich.console import Console
from rich.table import Table

from synth_lab.domain.entities.analysis_cache import CacheKeys
from synth_lab.repositories.analysis_cache_repository import AnalysisCacheRepository
from synth_lab.repositories.analysis_outcome_repository import AnalysisOutcomeRepository
from synth_lab.repositories.analysis_repository import AnalysisRepository
from synth_lab.repositories.experiment_repository import ExperimentRepository
from synth_lab.services.insight_service import InsightService

app = typer.Typer(help="Regenerate AI insights for quantitative analysis")
console = Console()

# Supported chart types with insights
CHART_TYPES_WITH_INSIGHTS = [
    "try_vs_success",
    "shap_summary",
    "pca_scatter",
    "radar_comparison",
    "extreme_cases",
    "outliers",
]


@app.command()
def list(
    experiment_id: str = typer.Argument(..., help="Experiment ID (e.g., exp_12345678)")
):
    """List all insights for an experiment with their status."""
    try:
        # Get repositories
        exp_repo = ExperimentRepository()
        ana_repo = AnalysisRepository()
        cache_repo = AnalysisCacheRepository()

        # Validate experiment exists
        experiment = exp_repo.get_by_id(experiment_id)
        if experiment is None:
            console.print(f"[red]❌ Experiment {experiment_id} not found[/red]")
            raise typer.Exit(1)

        # Get analysis
        analysis = ana_repo.get_by_experiment_id(experiment_id)
        if analysis is None:
            console.print(
                f"[red]❌ No analysis found for experiment {experiment_id}[/red]"
            )
            console.print(
                "[yellow]Run analysis first: POST /experiments/{id}/analysis[/yellow]"
            )
            raise typer.Exit(1)

        # Get all insights
        insights = cache_repo.get_all_chart_insights(analysis.id)
        insight_map = {i.chart_type: i for i in insights}

        # Create table
        table = Table(title=f"Insights for {experiment.name} ({experiment_id})")
        table.add_column("Chart Type", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("Summary (first 80 chars)", style="white")
        table.add_column("Cache Key", style="dim")

        for chart_type in CHART_TYPES_WITH_INSIGHTS:
            insight = insight_map.get(chart_type)
            if insight:
                status_emoji = {
                    "completed": "✅",
                    "pending": "⏳",
                    "failed": "❌",
                }.get(insight.status, "❓")
                summary_preview = (
                    insight.summary[:80] + "..."
                    if len(insight.summary) > 80
                    else insight.summary
                )
                table.add_row(
                    chart_type,
                    f"{status_emoji} {insight.status}",
                    summary_preview,
                    f"insight_{chart_type}",
                )
            else:
                table.add_row(
                    chart_type,
                    "⚠️  missing",
                    "[dim]Not generated yet[/dim]",
                    f"insight_{chart_type}",
                )

        console.print(table)
        console.print(
            f"\n[green]Analysis ID:[/green] {analysis.id}",
        )
        console.print(
            f"[green]Total insights:[/green] {len(insights)} / {len(CHART_TYPES_WITH_INSIGHTS)}"
        )

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        logger.error(f"Failed to list insights: {e}")
        raise typer.Exit(1)


@app.command()
def delete(
    experiment_id: str = typer.Argument(..., help="Experiment ID"),
    chart_type: str = typer.Argument(
        ..., help="Chart type (e.g., try_vs_success, shap_summary)"
    ),
):
    """Delete a specific insight from cache."""
    if chart_type not in CHART_TYPES_WITH_INSIGHTS:
        console.print(
            f"[red]❌ Invalid chart type: {chart_type}[/red]",
        )
        console.print(
            f"[yellow]Valid types: {', '.join(CHART_TYPES_WITH_INSIGHTS)}[/yellow]"
        )
        raise typer.Exit(1)

    try:
        # Get repositories
        exp_repo = ExperimentRepository()
        ana_repo = AnalysisRepository()
        cache_repo = AnalysisCacheRepository()

        # Validate experiment exists
        experiment = exp_repo.get_by_id(experiment_id)
        if experiment is None:
            console.print(f"[red]❌ Experiment {experiment_id} not found[/red]")
            raise typer.Exit(1)

        # Get analysis
        analysis = ana_repo.get_by_experiment_id(experiment_id)
        if analysis is None:
            console.print(
                f"[red]❌ No analysis found for experiment {experiment_id}[/red]"
            )
            raise typer.Exit(1)

        # Delete insight
        cache_key = f"insight_{chart_type}"
        deleted = cache_repo.delete(analysis.id, cache_key)

        if deleted:
            console.print(
                f"[green]✅ Deleted insight for {chart_type}[/green]",
            )
        else:
            console.print(
                f"[yellow]⚠️  Insight for {chart_type} not found in cache[/yellow]"
            )

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        logger.error(f"Failed to delete insight: {e}")
        raise typer.Exit(1)


@app.command()
def regenerate(
    experiment_id: str = typer.Argument(..., help="Experiment ID"),
    chart_type: str = typer.Argument(..., help="Chart type to regenerate"),
):
    """Regenerate a specific insight."""
    if chart_type not in CHART_TYPES_WITH_INSIGHTS:
        console.print(f"[red]❌ Invalid chart type: {chart_type}[/red]")
        console.print(
            f"[yellow]Valid types: {', '.join(CHART_TYPES_WITH_INSIGHTS)}[/yellow]"
        )
        raise typer.Exit(1)

    try:
        # Get repositories
        exp_repo = ExperimentRepository()
        ana_repo = AnalysisRepository()
        cache_repo = AnalysisCacheRepository()
        insight_service = InsightService()

        # Validate experiment exists
        experiment = exp_repo.get_by_id(experiment_id)
        if experiment is None:
            console.print(f"[red]❌ Experiment {experiment_id} not found[/red]")
            raise typer.Exit(1)

        # Get analysis
        analysis = ana_repo.get_by_experiment_id(experiment_id)
        if analysis is None:
            console.print(
                f"[red]❌ No analysis found for experiment {experiment_id}[/red]"
            )
            raise typer.Exit(1)

        # Get chart data from cache
        chart_cache_key = _get_chart_cache_key(chart_type)
        chart_cache = cache_repo.get(analysis.id, chart_cache_key)
        if chart_cache is None:
            console.print(
                f"[red]❌ Chart data not found in cache for {chart_type}[/red]",
            )
            console.print(
                "[yellow]Run analysis first to pre-compute chart cache[/yellow]"
            )
            raise typer.Exit(1)

        console.print(
            f"[cyan]🔄 Regenerating insight for {chart_type}...[/cyan]",
        )

        # Delete old insight if exists
        old_insight_key = f"insight_{chart_type}"
        cache_repo.delete(analysis.id, old_insight_key)

        # Generate new insight
        insight = insight_service.generate_insight(
            analysis.id, chart_type, chart_cache.data
        )

        if insight.status == "completed":
            console.print(f"[green]✅ Insight regenerated successfully![/green]")
            console.print(f"\n[bold]Summary:[/bold]")
            console.print(f"{insight.summary}\n")
        else:
            console.print(
                f"[red]❌ Failed to regenerate insight: {insight.summary}[/red]"
            )
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        logger.error(f"Failed to regenerate insight: {e}")
        raise typer.Exit(1)


@app.command()
def regenerate_all(
    experiment_id: str = typer.Argument(..., help="Experiment ID"),
):
    """Regenerate all insights for an experiment in parallel."""
    try:
        # Get repositories
        exp_repo = ExperimentRepository()
        ana_repo = AnalysisRepository()
        cache_repo = AnalysisCacheRepository()

        # Validate experiment exists
        experiment = exp_repo.get_by_id(experiment_id)
        if experiment is None:
            console.print(f"[red]❌ Experiment {experiment_id} not found[/red]")
            raise typer.Exit(1)

        # Get analysis
        analysis = ana_repo.get_by_experiment_id(experiment_id)
        if analysis is None:
            console.print(
                f"[red]❌ No analysis found for experiment {experiment_id}[/red]"
            )
            raise typer.Exit(1)

        console.print(
            f"[cyan]🔄 Regenerating all {len(CHART_TYPES_WITH_INSIGHTS)} insights...[/cyan]\n"
        )

        # Run parallel regeneration
        asyncio.run(_regenerate_all_parallel(analysis.id, cache_repo))

        console.print(f"\n[green]✅ All insights regenerated![/green]")

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        logger.error(f"Failed to regenerate all insights: {e}")
        raise typer.Exit(1)


async def _regenerate_all_parallel(
    analysis_id: str, cache_repo: AnalysisCacheRepository
) -> None:
    """Regenerate all insights in parallel."""
    insight_service = InsightService()

    async def regenerate_single(chart_type: str) -> None:
        try:
            # Get chart data
            chart_cache_key = _get_chart_cache_key(chart_type)
            chart_cache = cache_repo.get(analysis_id, chart_cache_key)
            if chart_cache is None:
                console.print(
                    f"[yellow]⚠️  Skipping {chart_type} - no chart data in cache[/yellow]"
                )
                return

            # Delete old insight
            old_insight_key = f"insight_{chart_type}"
            cache_repo.delete(analysis_id, old_insight_key)

            # Generate new insight
            console.print(f"[cyan]  → Generating {chart_type}...[/cyan]")
            insight = insight_service.generate_insight(
                analysis_id, chart_type, chart_cache.data
            )

            if insight.status == "completed":
                console.print(f"[green]  ✅ {chart_type} completed[/green]")
            else:
                console.print(f"[red]  ❌ {chart_type} failed[/red]")

        except Exception as e:
            console.print(f"[red]  ❌ {chart_type} error: {e}[/red]")

    # Create tasks for all chart types
    tasks = [regenerate_single(ct) for ct in CHART_TYPES_WITH_INSIGHTS]
    await asyncio.gather(*tasks, return_exceptions=True)


def _get_chart_cache_key(chart_type: str) -> str:
    """Get cache key for chart data based on chart type."""
    chart_key_map = {
        "try_vs_success": CacheKeys.TRY_VS_SUCCESS,
        "shap_summary": CacheKeys.SHAP_SUMMARY,
        "pca_scatter": CacheKeys.PCA_SCATTER,
        "radar_comparison": CacheKeys.RADAR_COMPARISON,
        "extreme_cases": CacheKeys.EXTREME_CASES,
        "outliers": CacheKeys.OUTLIERS,
    }
    return chart_key_map.get(chart_type, chart_type)


if __name__ == "__main__":
    # Configure logger
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>",
        level="INFO",
    )

    app()
