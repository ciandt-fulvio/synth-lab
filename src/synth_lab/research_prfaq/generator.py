"""PR-FAQ generation from research batch reports using LLM.

Implements hybrid chain-of-thought + structured output strategy:
1. Parse research report to extract pain points, benefits, segments
2. Use few-shot examples to guide LLM
3. Generate structured PR-FAQ with JSON validation
4. Calculate confidence score based on research completeness

Third-party documentation:
- OpenAI API: https://platform.openai.com/docs/
- Pydantic: https://docs.pydantic.dev/

Sample usage:
    from synth_lab.research_prfaq.generator import generate_prfaq
    from synth_lab.research_prfaq.models import ResearchReport, setup_logging

    setup_logging()
    report = ResearchReport(batch_id="b1", summary_content="...", sections={...})
    prfaq = generate_prfaq(report)

Expected output:
    PRFAQDocument with:
    - press_release: headline, one_liner, problem_statement, solution_overview
    - faq: 8-12 Q&A items with customer segments
    - confidence_score: based on research completeness
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

from openai import OpenAI
from loguru import logger

from synth_lab.research_prfaq.models import (
    ResearchReport,
    PRFAQDocument,
    PressRelease,
    FAQItem,
    GenerationMetadata,
)
from synth_lab.research_prfaq.prompts import (
    get_system_prompt,
    get_few_shot_examples,
    get_json_schema,
)
from synth_lab.research_prfaq.validator import validate_research_report, validate_prfaq


def generate_prfaq(
    report: ResearchReport,
    model: str = "gpt-4o-2024-08-06",
    api_key: Optional[str] = None
) -> PRFAQDocument:
    """Generate PR-FAQ from research batch report using OpenAI API.

    Args:
        report: ResearchReport with batch research data
        model: OpenAI model to use (default: gpt-4o with structured outputs)
        api_key: OpenAI API key (default: from OPENAI_API_KEY env var)

    Returns:
        PRFAQDocument with generated PR-FAQ content

    Raises:
        ValueError: If report lacks critical sections or validation fails
        RuntimeError: If LLM generation fails
    """
    logger.info(f"Starting PR-FAQ generation for batch {report.batch_id}")

    # Validate research report first
    validation_result = validate_research_report(report)
    if not validation_result.is_valid:
        error_msg = f"Research report validation failed: {validation_result.errors}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    if validation_result.warnings:
        logger.warning(f"Research report warnings: {validation_result.warnings}")

    logger.info(f"Research report validation passed with confidence {validation_result.confidence_score:.2f}")

    # Initialize OpenAI client
    client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

    # Build prompt with system prompt + few-shot examples + user content
    system_prompt = get_system_prompt()
    few_shot_examples = get_few_shot_examples()

    # Format few-shot examples as conversation
    messages = [
        {"role": "system", "content": system_prompt}
    ]

    # Add few-shot examples
    for example in few_shot_examples:
        messages.append({
            "role": "user",
            "content": f"Research Summary:\n\n{example['research_summary']}"
        })
        messages.append({
            "role": "assistant",
            "content": json.dumps(example['prfaq_output'], indent=2)
        })

    # Add current research report
    user_prompt = f"""Research Summary:

{report.summary_content}

Based on this research batch summary, generate a PR-FAQ document following the Amazon Working Backwards framework.

Focus on:
1. Extract pain points from "recommendations" and "recurrent_patterns" sections
2. Extract benefits from "recommendations" section
3. Map customer segments from identified personas in the research
4. Use key quotes to support the value proposition

