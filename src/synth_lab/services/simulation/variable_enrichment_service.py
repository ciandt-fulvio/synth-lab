"""
VariableEnrichmentService for enriching node metadata using LLM.

When a user adds a new node to the DAG, this service fills in the metadata
(type, scope, description, controllability, etc.) based on the variable name
and DAG context.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - DAG Constructor: dag_constructor_service.py
    - Hypothesis Individual: hypothesis_individual_service.py
"""

from loguru import logger
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes
from pydantic import BaseModel, ConfigDict, Field

from synth_lab.domain.entities.causal_dag import (
    CausalDAG,
    Controllability,
    Edge,
    RelationshipType,
    StrengthEstimated,
    Variable,
    VariableScope,
    VariableType,
)
from synth_lab.infrastructure.llm_client import LLMClient, get_llm_client
from synth_lab.infrastructure.phoenix_tracing import get_tracer

_tracer = get_tracer("variable-enrichment-service")

# Use faster/cheaper model for enrichment
ENRICHMENT_MODEL = "gpt-4o-mini"


# =============================================================================
# LLM Response Models
# =============================================================================


class EnrichedVariable(BaseModel):
    """Enriched variable metadata from LLM."""

    name: str = Field(..., description="Variable name (snake_case)")
    type: VariableType = Field(..., description="Variable type classification")
    scope: VariableScope = Field(..., description="Simulation scope (world or user)")
    description: str = Field(..., description="Clear description in Portuguese")
    controllability: Controllability = Field(..., description="Degree of control")
    is_intervention: bool = Field(default=False, description="Is intervention variable")
    is_outcome: bool = Field(default=False, description="Is outcome variable")
    is_critical_uncertainty: bool = Field(
        default=False,
        description="True if this variable has high uncertainty and significant impact on outcomes"
    )


class SuggestedEdge(BaseModel):
    """Suggested causal relationship from LLM."""

    model_config = ConfigDict(populate_by_name=True)

    from_var: str = Field(..., alias="from", description="Source variable name")
    to_var: str = Field(..., alias="to", description="Target variable name")
    relationship_type: RelationshipType = Field(
        default=RelationshipType.CAUSAL,
        description="Type of causal relationship",
    )
    strength_estimated: StrengthEstimated = Field(
        default=StrengthEstimated.HIGH,
        description="Estimated strength of the causal effect: high or low",
    )
    rationale: str = Field(..., description="Why this relationship exists")


class EnrichmentResponse(BaseModel):
    """Complete enrichment response from LLM."""

    variable: EnrichedVariable = Field(..., description="Enriched variable metadata")
    suggested_edges: list[SuggestedEdge] = Field(
        default_factory=list,
        description="Suggested relationships with existing variables",
    )


