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
2. Selecione mecanismos relevantes (exatamente 3-5 de {len(mechanisms)} possíveis). Em especial,
considere os mecanismos de intrinsic_value, operational_friction, e frequency_of_use,
pois em geral sao sempre importantes (obviamente, se nao fizer sentido, não use).
Por outro lado, usar só esses 3 não gera diferenciação, então use mais outros mecanismos também.
IMPORTANTE: Você DEVE retornar entre 3 e 5 mecanismos (não menos que 3, não mais que 5).
3. Gere narrativa em português com placeholders {{{{mechanism_key}}}}
4. Para cada mecanismo, escolha a opção default mais adequada

## Feature para Análise
{feature_desc}

## CRÍTICO: Regras de Fluidez Textual

### Princípio Fundamental
Você DEVE escrever o texto AO REDOR das opções disponíveis, não encaixar placeholders em texto pré-escrito.
ANTES de escrever cada frase, consulte as opções disponíveis e construa uma estrutura gramatical que funcione com TODAS as opções.

### Processo de Escrita (OBRIGATÓRIO)
1. Escolha um mecanismo para incluir na narrativa
2. LEIA TODAS as opções disponíveis para esse mecanismo
3. Identifique a função gramatical das opções (substantivo, adjetivo, verbo)
4. Construa a frase de forma que o placeholder se encaixe NATURALMENTE
5. Teste mentalmente: substitua o placeholder por cada opção — todas devem fazer sentido

### Padrões Linguísticos Recomendados

**Para mecanismos de frequência (frequency_of_use):**
ATENÇÃO: As opções deste mecanismo são ADVÉRBIOS (diariamente, semanalmente, mensalmente) ou ADJETIVOS (diário, semanal, mensal).

- ✅ PERFEITO: "usuários precisam acessar a funcionalidade {{{{frequency_of_use}}}}"
  → "acessar diariamente", "acessar semanalmente" (advérbio após verbo)
- ✅ PERFEITO: "a funcionalidade exige interação {{{{frequency_of_use}}}}"
  → "interação diária", "interação semanal" (adjetivo após substantivo)
- ✅ PERFEITO: "usuários utilizam o sistema {{{{frequency_of_use}}}}"
  → "utilizam diariamente", "utilizam semanalmente" (advérbio após verbo)
- ❌ PÉSSIMO: "requer um {{{{frequency_of_use}}}}"
  → "requer um diariamente" (não faz sentido - advérbio após artigo)
- ❌ PÉSSIMO: "exigindo um {{{{frequency_of_use}}}} de uso"
  → "exigindo um diário de uso" (estrutura gramatical incorreta)

**Para mecanismos de fricção (operational_friction):**
ATENÇÃO: As opções deste mecanismo são ADJETIVOS COMPOSTOS (sem fricção, de baixa fricção, etc).

- ✅ PERFEITO: "a operação é {{{{operational_friction}}}}"
  → "a operação é sem fricção", "a operação é de baixa fricção" (adjetivo predicativo)
- ✅ PERFEITO: "oferece uma experiência {{{{operational_friction}}}}"
  → "experiência sem fricção", "experiência de alta fricção" (adjetivo após substantivo)
- ✅ PERFEITO: "o processo se mostra {{{{operational_friction}}}}"
  → "se mostra sem fricção", "se mostra de média fricção" (adjetivo predicativo)
- ❌ PÉSSIMO: "tornando a operação {{{{operational_friction}}}}"
  → "tornando a operação sem fricção" (INCOMPLETO - falta continuação!)
  CORRETO seria: "tornando a operação {{{{operational_friction}}}} para o usuário"
- ❌ PÉSSIMO: "a operação oferece {{{{operational_friction}}}}"
  → "oferece sem fricção" (verbo 'oferecer' não combina com adjetivo diretamente)

**Para mecanismos de confiança (institutional_trust):**
- ✅ BOM: "a funcionalidade {{{{institutional_trust}}}} na instituição"
  → "requer confiança básica", "exige confiança total" (todas fluem)
- ✅ BOM: "depende de {{{{institutional_trust}}}} do usuário"
  → "depende de confiança básica", "depende de confiança total" (todas fluem)
- ❌ ERRADO: "a confiança é {{{{institutional_trust}}}}"
  → "a confiança é requer confiança básica" (não faz sentido)

**Para mecanismos de hábito (habit_displacement):**
- ✅ BOM: "usuários precisam de {{{{habit_displacement}}}} para adotar"
  → "de ajuste mínimo", "de mudança de rotina" (todas fluem)
- ✅ BOM: "a adoção exige {{{{habit_displacement}}}}"
  → "exige ajuste mínimo", "exige mudança de rotina" (todas fluem)
- ❌ ERRADO: "usuários desenvolvam nova rotina, uma vez que {{{{habit_displacement}}}}"
  → "uma vez que ajuste mínimo" (não faz sentido)

### VERIFICAÇÃO ANTI-ERRO (Execute ANTES de retornar)

Para CADA frase com placeholder, verifique:

1. **NUNCA termine frase com placeholder incompleto**
   ❌ "tornando a operação {{{{operational_friction}}}}" (FALTA continuação!)
   ✅ "tornando a operação {{{{operational_friction}}}} para todos" (completo)

2. **NUNCA use artigo + placeholder de advérbio**
   ❌ "requer um {{{{frequency_of_use}}}}" (artigo não combina com advérbio)
   ✅ "provavelmente usado {{{{frequency_of_use}}}}" (sem artigo)

3. **NUNCA use verbo inadequado + placeholder de adjetivo**
   ❌ "oferece {{{{operational_friction}}}}" (verbo 'oferecer' não combina)
   ✅ "é {{{{operational_friction}}}}" ou "oferece experiência {{{{operational_friction}}}}"

### Verificação Final (OBRIGATÓRIA)
Antes de retornar a narrativa, para CADA placeholder:
1. Substitua mentalmente por TODAS as opções disponíveis
2. Se qualquer substituição soar estranha ou gramaticalmente incorreta, REESCREVA a frase
3. Leia a frase completa em voz alta (mentalmente) - deve soar natural
4. Confirme que não há frases incompletas ou truncadas

### Instruções de Formatação
- Narrativa deve ser texto contínuo e natural em português (2-4 frases)
- Use placeholders {{{{key}}}} (ex: {{{{irreversibility}}}})
- Cada placeholder aparece uma única vez na narrativa
- Escolha opções default adequadas ao contexto
- Exclua mecanismos não relevantes para esta feature
- NUNCA use conjunções explicativas antes de placeholders ("pois", "porque", "uma vez que")

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
