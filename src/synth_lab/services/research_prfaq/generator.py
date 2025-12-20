"""PR-FAQ generation from research batch reports using LLM.

Generates Markdown-formatted PR-FAQ documents following Amazon's Working Backwards framework:
1. Parse research report from Markdown file
2. Use few-shot examples to guide LLM
3. Generate PR-FAQ directly in Markdown format
4. Save to output/reports directory

Third-party documentation:
- OpenAI API: https://platform.openai.com/docs/
- Amazon Working Backwards: https://www.amazon.jobs/en/landing_pages/working-backwards

Sample usage:
    from synth_lab.research_prfaq.generator import generate_prfaq_markdown
    from synth_lab.research_prfaq.models import setup_logging

    setup_logging()
    prfaq_md = generate_prfaq_markdown("batch_compra-amazon_20251218_164204")

Expected output:
    String containing Markdown-formatted PR-FAQ document with:
    - Press Release: Heading, Subheading, Summary, Problem, Solution, Quotes
    - FAQ: External FAQs (8-12) + Internal FAQs (8-12)
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional

from openai import OpenAI
from loguru import logger

from .generation_models import parse_batch_summary
from .prompts import get_system_prompt, get_few_shot_examples


def generate_prfaq_markdown(
    batch_id: str,
    model: str = "gpt-5-mini",
    api_key: Optional[str] = None,
    data_dir: str = "output/reports"
) -> str:
    """Generate PR-FAQ Markdown from research batch report using OpenAI API.

    Args:
        batch_id: Research batch identifier (e.g., batch_compra-amazon_20251218_164204)
        model: OpenAI model to use (default: gpt-4o)
        api_key: OpenAI API key (default: from OPENAI_API_KEY env var)
        data_dir: Directory containing research reports (default: output/reports)

    Returns:
        String containing Markdown-formatted PR-FAQ document

    Raises:
        FileNotFoundError: If batch report doesn't exist
        RuntimeError: If LLM generation fails
    """
    logger.info(f"Starting PR-FAQ Markdown generation for batch {batch_id}")

    # Load research report
    report = parse_batch_summary(batch_id, data_dir=data_dir)
    logger.info(f"Loaded research report with {len(report.sections)} sections")

    # Initialize OpenAI client
    client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    # Build prompt with system prompt + few-shot examples + user content
    system_prompt = get_system_prompt()
    few_shot_examples = get_few_shot_examples()

    # Format few-shot examples as conversation
    messages = [
        {"role": "system", "content": system_prompt}
    ]

    # Add few-shot examples (user research → assistant PR-FAQ MD)
    for example in few_shot_examples:
        messages.append({
            "role": "user",
            "content": f"Research Report:\n\n{example['research_summary']}"
        })
        messages.append({
            "role": "assistant",
            "content": example['prfaq_output']
        })

    # Add current research report
    user_prompt = f"""Research Report:

{report.summary_content}

Based on this research batch summary, generate a complete PR-FAQ document in Markdown format following the Amazon Working Backwards framework.

Batch ID: {batch_id}
Generated: {datetime.now().strftime('%Y-%m-%d')}

Generate the PR-FAQ with:
- Press Release sections (Heading, Subheading, Summary, Problem, Solution, Quotes)
- External FAQs (8-12 customer/press questions)
- Internal FAQs (8-12 stakeholder questions covering finance, operations, technical, risks)

Extract insights from the "Recomendações" and "Padrões Recorrentes" sections. Use actual quotes when available.

