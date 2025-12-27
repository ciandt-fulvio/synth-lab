"""
Research repository for synth-lab.

Data access layer for research execution and transcript data.

References:
    - Schema: specs/010-rest-api/data-model.md
"""

import json
from datetime import datetime
from pathlib import Path

from synth_lab.infrastructure.database import DatabaseManager
from synth_lab.models.pagination import PaginatedResponse, PaginationParams
from synth_lab.models.research import (
    ExecutionStatus,
    Message,
    ResearchExecutionDetail,
    ResearchExecutionSummary,
    TranscriptDetail,
    TranscriptSummary,
)
from synth_lab.repositories.base import BaseRepository
from synth_lab.services.errors import ExecutionNotFoundError, TranscriptNotFoundError


class ResearchRepository(BaseRepository):
    """Repository for research execution data access."""

    def __init__(self, db: DatabaseManager | None = None):
        super().__init__(db)

    def list_executions(
        self,
        params: PaginationParams,
    ) -> PaginatedResponse[ResearchExecutionSummary]:
        """
        List research executions with pagination.

        Args:
            params: Pagination parameters.

        Returns:
            Paginated response with execution summaries.
        """
        base_query = "SELECT * FROM research_executions"
        rows, meta = self._paginate_query(base_query, params)
        executions = [self._row_to_summary(row) for row in rows]
        return PaginatedResponse(data=executions, pagination=meta)

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
        row = self.db.fetchone(
            "SELECT * FROM research_executions WHERE exec_id = ?",
            (exec_id,),
        )
        if row is None:
            raise ExecutionNotFoundError(exec_id)

        return self._row_to_detail(row)

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
        # Verify execution exists
        self.get_execution(exec_id)

        params = params or PaginationParams()
        base_query = """
            SELECT t.*, s.nome as synth_name
            FROM transcripts t
            LEFT JOIN synths s ON t.synth_id = s.id
            WHERE t.exec_id = ?
        """
        rows, meta = self._paginate_query(
            base_query, params, query_params=(exec_id,))
        transcripts = [self._row_to_transcript_summary(row) for row in rows]
        return PaginatedResponse(data=transcripts, pagination=meta)

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
        row = self.db.fetchone(
            """
            SELECT t.*, s.nome as synth_name
            FROM transcripts t
            LEFT JOIN synths s ON t.synth_id = s.id
            WHERE t.exec_id = ? AND t.synth_id = ?
            """,
            (exec_id, synth_id),
        )
        if row is None:
            raise TranscriptNotFoundError(exec_id, synth_id)

        return self._row_to_transcript_detail(row)

    def get_summary_content(self, exec_id: str) -> str | None:
        """
        Get the summary content for an execution.

        Args:
            exec_id: Execution ID.

        Returns:
            Summary markdown content, or None if not available.

        Raises:
            ExecutionNotFoundError: If execution not found.
        """
        row = self.db.fetchone(
            "SELECT summary_content FROM research_executions WHERE exec_id = ?",
            (exec_id,),
        )
        if row is None:
            raise ExecutionNotFoundError(exec_id)

        return row["summary_content"]

    def _row_to_summary(self, row) -> ResearchExecutionSummary:
        """Convert a database row to ResearchExecutionSummary."""
        started_at = row["started_at"]
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)

        completed_at = row["completed_at"]
        if isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)

        return ResearchExecutionSummary(
            exec_id=row["exec_id"],
            experiment_id=row["experiment_id"] if "experiment_id" in row.keys() else None,
            topic_name=row["topic_name"],
            status=ExecutionStatus(row["status"]),
            synth_count=row["synth_count"],
            started_at=started_at,
            completed_at=completed_at,
        )

    def _row_to_detail(self, row) -> ResearchExecutionDetail:
        """Convert a database row to ResearchExecutionDetail."""
        started_at = row["started_at"]
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)

        completed_at = row["completed_at"]
        if isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)

        # Check if summary exists in database
        summary_content = row["summary_content"] if "summary_content" in row.keys(
        ) else None
        summary_available = summary_content is not None and len(
            summary_content) > 0

        # Check if PR-FAQ exists
        prfaq_row = self.db.fetchone(
            "SELECT 1 FROM prfaq_metadata WHERE exec_id = ?",
            (row["exec_id"],),
        )
        prfaq_available = prfaq_row is not None

        return ResearchExecutionDetail(
            exec_id=row["exec_id"],
            experiment_id=row["experiment_id"] if "experiment_id" in row.keys() else None,
            topic_name=row["topic_name"],
            status=ExecutionStatus(row["status"]),
            synth_count=row["synth_count"],
            started_at=started_at,
            completed_at=completed_at,
            successful_count=row["successful_count"] or 0,
            failed_count=row["failed_count"] or 0,
            model=row["model"] or "gpt-5-mini",
            max_turns=row["max_turns"] or 6,
            summary_available=summary_available,
            prfaq_available=prfaq_available,
        )

    def _row_to_transcript_summary(self, row) -> TranscriptSummary:
        """Convert a database row to TranscriptSummary."""
        timestamp = row["timestamp"]
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        # sqlite3.Row doesn't have .get(), use key access with fallback
        synth_name = row["synth_name"] if "synth_name" in row.keys() else None

        return TranscriptSummary(
            synth_id=row["synth_id"],
            synth_name=synth_name,
            turn_count=row["turn_count"] or 0,
            timestamp=timestamp,
            status=row["status"],
        )

    def _row_to_transcript_detail(self, row) -> TranscriptDetail:
        """Convert a database row to TranscriptDetail."""
        timestamp = row["timestamp"]
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        # sqlite3.Row doesn't have .get(), use key access with fallback
        synth_name = row["synth_name"] if "synth_name" in row.keys() else None

        # Parse messages JSON
        messages = []
        if row["messages"]:
            raw_messages = json.loads(row["messages"])
            for msg in raw_messages:
                messages.append(Message(
                    speaker=msg.get("speaker", "Unknown"),
                    text=msg.get("text", ""),
                    internal_notes=msg.get("internal_notes"),
                ))

        return TranscriptDetail(
            exec_id=row["exec_id"],
            synth_id=row["synth_id"],
            synth_name=synth_name,
            turn_count=row["turn_count"] or 0,
            timestamp=timestamp,
            status=row["status"],
            messages=messages,
        )

    # Write methods for creating executions and transcripts

    def create_execution(
        self,
        exec_id: str,
        topic_name: str,
        synth_count: int,
        model: str = "gpt-4o-mini",
        max_turns: int = 6,
        status: ExecutionStatus = ExecutionStatus.PENDING,
        experiment_id: str | None = None,
    ) -> None:
        """
        Create a new research execution record.

        Args:
            exec_id: Execution ID.
            topic_name: Topic guide name.
            synth_count: Number of synths to interview.
            model: LLM model to use.
            max_turns: Maximum turns per interview.
            status: Initial execution status.
            experiment_id: Optional parent experiment ID.
        """
        query = """
            INSERT INTO research_executions
            (exec_id, experiment_id, topic_name, synth_count, model, max_turns, status, started_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute(
            query,
            (exec_id, experiment_id, topic_name, synth_count, model, max_turns,
             status.value, datetime.now().isoformat()),
        )

    def update_execution_status(
        self,
        exec_id: str,
        status: ExecutionStatus,
        successful_count: int | None = None,
        failed_count: int | None = None,
        summary_content: str | None = None,
    ) -> None:
        """
        Update execution status and counts.

        Args:
            exec_id: Execution ID.
            status: New status.
            successful_count: Number of successful interviews.
            failed_count: Number of failed interviews.
            summary_content: Summary markdown content.
        """
        updates = ["status = ?"]
        params: list = [status.value]

        if successful_count is not None:
            updates.append("successful_count = ?")
            params.append(successful_count)

        if failed_count is not None:
            updates.append("failed_count = ?")
            params.append(failed_count)

        if summary_content is not None:
            updates.append("summary_content = ?")
            params.append(summary_content)

        if status in (ExecutionStatus.COMPLETED, ExecutionStatus.FAILED):
            updates.append("completed_at = ?")
            params.append(datetime.now().isoformat())

        params.append(exec_id)
        query = f"UPDATE research_executions SET {', '.join(updates)} WHERE exec_id = ?"
        self.db.execute(query, tuple(params))

    def create_transcript(
        self,
        exec_id: str,
        synth_id: str,
        synth_name: str,
        messages: list[Message],
        status: str = "completed",
    ) -> None:
        """
        Create a new transcript record.

        Args:
            exec_id: Execution ID.
            synth_id: Synth ID.
            synth_name: Synth display name.
            messages: List of interview messages.
            status: Transcript status.
        """
        messages_json = json.dumps(
            [{"speaker": m.speaker, "text": m.text,
                "internal_notes": m.internal_notes} for m in messages],
            ensure_ascii=False,
        )
        # A turn is a complete exchange (question + answer), so divide by 2
        turn_count = len(messages) // 2

        query = """
            INSERT INTO transcripts
            (exec_id, synth_id, synth_name, turn_count, timestamp, status, messages)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute(
            query,
            (exec_id, synth_id, synth_name, turn_count,
             datetime.now().isoformat(), status, messages_json),
        )

    def update_summary_content(self, exec_id: str, summary_content: str) -> None:
        """
        Update only the summary content for an execution.

        Args:
            exec_id: Execution ID.
            summary_content: Summary markdown content.

        Raises:
            ExecutionNotFoundError: If execution not found.
        """
        # Verify execution exists
        self.get_execution(exec_id)

        query = "UPDATE research_executions SET summary_content = ? WHERE exec_id = ?"
        self.db.execute(query, (summary_content, exec_id))

    def get_prfaq_metadata(self, exec_id: str) -> dict | None:
        """
        Get PR-FAQ metadata for an execution.

        Args:
            exec_id: Execution ID.

        Returns:
            Dict with prfaq_metadata fields or None if not found.

        Note:
            This returns raw dict for use with compute_prfaq_state.
            The dict includes: status, error_message, started_at, generated_at
        """
        row = self.db.fetchone(
            """
            SELECT exec_id, status, error_message, started_at, generated_at,
                   headline, markdown_content, validation_status, confidence_score
            FROM prfaq_metadata
            WHERE exec_id = ?
            """,
            (exec_id,),
        )
        if row is None:
            return None

        return {
            "exec_id": row["exec_id"],
            # Default for legacy records
            "status": row["status"] or "completed",
            "error_message": row["error_message"],
            "started_at": row["started_at"],
            "generated_at": row["generated_at"],
            "headline": row["headline"],
            "markdown_content": row["markdown_content"],
            "validation_status": row["validation_status"],
            "confidence_score": row["confidence_score"],
        }

    def list_executions_by_experiment(
        self,
        experiment_id: str,
        params: PaginationParams | None = None,
    ) -> PaginatedResponse[ResearchExecutionSummary]:
        """
        List research executions for a specific experiment.

        Args:
            experiment_id: Experiment ID to filter by.
            params: Pagination parameters.

        Returns:
            Paginated response with execution summaries.
        """
        params = params or PaginationParams()
        base_query = "SELECT * FROM research_executions WHERE experiment_id = ?"
        rows, meta = self._paginate_query(base_query, params, query_params=(experiment_id,))
        executions = [self._row_to_summary(row) for row in rows]
        return PaginatedResponse(data=executions, pagination=meta)


