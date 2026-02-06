"""
NarrativeService for generating mechanism-based narratives via LLM.

Analyzes feature descriptions and generates narrative text with mechanism
placeholders that can be configured via inline dropdowns.

References:
    - Spec: specs/039-narrative-mechanism-config/spec.md
    - Research: specs/039-narrative-mechanism-config/research.md (RQ-001, RQ-002)
    - Architecture: docs/architecture.md (LLM in services with tracing)

Sample usage:
    from synth_lab.services.narrative_service import NarrativeService

    service = NarrativeService()
    response = service.generate_narrative(
        name="Pix via WhatsApp",
        hypothesis="Usuários preferem pagar pelo app de mensagens",
        description="Permite enviar dinheiro para contatos do WhatsApp"
    )

Expected output:
    NarrativeResponse with narrative_template, selected_mechanisms, inferred_types
"""

from loguru import logger
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from synth_lab.domain.entities.narrative_response import (
    NarrativeResponse,
    SelectedMechanism,
)
from synth_lab.infrastructure.llm_client import LLMClient, get_llm_client
from synth_lab.infrastructure.phoenix_tracing import get_tracer
from synth_lab.repositories.mechanism_repository import MechanismRepository

# Phoenix/OpenTelemetry tracer for observability
_tracer = get_tracer("narrative-service")

# Model for narrative generation (gpt-4o-mini per RQ-002)
NARRATIVE_MODEL = "gpt-4o-mini"


class NarrativeGenerationError(Exception):
    """Raised when narrative generation fails."""

    pass


# ============================================================================
# LLM Response Schema for Structured Outputs
# ============================================================================


class LLMSelectedMechanism(BaseModel):
    """LLM output for a selected mechanism."""

    key: str = Field(..., description="Mechanism key")
    default_option_label: str = Field(
        ..., description="Label of the default option chosen"
    )


class LLMNarrativeResponse(BaseModel):
    """LLM output schema for narrative generation.

    This is the raw response from the LLM, which we then map to
    NarrativeResponse by resolving option labels to IDs.
    """

    inferred_types: list[str] = Field(
        ..., description="Feature types inferred (e.g., ['financial', 'social'])"
    )
    narrative_template: str = Field(
        ..., description="Narrative text with {mechanism_key} placeholders"
    )
    selected_mechanisms: list[LLMSelectedMechanism] = Field(
        ..., description="Mechanisms selected with default option labels"
    )
    excluded_mechanisms: list[str] = Field(
        ..., description="Mechanism keys not relevant for this feature"
    )


# ============================================================================
# NarrativeService
# ============================================================================


class NarrativeService:
    """LLM-powered narrative generation service."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        session: Session | None = None,
    ) -> None:
        """
        Initialize service.

        Args:
            llm_client: LLM client instance. If None, uses global client.
            session: SQLAlchemy session for repository. If None, creates new one.
        """
        self.llm = llm_client or get_llm_client()
        self.mechanism_repo = MechanismRepository(session=session)
        self.logger = logger.bind(component="narrative_service")

    def generate_narrative(
        self,
        name: str,
        hypothesis: str,
        description: str | None = None,
    ) -> NarrativeResponse:
        """
        Generate narrative with mechanism placeholders.

        Loads mechanisms and feature types from the database, calls LLM to
        generate narrative, and maps selected options to their UUIDs.

        Args:
            name: Feature name
            hypothesis: Hypothesis to test
            description: Additional context (optional)

        Returns:
            NarrativeResponse with template, selected mechanisms, and inferred types

        Raises:
            NarrativeGenerationError: If LLM call fails or returns invalid data
        """
        span_name = f"NarrativeGeneration | {name[:30]}"
        with _tracer.start_as_current_span(
            span_name,
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                "feature.name": name,
                "operation.type": "narrative_generation",
                "has_description": description is not None,
            },
        ):
            # Load mechanisms and feature types from database
            mechanisms = self.mechanism_repo.list_all_with_options()
            feature_types = self.mechanism_repo.list_feature_types()

            self.logger.info(
                f"Generating narrative for: {name} with {len(mechanisms)} mechanisms"
            )

            # Build prompt with database data
            prompt = self._build_prompt(
                name=name,
                hypothesis=hypothesis,
                description=description,
                mechanisms=mechanisms,
                feature_types=feature_types,
            )

            try:
                # Call LLM with structured output
                llm_response = self.llm.complete_structured(
                    messages=[{"role": "user", "content": prompt}],
                    response_model=LLMNarrativeResponse,
                    model=NARRATIVE_MODEL,
                    temperature=0.7,  # Some creativity for narrative text
                    operation_name=f"NarrativeLLM | {name[:20]}",
                )

                # Map option labels to UUIDs
                return self._map_response(llm_response, mechanisms)

            except Exception as e:
                self.logger.error(f"Narrative generation failed: {e}")
                raise NarrativeGenerationError(
                    f"Falha na geração de narrativa. Tente novamente. ({str(e)[:100]})"
                ) from e

    def _build_prompt(
        self,
        name: str,
        hypothesis: str,
        description: str | None,
        mechanisms: list,
        feature_types: list,
    ) -> str:
        """Build the LLM prompt with database data.

        The prompt structure follows RQ-001 from research.md.
        """
        # Build feature types section
        types_text = "\n".join(
            f"- **{ft.key}** ({ft.label_pt}): {ft.description or 'Sem descrição'}. "
            f"Amplifica: {', '.join(ft.amplifies_mechanisms) or 'nenhum'}"
            for ft in feature_types
        )

        # Build mechanisms section with options
        mechanisms_text = ""
        for mech in mechanisms:
            options_text = ", ".join(
                f'"{opt.label}" (valor={opt.value})' for opt in mech.options
            )
            mechanisms_text += (
                f"- **{mech.key}** ({mech.label_pt}): {mech.description}\n"
                f"  Opções: {options_text}\n"
            )

        # Build feature description
        feature_desc = f"Nome: {name}\nHipótese: {hypothesis}"
        if description:
            feature_desc += f"\nDescrição: {description}"

        prompt = f"""Você é um especialista em análise de features de produto.

