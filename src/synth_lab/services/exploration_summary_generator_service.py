"""
Exploration Summary Generator Service for synth-lab.

Generates narrative summaries for completed explorations using LLM.
Summaries describe the final optimized state after applying winning path actions.

Saves documents to experiment_documents table using exploration.experiment_id.

References:
    - Spec: specs/028-exploration-summary/spec.md
    - Data model: specs/028-exploration-summary/data-model.md
"""


from loguru import logger
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes

from synth_lab.domain.entities.experiment_document import (
    DocumentStatus,
    DocumentType,
    ExperimentDocument,
)
from synth_lab.domain.entities.exploration import Exploration, ExplorationStatus
from synth_lab.domain.entities.scenario_node import ScenarioNode
from synth_lab.infrastructure.llm_client import LLMClient, get_llm_client
from synth_lab.infrastructure.phoenix_tracing import get_tracer
from synth_lab.repositories.experiment_document_repository import (
    ExperimentDocumentRepository,
)
from synth_lab.repositories.experiment_material_repository import (
    ExperimentMaterialRepository,
)
from synth_lab.repositories.experiment_repository import ExperimentRepository
from synth_lab.repositories.exploration_repository import ExplorationRepository
from synth_lab.services.exploration_utils import get_winning_path
from synth_lab.services.materials_context import format_materials_for_prompt
from synth_lab.services.summary_image_service import (
    SummaryImageService,
    get_summary_image_service,
)

# Phoenix/OpenTelemetry tracer for observability
_tracer = get_tracer("exploration-summary-generator")


class ExplorationNotCompletedError(Exception):
    """Raised when trying to generate summary for incomplete exploration."""

    def __init__(self, exploration_id: str, status: str):
        self.exploration_id = exploration_id
        self.status = status
        super().__init__(
            f"Exploration {exploration_id} is not completed (status={status}). "
            "Only completed explorations can generate summaries."
        )


class SummaryGenerationInProgressError(Exception):
    """Raised when summary generation is already in progress."""

    def __init__(self, exploration_id: str):
        self.exploration_id = exploration_id
        super().__init__(f"Summary generation already in progress for exploration {exploration_id}")


