"""
PR-FAQ repository for synth-lab.

Data access layer for PR-FAQ document metadata.
Uses ExperimentDocumentRepository internally for data access.

References:
    - Schema: specs/026-experiment-documents/spec.md
    - Entity: synth_lab.domain.entities.experiment_document
"""

from datetime import datetime

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from synth_lab.domain.entities.experiment_document import (
    DocumentStatus,
    DocumentType,
    ExperimentDocument,
)
from synth_lab.models.orm.research import ResearchExecution as ResearchExecutionORM
from synth_lab.models.pagination import PaginatedResponse, PaginationMeta, PaginationParams
from synth_lab.models.prfaq import PRFAQSummary
from synth_lab.repositories.base import BaseRepository
from synth_lab.repositories.experiment_document_repository import ExperimentDocumentRepository
from synth_lab.services.errors import PRFAQNotFoundError


class PRFAQRepository(BaseRepository):
    """Repository for PR-FAQ document data access.

    Uses ExperimentDocumentRepository internally.

    Usage:
        repo = PRFAQRepository(session=session)
    """

    def __init__(self, session: Session | None = None):
        super().__init__(session=session)
        self._doc_repo = ExperimentDocumentRepository(session=self.session)
        self._logger = logger.bind(component="prfaq_repository")

    def _get_experiment_id(self, exec_id: str) -> str | None:
        """Get experiment_id from exec_id."""
        stmt = select(ResearchExecutionORM.experiment_id).where(
            ResearchExecutionORM.exec_id == exec_id
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def _get_execution_info(self, exec_id: str) -> tuple[str | None, str | None]:
        """Get experiment_id and topic_name from exec_id."""
        stmt = select(
            ResearchExecutionORM.experiment_id,
            ResearchExecutionORM.topic_name
        ).where(ResearchExecutionORM.exec_id == exec_id)
        result = self.session.execute(stmt).first()
        if result:
            return result[0], result[1]
        return None, None

    def list_prfaqs(
        self,
        params: PaginationParams
    ) -> PaginatedResponse[PRFAQSummary]:
        """
        List PR-FAQ documents with pagination.

        Args:
            params: Pagination parameters.

        Returns:
            Paginated response with PR-FAQ summaries.
        """
        from sqlalchemy import func as sqlfunc

        from synth_lab.models.orm.document import ExperimentDocument as ExperimentDocumentORM

        # Query experiment_documents with type=prfaq, joined with research_executions
        stmt = (
            select(
                ExperimentDocumentORM,
                ResearchExecutionORM.exec_id,
                ResearchExecutionORM.topic_name
            )
            .join(
                ResearchExecutionORM,
                ExperimentDocumentORM.experiment_id == ResearchExecutionORM.experiment_id
            )
            .where(ExperimentDocumentORM.document_type == DocumentType.RESEARCH_PRFAQ.value)
            .where(ExperimentDocumentORM.status == DocumentStatus.COMPLETED.value)
            .order_by(ExperimentDocumentORM.generated_at.desc())
        )

        # Get total count
        count_stmt = (
            select(sqlfunc.count())
            .select_from(ExperimentDocumentORM)
            .where(ExperimentDocumentORM.document_type == DocumentType.RESEARCH_PRFAQ.value)
            .where(ExperimentDocumentORM.status == DocumentStatus.COMPLETED.value)
        )
        total = self.session.execute(count_stmt).scalar() or 0

        # Apply pagination
        stmt = stmt.limit(params.limit).offset(params.offset)
        results = list(self.session.execute(stmt).all())

        # Convert to summaries
        summaries = []
        for doc_orm, exec_id, topic_name in results:
            summary = self._doc_to_summary(doc_orm, exec_id, topic_name)
            summaries.append(summary)

        meta = PaginationMeta.from_params(total, params)
        return PaginatedResponse(data=summaries, pagination=meta)

    def get_by_exec_id(self, exec_id: str) -> PRFAQSummary:
        """
        Get a PR-FAQ by execution ID.

        Args:
            exec_id: Execution ID.

        Returns:
            PRFAQSummary with metadata.

        Raises:
            PRFAQNotFoundError: If PR-FAQ not found.
        """
        from synth_lab.models.orm.document import ExperimentDocument as ExperimentDocumentORM

        experiment_id, topic_name = self._get_execution_info(exec_id)
        if not experiment_id:
            raise PRFAQNotFoundError(exec_id)

        stmt = (
            select(ExperimentDocumentORM)
            .where(ExperimentDocumentORM.experiment_id == experiment_id)
            .where(ExperimentDocumentORM.document_type == DocumentType.RESEARCH_PRFAQ.value)
        )
        doc_orm = self.session.execute(stmt).scalar_one_or_none()

        if doc_orm is None:
            raise PRFAQNotFoundError(exec_id)

        return self._doc_to_summary(doc_orm, exec_id, topic_name)

    def get_markdown_content(self, exec_id: str) -> str | None:
        """
        Get the PR-FAQ markdown content.

        Args:
            exec_id: Execution ID.

        Returns:
            Markdown content, or None if not set.

        Raises:
            PRFAQNotFoundError: If PR-FAQ not found.
        """
        experiment_id = self._get_experiment_id(exec_id)
        if not experiment_id:
            raise PRFAQNotFoundError(exec_id)

        markdown = self._doc_repo.get_markdown(experiment_id, DocumentType.RESEARCH_PRFAQ)
        if markdown is None:
            # Check if document exists at all
            doc = self._doc_repo.get_by_experiment(experiment_id, DocumentType.RESEARCH_PRFAQ)
            if doc is None:
                raise PRFAQNotFoundError(exec_id)

        return markdown

    def get_json_content(self, exec_id: str) -> str | None:
        """
        Get the PR-FAQ JSON content.

        Args:
            exec_id: Execution ID.

        Returns:
            JSON content string, or None if not set.

        Raises:
            PRFAQNotFoundError: If PR-FAQ not found.
        """
        import json

        experiment_id = self._get_experiment_id(exec_id)
        if not experiment_id:
            raise PRFAQNotFoundError(exec_id)

        doc = self._doc_repo.get_by_experiment(experiment_id, DocumentType.RESEARCH_PRFAQ)
        if doc is None:
            raise PRFAQNotFoundError(exec_id)

        # JSON content is stored in metadata
        if doc.metadata and "json_content" in doc.metadata:
            return doc.metadata["json_content"]
        return None

    def create_pending_prfaq(self, exec_id: str, model: str = "gpt-4o-mini") -> bool:
        """
        Create a pending PR-FAQ record to track generation state.

        This method checks if a PR-FAQ is already being generated to prevent
        concurrent generation requests.

        Args:
            exec_id: Execution ID.
            model: LLM model to use (default: gpt-4o-mini).

        Returns:
            True if pending record created successfully.
            False if already generating (status='generating').
        """
        experiment_id = self._get_experiment_id(exec_id)
        if not experiment_id:
            self._logger.warning(f"[{exec_id}] Execution not linked to experiment")
            return False

        # Check current status
        current_status = self._doc_repo.get_status(experiment_id, DocumentType.RESEARCH_PRFAQ)
        if current_status == DocumentStatus.GENERATING:
            self._logger.warning(
                f"[{exec_id}] PR-FAQ already generating for experiment {experiment_id}"
            )
            return False

        # Create pending document
        doc = self._doc_repo.create_pending(experiment_id, DocumentType.RESEARCH_PRFAQ, model)
        if doc is None:
            return False

        self._logger.info(f"[{exec_id}] PR-FAQ pending created for experiment {experiment_id}")
        return True

    def update_prfaq_status(
        self,
        exec_id: str,
        status: str,
        error_message: str | None = None,
        markdown_content: str | None = None,
        json_content: str | None = None,
        headline: str | None = None,
        one_liner: str | None = None,
        faq_count: int | None = None,
        validation_status: str | None = None,
        confidence_score: float | None = None
    ) -> None:
        """
        Update PR-FAQ status and optionally set content on completion.

        Args:
            exec_id: Execution ID.
            status: New status ('completed', 'failed').
            error_message: Error message if failed.
            markdown_content: Generated markdown content if completed.
            json_content: Generated JSON content if completed.
            headline: Press release headline.
            one_liner: One-line summary.
            faq_count: Number of FAQ items.
            validation_status: Validation status.
            confidence_score: Confidence score.
        """
        experiment_id = self._get_experiment_id(exec_id)
        if not experiment_id:
            self._logger.warning(f"[{exec_id}] Execution not found for status update")
            return

        # Map status string to DocumentStatus
        status_map = {
            "completed": DocumentStatus.COMPLETED,
            "failed": DocumentStatus.FAILED,
            "generating": DocumentStatus.GENERATING,
        }
        doc_status = status_map.get(status, DocumentStatus.COMPLETED)

        # Build metadata
        metadata = {}
        if headline is not None:
            metadata["headline"] = headline
        if one_liner is not None:
            metadata["one_liner"] = one_liner
        if faq_count is not None:
            metadata["faq_count"] = faq_count
        if validation_status is not None:
            metadata["validation_status"] = validation_status
        if confidence_score is not None:
            metadata["confidence_score"] = confidence_score
        if json_content is not None:
            metadata["json_content"] = json_content
        metadata["exec_id"] = exec_id

        self._doc_repo.update_status(
            experiment_id=experiment_id,
            document_type=DocumentType.RESEARCH_PRFAQ,
            status=doc_status,
            markdown_content=markdown_content,
            metadata=metadata if metadata else None,
            error_message=error_message
        )

        self._logger.info(f"[{exec_id}] PR-FAQ status updated to {status}")

    def get_prfaq_status(self, exec_id: str) -> str | None:
        """
        Get the current PR-FAQ generation status.

        Args:
            exec_id: Execution ID.

        Returns:
            Status string ('generating', 'completed', 'failed') or None if not found.
        """
        experiment_id = self._get_experiment_id(exec_id)
        if not experiment_id:
            return None

        status = self._doc_repo.get_status(experiment_id, DocumentType.RESEARCH_PRFAQ)
        if status is None:
            return None

        return status.value

    def create_prfaq_document(
        self,
        exec_id: str,
        markdown_content: str,
        model: str = "gpt-4o-mini",
        json_content: str | None = None,
        headline: str | None = None,
        one_liner: str | None = None,
        faq_count: int = 0,
        validation_status: str = "valid",
        confidence_score: float | None = None
    ) -> None:
        """
        Create or update PR-FAQ metadata.

        Args:
            exec_id: Execution ID.
            model: LLM model used.
            markdown_content: PR-FAQ markdown content.
            json_content: PR-FAQ JSON content (optional).
            headline: Press release headline.
            one_liner: One-line summary.
            faq_count: Number of FAQ items.
            validation_status: Validation status.
            confidence_score: Confidence score.
        """
        from synth_lab.domain.entities.experiment_document import generate_document_id

        experiment_id = self._get_experiment_id(exec_id)
        if not experiment_id:
            self._logger.warning(f"[{exec_id}] Execution not linked to experiment")
            return

        # Build metadata
        metadata = {
            "exec_id": exec_id,
            "headline": headline,
            "one_liner": one_liner,
            "faq_count": faq_count,
            "validation_status": validation_status,
            "confidence_score": confidence_score,
        }
        if json_content:
            metadata["json_content"] = json_content

        # Create document
        doc = ExperimentDocument(
            id=generate_document_id(),
            experiment_id=experiment_id,
            document_type=DocumentType.RESEARCH_PRFAQ,
            markdown_content=markdown_content,
            metadata=metadata,
            model=model,
            status=DocumentStatus.COMPLETED
        )

        self._doc_repo.save(doc)
        self._logger.info(f"[{exec_id}] PR-FAQ metadata created for experiment {experiment_id}")

    def _doc_to_summary(
        self,
        doc_orm,
        exec_id: str,
        topic_name: str | None
    ) -> PRFAQSummary:
        """Convert document ORM to PRFAQSummary."""
        generated_at = doc_orm.generated_at
        if isinstance(generated_at, str):
            generated_at = datetime.fromisoformat(generated_at)

        # Extract metadata fields
        metadata = doc_orm.doc_metadata or {}
        headline = metadata.get("headline")
        one_liner = metadata.get("one_liner")
        faq_count = metadata.get("faq_count", 0)
        validation_status = metadata.get("validation_status", "valid")
        confidence_score = metadata.get("confidence_score")

        return PRFAQSummary(
            exec_id=exec_id,
            topic_name=topic_name,
            headline=headline,
            one_liner=one_liner,
            faq_count=faq_count,
            generated_at=generated_at,
            validation_status=validation_status,
            confidence_score=confidence_score
        )


if __name__ == "__main__":
    import sys

    # Validation - module structure only (no database required)
    all_validation_failures = []
    total_tests = 0

    # Test 1: PRFAQRepository class exists
    total_tests += 1
    try:
        if not callable(PRFAQRepository):
            all_validation_failures.append("PRFAQRepository is not callable")
    except Exception as e:
        all_validation_failures.append(f"PRFAQRepository check failed: {e}")

    # Test 2: Required methods exist
    total_tests += 1
    required_methods = [
        "list_prfaqs",
        "get_by_exec_id",
        "get_markdown_content",
        "get_json_content",
        "create_pending_prfaq",
        "update_prfaq_status",
        "get_prfaq_status",
        "create_prfaq_document",
    ]
    for method in required_methods:
        if not hasattr(PRFAQRepository, method):
            all_validation_failures.append(f"Missing method: {method}")

    # Test 3: PRFAQSummary model exists
    total_tests += 1
    try:
        from synth_lab.models.prfaq import PRFAQSummary

        if not PRFAQSummary:
            all_validation_failures.append("PRFAQSummary import failed")
    except ImportError as e:
        all_validation_failures.append(f"PRFAQSummary import error: {e}")

    # Test 4: DocumentType.RESEARCH_PRFAQ exists
    total_tests += 1
    try:
        if DocumentType.RESEARCH_PRFAQ.value != "prfaq":
            all_validation_failures.append(
                f"DocumentType.RESEARCH_PRFAQ value is {DocumentType.RESEARCH_PRFAQ.value}, expected 'prfaq'"
            )
    except Exception as e:
        all_validation_failures.append(f"DocumentType.RESEARCH_PRFAQ check failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(
            f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("PRFAQRepository is validated and ready for use")
        sys.exit(0)
