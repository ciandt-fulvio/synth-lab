"""
PR-FAQ domain models for synth-lab.

Pydantic models for PR-FAQ document data.

References:
    - Schema definition: specs/010-rest-api/data-model.md
"""

from datetime import datetime

from pydantic import BaseModel, Field


class PRFAQSummary(BaseModel):
    """Summary PR-FAQ model for list endpoints."""

    exec_id: str = Field(..., description="Related execution ID")
    topic_name: str | None = Field(default=None, description="Topic guide name")
    headline: str | None = Field(default=None, description="Press release headline")
    one_liner: str | None = Field(default=None, description="One-line summary")
    faq_count: int = Field(default=0, description="Number of FAQ items")
    generated_at: datetime = Field(..., description="Generation timestamp")
    validation_status: str = Field(default="valid", description="Validation status")
    confidence_score: float | None = Field(default=None, description="Confidence score 0-1")


class PRFAQGenerateRequest(BaseModel):
    """Request model for generating PR-FAQ."""

    exec_id: str = Field(..., description="Execution ID to generate PR-FAQ from")
    model: str = Field(default="gpt-4.1-mini", description="LLM model to use")


class PRFAQGenerateResponse(BaseModel):
    """Response model for PR-FAQ generation."""

    exec_id: str = Field(..., description="Execution ID")
    status: str = Field(default="generated", description="Generation status")
    generated_at: datetime = Field(..., description="Generation timestamp")
    validation_status: str = Field(..., description="Validation status")
    confidence_score: float | None = Field(default=None, description="Confidence score")


if __name__ == "__main__":
    import sys

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Test 1: PRFAQSummary creation
    total_tests += 1
    try:
        summary = PRFAQSummary(
            exec_id="batch_test_20251219_120000",
            generated_at=datetime.now(),
        )
        if summary.exec_id != "batch_test_20251219_120000":
            all_validation_failures.append(f"Exec ID mismatch: {summary.exec_id}")
        if summary.validation_status != "valid":
            all_validation_failures.append(
                f"Default status should be valid: {summary.validation_status}"
            )
        if summary.faq_count != 0:
            all_validation_failures.append(f"Default faq_count should be 0: {summary.faq_count}")
    except Exception as e:
        all_validation_failures.append(f"PRFAQSummary creation failed: {e}")

    # Test 2: PRFAQSummary with all fields
    total_tests += 1
    try:
        summary = PRFAQSummary(
            exec_id="batch_test_20251219_120000",
            topic_name="compra-amazon",
            headline="Nova Experiência de Compra",
            one_liner="Revolucionando compras online",
            faq_count=5,
            generated_at=datetime.now(),
            validation_status="valid",
            confidence_score=0.95,
        )
        if summary.headline != "Nova Experiência de Compra":
            all_validation_failures.append(f"Headline mismatch: {summary.headline}")
        if summary.confidence_score != 0.95:
            all_validation_failures.append(
                f"Confidence score mismatch: {summary.confidence_score}"
            )
    except Exception as e:
        all_validation_failures.append(f"PRFAQSummary full test failed: {e}")

    # Test 3: PRFAQGenerateRequest defaults
    total_tests += 1
    try:
        req = PRFAQGenerateRequest(exec_id="batch_test_20251219_120000")
        if req.exec_id != "batch_test_20251219_120000":
            all_validation_failures.append(f"Exec ID mismatch: {req.exec_id}")
        if req.model != "gpt-4.1-mini":
            all_validation_failures.append(f"Default model should be gpt-4.1-mini: {req.model}")
    except Exception as e:
        all_validation_failures.append(f"PRFAQGenerateRequest test failed: {e}")

    # Test 4: PRFAQGenerateRequest custom model
    total_tests += 1
    try:
        req = PRFAQGenerateRequest(exec_id="batch_test", model="gpt-4")
        if req.model != "gpt-4":
            all_validation_failures.append(f"Custom model mismatch: {req.model}")
    except Exception as e:
        all_validation_failures.append(f"PRFAQGenerateRequest custom model test failed: {e}")

    # Test 5: PRFAQGenerateResponse
    total_tests += 1
    try:
        response = PRFAQGenerateResponse(
            exec_id="batch_test_20251219_120000",
            status="generated",
            generated_at=datetime.now(),
            validation_status="valid",
            confidence_score=0.88,
        )
        if response.status != "generated":
            all_validation_failures.append(f"Status mismatch: {response.status}")
        if response.confidence_score != 0.88:
            all_validation_failures.append(
                f"Confidence score mismatch: {response.confidence_score}"
            )
    except Exception as e:
        all_validation_failures.append(f"PRFAQGenerateResponse test failed: {e}")

    # Test 6: PRFAQGenerateResponse defaults
    total_tests += 1
    try:
        response = PRFAQGenerateResponse(
            exec_id="batch_test",
            generated_at=datetime.now(),
            validation_status="pending",
        )
        if response.status != "generated":
            all_validation_failures.append(f"Default status should be generated: {response.status}")
        if response.confidence_score is not None:
            all_validation_failures.append(
                f"Default confidence_score should be None: {response.confidence_score}"
            )
    except Exception as e:
        all_validation_failures.append(f"PRFAQGenerateResponse defaults test failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
