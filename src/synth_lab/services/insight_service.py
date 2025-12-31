"""
InsightService for AI-generated chart insights.

Generates LLM-powered insights for individual chart types using gpt-4.1-mini model.
Stores results in analysis_cache table for retrieval by frontend.

References:
    - Entity: src/synth_lab/domain/entities/chart_insight.py
    - Repository: src/synth_lab/repositories/analysis_cache_repository.py
    - Spec: specs/023-quantitative-ai-insights/spec.md (User Story 1, 3)

Sample usage:
    from synth_lab.services.insight_service import InsightService

    service = InsightService()
    chart_data = {"quadrants": [...], "total_synths": 500}
    insight = service.generate_insight("ana_12345678", "try_vs_success", chart_data)

Expected output:
    ChartInsight with summary field containing the AI-generated insight
"""

import json
from typing import Any

from loguru import logger
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes

from synth_lab.domain.entities.chart_insight import ChartInsight
from synth_lab.infrastructure.llm_client import LLMClient, get_llm_client
from synth_lab.infrastructure.phoenix_tracing import get_tracer
from synth_lab.repositories.analysis_cache_repository import AnalysisCacheRepository
from synth_lab.repositories.analysis_repository import AnalysisRepository
from synth_lab.repositories.experiment_repository import ExperimentRepository

_tracer = get_tracer()

# Model for chart insights (fast, no reasoning)
INSIGHT_MODEL = "gpt-4.1-mini"


class InsightService:
    """Service for generating AI-powered chart insights."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        cache_repo: AnalysisCacheRepository | None = None,
        analysis_repo: AnalysisRepository | None = None,
        experiment_repo: ExperimentRepository | None = None,
    ):
        """
        Initialize InsightService.

        Args:
            llm_client: LLM client for generation. Defaults to singleton.
            cache_repo: Cache repository for persistence. Defaults to new instance.
            analysis_repo: Analysis repository for fetching analysis data.
            experiment_repo: Experiment repository for fetching hypothesis.
        """
        self.llm = llm_client or get_llm_client()
        self.cache_repo = cache_repo or AnalysisCacheRepository()
        self.analysis_repo = analysis_repo or AnalysisRepository()
        self.experiment_repo = experiment_repo or ExperimentRepository()
        self.logger = logger.bind(component="insight_service")

    def _get_hypothesis(self, analysis_id: str) -> str:
        """
        Get hypothesis from experiment linked to analysis.

        Args:
            analysis_id: Analysis ID

        Returns:
            Hypothesis string or empty string if not found
        """
        analysis = self.analysis_repo.get_by_id(analysis_id)
        if analysis is None:
            return ""

        experiment = self.experiment_repo.get_by_id(analysis.experiment_id)
        if experiment is None:
            return ""

        return experiment.hypothesis or ""

    def generate_insight(
        self,
        analysis_id: str,
        chart_type: str,
        chart_data: dict[str, Any],
    ) -> ChartInsight:
        """
        Generate insight for a specific chart type.

        Uses LLM to analyze chart data and produce structured insight.
        Stores result in cache for retrieval.

        Args:
            analysis_id: Analysis ID (e.g., "ana_12345678")
            chart_type: Chart type (e.g., "try_vs_success", "shap_summary")
            chart_data: Chart data to analyze

        Returns:
            ChartInsight with status="completed" or status="failed"
        """
        span_name = f"ChartInsight {chart_type} | ana_{analysis_id[:12]}"
        with _tracer.start_as_current_span(
            span_name,
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                "analysis.id": analysis_id,
                "chart.type": chart_type,
                "operation.type": "chart_insight",
                "llm.model": INSIGHT_MODEL,
            },
        ):
            try:
                # Get hypothesis for context
                hypothesis = self._get_hypothesis(analysis_id)

                # Build prompt based on chart type
                prompt = self._build_prompt_for_chart_type(
                    chart_type, chart_data, hypothesis)

                # Call LLM with gpt-4.1-mini (no reasoning)
                self.logger.info(
                    f"Generating insight for {chart_type} (analysis: {analysis_id})")
                llm_response_str = self.llm.complete_json(
                    messages=[{"role": "user", "content": prompt}],
                    model=INSIGHT_MODEL,
                )

                # Parse JSON string to dict
                llm_response = json.loads(llm_response_str)

                # Extract summary from response
                summary = llm_response.get("resumo_key_findings", "")
                if not summary:
                    # Fallback to other possible field names
                    summary = llm_response.get("summary", str(llm_response))

                # Create ChartInsight
                insight = ChartInsight(
                    analysis_id=analysis_id,
                    chart_type=chart_type,
                    summary=summary,
                    status="completed",
                    model=INSIGHT_MODEL,
                )

                # Store in cache
                self.cache_repo.store_chart_insight(insight)
                self.logger.info(
                    f"Insight generated for {chart_type}: {insight.status}")

                return insight

            except Exception as e:
                self.logger.error(
                    f"Failed to generate insight for {chart_type}: {e}")
                # Create failed insight
                failed_insight = ChartInsight(
                    analysis_id=analysis_id,
                    chart_type=chart_type,
                    summary=f"Falha ao gerar insight: {e}",
                    status="failed",
                    model=INSIGHT_MODEL,
                )
                self.cache_repo.store_chart_insight(failed_insight)
                return failed_insight

    def _create_pending_insight(
        self,
        analysis_id: str,
        chart_type: str,
    ) -> ChartInsight:
        """
        Create a pending insight immediately to return to the client.

        Args:
            analysis_id: Analysis ID
            chart_type: Chart type

        Returns:
            ChartInsight with status="pending"
        """
        pending_insight = ChartInsight(
            analysis_id=analysis_id,
            chart_type=chart_type,
            summary="Gerando insight... Aguarde.",
            status="pending",
            model=INSIGHT_MODEL,
        )
        self.cache_repo.store_chart_insight(pending_insight)
        return pending_insight

    def _build_prompt_for_chart_type(
        self, chart_type: str, chart_data: dict[str, Any], hypothesis: str
    ) -> str:
        """
        Build LLM prompt for specific chart type.

        Args:
            chart_type: Type of chart
            chart_data: Chart data
            hypothesis: Experiment hypothesis for context

        Returns:
            Formatted prompt string
        """
        # Charts with pre-computed cache data (PDP excluded - dynamic with params)
        prompt_builders = {
            "try_vs_success": self._build_prompt_try_vs_success,
            "shap_summary": self._build_prompt_shap_summary,
            "extreme_cases": self._build_prompt_extreme_cases,
            "outliers": self._build_prompt_outliers,
            "pca_scatter": self._build_prompt_pca_scatter,
            "radar_comparison": self._build_prompt_radar_comparison,
        }

        builder = prompt_builders.get(chart_type)
        if builder is None:
            raise ValueError(f"Unknown chart type: {chart_type}")

        return builder(chart_data, hypothesis)

    def _build_prompt_try_vs_success(
        self, chart_data: dict[str, Any], hypothesis: str
    ) -> str:
        """Build prompt for Try vs Success chart."""
        return f"""Analise estes dados do gráfico "Tentativa vs Sucesso" e forneça insights em PORTUGUÊS BRASILEIRO.

