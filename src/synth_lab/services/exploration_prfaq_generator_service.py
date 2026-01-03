"""
Exploration PRFAQ Generator Service for synth-lab.

Generates Press Release / FAQ documents for completed explorations using LLM.
Follows Amazon PRFAQ format with 3 sections: Press Release + FAQ + Recommendations.

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
from synth_lab.repositories.exploration_repository import ExplorationRepository
from synth_lab.services.exploration_utils import get_winning_path

# Phoenix/OpenTelemetry tracer for observability
_tracer = get_tracer("exploration-prfaq-generator")


class ExplorationNotCompletedError(Exception):
    """Raised when trying to generate PRFAQ for incomplete exploration."""

    def __init__(self, exploration_id: str, status: str):
        self.exploration_id = exploration_id
        self.status = status
        super().__init__(
            f"Exploration {exploration_id} is not completed (status={status}). "
            "Only completed explorations can generate PRFAQs."
        )


class PRFAQGenerationInProgressError(Exception):
    """Raised when PRFAQ generation is already in progress."""

    def __init__(self, exploration_id: str):
        self.exploration_id = exploration_id
        super().__init__(f"PRFAQ generation already in progress for exploration {exploration_id}")


class ExplorationPRFAQGeneratorService:
    """Generates PRFAQ for exploration, saves to experiment_documents."""

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
        llm_client: LLMClient | None = None,
    ):
        """
        Initialize PRFAQ generator service.

        Args:
            exploration_repo: Repository for exploration data.
            document_repo: Repository for document storage.
            llm_client: LLM client for content generation.
        """
        self._exploration_repo = exploration_repo
        self._document_repo = document_repo
        self._llm_client = llm_client or get_llm_client()
        self._logger = logger.bind(component="exploration_prfaq_generator")

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

    def generate_for_exploration(
        self,
        exploration_id: str,
    ) -> ExperimentDocument:
        """
        Generate PRFAQ for exploration.

        Args:
            exploration_id: ID of the exploration.

        Returns:
            ExperimentDocument with generated PRFAQ.

        Raises:
            ValueError: If exploration not found.
            ExplorationNotCompletedError: If exploration is not completed.
            PRFAQGenerationInProgressError: If generation already in progress.
        """
        exploration_repo = self._get_exploration_repo()
        document_repo = self._get_document_repo()

        # 1. Get exploration
        exploration = exploration_repo.get_exploration_by_id(exploration_id)
        if exploration is None:
            raise ValueError(f"Exploration {exploration_id} not found")

        with _tracer.start_as_current_span(
            f"Generate Exploration PR-FAQ: {exploration.status.value}",
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                "exploration_id": exploration_id,
                "experiment_id": exploration.experiment_id,
                "status": exploration.status.value,
            },
        ) as span:

            # 2. Validate status
            if exploration.status not in self.COMPLETED_STATUSES:
                raise ExplorationNotCompletedError(exploration_id, exploration.status.value)

            # 3. Check for existing generation in progress
            existing = document_repo.get_by_experiment(
                exploration.experiment_id,
                DocumentType.EXPLORATION_PRFAQ,
                source_id=exploration_id,
            )
            if existing and existing.status == DocumentStatus.GENERATING:
                raise PRFAQGenerationInProgressError(exploration_id)

            # 4. Get winning path
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

            # 5. Create pending document
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
                document_type=DocumentType.EXPLORATION_PRFAQ,
                source_id=exploration_id,
                model="gpt-4o-mini",
            )

            if pending_doc is None:
                raise PRFAQGenerationInProgressError(exploration_id)

            try:
                # 6. Generate content via LLM
                prompt = self._build_prompt(exploration, winning_path)
                messages = [{"role": "user", "content": prompt}]

                content = self._llm_client.complete(
                    messages=messages,
                    temperature=0.7,
                    max_tokens=3000,
                    operation_name="Generate Exploration PRFAQ",
                )

                if span:
                    span.set_attribute("prfaq_length", len(content))
                    span.set_attribute("improvement_percentage", round(improvement, 1))

                # 7. Update document with content
                document_repo.update_status(
                    experiment_id=exploration.experiment_id,
                    document_type=DocumentType.EXPLORATION_PRFAQ,
                    status=DocumentStatus.COMPLETED,
                    source_id=exploration_id,
                    markdown_content=content,
                    metadata=metadata,
                )

                self._logger.info(
                    f"Generated PRFAQ for exploration {exploration_id} "
                    f"(path length: {len(winning_path)}, improvement: {improvement:.1f}%)"
                )

                # Return updated document
                return document_repo.get_by_experiment(
                    exploration.experiment_id,
                    DocumentType.EXPLORATION_PRFAQ,
                    source_id=exploration_id,
                )

            except Exception as e:
                # 8. Mark as failed
                self._logger.error(
                    f"Failed to generate PRFAQ for exploration {exploration_id}: {e}"
                )
                document_repo.update_status(
                    experiment_id=exploration.experiment_id,
                    document_type=DocumentType.EXPLORATION_PRFAQ,
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
    ) -> str:
        """
        Build LLM prompt for PRFAQ generation.

        Args:
            exploration: Exploration entity.
            winning_path: List of nodes from root to best leaf.

        Returns:
            Prompt string for LLM.
        """
        root_node = winning_path[0]
        final_node = winning_path[-1]

        # Format improvements (excluding root)
        improvements = []
        for i, node in enumerate(winning_path[1:], 1):
            prev_rate = winning_path[i - 1].get_success_rate() or 0
            curr_rate = node.get_success_rate() or 0

            improvements.append(
                f"- **{node.action_applied}** ({node.action_category or 'N/A'})\n"
                f"  - Justificativa: {node.rationale or 'N/A'}\n"
                f"  - Taxa de sucesso: {prev_rate:.0%} → {curr_rate:.0%}"
            )

        improvements_text = (
            "\n".join(improvements) if improvements else "Nenhuma melhoria aplicada."
        )

        # Calculate metrics
        baseline_rate = root_node.get_success_rate() or 0
        final_rate = final_node.get_success_rate() or 0
        improvement_pct = (
            ((final_rate - baseline_rate) / baseline_rate * 100) if baseline_rate > 0 else 0
        )

        # Format scorecard comparison
        root_sc = root_node.scorecard_params
        final_sc = final_node.scorecard_params

        return f"""Você é um Product Manager experiente escrevendo um documento PRFAQ (Press Release / FAQ).

