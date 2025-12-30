"""
Synth domain models for synth-lab.

Pydantic models for synthetic persona data following schema v1.

References:
    - Schema definition: data/schemas/synth-schema-v1.json
"""

from datetime import datetime

from pydantic import BaseModel, Field

# ============================================================================
# Demografia models
# ============================================================================


class Location(BaseModel):
    """Geographic location information (IBGE regions)."""

    pais: str | None = Field(default="Brasil", description="País (sempre Brasil)")
    regiao: str | None = Field(
        default=None, description="Região: Norte, Nordeste, Centro-Oeste, Sudeste, Sul"
    )
    estado: str | None = Field(default=None, description="UF (2 letras)")
    cidade: str | None = Field(default=None, description="Nome da cidade")


class FamilyComposition(BaseModel):
    """Family composition information."""

    tipo: str | None = Field(
        default=None,
        description="Tipo: unipessoal, casal sem filhos, casal com filhos, monoparental, multigeracional, outros",
    )
    numero_pessoas: int | None = Field(
        default=None, ge=1, le=15, description="Número de pessoas no domicílio"
    )


class Demographics(BaseModel):
    """Demographic data for a synth (IBGE Censo 2022, PNAD 2023)."""

    idade: int | None = Field(default=None, ge=0, le=120, description="Idade em anos completos")
    genero_biologico: str | None = Field(
        default=None, description="Gênero biológico: masculino, feminino, intersexo"
    )
    raca_etnia: str | None = Field(
        default=None, description="Raça/etnia IBGE: branco, pardo, preto, amarelo, indígena"
    )
    localizacao: Location | None = None
    escolaridade: str | None = Field(
        default=None,
        description="Nível: Sem instrução, Fundamental incompleto/completo, Médio incompleto/completo, Superior incompleto/completo, Pós-graduação",
    )
    renda_mensal: float | None = Field(
        default=None, ge=0, description="Renda mensal individual em BRL"
    )
    ocupacao: str | None = Field(default=None, description="Profissão/ocupação conforme CBO")
    estado_civil: str | None = Field(
        default=None, description="Estado civil: solteiro, casado, união estável, divorciado, viúvo"
    )
    composicao_familiar: FamilyComposition | None = None


# ============================================================================
# Psicografia models
# ============================================================================


class CognitiveContract(BaseModel):
    """Cognitive contract defining response patterns."""

    tipo: str | None = Field(
        default=None,
        description="Tipo: factual, narrador, desconfiado, racionalizador, impaciente, esforçado_confuso",
    )
    perfil_cognitivo: str | None = Field(default=None, description="Descrição do perfil cognitivo")
    regras: list[str] = Field(default_factory=list, description="Regras de comportamento")
    efeito_esperado: str | None = Field(default=None, description="Efeito esperado nas respostas")


class Psychographics(BaseModel):
    """Psychographic data for a synth."""

    interesses: list[str] = Field(
        default_factory=list, description="Áreas de interesse (1-4 itens)"
    )
    contrato_cognitivo: CognitiveContract | None = None


# ============================================================================
# Deficiências models
# ============================================================================


class VisualDisability(BaseModel):
    """Visual disability information (PNS 2019: 3.4%)."""

    tipo: str | None = Field(
        default=None, description="Tipo: nenhuma, leve, moderada, severa, cegueira"
    )


class HearingDisability(BaseModel):
    """Hearing disability information (PNS 2019: 1.1%)."""

    tipo: str | None = Field(
        default=None, description="Tipo: nenhuma, leve, moderada, severa, surdez"
    )


class MotorDisability(BaseModel):
    """Motor disability information (PNS 2019: 3.8%)."""

    tipo: str | None = Field(default=None, description="Tipo: nenhuma, leve, moderada, severa")


class CognitiveDisability(BaseModel):
    """Cognitive disability information (PNS 2019: 1.2%)."""

    tipo: str | None = Field(default=None, description="Tipo: nenhuma, leve, moderada, severa")


class Disabilities(BaseModel):
    """Disability information for a synth (IBGE PNS 2019)."""

    visual: VisualDisability | None = None
    auditiva: HearingDisability | None = None
    motora: MotorDisability | None = None
    cognitiva: CognitiveDisability | None = None


class SynthBase(BaseModel):
    """Base synth model with core fields."""

    id: str = Field(..., min_length=6, max_length=6, description="6-character unique ID")
    synth_group_id: str | None = Field(
        default=None, description="ID of the synth group this synth belongs to"
    )
    nome: str = Field(..., description="Display name")
    descricao: str | None = Field(default=None, description="Brief description")
    link_photo: str | None = Field(default=None, description="External photo URL")
    avatar_path: str | None = Field(default=None, description="Local avatar file path")
    created_at: datetime = Field(..., description="Creation timestamp")
    version: str = Field(default="2.3.0", description="Schema version")