class VariableEnrichmentService:
    """
    Service for enriching variable metadata using LLM.

    Used when a user adds a new node to the DAG with minimal information
    (just a name). The LLM analyzes the context and suggests:
    - Variable type (observable, latent, friction, etc.)
    - Scope (world vs user level)
    - Description
    - Controllability
    - Whether it's an intervention or outcome
    - Suggested edges to existing variables
    """

    def __init__(self, llm_client: LLMClient | None = None):
        """
        Initialize VariableEnrichmentService.

        Args:
            llm_client: LLM client for generation. Defaults to singleton.
        """
        self.llm = llm_client or get_llm_client()
        self.logger = logger.bind(component="variable_enrichment_service")

    def enrich(
        self,
        variable_name: str,
        context_dag: CausalDAG,
        intervention_hint: str | None = None,
        outcome_hint: str | None = None,
    ) -> tuple[Variable, list[Edge]]:
        """
        Enrich a variable with LLM-generated metadata.

        Args:
            variable_name: Name of the new variable
            context_dag: Existing DAG for context
            intervention_hint: Original intervention description (if available)
            outcome_hint: Original outcome description (if available)

        Returns:
            Tuple of (enriched Variable entity, list of suggested Edge entities)

        Example:
            >>> service = VariableEnrichmentService()
            >>> var, edges = service.enrich("taxa_conversao", dag)
            >>> print(f"Type: {var.type}, Scope: {var.scope}")
        """
        span_name = f"VariableEnrichment | {variable_name}"
        with _tracer.start_as_current_span(
            span_name,
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.LLM.value,
                "operation.type": "variable_enrichment",
                "variable.name": variable_name,
                "llm.model": ENRICHMENT_MODEL,
                "dag.num_variables": len(context_dag.nodes),
            },
        ):
            try:
                # Build prompt
                prompt = self._build_prompt(
                    variable_name, context_dag, intervention_hint, outcome_hint
                )

                # Call LLM with structured output
                response = self.llm.complete_structured(
                    messages=[{"role": "user", "content": prompt}],
                    response_model=EnrichmentResponse,
                    model=ENRICHMENT_MODEL,
                    operation_name=f"Enrich | {variable_name}",
                )

                # Convert to entities
                variable = self._response_to_variable(variable_name, response, context_dag)
                edges = self._response_to_edges(response, context_dag)

                # Helper to get value from enum or string
                def _val(v):
                    return v.value if hasattr(v, "value") else v

                self.logger.info(
                    f"Enriched variable {variable_name}: "
                    f"type={_val(variable.type)}, scope={_val(variable.scope)}, "
                    f"{len(edges)} suggested edges"
                )

                return variable, edges

            except Exception as e:
                self.logger.error(f"Failed to enrich {variable_name}: {e}")
                # Return default variable on error
                return self._create_default_variable(variable_name, context_dag), []

    def _build_prompt(
        self,
        variable_name: str,
        context_dag: CausalDAG,
        intervention_hint: str | None,
        outcome_hint: str | None,
    ) -> str:
        """Build prompt for variable enrichment."""
        # Helper to get string value from enum or string
        def _enum_val(val) -> str:
            return val.value if hasattr(val, "value") else str(val)

        # Get existing variables for context
        existing_vars = "\n".join(
            f"- {v.name} ({_enum_val(v.type)}, {_enum_val(v.scope)}): {v.description}"
            for v in context_dag.nodes
        )

        # Get existing edges
        existing_edges = "\n".join(
            f"- {e.from_var} → {e.to_var} ({_enum_val(e.relationship_type)})"
            for e in context_dag.edges
        )

        # Intervention/outcome info
        context_info = ""
        if intervention_hint:
            context_info += f"\n**Intervenção do estudo**: {intervention_hint}"
        if outcome_hint:
            context_info += f"\n**Resultado esperado**: {outcome_hint}"

        return f"""Você é um especialista em inferência causal ajudando a preencher metadados de uma variável em um DAG causal.

## Nova Variável a Enriquecer

**Nome**: {variable_name}
{context_info}

## Variáveis Existentes no DAG
{existing_vars if existing_vars else "(Nenhuma outra variável)"}

## Relações Causais Existentes
{existing_edges if existing_edges else "(Nenhuma relação definida)"}

## Tarefa

Com base no nome "{variable_name}" e no contexto do DAG, preencha os metadados da variável:

### Tipos de variáveis:
- `observable`: Diretamente mensurável (ex: preco, taxa_churn, cadastros)
- `latent`: Não diretamente mensurável (ex: percepcao_marca, confianca, motivacao)
- `friction`: Impedimentos (ex: falhas_entrega, complexidade_cadastro, bugs)
- `failure`: Modos de falha binários (ex: pagamento_recusado, estoque_esgotado)
- `process`: Sequencial/temporal (ex: etapa_onboarding, dias_desde_cadastro)
- `temporal`: Dependente do tempo (ex: sazonalidade, maturidade_mercado)

### Escopo:
- `world`: Nível do sistema (amostrado uma vez por mundo simulado)
- `user`: Nível individual (amostrado por usuário/unidade)

### Controlabilidade:
- `none`: Não pode ser controlado (ex: condições de mercado)
- `low`: Difícil de controlar (ex: ações de concorrentes)
- `medium`: Moderadamente controlável (ex: estratégia de preços)
- `high`: Totalmente controlável (ex: budget de marketing)

### Regras:
- `is_intervention`: Marque como true APENAS se esta variável representa a intervenção principal do estudo
- `is_outcome`: Marque como true APENAS se esta variável representa o resultado que queremos medir
- `is_critical_uncertainty`: Marque como true se a variável tem ALTA INCERTEZA (difícil de estimar) E ALTO IMPACTO (influência significativa no resultado)
  - Exemplos: variáveis latentes, fricções com alta variabilidade, modos de falha com probabilidade desconhecida
  - NÃO marque: intervenção, resultado, ou variáveis observáveis com dados confiáveis

### Sugestão de Arestas:
Sugira relações causais plausíveis com as variáveis existentes. Use nomes EXATOS das variáveis existentes.

Para cada aresta, informe:
- `relationship_type`: causal, mediating, confounding ou moderating
- `strength_estimated`: high (efeito forte) ou low (efeito fraco)
- `rationale`: justificativa da relação

Retorne APENAS o objeto JSON, sem texto adicional.
"""

    def _response_to_variable(
        self,
        variable_name: str,
        response: EnrichmentResponse,
        context_dag: CausalDAG,
    ) -> Variable:
        """Convert LLM response to Variable entity."""
        enriched = response.variable

        # Generate unique ID
        var_id = f"{context_dag.id}_{variable_name}" if context_dag.id else f"var_{variable_name}"

        return Variable(
            id=var_id,
            name=variable_name,
            type=enriched.type,
            scope=enriched.scope,
            description=enriched.description,
            controllability=enriched.controllability,
            is_intervention=enriched.is_intervention,
            is_outcome=enriched.is_outcome,
            is_critical_uncertainty=enriched.is_critical_uncertainty,
        )

    def _response_to_edges(
        self,
        response: EnrichmentResponse,
        context_dag: CausalDAG,
    ) -> list[Edge]:
        """Convert suggested edges to Edge entities."""
        # Get set of valid variable names
        valid_names = {v.name for v in context_dag.nodes}

        edges = []
        for suggested in response.suggested_edges:
            # Validate that edge connects to existing variables
            # The new variable might be 'from' or 'to'
            if suggested.from_var in valid_names or suggested.to_var in valid_names:
                edges.append(
                    Edge(
                        from_var=suggested.from_var,
                        to_var=suggested.to_var,
                        relationship_type=suggested.relationship_type,
                        strength_estimated=suggested.strength_estimated,
                    )
                )

        return edges

    def _create_default_variable(
        self,
        variable_name: str,
        context_dag: CausalDAG,
    ) -> Variable:
        """Create default variable when LLM fails."""
        var_id = f"{context_dag.id}_{variable_name}" if context_dag.id else f"var_{variable_name}"

        return Variable(
            id=var_id,
            name=variable_name,
            type=VariableType.OBSERVABLE,
            scope=VariableScope.WORLD,
            description=f"Variável {variable_name}",
            controllability=Controllability.MEDIUM,
            is_intervention=False,
            is_outcome=False,
            is_critical_uncertainty=False,
        )


