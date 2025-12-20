"""
Research service for synth-lab.

Business logic layer for research execution and transcript operations.

References:
    - API spec: specs/010-rest-api/contracts/openapi.yaml
"""

import asyncio
from datetime import datetime, timedelta, timezone

from synth_lab.models.pagination import PaginatedResponse, PaginationParams
from synth_lab.models.research import (
    ExecutionStatus,
    Message,
    ResearchExecuteRequest,
    ResearchExecuteResponse,
    ResearchExecutionDetail,
    ResearchExecutionSummary,
    TranscriptDetail,
    TranscriptSummary,
)
from synth_lab.repositories.research_repository import ResearchRepository
from synth_lab.repositories.topic_repository import TopicRepository
from synth_lab.services.errors import SummaryNotFoundError, TopicNotFoundError

# GMT-3 timezone (São Paulo)
TZ_GMT_MINUS_3 = timezone(timedelta(hours=-3))


class ResearchService:
    """Service for research business logic (read operations)."""

    def __init__(self, research_repo: ResearchRepository | None = None):
        """
        Initialize research service.

        Args:
            research_repo: Research repository. Defaults to new instance.
        """
        self.research_repo = research_repo or ResearchRepository()

    def list_executions(
        self,
        params: PaginationParams | None = None,
    ) -> PaginatedResponse[ResearchExecutionSummary]:
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
        params: PaginationParams | None = None,
    ) -> PaginatedResponse[TranscriptSummary]:
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

    def get_summary(self, exec_id: str) -> str:
        """
        Get the summary markdown content for an execution.

        Args:
            exec_id: Execution ID.

        Returns:
            Markdown summary content.

        Raises:
            ExecutionNotFoundError: If execution not found.
            SummaryNotFoundError: If summary file doesn't exist.
        """
        summary_path = self.research_repo.get_summary_path(exec_id)

        if summary_path is None or not summary_path.exists():
            raise SummaryNotFoundError(exec_id)

        return summary_path.read_text(encoding="utf-8")

    async def execute_research(self, request: ResearchExecuteRequest) -> ResearchExecuteResponse:
        """
        Execute a new research session.

        This method validates the topic, selects synths, creates the execution record,
        runs interviews via the batch runner, and saves results to the database.

        Args:
            request: Research execution request.

        Returns:
            ResearchExecuteResponse with execution ID and initial status.

        Raises:
            TopicNotFoundError: If topic doesn't exist.
        """
        # Validate topic exists
        topic_repo = TopicRepository()
        try:
            topic_repo.get_by_name(request.topic_name)
        except TopicNotFoundError:
            raise

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
        )

        # Start the batch interviews asynchronously
        asyncio.create_task(
            self._run_batch_and_save(
                exec_id=exec_id,
                topic_name=request.topic_name,
                synth_ids=request.synth_ids,
                synth_count=synth_count,
                max_concurrent=request.max_concurrent,
                max_turns=request.max_turns,
                model=request.model,
                generate_summary=request.generate_summary,
            )
        )

        return ResearchExecuteResponse(
            exec_id=exec_id,
            status=ExecutionStatus.RUNNING,
            topic_name=request.topic_name,
            synth_count=synth_count,
            started_at=datetime.now(),
        )

    async def _run_batch_and_save(
        self,
        exec_id: str,
        topic_name: str,
        synth_ids: list[str] | None,
        synth_count: int,
        max_concurrent: int,
        max_turns: int,
        model: str,
        generate_summary: bool,
    ) -> None:
        """
        Run batch interviews and save results to database.

        This runs in the background after execute_research returns.

        Args:
            exec_id: Execution ID.
            topic_name: Topic guide name.
            synth_ids: Optional specific synth IDs.
            synth_count: Number of synths to interview.
            max_concurrent: Max concurrent interviews.
            max_turns: Max turns per interview.
            model: LLM model to use.
            generate_summary: Whether to generate summary.
        """
        from loguru import logger
        from synth_lab.services.research_agentic.batch_runner import run_batch_interviews

        try:
            # Run the batch interviews
            result = await run_batch_interviews(
                topic_guide_name=topic_name,
                max_interviews=synth_count,
                max_concurrent=max_concurrent,
                max_turns=max_turns,
                model=model,
                generate_summary=generate_summary,
            )

            # Save transcripts to database
            for interview_result, synth in result.successful_interviews:
                messages = [
                    Message(
                        speaker=msg.speaker,
                        text=msg.text,
                        internal_notes=msg.internal_notes,
                    )
                    for msg in interview_result.messages
                ]
                self.research_repo.create_transcript(
                    exec_id=exec_id,
                    synth_id=interview_result.synth_id,
                    synth_name=interview_result.synth_name,
                    messages=messages,
                    status="completed",
                )

            # Update execution status
            self.research_repo.update_execution_status(
                exec_id=exec_id,
                status=ExecutionStatus.COMPLETED,
                successful_count=result.total_completed,
                failed_count=result.total_failed,
                summary_path=result.summary_path,
            )

            logger.info(f"Research execution {exec_id} completed successfully")

        except Exception as e:
            logger.error(f"Research execution {exec_id} failed: {e}")
            self.research_repo.update_execution_status(
                exec_id=exec_id,
                status=ExecutionStatus.FAILED,
                failed_count=synth_count,
            )


if __name__ == "__main__":
    import sys

    from synth_lab.infrastructure.config import DB_PATH
    from synth_lab.infrastructure.database import DatabaseManager
    from synth_lab.services.errors import ExecutionNotFoundError

    # Validation with real database
    all_validation_failures = []
    total_tests = 0

    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}. Run migration first.")
        sys.exit(1)

    db = DatabaseManager(DB_PATH)
    repo = ResearchRepository(db)
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

    # Test 6: Get summary (may not exist)
    total_tests += 1
    try:
        result = service.list_executions(PaginationParams(limit=1))
        if result.data:
            exec_id = result.data[0].exec_id
            try:
                summary = service.get_summary(exec_id)
                print(f"  Got summary: {len(summary)} chars")
            except SummaryNotFoundError:
                print(f"  Summary not found for {exec_id} (expected)")
    except Exception as e:
        all_validation_failures.append(f"Get summary failed: {e}")

    db.close()

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
