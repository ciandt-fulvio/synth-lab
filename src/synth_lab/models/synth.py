"""
Synth domain models for synth-lab.

Pydantic models for synthetic persona data.

References:
    - Schema definition: specs/010-rest-api/data-model.md
"""

from datetime import datetime

from pydantic import BaseModel, Field


class Location(BaseModel):
    """Geographic location information."""

    cidade: str | None = None
    estado: str | None = None
    regiao: str | None = None


class Demographics(BaseModel):
    """Demographic data for a synth."""

    idade: int | None = None
    genero: str | None = None
    localizacao: Location | None = None
    educacao: str | None = None
    ocupacao: str | None = None
    renda_familiar: str | None = None


class Psychographics(BaseModel):
    """Psychographic data for a synth."""

    valores: list[str] = Field(default_factory=list)
    interesses: list[str] = Field(default_factory=list)
    estilo_vida: str | None = None
    personalidade: str | None = None


class Disabilities(BaseModel):
    """Disability information for a synth."""

    tipo: str | None = None
    descricao: str | None = None
    nivel: str | None = None


class DeviceInfo(BaseModel):
    """Device information."""

    principal: str | None = None
    qualidade: str | None = None


class AccessibilityPrefs(BaseModel):
    """Accessibility preferences."""

    zoom_fonte: int | None = None
    alto_contraste: bool | None = None


class PlatformFamiliarity(BaseModel):
    """Platform familiarity scores."""

    e_commerce: int | None = None
    banco_digital: int | None = None
    redes_sociais: int | None = None


class TechCapabilities(BaseModel):
    """Technology capabilities for a synth."""

    # Legacy fields (from data-model.md spec)
    nivel_geral: str | None = None
    apps_frequentes: list[str] = Field(default_factory=list)
    comportamento_digital: str | None = None

    # Actual fields from existing data
    alfabetizacao_digital: int | None = None
    dispositivos: DeviceInfo | dict | list[str] | None = None
    preferencias_acessibilidade: AccessibilityPrefs | dict | None = None
    velocidade_digitacao: int | None = None
    frequencia_internet: str | None = None
    familiaridade_plataformas: PlatformFamiliarity | dict | None = None


class SynthBase(BaseModel):
    """Base synth model with core fields."""

    id: str = Field(..., min_length=6, max_length=6, description="6-character unique ID")
    nome: str = Field(..., description="Display name")
    arquetipo: str | None = Field(default=None, description="Archetype classification")
    descricao: str | None = Field(default=None, description="Brief description")
    link_photo: str | None = Field(default=None, description="External photo URL")
    avatar_path: str | None = Field(default=None, description="Local avatar file path")
    created_at: datetime = Field(..., description="Creation timestamp")
    version: str = Field(default="2.0.0", description="Schema version")


class SynthSummary(SynthBase):
    """Summary synth model for list endpoints."""

    pass


class SynthDetail(SynthBase):
    """Full synth model with all nested data."""

    demografia: Demographics | None = None
    psicografia: Psychographics | None = None
    deficiencias: Disabilities | None = None
    capacidades_tecnologicas: TechCapabilities | None = None


class SynthSearchRequest(BaseModel):
    """Request model for synth search."""

    where_clause: str | None = Field(
        default=None,
        description="SQL WHERE clause for filtering (e.g., 'idade > 30')",
    )
    query: str | None = Field(
        default=None,
        description="Full SQL SELECT query (limited to SELECT only)",
    )


class SynthFieldInfo(BaseModel):
    """Information about a synth field."""

    name: str
    type: str
    description: str | None = None
    nested_fields: list[str] | None = None


if __name__ == "__main__":
    import sys

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Test 1: SynthBase creation
    total_tests += 1
    try:
        synth = SynthBase(
            id="abc123",
            nome="Test Synth",
            created_at=datetime.now(),
        )
        if synth.id != "abc123":
            all_validation_failures.append(f"ID mismatch: {synth.id}")
        if synth.version != "2.0.0":
            all_validation_failures.append(f"Version mismatch: {synth.version}")
    except Exception as e:
        all_validation_failures.append(f"SynthBase creation failed: {e}")

    # Test 2: ID validation (min/max length)
    total_tests += 1
    try:
        from pydantic import ValidationError

        try:
            SynthBase(id="abc", nome="Test", created_at=datetime.now())
            all_validation_failures.append("Should reject ID with length < 6")
        except ValidationError:
            pass  # Expected

        try:
            SynthBase(id="abc1234", nome="Test", created_at=datetime.now())
            all_validation_failures.append("Should reject ID with length > 6")
        except ValidationError:
            pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"ID validation failed: {e}")

    # Test 3: Demographics model
    total_tests += 1
    try:
        demo = Demographics(
            idade=30,
            genero="Masculino",
            localizacao=Location(cidade="São Paulo", estado="SP", regiao="Sudeste"),
            educacao="Superior Completo",
        )
        if demo.idade != 30:
            all_validation_failures.append(f"Age mismatch: {demo.idade}")
        if demo.localizacao.regiao != "Sudeste":
            all_validation_failures.append(f"Region mismatch: {demo.localizacao.regiao}")
    except Exception as e:
        all_validation_failures.append(f"Demographics test failed: {e}")

    # Test 4: Psychographics with lists
    total_tests += 1
    try:
        psico = Psychographics(
            valores=["família", "trabalho"],
            interesses=["tecnologia", "esportes"],
            estilo_vida="Urbano",
        )
        if len(psico.valores) != 2:
            all_validation_failures.append(f"Valores length mismatch: {len(psico.valores)}")
        if "tecnologia" not in psico.interesses:
            all_validation_failures.append("Missing interesse: tecnologia")
    except Exception as e:
        all_validation_failures.append(f"Psychographics test failed: {e}")

    # Test 5: SynthDetail with nested objects
    total_tests += 1
    try:
        synth = SynthDetail(
            id="xyz789",
            nome="Full Synth",
            created_at=datetime.now(),
            demografia=Demographics(idade=25),
            psicografia=Psychographics(valores=["saúde"]),
        )
        if synth.demografia.idade != 25:
            all_validation_failures.append(f"Nested age mismatch: {synth.demografia.idade}")
    except Exception as e:
        all_validation_failures.append(f"SynthDetail test failed: {e}")

    # Test 6: TechCapabilities defaults
    total_tests += 1
    try:
        tech = TechCapabilities()
        if tech.dispositivos != []:
            all_validation_failures.append(f"Default dispositivos should be empty: {tech.dispositivos}")
        if tech.apps_frequentes != []:
            all_validation_failures.append(f"Default apps should be empty: {tech.apps_frequentes}")
    except Exception as e:
        all_validation_failures.append(f"TechCapabilities test failed: {e}")

    # Test 7: SynthSearchRequest
    total_tests += 1
    try:
        search = SynthSearchRequest(where_clause="idade > 30")
        if search.where_clause != "idade > 30":
            all_validation_failures.append(f"Where clause mismatch: {search.where_clause}")
        if search.query is not None:
            all_validation_failures.append(f"Query should be None: {search.query}")
    except Exception as e:
        all_validation_failures.append(f"SynthSearchRequest test failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
