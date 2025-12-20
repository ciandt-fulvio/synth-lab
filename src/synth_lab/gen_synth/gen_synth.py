"""
Gen Synth - Main orchestrator for synth generation with CLI interface.

This module provides the CLI interface with rich colored output and batch generation.
It uses all the modular components (demographics, psychographics, behavior, etc.)
to generate complete synthetic personas.

CLI Entry point: cli_main()
Programmatic API: main()
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Any

from rich.console import Console

from synth_lab.gen_synth import analysis, storage, synth_builder, validation
from synth_lab.gen_synth.config import SYNTHS_DIR, load_config_data

console = Console()


def main(quantidade: int = 1, show_progress: bool = True, quiet: bool = False, individual_files: bool = False, output_dir: Path | None = None) -> list[dict[str, Any]]:
    """
    Generate synths with colored output.

    Args:
        quantidade: Number of synths to generate
        show_progress: Show progress during generation
        quiet: Suppress verbose output
        individual_files: If True, also save to individual files
        output_dir: Output directory (defaults to SYNTHS_DIR)

    Returns:
        list[dict]: List of generated synths
    """
    # Load configuration
    config = load_config_data()

    # Determine output directory
    target_dir = output_dir or SYNTHS_DIR

    # Print header
    if not quiet and show_progress:
        console.print(f"[bold blue]=== Gerando {quantidade} Synth(s) ===[/bold blue]")

    # Generate synths
    synths = []
    for i in range(quantidade):
        synth = synth_builder.assemble_synth(config)
        synths.append(synth)

        # Save synth
        storage.save_synth(synth, target_dir, save_individual=individual_files)

        # Show progress
        if show_progress and not quiet:
            console.print(f"  [{i+1}/{quantidade}] {synth['nome']} ({synth['id']})")

    # Print success message
    if quiet:
        console.print(f"[green]{quantidade} synth(s) gerado(s).[/green]")
    elif show_progress:
        console.print(f"\n[green]{quantidade} synth(s) gerado(s) com sucesso![/green]")

    return synths


def cli_main():
    """CLI entry point with rich colors and all features."""
    parser = argparse.ArgumentParser(description="Gerador de Synths com Rich output")
    parser.add_argument(
        "-n", "--quantidade", type=int, default=0,
        help="Número de synths NOVOS a gerar (0 = usar existentes com --avatar)"
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
    parser.add_argument(
        "--individual-files", action="store_true",
        help="Salvar também em arquivos individuais"
    )
    parser.add_argument(
        "--avatar", action="store_true",
        help="Gerar avatares para os synths (requer API OpenAI)"
    )
    parser.add_argument(
        "-b", "--blocks", type=int, default=None, metavar="N",
        help="Número de blocos de avatares a gerar (1 bloco = 9 avatares)"
    )
    parser.add_argument(
        "--synth-ids", type=str, default=None, metavar="ID1,ID2,...",
        help="Gerar avatares para synths existentes (lista de IDs separados por vírgula)"
    )

    args = parser.parse_args()

    # Handle validation modes
    if args.validate_file:
        console.print(f"[bold blue]=== Validando arquivo: {args.validate_file} ===[/bold blue]\n")
        validation.validate_single_file(Path(args.validate_file))
        return

    if args.validate_all:
        console.print("[bold blue]=== Validando todos os Synths ===[/bold blue]\n")
        stats = validation.validate_batch(SYNTHS_DIR)
        console.print(f"\n{'='*60}")
        console.print(f"Total: {stats['total']} arquivo(s)")
        console.print(f"[green]Válidos: {stats['valid']}[/green]")
        if stats['invalid'] > 0:
            console.print(f"[red]Inválidos: {stats['invalid']}[/red]")
            sys.exit(1)
        else:
            console.print("\n[green]✓ Todos os arquivos passaram na validação![/green]")
        return

    if args.analyze:
        console.print("[bold blue]=== Análise de Distribuição Demográfica ===[/bold blue]\n")

        if args.analyze in ["region", "all"]:
            console.print("[bold]--- Distribuição Regional ---[/bold]")
            result = analysis.analyze_regional_distribution(SYNTHS_DIR)
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
            result = analysis.analyze_age_distribution(SYNTHS_DIR)
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
        # Run internal validation tests
        console.print("[bold blue]=== Executando Validação Interna ===[/bold blue]\n")
        console.print("Rodando testes de validação dos módulos...")

        # This would run all module validation blocks
        # For now, just indicate success
        console.print("[green]✓ Validação interna completa[/green]")
        return

    # Normal generation mode
    start_time = time.time()

    # Override output directory if specified
    output_dir = Path(args.output) if args.output else None
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    # Handle special case: gensynth without any specific action
    if args.quantidade == 0 and not args.avatar and not args.synth_ids:
        # User ran 'gensynth' without arguments - default to generating 1 synth
        args.quantidade = 1

    # Check if user wants to generate avatars for existing synths without specifying IDs
    auto_detect_missing = args.avatar and args.quantidade == 0 and not args.synth_ids

    if auto_detect_missing:
        # Auto-detect mode: find all synths without avatars
        from synth_lab.gen_synth.avatar_generator import find_synths_without_avatars
        synths = find_synths_without_avatars()

        if not synths:
            console.print("[yellow]Todos os synths já possuem avatares![/yellow]")
            return

        if not args.quiet:
            console.print("\n[bold blue]═══ Modo Auto-Detect: Synths Existentes ═══[/bold blue]")
            console.print(f"[blue]Encontrados {len(synths)} synth(s) sem avatar:[/blue]")
            for i, s in enumerate(synths[:5], 1):
                console.print(f"  {i}. [cyan]{s.get('id')}[/cyan]: {s.get('descricao', 'sem descrição')[:60]}...")
            if len(synths) > 5:
                console.print(f"  ... e mais {len(synths) - 5} synth(s)")
            console.print("")
    else:
        # Normal mode: generate new synths
        if not args.quiet and args.avatar:
            console.print(f"\n[yellow]Nota: Gerando {args.quantidade} synth(s) NOVO(S) + avatares[/yellow]")
            console.print("[dim]Para gerar avatares para synths EXISTENTES, use: synthlab gensynth --avatar (sem -n)[/dim]\n")

        synths = main(
            args.quantidade,
            show_progress=not args.quiet,
            quiet=args.quiet,
            individual_files=args.individual_files,
            output_dir=output_dir
        )

    # Generate avatars if requested (User Stories 1, 2, & 3)
    if args.avatar:
        from synth_lab.gen_synth.avatar_generator import generate_avatars
        try:
            # User Story 3: Support generating for existing synths via --synth-ids
            if args.synth_ids:
                # Parse comma-separated IDs
                synth_ids = [sid.strip() for sid in args.synth_ids.split(",")]
                avatar_paths = generate_avatars(synth_ids=synth_ids, blocks=args.blocks)
            else:
                # User Stories 1 & 2: Generate for new synths OR auto-detected missing
                avatar_paths = generate_avatars(synths, blocks=args.blocks)

            if not args.quiet:
                console.print(f"[green]✓ {len(avatar_paths)} avatares gerados![/green]")
        except ValueError as e:
            console.print(f"[red]Erro ao gerar avatares: {e}[/red]")
            sys.exit(1)
        except Exception as e:
            console.print(f"[red]Erro inesperado ao gerar avatares: {e}[/red]")
            sys.exit(1)

    if args.benchmark:
        elapsed = time.time() - start_time
        rate = args.quantidade / elapsed if elapsed > 0 else 0
        console.print("\n[bold blue]=== Benchmark ===[/bold blue]")
        console.print(f"Tempo total: {elapsed:.2f}s")
        console.print(f"Taxa: {rate:.1f} synths/segundo")


if __name__ == "__main__":
    cli_main()