class SynthSummary(SynthBase):
    """Summary synth model for list endpoints."""

    pass


class SimulationAttributesForDisplay(BaseModel):
    """Simulation attributes formatted for PM display."""

    observables_formatted: list[dict] = Field(
        default_factory=list,
        description="Array of observables with labels for PM display",
    )
    raw: dict | None = Field(
        default=None,
        description="Raw simulation attributes for backward compatibility",
    )


class SynthDetail(SynthBase):
    """Full synth model with all nested data following schema v2.3.0."""

    demografia: Demographics | None = None
    psicografia: Psychographics | None = None
    deficiencias: Disabilities | None = None
    observables: dict | None = Field(
        default=None,
        description="Observable attributes for simulation (v2.3.0+): digital_literacy, similar_tool_experience, motor_ability, time_availability, domain_expertise",
    )
    simulation_attributes: SimulationAttributesForDisplay | None = None


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
        if synth.version != "2.3.0":
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

    # Test 3: Demographics model with v1 fields
    total_tests += 1
    try:
        demo = Demographics(
            idade=30,
            genero_biologico="masculino",
            raca_etnia="pardo",
            localizacao=Location(cidade="São Paulo", estado="SP", regiao="Sudeste"),
            escolaridade="Superior completo",
            renda_mensal=5000.0,
            estado_civil="casado",
            composicao_familiar=FamilyComposition(tipo="casal com filhos", numero_pessoas=4),
        )
        if demo.idade != 30:
            all_validation_failures.append(f"Age mismatch: {demo.idade}")
        if demo.localizacao.regiao != "Sudeste":
            all_validation_failures.append(f"Region mismatch: {demo.localizacao.regiao}")
        if demo.genero_biologico != "masculino":
            all_validation_failures.append(f"Genero biologico mismatch: {demo.genero_biologico}")
        if demo.raca_etnia != "pardo":
            all_validation_failures.append(f"Raca/etnia mismatch: {demo.raca_etnia}")
    except Exception as e:
        all_validation_failures.append(f"Demographics test failed: {e}")

    # Test 4: Psychographics with cognitive contract
    total_tests += 1
    try:
        psico = Psychographics(
            interesses=["tecnologia", "esportes"],
            contrato_cognitivo=CognitiveContract(
                tipo="factual", perfil_cognitivo="Responde diretamente", regras=["Ser objetivo"]
            ),
        )
        if "tecnologia" not in psico.interesses:
            all_validation_failures.append("Missing interesse: tecnologia")
        if psico.contrato_cognitivo.tipo != "factual":
            all_validation_failures.append(
                f"Contrato tipo mismatch: {psico.contrato_cognitivo.tipo}"
            )
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
            psicografia=Psychographics(interesses=["música"]),
        )
        if synth.demografia.idade != 25:
            all_validation_failures.append(f"Nested age mismatch: {synth.demografia.idade}")
    except Exception as e:
        all_validation_failures.append(f"SynthDetail test failed: {e}")

    # Test 6: Disabilities structure
    total_tests += 1
    try:
        disabilities = Disabilities(
            visual=VisualDisability(tipo="nenhuma"),
            auditiva=HearingDisability(tipo="leve"),
            motora=MotorDisability(tipo="nenhuma"),
            cognitiva=CognitiveDisability(tipo="nenhuma"),
        )
        if disabilities.visual.tipo != "nenhuma":
            all_validation_failures.append(
                f"Visual disability mismatch: {disabilities.visual.tipo}"
            )
        if disabilities.auditiva.tipo != "leve":
            all_validation_failures.append(
                f"Hearing disability mismatch: {disabilities.auditiva.tipo}"
            )
    except Exception as e:
        all_validation_failures.append(f"Disabilities test failed: {e}")

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

    # Test 8: SynthDetail with observables (v2.3.0)
    total_tests += 1
    try:
        synth = SynthDetail(
            id="obs123",
            nome="Synth with Observables",
            created_at=datetime.now(),
            observables={
                "digital_literacy": 0.75,
                "similar_tool_experience": 0.5,
                "motor_ability": 1.0,
                "time_availability": 0.6,
                "domain_expertise": 0.5,
            },
        )
        if synth.observables is None:
            all_validation_failures.append("Observables should not be None")
        elif synth.observables.get("digital_literacy") != 0.75:
            all_validation_failures.append(
                f"Observables digital_literacy mismatch: {synth.observables.get('digital_literacy')}"
            )
        if synth.version != "2.3.0":
            all_validation_failures.append(f"Version should be 2.3.0: {synth.version}")
    except Exception as e:
        all_validation_failures.append(f"SynthDetail with observables test failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
