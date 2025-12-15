"""
Gen Synth - Main orchestrator for synth generation.

This module provides the CLI interface with rich colored output.
"""

import sys
import time
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# Import from original implementation temporarily
# We'll refactor this into separate modules later
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))
import gen_synth as original_gen_synth

console = Console()


def main(quantidade: int = 1, show_progress: bool = True, quiet: bool = False) -> list[dict[str, Any]]:
    """
    Generate synths with colored output.

    Args:
        quantidade: Number of synths to generate
        show_progress: Show progress during generation
        quiet: Suppress verbose output

    Returns:
        list[dict]: List of generated synths
    """
    # Print header before suppressing stdout
    if not quiet and show_progress:
        console.print(f"[bold blue]=== Gerando {quantidade} Synth(s) ===[/bold blue]")

    # Suppress original output and use rich colors instead
    import os
    devnull = open(os.devnull, 'w')
    old_stdout = sys.stdout
    sys.stdout = devnull

    synths = original_gen_synth.main(quantidade, show_progress=show_progress)

    sys.stdout = old_stdout
    devnull.close()

    # Print success message
    if quiet:
        console.print(f"[green]{quantidade} synth(s) gerado(s).[/green]")
    elif show_progress:
        console.print(f"\n[green]{quantidade} synth(s) gerado(s) com sucesso![/green]")

    return synths


def cli_main():
    """CLI entry point that wraps original gen_synth with rich colors."""
    import argparse

    parser = argparse.ArgumentParser(description="Gerador de Synths com Rich output")
    parser.add_argument(
        "-n", "--quantidade", type=int, default=1,
        help="Número de synths a gerar (padrão: 1)"
    )
    parser.add_argument(
        "-o", "--output", type=str, metavar="DIR",
        help="Diretório de saída"
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true",
        help="Modo silencioso"
    )
    parser.add_argument(
        "--benchmark", action="store_true",
        help="Mostrar estatísticas de performance"
    )
    parser.add_argument(
        "--validate-file", type=str,
        help="Validar arquivo único"
    )
    parser.add_argument(
        "--validate-all", action="store_true",
        help="Validar todos os synths"
    )
    parser.add_argument(
        "--validar", action="store_true",
        help="Executar validação interna"
    )
    parser.add_argument(
        "--analyze", type=str, choices=["region", "age", "all"],
        help="Analisar distribuição"
    )

    args = parser.parse_args()

    # Handle validation modes
    if args.validate_file:
        console.print(f"[bold blue]=== Validando arquivo: {args.validate_file} ===[/bold blue]\n")
        original_gen_synth.validate_single_file(Path(args.validate_file))
        return

    if args.validate_all:
        console.print(f"[bold blue]=== Validando todos os Synths ===[/bold blue]\n")
        stats = original_gen_synth.validate_batch()
        console.print(f"\n{'='*60}")
        console.print(f"Total: {stats['total']} arquivo(s)")
        console.print(f"[green]Válidos: {stats['valid']}[/green]")
        if stats['invalid'] > 0:
            console.print(f"[red]Inválidos: {stats['invalid']}[/red]")
            sys.exit(1)
        else:
            console.print(f"\n[green]✓ Todos os arquivos passaram na validação![/green]")
        return

    if args.analyze:
        console.print(f"[bold blue]=== Análise de Distribuição Demográfica ===[/bold blue]\n")

        if args.analyze in ["region", "all"]:
            console.print("[bold]--- Distribuição Regional ---[/bold]")
            result = original_gen_synth.analyze_regional_distribution()
            if "error" not in result:
                console.print(f"Total de Synths: {result['total']}\n")
                console.print(f"{'Região':<15} {'IBGE %':<10} {'Real %':<10} {'Count':<8} {'Erro %':<10}")
                console.print("-" * 60)
                for regiao, data in result["regions"].items():
                    console.print(
                        f"{regiao:<15} {data['ibge']:>7.2f}%  {data['actual']:>7.2f}%  "
                        f"{data['count']:>5}    {data['error']:>7.2f}%"
                    )
                console.print()

        if args.analyze in ["age", "all"]:
            console.print("[bold]--- Distribuição Etária ---[/bold]")
            result = original_gen_synth.analyze_age_distribution()
            if "error" not in result:
                console.print(f"Total de Synths: {result['total']}\n")
                console.print(f"{'Faixa':<10} {'IBGE %':<10} {'Real %':<10} {'Count':<8} {'Erro %':<10}")
                console.print("-" * 60)
                for faixa, data in result["age_groups"].items():
                    console.print(
                        f"{faixa:<10} {data['ibge']:>7.2f}%  {data['actual']:>7.2f}%  "
                        f"{data['count']:>5}    {data['error']:>7.2f}%"
                    )
        return

    if args.validar:
        # Run original internal validation
        original_gen_synth.sys.argv = ["gen_synth.py", "--validar"]
        original_gen_synth.cli_main()
        return

    # Normal generation mode
    start_time = time.time()

    if args.output:
        # Override output directory temporarily
        original_output = original_gen_synth.SYNTHS_DIR
        original_gen_synth.SYNTHS_DIR = Path(args.output)

    synths = main(args.quantidade, show_progress=not args.quiet, quiet=args.quiet)

    if args.output:
        original_gen_synth.SYNTHS_DIR = original_output

    if args.benchmark:
        elapsed = time.time() - start_time
        rate = args.quantidade / elapsed if elapsed > 0 else 0
        console.print(f"\n[bold blue]=== Benchmark ===[/bold blue]")
        console.print(f"Tempo total: {elapsed:.2f}s")
        console.print(f"Taxa: {rate:.1f} synths/segundo")


if __name__ == "__main__":
    cli_main()
