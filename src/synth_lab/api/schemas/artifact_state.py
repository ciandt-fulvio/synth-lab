"""
API schemas for artifact state management.

Pydantic models for the artifact states API endpoint responses.

References:
    - Spec: specs/013-summary-prfaq-states/spec.md
    - OpenAPI contract: specs/013-summary-prfaq-states/contracts/openapi.yaml
"""

from datetime import datetime

from pydantic import BaseModel, Field

from synth_lab.domain.entities.artifact_state import (
    ArtifactState as DomainArtifactState,
)
from synth_lab.domain.entities.artifact_state import (
    ArtifactStateEnum,
    ArtifactType,
)


class ArtifactState(BaseModel):
    """API response model for a single artifact state."""

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

    @classmethod
    def from_domain(cls, domain_state: DomainArtifactState) -> "ArtifactState":
        """Convert from domain model to API schema."""
        return cls(
            artifact_type=domain_state.artifact_type,
            state=domain_state.state,
            can_generate=domain_state.can_generate,
            can_view=domain_state.can_view,
            prerequisite_met=domain_state.prerequisite_met,
            prerequisite_message=domain_state.prerequisite_message,
            error_message=domain_state.error_message,
            started_at=domain_state.started_at,
            completed_at=domain_state.completed_at,
        )


class ArtifactStatesResponse(BaseModel):
    """API response model for GET /research/{exec_id}/artifacts."""

    exec_id: str = Field(description="Research execution ID")
    summary: ArtifactState = Field(description="Summary artifact state")
    prfaq: ArtifactState = Field(description="PR-FAQ artifact state")


if __name__ == "__main__":
    import sys

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Test 1: ArtifactState creation
    total_tests += 1
    try:
        state = ArtifactState(
            artifact_type=ArtifactType.SUMMARY,
            state=ArtifactStateEnum.AVAILABLE,
            can_view=True,
        )
        if state.artifact_type != ArtifactType.SUMMARY:
            all_validation_failures.append("artifact_type mismatch")
        if state.state != ArtifactStateEnum.AVAILABLE:
            all_validation_failures.append("state mismatch")
    except Exception as e:
        all_validation_failures.append(f"ArtifactState creation failed: {e}")

    # Test 2: ArtifactStatesResponse creation
    total_tests += 1
    try:
        response = ArtifactStatesResponse(
            exec_id="test_exec_123",
            summary=ArtifactState(
                artifact_type=ArtifactType.SUMMARY,
                state=ArtifactStateEnum.AVAILABLE,
                can_view=True,
            ),
            prfaq=ArtifactState(
                artifact_type=ArtifactType.PRFAQ,
                state=ArtifactStateEnum.UNAVAILABLE,
                can_generate=True,
                prerequisite_met=True,
            ),
        )
        if response.exec_id != "test_exec_123":
            all_validation_failures.append("exec_id mismatch")
        if response.summary.can_view is not True:
            all_validation_failures.append("summary.can_view mismatch")
        if response.prfaq.can_generate is not True:
            all_validation_failures.append("prfaq.can_generate mismatch")
    except Exception as e:
        all_validation_failures.append(f"ArtifactStatesResponse creation failed: {e}")

    # Test 3: from_domain conversion
    total_tests += 1
    try:
        from synth_lab.domain.entities.artifact_state import (
            compute_summary_state,
        )

        domain_state = compute_summary_state("completed", "# Summary")
        api_state = ArtifactState.from_domain(domain_state)
        if api_state.state != ArtifactStateEnum.AVAILABLE:
            all_validation_failures.append("from_domain conversion failed")
        if api_state.artifact_type != ArtifactType.SUMMARY:
            all_validation_failures.append("from_domain artifact_type mismatch")
    except Exception as e:
        all_validation_failures.append(f"from_domain test failed: {e}")

    # Test 4: JSON serialization
    total_tests += 1
    try:
        state = ArtifactState(
            artifact_type=ArtifactType.PRFAQ,
            state=ArtifactStateEnum.GENERATING,
            started_at=datetime(2025, 12, 21, 10, 0, 0),
        )
        json_data = state.model_dump_json()
        if "generating" not in json_data:
            all_validation_failures.append("JSON serialization missing state")
        if "prfaq" not in json_data:
            all_validation_failures.append("JSON serialization missing artifact_type")
    except Exception as e:
        all_validation_failures.append(f"JSON serialization failed: {e}")

    # Final validation result
    if all_validation_failures:
        failed = len(all_validation_failures)
        print(f"VALIDATION FAILED - {failed} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
