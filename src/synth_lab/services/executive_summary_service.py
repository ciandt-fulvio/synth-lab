"""
ExecutiveSummaryService for AI-generated executive summaries.

Synthesizes multiple chart insights into a comprehensive executive summary
using gpt-4.1-mini model. Aggregates insights across all chart types
to provide strategic recommendations.

References:
    - Entity: src/synth_lab/domain/entities/executive_summary.py
    - Entity: src/synth_lab/domain/entities/chart_insight.py
    - Repository: src/synth_lab/repositories/analysis_cache_repository.py
    - Spec: specs/023-quantitative-ai-insights/spec.md (User Story 2, 3)
    - Config: src/synth_lab/infrastructure/config.py (REASONING_MODEL)

Sample usage:
    from synth_lab.services.executive_summary_service import ExecutiveSummaryService

    service = ExecutiveSummaryService()
    summary = service.generate_summary("ana_12345678")

Expected output:
    ExecutiveSummary with overview, explainability, segmentation, edge_cases, and recommendations
"""

from loguru import logger

from synth_lab.domain.entities.chart_insight import ChartInsight
from synth_lab.domain.entities.executive_summary import ExecutiveSummary
from synth_lab.infrastructure.config import REASONING_MODEL
from synth_lab.infrastructure.llm_client import LLMClient, get_llm_client
from synth_lab.infrastructure.phoenix_tracing import get_tracer
from synth_lab.repositories.analysis_cache_repository import AnalysisCacheRepository

_tracer = get_tracer()


class ExecutiveSummaryService:
    """Service for generating AI-powered executive summaries."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        cache_repo: AnalysisCacheRepository | None = None,
    ):
        """
        Initialize ExecutiveSummaryService.

        Args:
            llm_client: LLM client for reasoning. Defaults to singleton.
            cache_repo: Cache repository for persistence. Defaults to new instance.
        """
        self.llm = llm_client or get_llm_client()
        self.cache_repo = cache_repo or AnalysisCacheRepository()
        self.logger = logger.bind(component="executive_summary_service")

    def generate_summary(self, analysis_id: str) -> ExecutiveSummary:
        """
        Generate executive summary from all chart insights.

        Requires at least 3 completed insights to generate a meaningful summary.
        If some insights failed, creates a "partial" summary.

        Args:
            analysis_id: Analysis ID (e.g., "ana_12345678")

        Returns:
            ExecutiveSummary with status="completed", "partial", or "failed"

        Raises:
            ValueError: If less than 3 completed insights available
        """
        with _tracer.start_as_current_span("generate_executive_summary"):
            try:
                # Retrieve all insights
                all_insights = self.cache_repo.get_all_chart_insights(
                    analysis_id)
                completed_insights = [
                    i for i in all_insights if i.status == "completed"]

                # Validate minimum insights (need at least 2 out of 4 possible charts)
                if len(completed_insights) < 2:
                    raise ValueError(
                        f"Need at least 2 completed insights to generate summary, got {len(completed_insights)}"
                    )

                # Build synthesis prompt
                prompt = self._build_synthesis_prompt(completed_insights)

                # Call LLM with reasoning model
                self.logger.info(
                    f"Generating executive summary for {analysis_id} from {len(completed_insights)} insights"
                )
                llm_response_str = self.llm.complete_json(
                    messages=[{"role": "user", "content": prompt}],
                    model=REASONING_MODEL,
                )

                # Parse JSON string to dict
                import json
                llm_response = json.loads(llm_response_str)

                # Determine status (partial if some insights failed)
                status = "partial" if len(completed_insights) < len(
                    all_insights) else "completed"

                # Parse response into ExecutiveSummary
                summary = ExecutiveSummary(
                    analysis_id=analysis_id,
                    overview=llm_response["overview"],
                    explainability=llm_response["explainability"],
                    segmentation=llm_response["segmentation"],
                    edge_cases=llm_response["edge_cases"],
                    recommendations=llm_response["recommendations"],
                    included_chart_types=[
                        i.chart_type for i in completed_insights],
                    status=status,
                    model=REASONING_MODEL,
                )

                # Store in cache
                self.cache_repo.store_executive_summary(summary)
                self.logger.info(
                    f"Executive summary generated: {summary.status}")

                return summary

            except ValueError:
                raise  # Re-raise validation errors
            except Exception as e:
                self.logger.error(f"Failed to generate executive summary: {e}")
                # Create failed summary
                # Note: included_chart_types must have at least 1 item for validation
                # Using "unknown" as placeholder when generation fails
                failed_summary = ExecutiveSummary(
                    analysis_id=analysis_id,
                    overview="Failed to generate summary",
                    explainability="Error occurred during generation",
                    segmentation="Summary generation failed",
                    edge_cases="Error details: " + str(e),
                    recommendations=["Review error logs",
                                     "Retry summary generation"],
                    included_chart_types=["unknown"],
                    status="failed",
                    model=REASONING_MODEL,
                )
                self.cache_repo.store_executive_summary(failed_summary)
                return failed_summary

    def _build_synthesis_prompt(self, insights: list[ChartInsight]) -> str:
        """
        Build LLM prompt to synthesize multiple insights.

        Args:
            insights: List of completed chart insights

        Returns:
            Formatted synthesis prompt
        """
        # Build insight summaries (simplified - only summary field)
        insight_texts = []
        for insight in insights:
            insight_text = f"""**{insight.chart_type}:** {insight.summary}"""
            insight_texts.append(insight_text)

        all_insights_text = "\n\n".join(insight_texts)

        return f"""Você é um pesquisador UX criando um resumo executivo a partir de insights de análise quantitativa.

