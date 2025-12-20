"""Data models for PR-FAQ generation and storage.

Pydantic v2 models for:
- PR-FAQ documents (output)
- Version tracking and metadata

Third-party documentation:
- Pydantic v2: https://docs.pydantic.dev/latest/

Expected output (prfaq):
    PRFAQDocument(
        batch_id="batch_001",
        press_release=PressRelease(
            headline="New Product...",
            one_liner="Solves customer problem",
            problem_statement="Customers struggle with...",
            solution_overview="Our solution provides..."
        ),
        faq=[
            FAQItem(
                question="Why is this important?",
                answer="It solves critical pain point...",
                customer_segment="Product Manager"
            )
        ]
    )
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field


class ResearchReport(BaseModel):
    """Research batch report structure from summarizer agent."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "batch_id": "batch_001",
                "summary_content": "# Research Findings\n\nKey insights...",
                "sections": {
                    "executive_summary": "Summary of findings",
                    "recommendations": "Recommended product features"
                }
            }
        }
    )

    batch_id: str = Field(..., description="Unique batch identifier")
    summary_content: str = Field(..., description="Markdown-formatted summary text")
    sections: Dict[str, str] = Field(
        default_factory=dict,
        description="Structured sections: executive_summary, recommendations (required), "
        "recurrent_patterns, relevant_divergences, identified_tensions, notable_absences, key_quotes (optional)"
    )


class PressRelease(BaseModel):
    """Press Release component of PR-FAQ."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "headline": "Introducing CustomerInsight: Transform Research into Strategy",
                "one_liner": "AI-powered synthesis of qualitative research into actionable product documents",
                "problem_statement": "Product teams spend weeks manually analyzing interviews to create strategic documents",
                "solution_overview": "Automatically generates PR-FAQ from research batch summaries using AI synthesis"
            }
        }
    )

    headline: str = Field(..., description="Compelling product headline")
    one_liner: str = Field(..., description="One-sentence value proposition")
    problem_statement: str = Field(..., description="Customer problem description")
    solution_overview: str = Field(..., description="Solution benefits overview")


class FAQItem(BaseModel):
    """Single FAQ question-answer pair with customer segment."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "How does this help with research synthesis?",
                "answer": "Reduces analysis time from weeks to hours by extracting insights from interview data",
                "customer_segment": "Product Manager"
            }
        }
    )

    question: str = Field(..., description="FAQ question")
    answer: str = Field(..., description="FAQ answer derived from research")
    customer_segment: str = Field(..., description="Synth persona archetype this FAQ addresses")


class PRFAQDocument(BaseModel):
    """Complete PR-FAQ document with metadata and version tracking."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "batch_id": "batch_001",
                "press_release": {
                    "headline": "New Product",
                    "one_liner": "Solves problem",
                    "problem_statement": "Customer issue",
                    "solution_overview": "Our solution"
                },
                "faq": [
                    {
                        "question": "Q?",
                        "answer": "A",
                        "customer_segment": "Product Manager"
                    }
                ]
            }
        }
    )

    batch_id: str = Field(..., description="Source batch ID")
    press_release: PressRelease = Field(..., description="Press release section")
    faq: list[FAQItem] = Field(..., description="FAQ items (8-12 questions)")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(datetime.UTC) if hasattr(datetime, 'UTC') else datetime.utcnow())
    version: int = Field(default=1, description="Version number")
    edit_history: list[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of edits with timestamp, field, old_value, new_value"
    )
    validation_status: str = Field(
        default="valid",
        description="Validation status: valid, invalid, needs_review"
    )
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Quality confidence score (0-1)"
    )


class PRFAQVersion(BaseModel):
    """Historical version record for PR-FAQ document."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "batch_id": "batch_001",
                "version": 1,
                "generated_at": "2025-12-19T10:00:00",
                "generation_method": "auto_generated",
                "diff_with_previous": None
            }
        }
    )

    batch_id: str = Field(..., description="Source batch ID")
    version: int = Field(..., description="Version number")
    generated_at: datetime = Field(..., description="Generation timestamp")
    generation_method: str = Field(..., description="auto_generated or manual_edit")
    prfaq_data: PRFAQDocument = Field(..., description="Complete PR-FAQ snapshot")
    diff_with_previous: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Changes from previous version"
    )


