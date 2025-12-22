"""
Artifact state entities for synth-lab.

Defines enums and models for tracking summary and PR-FAQ generation states.

References:
    - Spec: specs/013-summary-prfaq-states/spec.md
    - Data model: specs/013-summary-prfaq-states/data-model.md
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ArtifactStateEnum(str, Enum):
    """Current state of an artifact (summary or PR-FAQ)."""

    UNAVAILABLE = "unavailable"
    GENERATING = "generating"
    AVAILABLE = "available"
    FAILED = "failed"


class ArtifactType(str, Enum):
    """Type of artifact."""

    SUMMARY = "summary"
    PRFAQ = "prfaq"


class PRFAQStatus(str, Enum):
    """PR-FAQ generation status stored in database."""

    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class ArtifactState(BaseModel):
    """State information for a single artifact."""

    artifact_type: ArtifactType = Field(description="Type of artifact")
    state: ArtifactStateEnum = Field(description="Current state")
    can_generate: bool = Field(
        default=False, description="Whether generate action is available"
    )
    can_view: bool = Field(
        default=False, description="Whether view action is available"
    )
    prerequisite_met: bool = Field(
        default=True, description="Whether prerequisites are satisfied"
    )
    prerequisite_message: str | None = Field(
        default=None, description="Message if prerequisite not met"
    )
    error_message: str | None = Field(
        default=None, description="Last error message if failed"
    )
    started_at: datetime | None = Field(
        default=None, description="Generation start timestamp"
    )
    completed_at: datetime | None = Field(
        default=None, description="Generation completion timestamp"
    )


def compute_summary_state(
    execution_status: str,
    summary_content: str | None,
    has_transcripts: bool = False,
) -> ArtifactState:
    """
    Compute summary artifact state from execution data.

    Args:
        execution_status: Current execution status (from ExecutionStatus enum).
        summary_content: Summary markdown content (nullable).
        has_transcripts: Whether the execution has transcripts available.

    Returns:
        ArtifactState for summary.

    Examples:
        >>> state = compute_summary_state("generating_summary", None)
        >>> state.state
        <ArtifactStateEnum.GENERATING: 'generating'>

        >>> state = compute_summary_state("completed", "# Summary\\n...")
        >>> state.state
        <ArtifactStateEnum.AVAILABLE: 'available'>

        >>> state = compute_summary_state("completed", None, has_transcripts=True)
        >>> state.can_generate
        True
    """
    has_summary = summary_content is not None and len(summary_content) > 0

    if execution_status == "generating_summary":
        state = ArtifactStateEnum.GENERATING
    elif has_summary:
        state = ArtifactStateEnum.AVAILABLE
    elif execution_status == "failed":
        state = ArtifactStateEnum.FAILED
    else:
        state = ArtifactStateEnum.UNAVAILABLE

    # Can generate manually if execution is completed, has transcripts, but no summary
    can_generate = (
        state == ArtifactStateEnum.UNAVAILABLE
        and execution_status == "completed"
        and has_transcripts
    )

    # Prerequisite message for when summary is unavailable but can't be generated
    prerequisite_message = None
    if state == ArtifactStateEnum.UNAVAILABLE and not can_generate:
        if execution_status not in ("completed", "failed"):
            prerequisite_message = "Aguardando conclusao das entrevistas"
        elif not has_transcripts:
            prerequisite_message = "Nenhuma entrevista disponivel"

    return ArtifactState(
        artifact_type=ArtifactType.SUMMARY,
        state=state,
        can_generate=can_generate,
        can_view=state == ArtifactStateEnum.AVAILABLE,
        prerequisite_met=can_generate or state != ArtifactStateEnum.UNAVAILABLE,
        prerequisite_message=prerequisite_message,
    )


def compute_prfaq_state(
    summary_available: bool,
    prfaq_metadata: dict | None,
) -> ArtifactState:
    """
    Compute PR-FAQ artifact state from execution and prfaq data.

    Args:
        summary_available: Whether summary is available.
        prfaq_metadata: PR-FAQ metadata row as dict (nullable).
            Expected keys: status, error_message, started_at, generated_at

    Returns:
        ArtifactState for PR-FAQ.

    Examples:
        >>> state = compute_prfaq_state(False, None)
        >>> state.state
        <ArtifactStateEnum.UNAVAILABLE: 'unavailable'>
        >>> state.prerequisite_met
        False

        >>> state = compute_prfaq_state(True, {"status": "generating"})
        >>> state.state
        <ArtifactStateEnum.GENERATING: 'generating'>
    """
    if prfaq_metadata is None:
        # No PR-FAQ record exists
        return ArtifactState(
            artifact_type=ArtifactType.PRFAQ,
            state=ArtifactStateEnum.UNAVAILABLE,
            can_generate=summary_available,
            can_view=False,
            prerequisite_met=summary_available,
            prerequisite_message=(
                "Summary necessario para gerar PR-FAQ" if not summary_available else None
            ),
        )

    status = prfaq_metadata.get("status", "completed")
    error_message = prfaq_metadata.get("error_message")
    started_at_str = prfaq_metadata.get("started_at")
    generated_at_str = prfaq_metadata.get("generated_at")

    # Parse timestamps
    started_at = None
    if started_at_str:
        try:
            started_at = datetime.fromisoformat(started_at_str)
        except (ValueError, TypeError):
            pass

    completed_at = None
    if generated_at_str:
        try:
            completed_at = datetime.fromisoformat(generated_at_str)
        except (ValueError, TypeError):
            pass

    if status == PRFAQStatus.GENERATING.value:
        state = ArtifactStateEnum.GENERATING
    elif status == PRFAQStatus.FAILED.value:
        state = ArtifactStateEnum.FAILED
    else:
        state = ArtifactStateEnum.AVAILABLE

    return ArtifactState(
        artifact_type=ArtifactType.PRFAQ,
        state=state,
        can_generate=state in (ArtifactStateEnum.UNAVAILABLE, ArtifactStateEnum.FAILED)
        and summary_available,
        can_view=state == ArtifactStateEnum.AVAILABLE,
        prerequisite_met=summary_available,
        prerequisite_message=(
            "Summary necessario para gerar PR-FAQ" if not summary_available else None
        ),
        error_message=error_message,
        started_at=started_at,
        completed_at=completed_at,
    )


if __name__ == "__main__":
    import sys

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Test 1: ArtifactStateEnum values
    total_tests += 1
    try:
        if ArtifactStateEnum.UNAVAILABLE.value != "unavailable":
            all_validation_failures.append(
                f"UNAVAILABLE value mismatch: {ArtifactStateEnum.UNAVAILABLE.value}"
            )
        if ArtifactStateEnum("generating") != ArtifactStateEnum.GENERATING:
            all_validation_failures.append("Enum from string failed")
    except Exception as e:
        all_validation_failures.append(f"ArtifactStateEnum test failed: {e}")

    # Test 2: PRFAQStatus values
    total_tests += 1
    try:
        if PRFAQStatus.GENERATING.value != "generating":
            all_validation_failures.append("GENERATING value mismatch")
        if PRFAQStatus.COMPLETED.value != "completed":
            all_validation_failures.append("COMPLETED value mismatch")
        if PRFAQStatus.FAILED.value != "failed":
            all_validation_failures.append("FAILED value mismatch")
    except Exception as e:
        all_validation_failures.append(f"PRFAQStatus test failed: {e}")

    # Test 3: ArtifactType values
    total_tests += 1
    try:
        if ArtifactType.SUMMARY.value != "summary":
            all_validation_failures.append("SUMMARY value mismatch")
        if ArtifactType.PRFAQ.value != "prfaq":
            all_validation_failures.append("PRFAQ value mismatch")
    except Exception as e:
        all_validation_failures.append(f"ArtifactType test failed: {e}")

    # Test 4: ArtifactState creation
    total_tests += 1
    try:
        state = ArtifactState(
            artifact_type=ArtifactType.SUMMARY,
            state=ArtifactStateEnum.AVAILABLE,
            can_view=True,
        )
        if state.can_generate is not False:
            all_validation_failures.append("Default can_generate should be False")
        if state.prerequisite_met is not True:
            all_validation_failures.append("Default prerequisite_met should be True")
    except Exception as e:
        all_validation_failures.append(f"ArtifactState creation failed: {e}")

    # Test 5: compute_summary_state - generating
    total_tests += 1
    try:
        state = compute_summary_state("generating_summary", None)
        if state.state != ArtifactStateEnum.GENERATING:
            all_validation_failures.append(
                f"Expected GENERATING, got {state.state}"
            )
        if state.can_view is not False:
            all_validation_failures.append("Generating state should not be viewable")
    except Exception as e:
        all_validation_failures.append(f"compute_summary_state generating failed: {e}")

    # Test 6: compute_summary_state - available
    total_tests += 1
    try:
        state = compute_summary_state("completed", "# Summary\nContent here")
        if state.state != ArtifactStateEnum.AVAILABLE:
            all_validation_failures.append(f"Expected AVAILABLE, got {state.state}")
        if state.can_view is not True:
            all_validation_failures.append("Available state should be viewable")
    except Exception as e:
        all_validation_failures.append(f"compute_summary_state available failed: {e}")

    # Test 7: compute_summary_state - failed
    total_tests += 1
    try:
        state = compute_summary_state("failed", None)
        if state.state != ArtifactStateEnum.FAILED:
            all_validation_failures.append(f"Expected FAILED, got {state.state}")
    except Exception as e:
        all_validation_failures.append(f"compute_summary_state failed state test: {e}")

    # Test 7b: compute_summary_state - completed with transcripts but no summary (can generate)
    total_tests += 1
    try:
        state = compute_summary_state("completed", None, has_transcripts=True)
        if state.state != ArtifactStateEnum.UNAVAILABLE:
            all_validation_failures.append(f"Expected UNAVAILABLE, got {state.state}")
        if state.can_generate is not True:
            all_validation_failures.append("Should be able to generate with transcripts")
        if state.prerequisite_met is not True:
            all_validation_failures.append("Prerequisite should be met when can_generate")
    except Exception as e:
        all_validation_failures.append(f"compute_summary_state can_generate test: {e}")

    # Test 7c: compute_summary_state - completed without transcripts (cannot generate)
    total_tests += 1
    try:
        state = compute_summary_state("completed", None, has_transcripts=False)
        if state.state != ArtifactStateEnum.UNAVAILABLE:
            all_validation_failures.append(f"Expected UNAVAILABLE, got {state.state}")
        if state.can_generate is not False:
            all_validation_failures.append("Should not be able to generate without transcripts")
        if state.prerequisite_message != "Nenhuma entrevista disponivel":
            all_validation_failures.append(f"Wrong prerequisite message: {state.prerequisite_message}")
    except Exception as e:
        all_validation_failures.append(f"compute_summary_state no_transcripts test: {e}")

    # Test 7d: compute_summary_state - running (cannot generate yet)
    total_tests += 1
    try:
        state = compute_summary_state("running", None, has_transcripts=True)
        if state.state != ArtifactStateEnum.UNAVAILABLE:
            all_validation_failures.append(f"Expected UNAVAILABLE, got {state.state}")
        if state.can_generate is not False:
            all_validation_failures.append("Should not be able to generate while running")
        if state.prerequisite_message != "Aguardando conclusao das entrevistas":
            all_validation_failures.append(f"Wrong prerequisite message: {state.prerequisite_message}")
    except Exception as e:
        all_validation_failures.append(f"compute_summary_state running test: {e}")

    # Test 8: compute_prfaq_state - no metadata, no summary
    total_tests += 1
    try:
        state = compute_prfaq_state(False, None)
        if state.state != ArtifactStateEnum.UNAVAILABLE:
            all_validation_failures.append(f"Expected UNAVAILABLE, got {state.state}")
        if state.prerequisite_met is not False:
            all_validation_failures.append("Prerequisite should not be met")
        if state.can_generate is not False:
            all_validation_failures.append("Should not be able to generate without summary")
    except Exception as e:
        all_validation_failures.append(f"compute_prfaq_state no prereq failed: {e}")

    # Test 9: compute_prfaq_state - no metadata, has summary
    total_tests += 1
    try:
        state = compute_prfaq_state(True, None)
        if state.state != ArtifactStateEnum.UNAVAILABLE:
            all_validation_failures.append(f"Expected UNAVAILABLE, got {state.state}")
        if state.prerequisite_met is not True:
            all_validation_failures.append("Prerequisite should be met")
        if state.can_generate is not True:
            all_validation_failures.append("Should be able to generate with summary")
    except Exception as e:
        all_validation_failures.append(f"compute_prfaq_state with prereq failed: {e}")

    # Test 10: compute_prfaq_state - generating
    total_tests += 1
    try:
        state = compute_prfaq_state(True, {"status": "generating"})
        if state.state != ArtifactStateEnum.GENERATING:
            all_validation_failures.append(f"Expected GENERATING, got {state.state}")
        if state.can_generate is not False:
            all_validation_failures.append("Should not be able to generate while generating")
    except Exception as e:
        all_validation_failures.append(f"compute_prfaq_state generating failed: {e}")

    # Test 11: compute_prfaq_state - completed
    total_tests += 1
    try:
        prfaq_meta = {"status": "completed", "generated_at": "2025-12-21T10:00:00"}
        state = compute_prfaq_state(True, prfaq_meta)
        if state.state != ArtifactStateEnum.AVAILABLE:
            all_validation_failures.append(f"Expected AVAILABLE, got {state.state}")
        if state.can_view is not True:
            all_validation_failures.append("Completed state should be viewable")
        if state.completed_at is None:
            all_validation_failures.append("completed_at should be set")
    except Exception as e:
        all_validation_failures.append(f"compute_prfaq_state completed failed: {e}")

    # Test 12: compute_prfaq_state - failed with error
    total_tests += 1
    try:
        state = compute_prfaq_state(True, {"status": "failed", "error_message": "API error"})
        if state.state != ArtifactStateEnum.FAILED:
            all_validation_failures.append(f"Expected FAILED, got {state.state}")
        if state.error_message != "API error":
            all_validation_failures.append(f"Error message mismatch: {state.error_message}")
        if state.can_generate is not True:
            all_validation_failures.append("Failed state should allow retry")
    except Exception as e:
        all_validation_failures.append(f"compute_prfaq_state failed state: {e}")

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
