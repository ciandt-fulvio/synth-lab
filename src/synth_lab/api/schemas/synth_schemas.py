"""
Synth API schemas for synth-lab.

Response schemas for synth endpoints including formatted simulation
attributes with observables and labels.

References:
    - Spec: specs/022-observable-latent-traits/spec.md (FR-013, FR-014)
    - Contract: specs/022-observable-latent-traits/contracts/synth-api.yaml
"""

from pydantic import BaseModel, Field

from synth_lab.domain.entities.simulation_attributes import (
    SimulationAttributes,
    SimulationLatentTraits,
    SimulationObservables)


class ObservableWithLabelResponse(BaseModel):
    """
    Observable attribute with formatted label for API response.

    Used in GET /synths/{id} response for PM-friendly display.
    """

    key: str = Field(..., description="Observable field key (e.g., 'digital_literacy')")
    name: str = Field(..., description="Human-readable name in Portuguese")
    value: float = Field(..., ge=0.0, le=1.0, description="Observable value [0, 1]")
    label: str = Field(
        ...,
        description="Textual label: Muito Baixo, Baixo, Médio, Alto, Muito Alto")
    description: str = Field(..., description="Brief description of what this observable means")

    model_config = {
        "json_schema_extra": {
            "example": {
                "key": "digital_literacy",
                "name": "Literacia Digital",
                "value": 0.42,
                "label": "Médio",
                "description": "Familiaridade com tecnologia e interfaces digitais",
            }
        }
    }


class SimulationObservablesResponse(BaseModel):
    """
    Raw simulation observables for API response.

    Used for backward compatibility and internal use.
    """

    digital_literacy: float = Field(..., ge=0.0, le=1.0)
    similar_tool_experience: float = Field(..., ge=0.0, le=1.0)
    motor_ability: float = Field(..., ge=0.0, le=1.0)
    time_availability: float = Field(..., ge=0.0, le=1.0)
    domain_expertise: float = Field(..., ge=0.0, le=1.0)

    @classmethod
    def from_entity(cls, obs: SimulationObservables) -> "SimulationObservablesResponse":
        """Create response from entity."""
        return cls(
            digital_literacy=obs.digital_literacy,
            similar_tool_experience=obs.similar_tool_experience,
            motor_ability=obs.motor_ability,
            time_availability=obs.time_availability,
            domain_expertise=obs.domain_expertise)


class SimulationLatentTraitsResponse(BaseModel):
    """
    Simulation latent traits for API response.

    Internal use only - not exposed to PM in frontend.
    """

    capability_mean: float = Field(..., ge=0.0, le=1.0)
    trust_mean: float = Field(..., ge=0.0, le=1.0)
    friction_tolerance_mean: float = Field(..., ge=0.0, le=1.0)
    exploration_prob: float = Field(..., ge=0.0, le=1.0)

    @classmethod
    def from_entity(cls, traits: SimulationLatentTraits) -> "SimulationLatentTraitsResponse":
        """Create response from entity."""
        return cls(
            capability_mean=traits.capability_mean,
            trust_mean=traits.trust_mean,
            friction_tolerance_mean=traits.friction_tolerance_mean,
            exploration_prob=traits.exploration_prob)


class SimulationAttributesRaw(BaseModel):
    """
    Raw simulation attributes (observables + latent traits).

    For backward compatibility.
    """

    observables: SimulationObservablesResponse
    latent_traits: SimulationLatentTraitsResponse

    @classmethod
    def from_entity(cls, attrs: SimulationAttributes) -> "SimulationAttributesRaw":
        """Create response from entity."""
        return cls(
            observables=SimulationObservablesResponse.from_entity(attrs.observables),
            latent_traits=SimulationLatentTraitsResponse.from_entity(attrs.latent_traits))


class SimulationAttributesFormatted(BaseModel):
    """
    Formatted simulation attributes for PM display.

    Contains observables with labels for PM-friendly display and
    raw values for backward compatibility.

    Frontend should use `observables_formatted` for display,
    and NEVER show `raw.latent_traits` to PM.
    """

    observables_formatted: list[ObservableWithLabelResponse] = Field(
        ...,
        description="Array of observables with labels for PM display")
    raw: SimulationAttributesRaw = Field(
        ...,
        description="Raw values for backward compatibility")


