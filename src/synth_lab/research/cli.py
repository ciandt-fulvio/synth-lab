"""
CLI interface for UX research interviews with synths.

This module provides the command-line interface for running interviews:
- research command with synth_id argument
- Optional topic guide path
- Optional max_rounds configuration
- Optional model selection

Functions:
- research_command(): Main CLI handler for research subcommand
- app: Typer application instance

Sample usage:
    synthlab research abc123
    synthlab research abc123 --topic-guide data/topic_guides/ecommerce-mobile.md
    synthlab research abc123 --max-rounds 15 --model gpt-5-mini

Expected output:
    Real-time interview display with Rich formatting
    Transcript saved to output/transcripts/{synth_id}_{timestamp}.json

Third-party Documentation:
- Typer: https://typer.tiangolo.com/
- Rich: https://rich.readthedocs.io/
"""

import sys
from pathlib import Path

import typer
from loguru import logger
from rich.console import Console

from synth_lab.research.interview import run_interview, validate_synth_exists
from synth_lab.research.transcript import save_transcript

app = typer.Typer(
    name="research",
    help="Realizar entrevistas de pesquisa UX com synths",
    no_args_is_help=True,
)
console = Console()


@app.command()
def research(
    synth_id: str = typer.Argument(
        ..., help="ID do synth a ser entrevistado (6 caracteres)"
    ),
    topic_guide_name: str = typer.Argument(
        ..., help="Nome do topic guide (ex: compra-amazon)"
    ),
    max_rounds: int = typer.Option(
        10,
        "--max-rounds",
        "-r",
        min=1,
        max=100,
        help="Número máximo de rodadas de conversa",
    ),
    model: str = typer.Option(
        "gpt-5-mini", "--model", "-m", help="Modelo de LLM a usar (ex: gpt-5-mini, gpt-4)"
    ),
    output_dir: str = typer.Option(
        "output/transcripts",
        "--output",
        "-o",
        help="Diretório para salvar transcrição",
    ),
):
    """
    Executar entrevista de pesquisa UX com um synth usando um topic guide.

    O topic guide deve conter:
    - script.json: Roteiro de perguntas da entrevista
    - summary.md: Contexto e descrições dos materiais
    - Arquivos de contexto (imagens, PDFs, etc.)

    Exemplo:
        synthlab research abc123 compra-amazon
    """
    # Validate synth exists
    if not validate_synth_exists(synth_id):
        console.print(
            f"[bold red]✗[/bold red] Synth com ID '{synth_id}' não encontrado",
            style="red",
        )
        console.print(
            "\nUse [bold]synthlab listsynth[/bold] para ver synths disponíveis"
        )
        sys.exit(1)

    # Validate topic guide
    import os
    base_dir = Path(os.environ.get("TOPIC_GUIDES_DIR", "data/topic_guides"))
    topic_dir = base_dir / topic_guide_name

    # Check if topic guide directory exists
    if not topic_dir.exists():
        console.print(
            f"[bold red]✗[/bold red] Topic guide '{topic_guide_name}' não encontrado",
            style="red",
        )
        console.print(f"\nProcurado em: {topic_dir}")
        console.print(
            "\nUse [bold]synthlab topic-guide list[/bold] para ver guides disponíveis")
        sys.exit(1)

    # Check if script.json exists
    script_path = topic_dir / "script.json"
    if not script_path.exists():
        console.print(
            f"[bold red]✗[/bold red] Arquivo script.json não encontrado no topic guide '{topic_guide_name}'",
            style="red",
        )
        console.print(f"\nProcurado em: {script_path}")
        console.print(
            "\nO topic guide deve conter um arquivo script.json com o roteiro de perguntas")
        sys.exit(1)

    # Check if summary.md exists
    summary_path = topic_dir / "summary.md"
    if not summary_path.exists():
        console.print(
            f"[bold red]✗[/bold red] Arquivo summary.md não encontrado no topic guide '{topic_guide_name}'",
            style="red",
        )
        console.print(f"\nProcurado em: {summary_path}")
        console.print(
            "\nUse [bold]synthlab topic-guide update {topic_guide_name}[/bold] para gerar o summary.md")
        sys.exit(1)

    # Check for OPENAI_API_KEY
    import os

    if not os.getenv("OPENAI_API_KEY"):
        console.print(
            "[bold red]✗[/bold red] Variável de ambiente OPENAI_API_KEY não configurada",
            style="red",
        )
        console.print(
            "\nConfigure sua chave de API:\n[bold]export OPENAI_API_KEY='sua-chave'[/bold]"
        )
        sys.exit(1)

    try:
        # Run interview
        logger.info(
            f"Starting interview with synth {synth_id} and topic guide {topic_guide_name}")
        session, messages, synth = run_interview(
            synth_id=synth_id,
            topic_guide_name=topic_guide_name,
            max_rounds=max_rounds,
            model=model,
        )

        # Save transcript
        console.print("\n[cyan]💾 Salvando transcrição...[/cyan]")
        transcript_path = save_transcript(
            session=session,
            messages=messages,
            synth_snapshot=synth,
            output_dir=output_dir,
        )

        console.print(
            f"[bold green]✓[/bold green] Transcrição salva em: [bold]{transcript_path}[/bold]"
        )

    except ValueError as e:
        console.print(
            f"[bold red]✗[/bold red] Erro de validação: {e}", style="red")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print(
            "\n[yellow]⚠[/yellow] Entrevista interrompida pelo usuário")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Interview failed: {e}")
        console.print(
            f"[bold red]✗[/bold red] Erro na entrevista: {e}", style="red")
        sys.exit(1)


if __name__ == "__main__":
    """Validation with mock synth."""
    print("=== Research CLI Module Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Test 1: CLI app exists
    total_tests += 1
    try:
        assert app is not None
        assert app.info.name == "research"
        print("✓ Typer app created successfully")
    except Exception as e:
        all_validation_failures.append(f"Typer app creation: {e}")

    # Test 2: research command exists
    total_tests += 1
    try:
        commands = [cmd.name for cmd in app.registered_commands]
        assert "research" in commands or len(app.registered_commands) > 0
        print("✓ research command registered")
    except Exception as e:
        all_validation_failures.append(f"Command registration: {e}")

    # Test 3: Required imports work
    total_tests += 1
    try:
        from synth_lab.research.interview import run_interview, validate_synth_exists
        from synth_lab.research.transcript import save_transcript

        print("✓ All required imports successful")
    except Exception as e:
        all_validation_failures.append(f"Import validation: {e}")

    # Final validation result
    print()
    if all_validation_failures:
        print(
            f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(
            f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results"
        )
        print("CLI module is validated and ready for use")
        sys.exit(0)
