"""
Region analysis entities for synth-lab.

Defines models for emergent groups identified in simulation analysis.

References:
    - Spec: specs/016-feature-impact-simulation/spec.md
    - Data model: specs/016-feature-impact-simulation/data-model.md
"""

import secrets
from typing import Literal

from pydantic import BaseModel, Field


def generate_region_id() -> str:
    """Generate a region analysis ID."""
    return f"region_{secrets.token_hex(4)}"


class RegionRule(BaseModel):
    """A rule that defines a region in the synth attribute space."""

    attribute: str = Field(
        description="Attribute name. Ex: 'capability_mean', 'digital_literacy'",
    )

    operator: Literal["<", "<=", ">", ">="] = Field(
        description="Comparison operator.",
    )

    threshold: float = Field(
        description="Threshold value for comparison.",
    )


class RegionAnalysis(BaseModel):
    """
    Emergent group identified in simulation analysis.

    Represents a region of the synth attribute space with
    distinctive outcome characteristics.
    """

    id: str = Field(
        default_factory=generate_region_id,
        description="Unique region identifier.",
    )

    simulation_id: str = Field(description="ID of the simulation this analysis belongs to.")

    # Rules defining the region
    rules: list[RegionRule] = Field(
        description="Rules that define this region. Ex: capability < 0.48 AND trust < 0.4",
    )

    # Human-readable rule text
    rule_text: str = Field(
        description="Human-readable rule text. Ex: 'capability_mean < 0.48 AND trust_mean < 0.4'",
    )

    # Metrics
    synth_count: int = Field(
        ge=0,
        description="Number of synths in this region.",
    )

    synth_percentage: float = Field(
        ge=0.0,
        le=100.0,
        description="Percentage of total population in this region.",
    )

    # Outcome rates for this region
    did_not_try_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Rate of did_not_try outcomes in this region.",
    )

    failed_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Rate of failed outcomes in this region.",
    )

    success_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Rate of success outcomes in this region.",
    )

    # Comparison with overall population
    failure_delta: float = Field(
        description="Difference between this region's failure rate and overall population.",
    )


def format_rules_as_text(rules: list[RegionRule]) -> str:
    """Format a list of rules as human-readable text."""
    if not rules:
        return ""
    rule_texts = [f"{r.attribute} {r.operator} {r.threshold:.2f}" for r in rules]
    return " AND ".join(rule_texts)


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Create valid RegionRule
    total_tests += 1
    try:
        rule = RegionRule(
            attribute="capability_mean",
            operator="<",
            threshold=0.48,
        )
        if rule.attribute != "capability_mean":
            all_validation_failures.append(f"attribute mismatch: {rule.attribute}")
    except Exception as e:
        all_validation_failures.append(f"RegionRule creation failed: {e}")

    # Test 2: Reject invalid operator
    total_tests += 1
    try:
        RegionRule(
            attribute="test",
            operator="==",  # Invalid
            threshold=0.5,
        )
        all_validation_failures.append("Should reject invalid operator")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for invalid operator: {e}")

    # Test 3: Create valid RegionAnalysis
    total_tests += 1
    try:
        analysis = RegionAnalysis(
            simulation_id="sim_abc12345",
            rules=[
                RegionRule(attribute="capability_mean", operator="<", threshold=0.48),
                RegionRule(attribute="trust_mean", operator="<", threshold=0.40),
            ],
            rule_text="capability_mean < 0.48 AND trust_mean < 0.40",
            synth_count=87,
            synth_percentage=17.4,
            did_not_try_rate=0.15,
            failed_rate=0.68,
            success_rate=0.17,
            failure_delta=0.30,
        )
        if analysis.synth_count != 87:
            all_validation_failures.append(f"synth_count mismatch: {analysis.synth_count}")
    except Exception as e:
        all_validation_failures.append(f"RegionAnalysis creation failed: {e}")

    # Test 4: ID generation
    total_tests += 1
    try:
        id1 = generate_region_id()
        id2 = generate_region_id()
        if not id1.startswith("region_"):
            all_validation_failures.append(f"ID should start with region_: {id1}")
        if id1 == id2:
            all_validation_failures.append("Generated IDs should be unique")
    except Exception as e:
        all_validation_failures.append(f"ID generation test failed: {e}")

    # Test 5: format_rules_as_text
    total_tests += 1
    try:
        rules = [
            RegionRule(attribute="capability_mean", operator="<", threshold=0.48),
            RegionRule(attribute="trust_mean", operator="<", threshold=0.40),
        ]
        text = format_rules_as_text(rules)
        if "capability_mean < 0.48" not in text:
            all_validation_failures.append(f"Rule text missing capability: {text}")
        if "AND" not in text:
            all_validation_failures.append(f"Rule text missing AND: {text}")
    except Exception as e:
        all_validation_failures.append(f"format_rules_as_text failed: {e}")

    # Test 6: Empty rules
    total_tests += 1
    try:
        text = format_rules_as_text([])
        if text != "":
            all_validation_failures.append(f"Empty rules should produce empty text: {text}")
    except Exception as e:
        all_validation_failures.append(f"Empty rules test failed: {e}")

    # Test 7: Reject invalid synth_percentage
    total_tests += 1
    try:
        RegionAnalysis(
            simulation_id="sim_abc12345",
            rules=[],
            rule_text="",
            synth_count=100,
            synth_percentage=150.0,  # Invalid
            did_not_try_rate=0.0,
            failed_rate=0.5,
            success_rate=0.5,
            failure_delta=0.0,
        )
        all_validation_failures.append("Should reject percentage > 100")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for invalid percentage: {e}")

    # Test 8: Model dump
    total_tests += 1
    try:
        analysis = RegionAnalysis(
            simulation_id="sim_abc12345",
            rules=[RegionRule(attribute="test", operator="<", threshold=0.5)],
            rule_text="test < 0.50",
            synth_count=50,
            synth_percentage=10.0,
            did_not_try_rate=0.2,
            failed_rate=0.5,
            success_rate=0.3,
            failure_delta=0.2,
        )
        dump = analysis.model_dump()
        if "rules" not in dump:
            all_validation_failures.append("model_dump missing rules")
        if len(dump["rules"]) != 1:
            all_validation_failures.append("model_dump rules count mismatch")
    except Exception as e:
        all_validation_failures.append(f"model_dump test failed: {e}")

    # Final validation result
    if all_validation_failures:
        failed = len(all_validation_failures)
        print(f"VALIDATION FAILED - {failed} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
