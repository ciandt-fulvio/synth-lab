"""
Contract tests for LLM response format.

Validates that the InterviewResponse format matches the contract defined in
contracts/interview-response.json schema.
"""

import sys
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from synth_lab.research.models import InterviewResponse


class TestInterviewResponseContract:
    """Contract tests for InterviewResponse against JSON schema."""

    @pytest.fixture
    def contract_schema(self):
        """Load the contract schema."""
        schema_path = Path(__file__).parents[4] / "specs" / "005-ux-research-interviews" / "contracts" / "interview-response.json"
        with open(schema_path) as f:
            return json.load(f)

    def test_response_has_required_fields(self):
        """Test that response has all required fields."""
        response = InterviewResponse(
            message="Test message",
            should_end=False
        )

        # Convert to dict to check structure
        data = response.model_dump()
        assert "message" in data
        assert "should_end" in data
        assert "internal_notes" in data

    def test_message_field_is_string(self):
        """Test that message field accepts strings."""
        response = InterviewResponse(message="Test", should_end=False)
        assert isinstance(response.message, str)

    def test_message_field_non_empty(self):
        """Test that message field must be non-empty."""
        with pytest.raises(ValidationError):
            InterviewResponse(message="", should_end=False)

    def test_should_end_field_is_boolean(self):
        """Test that should_end field is boolean."""
        response = InterviewResponse(message="Test", should_end=True)
        assert isinstance(response.should_end, bool)

    def test_should_end_defaults_to_false(self):
        """Test that should_end defaults to False."""
        response = InterviewResponse(message="Test")
        assert response.should_end is False

    def test_internal_notes_is_optional(self):
        """Test that internal_notes is optional."""
        # Without internal_notes
        response1 = InterviewResponse(message="Test", should_end=False)
        assert response1.internal_notes is None

        # With internal_notes
        response2 = InterviewResponse(
            message="Test",
            should_end=False,
            internal_notes="Notes"
        )
        assert response2.internal_notes == "Notes"

    def test_interviewer_response_example(self):
        """Test example interviewer response from contract."""
        response = InterviewResponse(
            message="Olá! Obrigado por participar desta pesquisa. Podemos começar falando um pouco sobre seus hábitos de compra online?",
            should_end=False,
            internal_notes="Começando com pergunta aberta para estabelecer rapport"
        )

        assert response.message.startswith("Olá!")
        assert response.should_end is False
        assert "rapport" in response.internal_notes

    def test_synth_response_example(self):
        """Test example synth response from contract."""
        response = InterviewResponse(
            message="Bom, eu costumo fazer compras pelo celular quando estou no ônibus voltando do trabalho. É mais prático assim.",
            should_end=False,
            internal_notes="Demonstrando preferência por mobile e compras durante transporte"
        )

        assert "celular" in response.message
        assert response.should_end is False

    def test_end_interview_response_example(self):
        """Test example end interview response from contract."""
        response = InterviewResponse(
            message="Muito obrigado pelas suas respostas! Foram insights muito valiosos para nossa pesquisa. Agradeço sua participação.",
            should_end=True,
            internal_notes="Objetivos da pesquisa atingidos. Encerrando com agradecimento."
        )

        assert response.should_end is True
        assert "obrigado" in response.message.lower()

    def test_response_serialization(self):
        """Test that response can be serialized to JSON."""
        response = InterviewResponse(
            message="Test message",
            should_end=False,
            internal_notes="Notes"
        )

        json_str = response.model_dump_json()
        data = json.loads(json_str)

        assert data["message"] == "Test message"
        assert data["should_end"] is False
        assert data["internal_notes"] == "Notes"

    def test_response_deserialization(self):
        """Test that response can be created from JSON."""
        json_data = {
            "message": "Test message",
            "should_end": True,
            "internal_notes": None
        }

        response = InterviewResponse(**json_data)
        assert response.message == "Test message"
        assert response.should_end is True


if __name__ == "__main__":
    """Validation with real test execution."""
    print("=== InterviewResponse Contract Test Validation ===\n")

    # Run pytest programmatically
    try:
        exit_code = pytest.main([__file__, "-v", "--tb=short"])

        if exit_code == 0:
            print("\n✅ VALIDATION PASSED - All contract tests are ready")
            print("InterviewResponse model implementation can proceed")
            sys.exit(0)
        else:
            print(f"\n❌ VALIDATION FAILED - Contract test setup has issues (exit code: {exit_code})")
            sys.exit(1)
    except Exception as e:
        print(f"❌ VALIDATION FAILED - Error running tests: {e}")
        sys.exit(1)
