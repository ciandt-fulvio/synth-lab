"""
DAGConstructorService for causal simulation system.

Generates causal DAGs from problem decomposition using LLM, validates structure
using NetworkX, and serializes for storage.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - Data model: specs/035-causal-simulation/data-model.md
    - NetworkX: https://networkx.org/documentation/stable/
    - OpenAI Structured Outputs: https://platform.openai.com/docs/guides/structured-outputs
"""

from loguru import logger
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes
from pydantic import BaseModel, Field

from synth_lab.domain.entities.causal_dag import (
    Assumption,
    CausalDAG,
    ConfidenceLevel,
    Controllability,
    Edge,
    ImpactLevel,
    RelationshipType,
    Risk,
    StrengthEstimated,
    Variable,
    VariableScope,
    VariableType,
    generate_dag_id,
)
from synth_lab.domain.entities.simulation import ProblemDecomposition
from synth_lab.infrastructure.llm_client import LLMClient, get_llm_client
from synth_lab.infrastructure.phoenix_tracing import get_tracer
from synth_lab.services.simulation.dag_validator import DAGValidator

# =============================================================================
# LLM Response Models (for Structured Outputs)
# =============================================================================


class LLMVariable(BaseModel):
    """Variable in LLM response - uses enums to guarantee valid values."""

    id: str = Field(..., description="Unique variable ID (e.g., var_001)")
    name: str = Field(..., description="Human-readable variable name in snake_case")
    type: VariableType = Field(..., description="Variable type classification")
    scope: VariableScope = Field(..., description="Simulation scope (world or user)")
    description: str = Field(..., description="Clear description of the variable")
    controllability: Controllability = Field(..., description="Degree of control")
    is_intervention: bool = Field(default=False, description="Is intervention variable")
    is_outcome: bool = Field(default=False, description="Is outcome variable")
    is_critical_uncertainty: bool = Field(
        default=False,
        description="True if this variable has high uncertainty and significant impact on outcomes"
    )


class LLMEdge(BaseModel):
    """Edge in LLM response - uses enum to guarantee valid relationship types."""

    from_var: str = Field(..., alias="from", description="Source variable ID")
    to_var: str = Field(..., alias="to", description="Target variable ID")
    relationship_type: RelationshipType = Field(
        default=RelationshipType.CAUSAL,
        description="Type of causal relationship: causal, mediating, confounding, or moderating",
    )
    strength_estimated: StrengthEstimated = Field(
        default=StrengthEstimated.HIGH,
        description="Estimated strength of the causal effect: high or low",
    )

    class Config:
        populate_by_name = True


class LLMAssumption(BaseModel):
    """Assumption in LLM response."""

    assumption: str = Field(..., description="Statement of assumption")
    rationale: str = Field(..., description="Why this assumption is necessary")
    confidence: ConfidenceLevel = Field(..., description="Confidence level")


class LLMRisk(BaseModel):
    """Risk in LLM response."""

    risk: str = Field(..., description="Description of identified risk")
    impact: ImpactLevel = Field(..., description="Potential impact level")
    mitigation: str = Field(..., description="How to address this risk")


class DAGResponse(BaseModel):
    """
    Complete DAG response from LLM.

    This model is used with OpenAI's Structured Outputs to guarantee
    the response adheres to the schema - no invalid enum values possible.
    """

    variables: list[LLMVariable] = Field(
        ..., description="List of 8-20 variables in the DAG"
    )
    edges: list[LLMEdge] = Field(..., description="Causal relationships between variables")
    assumptions: list[LLMAssumption] = Field(
        ..., description="2-3 modeling assumptions"
    )
    risks: list[LLMRisk] = Field(..., description="2-3 identified risks/uncertainties")

_tracer = get_tracer("dag-constructor-service")

# Model for DAG generation (needs reasoning for causal relationships)
DAG_MODEL = "gpt-4o"

# Maximum retry attempts for DAG generation
MAX_DAG_RETRIES = 2


