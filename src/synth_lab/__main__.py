"""
SynthLab CLI - Main entry point.

Command-line interface for generating synthetic Brazilian personas.
"""

import argparse
import sys

from synth_lab import __version__
from synth_lab.infrastructure.config import configure_logging
from synth_lab.infrastructure.phoenix_tracing import maybe_setup_tracing, shutdown_tracing


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="synthlab",
        description="SynthLab - Gerador de Personas Sintéticas Brasileiras",
        epilog="Use 'synthlab <comando> --help' para mais informações sobre um comando específico.",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(
        dest="command", help="Comandos disponíveis", required=False
    )

    # gensynth subcommand
    gensynth_parser = subparsers.add_parser(
        "gensynth", help="Gerar personas sintéticas"
    )
    gensynth_parser.add_argument(
        "-n",
        "--quantidade",
        type=int,
        default=0,
        help="Número de synths NOVOS a gerar (0 = usar existentes com --avatar)",
    )
    gensynth_parser.add_argument(
        "-o",
        "--output",
        type=str,
        metavar="DIR",
        help="Diretório de saída para synths gerados (padrão: output/synths/)",
    )
    gensynth_parser.add_argument(
        "-q", "--quiet", action="store_true", help="Modo silencioso - suprimir output verboso"
    )
    gensynth_parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Mostrar estatísticas de performance (tempo total, synths/segundo)",
    )
    gensynth_parser.add_argument(
        "--validate-file", type=str, metavar="FILE", help="Validar um único arquivo JSON de Synth"
    )
    gensynth_parser.add_argument(
        "--validate-all",
        action="store_true",
        help="Validar todos os Synths em output/synths/",
    )
    gensynth_parser.add_argument(
        "--validar", action="store_true", help="Executar testes de validação internos"
    )
    gensynth_parser.add_argument(
        "--analyze",
        type=str,
        choices=["region", "age", "all"],
        help="Analisar distribuição demográfica (region|age|all)",
    )
    gensynth_parser.add_argument(
        "--individual-files",
        action="store_true",
        help="Salvar também em arquivos individuais (além do arquivo consolidado)",
    )
    gensynth_parser.add_argument(
        "--avatar",
        action="store_true",
        help="Gerar avatares para os synths (requer API OpenAI)",
    )
    gensynth_parser.add_argument(
        "-b",
        "--blocks",
        type=int,
        default=None,
        metavar="N",
        help="Número de blocos de avatares a gerar (1 bloco = 9 avatares)",
    )
    gensynth_parser.add_argument(
        "--synth-ids",
        type=str,
        default=None,
        metavar="ID1,ID2,...",
        help="Gerar avatares para synths existentes (lista de IDs separados por vírgula)",
    )

    return parser


def main():
    """Main CLI entry point."""
    configure_logging()
    # Setup Phoenix tracing if PHOENIX_ENABLED=true
    maybe_setup_tracing()

    parser = create_parser()

    # Parse arguments
    args = parser.parse_args()

    # If no command specified, show help
    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Handle gensynth command
    if args.command == "gensynth":
        # Import here to avoid circular imports and speed up --help
        from synth_lab.gen_synth.gen_synth import cli_main as gensynth_cli_main

        # Convert args to match original gen_synth.py interface
        sys.argv = ["synthlab gensynth"]
        # Always pass -n, even if 0 (to support auto-detect mode)
        sys.argv.extend(["-n", str(args.quantidade)])
        if args.output:
            sys.argv.extend(["-o", args.output])
        if args.quiet:
            sys.argv.append("-q")
        if args.benchmark:
            sys.argv.append("--benchmark")
        if args.validate_file:
            sys.argv.extend(["--validate-file", args.validate_file])
        if args.validate_all:
            sys.argv.append("--validate-all")
        if args.validar:
            sys.argv.append("--validar")
        if args.analyze:
            sys.argv.extend(["--analyze", args.analyze])
        if args.individual_files:
            sys.argv.append("--individual-files")
        if args.avatar:
            sys.argv.append("--avatar")
        if args.blocks:
            sys.argv.extend(["-b", str(args.blocks)])
        if args.synth_ids:
            sys.argv.extend(["--synth-ids", args.synth_ids])

        try:
            gensynth_cli_main()
        finally:
            shutdown_tracing()


if __name__ == "__main__":
    main()