if __name__ == "__main__":
    import sys

    from synth_lab.infrastructure.config import DB_PATH
    from synth_lab.infrastructure.database import DatabaseManager

    # Validation with real database
    all_validation_failures = []
    total_tests = 0

    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}. Run migration first.")
        sys.exit(1)

    db = DatabaseManager(DB_PATH)
    repo = ResearchRepository(db)

    # Test 1: List executions
    total_tests += 1
    try:
        result = repo.list_executions(PaginationParams(limit=10))
        print(f"  Found {result.pagination.total} executions")
        if result.pagination.total < 1:
            all_validation_failures.append("No executions found in database")
    except Exception as e:
        all_validation_failures.append(f"List executions failed: {e}")

    # Test 2: Get execution by ID
    total_tests += 1
    try:
        result = repo.list_executions(PaginationParams(limit=1))
        if result.data:
            exec_id = result.data[0].exec_id
            execution = repo.get_execution(exec_id)
            if execution.exec_id != exec_id:
                all_validation_failures.append(
                    f"Exec ID mismatch: {execution.exec_id}")
            print(f"  Got execution: {execution.topic_name}")
    except Exception as e:
        all_validation_failures.append(f"Get execution failed: {e}")

    # Test 3: Get non-existent execution
    total_tests += 1
    try:
        repo.get_execution("nonexistent_12345678")
        all_validation_failures.append("Should raise ExecutionNotFoundError")
    except ExecutionNotFoundError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Wrong exception: {e}")

    # Test 4: Get transcripts
    total_tests += 1
    try:
        result = repo.list_executions(PaginationParams(limit=1))
        if result.data:
            exec_id = result.data[0].exec_id
            transcripts = repo.get_transcripts(exec_id)
            print(f"  Found {transcripts.pagination.total} transcripts")
    except Exception as e:
        all_validation_failures.append(f"Get transcripts failed: {e}")

    # Test 5: Get specific transcript
    total_tests += 1
    try:
        result = repo.list_executions(PaginationParams(limit=1))
        if result.data:
            exec_id = result.data[0].exec_id
            transcripts = repo.get_transcripts(exec_id)
            if transcripts.data:
                synth_id = transcripts.data[0].synth_id
                transcript = repo.get_transcript(exec_id, synth_id)
                print(
                    f"  Got transcript with {len(transcript.messages)} messages")
    except Exception as e:
        all_validation_failures.append(f"Get transcript failed: {e}")

    db.close()

    # Final validation result
    if all_validation_failures:
        print(
            f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(
            f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
