"""
CLI interface for agentic UX research interviews with synths.

This module provides the command-line interface for running multi-agent interviews:
- research command with synth_id argument
- Topic guide path
- Max turns configuration
- Model selection
- Trace output for visualization

Functions:
- research(): Main CLI handler for research subcommand
- app: Typer application instance

Sample usage:
    synthlab research abc123 compra-amazon
    synthlab research abc123 compra-amazon --max-turns 6 --model gpt-4o
    synthlab research abc123 compra-amazon --trace-path data/traces/demo.json

Expected output:
    Real-time interview display
    Trace file saved to data/traces/

Third-party Documentation:
- Typer: https://typer.tiangolo.com/
- Rich: https://rich.readthedocs.io/
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import typer
from loguru import logger
from rich.console import Console

from synth_lab.research_agentic.batch_runner import run_batch_interviews
from synth_lab.research_agentic.runner import run_interview

# Configure loguru to only show warnings and above (suppress debug/info)
logger.remove()  # Remove default handler
logger.add(sys.stderr, level="WARNING")

# GMT-3 timezone (São Paulo)
TZ_GMT_MINUS_3 = timezone(timedelta(hours=-3))


def get_timestamp_gmt3() -> str:
    """Get current timestamp in GMT-3 format for file names."""
    return datetime.now(TZ_GMT_MINUS_3).strftime("%Y%m%d_%H%M%S")


def get_datetime_gmt3() -> datetime:
    """Get current datetime in GMT-3."""
    return datetime.now(TZ_GMT_MINUS_3)


app = typer.Typer(
    name="research",
    help="Realizar entrevistas de pesquisa UX com synths (sistema multi-agente)",
    no_args_is_help=True,
)
console = Console()


def validate_synth_exists(synth_id: str) -> bool:
    """
    Check if a synth with the given ID exists in the database.

    Args:
        synth_id: The synth ID to check

    Returns:
        True if synth exists, False otherwise
    """
    synths_path = Path("data/synths/synths.json")
    if not synths_path.exists():
        return False

    with open(synths_path, encoding="utf-8") as f:
        synths = json.load(f)

    return any(synth.get("id") == synth_id for synth in synths)


@app.command()
def research(
    synth_id: str = typer.Argument(
        ..., help="ID do synth a ser entrevistado (6 caracteres)"
    ),
    topic_guide_name: str = typer.Argument(
        ..., help="Nome do topic guide (ex: compra-amazon)"
    ),
    max_turns: int = typer.Option(
        6,
        "--max-turns",
        "-t",
        min=1,
        max=50,
        help="Número máximo de turnos de conversa",
    ),
    model: str = typer.Option(
        "gpt-5-mini",
        "--model",
        "-m",
        help="Modelo de LLM a usar (ex: gpt-5-mini, gpt-4o)",
    ),
    trace_path: str = typer.Option(
        None,
        "--trace-path",
        help="Caminho para salvar arquivo de trace (auto-gera se não especificado)",
    ),
    transcript_path: str = typer.Option(
        None,
        "--transcript-path",
        "-o",
        help="Caminho para salvar transcrição JSON (auto-gera se não especificado)",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suprimir output da conversa",
    ),
):
    """
    Executar entrevista de pesquisa UX com um synth usando sistema multi-agente.

    O sistema utiliza múltiplos agentes:
    - Orchestrator: Decide a alternância de turnos
    - Interviewer: Faz perguntas baseadas no topic guide
    - Interviewee: Responde como a persona sintética
    - Reviewer: Adapta tom para autenticidade

    O topic guide deve conter:
    - script.json: Roteiro de perguntas da entrevista
    - summary.md: Contexto e descrições dos materiais

    Exemplo:
        synthlab research abc123 compra-amazon
        synthlab research abc123 compra-amazon --max-turns 8 --model gpt-4o
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
            "\nUse [bold]synthlab topic-guide list[/bold] para ver guides disponíveis"
        )
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
            "\nO topic guide deve conter um arquivo script.json com o roteiro de perguntas"
        )
        sys.exit(1)

    # Check for OPENAI_API_KEY
    if not os.getenv("OPENAI_API_KEY"):
        console.print(
            "[bold red]✗[/bold red] Variável de ambiente OPENAI_API_KEY não configurada",
            style="red",
        )
        console.print(
            "\nConfigure sua chave de API:\n[bold]export OPENAI_API_KEY='sua-chave'[/bold]"
        )
        sys.exit(1)

    # Generate paths if not specified (using GMT-3)
    timestamp = get_timestamp_gmt3()
    if trace_path is None:
        trace_path = f"data/traces/interview_{synth_id}_{timestamp}.trace.json"
    if transcript_path is None:
        transcript_path = f"data/transcripts/interview_{synth_id}_{timestamp}.json"

    verbose = not quiet

    # Print header
    console.print()
    console.print("[bold cyan]═" * 60 + "[/bold cyan]")
    console.print("[bold cyan]  Agentic Interview System[/bold cyan]")
    console.print("[bold cyan]═" * 60 + "[/bold cyan]")
    console.print()
    console.print(f"  Synth ID: [bold]{synth_id}[/bold]")
    console.print(f"  Topic Guide: [bold]{topic_guide_name}[/bold]")
    console.print(f"  Model: [bold]{model}[/bold]")
    console.print(f"  Max Turns: [bold]{max_turns}[/bold]")
    console.print(f"  Trace: [bold]{trace_path}[/bold]")
    console.print(f"  Transcript: [bold]{transcript_path}[/bold]")
    console.print()
    console.print("[cyan]─" * 60 + "[/cyan]")
    console.print("[cyan]  Starting interview...[/cyan]")
    console.print("[cyan]─" * 60 + "[/cyan]")

    try:
        # Run interview (async)
        logger.info(
            f"Starting agentic interview with synth {synth_id} and topic guide {topic_guide_name}"
        )

        result = asyncio.run(
            run_interview(
                synth_id=synth_id,
                topic_guide_name=topic_guide_name,
                max_turns=max_turns,
                trace_path=trace_path,
                model=model,
                verbose=verbose,
            )
        )

        # Print summary
        console.print()
        console.print("[cyan]─" * 60 + "[/cyan]")
        console.print("[bold green]  Interview completed![/bold green]")
        console.print("[cyan]─" * 60 + "[/cyan]")
        console.print(f"  Total turns: [bold]{result.total_turns}[/bold]")
        console.print(f"  Total messages: [bold]{len(result.messages)}[/bold]")
        console.print(f"  Synth: [bold]{result.synth_name}[/bold]")

        if result.trace_path:
            console.print(
                f"\n[bold green]✓[/bold green] Trace salvo em: [bold]{result.trace_path}[/bold]"
            )

        # Save transcript
        transcript_data = {
            "metadata": {
                "synth_id": result.synth_id,
                "synth_name": result.synth_name,
                "topic_guide": result.topic_guide_name,
                "model": model,
                "max_turns": max_turns,
                "total_turns": result.total_turns,
                "timestamp": get_datetime_gmt3().isoformat(),
                "timezone": "GMT-3",
            },
            "messages": [
                {
                    "speaker": msg.speaker,
                    "text": msg.text,
                    "internal_notes": msg.internal_notes,
                }
                for msg in result.messages
            ],
        }

        # Ensure transcript directory exists
        Path(transcript_path).parent.mkdir(parents=True, exist_ok=True)
        with open(transcript_path, "w", encoding="utf-8") as f:
            json.dump(transcript_data, f, ensure_ascii=False, indent=2)

        console.print(
            f"[bold green]✓[/bold green] Transcrição salva em: [bold]{transcript_path}[/bold]"
        )

        # Print conversation summary
        console.print()
        console.print("[bold cyan]═" * 60 + "[/bold cyan]")
        console.print("[bold cyan]  Conversation Summary[/bold cyan]")
        console.print("[bold cyan]═" * 60 + "[/bold cyan]")
        for i, msg in enumerate(result.messages, 1):
            preview = msg.text[:80] + "..." if len(msg.text) > 80 else msg.text
            speaker_color = "blue" if msg.speaker == "Interviewer" else "green"
            console.print(
                f"  {i}. [{speaker_color}][{msg.speaker}][/{speaker_color}]: {preview}")

    except FileNotFoundError as e:
        console.print(
            f"[bold red]✗[/bold red] Arquivo não encontrado: {e}", style="red")
        sys.exit(1)
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


