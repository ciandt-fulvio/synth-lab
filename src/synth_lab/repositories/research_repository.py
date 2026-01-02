"""
Research repository for synth-lab.

Data access layer for research execution and transcript data.
Uses SQLAlchemy ORM for database operations.

References:
    - Schema: specs/010-rest-api/data-model.md
    - ORM models: synth_lab.models.orm.research
"""

import json
from datetime import datetime
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from synth_lab.models.orm.research import ResearchExecution as ResearchExecutionORM
from synth_lab.models.orm.research import Transcript as TranscriptORM
from synth_lab.models.pagination import PaginatedResponse, PaginationMeta, PaginationParams
from synth_lab.models.research import (
    ExecutionStatus,
    Message,
    ResearchExecutionDetail,
    ResearchExecutionSummary,
    TranscriptDetail,
    TranscriptSummary)
from synth_lab.repositories.base import BaseRepository
from synth_lab.services.errors import ExecutionNotFoundError, TranscriptNotFoundError


class ResearchRepository(BaseRepository):
    """Repository for research execution data access.

    Uses SQLAlchemy ORM for database operations.

    Usage:
        # ORM mode
        repo = ResearchRepository(db=database_manager)

        # ORM mode (SQLAlchemy)
        repo = ResearchRepository(session=session)
    """

    def __init__(
        self,
session: Session | None = None):
        super().__init__( session=session)

    def list_executions(
        self,
        params: PaginationParams) -> PaginatedResponse[ResearchExecutionSummary]:
        """
        List research executions with pagination.

        Args:
            params: Pagination parameters.

        Returns:
            Paginated response with execution summaries.
        """
        return self._list_executions_orm(params)

    def _list_executions_orm(
        self,
        params: PaginationParams) -> PaginatedResponse[ResearchExecutionSummary]:
        """List executions using ORM."""
        stmt = select(ResearchExecutionORM).order_by(
            ResearchExecutionORM.started_at.desc()
        )

        # Get total count
        count_stmt = select(func.count()).select_from(ResearchExecutionORM)
        total = self.session.execute(count_stmt).scalar() or 0

        # Apply pagination
        stmt = stmt.limit(params.limit).offset(params.offset)
        executions_orm = list(self.session.execute(stmt).scalars().all())

        summaries = [self._orm_to_summary(e) for e in executions_orm]
        meta = PaginationMeta.from_params(total, params)
        return PaginatedResponse(data=summaries, pagination=meta)

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
        return self._get_execution_orm(exec_id)

    def _get_execution_orm(self, exec_id: str) -> ResearchExecutionDetail:
        """Get execution by ID using ORM."""
        orm_exec = self.session.get(ResearchExecutionORM, exec_id)
        if orm_exec is None:
            raise ExecutionNotFoundError(exec_id)

        return self._orm_to_detail(orm_exec)

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
        # Verify execution exists
        self.get_execution(exec_id)

        params = params or PaginationParams()

        return self._get_transcripts_orm(exec_id, params)

    def _get_transcripts_orm(
        self,
        exec_id: str,
        params: PaginationParams) -> PaginatedResponse[TranscriptSummary]:
        """Get transcripts using ORM."""
        stmt = select(TranscriptORM).where(
            TranscriptORM.exec_id == exec_id
        ).order_by(TranscriptORM.timestamp.desc())

        # Get total count
        count_stmt = (
            select(func.count())
            .select_from(TranscriptORM)
            .where(TranscriptORM.exec_id == exec_id)
        )
        total = self.session.execute(count_stmt).scalar() or 0

        # Apply pagination
        stmt = stmt.limit(params.limit).offset(params.offset)
        transcripts_orm = list(self.session.execute(stmt).scalars().all())

        summaries = [self._orm_to_transcript_summary(t) for t in transcripts_orm]
        meta = PaginationMeta.from_params(total, params)
        return PaginatedResponse(data=summaries, pagination=meta)

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
        return self._get_transcript_orm(exec_id, synth_id)

    def _get_transcript_orm(self, exec_id: str, synth_id: str) -> TranscriptDetail:
        """Get specific transcript using ORM."""
        stmt = select(TranscriptORM).where(
            TranscriptORM.exec_id == exec_id,
            TranscriptORM.synth_id == synth_id)
        orm_transcript = self.session.execute(stmt).scalar_one_or_none()
        if orm_transcript is None:
            raise TranscriptNotFoundError(exec_id, synth_id)

        return self._orm_to_transcript_detail(orm_transcript)

    # =========================================================================
    # ORM conversion methods
    # =========================================================================

    def _orm_to_summary(self, orm_exec: ResearchExecutionORM) -> ResearchExecutionSummary:
        """Convert ORM model to ResearchExecutionSummary."""
        started_at = orm_exec.started_at
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)

        completed_at = orm_exec.completed_at
        if completed_at and isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)

        return ResearchExecutionSummary(
            exec_id=orm_exec.exec_id,
            experiment_id=orm_exec.experiment_id,
            topic_name=orm_exec.topic_name,
            status=ExecutionStatus(orm_exec.status),
            synth_count=orm_exec.synth_count,
            started_at=started_at,
            completed_at=completed_at)

    def _orm_to_detail(self, orm_exec: ResearchExecutionORM) -> ResearchExecutionDetail:
        """Convert ORM model to ResearchExecutionDetail."""
        started_at = orm_exec.started_at
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)

        completed_at = orm_exec.completed_at
        if completed_at and isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)

        # Check if summary/prfaq exist in experiment_documents
        experiment_id = orm_exec.experiment_id
        summary_available = False
        prfaq_available = False

        if experiment_id:
            from sqlalchemy import text

            # Check for summary in experiment_documents
            summary_stmt = text("""
                SELECT 1 FROM experiment_documents
                WHERE experiment_id = :exp_id AND document_type = 'summary' AND status = 'completed'
            """)
            summary_result = self.session.execute(
                summary_stmt, {"exp_id": experiment_id}
            ).first()
            summary_available = summary_result is not None

            # Check for PR-FAQ in experiment_documents
            prfaq_stmt = text("""
                SELECT 1 FROM experiment_documents
                WHERE experiment_id = :exp_id AND document_type = 'prfaq' AND status = 'completed'
            """)
            prfaq_result = self.session.execute(
                prfaq_stmt, {"exp_id": experiment_id}
            ).first()
            prfaq_available = prfaq_result is not None

        return ResearchExecutionDetail(
            exec_id=orm_exec.exec_id,
            experiment_id=orm_exec.experiment_id,
            topic_name=orm_exec.topic_name,
            status=ExecutionStatus(orm_exec.status),
            synth_count=orm_exec.synth_count,
            started_at=started_at,
            completed_at=completed_at,
            successful_count=orm_exec.successful_count or 0,
            failed_count=orm_exec.failed_count or 0,
            model=orm_exec.model or "gpt-4o-mini",
            max_turns=orm_exec.max_turns or 6,
            summary_available=summary_available,
            prfaq_available=prfaq_available)

    def _orm_to_transcript_summary(self, orm_transcript: TranscriptORM) -> TranscriptSummary:
        """Convert ORM model to TranscriptSummary."""
        timestamp = orm_transcript.timestamp
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        return TranscriptSummary(
            synth_id=orm_transcript.synth_id,
            synth_name=orm_transcript.synth_name,
            turn_count=orm_transcript.turn_count or 0,
            timestamp=timestamp,
            status=orm_transcript.status)

    def _orm_to_transcript_detail(self, orm_transcript: TranscriptORM) -> TranscriptDetail:
        """Convert ORM model to TranscriptDetail."""
        timestamp = orm_transcript.timestamp
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        # Parse messages - ORM stores as list[dict] directly
        messages = []
        if orm_transcript.messages:
            for msg in orm_transcript.messages:
                messages.append(
                    Message(
                        speaker=msg.get("speaker", "Unknown"),
                        text=msg.get("text", ""),
                        internal_notes=msg.get("internal_notes"))
                )

        return TranscriptDetail(
            exec_id=orm_transcript.exec_id,
            synth_id=orm_transcript.synth_id,
            synth_name=orm_transcript.synth_name,
            turn_count=orm_transcript.turn_count or 0,
            timestamp=timestamp,
            status=orm_transcript.status,
            messages=messages)

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
        additional_context: str | None = None) -> None:
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
            additional_context: Optional additional context for the interview.
        """
        orm_exec = ResearchExecutionORM(
            exec_id=exec_id,
            experiment_id=experiment_id,
            topic_name=topic_name,
            synth_count=synth_count,
            model=model,
            max_turns=max_turns,
            status=status.value,
            started_at=datetime.now().isoformat(),
            additional_context=additional_context)
        self._add(orm_exec)
        self._flush()
        self._commit()
        return
    def update_execution_status(
        self,
        exec_id: str,
        status: ExecutionStatus,
        successful_count: int | None = None,
        failed_count: int | None = None) -> None:
        """
        Update execution status and counts.

        Args:
            exec_id: Execution ID.
            status: New status.
            successful_count: Number of successful interviews.
            failed_count: Number of failed interviews.
        """
        orm_exec = self.session.get(ResearchExecutionORM, exec_id)
        if orm_exec is None:
            return

        orm_exec.status = status.value

        if successful_count is not None:
            orm_exec.successful_count = successful_count

        if failed_count is not None:
            orm_exec.failed_count = failed_count

        if status in (ExecutionStatus.COMPLETED, ExecutionStatus.FAILED):
            orm_exec.completed_at = datetime.now().isoformat()

        self._flush()
        self._commit()
        return
    def create_transcript(
        self,
        exec_id: str,
        synth_id: str,
        synth_name: str,
        messages: list[Message],
        status: str = "completed") -> None:
        """
        Create a new transcript record.

        Args:
            exec_id: Execution ID.
            synth_id: Synth ID.
            synth_name: Synth display name.
            messages: List of interview messages.
            status: Transcript status.
        """
        # A turn is a complete exchange (question + answer), so divide by 2
        turn_count = len(messages) // 2

        messages_list = [
            {"speaker": m.speaker, "text": m.text, "internal_notes": m.internal_notes}
            for m in messages
        ]
        orm_transcript = TranscriptORM(
            id=str(uuid4()),
            exec_id=exec_id,
            synth_id=synth_id,
            synth_name=synth_name,
            turn_count=turn_count,
            timestamp=datetime.now().isoformat(),
            status=status,
            messages=messages_list)
        self._add(orm_transcript)
        self._flush()
        self._commit()
        return
    def list_executions_by_experiment(
        self,
        experiment_id: str,
        params: PaginationParams | None = None) -> PaginatedResponse[ResearchExecutionSummary]:
        """
        List research executions for a specific experiment.

        Args:
            experiment_id: Experiment ID to filter by.
            params: Pagination parameters.

        Returns:
            Paginated response with execution summaries.
        """
        params = params or PaginationParams()

        stmt = (
            select(ResearchExecutionORM)
            .where(ResearchExecutionORM.experiment_id == experiment_id)
            .order_by(ResearchExecutionORM.started_at.desc())
        )

        # Get total count
        count_stmt = (
            select(func.count())
            .select_from(ResearchExecutionORM)
            .where(ResearchExecutionORM.experiment_id == experiment_id)
        )
        total = self.session.execute(count_stmt).scalar() or 0

        # Apply pagination
        stmt = stmt.limit(params.limit).offset(params.offset)
        executions_orm = list(self.session.execute(stmt).scalars().all())

        summaries = [self._orm_to_summary(e) for e in executions_orm]
        meta = PaginationMeta.from_params(total, params)
        return PaginatedResponse(data=summaries, pagination=meta)
    def get_auto_interview_for_experiment(
        self, experiment_id: str
    ) -> ResearchExecutionSummary | None:
        """
        Get the most recent auto-interview for an experiment.

        Auto-interviews have topic_name pattern: "exp_{experiment_id}_auto".

        Args:
            experiment_id: Experiment ID to search for.

        Returns:
            Most recent auto-interview execution summary, or None if not found.
        """
        topic_pattern = f"exp_{experiment_id}_auto%"

        stmt = (
            select(ResearchExecutionORM)
            .where(ResearchExecutionORM.experiment_id == experiment_id)
            .where(ResearchExecutionORM.topic_name.like(topic_pattern))
            .order_by(ResearchExecutionORM.started_at.desc())
            .limit(1)
        )
        orm_exec = self.session.execute(stmt).scalar_one_or_none()
        if orm_exec is None:
            return None
        return self._orm_to_summary(orm_exec)
    def check_summaries_exist_batch(self, exec_ids: list[str]) -> dict[str, bool]:
        """
        Check which executions have summary documents in experiment_documents.

        Args:
            exec_ids: List of execution IDs to check.

        Returns:
            Dict mapping exec_id to True if summary exists.
        """
        if not exec_ids:
            return {}

        # Documents are stored by experiment_id in experiment_documents table
        # Join research_executions to experiment_documents to check by exec_id
        from sqlalchemy import text

        stmt = text("""
            SELECT re.exec_id
            FROM research_executions re
            INNER JOIN experiment_documents ed
                ON re.experiment_id = ed.experiment_id
            WHERE re.exec_id IN :exec_ids
            AND ed.document_type = 'summary'
            AND ed.status = 'completed'
        """)
        result = self.session.execute(stmt, {"exec_ids": tuple(exec_ids)})
        return {row[0]: True for row in result}
    def check_prfaqs_exist_batch(self, exec_ids: list[str]) -> dict[str, bool]:
        """
        Check which executions have prfaq documents in experiment_documents.

        Args:
            exec_ids: List of execution IDs to check.

        Returns:
            Dict mapping exec_id to True if prfaq exists and is completed.
        """
        if not exec_ids:
            return {}

        # Documents are stored by experiment_id in experiment_documents table
        # Join research_executions to experiment_documents to check by exec_id
        from sqlalchemy import text

        stmt = text("""
            SELECT re.exec_id
            FROM research_executions re
            INNER JOIN experiment_documents ed
                ON re.experiment_id = ed.experiment_id
            WHERE re.exec_id IN :exec_ids
            AND ed.document_type = 'prfaq'
            AND ed.status = 'completed'
        """)
        result = self.session.execute(stmt, {"exec_ids": tuple(exec_ids)})
        return {row[0]: True for row in result}
    def check_additional_context_exist_batch(self, exec_ids: list[str]) -> dict[str, bool]:
        """
        Check which executions have additional_context filled.

        Args:
            exec_ids: List of execution IDs to check.

        Returns:
            Dict mapping exec_id to True if additional_context exists.
        """
        if not exec_ids:
            return {}

        stmt = (
            select(ResearchExecutionORM.exec_id)
            .where(ResearchExecutionORM.exec_id.in_(exec_ids))
            .where(ResearchExecutionORM.additional_context.isnot(None))
            .where(ResearchExecutionORM.additional_context != "")
        )
        result = self.session.execute(stmt)
        return {row[0]: True for row in result}
    def get_additional_context_batch(self, exec_ids: list[str]) -> dict[str, str | None]:
        """
        Get additional_context text for executions.

        Args:
            exec_ids: List of execution IDs.

        Returns:
            Dict mapping exec_id to additional_context text (or None).
        """
        if not exec_ids:
            return {}

        stmt = (
            select(
                ResearchExecutionORM.exec_id,
                ResearchExecutionORM.additional_context)
            .where(ResearchExecutionORM.exec_id.in_(exec_ids))
        )
        result = self.session.execute(stmt)
        return {row[0]: row[1] for row in result}
    def get_total_turns_batch(self, exec_ids: list[str]) -> dict[str, int]:
        """
        Get total turn count for executions (sum of turns from all transcripts).

        Args:
            exec_ids: List of execution IDs.

        Returns:
            Dict mapping exec_id to total turn count.
        """
        if not exec_ids:
            return {}

        from sqlalchemy import func as sqlfunc

        stmt = (
            select(
                TranscriptORM.exec_id,
                sqlfunc.coalesce(sqlfunc.sum(TranscriptORM.turn_count), 0).label(
                    "total_turns"
                ))
            .where(TranscriptORM.exec_id.in_(exec_ids))
            .group_by(TranscriptORM.exec_id)
        )
        result = self.session.execute(stmt)
        return {row[0]: row[1] for row in result}