"""
Research Summary Generator Service for synth-lab.

Generates narrative summaries for completed research executions using LLM.
Summaries synthesize interview transcripts into actionable insights.

Saves documents to experiment_documents table using execution.experiment_id.

References:
    - Pattern: exploration_summary_generator_service.py
    - Summarizer: services/research_agentic/summarizer.py
"""

import asyncio

from loguru import logger
from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes

from synth_lab.domain.entities.experiment_document import (
    DocumentStatus,
    DocumentType,
    ExperimentDocument,
)
from synth_lab.gen_synth.storage import load_synths
from synth_lab.infrastructure.phoenix_tracing import get_tracer
from synth_lab.repositories.experiment_document_repository import (
    ExperimentDocumentRepository,
)
from synth_lab.repositories.experiment_repository import ExperimentRepository
from synth_lab.repositories.research_repository import ResearchRepository
from synth_lab.services.research_agentic.runner import ConversationMessage, InterviewResult
from synth_lab.services.research_agentic.summarizer import summarize_interviews

# Phoenix/OpenTelemetry tracer for observability
_tracer = get_tracer("research-summary-generator")


class ExecutionNotCompletedError(Exception):
    """Raised when trying to generate summary for incomplete execution."""

    def __init__(self, exec_id: str, status: str):
        self.exec_id = exec_id
        self.status = status
        super().__init__(
            f"Execution {exec_id} is not completed (status={status}). "
            "Only completed executions can generate summaries."
        )


class NoTranscriptsError(Exception):
    """Raised when execution has no transcripts."""

    def __init__(self, exec_id: str):
        self.exec_id = exec_id
        super().__init__(f"Execution {exec_id} has no transcripts.")


class NotLinkedToExperimentError(Exception):
    """Raised when execution is not linked to an experiment."""

    def __init__(self, exec_id: str):
        self.exec_id = exec_id
        super().__init__(f"Execution {exec_id} is not linked to an experiment.")


class SummaryGenerationInProgressError(Exception):
    """Raised when summary generation is already in progress."""

    def __init__(self, exec_id: str):
        self.exec_id = exec_id
        super().__init__(f"Summary generation already in progress for execution {exec_id}")


