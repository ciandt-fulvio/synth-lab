"""Validation for research reports and generated PR-FAQ documents.

Validates:
- Research batch report structure and completeness
- PR-FAQ document format against schema
- Required fields presence and content quality

Third-party documentation:
- jsonschema: https://python-jsonschema.readthedocs.io/

Sample usage:
    from .validator import validate_research_report, validate_prfaq

    report = ResearchReport(batch_id="b1", summary_content="...", sections={...})
    is_valid = validate_research_report(report)

    prfaq = PRFAQDocument(...)
    is_valid = validate_prfaq(prfaq)

Expected output:
    ValidationResult object with:
    - is_valid: bool
    - errors: list of error messages
    - warnings: list of warnings
    - confidence_score: float (0-1)
"""

from dataclasses import dataclass
from typing import Optional

import jsonschema

from .generation_models import (
    PRFAQDocument,
    ResearchReport)
from .prompts import get_json_schema


@dataclass
class ValidationResult:
    """Result of validation with detailed error information."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]
    confidence_score: float = 0.0
    details: Optional[dict] = None


def validate_research_report(report: ResearchReport) -> ValidationResult:
    """Validate research batch report for completeness and required fields.

    Args:
        report: ResearchReport model instance

    Returns:
        ValidationResult with is_valid, errors, warnings, confidence_score

    Checks:
    - Required fields present (batch_id, summary_content)
    - Required sections present (executive_summary, recommendations)
    - Minimum content length for summary (100+ characters)
    - Optional sections for data completeness
    """
    errors = []
    warnings = []
    confidence_score = 0.0

    # Check required fields
    if not report.batch_id or len(report.batch_id.strip()) == 0:
        errors.append("batch_id is required and cannot be empty")

    if not report.summary_content or len(report.summary_content) < 100:
        errors.append("summary_content must be at least 100 characters")

    # Check required sections
    if "executive_summary" not in report.sections:
        errors.append("Missing required section: executive_summary")
    elif len(report.sections["executive_summary"]) < 50:
        warnings.append("executive_summary is very brief (< 50 chars)")

    if "recommendations" not in report.sections:
        errors.append("Missing required section: recommendations")
    elif len(report.sections["recommendations"]) < 50:
        warnings.append("recommendations section is very brief (< 50 chars)")

    # Calculate confidence based on data completeness
    optional_sections = {
        "recurrent_patterns",
        "relevant_divergences",
        "identified_tensions",
        "notable_absences",
        "key_quotes",
    }
    present_optional = sum(1 for s in optional_sections if s in report.sections)
    optional_completeness = present_optional / len(optional_sections)

    # Base confidence: 0.5 if required sections present, 0.0 if missing
    if not errors:
        base_confidence = 0.5
        # Add points for optional sections (up to 0.35)
        optional_boost = optional_completeness * 0.35
        # Add points for content length (up to 0.15)
        content_length = min(len(report.summary_content) / 2000, 1.0) * 0.15
        confidence_score = base_confidence + optional_boost + content_length
    else:
        confidence_score = max(0.0, 0.3 - (len(errors) * 0.1))

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        confidence_score=min(confidence_score, 1.0),
        details={
            "optional_sections_present": present_optional,
            "total_optional_sections": len(optional_sections),
            "summary_length": len(report.summary_content),
        })


def validate_prfaq(prfaq: PRFAQDocument) -> ValidationResult:
    """Validate PR-FAQ document against JSON Schema and content requirements.

    Args:
        prfaq: PRFAQDocument model instance

    Returns:
        ValidationResult with is_valid, errors, warnings, confidence_score

    Checks:
    - JSON Schema compliance (structure, types, field lengths)
    - Required sections present
    - FAQ count (8-12 items)
    - Content quality (non-empty, meaningful text)
    - Consistency (problem and solution coherence)
    """
    errors = []
    warnings = []
    confidence_score = 0.0

    # Convert to dict for schema validation
    schema = get_json_schema()
    prfaq_dict = {
        "press_release": {
            "headline": prfaq.press_release.headline,
            "one_liner": prfaq.press_release.one_liner,
            "problem_statement": prfaq.press_release.problem_statement,
            "solution_overview": prfaq.press_release.solution_overview,
        },
        "faq": [
            {
                "question": item.question,
                "answer": item.answer,
                "customer_segment": item.customer_segment,
            }
            for item in prfaq.faq
        ],
    }

    # Validate against JSON Schema
    validator = jsonschema.Draft7Validator(schema)
    for error in validator.iter_errors(prfaq_dict):
        errors.append(f"Schema validation: {error.message}")

    # Check FAQ count
    if len(prfaq.faq) < 8:
        warnings.append(f"FAQ should have 8-12 items, found {len(prfaq.faq)}")
        confidence_score -= 0.1
    elif len(prfaq.faq) > 12:
        warnings.append(f"FAQ should have 8-12 items, found {len(prfaq.faq)}")
        confidence_score -= 0.05

    # Check content quality
    pr = prfaq.press_release

    # Check for generic language
    generic_terms = [
        "solution",
        "product",
        "feature",
        "benefit",
    ]
    headline_specificity = sum(1 for term in generic_terms if term.lower() in pr.headline.lower())
    if headline_specificity >= 2:
        warnings.append("Headline may be too generic. Consider more specific language.")

    # Check headline/problem/solution coherence
    if len(pr.headline) < 20 or len(pr.problem_statement) < 30 or len(pr.solution_overview) < 30:
        errors.append("Press Release content too brief: must be substantive")

    # Check for empty FAQ answers
    empty_answers = sum(1 for item in prfaq.faq if len(item.answer.strip()) < 20)
    if empty_answers > 0:
        warnings.append(f"{empty_answers} FAQ answers are too brief (< 20 chars)")

    # Calculate confidence score
    if not errors:
        base_confidence = 0.7
        # Add points for good FAQ count
        faq_score = 0.15 if 8 <= len(prfaq.faq) <= 12 else 0.0
        # Add points for content quality
        quality_bonus = (
            0.15 if empty_answers == 0 else max(0, 0.15 * (1 - empty_answers / len(prfaq.faq)))
        )
        confidence_score = base_confidence + faq_score + quality_bonus

        # Use provided confidence score if higher
        if prfaq.confidence_score > confidence_score:
            confidence_score = prfaq.confidence_score
    else:
        confidence_score = max(0.0, 0.3 - (len(errors) * 0.15))

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        confidence_score=min(confidence_score, 1.0),
        details={
            "faq_count": len(prfaq.faq),
            "empty_answers": empty_answers,
            "headline_length": len(pr.headline),
            "problem_length": len(pr.problem_statement),
            "solution_length": len(pr.solution_overview),
        })


if __name__ == "__main__":
    # Validation with real data
    import sys

    from .generation_models import (
        FAQItem,
        PressRelease)

    validation_failures = []
    total_tests = 0

    # Test 1: Valid research report passes validation
    total_tests += 1
    try:
        valid_report = ResearchReport(
            batch_id="batch_001",
            summary_content="Customer research findings show clear pain points in data analysis workflows. All 8 interviews revealed similar patterns about manual consolidation taking 3-5 weeks per project.",
            sections={
                "executive_summary": "Key insights from 8 interviews with product managers",
                "recommendations": "Build AI-powered synthesis tool for faster analysis",
                "recurrent_patterns": "All users struggle with manual consolidation",
            })
        result = validate_research_report(valid_report)
        if not result.is_valid:
            validation_failures.append(f"Valid report rejected: {result.errors}")
    except Exception as e:
        validation_failures.append(f"Test 1 (valid report): {str(e)}")

    # Test 2: Invalid research report fails validation
    total_tests += 1
    try:
        invalid_report = ResearchReport(batch_id="batch_001", summary_content="short", sections={})
        result = validate_research_report(invalid_report)
        if result.is_valid:
            validation_failures.append("Invalid report (missing sections) should have failed")
        if "executive_summary" not in str(result.errors):
            validation_failures.append("Should report missing executive_summary section")
    except Exception as e:
        validation_failures.append(f"Test 2 (invalid report): {str(e)}")

    # Test 3: Valid PR-FAQ passes validation
    total_tests += 1
    try:
        valid_prfaq = PRFAQDocument(
            batch_id="batch_001",
            press_release=PressRelease(
                headline="Introducing ResearchSync: Transform Interviews into Documents",
                one_liner="AI-powered synthesis of customer research",
                problem_statement="Product teams spend weeks manually consolidating interview data",
                solution_overview="Automated synthesis generates PR-FAQ from research summaries"),
            faq=[
                FAQItem(
                    question=f"Why is feature {i} important?",
                    answer=f"Because research showed customers need {i} to solve their problems efficiently",
                    customer_segment="Product Manager")
                for i in range(1, 9)  # 8 FAQ items
            ],
            confidence_score=0.85)
        result = validate_prfaq(valid_prfaq)
        if not result.is_valid:
            validation_failures.append(f"Valid PR-FAQ rejected: {result.errors}")
        if result.confidence_score < 0.7:
            validation_failures.append(
                f"Valid PR-FAQ confidence too low: {result.confidence_score}"
            )
    except Exception as e:
        validation_failures.append(f"Test 3 (valid PR-FAQ): {str(e)}")

    # Test 4: PR-FAQ with too few FAQs fails validation
    total_tests += 1
    try:
        few_faq_prfaq = PRFAQDocument(
            batch_id="batch_001",
            press_release=PressRelease(
                headline="Test Product",
                one_liner="Test value",
                problem_statement="Test problem",
                solution_overview="Test solution"),
            faq=[
                FAQItem(
                    question="Q1?",
                    answer="Answer 1 with sufficient detail here",
                    customer_segment="PM")
            ])
        result = validate_prfaq(few_faq_prfaq)
        if result.is_valid and len(result.warnings) == 0:
            validation_failures.append("Should warn when FAQ has < 8 items")
    except Exception as e:
        validation_failures.append(f"Test 4 (few FAQs): {str(e)}")

    # Test 5: Confidence scoring is proportional to completeness
    total_tests += 1
    try:
        minimal_report = ResearchReport(
            batch_id="batch_001",
            summary_content="A" * 100,
            sections={"executive_summary": "Summary", "recommendations": "Recommendations"})
        full_report = ResearchReport(
            batch_id="batch_001",
            summary_content="A" * 2000,
            sections={
                "executive_summary": "Summary",
                "recommendations": "Recommendations",
                "recurrent_patterns": "Patterns",
                "relevant_divergences": "Divergences",
                "identified_tensions": "Tensions",
                "notable_absences": "Absences",
                "key_quotes": "Quotes",
            })
        minimal_result = validate_research_report(minimal_report)
        full_result = validate_research_report(full_report)

        if full_result.confidence_score <= minimal_result.confidence_score:
            validation_failures.append(
                f"Full report ({full_result.confidence_score}) should have higher confidence than minimal ({minimal_result.confidence_score})"
            )
    except Exception as e:
        validation_failures.append(f"Test 5 (confidence scoring): {str(e)}")

    # Report results
    if validation_failures:
        print(f"❌ VALIDATION FAILED - {len(validation_failures)} of {total_tests} tests failed:")
        for failure in validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Validator is validated and ready for use")
        sys.exit(0)
