"""
Demo script for agentic interview system.

This script demonstrates the multi-agent interview system with:
- Orchestrator deciding turn-taking
- Interviewer asking questions
- Interviewee (synth) responding
- Reviewers adapting tone for each speaker
- Full trace integration for visualization

References:
- OpenAI Agents SDK: https://openai.github.io/openai-agents-python/
- Trace Visualizer: src/synth_lab/trace_visualizer/

Sample usage:
```bash
# Install dependencies first
uv pip install -e .

# Run with synth ID from database
uv run examples/research_agentic/demo_interview.py --synth-id fhynws

# Run with custom settings
uv run examples/research_agentic/demo_interview.py --synth-id fhynws --max-turns 4 --model gpt-4o

# Run with trace output
uv run examples/research_agentic/demo_interview.py --synth-id fhynws --trace-path data/traces/demo.trace.json

# List available synths
uv run python -c "import json; data = json.load(open('data/synths/synths.json')); print('\\n'.join(f'{s[\"id\"]}: {s[\"nome\"]}' for s in data[:10]))"
```

Expected output:
- Conversation printed to console
- Trace file saved to data/traces/ (if --trace-path specified)
"""

from synth_lab.research_agentic.runner import run_interview
from loguru import logger
import argparse
import asyncio
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Suppress debug logging
logger.remove()
logger.add(sys.stderr, level="WARNING")


# GMT-3 timezone (São Paulo)
TZ_GMT_MINUS_3 = timezone(timedelta(hours=-3))


def get_timestamp_gmt3() -> str:
    """Get current timestamp in GMT-3 format for file names."""
    return datetime.now(TZ_GMT_MINUS_3).strftime("%Y%m%d_%H%M%S")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run an agentic interview with a synthetic persona from the database.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with a specific synth ID
  python demo_interview.py --synth-id fhynws

  # Run with custom topic guide
  python demo_interview.py --synth-id fhynws --topic-guide compra-amazon

  # Use a different model
  python demo_interview.py --synth-id fhynws --model gpt-4o

  # Save trace for visualization
  python demo_interview.py --synth-id fhynws --trace-path data/traces/demo.trace.json
        """,
    )
    parser.add_argument(
        "--synth-id",
        type=str,
        required=True,
        help="ID of the synth to interview (from data/synths/synths.json)",
    )
    parser.add_argument(
        "--topic-guide",
        type=str,
        default="compra-amazon",
        help="Name of the topic guide directory (default: compra-amazon)",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=6,
        help="Maximum number of conversation turns (default: 6)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-5-nano",
        help="LLM model to use (default: gpt-5-nano)",
    )
    parser.add_argument(
        "--trace-path",
        type=str,
        default=None,
        help="Path to save trace file (optional, auto-generates if not specified)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=True,
        help="Print conversation to console (default: True)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress conversation output",
    )
    return parser.parse_args()


async def main():
    """Run an agentic interview with a synth from the database."""
    args = parse_args()
    verbose = not args.quiet

    # Generate trace path if not specified (using GMT-3)
    trace_path = args.trace_path
    if trace_path is None:
        timestamp = get_timestamp_gmt3()
        trace_path = f"data/traces/interview_{args.synth_id}_{timestamp}.trace.json"

    print("=" * 60)
    print("Agentic Interview Demo")
    print("=" * 60)
    print()
    print("This demo shows a multi-agent interview system with:")
    print("- Orchestrator (decides turn-taking)")
    print("- Interviewer (asks questions)")
    print("- Interviewee (synthetic persona from database)")
    print("- Reviewers (adapt tone for authenticity)")
    print()
    print(f"Synth ID: {args.synth_id}")
    print(f"Topic Guide: {args.topic_guide}")
    print(f"Model: {args.model}")
    print(f"Max turns: {args.max_turns}")
    print(f"Trace path: {trace_path}")
    print()
    print("-" * 60)
    print("Starting interview...")
    print("-" * 60)

    try:
        result = await run_interview(
            synth_id=args.synth_id,
            topic_guide_name=args.topic_guide,
            max_turns=args.max_turns,
            trace_path=trace_path,
            model=args.model,
            verbose=verbose,
        )

        print()
        print("-" * 60)
        print("Interview completed!")
        print("-" * 60)
        print(f"Total turns: {result.total_turns}")
        print(f"Total messages: {len(result.messages)}")
        print(f"Synth: {result.synth_name}")
        if result.trace_path:
            print(f"Trace saved to: {result.trace_path}")

        # Summary
        print()
        print("=" * 60)
        print("Conversation Summary")
        print("=" * 60)
        for i, msg in enumerate(result.messages, 1):
            preview = msg.text[:100] + \
                "..." if len(msg.text) > 100 else msg.text
            print(f"{i}. [{msg.speaker}]: {preview}")

    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("\nMake sure:")
        print("- synths.json exists at data/synths/synths.json")
        print(f"- topic guide exists at data/topic_guides/{args.topic_guide}/")
        sys.exit(1)
    except ValueError as e:
        print(f"\nError: {e}")
        print("\nUse --synth-id with a valid ID from data/synths/synths.json")
        print("List available synths with:")
        print(
            '  python -c "import json; data = json.load(open(\'data/synths/synths.json\')); print(\'\\n\'.join(f\'{s[\"id\"]}: {s[\"nome\"]}\' for s in data[:10]))"')
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure you have:")
        print("1. Set OPENAI_API_KEY environment variable")
        print("2. Installed dependencies: uv pip install -e .")
        raise


if __name__ == "__main__":
    asyncio.run(main())
