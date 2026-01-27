"""
InsightGeneratorService for causal simulation system.

Synthesizes actionable insights from simulation evidence using LLM with full
traceability to statistical support.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - Data model: specs/035-causal-simulation/data-model.md
"""

import json
from typing import Any

from loguru import logger
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes

from synth_lab.domain.entities.causal_dag import CausalDAG
from synth_lab.domain.entities.simulated_world import (
    BehavioralCluster,
    Evidence,
    FailureMode,
)
from synth_lab.infrastructure.llm_client import LLMClient, get_llm_client
from synth_lab.infrastructure.phoenix_tracing import get_tracer

_tracer = get_tracer("insight-generator-service")

# Model for insight generation (needs reasoning to synthesize evidence)
INSIGHT_MODEL = "gpt-4o"


class InsightGeneratorService:
    """
    Service for generating actionable insights from simulation evidence.

    Uses LLM to synthesize evidence into clear insights with recommendations,
    maintaining full traceability to statistical support.
    """

    def __init__(self, llm_client: LLMClient | None = None):
        """
        Initialize InsightGeneratorService.

        Args:
            llm_client: LLM client for generation. Defaults to singleton.
        """
        self.llm = llm_client or get_llm_client()
        self.logger = logger.bind(component="insight_generator_service")

    def synthesize(
        self,
        simulation_id: str,
        dag: CausalDAG,
        evidence: Evidence,
        failure_modes: list[FailureMode],
        clusters: list[BehavioralCluster],
    ) -> list[dict[str, Any]]:
        """
        Generate actionable insights from simulation evidence.

        Args:
            simulation_id: Parent simulation ID
            dag: Causal DAG
            evidence: Aggregated evidence
            failure_modes: Detected failure modes
            clusters: Behavioral clusters

        Returns:
            List of insight dictionaries with traceability

        Raises:
            ValueError: If synthesis fails

        Example:
            >>> generator = InsightGeneratorService()
            >>> insights = generator.synthesize(
            ...     "sim_12345678", dag, evidence, failure_modes, clusters
            ... )
            >>> print(insights[0]['title'])
        """
        span_name = f"InsightGenerator | simulation {simulation_id[:12]}"
        with _tracer.start_as_current_span(
            span_name,
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                "operation.type": "insight_generation",
                "llm.model": INSIGHT_MODEL,
                "simulation.id": simulation_id,
                "evidence.num_outcomes": len(evidence.outcome_distributions),
                "evidence.num_failure_modes": len(failure_modes),
                "evidence.num_clusters": len(clusters),
            },
        ):
            try:
                self.logger.info(
                    f"Synthesizing insights for simulation {simulation_id}"
                )

                # Build prompt with evidence summary
                prompt = self._build_insight_prompt(
                    dag, evidence, failure_modes, clusters
                )

                # Call LLM with gpt-4o (reasoning needed)
                llm_response_str = self.llm.complete_json(
                    messages=[{"role": "user", "content": prompt}],
                    model=INSIGHT_MODEL,
                )

                # Parse LLM response
                llm_response = json.loads(llm_response_str)

                # Convert to insight dictionaries with traceability
                insights = self._parse_insights_response(
                    simulation_id, llm_response, evidence, failure_modes, clusters
                )

                self.logger.info(
                    f"Generated {len(insights)} insights for simulation {simulation_id}"
                )

                return insights

            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse LLM response as JSON: {e}"
                self.logger.error(error_msg)
                raise ValueError(error_msg) from e

            except Exception as e:
                error_msg = f"Insight generation failed: {e}"
                self.logger.error(error_msg)
                raise ValueError(error_msg) from e

    def _build_insight_prompt(
        self,
        dag: CausalDAG,
        evidence: Evidence,
        failure_modes: list[FailureMode],
        clusters: list[BehavioralCluster],
    ) -> str:
        """
        Build prompt for insight generation.

        Args:
            dag: Causal DAG
            evidence: Evidence with statistics
            failure_modes: Detected failure modes
            clusters: Behavioral clusters

        Returns:
            Formatted prompt string
        """
        # Summarize outcome distributions
        outcome_summary = []
        for outcome_name, dist in evidence.outcome_distributions.items():
            outcome_summary.append(
                f"- {outcome_name}: p5={dist.p5:.3f}, p50={dist.p50:.3f}, "
                f"p95={dist.p95:.3f}, mean={dist.mean:.3f}, std={dist.std:.3f}"
            )

        # Summarize top variance drivers
        top_drivers = evidence.variance_explained[:3]
        driver_summary = []
        for driver in top_drivers:
            driver_summary.append(
                f"- {driver.variable_name}: explains {driver.variance_explained:.1%} of variance (rank {driver.rank})"
            )

        # Summarize failure modes
        failure_summary = []
        for fm in failure_modes[:3]:
            failure_summary.append(
                f"- {fm.description} (severity: {fm.severity}, frequency: {fm.frequency:.1%})"
            )

        # Summarize clusters
        cluster_summary = []
        for cluster in clusters[:3]:
            cluster_summary.append(
                f"- {cluster.label}: {cluster.size} worlds ({cluster.percentage:.1%})"
            )

        return f"""Você é um analista de negócios gerando insights acionáveis a partir dos resultados da simulação.

**Evidências da Simulação**:

**Distribuições de Resultados** (entre {len(evidence.outcome_distributions)} resultados):
{chr(10).join(outcome_summary)}

**Principais Drivers de Variância** (análise de sensibilidade):
{chr(10).join(driver_summary) if driver_summary else "Nenhum detectado"}

**Modos de Falha** ({len(failure_modes)} detectados):
{chr(10).join(failure_summary) if failure_summary else "Nenhum detectado"}

**Clusters Comportamentais** ({len(clusters)} detectados):
{chr(10).join(cluster_summary) if cluster_summary else "Nenhum detectado"}

**Tarefa**: Gere 3-5 insights acionáveis para tomadores de decisão.

**Tipos de insight**:
1. **key_driver**: Fatores primários que influenciam os resultados
2. **failure_mode**: Cenários de risco específicos a evitar
3. **cluster_finding**: Padrões comportamentais distintos
4. **recommendation**: Próximos passos acionáveis

**Requisitos**:
- Cada insight deve ser específico e acionável
- Vincule insights às evidências estatísticas (percentis, variância, correlações)
- Priorize por impacto no negócio (falhas de alta severidade, principais drivers)
- Inclua recomendações concretas
- Use linguagem simples em português brasileiro (evite jargões)

**Formato de saída** (apenas JSON, sem markdown):
{{
  "insights": [
    {{
      "insight_type": "key_driver|failure_mode|cluster_finding|recommendation",
      "title": "Resumo breve em português (máx 100 caracteres)",
      "description": "Explicação detalhada com evidências em português",
      "confidence": "low|medium|high",
      "recommended_actions": [
        {{
          "action_type": "experiment|rollout_strategy|exclusion_criteria|data_collection",
          "description": "Ação específica a tomar em português",
          "priority": "low|medium|high"
        }}
      ]
    }}
  ]
}}

Retorne APENAS o objeto JSON, sem texto ou formatação adicional.
"""

    def _parse_insights_response(
        self,
        simulation_id: str,
        response: dict[str, Any],
        evidence: Evidence,
        failure_modes: list[FailureMode],
        clusters: list[BehavioralCluster],
    ) -> list[dict[str, Any]]:
        """
        Parse LLM response into insight dictionaries with traceability.

        Args:
            simulation_id: Parent simulation ID
            response: Parsed JSON response from LLM
            evidence: Evidence (for traceability)
            failure_modes: Failure modes (for traceability)
            clusters: Clusters (for traceability)

        Returns:
            List of insight dictionaries
        """
        insights = []

        for insight_data in response.get("insights", []):
            # Build evidence references for traceability
            evidence_refs = {
                "variance_explained_rank": (
                    evidence.variance_explained[0].rank
                    if evidence.variance_explained
                    else None
                ),
                "failure_mode_ids": [fm.id for fm in failure_modes[:3]],
                "cluster_ids": [c.id for c in clusters[:3]],
            }

            # Build statistical support
            statistical_support = {}
            if evidence.variance_explained:
                top_driver = evidence.variance_explained[0]
                statistical_support = {
                    "variance_explained": top_driver.variance_explained,
                    "sample_size": 500,  # Default from simulation
                }

            insights.append(
                {
                    "simulation_id": simulation_id,
                    "insight_type": insight_data["insight_type"],
                    "title": insight_data["title"],
                    "description": insight_data["description"],
                    "confidence": insight_data["confidence"],
                    "evidence_references": evidence_refs,
                    "statistical_support": statistical_support,
                    "recommended_actions": insight_data.get(
                        "recommended_actions", []
                    ),
                }
            )

        return insights