class GenerationMetadata(BaseModel):
    """Metadata about PR-FAQ generation process."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "batch_id": "batch_001",
                "generation_timestamp": "2025-12-19T10:00:00",
                "model_used": "gpt-4",
                "prompt_strategy": "hybrid_chain_of_thought_structured_output",
                "token_usage": {"prompt": 500, "completion": 300, "total": 800}
            }
        }
    )

    batch_id: str = Field(..., description="Source batch ID")
    generation_timestamp: datetime = Field(default_factory=lambda: datetime.now(datetime.UTC) if hasattr(datetime, 'UTC') else datetime.utcnow())
    model_used: str = Field(default="gpt-4", description="LLM model identifier")
    prompt_strategy: str = Field(
        default="hybrid_chain_of_thought_structured_output",
        description="Prompting strategy used"
    )
    token_usage: Dict[str, int] = Field(
        default_factory=lambda: {"prompt": 0, "completion": 0, "total": 0},
        description="Token usage metrics"
    )
    validation_status: str = Field(default="valid", description="Validation result")
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Generation quality confidence"
    )


# Logging configuration
def setup_logging(log_file: str = "logs/research_prfaq.log") -> None:
    """Configure loguru logger for PR-FAQ feature.

    Args:
        log_file: Path to log file (default: logs/research_prfaq.log)
    """
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove default handler
    logger.remove()

    # Add console handler with INFO level
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level="INFO"
    )

    # Add file handler with DEBUG level and rotation
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
        compression="zip"
    )

    logger.info("PR-FAQ logging initialized")


if __name__ == "__main__":
    # Validation of models with real-world-like data
    import sys

    validation_failures = []
    total_tests = 0

    # Test 1: Create ResearchReport
    total_tests += 1
    try:
        report = ResearchReport(
            batch_id="batch_001",
            summary_content="# Research Findings\n\nCustomers struggle with data analysis",
            sections={
                "executive_summary": "3 key insights identified",
                "recommendations": "Build AI-powered synthesis tool"
            }
        )
        assert report.batch_id == "batch_001"
        assert "Research Findings" in report.summary_content
    except Exception as e:
        validation_failures.append(f"ResearchReport creation: {str(e)}")

    # Test 2: Create PressRelease
    total_tests += 1
    try:
        press_release = PressRelease(
            headline="Transform Research into Strategy",
            one_liner="AI-powered research synthesis",
            problem_statement="Manual analysis takes weeks",
            solution_overview="Automated synthesis saves time"
        )
        assert press_release.headline == "Transform Research into Strategy"
        assert len(press_release.one_liner) > 0
    except Exception as e:
        validation_failures.append(f"PressRelease creation: {str(e)}")

    # Test 3: Create FAQItem
    total_tests += 1
    try:
        faq_item = FAQItem(
            question="How does it work?",
            answer="Uses AI to analyze research interviews",
            customer_segment="Product Manager"
        )
        assert faq_item.question == "How does it work?"
        assert faq_item.customer_segment == "Product Manager"
    except Exception as e:
        validation_failures.append(f"FAQItem creation: {str(e)}")

    # Test 4: Create PRFAQDocument
    total_tests += 1
    try:
        prfaq = PRFAQDocument(
            batch_id="batch_001",
            press_release=PressRelease(
                headline="Test Product",
                one_liner="Test value",
                problem_statement="Test problem",
                solution_overview="Test solution"
            ),
            faq=[
                FAQItem(
                    question="Q1?",
                    answer="A1",
                    customer_segment="PM"
                )
            ]
        )
        assert prfaq.batch_id == "batch_001"
        assert len(prfaq.faq) == 1
        assert prfaq.version == 1
    except Exception as e:
        validation_failures.append(f"PRFAQDocument creation: {str(e)}")

    # Test 5: Test confidence_score bounds
    total_tests += 1
    try:
        prfaq_high = PRFAQDocument(
            batch_id="batch_001",
            press_release=PressRelease(
                headline="Test",
                one_liner="Test",
                problem_statement="Test",
                solution_overview="Test"
            ),
            faq=[FAQItem(question="Q?", answer="A", customer_segment="PM")],
            confidence_score=0.95
        )
        assert 0.0 <= prfaq_high.confidence_score <= 1.0
    except Exception as e:
        validation_failures.append(f"Confidence score bounds: {str(e)}")

    # Report results
    if validation_failures:
        print(f"❌ VALIDATION FAILED - {len(validation_failures)} of {total_tests} tests failed:")
        for failure in validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Models are validated and ready for use")
        sys.exit(0)