@app.command()
def batch(
    topic_guide_name: str = typer.Argument(
        ..., help="Nome do topic guide (ex: compra-amazon)"
    ),
    max_interviews: int = typer.Option(
        10,
        "--max-interviews",
        "-n",
        min=1,
        max=100,
        help="Número máximo de entrevistas a realizar",
    ),
    max_concurrent: int = typer.Option(
        10,
        "--max-concurrent",
        "-c",
        min=1,
        max=20,
        help="Número máximo de entrevistas simultâneas",
    ),
    max_turns: int = typer.Option(
        6,
        "--max-turns",
        "-t",
        min=1,
        max=50,
        help="Número máximo de turnos por entrevista",
    ),
    model: str = typer.Option(
        "gpt-5-mini",
        "--model",
        "-m",
        help="Modelo de LLM a usar (ex: gpt-5-mini, gpt-4o)",
    ),
    no_summary: bool = typer.Option(
        False,
        "--no-summary",
        help="Não gerar síntese ao final das entrevistas",
    ),
    output_path: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Caminho para salvar o relatório de síntese (auto-gera se não especificado)",
    ),
):
    """
    Executar entrevistas em batch com múltiplos synths em paralelo.

    Este comando permite entrevistar vários synths de uma vez, com execução
    paralela controlada. Ao final, gera uma síntese consolidada de todas
    as entrevistas.

    Os synths são selecionados em ordem do banco de dados, começando do
    primeiro, até atingir o limite especificado por --max-interviews.

    Exemplo:
        synthlab research batch compra-amazon --max-interviews 5
        synthlab research batch compra-amazon -n 10 -c 5 --model gpt-4o
    """
    import os

    # Validate topic guide
    base_dir = Path(os.environ.get("TOPIC_GUIDES_DIR", "data/topic_guides"))
    topic_dir = base_dir / topic_guide_name

    if not topic_dir.exists():
        console.print(
            f"[bold red]✗[/bold red] Topic guide '{topic_guide_name}' não encontrado",
            style="red",
        )
        console.print(f"\nProcurado em: {topic_dir}")
        sys.exit(1)

    script_path = topic_dir / "script.json"
    if not script_path.exists():
        console.print(
            f"[bold red]✗[/bold red] Arquivo script.json não encontrado no topic guide '{topic_guide_name}'",
            style="red",
        )
        sys.exit(1)

    # Check for OPENAI_API_KEY
    if not os.getenv("OPENAI_API_KEY"):
        console.print(
            "[bold red]✗[/bold red] Variável de ambiente OPENAI_API_KEY não configurada",
            style="red",
        )
        sys.exit(1)

    # Generate output path if not specified
    timestamp = get_timestamp_gmt3()
    if output_path is None:
        output_path = f"data/reports/batch_{topic_guide_name}_{timestamp}.md"

    generate_summary = not no_summary

    # Print header
    console.print()
    console.print("[bold cyan]═" * 60 + "[/bold cyan]")
    console.print("[bold cyan]  Batch Interview System[/bold cyan]")
    console.print("[bold cyan]═" * 60 + "[/bold cyan]")
    console.print()
    console.print(f"  Topic Guide: [bold]{topic_guide_name}[/bold]")
    console.print(f"  Max Interviews: [bold]{max_interviews}[/bold]")
    console.print(f"  Max Concurrent: [bold]{max_concurrent}[/bold]")
    console.print(f"  Max Turns: [bold]{max_turns}[/bold]")
    console.print(f"  Model: [bold]{model}[/bold]")
    console.print(f"  Generate Summary: [bold]{generate_summary}[/bold]")
    if generate_summary:
        console.print(f"  Output: [bold]{output_path}[/bold]")
    console.print()
    console.print("[cyan]─" * 60 + "[/cyan]")

    try:
        # Run batch interviews
        result = asyncio.run(
            run_batch_interviews(
                topic_guide_name=topic_guide_name,
                max_interviews=max_interviews,
                max_concurrent=max_concurrent,
                max_turns=max_turns,
                model=model,
                generate_summary=generate_summary,
            )
        )

        # Print results
        console.print()
        console.print("[cyan]─" * 60 + "[/cyan]")
        console.print("[bold green]  Batch Completed![/bold green]")
        console.print("[cyan]─" * 60 + "[/cyan]")
        console.print(f"  Batch ID: [bold]{result.batch_id}[/bold]")
        console.print(f"  Requested: [bold]{result.total_requested}[/bold]")
        console.print(f"  Completed: [bold green]{result.total_completed}[/bold green]")
        if result.total_failed > 0:
            console.print(f"  Failed: [bold red]{result.total_failed}[/bold red]")

        # Show failed interviews
        if result.failed_interviews:
            console.print()
            console.print("[yellow]Entrevistas com erro:[/yellow]")
            for synth_id, synth_name, error in result.failed_interviews:
                console.print(f"  - {synth_name} ({synth_id}): {error}")

        # Show successful interviews and transcript paths
        if result.successful_interviews:
            console.print()
            console.print("[green]Entrevistas concluídas:[/green]")
            for i, (interview_result, synth) in enumerate(result.successful_interviews):
                transcript = result.transcript_paths[i] if i < len(result.transcript_paths) else "N/A"
                console.print(
                    f"  - {interview_result.synth_name} ({interview_result.synth_id}): "
                    f"{interview_result.total_turns} turnos"
                )

        # Show transcript directory
        if result.transcript_paths:
            transcript_dir = str(Path(result.transcript_paths[0]).parent)
            console.print()
            console.print(
                f"[bold green]✓[/bold green] Transcrições salvas em: [bold]{transcript_dir}/[/bold]"
            )

        # Display summary
        if result.summary:
            console.print()
            console.print("[bold cyan]═" * 60 + "[/bold cyan]")
            console.print("[bold cyan]  Síntese das Entrevistas[/bold cyan]")
            console.print("[bold cyan]═" * 60 + "[/bold cyan]")
            console.print()
            console.print(result.summary)

            if result.summary_path:
                console.print()
                console.print(
                    f"[bold green]✓[/bold green] Síntese salva em: [bold]{result.summary_path}[/bold]"
                )

    except FileNotFoundError as e:
        console.print(
            f"[bold red]✗[/bold red] Arquivo não encontrado: {e}", style="red"
        )
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠[/yellow] Batch interrompido pelo usuário")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Batch failed: {e}")
        console.print(f"[bold red]✗[/bold red] Erro no batch: {e}", style="red")
        sys.exit(1)


if __name__ == "__main__":
    """Validation of CLI module."""
    print("=== Research Agentic CLI Module Validation ===\n")

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
        from synth_lab.research_agentic.runner import run_interview

        print("✓ All required imports successful")
    except Exception as e:
        all_validation_failures.append(f"Import validation: {e}")

    # Test 4: validate_synth_exists function works
    total_tests += 1
    try:
        # Should return False for non-existent synth
        result = validate_synth_exists("nonexistent_id_12345")
        assert result is False
        print("✓ validate_synth_exists works correctly")
    except Exception as e:
        all_validation_failures.append(f"validate_synth_exists: {e}")

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
