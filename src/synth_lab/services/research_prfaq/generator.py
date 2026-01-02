"""PR-FAQ generation from research batch reports using LLM.

Generates Markdown-formatted PR-FAQ documents following Amazon's Working Backwards framework:
1. Parse research report from summary content
2. Use few-shot examples to guide LLM
3. Generate PR-FAQ directly in Markdown format
4. Return content (stored in database by caller)

Third-party documentation:
- OpenAI API: https://platform.openai.com/docs/
- Amazon Working Backwards: https://www.amazon.jobs/en/landing_pages/working-backwards

Sample usage:
    from .generator import generate_prfaq_from_content

    prfaq_md = generate_prfaq_from_content(summary_content, "batch_id", "gpt-xxxx")

Expected output:
    String containing Markdown-formatted PR-FAQ document with:
    - Press Release: Heading, Subheading, Summary, Problem, Solution, Quotes
    - FAQ: External FAQs (8-12) + Internal FAQs (8-12)
"""

import os
from datetime import datetime
from typing import Optional

from loguru import logger
from openai import OpenAI
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes

from synth_lab.infrastructure.phoenix_tracing import get_tracer

from .prompts import get_few_shot_examples, get_system_prompt

# Phoenix/OpenTelemetry tracer for observability
_tracer = get_tracer("prfaq-generator")


def generate_prfaq_from_content(
    summary_content: str,
    batch_id: str,
    model: str = "gpt-4.1-mini",
    api_key: Optional[str] = None) -> str:
    """Generate PR-FAQ Markdown from research summary content using OpenAI API.

    Args:
        summary_content: Research summary markdown content
        batch_id: Research batch identifier for logging
        model: OpenAI model to use (default: gpt-4.1-mini)
        api_key: OpenAI API key (default: from OPENAI_API_KEY env var)

    Returns:
        String containing Markdown-formatted PR-FAQ document

    Raises:
        RuntimeError: If LLM generation fails
    """
    logger.info(f"Starting PR-FAQ Markdown generation for batch {batch_id}")

    with _tracer.start_as_current_span(
        f"Generate PR-FAQ: {batch_id}",
        attributes={
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
            "batch_id": batch_id,
            "model": model,
            "summary_length": len(summary_content),
        }) as span:
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))

        # Build prompt with system prompt + few-shot examples + user content
        system_prompt = get_system_prompt()
        few_shot_examples = get_few_shot_examples()

        # Format few-shot examples as conversation
        messages = [{"role": "system", "content": system_prompt}]

        # Add few-shot examples (user research → assistant PR-FAQ MD)
        for example in few_shot_examples:
            messages.append(
                {"role": "user", "content": f"Research Report:\n\n{example['research_summary']}"}
            )
            messages.append({"role": "assistant", "content": example["prfaq_output"]})

        # Add current research report
        user_prompt = f"""Research Report:

{summary_content}

Based on this research batch summary, generate a complete PR-FAQ document in Markdown format following the Amazon Working Backwards framework.

Batch ID: {batch_id}
Generated: {datetime.now().strftime("%Y-%m-%d")}

Generate the PR-FAQ with:
- Press Release sections (Heading, Subheading, Summary, Problem, Solution, Quotes)
- External FAQs (8-12 customer/press questions)
- Internal FAQs (8-12 stakeholder questions covering finance, operations, technical, risks)

Extract insights from the "Recomendações" and "Padrões Recorrentes" sections. Use actual quotes when available.

Return ONLY the Markdown-formatted PR-FAQ document."""

        messages.append({"role": "user", "content": user_prompt})

        logger.debug(f"Calling OpenAI API with model {model}")

        # Call OpenAI API for Markdown generation
        # Note: gpt-4.1-mini is a fast, cost-effective model for generation tasks.
        # 16000 max tokens allows for comprehensive PR-FAQ output.
        try:
            response = client.chat.completions.create(
                model=model, messages=messages, max_completion_tokens=16000
            )

            logger.info(f"OpenAI API call successful. Tokens used: {response.usage.total_tokens}")

            # Extract Markdown response
            prfaq_markdown = response.choices[0].message.content.strip()

            logger.info(
                f"PR-FAQ Markdown generation successful for {batch_id} ({len(prfaq_markdown)} characters)"
            )

            if span:
                span.set_attribute("tokens_used", response.usage.total_tokens)
                span.set_attribute("prfaq_length", len(prfaq_markdown))

            return prfaq_markdown

        except Exception as e:
            error_msg = f"LLM generation failed: {str(e)}"
            logger.error(error_msg)
            if span:
                span.set_attribute("error", error_msg)
            raise RuntimeError(error_msg) from e


if __name__ == "__main__":
    # Validation test
    import sys

    validation_failures = []
    total_tests = 0

    # Test 1: Import check
    total_tests += 1
    try:
        from synth_lab.services.research_prfaq.generator import generate_prfaq_from_content

        print("✓ Import successful")
    except Exception as e:
        validation_failures.append(f"Import failed: {e}")

    # Test 2: Check OPENAI_API_KEY
    total_tests += 1
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OPENAI_API_KEY not set - skipping LLM generation test")
        print("   Set OPENAI_API_KEY environment variable to test full generation")
    else:
        # Test 3: Generate PR-FAQ from sample content
        total_tests += 1
        sample_content = """# Síntese das Entrevistas

## Padrões Recorrentes
- Usuários preferem interfaces simples
- Preço é um fator decisivo

## Recomendações
1. Simplificar o processo de checkout
2. Oferecer mais opções de pagamento
"""
        try:
            prfaq_md = generate_prfaq_from_content(
                summary_content=sample_content,
                batch_id="test_validation",
                model="gpt-4.1-mini")
            logger.info(f"Generated PR-FAQ Markdown ({len(prfaq_md)} characters)")

            # Verify structure
            if "Press Release" not in prfaq_md and "FAQ" not in prfaq_md:
                validation_failures.append("Generated PR-FAQ missing key sections")
            else:
                print(f"✓ Generated PR-FAQ with {len(prfaq_md)} characters")

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
        if api_key and total_tests > 2:
            print(f"\n✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
            print("Generator is validated and ready for use")
        else:
            print(f"\n⚠️  PARTIAL VALIDATION - {total_tests} basic test(s) passed")
            print("   Set OPENAI_API_KEY to run full validation")
        sys.exit(0)
