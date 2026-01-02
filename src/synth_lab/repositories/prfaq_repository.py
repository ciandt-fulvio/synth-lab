"""
PR-FAQ repository for synth-lab.

Data access layer for PR-FAQ document metadata (database + filesystem).
Uses SQLAlchemy ORM for database operations.

References:
    - Schema: specs/010-rest-api/data-model.md
    - ORM model: synth_lab.models.orm.legacy.PRFAQMetadata
"""

from datetime import datetime

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from synth_lab.models.orm.legacy import PRFAQMetadata as PRFAQMetadataORM
from synth_lab.models.orm.research import ResearchExecution as ResearchExecutionORM
from synth_lab.models.pagination import PaginatedResponse, PaginationMeta, PaginationParams
from synth_lab.models.prfaq import PRFAQSummary
from synth_lab.repositories.base import BaseRepository
from synth_lab.services.errors import PRFAQNotFoundError


class PRFAQRepository(BaseRepository):
    """Repository for PR-FAQ document data access.

    Uses SQLAlchemy ORM for database operations.

    Usage:
        # ORM mode
        repo = PRFAQRepository(db=database_manager)

        # ORM mode (SQLAlchemy)
        repo = PRFAQRepository(session=session)
    """

    def __init__(
        self,
session: Session | None = None):
        super().__init__( session=session)

    def list_prfaqs(
        self,
        params: PaginationParams) -> PaginatedResponse[PRFAQSummary]:
        """
        List PR-FAQ documents with pagination.

        Args:
            params: Pagination parameters.

        Returns:
            Paginated response with PR-FAQ summaries.
        """
        return self._list_prfaqs_orm(params)

    def _list_prfaqs_orm(self, params: PaginationParams) -> PaginatedResponse[PRFAQSummary]:
        """List PR-FAQs using ORM with eager-loaded relationships."""
        from sqlalchemy import func as sqlfunc

        # Base query with join to get topic_name
        stmt = (
            select(PRFAQMetadataORM, ResearchExecutionORM.topic_name)
            .outerjoin(
                ResearchExecutionORM,
                PRFAQMetadataORM.exec_id == ResearchExecutionORM.exec_id)
            .order_by(PRFAQMetadataORM.generated_at.desc())
        )

        # Get total count
        count_stmt = select(sqlfunc.count()).select_from(PRFAQMetadataORM)
        total = self.session.execute(count_stmt).scalar() or 0

        # Apply pagination
        stmt = stmt.limit(params.limit).offset(params.offset)
        results = list(self.session.execute(stmt).all())

        # Convert to summaries
        summaries = [
            self._orm_to_summary(prfaq_orm, topic_name)
            for prfaq_orm, topic_name in results
        ]
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
        return self._get_by_exec_id_orm(exec_id)

    def _get_by_exec_id_orm(self, exec_id: str) -> PRFAQSummary:
        """Get PR-FAQ by exec_id using ORM."""
        stmt = (
            select(PRFAQMetadataORM, ResearchExecutionORM.topic_name)
            .outerjoin(
                ResearchExecutionORM,
                PRFAQMetadataORM.exec_id == ResearchExecutionORM.exec_id)
            .where(PRFAQMetadataORM.exec_id == exec_id)
        )
        result = self.session.execute(stmt).first()

        if result is None:
            raise PRFAQNotFoundError(exec_id)

        prfaq_orm, topic_name = result
        return self._orm_to_summary(prfaq_orm, topic_name)

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
        return self._get_markdown_content_orm(exec_id)

    def _get_markdown_content_orm(self, exec_id: str) -> str | None:
        """Get markdown content using ORM."""
        stmt = select(PRFAQMetadataORM.markdown_content).where(
            PRFAQMetadataORM.exec_id == exec_id
        )
        result = self.session.execute(stmt).scalar_one_or_none()

        if result is None:
            # Check if the record exists
            exists_stmt = select(PRFAQMetadataORM.exec_id).where(
                PRFAQMetadataORM.exec_id == exec_id
            )
            if self.session.execute(exists_stmt).scalar_one_or_none() is None:
                raise PRFAQNotFoundError(exec_id)

        return result

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
        return self._get_json_content_orm(exec_id)

    def _get_json_content_orm(self, exec_id: str) -> str | None:
        """Get JSON content using ORM."""
        stmt = select(PRFAQMetadataORM.json_content).where(
            PRFAQMetadataORM.exec_id == exec_id
        )
        result = self.session.execute(stmt).scalar_one_or_none()

        if result is None:
            # Check if the record exists
            exists_stmt = select(PRFAQMetadataORM.exec_id).where(
                PRFAQMetadataORM.exec_id == exec_id
            )
            if self.session.execute(exists_stmt).scalar_one_or_none() is None:
                raise PRFAQNotFoundError(exec_id)

        return result

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
        return self._create_pending_prfaq_orm(exec_id, model)

    def _create_pending_prfaq_orm(self, exec_id: str, model: str = "gpt-4o-mini") -> bool:
        """Create pending PR-FAQ using ORM."""
        # Check if already generating
        stmt = select(PRFAQMetadataORM).where(PRFAQMetadataORM.exec_id == exec_id)
        existing = self.session.execute(stmt).scalar_one_or_none()

        if existing and existing.status == "generating":
            logger.warning(
                f"[{exec_id}] PR-FAQ state transition blocked: already in 'generating' state"
            )
            return False  # Already generating, prevent concurrent request

        previous_status = existing.status if existing else None

        if existing:
            # Update existing record
            existing.status = "generating"
            existing.started_at = datetime.now().isoformat()
            existing.model = model
            existing.error_message = None
        else:
            # Insert new record
            new_prfaq = PRFAQMetadataORM(
                exec_id=exec_id,
                status="generating",
                started_at=datetime.now().isoformat(),
                model=model)
            self._add(new_prfaq)

        self._flush()
        self._commit()

        logger.info(
            f"[{exec_id}] PR-FAQ state transition: {previous_status or 'none'} -> generating"
        )
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
        confidence_score: float | None = None) -> None:
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
        self._update_prfaq_status_orm(
            exec_id=exec_id,
            status=status,
            error_message=error_message,
            markdown_content=markdown_content,
            json_content=json_content,
            headline=headline,
            one_liner=one_liner,
            faq_count=faq_count,
            validation_status=validation_status,
            confidence_score=confidence_score)
        return
    def _update_prfaq_status_orm(
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
        confidence_score: float | None = None) -> None:
        """Update PR-FAQ status using ORM."""
        stmt = select(PRFAQMetadataORM).where(PRFAQMetadataORM.exec_id == exec_id)
        orm_prfaq = self.session.execute(stmt).scalar_one_or_none()

        if orm_prfaq is None:
            logger.warning(f"[{exec_id}] PR-FAQ not found for status update")
            return

        previous_status = orm_prfaq.status
        orm_prfaq.status = status

        if status == "completed":
            orm_prfaq.generated_at = datetime.now().isoformat()

        if error_message is not None:
            orm_prfaq.error_message = error_message

        if markdown_content is not None:
            orm_prfaq.markdown_content = markdown_content

        if json_content is not None:
            orm_prfaq.json_content = json_content

        if headline is not None:
            orm_prfaq.headline = headline

        if one_liner is not None:
            orm_prfaq.one_liner = one_liner

        if faq_count is not None:
            orm_prfaq.faq_count = faq_count

        if validation_status is not None:
            orm_prfaq.validation_status = validation_status

        if confidence_score is not None:
            orm_prfaq.confidence_score = confidence_score

        self._flush()
        self._commit()

        # Log state transition
        if status == "completed":
            content_size = len(markdown_content) if markdown_content else 0
            logger.info(
                f"[{exec_id}] PR-FAQ state transition: "
                f"{previous_status} -> {status} (content: {content_size} chars)"
            )
        elif status == "failed":
            logger.warning(
                f"[{exec_id}] PR-FAQ state transition: "
                f"{previous_status} -> {status} (error: {error_message})"
            )
        else:
            logger.info(f"[{exec_id}] PR-FAQ state transition: {previous_status} -> {status}")

    def get_prfaq_status(self, exec_id: str) -> str | None:
        """
        Get the current PR-FAQ generation status.

        Args:
            exec_id: Execution ID.

        Returns:
            Status string ('generating', 'completed', 'failed') or None if not found.
        """
        return self._get_prfaq_status_orm(exec_id)

    def _get_prfaq_status_orm(self, exec_id: str) -> str | None:
        """Get PR-FAQ status using ORM."""
        stmt = select(PRFAQMetadataORM.status).where(PRFAQMetadataORM.exec_id == exec_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def create_prfaq_metadata(
        self,
        exec_id: str,
        markdown_content: str,
        model: str = "gpt-4o-mini",
        json_content: str | None = None,
        headline: str | None = None,
        one_liner: str | None = None,
        faq_count: int = 0,
        validation_status: str = "valid",
        confidence_score: float | None = None) -> None:
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
        self._create_prfaq_metadata_orm(
            exec_id=exec_id,
            markdown_content=markdown_content,
            model=model,
            json_content=json_content,
            headline=headline,
            one_liner=one_liner,
            faq_count=faq_count,
            validation_status=validation_status,
            confidence_score=confidence_score)
        return
    def _create_prfaq_metadata_orm(
        self,
        exec_id: str,
        markdown_content: str,
        model: str = "gpt-4o-mini",
        json_content: str | None = None,
        headline: str | None = None,
        one_liner: str | None = None,
        faq_count: int = 0,
        validation_status: str = "valid",
        confidence_score: float | None = None) -> None:
        """Create or update PR-FAQ metadata using ORM."""
        stmt = select(PRFAQMetadataORM).where(PRFAQMetadataORM.exec_id == exec_id)
        existing = self.session.execute(stmt).scalar_one_or_none()

        generated_at = datetime.now().isoformat()

        if existing:
            # Update existing record
            existing.generated_at = generated_at
            existing.model = model
            existing.markdown_content = markdown_content
            existing.json_content = json_content
            existing.headline = headline
            existing.one_liner = one_liner
            existing.faq_count = faq_count
            existing.validation_status = validation_status
            existing.confidence_score = confidence_score
            existing.status = "completed"
        else:
            # Insert new record
            new_prfaq = PRFAQMetadataORM(
                exec_id=exec_id,
                generated_at=generated_at,
                model=model,
                markdown_content=markdown_content,
                json_content=json_content,
                headline=headline,
                one_liner=one_liner,
                faq_count=faq_count,
                validation_status=validation_status,
                confidence_score=confidence_score,
                status="completed")
            self._add(new_prfaq)

        self._flush()
        self._commit()

    def _row_to_summary(self, row) -> PRFAQSummary:
        """Convert a database row to PRFAQSummary."""
        # Handle generated_at - might be ISO string
        generated_at = row["generated_at"]
        if isinstance(generated_at, str):
            generated_at = datetime.fromisoformat(generated_at)

        return PRFAQSummary(
            exec_id=row["exec_id"],
            topic_name=row["topic_name"] if "topic_name" in row.keys() else None,
            headline=row["headline"],
            one_liner=row["one_liner"],
            faq_count=row["faq_count"] or 0,
            generated_at=generated_at,
            validation_status=row["validation_status"] or "valid",
            confidence_score=row["confidence_score"])

    # =========================================================================
    # ORM conversion methods
    # =========================================================================

    def _orm_to_summary(
        self,
        orm_prfaq: PRFAQMetadataORM,
        topic_name: str | None = None) -> PRFAQSummary:
        """Convert ORM model to PRFAQSummary."""
        generated_at = orm_prfaq.generated_at
        if isinstance(generated_at, str):
            generated_at = datetime.fromisoformat(generated_at)

        return PRFAQSummary(
            exec_id=orm_prfaq.exec_id,
            topic_name=topic_name,
            headline=orm_prfaq.headline,
            one_liner=orm_prfaq.one_liner,
            faq_count=orm_prfaq.faq_count or 0,
            generated_at=generated_at,
            validation_status=orm_prfaq.validation_status or "valid",
            confidence_score=orm_prfaq.confidence_score)


if __name__ == "__main__":
    import sys
    import tempfile
    from pathlib import Path


    # Validation
    all_validation_failures = []
    total_tests = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test.db"
        db = DatabaseManager(test_db_path)

        # Create tables
        db.execute(
            """
            CREATE TABLE research_executions (
                exec_id TEXT PRIMARY KEY,
                topic_name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                started_at TEXT NOT NULL
            )
            """
        )
        db.execute(
            """
            CREATE TABLE prfaq_metadata (
                exec_id TEXT PRIMARY KEY,
                generated_at TEXT,
                model TEXT DEFAULT 'gpt-4o-mini',
                validation_status TEXT DEFAULT 'valid',
                confidence_score REAL,
                headline TEXT,
                one_liner TEXT,
                faq_count INTEGER DEFAULT 0,
                markdown_content TEXT,
                json_content TEXT,
                status TEXT DEFAULT 'completed',
                error_message TEXT,
                started_at TEXT,
                FOREIGN KEY (exec_id) REFERENCES research_executions(exec_id)
            )
            """
        )

        # Insert test data
        db.execute(
            """
            INSERT INTO research_executions (exec_id, topic_name, status, started_at)
            VALUES ('batch_test_20251219_120000', 'compra-amazon', 'completed', datetime('now'))
            """
        )
        db.execute(
            """
            INSERT INTO prfaq_metadata
            (exec_id, generated_at, model, headline, one_liner, faq_count,
             markdown_content, status, validation_status, confidence_score)
            VALUES ('batch_test_20251219_120000', datetime('now'), 'gpt-4o-mini',
                    'Nova Experiencia de Compra', 'Revolucionando compras online', 5,
                    '# PR-FAQ\\n\\nTest content', 'completed', 'valid', 0.95)
            """
        )

        repo = PRFAQRepository()

        # Test 1: List PR-FAQs
        total_tests += 1
        try:
            result = repo.list_prfaqs(PaginationParams(limit=10))
            if result.pagination.total != 1:
                all_validation_failures.append(
                    f"Expected 1 PR-FAQ, got {result.pagination.total}"
                )
        except Exception as e:
            all_validation_failures.append(f"List PR-FAQs failed: {e}")

        # Test 2: Get PR-FAQ by exec_id
        total_tests += 1
        try:
            prfaq = repo.get_by_exec_id("batch_test_20251219_120000")
            if prfaq.exec_id != "batch_test_20251219_120000":
                all_validation_failures.append(f"Exec ID mismatch: {prfaq.exec_id}")
            if prfaq.topic_name != "compra-amazon":
                all_validation_failures.append(f"Topic name mismatch: {prfaq.topic_name}")
            if prfaq.headline != "Nova Experiencia de Compra":
                all_validation_failures.append(f"Headline mismatch: {prfaq.headline}")
        except Exception as e:
            all_validation_failures.append(f"Get PR-FAQ failed: {e}")

        # Test 3: Get non-existent PR-FAQ raises error
        total_tests += 1
        try:
            repo.get_by_exec_id("nonexistent_12345678")
            all_validation_failures.append("Should raise PRFAQNotFoundError")
        except PRFAQNotFoundError:
            pass  # Expected
        except Exception as e:
            all_validation_failures.append(f"Wrong exception: {e}")

        # Test 4: Get markdown content
        total_tests += 1
        try:
            markdown = repo.get_markdown_content("batch_test_20251219_120000")
            if markdown != "# PR-FAQ\\n\\nTest content":
                all_validation_failures.append(f"Markdown content mismatch: {markdown}")
        except Exception as e:
            all_validation_failures.append(f"Get markdown content failed: {e}")

        # Test 5: Get markdown for non-existent raises error
        total_tests += 1
        try:
            repo.get_markdown_content("nonexistent_12345678")
            all_validation_failures.append("Should raise PRFAQNotFoundError for markdown")
        except PRFAQNotFoundError:
            pass  # Expected
        except Exception as e:
            all_validation_failures.append(f"Wrong exception for markdown: {e}")

        # Test 6: Get status
        total_tests += 1
        try:
            status = repo.get_prfaq_status("batch_test_20251219_120000")
            if status != "completed":
                all_validation_failures.append(f"Status should be 'completed': {status}")
        except Exception as e:
            all_validation_failures.append(f"Get status failed: {e}")

        # Test 7: Get non-existent status returns None
        total_tests += 1
        try:
            status = repo.get_prfaq_status("nonexistent_12345678")
            if status is not None:
                all_validation_failures.append(f"Status should be None: {status}")
        except Exception as e:
            all_validation_failures.append(f"Get nonexistent status failed: {e}")

        # Test 8: Create pending PR-FAQ
        total_tests += 1
        try:
            # Create a new research execution for pending test
            db.execute(
                """
                INSERT INTO research_executions (exec_id, topic_name, status, started_at)
                VALUES ('batch_pending_test', 'test-topic', 'completed', datetime('now'))
                """
            )
            result = repo.create_pending_prfaq("batch_pending_test")
            if not result:
                all_validation_failures.append("create_pending_prfaq should return True")
            status = repo.get_prfaq_status("batch_pending_test")
            if status != "generating":
                all_validation_failures.append(f"Status should be 'generating': {status}")
        except Exception as e:
            all_validation_failures.append(f"Create pending PR-FAQ failed: {e}")

        # Test 9: Prevent concurrent generation
        total_tests += 1
        try:
            result = repo.create_pending_prfaq("batch_pending_test")
            if result:
                all_validation_failures.append(
                    "create_pending_prfaq should return False for concurrent"
                )
        except Exception as e:
            all_validation_failures.append(f"Concurrent prevention test failed: {e}")

        # Test 10: Update status to completed
        total_tests += 1
        try:
            repo.update_prfaq_status(
                exec_id="batch_pending_test",
                status="completed",
                markdown_content="# Test PR-FAQ\n\nContent",
                headline="Test Headline",
                one_liner="Test one-liner",
                faq_count=3,
                validation_status="valid",
                confidence_score=0.88)
            status = repo.get_prfaq_status("batch_pending_test")
            if status != "completed":
                all_validation_failures.append(f"Status should be 'completed': {status}")
        except Exception as e:
            all_validation_failures.append(f"Update status failed: {e}")

        # Test 11: Create PR-FAQ metadata directly
        total_tests += 1
        try:
            db.execute(
                """
                INSERT INTO research_executions (exec_id, topic_name, status, started_at)
                VALUES ('batch_create_test', 'create-topic', 'completed', datetime('now'))
                """
            )
            repo.create_prfaq_metadata(
                exec_id="batch_create_test",
                markdown_content="# Created PR-FAQ\n\nDirect creation",
                headline="Created Headline",
                one_liner="Created one-liner",
                faq_count=2)
            prfaq = repo.get_by_exec_id("batch_create_test")
            if prfaq.headline != "Created Headline":
                all_validation_failures.append(f"Headline mismatch: {prfaq.headline}")
        except Exception as e:
            all_validation_failures.append(f"Create PR-FAQ metadata failed: {e}")

        # Test 12: Pagination
        total_tests += 1
        try:
            result = repo.list_prfaqs(PaginationParams(limit=1, offset=0))
            if result.pagination.limit != 1:
                all_validation_failures.append(f"Limit should be 1: {result.pagination.limit}")
            if len(result.data) != 1:
                all_validation_failures.append(f"Should have 1 item: {len(result.data)}")
        except Exception as e:
            all_validation_failures.append(f"Pagination test failed: {e}")

        db.close()

    # Final validation result
    if all_validation_failures:
        print(
            f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("PRFAQRepository is validated and ready for use")
        sys.exit(0)