if __name__ == "__main__":
    import sys

    print("=== Variable Enrichment Service Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Test 1: Service instantiation
    total_tests += 1
    try:
        service = VariableEnrichmentService()
        print("Test 1 PASSED: Service instantiation")
    except Exception as e:
        all_validation_failures.append(f"Service instantiation failed: {e}")

    # Test 2: Default variable creation
    total_tests += 1
    try:
        from synth_lab.domain.entities.causal_dag import generate_dag_id
        from synth_lab.domain.entities.simulation import generate_simulation_id

        mock_dag = CausalDAG(
            id=generate_dag_id(),
            simulation_id=generate_simulation_id(),
            nodes=[],
            edges=[],
        )

        default_var = service._create_default_variable("taxa_conversao", mock_dag)

        if default_var.name != "taxa_conversao":
            all_validation_failures.append(
                f"Default variable name wrong: {default_var.name}"
            )
        elif default_var.type != VariableType.OBSERVABLE:
            all_validation_failures.append(
                f"Default variable type wrong: {default_var.type}"
            )
        else:
            print("Test 2 PASSED: Default variable creation")
    except Exception as e:
        all_validation_failures.append(f"Default variable creation failed: {e}")

    # Test 3: Prompt building
    total_tests += 1
    try:
        test_dag = CausalDAG(
            id=generate_dag_id(),
            simulation_id=generate_simulation_id(),
            nodes=[
                Variable(
                    id="var_1",
                    name="investimento_marketing",
                    type=VariableType.OBSERVABLE,
                    scope=VariableScope.WORLD,
                    description="Investimento em marketing",
                    controllability=Controllability.HIGH,
                )
            ],
            edges=[],
        )

        prompt = service._build_prompt(
            "taxa_conversao",
            test_dag,
            intervention_hint="Aumentar investimento em marketing",
            outcome_hint="Melhorar taxa de conversão",
        )

        if "taxa_conversao" not in prompt:
            all_validation_failures.append("Prompt missing variable name")
        elif "investimento_marketing" not in prompt:
            all_validation_failures.append("Prompt missing context variable")
        else:
            print("Test 3 PASSED: Prompt building includes context")
    except Exception as e:
        all_validation_failures.append(f"Prompt building failed: {e}")

    # Final result
    print()
    if all_validation_failures:
        print(
            f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