if __name__ == "__main__":
    import sys

    all_validation_failures: list[str] = []
    total_tests = 0

    # Test 1: ObservableWithLabelResponse creation
    total_tests += 1
    try:
        obs_label = ObservableWithLabelResponse(
            key="digital_literacy",
            name="Literacia Digital",
            value=0.42,
            label="Médio",
            description="Familiaridade com tecnologia")
        if obs_label.key != "digital_literacy":
            all_validation_failures.append(f"key mismatch: {obs_label.key}")
    except Exception as e:
        all_validation_failures.append(f"ObservableWithLabelResponse creation failed: {e}")

    # Test 2: SimulationObservablesResponse from entity
    total_tests += 1
    try:
        entity = SimulationObservables(
            digital_literacy=0.35,
            similar_tool_experience=0.42,
            motor_ability=0.85,
            time_availability=0.28,
            domain_expertise=0.55)
        response = SimulationObservablesResponse.from_entity(entity)
        if response.digital_literacy != 0.35:
            all_validation_failures.append(
                f"digital_literacy mismatch: {response.digital_literacy}"
            )
    except Exception as e:
        all_validation_failures.append(f"SimulationObservablesResponse.from_entity failed: {e}")

    # Test 3: SimulationLatentTraitsResponse from entity
    total_tests += 1
    try:
        entity = SimulationLatentTraits(
            capability_mean=0.42,
            trust_mean=0.39,
            friction_tolerance_mean=0.35,
            exploration_prob=0.38)
        response = SimulationLatentTraitsResponse.from_entity(entity)
        if response.capability_mean != 0.42:
            all_validation_failures.append(f"capability_mean mismatch: {response.capability_mean}")
    except Exception as e:
        all_validation_failures.append(f"SimulationLatentTraitsResponse.from_entity failed: {e}")

    # Test 4: SimulationAttributesRaw from entity
    total_tests += 1
    try:
        entity = SimulationAttributes(
            observables=SimulationObservables(
                digital_literacy=0.35,
                similar_tool_experience=0.42,
                motor_ability=0.85,
                time_availability=0.28,
                domain_expertise=0.55),
            latent_traits=SimulationLatentTraits(
                capability_mean=0.42,
                trust_mean=0.39,
                friction_tolerance_mean=0.35,
                exploration_prob=0.38))
        response = SimulationAttributesRaw.from_entity(entity)
        if response.observables.digital_literacy != 0.35:
            all_validation_failures.append("SimulationAttributesRaw conversion failed")
    except Exception as e:
        all_validation_failures.append(f"SimulationAttributesRaw.from_entity failed: {e}")

    # Test 5: SimulationAttributesFormatted creation
    total_tests += 1
    try:
        formatted = SimulationAttributesFormatted(
            observables_formatted=[
                ObservableWithLabelResponse(
                    key="digital_literacy",
                    name="Literacia Digital",
                    value=0.35,
                    label="Baixo",
                    description="Familiaridade com tecnologia"),
            ],
            raw=SimulationAttributesRaw(
                observables=SimulationObservablesResponse(
                    digital_literacy=0.35,
                    similar_tool_experience=0.42,
                    motor_ability=0.85,
                    time_availability=0.28,
                    domain_expertise=0.55),
                latent_traits=SimulationLatentTraitsResponse(
                    capability_mean=0.42,
                    trust_mean=0.39,
                    friction_tolerance_mean=0.35,
                    exploration_prob=0.38)))
        if len(formatted.observables_formatted) != 1:
            all_validation_failures.append(
                f"observables_formatted length wrong: {len(formatted.observables_formatted)}"
            )
    except Exception as e:
        all_validation_failures.append(f"SimulationAttributesFormatted creation failed: {e}")

    # Test 6: Value range validation
    total_tests += 1
    try:
        from pydantic import ValidationError

        try:
            ObservableWithLabelResponse(
                key="test",
                name="Test",
                value=1.5,  # Invalid - > 1.0
                label="Alto",
                description="Test")
            all_validation_failures.append("Should reject value > 1.0")
        except ValidationError:
            pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Value range validation failed: {e}")

    # Final validation result
    if all_validation_failures:
        failed = len(all_validation_failures)
        print(f"VALIDATION FAILED - {failed} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Synth schemas ready for use")
        sys.exit(0)