## Tipos de Feature Disponíveis
{types_text}

## Mecanismos e suas Opções
{mechanisms_text}

## Tarefa
Analise a feature descrita e:
1. Infira os tipos aplicáveis (1-3 dos disponíveis acima)
2. Selecione mecanismos relevantes (2-4 de {len(mechanisms)} possíveis)
3. Gere narrativa em português com placeholders {{{{mechanism_key}}}}
4. Para cada mecanismo, escolha a opção default mais adequada

## Feature para Análise
{feature_desc}

## Instruções Importantes
- Narrativa deve ser texto contínuo e natural em português (2-4 frases)
- Use placeholders {{{{key}}}} (ex: {{{{irreversibility}}}})
- Cada placeholder aparece uma única vez na narrativa
- Escolha opções default adequadas ao contexto
- Exclua mecanismos não relevantes para esta feature

## Regras de Posicionamento dos Placeholders (CRÍTICO)
O placeholder DEVE ser um elemento gramatical da frase (adjetivo, substantivo).
Nunca coloque o placeholder após conjunções explicativas como "uma vez que", "pois", "porque".

ERRADO: "usuários desenvolvam nova rotina, uma vez que {{{{habit_displacement}}}}"
CERTO: "usuários precisam de um {{{{habit_displacement}}}} para adotar esta feature"

ERRADO: "a transação é segura, o que implica que {{{{institutional_trust}}}}"
CERTO: "esta funcionalidade {{{{institutional_trust}}}} na instituição financeira"

O placeholder substitui uma descrição, não é a explicação de algo anterior.

Retorne JSON: inferred_types, narrative_template, selected_mechanisms, excluded_mechanisms."""

        return prompt

    def _map_response(
        self,
        llm_response: LLMNarrativeResponse,
        mechanisms: list,
    ) -> NarrativeResponse:
        """Map LLM response to NarrativeResponse with option UUIDs."""
        # Build lookup dict: mechanism_key -> {option_label: option_id}
        mech_lookup = {}
        for mech in mechanisms:
            mech_lookup[mech.key] = {
                opt.label.lower(): opt.id for opt in mech.options
            }

        # Map selected mechanisms
        selected = []
        for sm in llm_response.selected_mechanisms:
            if sm.key not in mech_lookup:
                self.logger.warning(f"Unknown mechanism key from LLM: {sm.key}")
                continue

            option_lookup = mech_lookup[sm.key]
            label_lower = sm.default_option_label.lower()

            # Find option ID by label (fuzzy match)
            option_id = option_lookup.get(label_lower)
            if not option_id:
                # Try partial match
                for opt_label, opt_id in option_lookup.items():
                    if label_lower in opt_label or opt_label in label_lower:
                        option_id = opt_id
                        break

            if not option_id:
                # Default to middle option if label not found
                mech = next(m for m in mechanisms if m.key == sm.key)
                mid_idx = len(mech.options) // 2
                option_id = mech.options[mid_idx].id
                self.logger.warning(
                    f"Could not match label '{sm.default_option_label}' "
                    f"for {sm.key}, using middle option"
                )

            selected.append(
                SelectedMechanism(key=sm.key, default_option_id=option_id)
            )

        return NarrativeResponse(
            inferred_types=llm_response.inferred_types,
            narrative_template=llm_response.narrative_template,
            selected_mechanisms=selected,
            excluded_mechanisms=llm_response.excluded_mechanisms,
        )


# ============================================================================
# Module-level helper
# ============================================================================


def get_narrative_service(session: Session | None = None) -> NarrativeService:
    """Get a NarrativeService instance.

    Args:
        session: Optional SQLAlchemy session

    Returns:
        NarrativeService instance
    """
    return NarrativeService(session=session)