class ResearchSummaryGeneratorService:
    """Generates summary for research execution, saves to experiment_documents."""

    # Statuses that allow summary generation
    COMPLETED_STATUSES = {"completed", "failed"}

    def __init__(
        self,
        research_repo: ResearchRepository | None = None,
        document_repo: ExperimentDocumentRepository | None = None,
        experiment_repo: ExperimentRepository | None = None,
    ):
        """
        Initialize summary generator service.

        Args:
            research_repo: Repository for research execution data.
            document_repo: Repository for document storage.
            experiment_repo: Repository for experiment data.
        """
        self._research_repo = research_repo
        self._document_repo = document_repo
        self._experiment_repo = experiment_repo
        self._logger = logger.bind(component="research_summary_generator")

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

    def _get_experiment_repo(self) -> ExperimentRepository:
        """Get or create experiment repository."""
        if self._experiment_repo is None:
            self._experiment_repo = ExperimentRepository()
        return self._experiment_repo

    def generate_for_execution(
        self,
        exec_id: str,
        model: str = "gpt-4.1-mini",
    ) -> ExperimentDocument:
        """
        Generate summary for research execution.

        Args:
            exec_id: ID of the execution.
            model: LLM model to use.

        Returns:
            ExperimentDocument with generated summary.

        Raises:
            ExecutionNotFoundError: If execution not found.
            ExecutionNotCompletedError: If execution is not completed.
            NoTranscriptsError: If execution has no transcripts.
            NotLinkedToExperimentError: If execution not linked to experiment.
            SummaryGenerationInProgressError: If generation already in progress.
        """

        research_repo = self._get_research_repo()
        document_repo = self._get_document_repo()
        experiment_repo = self._get_experiment_repo()

        # 1. Get execution
        execution = research_repo.get_execution(exec_id)

        # 2. Validate status
        if execution.status.value not in self.COMPLETED_STATUSES:
            raise ExecutionNotCompletedError(exec_id, execution.status.value)

        # 3. Validate experiment link
        if not execution.experiment_id:
            raise NotLinkedToExperimentError(exec_id)

        # 4. Get transcripts
        transcripts = research_repo.get_transcripts(exec_id)
        if not transcripts.data:
            raise NoTranscriptsError(exec_id)

        transcript_count = len(transcripts.data)

        with _tracer.start_as_current_span(
            f"Generate Research Summary: {execution.topic_name}",
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                "exec_id": exec_id,
                "experiment_id": execution.experiment_id,
                "topic_name": execution.topic_name,
                "transcript_count": transcript_count,
                "model": model,
            },
        ) as span:
            # 5. Check for existing generation in progress
            existing = document_repo.get_by_experiment(
                execution.experiment_id,
                DocumentType.RESEARCH_SUMMARY,
                source_id=exec_id,
            )
            if existing and existing.status == DocumentStatus.GENERATING:
                raise SummaryGenerationInProgressError(exec_id)

            # 6. Create pending document (prevents concurrent generation)
            pending_doc = document_repo.create_pending(
                experiment_id=execution.experiment_id,
                document_type=DocumentType.RESEARCH_SUMMARY,
                source_id=exec_id,
                model=model,
            )

            if pending_doc is None:
                raise SummaryGenerationInProgressError(exec_id)

            # Build metadata
            metadata = {
                "source": "research",
                "exec_id": exec_id,
                "transcript_count": transcript_count,
                "topic_name": execution.topic_name,
            }

            try:
                # 7. Load synths for enrichment
                all_synths = load_synths()
                synths_by_id = {s["id"]: s for s in all_synths}

                # 8. Convert transcripts to InterviewResult format
                interview_results: list[tuple[InterviewResult, dict]] = []
                for transcript_summary in transcripts.data:
                    transcript = research_repo.get_transcript(
                        exec_id, transcript_summary.synth_id
                    )

                    messages = [
                        ConversationMessage(
                            speaker=msg.speaker,
                            text=msg.text,
                            internal_notes=msg.internal_notes,
                        )
                        for msg in transcript.messages
                    ]

                    interview_result = InterviewResult(
                        messages=messages,
                        synth_id=transcript.synth_id,
                        synth_name=transcript.synth_name or transcript.synth_id,
                        topic_guide_name=execution.topic_name,
                        trace_path=None,
                        total_turns=transcript.turn_count,
                    )

                    synth_data = synths_by_id.get(
                        transcript.synth_id,
                        {"id": transcript.synth_id, "nome": transcript.synth_name},
                    )

                    interview_results.append((interview_result, synth_data))

                # 9. Get experiment name for summary title
                summary_title = execution.topic_name
                experiment = experiment_repo.get_by_id(execution.experiment_id)
                if experiment:
                    summary_title = experiment.name

                # 10. Generate summary via LLM
                self._logger.info(
                    f"Generating summary for {exec_id} with "
                    f"{transcript_count} transcripts"
                )

                # Run async summarizer in sync context
                content = asyncio.get_event_loop().run_until_complete(
                    summarize_interviews(
                        interview_results=interview_results,
                        topic_guide_name=summary_title,
                        model=model,
                    )
                )

                if span:
                    span.set_attribute("summary_length", len(content))

                # 11. Update document with content
                document_repo.update_status(
                    experiment_id=execution.experiment_id,
                    document_type=DocumentType.RESEARCH_SUMMARY,
                    status=DocumentStatus.COMPLETED,
                    source_id=exec_id,
                    markdown_content=content,
                    metadata=metadata,
                )

                self._logger.info(
                    f"Generated summary for execution {exec_id} "
                    f"({transcript_count} transcripts, {len(content)} chars)"
                )

                # Return updated document
                return document_repo.get_by_experiment(
                    execution.experiment_id,
                    DocumentType.RESEARCH_SUMMARY,
                    source_id=exec_id,
                )

            except Exception as e:
                # 12. Mark as failed
                self._logger.error(f"Failed to generate summary for {exec_id}: {e}")
                document_repo.update_status(
                    experiment_id=execution.experiment_id,
                    document_type=DocumentType.RESEARCH_SUMMARY,
                    status=DocumentStatus.FAILED,
                    source_id=exec_id,
                    error_message=str(e),
                    metadata=metadata,
                )
                raise

    async def generate_for_execution_async(
        self,
        exec_id: str,
        model: str = "gpt-4.1-mini",
    ) -> ExperimentDocument:
        """
        Async version of generate_for_execution.

        Args:
            exec_id: ID of the execution.
            model: LLM model to use.

        Returns:
            ExperimentDocument with generated summary.
        """

        research_repo = self._get_research_repo()
        document_repo = self._get_document_repo()
        experiment_repo = self._get_experiment_repo()

        # 1. Get execution
        execution = research_repo.get_execution(exec_id)

        # 2. Validate status
        if execution.status.value not in self.COMPLETED_STATUSES:
            raise ExecutionNotCompletedError(exec_id, execution.status.value)

        # 3. Validate experiment link
        if not execution.experiment_id:
            raise NotLinkedToExperimentError(exec_id)

        # 4. Get transcripts
        transcripts = research_repo.get_transcripts(exec_id)
        if not transcripts.data:
            raise NoTranscriptsError(exec_id)

        transcript_count = len(transcripts.data)

        with _tracer.start_as_current_span(
            f"Generate Research Summary: {execution.topic_name}",
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                "exec_id": exec_id,
                "experiment_id": execution.experiment_id,
                "topic_name": execution.topic_name,
                "transcript_count": transcript_count,
                "model": model,
            },
        ) as span:
            # 5. Check for existing generation in progress
            existing = document_repo.get_by_experiment(
                execution.experiment_id,
                DocumentType.RESEARCH_SUMMARY,
                source_id=exec_id,
            )
            if existing and existing.status == DocumentStatus.GENERATING:
                raise SummaryGenerationInProgressError(exec_id)

            # 6. Create pending document
            pending_doc = document_repo.create_pending(
                experiment_id=execution.experiment_id,
                document_type=DocumentType.RESEARCH_SUMMARY,
                source_id=exec_id,
                model=model,
            )

            if pending_doc is None:
                raise SummaryGenerationInProgressError(exec_id)

            metadata = {
                "source": "research",
                "exec_id": exec_id,
                "transcript_count": transcript_count,
                "topic_name": execution.topic_name,
            }

            try:
                # 7. Load synths for enrichment
                all_synths = load_synths()
                synths_by_id = {s["id"]: s for s in all_synths}

                # 8. Convert transcripts to InterviewResult format
                interview_results: list[tuple[InterviewResult, dict]] = []
                for transcript_summary in transcripts.data:
                    transcript = research_repo.get_transcript(
                        exec_id, transcript_summary.synth_id
                    )

                    messages = [
                        ConversationMessage(
                            speaker=msg.speaker,
                            text=msg.text,
                            internal_notes=msg.internal_notes,
                        )
                        for msg in transcript.messages
                    ]

                    interview_result = InterviewResult(
                        messages=messages,
                        synth_id=transcript.synth_id,
                        synth_name=transcript.synth_name or transcript.synth_id,
                        topic_guide_name=execution.topic_name,
                        trace_path=None,
                        total_turns=transcript.turn_count,
                    )

                    synth_data = synths_by_id.get(
                        transcript.synth_id,
                        {"id": transcript.synth_id, "nome": transcript.synth_name},
                    )

                    interview_results.append((interview_result, synth_data))

                # 9. Get experiment name for summary title
                summary_title = execution.topic_name
                experiment = experiment_repo.get_by_id(execution.experiment_id)
                if experiment:
                    summary_title = experiment.name

                # 10. Generate summary via LLM (async)
                self._logger.info(
                    f"Generating summary for {exec_id} with "
                    f"{transcript_count} transcripts"
                )

                content = await summarize_interviews(
                    interview_results=interview_results,
                    topic_guide_name=summary_title,
                    model=model,
                )

                if span:
                    span.set_attribute("summary_length", len(content))

                # 11. Update document with content
                document_repo.update_status(
                    experiment_id=execution.experiment_id,
                    document_type=DocumentType.RESEARCH_SUMMARY,
                    status=DocumentStatus.COMPLETED,
                    source_id=exec_id,
                    markdown_content=content,
                    metadata=metadata,
                )

                self._logger.info(
                    f"Generated summary for execution {exec_id} "
                    f"({transcript_count} transcripts, {len(content)} chars)"
                )

                return document_repo.get_by_experiment(
                    execution.experiment_id,
                    DocumentType.RESEARCH_SUMMARY,
                    source_id=exec_id,
                )

            except Exception as e:
                self._logger.error(f"Failed to generate summary for {exec_id}: {e}")
                document_repo.update_status(
                    experiment_id=execution.experiment_id,
                    document_type=DocumentType.RESEARCH_SUMMARY,
                    status=DocumentStatus.FAILED,
                    source_id=exec_id,
                    error_message=str(e),
                    metadata=metadata,
                )
                raise

    def get_summary(self, exec_id: str) -> ExperimentDocument | None:
        """
        Get existing summary for execution.

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
            DocumentType.RESEARCH_SUMMARY,
            source_id=exec_id,
        )

    def delete_summary(self, exec_id: str) -> bool:
        """
        Delete summary for execution.

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
            DocumentType.RESEARCH_SUMMARY,
            source_id=exec_id,
        )


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Service instantiation
    total_tests += 1
    try:
        service = ResearchSummaryGeneratorService()
        print("  Service instantiated successfully")
    except Exception as e:
        all_validation_failures.append(f"Service instantiation failed: {e}")

    # Test 2: COMPLETED_STATUSES
    total_tests += 1
    try:
        expected = {"completed", "failed"}
        if ResearchSummaryGeneratorService.COMPLETED_STATUSES != expected:
            all_validation_failures.append("COMPLETED_STATUSES mismatch")
    except Exception as e:
        all_validation_failures.append(f"COMPLETED_STATUSES test failed: {e}")

    # Test 3: ExecutionNotCompletedError
    total_tests += 1
    try:
        error = ExecutionNotCompletedError("exec_12345678", "running")
        if "exec_12345678" not in str(error):
            all_validation_failures.append("Error should include exec_id")
        if "running" not in str(error):
            all_validation_failures.append("Error should include status")
    except Exception as e:
        all_validation_failures.append(f"ExecutionNotCompletedError test failed: {e}")

    # Test 4: SummaryGenerationInProgressError
    total_tests += 1
    try:
        error = SummaryGenerationInProgressError("exec_12345678")
        if "exec_12345678" not in str(error):
            all_validation_failures.append("Error should include exec_id")
        if "in progress" not in str(error).lower():
            all_validation_failures.append("Error should mention in progress")
    except Exception as e:
        all_validation_failures.append(
            f"SummaryGenerationInProgressError test failed: {e}"
        )

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
