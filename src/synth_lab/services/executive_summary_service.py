"""
ExecutiveSummaryService for AI-generated executive summaries.

Synthesizes multiple chart insights into a comprehensive executive summary
using reasoning model. Aggregates insights across all chart types
to provide strategic recommendations.

v16: Now generates markdown output and stores in experiment_documents table.
     Also maintains backward compatibility with analysis_cache for legacy callers.

References:
    - Entity: src/synth_lab/domain/entities/executive_summary.py
    - Entity: src/synth_lab/domain/entities/chart_insight.py
    - Entity: src/synth_lab/domain/entities/experiment_document.py
    - Repository: src/synth_lab/repositories/analysis_cache_repository.py
    - Service: src/synth_lab/services/document_service.py
    - Spec: specs/023-quantitative-ai-insights/spec.md (User Story 2, 3)
    - Config: src/synth_lab/infrastructure/config.py (REASONING_MODEL)

Sample usage:
    from synth_lab.services.executive_summary_service import ExecutiveSummaryService

    service = ExecutiveSummaryService()
    # New: Generate markdown and store in experiment_documents
    markdown = service.generate_markdown_summary("exp_12345678", "ana_12345678")

    # Legacy: Generate and store in analysis_cache (backward compatible)
    summary = service.generate_summary("ana_12345678")

Expected output:
    Markdown string or ExecutiveSummary (legacy)
"""

from loguru import logger
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes

from synth_lab.domain.entities.chart_insight import ChartInsight
from synth_lab.domain.entities.executive_summary import ExecutiveSummary
from synth_lab.domain.entities.experiment_document import DocumentStatus, DocumentType
from synth_lab.infrastructure.config import REASONING_MODEL
from synth_lab.infrastructure.llm_client import LLMClient, get_llm_client
from synth_lab.infrastructure.phoenix_tracing import get_tracer
from synth_lab.repositories.analysis_cache_repository import AnalysisCacheRepository
from synth_lab.services.document_service import DocumentService

_tracer = get_tracer()


def _strip_markdown_fence(content: str) -> str:
    """
    Strip markdown code fence wrapper from LLM response.

    LLMs sometimes wrap markdown in ```markdown ... ``` even when asked not to.
    This function removes that wrapper to get clean markdown.

    Args:
        content: Raw LLM response

    Returns:
        Clean markdown without code fence wrapper
    """
    content = content.strip()
    # Check for ```markdown or ``` at start
    if content.startswith("```markdown"):
        content = content[len("```markdown") :].strip()
    elif content.startswith("```"):
        content = content[3:].strip()

    # Check for ``` at end
    if content.endswith("```"):
        content = content[:-3].strip()

    return content