class ExplorationSummaryGeneratorService:
    """Generates summary for exploration, saves to experiment_documents."""

    # Completion statuses that allow document generation
    COMPLETED_STATUSES = {
        ExplorationStatus.GOAL_ACHIEVED,
        ExplorationStatus.DEPTH_LIMIT_REACHED,
        ExplorationStatus.COST_LIMIT_REACHED,
    }

    def __init__(
        self,
        exploration_repo: ExplorationRepository | None = None,
        document_repo: ExperimentDocumentRepository | None = None,
        experiment_repo: ExperimentRepository | None = None,
        llm_client: LLMClient | None = None,
        image_service: SummaryImageService | None = None,
    ):
        """
        Initialize summary generator service.

        Args:
            exploration_repo: Repository for exploration data.
            document_repo: Repository for document storage.
            experiment_repo: Repository for experiment data.
            llm_client: LLM client for content generation.
            image_service: Service for generating summary images.
        """
        self._exploration_repo = exploration_repo
        self._document_repo = document_repo
        self._experiment_repo = experiment_repo
        self._llm_client = llm_client or get_llm_client()
        self._image_service = image_service
        self._logger = logger.bind(component="exploration_summary_generator")

    def _get_image_service(self) -> SummaryImageService:
        """Get or create image service."""
        if self._image_service is None:
            self._image_service = get_summary_image_service()
        return self._image_service

    def _get_exploration_repo(self) -> ExplorationRepository:
        """Get or create exploration repository."""
        if self._exploration_repo is None:
            self._exploration_repo = ExplorationRepository()
        return self._exploration_repo

    def _get_document_repo(self) -> ExperimentDocumentRepository:
        """Get or create document repository."""
        if self._document_repo is None:
            self._document_repo = ExperimentDocumentRepository()
        return self._document_repo

    def _get_experiment_repo(self) -> ExperimentRepository:
        """Get or create experiment repository."""
        if self._experiment_repo is None:
            self._experiment_repo = ExperimentRepository()
        return self._experiment_repo

    def generate_for_exploration(
        self,
        exploration_id: str,
    ) -> ExperimentDocument:
        """
        Generate summary for exploration.

        Args:
            exploration_id: ID of the exploration.

        Returns:
            ExperimentDocument with generated summary.

        Raises:
            ValueError: If exploration not found.
            ExplorationNotCompletedError: If exploration is not completed.
            SummaryGenerationInProgressError: If generation already in progress.
        """
        exploration_repo = self._get_exploration_repo()
        document_repo = self._get_document_repo()
        experiment_repo = self._get_experiment_repo()

        # 1. Get exploration
        exploration = exploration_repo.get_exploration_by_id(exploration_id)
        if exploration is None:
            raise ValueError(f"Exploration {exploration_id} not found")

        # 2. Get experiment name
        experiment = experiment_repo.get_by_id(exploration.experiment_id)
        experiment_name = experiment.name if experiment else "Experimento"

        # 2.5 Fetch materials if experiment exists
        materials = None
        if experiment:
            self._logger.debug(f"Fetching materials for experiment {exploration.experiment_id}")
            material_repo = ExperimentMaterialRepository()
            materials = material_repo.list_by_experiment(exploration.experiment_id)
            if materials:
                self._logger.info(
                    f"Loaded {len(materials)} materials for experiment {exploration.experiment_id}"
                )

        with _tracer.start_as_current_span(
            f"Generate Exploration Summary: {exploration.status.value}",
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                "exploration_id": exploration_id,
                "experiment_id": exploration.experiment_id,
                "status": exploration.status.value,
                "materials_count": len(materials) if materials else 0,
            },
        ) as span:

            # 3. Validate status
            if exploration.status not in self.COMPLETED_STATUSES:
                raise ExplorationNotCompletedError(exploration_id, exploration.status.value)

            # 4. Check for existing generation in progress
            existing = document_repo.get_by_experiment(
                exploration.experiment_id,
                DocumentType.EXPLORATION_SUMMARY,
                source_id=exploration_id,
            )
            if existing and existing.status == DocumentStatus.GENERATING:
                raise SummaryGenerationInProgressError(exploration_id)

            # 5. Get winning path
            winning_path = get_winning_path(exploration_repo, exploration_id)
            span.set_attribute("path_length", len(winning_path))

            if not winning_path:
                raise ValueError(f"No nodes found for exploration {exploration_id}")

            root_node = winning_path[0]
            final_node = winning_path[-1]

            # Calculate improvement metrics
            baseline_rate = root_node.get_success_rate() or 0
            final_rate = final_node.get_success_rate() or 0
            improvement = (
                ((final_rate - baseline_rate) / baseline_rate * 100) if baseline_rate > 0 else 0
            )

            # 6. Create pending document
            metadata = {
                "source": "exploration",
                "exploration_id": exploration_id,
                "winning_path_nodes": [n.id for n in winning_path],
                "path_length": len(winning_path),
                "baseline_success_rate": baseline_rate,
                "final_success_rate": final_rate,
                "improvement_percentage": round(improvement, 1),
            }

            pending_doc = document_repo.create_pending(
                experiment_id=exploration.experiment_id,
                document_type=DocumentType.EXPLORATION_SUMMARY,
                source_id=exploration_id,
                model="gpt-4o-mini",
            )

            if pending_doc is None:
                raise SummaryGenerationInProgressError(exploration_id)

            try:
                # 7. Generate content via LLM
                prompt = self._build_prompt(
                    exploration, winning_path, experiment_name, materials=materials
                )
                messages = [{"role": "user", "content": prompt}]

                content = self._llm_client.complete(
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2000,
                    operation_name="Generate Exploration Summary",
                )

                if span:
                    span.set_attribute("summary_length", len(content))
                    span.set_attribute("improvement_percentage", round(improvement, 1))

                # 8. Generate summary image and append to content
                image_service = self._get_image_service()
                content = image_service.generate_and_append_image(
                    markdown_content=content,
                    experiment_id=exploration.experiment_id,
                    doc_id=pending_doc.id,
                    materials=materials,
                )

                # 9. Update document with content
                document_repo.update_status(
                    experiment_id=exploration.experiment_id,
                    document_type=DocumentType.EXPLORATION_SUMMARY,
                    status=DocumentStatus.COMPLETED,
                    source_id=exploration_id,
                    markdown_content=content,
                    metadata=metadata,
                )

                self._logger.info(
                    f"Generated summary for exploration {exploration_id} "
                    f"(path length: {len(winning_path)}, improvement: {improvement:.1f}%)"
                )

                # Return updated document
                return document_repo.get_by_experiment(
                    exploration.experiment_id,
                    DocumentType.EXPLORATION_SUMMARY,
                    source_id=exploration_id,
                )

            except Exception as e:
                # 10. Mark as failed
                self._logger.error(
                    f"Failed to generate summary for exploration {exploration_id}: {e}"
                )
                document_repo.update_status(
                    experiment_id=exploration.experiment_id,
                    document_type=DocumentType.EXPLORATION_SUMMARY,
                    status=DocumentStatus.FAILED,
                    source_id=exploration_id,
                    error_message=str(e),
                    metadata=metadata,
                )
                raise

    def _build_prompt(
        self,
        exploration: Exploration,
        winning_path: list[ScenarioNode],
        experiment_name: str,
        materials: list | None = None,
    ) -> str:
        """
        Build LLM prompt for summary generation.

        Args:
            exploration: Exploration entity.
            winning_path: List of nodes from root to best leaf.
            experiment_name: Name of the experiment.
            materials: Optional list of ExperimentMaterial objects to include.

        Returns:
            Prompt string for LLM.
        """
        root_node = winning_path[0]
        final_node = winning_path[-1]

        # Calculate improvement metrics
        baseline_rate = root_node.get_success_rate() or 0
        final_rate = final_node.get_success_rate() or 0
        improvement_pct = (
            ((final_rate - baseline_rate) / baseline_rate * 100) if baseline_rate > 0 else 0
        )

        # Format improvements (excluding root)
        improvements = []
        for i, node in enumerate(winning_path[1:], 1):
            prev_rate = winning_path[i - 1].get_success_rate() or 0
            curr_rate = node.get_success_rate() or 0
            delta = curr_rate - prev_rate

            improvements.append(
                f"- **{node.action_applied}**\n"
                f"  - Categoria: {node.action_category or 'N/A'}\n"
                f"  - Justificativa: {node.rationale or 'N/A'}\n"
                f"  - Impacto: Taxa de sucesso {prev_rate:.0%} → {curr_rate:.0%} "
                f"({'+' if delta >= 0 else ''}{delta:.0%})"
            )

        improvements_text = (
            "\n".join(improvements) if improvements else "Nenhuma melhoria aplicada."
        )

        # Format scorecard comparison
        root_sc = root_node.scorecard_params
        final_sc = final_node.scorecard_params

        # Calculate scorecard deltas
        complexity_delta = final_sc.complexity - root_sc.complexity
        effort_delta = final_sc.initial_effort - root_sc.initial_effort
        risk_delta = final_sc.perceived_risk - root_sc.perceived_risk
        ttv_delta = final_sc.time_to_value - root_sc.time_to_value

        # Format delta strings for display
        complexity_str = f"{'+' if complexity_delta >= 0 else ''}{complexity_delta:.0%}"
        effort_str = f"{'+' if effort_delta >= 0 else ''}{effort_delta:.0%}"
        risk_str = f"{'+' if risk_delta >= 0 else ''}{risk_delta:.0%}"
        ttv_str = f"{'+' if ttv_delta >= 0 else ''}{ttv_delta:.0%}"
        improvement_str = f"{'+' if improvement_pct >= 0 else ''}{improvement_pct:.1f}%"

        scorecard_comparison = f"""
**Baseline**:
- Complexidade: {root_sc.complexity:.0%}
- Esforço Inicial: {root_sc.initial_effort:.0%}
- Risco Percebido: {root_sc.perceived_risk:.0%}
- Tempo até Valor: {root_sc.time_to_value:.0%}
- Taxa de Sucesso: {baseline_rate:.0%}

**Resultado Final**:
- Complexidade: {final_sc.complexity:.0%} ({complexity_str})
- Esforço Inicial: {final_sc.initial_effort:.0%} ({effort_str})
- Risco Percebido: {final_sc.perceived_risk:.0%} ({risk_str})
- Tempo até Valor: {final_sc.time_to_value:.0%} ({ttv_str})
- Taxa de Sucesso: {final_rate:.0%} ({improvement_str})
"""

        # Format materials section if provided
        materials_section = ""
        if materials:
            materials_formatted = format_materials_for_prompt(
                materials=materials,
                context="exploration",
                include_tool_instructions=False  # Summaries use metadata only
            )
            if materials_formatted:
                materials_section = f"\n{materials_formatted}\n"

        return f"""Você é um especialista em UX Research e Product Management.

## CONTEXTO DA EXPLORAÇÃO

- **Experimento**: {experiment_name}
- **Meta**: Alcançar taxa de sucesso >= {exploration.goal.value:.0%}
- **Status Final**: {exploration.status.value}
- **Melhoria Total**: {improvement_pct:.1f}% (de {baseline_rate:.0%} para {final_rate:.0%})
- **Profundidade Explorada**: {len(winning_path)} níveis
- **Total de Nós Explorados**: {exploration.total_nodes}

## COMPARAÇÃO DE SCORECARD
{scorecard_comparison}
{materials_section}
## MELHORIAS APLICADAS NO CAMINHO VENCEDOR
{improvements_text}

## TAREFA

Escreva uma síntese profissional descrevendo como o experimento ficaria APÓS a
aplicação de todas essas melhorias.

**IMPORTANTE**: NÃO descreva as melhorias como passos sequenciais ("primeiro
fazer X, depois Y"). Em vez disso, descreva o estado final integrado do
experimento otimizado.

## DIRETRIZES DE ANÁLISE

1. **Foque no Estado Final**: Descreva a experiência otimizada como se já
   estivesse implementada
2. **Use Dados Concretos**: Cite as métricas de scorecard e taxa de sucesso
3. **Identifique Trade-offs**: Onde houve ganhos e onde houve custos (ex: menor
   complexidade vs maior esforço)
4. **Seja Específico**: Use detalhes das ações aplicadas, não generalidades

## FORMATO DE SAÍDA

Estruture sua resposta em Markdown com EXATAMENTE estas seções:

# Síntese de Exploração: {experiment_name}

## Resumo Executivo
(2-3 parágrafos descrevendo o estado final otimizado, destacando a melhoria de
{improvement_pct:.1f}% na taxa de sucesso)

## Características Principais
(4-6 aspectos-chave que definem esta versão melhorada, com referências
específicas às ações aplicadas)

## Análise de Métricas
(Discussão detalhada das mudanças no scorecard: o que melhorou, o que piorou,
e por quê)

## Trade-offs Identificados
(Onde houve ganhos em uma dimensão mas custos em outra - ex: redução de
complexidade aumentou esforço inicial)

## Impacto Esperado
(Como essas mudanças afetam a experiência do usuário e os resultados do
negócio, com base nas evidências das melhorias)

---

Responda em português, com tom profissional mas acessível. Use os dados
numéricos fornecidos para embasar suas afirmações."""

    def get_summary(self, exploration_id: str) -> ExperimentDocument | None:
        """
        Get existing summary for exploration.

        Args:
            exploration_id: Exploration ID.

        Returns:
            ExperimentDocument if found, None otherwise.
        """
        exploration_repo = self._get_exploration_repo()
        document_repo = self._get_document_repo()

        exploration = exploration_repo.get_exploration_by_id(exploration_id)
        if exploration is None:
            return None

        return document_repo.get_by_experiment(
            exploration.experiment_id,
            DocumentType.EXPLORATION_SUMMARY,
            source_id=exploration_id,
        )

    def delete_summary(self, exploration_id: str) -> bool:
        """
        Delete summary for exploration.

        Args:
            exploration_id: Exploration ID.

        Returns:
            True if deleted, False if not found.
        """
        exploration_repo = self._get_exploration_repo()
        document_repo = self._get_document_repo()

        exploration = exploration_repo.get_exploration_by_id(exploration_id)
        if exploration is None:
            return False

        return document_repo.delete(
            exploration.experiment_id,
            DocumentType.EXPLORATION_SUMMARY,
            source_id=exploration_id,
        )


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Service instantiation
    total_tests += 1
    try:
        service = ExplorationSummaryGeneratorService()
        if service._llm_client is None:
            all_validation_failures.append("LLM client should be initialized")
    except Exception as e:
        all_validation_failures.append(f"Service instantiation failed: {e}")

    # Test 2: COMPLETED_STATUSES
    total_tests += 1
    try:
        expected = {
            ExplorationStatus.GOAL_ACHIEVED,
            ExplorationStatus.DEPTH_LIMIT_REACHED,
            ExplorationStatus.COST_LIMIT_REACHED,
        }
        if ExplorationSummaryGeneratorService.COMPLETED_STATUSES != expected:
            all_validation_failures.append("COMPLETED_STATUSES mismatch")
    except Exception as e:
        all_validation_failures.append(f"COMPLETED_STATUSES test failed: {e}")

    # Test 3: ExplorationNotCompletedError
    total_tests += 1
    try:
        error = ExplorationNotCompletedError("expl_12345678", "running")
        if "expl_12345678" not in str(error):
            all_validation_failures.append("Error should include exploration_id")
        if "running" not in str(error):
            all_validation_failures.append("Error should include status")
    except Exception as e:
        all_validation_failures.append(f"ExplorationNotCompletedError test failed: {e}")

    # Test 4: SummaryGenerationInProgressError
    total_tests += 1
    try:
        error = SummaryGenerationInProgressError("expl_12345678")
        if "expl_12345678" not in str(error):
            all_validation_failures.append("Error should include exploration_id")
        if "in progress" not in str(error).lower():
            all_validation_failures.append("Error should mention in progress")
    except Exception as e:
        all_validation_failures.append(f"SummaryGenerationInProgressError test failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
