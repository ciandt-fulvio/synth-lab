"""
Research service for synth-lab.

Business logic layer for research execution and transcript operations.

References:
    - API spec: specs/010-rest-api/contracts/openapi.yaml
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta, timezone

from synth_lab.models.pagination import PaginatedResponse, PaginationParams
from synth_lab.models.research import (
    ExecutionStatus,
    Message,
    ResearchExecuteRequest,
    ResearchExecuteResponse,
    ResearchExecutionDetail,
    ResearchExecutionSummary,
    TranscriptDetail,
    TranscriptSummary)
from synth_lab.repositories.interview_guide_repository import (
    InterviewGuide,
    InterviewGuideRepository)
from synth_lab.repositories.research_repository import ResearchRepository
from synth_lab.services.message_broker import BrokerMessage, MessageBroker
from synth_lab.services.research_agentic.runner import (
    ConversationMessage,
    InterviewGuideData,
    InterviewResult)

# GMT-3 timezone (São Paulo)
TZ_GMT_MINUS_3 = timezone(timedelta(hours=-3))


class ResearchService:
    """Service for research business logic (read operations)."""

    def __init__(
        self,
        research_repo: ResearchRepository | None = None,
        interview_guide_repo: InterviewGuideRepository | None = None):
        """
        Initialize research service.

        Args:
            research_repo: Research repository. Defaults to new instance.
            interview_guide_repo: Interview guide repository. Defaults to new instance.
        """
        self.research_repo = research_repo or ResearchRepository()
        self.interview_guide_repo = interview_guide_repo or InterviewGuideRepository()

    def _guide_to_interview_guide_data(self, guide: InterviewGuide) -> InterviewGuideData:
        """Convert InterviewGuide from DB to InterviewGuideData for runner."""
        return InterviewGuideData(
            context_definition=guide.context_definition,
            questions=guide.questions,
            context_examples=guide.context_examples)

    def list_executions(
        self,
        params: PaginationParams | None = None) -> PaginatedResponse[ResearchExecutionSummary]:
        """
        List research executions with pagination.

        Args:
            params: Pagination parameters.

        Returns:
            Paginated response with execution summaries.
        """
        params = params or PaginationParams()
        return self.research_repo.list_executions(params)

    def get_execution(self, exec_id: str) -> ResearchExecutionDetail:
        """
        Get a research execution by ID.

        Args:
            exec_id: Execution ID.

        Returns:
            ResearchExecutionDetail with full details.

        Raises:
            ExecutionNotFoundError: If execution not found.
        """
        return self.research_repo.get_execution(exec_id)

    def get_transcripts(
        self,
        exec_id: str,
        params: PaginationParams | None = None) -> PaginatedResponse[TranscriptSummary]:
        """
        Get transcripts for a research execution.

        Args:
            exec_id: Execution ID.
            params: Pagination parameters.

        Returns:
            Paginated response with transcript summaries.

        Raises:
            ExecutionNotFoundError: If execution not found.
        """
        params = params or PaginationParams()
        return self.research_repo.get_transcripts(exec_id, params)

    def get_transcript(self, exec_id: str, synth_id: str) -> TranscriptDetail:
        """
        Get a specific transcript.

        Args:
            exec_id: Execution ID.
            synth_id: Synth ID.

        Returns:
            TranscriptDetail with full messages.

        Raises:
            TranscriptNotFoundError: If transcript not found.
        """
        return self.research_repo.get_transcript(exec_id, synth_id)

    async def generate_summary(self, exec_id: str, model: str = "gpt-4.1-mini") -> str:
        """
        Generate a summary for a completed execution.

        This is used when interviews completed but summary was not generated
        (e.g., generate_summary was False during execution).

        Args:
            exec_id: Execution ID.
            model: LLM model to use for summarization.

        Returns:
            Generated summary markdown content.

        Raises:
            ExecutionNotFoundError: If execution not found.
            ValueError: If execution is not completed or has no transcripts.
        """
        from loguru import logger

        from synth_lab.gen_synth.storage import load_synths
        from synth_lab.repositories.experiment_repository import ExperimentRepository
        from synth_lab.services.research_agentic.runner import ConversationMessage, InterviewResult
        from synth_lab.services.research_agentic.summarizer import summarize_interviews

        # Get execution and verify it's completed
        execution = self.research_repo.get_execution(exec_id)
        if execution.status.value not in ("completed", "failed"):
            raise ValueError(
                f"Execution {exec_id} is not completed (status: {execution.status.value})"
            )

        # Get transcripts
        transcripts = self.research_repo.get_transcripts(exec_id)
        if not transcripts.data:
            raise ValueError(f"Execution {exec_id} has no transcripts")

        logger.info(f"Generating summary for {exec_id} with {len(transcripts.data)} transcripts")

        # Verify experiment_id is set (required for saving document)
        if not execution.experiment_id:
            raise ValueError(f"Execution {exec_id} must be linked to an experiment")

        from synth_lab.domain.entities.experiment_document import DocumentType
        from synth_lab.services.document_service import DocumentService

        doc_service = DocumentService()
        # Note: start_generation is now called in the router before the background task
        # to prevent race conditions. Here we only complete the generation.

        # Load synths for enrichment
        all_synths = load_synths()
        synths_by_id = {s["id"]: s for s in all_synths}

        # Convert transcripts to InterviewResult format
        interview_results: list[tuple[InterviewResult, dict]] = []
        for transcript_summary in transcripts.data:
            transcript = self.research_repo.get_transcript(exec_id, transcript_summary.synth_id)

            # Convert messages to ConversationMessage
            messages = [
                ConversationMessage(
                    speaker=msg.speaker,
                    text=msg.text,
                    internal_notes=msg.internal_notes)
                for msg in transcript.messages
            ]

            interview_result = InterviewResult(
                messages=messages,
                synth_id=transcript.synth_id,
                synth_name=transcript.synth_name or transcript.synth_id,
                topic_guide_name=execution.topic_name,
                trace_path=None,
                total_turns=transcript.turn_count)

            # Get synth data for enrichment
            synth_data = synths_by_id.get(
                transcript.synth_id, {"id": transcript.synth_id, "nome": transcript.synth_name}
            )

            interview_results.append((interview_result, synth_data))

        # Get experiment name for summary title (if linked to an experiment)
        summary_title = execution.topic_name
        if execution.experiment_id:
            experiment_repo = ExperimentRepository()
            experiment = experiment_repo.get_by_id(execution.experiment_id)
            if experiment:
                summary_title = experiment.name

        # Generate summary
        summary = await summarize_interviews(
            interview_results=interview_results,
            topic_guide_name=summary_title,
            model=model)

        # Complete generation (update status from "generating" to "completed")
        doc_service.complete_generation(
            experiment_id=execution.experiment_id,
            document_type=DocumentType.SUMMARY,
            markdown_content=summary,
            metadata={"exec_id": exec_id, "transcript_count": len(transcripts.data)})

        return summary

    async def execute_research(self, request: ResearchExecuteRequest) -> ResearchExecuteResponse:
        """
        Execute a new research session.

        This method validates the interview guide exists, selects synths,
        creates the execution record, runs interviews via the batch runner,
        and saves results to the database.

        Args:
            request: Research execution request.

        Returns:
            ResearchExecuteResponse with execution ID and initial status.

        Raises:
            ValueError: If experiment doesn't have an interview_guide configured.
        """
        # Validate interview guide exists for experiment
        if not request.experiment_id:
            raise ValueError("experiment_id is required for research execution")

        interview_guide = self.interview_guide_repo.get_by_experiment_id(request.experiment_id)
        if interview_guide is None:
            raise ValueError(
                f"No interview guide configured for experiment {request.experiment_id}"
            )

        # Get analysis_id for simulation context in interviews
        from synth_lab.repositories.analysis_repository import AnalysisRepository
        from synth_lab.repositories.experiment_repository import ExperimentRepository

        analysis_repo = AnalysisRepository()
        analysis = analysis_repo.get_by_experiment_id(request.experiment_id)
        analysis_id = analysis.id if analysis else None

        # Get experiment name for summary title
        experiment_repo = ExperimentRepository()
        experiment = experiment_repo.get_by_id(request.experiment_id)
        experiment_name = experiment.name if experiment else None

        # Determine synth count
        synth_count = request.synth_count or (len(request.synth_ids) if request.synth_ids else 5)

        # Generate execution ID
        timestamp = datetime.now(TZ_GMT_MINUS_3).strftime("%Y%m%d_%H%M%S")
        exec_id = f"batch_{request.topic_name}_{timestamp}"

        # Create execution record
        self.research_repo.create_execution(
            exec_id=exec_id,
            topic_name=request.topic_name,
            synth_count=synth_count,
            model=request.model,
            max_turns=request.max_turns,
            status=ExecutionStatus.RUNNING,
            experiment_id=request.experiment_id,
            additional_context=request.additional_context)

        # Convert to InterviewGuideData for runner
        interview_guide_data = self._guide_to_interview_guide_data(interview_guide)

        # Start the batch interviews asynchronously
        asyncio.create_task(
            self._run_batch_and_save(
                exec_id=exec_id,
                interview_guide_data=interview_guide_data,
                guide_name=request.topic_name,
                additional_context=request.additional_context,
                synth_ids=request.synth_ids,
                synth_count=synth_count,
                max_concurrent=request.max_concurrent,
                max_turns=request.max_turns,
                model=request.model,
                skip_interviewee_review=request.skip_interviewee_review,
                analysis_id=analysis_id,
                summary_title=experiment_name)
        )

        return ResearchExecuteResponse(
            exec_id=exec_id,
            status=ExecutionStatus.RUNNING,
            topic_name=request.topic_name,
            synth_count=synth_count,
            started_at=datetime.now())

    async def _run_batch_and_save(
        self,
        exec_id: str,
        interview_guide_data: InterviewGuideData,
        guide_name: str,
        additional_context: str | None,
        synth_ids: list[str] | None,
        synth_count: int,
        max_concurrent: int,
        max_turns: int,
        model: str = "gpt-4o-mini",
        skip_interviewee_review: bool = True,
        analysis_id: str | None = None,
        summary_title: str | None = None) -> None:
        """
        Run batch interviews and save results to database.

        This runs in the background after execute_research returns.

        Args:
            exec_id: Execution ID.
            interview_guide_data: InterviewGuideData with context, questions, examples.
            guide_name: Name identifier for the guide (for logging/tracing).
            additional_context: Optional additional context to complement the research scenario.
            synth_ids: Optional specific synth IDs.
            synth_count: Number of synths to interview.
            max_concurrent: Max concurrent interviews.
            max_turns: Max turns per interview.
            skip_interviewee_review: Whether to skip interviewee response reviewer.
            model: LLM model to use.
            summary_title: Title for the research summary (defaults to guide_name).

        Note:
            Summary is ALWAYS generated automatically after all interviews complete.
        """
        from loguru import logger

        from synth_lab.services.research_agentic.batch_runner import run_batch_interviews

        # Setup message broker for SSE streaming
        broker = MessageBroker()

        async def on_message(
            exec_id: str, synth_id: str, turn: int, msg: ConversationMessage
        ) -> None:
            """Publish interview message to SSE subscribers."""
            await broker.publish(
                exec_id,
                BrokerMessage(
                    event_type="message",
                    data={
                        "synth_id": synth_id,
                        "turn_number": turn,
                        "speaker": msg.speaker,
                        "text": msg.text,
                        "sentiment": msg.sentiment,
                    },
                    timestamp=datetime.now(UTC)))

        async def on_transcription_complete(exec_id: str, successful: int, failed: int) -> None:
            """Publish transcription_completed event before summary generation."""
            await broker.publish(
                exec_id,
                BrokerMessage(
                    event_type="transcription_completed",
                    data={
                        "successful_count": successful,
                        "failed_count": failed,
                    },
                    timestamp=datetime.now(UTC)))

        async def on_summary_start(exec_id: str) -> None:
            """Update execution status to generating_summary when summary starts."""
            logger.info(f"Updating execution {exec_id} status to generating_summary")
            self.research_repo.update_execution_status(
                exec_id=exec_id,
                status=ExecutionStatus.GENERATING_SUMMARY)

        async def on_avatar_generation_start(count: int) -> None:
            """Publish avatar_generation_started event."""
            await broker.publish(
                exec_id,
                BrokerMessage(
                    event_type="avatar_generation_started",
                    data={
                        "count": count,
                    },
                    timestamp=datetime.now(UTC)))
            logger.debug(f"Published avatar_generation_started for {count} synths")

        async def on_avatar_generation_complete(count: int) -> None:
            """Publish avatar_generation_completed event."""
            await broker.publish(
                exec_id,
                BrokerMessage(
                    event_type="avatar_generation_completed",
                    data={
                        "count": count,
                    },
                    timestamp=datetime.now(UTC)))
            logger.debug(f"Published avatar_generation_completed for {count} synths")

        async def on_interview_complete(
            exec_id: str, synth_id: str, total_turns: int, result: InterviewResult
        ) -> None:
            """Save transcript and publish interview_completed event for a single interview."""

            # Save transcript immediately so it's available when user clicks the card
            messages = [
                Message(
                    speaker=msg.speaker,
                    text=msg.text,
                    internal_notes=msg.internal_notes)
                for msg in result.messages
            ]
            self.research_repo.create_transcript(
                exec_id=exec_id,
                synth_id=result.synth_id,
                synth_name=result.synth_name,
                messages=messages,
                status="completed")
            logger.debug(f"Saved transcript for {synth_id}")

            # Then publish the event to notify frontend
            await broker.publish(
                exec_id,
                BrokerMessage(
                    event_type="interview_completed",
                    data={
                        "synth_id": synth_id,
                        "total_turns": total_turns,
                    },
                    timestamp=datetime.now(UTC)))
            logger.debug(f"Published interview_completed for {synth_id}")

        try:
            # Callback to save transcripts immediately when interviews complete
            # This ensures transcripts are available during summary generation
            async def on_transcription_complete_with_save(
                exec_id: str, successful: int, failed: int
            ) -> None:
                """Save transcripts and notify SSE subscribers."""
                # First, call the original callback to notify SSE subscribers
                await on_transcription_complete(exec_id, successful, failed)

            # Run the batch interviews (without summary generation first)
            # We'll generate summary separately after saving transcripts
            result = await run_batch_interviews(
                interview_guide=interview_guide_data,
                max_interviews=synth_count,
                max_concurrent=max_concurrent,
                max_turns=max_turns,
                model=model,
                generate_summary=False,  # Don't generate summary yet
                exec_id=exec_id,
                synth_ids=synth_ids,
                message_callback=on_message,
                on_interview_completed=on_interview_complete,
                on_transcription_completed=on_transcription_complete_with_save,
                on_summary_start=None,  # Not used since we're not generating summary here
                on_avatar_generation_start=on_avatar_generation_start,
                on_avatar_generation_complete=on_avatar_generation_complete,
                skip_interviewee_review=skip_interviewee_review,
                additional_context=additional_context,
                guide_name=guide_name,
                analysis_id=analysis_id)

            # Transcripts are now saved immediately in on_interview_complete callback
            # This ensures they're available as soon as the user clicks on a completed card
            logger.info(
                f"Batch completed: {len(result.successful_interviews)} successful interviews "
                f"for {exec_id}"
            )

            # Always generate summary automatically after interviews complete
            if result.successful_interviews:
                # Notify that summary generation is starting
                await on_summary_start(exec_id)

                from synth_lab.domain.entities.experiment_document import DocumentType
                from synth_lab.services.document_service import DocumentService
                from synth_lab.services.research_agentic.summarizer import (
                    summarize_interviews)

                logger.info(
                    f"Generating summary for {len(result.successful_interviews)} interviews"
                )
                try:
                    summary_content = await summarize_interviews(
                        interview_results=result.successful_interviews,
                        topic_guide_name=summary_title or guide_name,
                        model="gpt-4.1-mini")
                    logger.info(f"Summary generated: {len(summary_content)} chars")

                    # Get execution to find experiment_id
                    execution = self.research_repo.get_execution(exec_id)
                    if execution.experiment_id:
                        # Save to experiment_documents
                        doc_service = DocumentService()
                        doc_service.save_document(
                            experiment_id=execution.experiment_id,
                            document_type=DocumentType.SUMMARY,
                            markdown_content=summary_content,
                            model="gpt-4.1-mini",
                            metadata={"exec_id": exec_id, "interview_count": len(result.successful_interviews)})
                        logger.info(f"Summary saved to experiment_documents for {execution.experiment_id}")
                    else:
                        logger.warning(f"Execution {exec_id} not linked to experiment, summary not saved")
                except Exception as e:
                    logger.error(f"Failed to generate summary: {e}")

            # Update execution status
            self.research_repo.update_execution_status(
                exec_id=exec_id,
                status=ExecutionStatus.COMPLETED,
                successful_count=result.total_completed,
                failed_count=result.total_failed)

            logger.info(f"Research execution {exec_id} completed successfully")

            # Signal end of execution to SSE subscribers
            await broker.close_execution(exec_id)

        except Exception as e:
            logger.error(f"Research execution {exec_id} failed: {e}")
            self.research_repo.update_execution_status(
                exec_id=exec_id,
                status=ExecutionStatus.FAILED,
                failed_count=synth_count)
            # Signal end of execution to SSE subscribers even on failure
            await broker.close_execution(exec_id)


if __name__ == "__main__":
    import sys

    from synth_lab.infrastructure.config import DB_PATH
    from synth_lab.services.errors import ExecutionNotFoundError

    # Validation with real database
    all_validation_failures = []
    total_tests = 0

    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}. Run migration first.")
        sys.exit(1)

    db = DatabaseManager(DB_PATH)
    repo = ResearchRepository()
    service = ResearchService(repo)

    # Test 1: List executions
    total_tests += 1
    try:
        result = service.list_executions()
        print(f"  Listed {result.pagination.total} executions")
        if result.pagination.total < 1:
            all_validation_failures.append("No executions found")
    except Exception as e:
        all_validation_failures.append(f"List executions failed: {e}")

    # Test 2: Get execution by ID
    total_tests += 1
    try:
        result = service.list_executions(PaginationParams(limit=1))
        if result.data:
            exec_id = result.data[0].exec_id
            execution = service.get_execution(exec_id)
            print(f"  Got execution: {execution.topic_name}")
    except Exception as e:
        all_validation_failures.append(f"Get execution failed: {e}")

    # Test 3: Get non-existent execution
    total_tests += 1
    try:
        service.get_execution("nonexistent_12345678")
        all_validation_failures.append("Should raise ExecutionNotFoundError")
    except ExecutionNotFoundError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Wrong exception: {e}")

    # Test 4: Get transcripts
    total_tests += 1
    try:
        result = service.list_executions(PaginationParams(limit=1))
        if result.data:
            exec_id = result.data[0].exec_id
            transcripts = service.get_transcripts(exec_id)
            print(f"  Got {transcripts.pagination.total} transcripts")
    except Exception as e:
        all_validation_failures.append(f"Get transcripts failed: {e}")

    # Test 5: Get specific transcript
    total_tests += 1
    try:
        result = service.list_executions(PaginationParams(limit=1))
        if result.data:
            exec_id = result.data[0].exec_id
            transcripts = service.get_transcripts(exec_id)
            if transcripts.data:
                synth_id = transcripts.data[0].synth_id
                transcript = service.get_transcript(exec_id, synth_id)
                print(f"  Got transcript with {len(transcript.messages)} messages")
    except Exception as e:
        all_validation_failures.append(f"Get transcript failed: {e}")


    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