**Hipótese:**
{hypothesis}

**Dados do Gráfico:**
{chart_data}

**Sua Tarefa:**
Você é um pesquisador UX analisando dados quantitativos de uma simulação de feature. Sua função é olhar os dados e fazer análises profundas, sem dizer obviedades, nem ficar explicando como o gráfico funciona.

**Diretrizes:**
- A ideia aqui não é dar ideias de melhorias, mas tentar dar clareza de problemas.
- Fale de forma clara e simples, sem complicações desnecessárias.
- SEMPRE em português brasileiro

**Formato de Saída (JSON):**
{{
  "problem_understanding": "Breve descrição do que está sendo testado (≤80 tokens)",
  "trends_observed": "Padrões principais nos dados (≤80 tokens)",
  "resumo_key_findings": "Suas conclusões (>120 E ≤200 tokens)"
}}
"""

    def _build_prompt_shap_summary(
        self, chart_data: dict[str, Any], hypothesis: str
    ) -> str:
        """Build prompt for SHAP Summary chart."""
        return f"""Analise estes dados do gráfico "SHAP Summary" e forneça insights em PORTUGUÊS BRASILEIRO.

**Hipótese:**
{hypothesis}

**Dados do Gráfico:**
{chart_data}

**Sua Tarefa:**
Você é um pesquisador UX analisando dados de importância de features (SHAP). Sua função é explicar quais atributos dos usuários mais influenciam o sucesso/falha, de forma clara e não-técnica.

**Diretrizes:**
- Foque nos problemas revelados, não em sugestões de melhoria.
- Traduza termos técnicos para linguagem de negócio.
- Fale de forma clara e simples.
- SEMPRE em português brasileiro

**Formato de Saída (JSON):**
{{
  "problem_understanding": "O que está sendo medido (≤80 tokens)",
  "trends_observed": "Top 3 atributos mais importantes e seu impacto (≤80 tokens)",
  "resumo_key_findings": "Suas conclusões sobre os drivers de sucesso/falha (>120 E ≤200 tokens)"
}}
"""

    def _build_prompt_pca_scatter(
        self, chart_data: dict[str, Any], hypothesis: str
    ) -> str:
        """Build prompt for PCA Scatter chart."""
        return f"""Analise estes dados do gráfico "PCA Scatter" em PORTUGUÊS BRASILEIRO.

**Hipótese:**
{hypothesis}

**Dados do Gráfico:**
{chart_data}

**Sua Tarefa:**
Você é um pesquisador UX explicando padrões de segmentação de usuários revelados pelo PCA. Descreva os clusters em termos comportamentais, não técnicos.

**Diretrizes:**
- Descreva segmentos em termos de comportamento, não de matemática.
- Foque nos problemas revelados, não em sugestões.
- Fale de forma clara e simples.
- SEMPRE em português brasileiro

