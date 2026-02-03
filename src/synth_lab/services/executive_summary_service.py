"""
ExecutiveSummaryService for AI-generated executive summaries.

Synthesizes multiple chart insights into a comprehensive executive summary
using reasoning model. Aggregates insights across all chart types
to provide strategic recommendations.

Generates markdown output and stores in experiment_documents table.
Includes experiment context (name, hypothesis) for specific, non-generic summaries.

References:
    - Entity: src/synth_lab/domain/entities/chart_insight.py
    - Entity: src/synth_lab/domain/entities/experiment_document.py
    - Repository: src/synth_lab/repositories/analysis_cache_repository.py
    - Repository: src/synth_lab/repositories/experiment_repository.py
    - Service: src/synth_lab/services/document_service.py
    - Spec: specs/023-quantitative-ai-insights/spec.md (User Story 2, 3)
    - Config: src/synth_lab/infrastructure/config.py (REASONING_MODEL)

Sample usage:
    from synth_lab.services.executive_summary_service import ExecutiveSummaryService

    service = ExecutiveSummaryService()
    markdown = service.generate_markdown_summary("exp_12345678", "ana_12345678")

Expected output:
    Markdown string with executive summary contextualized for the experiment
"""

from loguru import logger
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes

from synth_lab.domain.entities.chart_insight import ChartInsight
from synth_lab.domain.entities.experiment import Experiment
from synth_lab.domain.entities.experiment_document import DocumentStatus, DocumentType
from synth_lab.infrastructure.config import REASONING_MODEL
from synth_lab.infrastructure.llm_client import LLMClient, get_llm_client
from synth_lab.infrastructure.phoenix_tracing import get_tracer
from synth_lab.repositories.analysis_cache_repository import AnalysisCacheRepository
from synth_lab.repositories.experiment_repository import ExperimentRepository
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
        document_service: DocumentService | None = None,
        experiment_repo: ExperimentRepository | None = None):
        """
        Initialize ExecutiveSummaryService.

        Args:
            llm_client: LLM client for reasoning. Defaults to singleton.
            cache_repo: Cache repository for persistence. Defaults to new instance.
            document_service: Document service for storing in experiment_documents.
            experiment_repo: Experiment repository for fetching experiment context.
        """
        self.llm = llm_client or get_llm_client()
        self.cache_repo = cache_repo or AnalysisCacheRepository()
        self.document_service = document_service or DocumentService()
        self.experiment_repo = experiment_repo or ExperimentRepository()
        self.logger = logger.bind(component="executive_summary_service")

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

                # Fetch experiment context for the prompt
                experiment = self.experiment_repo.get_by_id(experiment_id)

                # Build markdown prompt with experiment context
                prompt = self._build_markdown_synthesis_prompt(
                    completed_insights, experiment
                )

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

    def _build_markdown_synthesis_prompt(
        self,
        insights: list[ChartInsight],
        experiment: Experiment | None = None,
    ) -> str:
        """
        Build LLM prompt to synthesize multiple insights into markdown format.

        Args:
            insights: List of completed chart insights
            experiment: Experiment entity with context (name, hypothesis, description)

        Returns:
            Formatted synthesis prompt for markdown output
        """
        # Build insight summaries
        insight_texts = []
        for insight in insights:
            insight_text = f"""**{insight.chart_type}:** {insight.summary}"""
            insight_texts.append(insight_text)

        all_insights_text = "\n\n".join(insight_texts)

        # Build experiment context section
        experiment_context = ""
        if experiment:
            feature_name = experiment.name
            hypothesis = experiment.hypothesis
            description = experiment.description or ""
            scorecard_description = ""
            if experiment.scorecard_data:
                scorecard_description = experiment.scorecard_data.description_text

            experiment_context = f"""
**Contexto do Experimento:**
- **Feature/Funcionalidade:** {feature_name}
- **Hipótese sendo testada:** {hypothesis}
- **Descrição adicional:** {description or scorecard_description or "(não especificada)"}

IMPORTANTE: Todas as seções do resumo executivo devem ser contextualizadas especificamente para este experimento. Mencione a feature "{feature_name}" e relacione os resultados diretamente com a hipótese "{hypothesis}". Evite linguagem genérica - seja específico sobre o que está sendo testado e o que os resultados significam para esta feature em particular.
"""

        return f"""Você é um pesquisador UX criando um resumo executivo a partir de insights de análise quantitativa.
{experiment_context}
**Sua Tarefa:**
Sintetize os seguintes {len(insights)} insights de gráficos em um resumo executivo abrangente para stakeholders de produto. O resumo deve ser específico e contextualizado para o experimento sendo analisado.

**Todos os Insights:**
{all_insights_text}

**Formato de Saída (Markdown):**
Gere um documento markdown bem estruturado com as seguintes seções:

## Visão Geral
O que foi testado especificamente neste experimento e quais foram os resultados gerais (≤200 palavras). Mencione explicitamente a feature/funcionalidade testada e como ela se comportou. Sintetize insights de Tentativa vs Sucesso e distribuição de resultados no contexto desta hipótese.

## Explicabilidade
Quais características dos usuários ou do contexto mais influenciam o sucesso no uso desta feature específica (≤200 palavras). Relacione os drivers identificados (SHAP/PDP) com as particularidades da funcionalidade sendo testada.

## Segmentação
Quais grupos de usuários se destacam em relação ao uso desta feature (≤200 palavras). Descreva os segmentos em termos de como eles interagem especificamente com a funcionalidade testada, não apenas em termos genéricos.

## Casos Extremos
Descobertas surpreendentes ou inesperadas no contexto desta feature (≤200 palavras). O que os outliers e casos extremos revelam especificamente sobre as limitações ou oportunidades desta funcionalidade?

## Recomendações
Liste 2-3 recomendações acionáveis específicas para melhorar esta feature:
- **Recomendação 1:** [Ação específica relacionada à feature testada]
- **Recomendação 2:** [Ação específica relacionada à feature testada]
- **Recomendação 3 (opcional):** [Apenas se fortemente suportada pelos insights]

**Diretrizes:**
- SEJA ESPECÍFICO: sempre mencione a feature/funcionalidade sendo testada pelo nome
- CONTEXTUALIZE: relacione cada descoberta com a hipótese do experimento
- EVITE GENÉRICO: não use frases que poderiam se aplicar a qualquer experimento
- 2-3 recomendações obrigatórias (não mais de 3)
- Sintetize entre insights - não apenas liste descobertas individuais
- Foque em implicações estratégicas para decisões sobre ESTA feature
- Priorize recomendações por impacto e viabilidade
- Faça recomendações concretas e acionáveis para ESTA funcionalidade
- SEMPRE responda em português brasileiro
- NÃO inclua código, JSON ou formatação estruturada - apenas markdown limpo

**Síntese Entre Insights:**
- Conecte descobertas entre gráficos no contexto desta feature específica
- Identifique quais segmentos de usuário têm mais dificuldade ou sucesso com ESTA funcionalidade
- Priorize recomendações baseado em tamanho do segmento × impacto no sucesso DESTA feature
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
        if service.experiment_repo is None:
            all_validation_failures.append("Experiment repository not initialized")
    except Exception as e:
        all_validation_failures.append(f"Service instantiation failed: {e}")

    # Test 2: Markdown prompt building (without experiment context)
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

    # Test 3: Markdown prompt with experiment context
    total_tests += 1
    try:
        from synth_lab.domain.entities.experiment import (
            Experiment,
            ScorecardData,
            ScorecardDimension,
        )

        service = ExecutiveSummaryService()
        sample_insights = [
            ChartInsight(
                analysis_id="ana_12345678",
                chart_type="try_vs_success",
                summary="70% dos usuários tentaram a funcionalidade",
                status="completed"),
            ChartInsight(
                analysis_id="ana_12345678",
                chart_type="shap_summary",
                summary="Alfabetização digital é o principal driver",
                status="completed"),
        ]
        sample_experiment = Experiment(
            id="exp_12345678",
            name="Entrega Agendada",
            hypothesis="Usuários preferem agendar entregas para horários específicos",
            description="Funcionalidade de delivery com agendamento",
            scorecard_data=ScorecardData(
                feature_name="Entrega Agendada",
                description_text="Permite agendar entregas para horários específicos",
                complexity=ScorecardDimension(score=0.3),
                initial_effort=ScorecardDimension(score=0.4),
                perceived_risk=ScorecardDimension(score=0.2),
                time_to_value=ScorecardDimension(score=0.6),
            ),
        )
        prompt = service._build_markdown_synthesis_prompt(sample_insights, sample_experiment)
        # Check that experiment context is included
        if "Entrega Agendada" not in prompt:
            all_validation_failures.append("Prompt should include experiment name")
        if "agendar entregas" not in prompt:
            all_validation_failures.append("Prompt should include hypothesis")
        if "Contexto do Experimento" not in prompt:
            all_validation_failures.append("Prompt should include context section")
        if "SEJA ESPECÍFICO" not in prompt:
            all_validation_failures.append("Prompt should have specificity guidelines")
    except Exception as e:
        all_validation_failures.append(f"Markdown prompt with experiment failed: {e}")

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