Return ONLY valid JSON matching the schema."""

    messages.append({"role": "user", "content": user_prompt})

    logger.debug(f"Calling OpenAI API with model {model}")

    # Call OpenAI API with JSON mode for structured output
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=2000
        )

        logger.info(f"OpenAI API call successful. Tokens used: {response.usage.total_tokens}")

        # Extract JSON response
        response_text = response.choices[0].message.content
        prfaq_data = json.loads(response_text)

    except Exception as e:
        error_msg = f"LLM generation failed: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    # Parse response into Pydantic models
    try:
        press_release = PressRelease(**prfaq_data["press_release"])
        faq_items = [FAQItem(**item) for item in prfaq_data["faq"]]

        # Create PRFAQDocument
        prfaq = PRFAQDocument(
            batch_id=report.batch_id,
            press_release=press_release,
            faq=faq_items,
            generated_at=datetime.now(datetime.UTC) if hasattr(datetime, 'UTC') else datetime.utcnow(),
            version=1,
            validation_status="valid",
            confidence_score=validation_result.confidence_score
        )

        logger.debug(f"Created PRFAQDocument with {len(faq_items)} FAQ items")

    except Exception as e:
        error_msg = f"Failed to parse LLM response into models: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e

    # Validate generated PR-FAQ
    prfaq_validation = validate_prfaq(prfaq)
    if not prfaq_validation.is_valid:
        error_msg = f"Generated PR-FAQ validation failed: {prfaq_validation.errors}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    if prfaq_validation.warnings:
        logger.warning(f"Generated PR-FAQ warnings: {prfaq_validation.warnings}")

    # Update confidence score to be the minimum of report and prfaq confidence
    final_confidence = min(validation_result.confidence_score, prfaq_validation.confidence_score)
    prfaq.confidence_score = final_confidence

    logger.info(
        f"PR-FAQ generation successful for {report.batch_id}. "
        f"Confidence: {final_confidence:.2f}, FAQ items: {len(faq_items)}"
    )

    return prfaq


def save_prfaq_json(
    prfaq: PRFAQDocument,
    output_dir: str = "output/reports"
) -> Path:
    """Save PR-FAQ document to JSON file.

    Args:
        prfaq: PRFAQDocument to save
        output_dir: Base directory for PR-FAQ outputs (default: output/reports)

    Returns:
        Path to saved JSON file
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Create filename with batch_id
    filename = f"{prfaq.batch_id}_prfaq.json"
    file_path = output_path / filename

    # Convert to dict and save
    prfaq_dict = prfaq.model_dump(mode='json')

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(prfaq_dict, f, indent=2, default=str)

    logger.info(f"Saved PR-FAQ to {file_path}")
    return file_path


def load_prfaq_json(
    batch_id: str,
    output_dir: str = "output/reports"
) -> PRFAQDocument:
    """Load PR-FAQ document from JSON file.

    Args:
        batch_id: Batch identifier
        output_dir: Base directory for PR-FAQ outputs

    Returns:
        PRFAQDocument loaded from file

    Raises:
        FileNotFoundError: If PR-FAQ file doesn't exist
    """
    output_path = Path(output_dir)
    filename = f"{batch_id}_prfaq.json"
    file_path = output_path / filename

    if not file_path.exists():
        raise FileNotFoundError(f"PR-FAQ file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        prfaq_dict = json.load(f)

    # Parse dates
    if "generated_at" in prfaq_dict and isinstance(prfaq_dict["generated_at"], str):
        prfaq_dict["generated_at"] = datetime.fromisoformat(prfaq_dict["generated_at"].replace("Z", "+00:00"))

    prfaq = PRFAQDocument(**prfaq_dict)
    logger.info(f"Loaded PR-FAQ from {file_path}")
    return prfaq


if __name__ == "__main__":
    # Validation test with real batch summary
    import sys
    from synth_lab.research_prfaq.models import parse_batch_summary, setup_logging

    setup_logging()

    validation_failures = []
    total_tests = 0

    # Test 1: Parse test batch summary
    total_tests += 1
    try:
        report = parse_batch_summary("test_batch_001")
        logger.info(f"Loaded test batch: {report.batch_id}")
    except Exception as e:
        validation_failures.append(f"Failed to parse test batch: {str(e)}")

    # Test 2: Generate PR-FAQ (requires OPENAI_API_KEY)
    total_tests += 1
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY not set - skipping LLM generation test")
        print("   Set OPENAI_API_KEY environment variable to test full generation")
    else:
        try:
            prfaq = generate_prfaq(report)
            logger.info(f"Generated PR-FAQ with {len(prfaq.faq)} FAQ items")

            # Test 3: Save PR-FAQ
            total_tests += 1
            saved_path = save_prfaq_json(prfaq)
            if not saved_path.exists():
                validation_failures.append(f"Saved file not found: {saved_path}")

            # Test 4: Load PR-FAQ
            total_tests += 1
            loaded_prfaq = load_prfaq_json(report.batch_id)
            if loaded_prfaq.batch_id != prfaq.batch_id:
                validation_failures.append("Loaded PR-FAQ doesn't match saved PR-FAQ")

        except Exception as e:
            validation_failures.append(f"PR-FAQ generation failed: {str(e)}")

    # Report results
    if validation_failures:
        print(f"❌ VALIDATION FAILED - {len(validation_failures)} of {total_tests} tests failed:")
        for failure in validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        if api_key:
            print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
            print("Generator is validated and ready for use")
        else:
            print(f"⚠️  PARTIAL VALIDATION - {total_tests-3} of {total_tests} tests passed (LLM tests skipped)")
            print("   Set OPENAI_API_KEY to run full validation")
        sys.exit(0)
