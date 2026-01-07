"""
Research PRFAQ Generator Service for synth-lab.

Generates Press Release / FAQ documents for completed research executions using LLM.
Follows Amazon PRFAQ format with Press Release + FAQ sections.

Saves documents to experiment_documents table using execution.experiment_id.

References:
    - Pattern: exploration_prfaq_generator_service.py
    - Generator: services/research_prfaq/generator.py
"""

from loguru import logger
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes

from synth_lab.domain.entities.experiment_document import (
    DocumentStatus,
    DocumentType,
    ExperimentDocument,
)
from synth_lab.infrastructure.phoenix_tracing import get_tracer
from synth_lab.repositories.experiment_document_repository import (
    ExperimentDocumentRepository,
)
from synth_lab.repositories.research_repository import ResearchRepository
from synth_lab.services.research_prfaq.generator import generate_prfaq_from_content

# Phoenix/OpenTelemetry tracer for observability
_tracer = get_tracer("research-prfaq-generator")


class SummaryNotFoundError(Exception):
    """Raised when summary is required but not found."""

    def __init__(self, exec_id: str):
        self.exec_id = exec_id
        super().__init__(
            f"Summary not found for execution {exec_id}. "
            "Generate a summary before creating PRFAQ."
        )


class NotLinkedToExperimentError(Exception):
    """Raised when execution is not linked to an experiment."""

    def __init__(self, exec_id: str):
        self.exec_id = exec_id
        super().__init__(f"Execution {exec_id} is not linked to an experiment.")


class PRFAQGenerationInProgressError(Exception):
    """Raised when PRFAQ generation is already in progress."""

    def __init__(self, exec_id: str):
        self.exec_id = exec_id
        super().__init__(f"PRFAQ generation already in progress for execution {exec_id}")