**Formato de Saída (JSON):**
{{
  "problem_understanding": "Qual segmentação de usuário está sendo revelada (≤80 tokens)",
  "trends_observed": "Quantos clusters, suas características principais (≤80 tokens)",
  "resumo_key_findings": "Suas conclusões sobre os segmentos e suas diferenças (>120 E ≤200 tokens)"
}}
"""

    def _build_prompt_radar_comparison(
        self, chart_data: dict[str, Any], hypothesis: str
    ) -> str:
        """Build prompt for Radar Comparison chart."""
        return f"""Analise este gráfico de "Comparação Radar" em PORTUGUÊS BRASILEIRO.

**Hipótese:**
{hypothesis}

**Dados do Gráfico:**
{chart_data}

**Sua Tarefa:**
Você é um pesquisador UX comparando perfis de clusters de usuários em múltiplas dimensões (capacidade, motivação, confiança, etc.).

**Diretrizes:**
- Compare clusters em termos de diferenças práticas.
- Foque nos problemas revelados, não em sugestões.
- Fale de forma clara e simples.
- SEMPRE em português brasileiro

**Formato de Saída (JSON):**
{{
  "problem_understanding": "Quais perfis de cluster estão sendo comparados (≤80 tokens)",
  "trends_observed": "Diferenças-chave entre os clusters (≤80 tokens)",
  "resumo_key_findings": "Suas conclusões sobre como os grupos diferem (>120 E ≤200 tokens)"
}}
"""

    def _build_prompt_extreme_cases(
        self, chart_data: dict[str, Any], hypothesis: str
    ) -> str:
        """Build prompt for Extreme Cases chart."""
        return f"""Analise estes dados de "Casos Extremos" em PORTUGUÊS BRASILEIRO.

**Hipótese:**
{hypothesis}

**Dados do Gráfico:**
{chart_data}

**Sua Tarefa:**
Você é um pesquisador UX explicando casos surpreendentes ou contraintuitivos de sucesso/falha. Foque em anomalias que revelam problemas ocultos.

**Diretrizes:**
- Destaque o que é surpreendente ou inesperado.
- Foque nos problemas revelados, não em sugestões.
- Fale de forma clara e simples.
- SEMPRE em português brasileiro

**Formato de Saída (JSON):**
{{
  "problem_understanding": "Quais casos extremos estão sendo examinados (≤80 tokens)",
  "trends_observed": "Padrões em sucessos/falhas inesperados (≤80 tokens)",
  "resumo_key_findings": "Suas conclusões sobre o que os casos extremos revelam (>120 E ≤200 tokens)"
}}
"""

    def _build_prompt_outliers(
        self, chart_data: dict[str, Any], hypothesis: str
    ) -> str:
        """Build prompt for Outliers chart."""
        return f"""Analise estes dados de "Outliers" em PORTUGUÊS BRASILEIRO.

**Hipótese:**
{hypothesis}

**Dados do Gráfico:**
{chart_data}

**Sua Tarefa:**
Você é um pesquisador UX identificando outliers estatísticos no comportamento do usuário. Distingua entre ruído e outliers significativos.

**Diretrizes:**
- Foque em outliers que revelam problemas reais, não ruído estatístico.
- Foque nos problemas revelados, não em sugestões.
- Fale de forma clara e simples.
- SEMPRE em português brasileiro

**Formato de Saída (JSON):**
{{
  "problem_understanding": "Qual comportamento outlier está sendo identificado (≤80 tokens)",
  "trends_observed": "Características dos usuários outliers (≤80 tokens)",
  "resumo_key_findings": "Suas conclusões sobre o que os outliers revelam (>120 E ≤200 tokens)"
}}
"""


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Service instantiation
    total_tests += 1
    try:
        service = InsightService()
        if service.llm is None:
            all_validation_failures.append("LLM client not initialized")
        if service.cache_repo is None:
            all_validation_failures.append("Cache repository not initialized")
    except Exception as e:
        all_validation_failures.append(f"Service instantiation failed: {e}")

    # Test 2: Prompt building for supported chart types (with pre-computed cache)
    total_tests += 1
    try:
        service = InsightService()
        # Only test charts with pre-computed cache data (PDP excluded)
        chart_types = [
            "try_vs_success",
            "shap_summary",
            "extreme_cases",
            "outliers",
            "pca_scatter",
            "radar_comparison",
        ]
        for chart_type in chart_types:
            prompt = service._build_prompt_for_chart_type(
                chart_type, {"test": "data"}, "Hipótese de teste")
            if len(prompt) < 100:
                all_validation_failures.append(
                    f"Prompt too short for {chart_type}")
            if "Hipótese" not in prompt:
                all_validation_failures.append(
                    f"Prompt missing hypothesis for {chart_type}")
            if "resumo_key_findings" not in prompt:
                all_validation_failures.append(
                    f"Prompt missing resumo_key_findings for {chart_type}")
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
        print("InsightService is validated and ready for use")
        sys.exit(0)