## CONTEXTO DA EXPLORAÇÃO

- **Meta**: Alcançar taxa de sucesso >= {exploration.goal.value:.0%}
- **Status Final**: {exploration.status.value}
- **Taxa de Sucesso Inicial**: {baseline_rate:.0%}
- **Taxa de Sucesso Final**: {final_rate:.0%}
- **Melhoria Total**: {improvement_pct:.1f}%

## SCORECARD INICIAL
- Complexidade: {root_sc.complexity:.0%}
- Esforço Inicial: {root_sc.initial_effort:.0%}
- Risco Percebido: {root_sc.perceived_risk:.0%}
- Tempo até Valor: {root_sc.time_to_value:.0%}

## SCORECARD FINAL
- Complexidade: {final_sc.complexity:.0%}
- Esforço Inicial: {final_sc.initial_effort:.0%}
- Risco Percebido: {final_sc.perceived_risk:.0%}
- Tempo até Valor: {final_sc.time_to_value:.0%}

## MELHORIAS APLICADAS
{improvements_text}

## TAREFA

Escreva um documento PRFAQ profissional que formalize as recomendações desta exploração. O documento DEVE ter exatamente 3 seções:

---

# Press Release

Anuncie a versão otimizada do experimento como se já estivesse implementada. Use estilo jornalístico com:
- **Título** chamativo
- **Subtítulo** com a principal métrica de melhoria
- **Corpo** (2-3 parágrafos) descrevendo o que mudou e os benefícios
- **Citação** de um stakeholder fictício sobre o impacto

---

# FAQ (Perguntas Frequentes)

Responda 5 perguntas-chave sobre as mudanças propostas:

1. **Por que essas mudanças específicas foram escolhidas?**
2. **Qual foi o impacto nas métricas de scorecard?**
3. **Que riscos ainda existem?**
4. **Quanto esforço é necessário para implementar?**
5. **Quando veremos resultados?**

---

# Recomendações para Implementação

## Próximos Passos
Liste 3-5 ações concretas para implementar as melhorias.

## Métricas de Sucesso
Liste 2-3 métricas para validar se as melhorias funcionaram.

## Considerações de Longo Prazo
Insights sobre escalabilidade, manutenção e evolução futura.

---

Use formato markdown e mantenha tom executivo mas acessível. Responda em português."""

    def get_prfaq(self, exploration_id: str) -> ExperimentDocument | None:
        """
        Get existing PRFAQ for exploration.

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
            DocumentType.EXPLORATION_PRFAQ,
            source_id=exploration_id,
        )

    def delete_prfaq(self, exploration_id: str) -> bool:
        """
        Delete PRFAQ for exploration.

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
            DocumentType.EXPLORATION_PRFAQ,
            source_id=exploration_id,
        )


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Service instantiation
    total_tests += 1
    try:
        service = ExplorationPRFAQGeneratorService()
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
        if ExplorationPRFAQGeneratorService.COMPLETED_STATUSES != expected:
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

    # Test 4: PRFAQGenerationInProgressError
    total_tests += 1
    try:
        error = PRFAQGenerationInProgressError("expl_12345678")
        if "expl_12345678" not in str(error):
            all_validation_failures.append("Error should include exploration_id")
        if "in progress" not in str(error).lower():
            all_validation_failures.append("Error should mention in progress")
    except Exception as e:
        all_validation_failures.append(f"PRFAQGenerationInProgressError test failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