class ResearchPRFAQGeneratorService:
    """Generates PRFAQ for research execution, saves to experiment_documents."""

    def __init__(
        self,
        research_repo: ResearchRepository | None = None,
        document_repo: ExperimentDocumentRepository | None = None,
    ):
        """
        Initialize PRFAQ generator service.

        Args:
            research_repo: Repository for research execution data.
            document_repo: Repository for document storage.
        """
        self._research_repo = research_repo
        self._document_repo = document_repo
        self._logger = logger.bind(component="research_prfaq_generator")

    def _get_research_repo(self) -> ResearchRepository:
        """Get or create research repository."""
        if self._research_repo is None:
            self._research_repo = ResearchRepository()
        return self._research_repo

    def _get_document_repo(self) -> ExperimentDocumentRepository:
        """Get or create document repository."""
        if self._document_repo is None:
            self._document_repo = ExperimentDocumentRepository()
        return self._document_repo

    def generate_for_execution(
        self,
        exec_id: str,
        model: str = "gpt-4o-mini",
    ) -> ExperimentDocument:
        """
        Generate PRFAQ for research execution.

        Args:
            exec_id: ID of the execution.
            model: LLM model to use.

        Returns:
            ExperimentDocument with generated PRFAQ.

        Raises:
            ExecutionNotFoundError: If execution not found.
            NotLinkedToExperimentError: If execution not linked to experiment.
            SummaryNotFoundError: If summary not found or not completed.
            PRFAQGenerationInProgressError: If generation already in progress.
        """
        research_repo = self._get_research_repo()
        document_repo = self._get_document_repo()

        # 1. Get execution
        execution = research_repo.get_execution(exec_id)

        # 2. Validate experiment link
        if not execution.experiment_id:
            raise NotLinkedToExperimentError(exec_id)

        with _tracer.start_as_current_span(
            f"Generate Research PR-FAQ: {execution.topic_name}",
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                "exec_id": exec_id,
                "experiment_id": execution.experiment_id,
                "topic_name": execution.topic_name,
                "model": model,
            },
        ) as span:
            # 3. Check if summary exists and is completed
            summary_doc = document_repo.get_by_experiment(
                execution.experiment_id,
                DocumentType.RESEARCH_SUMMARY,
                source_id=exec_id,
            )
            if not summary_doc or summary_doc.status != DocumentStatus.COMPLETED:
                raise SummaryNotFoundError(exec_id)

            summary_content = summary_doc.markdown_content
            if not summary_content:
                raise SummaryNotFoundError(exec_id)

            if span:
                span.set_attribute("summary_length", len(summary_content))

            # 4. Check for existing generation in progress
            existing = document_repo.get_by_experiment(
                execution.experiment_id,
                DocumentType.RESEARCH_PRFAQ,
                source_id=exec_id,
            )
            if existing and existing.status == DocumentStatus.GENERATING:
                raise PRFAQGenerationInProgressError(exec_id)

            # 5. Create pending document (prevents concurrent generation)
            pending_doc = document_repo.create_pending(
                experiment_id=execution.experiment_id,
                document_type=DocumentType.RESEARCH_PRFAQ,
                source_id=exec_id,
                model=model,
            )

            if pending_doc is None:
                raise PRFAQGenerationInProgressError(exec_id)

            # Build metadata
            metadata = {
                "source": "research",
                "exec_id": exec_id,
                "topic_name": execution.topic_name,
            }

            try:
                # 6. Generate PRFAQ content via LLM
                self._logger.info(f"Generating PRFAQ for execution {exec_id}")

                content = generate_prfaq_from_content(
                    summary_content=summary_content,
                    batch_id=exec_id,
                    model=model,
                    experiment_id=execution.experiment_id,
                )

                if span:
                    span.set_attribute("prfaq_length", len(content))

                # 7. Extract headline from markdown (first # line)
                headline = None
                for line in content.split("\n"):
                    if line.startswith("# "):
                        headline = line[2:].strip()
                        break

                metadata["headline"] = headline

                # 8. Update document with content
                document_repo.update_status(
                    experiment_id=execution.experiment_id,
                    document_type=DocumentType.RESEARCH_PRFAQ,
                    status=DocumentStatus.COMPLETED,
                    source_id=exec_id,
                    markdown_content=content,
                    metadata=metadata,
                )

                self._logger.info(
                    f"Generated PRFAQ for execution {exec_id} ({len(content)} chars)"
                )

                # Return updated document
                return document_repo.get_by_experiment(
                    execution.experiment_id,
                    DocumentType.RESEARCH_PRFAQ,
                    source_id=exec_id,
                )

            except Exception as e:
                # 9. Mark as failed
                self._logger.error(f"Failed to generate PRFAQ for {exec_id}: {e}")
                document_repo.update_status(
                    experiment_id=execution.experiment_id,
                    document_type=DocumentType.RESEARCH_PRFAQ,
                    status=DocumentStatus.FAILED,
                    source_id=exec_id,
                    error_message=str(e),
                    metadata=metadata,
                )
                raise

    def get_prfaq(self, exec_id: str) -> ExperimentDocument | None:
        """
        Get existing PRFAQ for execution.

        Args:
            exec_id: Execution ID.

        Returns:
            ExperimentDocument if found, None otherwise.
        """
        research_repo = self._get_research_repo()
        document_repo = self._get_document_repo()

        try:
            execution = research_repo.get_execution(exec_id)
        except Exception:
            return None

        if not execution.experiment_id:
            return None

        return document_repo.get_by_experiment(
            execution.experiment_id,
            DocumentType.RESEARCH_PRFAQ,
            source_id=exec_id,
        )

    def delete_prfaq(self, exec_id: str) -> bool:
        """
        Delete PRFAQ for execution.

        Args:
            exec_id: Execution ID.

        Returns:
            True if deleted, False if not found.
        """
        research_repo = self._get_research_repo()
        document_repo = self._get_document_repo()

        try:
            execution = research_repo.get_execution(exec_id)
        except Exception:
            return False

        if not execution.experiment_id:
            return False

        return document_repo.delete(
            execution.experiment_id,
            DocumentType.RESEARCH_PRFAQ,
            source_id=exec_id,
        )


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Service instantiation
    total_tests += 1
    try:
        service = ResearchPRFAQGeneratorService()
        print("  Service instantiated successfully")
    except Exception as e:
        all_validation_failures.append(f"Service instantiation failed: {e}")

    # Test 2: SummaryNotFoundError
    total_tests += 1
    try:
        error = SummaryNotFoundError("exec_12345678")
        if "exec_12345678" not in str(error):
            all_validation_failures.append("Error should include exec_id")
        if "summary" not in str(error).lower():
            all_validation_failures.append("Error should mention summary")
    except Exception as e:
        all_validation_failures.append(f"SummaryNotFoundError test failed: {e}")

    # Test 3: PRFAQGenerationInProgressError
    total_tests += 1
    try:
        error = PRFAQGenerationInProgressError("exec_12345678")
        if "exec_12345678" not in str(error):
            all_validation_failures.append("Error should include exec_id")
        if "in progress" not in str(error).lower():
            all_validation_failures.append("Error should mention in progress")
    except Exception as e:
        all_validation_failures.append(
            f"PRFAQGenerationInProgressError test failed: {e}"
        )

    # Test 4: NotLinkedToExperimentError
    total_tests += 1
    try:
        error = NotLinkedToExperimentError("exec_12345678")
        if "exec_12345678" not in str(error):
            all_validation_failures.append("Error should include exec_id")
        if "experiment" not in str(error).lower():
            all_validation_failures.append("Error should mention experiment")
    except Exception as e:
        all_validation_failures.append(f"NotLinkedToExperimentError test failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(
            f"VALIDATION FAILED - {len(all_validation_failures)} of "
            f"{total_tests} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