class ExecutiveSummaryService:
    """Service for generating AI-powered executive summaries."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        cache_repo: AnalysisCacheRepository | None = None,
        document_service: DocumentService | None = None):
        """
        Initialize ExecutiveSummaryService.

        Args:
            llm_client: LLM client for reasoning. Defaults to singleton.
            cache_repo: Cache repository for persistence. Defaults to new instance.
            document_service: Document service for storing in experiment_documents.
        """
        self.llm = llm_client or get_llm_client()
        self.cache_repo = cache_repo or AnalysisCacheRepository()
        self.document_service = document_service or DocumentService()
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
        span_name = f"ExecutiveSummary | ana_{analysis_id[:12]}"
        with _tracer.start_as_current_span(
            span_name,
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                "analysis.id": analysis_id,
                "operation.type": "executive_summary",
                "output.format": "json",
            }):
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
                    model=REASONING_MODEL)

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
                    model=REASONING_MODEL)

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
                    model=REASONING_MODEL)
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

    def generate_markdown_summary(
        self, experiment_id: str, analysis_id: str
    ) -> str:
        """
        Generate executive summary as markdown and store in experiment_documents.

        This is the new v16 method that generates free-form markdown output
        and stores it in the centralized experiment_documents table.

        Args:
            experiment_id: Experiment ID (e.g., "exp_12345678")
            analysis_id: Analysis ID (e.g., "ana_12345678")

        Returns:
            Markdown string with the executive summary

        Raises:
            ValueError: If less than 2 completed insights available
        """
        span_name = f"ExecutiveSummary Markdown | exp_{experiment_id[:12]}"
        with _tracer.start_as_current_span(
            span_name,
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                "experiment.id": experiment_id,
                "analysis.id": analysis_id,
                "operation.type": "executive_summary_markdown",
                "output.format": "markdown",
            }):
            try:
                # Mark as generating (prevents concurrent generation)
                pending = self.document_service.start_generation(
                    experiment_id,
                    DocumentType.EXECUTIVE_SUMMARY,
                    model=REASONING_MODEL)
                if pending is None:
                    # Already generating, check current status
                    status = self.document_service.get_document_status(
                        experiment_id, DocumentType.EXECUTIVE_SUMMARY
                    )
                    if status == DocumentStatus.COMPLETED:
                        return self.document_service.get_markdown(
                            experiment_id, DocumentType.EXECUTIVE_SUMMARY
                        )
                    raise ValueError("Executive summary generation already in progress")

                # Retrieve all insights
                all_insights = self.cache_repo.get_all_chart_insights(analysis_id)
                completed_insights = [
                    i for i in all_insights if i.status == "completed"
                ]

                # Validate minimum insights
                if len(completed_insights) < 2:
                    self.document_service.fail_generation(
                        experiment_id,
                        DocumentType.EXECUTIVE_SUMMARY,
                        f"Need at least 2 completed insights, got {len(completed_insights)}")
                    raise ValueError(
                        f"Need at least 2 completed insights to generate summary, "
                        f"got {len(completed_insights)}"
                    )

                # Build markdown prompt
                prompt = self._build_markdown_synthesis_prompt(completed_insights)

                # Call LLM with reasoning model
                self.logger.info(
                    f"Generating markdown executive summary for {experiment_id} "
                    f"from {len(completed_insights)} insights"
                )
                markdown_content = self.llm.complete(
                    messages=[{"role": "user", "content": prompt}],
                    model=REASONING_MODEL)

                # Strip any markdown code fence wrapper from LLM response
                markdown_content = _strip_markdown_fence(markdown_content)

                # Determine status (partial if some insights failed)
                status_str = (
                    "partial"
                    if len(completed_insights) < len(all_insights)
                    else "completed"
                )

                # Store in experiment_documents
                self.document_service.complete_generation(
                    experiment_id,
                    DocumentType.EXECUTIVE_SUMMARY,
                    markdown_content,
                    metadata={
                        "analysis_id": analysis_id,
                        "included_chart_types": [i.chart_type for i in completed_insights],
                        "total_insights": len(all_insights),
                        "completed_insights": len(completed_insights),
                        "generation_status": status_str,
                        "model": REASONING_MODEL,
                    })

                self.logger.info(
                    f"Markdown executive summary generated: {status_str} "
                    f"({len(markdown_content)} chars)"
                )
                return markdown_content

            except ValueError:
                raise  # Re-raise validation errors
            except Exception as e:
                self.logger.error(f"Failed to generate markdown executive summary: {e}")
                # Mark as failed
                self.document_service.fail_generation(
                    experiment_id,
                    DocumentType.EXECUTIVE_SUMMARY,
                    str(e))
                raise

    async def generate_markdown_summary_background(
        self, experiment_id: str, analysis_id: str
    ) -> None:
        """
        Background task wrapper for generating executive summary markdown.

        This method is designed to be called as a FastAPI background task.
        It catches all exceptions and handles them internally without re-raising,
        as background tasks should not propagate exceptions to the caller.

        Args:
            experiment_id: Experiment ID (e.g., "exp_12345678")
            analysis_id: Analysis ID (e.g., "ana_12345678")
        """
        try:
            self.generate_markdown_summary(experiment_id, analysis_id)
            self.logger.info(f"Executive summary generated for {experiment_id}")
        except Exception as e:
            # Error already logged and document marked as failed in generate_markdown_summary
            self.logger.error(
                f"Background task: Failed to generate executive summary for {experiment_id}: {e}"
            )

    def _build_markdown_synthesis_prompt(self, insights: list[ChartInsight]) -> str:
        """
        Build LLM prompt to synthesize multiple insights into markdown format.

        Args:
            insights: List of completed chart insights

        Returns:
            Formatted synthesis prompt for markdown output
        """
        # Build insight summaries
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

**Formato de Saída (Markdown):**
Gere um documento markdown bem estruturado com as seguintes seções:

## Visão Geral
O que foi testado e resultados gerais (≤200 palavras). Sintetize insights de Tentativa vs Sucesso e distribuição de resultados.

## Explicabilidade
Principais drivers e impactos de features (≤200 palavras). Sintetize insights SHAP e PDP sobre o que influencia o sucesso.

## Segmentação
Grupos de usuários e padrões comportamentais (≤200 palavras). Sintetize insights PCA e radar sobre segmentos de usuários.

## Casos Extremos
Surpresas, anomalias, descobertas inesperadas (≤200 palavras). Sintetize insights de casos extremos e outliers.

## Recomendações
Liste 2-3 recomendações acionáveis em formato de bullet points:
- **Recomendação 1:** [Descrição clara e acionável]
- **Recomendação 2:** [Descrição clara e acionável]
- **Recomendação 3 (opcional):** [Apenas se fortemente suportada pelos insights]

**Diretrizes:**
- 2-3 recomendações obrigatórias (não mais de 3)
- Sintetize entre insights - não apenas liste descobertas individuais
- Foque em implicações estratégicas para decisões de produto
- Priorize recomendações por impacto e viabilidade
- Identifique padrões que emergem de múltiplos tipos de gráficos
- Destaque o insight mais importante de cada categoria
- Faça recomendações concretas e acionáveis
- SEMPRE responda em português brasileiro
- NÃO inclua código, JSON ou formatação estruturada - apenas markdown limpo

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
        if service.document_service is None:
            all_validation_failures.append("Document service not initialized")
    except Exception as e:
        all_validation_failures.append(f"Service instantiation failed: {e}")

    # Test 2: Legacy JSON prompt building
    total_tests += 1
    try:
        service = ExecutiveSummaryService()
        sample_insights = [
            ChartInsight(
                analysis_id="ana_12345678",
                chart_type=f"chart_{i}",
                summary=f"Insight resumido número {i} sobre o gráfico",
                status="completed")
            for i in range(3)
        ]
        prompt = service._build_synthesis_prompt(sample_insights)
        if len(prompt) < 200:
            all_validation_failures.append("Synthesis prompt too short")
        if "overview" not in prompt or "recommendations" not in prompt:
            all_validation_failures.append("Prompt missing required sections")
    except Exception as e:
        all_validation_failures.append(f"Legacy prompt building failed: {e}")

    # Test 3: New markdown prompt building
    total_tests += 1
    try:
        service = ExecutiveSummaryService()
        sample_insights = [
            ChartInsight(
                analysis_id="ana_12345678",
                chart_type=f"chart_{i}",
                summary=f"Insight resumido número {i} sobre o gráfico",
                status="completed")
            for i in range(3)
        ]
        prompt = service._build_markdown_synthesis_prompt(sample_insights)
        if len(prompt) < 200:
            all_validation_failures.append("Markdown prompt too short")
        # Check for markdown format instructions
        if "## Visão Geral" not in prompt:
            all_validation_failures.append("Markdown prompt missing '## Visão Geral'")
        if "## Recomendações" not in prompt:
            all_validation_failures.append("Markdown prompt missing '## Recomendações'")
        if "JSON" not in prompt:
            all_validation_failures.append("Markdown prompt should mention to avoid JSON")
    except Exception as e:
        all_validation_failures.append(f"Markdown prompt building failed: {e}")

    # Test 4: DocumentService integration
    total_tests += 1
    try:
        doc_service = DocumentService()
        service = ExecutiveSummaryService(document_service=doc_service)
        if service.document_service is not doc_service:
            all_validation_failures.append("Document service injection failed")
    except Exception as e:
        all_validation_failures.append(f"DocumentService integration failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(
            f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(
            f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results"
        )
        print("ExecutiveSummaryService is validated and ready for use")
        sys.exit(0)