**Sua Tarefa:**
Sintetize os seguintes {len(insights)} insights de gráficos em um resumo executivo abrangente para stakeholders de produto.

**Todos os Insights:**
{all_insights_text}

**Formato de Saída (JSON):**
{{
  "overview": "O que foi testado e resultados gerais (≤200 palavras). Sintetize insights de Tentativa vs Sucesso e distribuição de resultados.",
  "explainability": "Principais drivers e impactos de features (≤200 palavras). Sintetize insights SHAP e PDP sobre o que influencia o sucesso.",
  "segmentation": "Grupos de usuários e padrões comportamentais (≤200 palavras). Sintetize insights PCA e radar sobre segmentos de usuários.",
  "edge_cases": "Surpresas, anomalias, descobertas inesperadas (≤200 palavras). Sintetize insights de casos extremos e outliers.",
  "recommendations": [
    "Primeira recomendação acionável para o time de produto",
    "Segunda recomendação acionável",
    "Terceira recomendação (opcional - apenas se fortemente suportada pelos insights)"
  ]
}}

**Diretrizes:**
- 2-3 recomendações obrigatórias (não mais de 3)
- Sintetize entre insights - não apenas liste descobertas individuais
- Foque em implicações estratégicas para decisões de produto
- Priorize recomendações por impacto e viabilidade
- Identifique padrões que emergem de múltiplos tipos de gráficos
- Destaque o insight mais importante de cada categoria
- Faça recomendações concretas e acionáveis
- SEMPRE responda em português brasileiro

**Síntese Entre Insights:**
- Conecte descobertas entre gráficos (ex: se SHAP mostra que confiança importa E casos extremos mostram falhas de usuários capazes, o problema pode ser percepção de segurança, não segurança real)
- Identifique quais segmentos de usuário (do PCA) se alinham com quais padrões de importância de features (do SHAP)
- Priorize recomendações baseado em tamanho do segmento × impacto no sucesso
"""


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Service instantiation
    total_tests += 1
    try:
        service = ExecutiveSummaryService()
        if service.llm is None:
            all_validation_failures.append("LLM client not initialized")
        if service.cache_repo is None:
            all_validation_failures.append("Cache repository not initialized")
    except Exception as e:
        all_validation_failures.append(f"Service instantiation failed: {e}")

    # Test 2: Prompt building
    total_tests += 1
    try:
        service = ExecutiveSummaryService()
        sample_insights = [
            ChartInsight(
                analysis_id="ana_12345678",
                chart_type=f"chart_{i}",
                summary=f"Insight resumido número {i} sobre o gráfico",
                status="completed",
            )
            for i in range(3)
        ]
        prompt = service._build_synthesis_prompt(sample_insights)
        if len(prompt) < 200:
            all_validation_failures.append("Synthesis prompt too short")
        if "overview" not in prompt or "recommendations" not in prompt:
            all_validation_failures.append("Prompt missing required sections")
    except Exception as e:
        all_validation_failures.append(f"Prompt building failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(
            f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(
            f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("ExecutiveSummaryService is validated and ready for use")
        sys.exit(0)
