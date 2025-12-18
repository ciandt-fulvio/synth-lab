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
        default=0,
        help="Número de synths NOVOS a gerar (0 = usar existentes com --avatar)",
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

    # research subcommand (agentic multi-agent system)
    research_parser = subparsers.add_parser(
        "research", help="Realizar entrevistas de pesquisa UX com synths (sistema multi-agente)"
    )
    research_parser.add_argument(
        "synth_id",
        type=str,
        help="ID do synth a ser entrevistado (6 caracteres)",
    )
    research_parser.add_argument(
        "topic_guide_name",
        type=str,
        help="Nome do topic guide (ex: compra-amazon)",
    )
    research_parser.add_argument(
        "-t",
        "--max-turns",
        type=int,
        default=6,
        help="Número máximo de turnos de conversa (padrão: 6)",
    )
    research_parser.add_argument(
        "-m",
        "--model",
        type=str,
        default="gpt-5-mini",
        help="Modelo de LLM a usar (padrão: gpt-5-mini)",
    )
    research_parser.add_argument(
        "--trace-path",
        type=str,
        default=None,
        help="Caminho para salvar trace (auto-gera se não especificado)",
    )
    research_parser.add_argument(
        "-o",
        "--transcript-path",
        type=str,
        default=None,
        help="Caminho para salvar transcrição JSON (auto-gera se não especificado)",
    )
    research_parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suprimir output da conversa",
    )

    # topic-guide subcommand
    # topic-guide has its own Typer sub-app with multiple commands (create, update, list, show)
    # We use parse_known_args to pass remaining args to Typer
    subparsers.add_parser(
        "topic-guide", help="Manage topic guides with multi-modal context materials",
        add_help=False  # Let Typer handle --help
    )

    return parser


def main():
    """Main CLI entry point."""
    parser = create_parser()

    # Use parse_known_args to handle topic-guide's sub-commands
    args, unknown_args = parser.parse_known_args()

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

        gensynth_cli_main()

    # Handle research command (agentic multi-agent system)
    if args.command == "research":
        # Import here to avoid circular imports and speed up --help
        from synth_lab.research_agentic.cli import app as research_app

        # Convert args to match Typer interface
        sys.argv = ["synthlab research", args.synth_id, args.topic_guide_name]
        if args.max_turns:
            sys.argv.extend(["--max-turns", str(args.max_turns)])
        if args.model:
            sys.argv.extend(["--model", args.model])
        if args.trace_path:
            sys.argv.extend(["--trace-path", args.trace_path])
        if args.transcript_path:
            sys.argv.extend(["--transcript-path", args.transcript_path])
        if args.quiet:
            sys.argv.append("--quiet")

        research_app()

    # Handle topic-guide command
    if args.command == "topic-guide":
        # Import here to avoid circular imports and speed up --help
        from synth_lab.topic_guides.cli import app as topic_guide_app

        # Typer will handle all subcommands (create, update, list, show)
        # Reset sys.argv to pass remaining args to Typer
        sys.argv = ["synthlab topic-guide"] + unknown_args
        topic_guide_app()


if __name__ == "__main__":
    main()
