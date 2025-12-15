"""
SynthLab CLI - Main entry point.

Command-line interface for generating synthetic Brazilian personas.
"""

import argparse
import sys
from synth_lab import __version__


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="synthlab",
        description="Synth Lab - Gerador de Personas Sintéticas Brasileiras",
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

    # listsynth subcommand
    listsynth_parser = subparsers.add_parser(
        "listsynth", help="Consultar dados sintéticos"
    )
    listsynth_parser.add_argument(
        "--where",
        type=str,
        help="Condição SQL WHERE (sem a palavra WHERE)",
    )
    listsynth_parser.add_argument(
        "--full-query",
        type=str,
        help="Consulta SQL SELECT completa",
    )

    # gensynth subcommand
    gensynth_parser = subparsers.add_parser(
        "gensynth", help="Gerar personas sintéticas"
    )
    gensynth_parser.add_argument(
        "-n",
        "--quantidade",
        type=int,
        default=1,
        help="Número de synths a gerar (padrão: 1)",
    )
    gensynth_parser.add_argument(
        "-o",
        "--output",
        type=str,
        metavar="DIR",
        help="Diretório de saída para synths gerados (padrão: data/synths/)",
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
        help="Validar todos os Synths em data/synths/",
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

    return parser


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # If no command specified, show help
    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Handle listsynth command
    if args.command == "listsynth":
        from synth_lab.query.cli import listsynth

        # Call listsynth with parsed arguments
        sys.argv = ["synthlab listsynth"]
        if args.where:
            sys.argv.extend(["--where", args.where])
        if args.full_query:
            sys.argv.extend(["--full-query", args.full_query])

        # Import and run Typer app
        from synth_lab.query.cli import app as query_app
        query_app()
        return

    # Handle gensynth command
    if args.command == "gensynth":
        # Import here to avoid circular imports and speed up --help
        from synth_lab.gen_synth.gen_synth import cli_main as gensynth_cli_main

        # Convert args to match original gen_synth.py interface
        sys.argv = ["synthlab gensynth"]
        if args.quantidade:
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

        gensynth_cli_main()


if __name__ == "__main__":
    main()