class DAGConstructorService:
    """
    Service for generating and validating causal DAGs.

    Uses LLM to generate DAG structure with variables and causal relationships,
    then validates using NetworkX graph algorithms.
    """

    def __init__(self, llm_client: LLMClient | None = None):
        """
        Initialize DAGConstructorService.

        Args:
            llm_client: LLM client for generation. Defaults to singleton.
        """
        self.llm = llm_client or get_llm_client()
        self.validator = DAGValidator()
        self.logger = logger.bind(component="dag_constructor_service")

    def generate(
        self, simulation_id: str, problem: ProblemDecomposition
    ) -> CausalDAG:
        """
        Generate causal DAG from problem decomposition.

        Args:
            simulation_id: Parent simulation ID
            problem: Structured problem decomposition

        Returns:
            CausalDAG with validated structure (8-20 variables, no cycles)

        Raises:
            ValueError: If DAG generation fails or validation fails

        Example:
            >>> constructor = DAGConstructorService()
            >>> problem = ProblemDecomposition(...)
            >>> dag = constructor.generate("sim_12345678", problem)
            >>> print(f"Generated {len(dag.nodes)} variables")
        """
        span_name = f"DAGConstructor | {problem.intervention[:40]}..."
        with _tracer.start_as_current_span(
            span_name,
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                "operation.type": "dag_generation",
                "llm.model": DAG_MODEL,
                "simulation.id": simulation_id,
                "problem.intervention": problem.intervention,
                "problem.outcome": problem.primary_outcome,
            },
        ):
            last_error = None
            validation_feedback = None

            for attempt in range(MAX_DAG_RETRIES + 1):
                try:
                    # Build prompt for DAG generation (include feedback if retry)
                    prompt = self._build_dag_prompt(problem, validation_feedback)

                    # Call LLM with Structured Outputs - guarantees valid schema
                    self.logger.info(
                        f"Generating DAG for intervention: {problem.intervention[:60]}"
                        + (f" (attempt {attempt + 1})" if attempt > 0 else "")
                    )
                    dag_response = self.llm.complete_structured(
                        messages=[{"role": "user", "content": prompt}],
                        response_model=DAGResponse,
                        model=DAG_MODEL,
                        operation_name=f"DAG Generation | {problem.intervention[:30]}",
                    )

                    # Convert structured response to CausalDAG entity
                    dag = self._convert_to_dag(simulation_id, dag_response)

                    # Validate DAG structure (cycles, orphans, etc.)
                    is_valid, errors, _warnings = self.validator.validate(dag)
                    if not is_valid:
                        error_msgs = [err.description for err in errors]
                        validation_feedback = "; ".join(error_msgs)
                        last_error = ValueError(f"DAG validation failed: {validation_feedback}")
                        self.logger.warning(
                            f"DAG validation failed (attempt {attempt + 1}): {validation_feedback}"
                        )
                        continue  # Retry with feedback

                    dag.is_validated = True
                    dag.validation_errors = None

                    self.logger.info(
                        f"Successfully generated DAG: {len(dag.nodes)} variables, "
                        f"{len(dag.edges)} edges"
                    )

                    return dag

                except ValueError:
                    raise  # Re-raise validation errors after retries exhausted
                except Exception as e:
                    last_error = e
                    self.logger.warning(f"DAG generation attempt {attempt + 1} failed: {e}")
                    continue

            # All retries exhausted
            error_msg = f"DAG generation failed after {MAX_DAG_RETRIES + 1} attempts: {last_error}"
            self.logger.error(error_msg)
            raise ValueError(error_msg) from last_error

    def _build_dag_prompt(
        self, problem: ProblemDecomposition, validation_feedback: str | None = None
    ) -> str:
        """
        Build prompt for DAG generation.

        Args:
            problem: Problem decomposition
            validation_feedback: Error message from previous validation attempt (for retry)

        Returns:
            Formatted prompt string
        """
        feedback_section = ""
        if validation_feedback:
            feedback_section = f"""
**IMPORTANTE - A tentativa anterior falhou na validação com estes erros:**
{validation_feedback}

Por favor, corrija esses problemas na nova resposta. Correções comuns:
- "Componente desconectado": Garanta que TODA variável tenha pelo menos uma aresta conectando-a
- "Ciclo detectado": Remova arestas que criam loops
- "Intervenção faltando": Marque exatamente uma variável com is_intervention=true
- "Resultado faltando": Marque pelo menos uma variável com is_outcome=true

"""
        return f"""Você é um especialista em inferência causal gerando um Grafo Acíclico Dirigido (DAG) para simulação.
{feedback_section}

**Problema**:
- Intervenção: {problem.intervention}
- Resultado Principal: {problem.primary_outcome}
- Resultados Secundários: {', '.join(problem.secondary_outcomes) if problem.secondary_outcomes else 'Nenhum'}
- Unidade de Análise: {problem.unit_of_analysis}
- Horizonte de Tempo: {problem.time_horizon}
- Tipo de Decisão: {problem.decision_type}

**Tarefa**: Gere um DAG causal com 8-20 variáveis representando:
1. A variável de intervenção
2. A variável de resultado principal
3. Variáveis mediadoras (fatores que transmitem o efeito da intervenção)
4. Variáveis de confusão (causas comuns)
5. Variáveis de fricção (impedimentos ao sucesso)
6. Métricas observáveis (diretamente mensuráveis)
7. Variáveis latentes (não diretamente mensuráveis mas importantes)

**Tipos de variáveis**:
- `observable`: Diretamente mensurável (ex: preco, taxa_churn, cadastros)
- `latent`: Não diretamente mensurável (ex: percepcao_marca, confianca, motivacao)
- `friction`: Impedimentos (ex: falhas_entrega, complexidade_cadastro, bugs)
- `failure`: Modos de falha binários (ex: pagamento_recusado, estoque_esgotado)
- `process`: Sequencial/temporal (ex: etapa_onboarding, dias_desde_cadastro)
- `temporal`: Dependente do tempo (ex: sazonalidade, maturidade_mercado)

**Escopo da variável**:
- `world`: Nível do sistema (amostrado uma vez por mundo simulado, ex: investimento_marketing)
- `user`: Nível individual (amostrado por {problem.unit_of_analysis} no mundo, ex: engajamento_usuario)

**Controlabilidade**:
- `none`: Não pode ser controlado (ex: condicoes_mercado)
- `low`: Difícil de controlar (ex: acoes_concorrentes)
- `medium`: Moderadamente controlável (ex: estrategia_precos)
- `high`: Totalmente controlável (ex: budget_marketing, disponibilidade_feature)

**Incertezas Críticas** (`is_critical_uncertainty`):
Marque como `true` se a variável atende AMBOS os critérios:
1. **Alta Incerteza**: O valor ou distribuição é difícil de estimar com precisão (ex: variáveis latentes, fricções com alta variabilidade, modos de falha com probabilidade desconhecida)
2. **Alto Impacto**: Tem influência significativa no resultado principal (direta ou indiretamente através de mediadores)

Exemplos de incertezas críticas:
- Variáveis **latentes** (ex: percepcao_facilidade, satisfacao_cliente) - não observáveis, alta incerteza
- **Fricções** com alta variabilidade (ex: falhas_tecnicas, complexidade_cadastro) - difíceis de prever
- **Modos de falha** com probabilidade desconhecida (ex: ficou_sem_estoque) - frequência incerta
- Variáveis **temporais** difíceis de prever (ex: sazonalidade) - comportamento futuro incerto

NÃO marque como incerteza crítica:
- A variável de **intervenção** (é o que estamos controlando)
- A variável de **resultado** (é o que estamos medindo)
- Variáveis **observáveis** com dados históricos confiáveis (ex: preco fixo)

**Tipos de arestas**:
- `causal`: Efeito causal direto (A → B)
- `mediating`: Variável que transmite o efeito (A → M → B)
- `confounding`: Causa comum (C → A e C → B)
- `moderating`: Modificador de efeito (M altera a força de A → B)

**Força estimada da aresta**:
- `high`: Efeito causal forte esperado (ex: preço → demanda)
- `low`: Efeito causal fraco esperado (ex: cor_botao → conversao)

**Requisitos**:
- O DAG DEVE ser acíclico (sem ciclos)
- Inclua 8-20 variáveis (mire em 12-15)
- Marque a variável de intervenção com `is_intervention: true`
- Marque a(s) variável(is) de resultado com `is_outcome: true`
- Inclua 2-3 suposições sobre a estrutura do modelo
- Inclua 2-3 riscos/incertezas
- Use nomes descritivos de variáveis em português (snake_case)
- CRÍTICO: TODAS as variáveis DEVEM estar conectadas - cada variável deve ter pelo menos uma aresta (entrando ou saindo)
- O grafo deve formar um único componente conectado (sem variáveis isoladas)

**Formato de saída** (apenas JSON, sem markdown):
{{
  "variables": [
    {{
      "id": "var_001",
      "name": "nome_variavel",
      "type": "observable|latent|friction|failure|process|temporal",
      "scope": "world|user",
      "description": "Descrição clara da variável em português",
      "controllability": "none|low|medium|high",
      "is_intervention": false,
      "is_outcome": false,
      "is_critical_uncertainty": false
    }}
  ],
  "edges": [
    {{
      "from": "var_001",
      "to": "var_002",
      "relationship_type": "causal|mediating|confounding|moderating",
      "strength_estimated": "high|low"
    }}
  ],
  "assumptions": [
    {{
      "assumption": "Declaração da suposição em português",
      "rationale": "Por que esta suposição é necessária",
      "confidence": "low|medium|high"
    }}
  ],
  "risks": [
    {{
      "risk": "Risco ou incerteza identificado em português",
      "impact": "low|medium|high",
      "mitigation": "Como endereçar este risco"
    }}
  ]
}}

Retorne APENAS o objeto JSON, sem texto ou formatação adicional.
"""

    def _convert_to_dag(
        self, simulation_id: str, response: DAGResponse
    ) -> CausalDAG:
        """
        Convert structured LLM response to CausalDAG entity.

        Since we use Structured Outputs, all values are already validated.
        Variable IDs are prefixed with DAG ID to ensure global uniqueness.

        Args:
            simulation_id: Parent simulation ID
            response: Validated DAGResponse from LLM

        Returns:
            CausalDAG entity
        """
        # Generate DAG ID first to use in variable ID prefixes
        dag_id = generate_dag_id()

        # Create mapping from LLM variable IDs to globally unique IDs
        id_mapping = {v.id: f"{dag_id}_{v.id}" for v in response.variables}

        # Create mapping from LLM variable IDs to variable names (for edges)
        name_mapping = {v.id: v.name for v in response.variables}

        # Convert LLMVariable to Variable with unique IDs
        variables = [
            Variable(
                id=id_mapping[v.id],
                name=v.name,
                type=v.type,
                scope=v.scope,
                description=v.description,
                controllability=v.controllability,
                is_intervention=v.is_intervention,
                is_outcome=v.is_outcome,
                is_critical_uncertainty=v.is_critical_uncertainty,
            )
            for v in response.variables
        ]

        # Convert LLMEdge to Edge with variable names (not IDs)
        # This allows edges to reference variables by their user-visible names
        edges = [
            Edge(
                from_var=name_mapping[e.from_var],
                to_var=name_mapping[e.to_var],
                relationship_type=e.relationship_type,
                strength_estimated=e.strength_estimated,
            )
            for e in response.edges
        ]

        # Convert LLMAssumption to Assumption
        assumptions = [
            Assumption(
                assumption=a.assumption,
                rationale=a.rationale,
                confidence=a.confidence,
            )
            for a in response.assumptions
        ]

        # Convert LLMRisk to Risk
        risks = [
            Risk(
                risk=r.risk,
                impact=r.impact,
                mitigation=r.mitigation,
            )
            for r in response.risks
        ]

        return CausalDAG(
            id=dag_id,
            simulation_id=simulation_id,
            nodes=variables,
            edges=edges,
            assumptions=assumptions,
            risks=risks,
        )