Return ONLY the Markdown-formatted PR-FAQ document."""

    messages.append({"role": "user", "content": user_prompt})

    logger.debug(f"Calling OpenAI API with model {model}")

    # Call OpenAI API for Markdown generation
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_completion_tokens=4000  # Increased for full Markdown output
        )

        logger.info(f"OpenAI API call successful. Tokens used: {response.usage.total_tokens}")

        # Extract Markdown response
        prfaq_markdown = response.choices[0].message.content.strip()

        logger.info(f"PR-FAQ Markdown generation successful for {batch_id} ({len(prfaq_markdown)} characters)")

        return prfaq_markdown

    except Exception as e:
        error_msg = f"LLM generation failed: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e


def save_prfaq_markdown(
    prfaq_markdown: str,
    batch_id: str,
    output_dir: str = "output/reports"
) -> Path:
    """Save PR-FAQ Markdown to file.

    Args:
        prfaq_markdown: Markdown content of PR-FAQ
        batch_id: Batch identifier for filename
        output_dir: Base directory for PR-FAQ outputs (default: output/reports)

    Returns:
        Path to saved Markdown file
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Create filename with batch_id
    filename = f"{batch_id}_prfaq.md"
    file_path = output_path / filename

    # Save Markdown content
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(prfaq_markdown)

    logger.info(f"Saved PR-FAQ Markdown to {file_path} ({len(prfaq_markdown)} characters)")
    return file_path


def load_prfaq_markdown(
    batch_id: str,
    output_dir: str = "output/reports"
) -> str:
    """Load PR-FAQ Markdown from file.

    Args:
        batch_id: Batch identifier
        output_dir: Base directory for PR-FAQ outputs

    Returns:
        String containing Markdown content

    Raises:
        FileNotFoundError: If PR-FAQ file doesn't exist
    """
    output_path = Path(output_dir)
    filename = f"{batch_id}_prfaq.md"
    file_path = output_path / filename

    if not file_path.exists():
        raise FileNotFoundError(f"PR-FAQ Markdown file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        prfaq_markdown = f.read()

    logger.info(f"Loaded PR-FAQ Markdown from {file_path} ({len(prfaq_markdown)} characters)")
    return prfaq_markdown


if __name__ == "__main__":
    # Validation test with real batch summary
    import sys
    from synth_lab.research_prfaq.models import setup_logging

    setup_logging()

    validation_failures = []
    total_tests = 0

    # Test 1: Check for available research reports
    total_tests += 1
    reports_dir = Path("output/reports")
    if not reports_dir.exists():
        validation_failures.append(f"Reports directory not found: {reports_dir}")
    else:
        md_files = list(reports_dir.glob("*.md"))
        if not md_files:
            print("⚠️  No research reports found in output/reports/")
            print("   Run research summarizer first to generate batch reports")
        else:
            # Use first available report for testing
            test_report = md_files[0].stem  # Get filename without extension
            logger.info(f"Using test report: {test_report}")

            # Test 2: Generate PR-FAQ Markdown (requires OPENAI_API_KEY)
            total_tests += 1
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("⚠️  OPENAI_API_KEY not set - skipping LLM generation test")
                print("   Set OPENAI_API_KEY environment variable to test full generation")
            else:
                try:
                    prfaq_md = generate_prfaq_markdown(test_report)
                    logger.info(f"Generated PR-FAQ Markdown ({len(prfaq_md)} characters)")

                    # Verify structure
                    required_sections = ["Press Release", "Frequently Asked Questions"]
                    missing = [s for s in required_sections if s not in prfaq_md]
                    if missing:
                        validation_failures.append(f"Generated PR-FAQ missing sections: {missing}")

                    # Test 3: Save PR-FAQ
                    total_tests += 1
                    saved_path = save_prfaq_markdown(prfaq_md, test_report)
                    if not saved_path.exists():
                        validation_failures.append(f"Saved file not found: {saved_path}")

                    # Test 4: Load PR-FAQ
                    total_tests += 1
                    loaded_md = load_prfaq_markdown(test_report)
                    if loaded_md != prfaq_md:
                        validation_failures.append("Loaded PR-FAQ doesn't match saved PR-FAQ")
                    else:
                        logger.info("Save/load round-trip successful")

                except Exception as e:
                    validation_failures.append(f"PR-FAQ generation failed: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())

    # Report results
    if validation_failures:
        print(f"\n❌ VALIDATION FAILED - {len(validation_failures)} of {total_tests} tests failed:")
        for failure in validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and total_tests > 1:
            print(f"\n✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
            print("Generator is validated and ready for use")
        else:
            print(f"\n⚠️  PARTIAL VALIDATION - {total_tests} basic test(s) passed")
            print("   Set OPENAI_API_KEY and add research reports to run full validation")
        sys.exit(0)
