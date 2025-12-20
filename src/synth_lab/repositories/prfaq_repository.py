"""
PR-FAQ repository for synth-lab.

Data access layer for PR-FAQ document metadata (database + filesystem).

References:
    - Schema: specs/010-rest-api/data-model.md
"""

from datetime import datetime
from pathlib import Path

from synth_lab.infrastructure.config import DB_PATH
from synth_lab.infrastructure.database import DatabaseManager
from synth_lab.models.pagination import PaginatedResponse, PaginationParams
from synth_lab.models.prfaq import PRFAQSummary
from synth_lab.repositories.base import BaseRepository
from synth_lab.services.errors import PRFAQNotFoundError


class PRFAQRepository(BaseRepository):
    """Repository for PR-FAQ document data access."""

    def __init__(self, db: DatabaseManager | None = None):
        if db is None:
            db = DatabaseManager(DB_PATH)
        super().__init__(db)

    def list_prfaqs(
        self,
        params: PaginationParams,
    ) -> PaginatedResponse[PRFAQSummary]:
        """
        List PR-FAQ documents with pagination.

        Args:
            params: Pagination parameters.

        Returns:
            Paginated response with PR-FAQ summaries.
        """
        # Join with research_executions to get topic_name
        base_query = """
            SELECT
                p.exec_id,
                r.topic_name,
                p.headline,
                p.one_liner,
                p.faq_count,
                p.generated_at,
                p.validation_status,
                p.confidence_score
            FROM prfaq_metadata p
            LEFT JOIN research_executions r ON p.exec_id = r.exec_id
        """
        count_query = "SELECT COUNT(*) as count FROM prfaq_metadata"

        rows, meta = self._paginate_query(
            base_query,
            params,
            count_query=count_query,
        )

        prfaqs = [self._row_to_summary(row) for row in rows]
        return PaginatedResponse(data=prfaqs, pagination=meta)

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
        query = """
            SELECT
                p.exec_id,
                r.topic_name,
                p.headline,
                p.one_liner,
                p.faq_count,
                p.generated_at,
                p.validation_status,
                p.confidence_score
            FROM prfaq_metadata p
            LEFT JOIN research_executions r ON p.exec_id = r.exec_id
            WHERE p.exec_id = ?
        """
        row = self.db.fetchone(query, (exec_id,))

        if row is None:
            raise PRFAQNotFoundError(exec_id)

        return self._row_to_summary(row)

    def get_markdown_path(self, exec_id: str) -> Path | None:
        """
        Get the path to the PR-FAQ markdown file.

        Args:
            exec_id: Execution ID.

        Returns:
            Path to markdown file, or None if not set.

        Raises:
            PRFAQNotFoundError: If PR-FAQ not found.
        """
        query = "SELECT markdown_path FROM prfaq_metadata WHERE exec_id = ?"
        row = self.db.fetchone(query, (exec_id,))

        if row is None:
            raise PRFAQNotFoundError(exec_id)

        markdown_path = row["markdown_path"]
        if markdown_path:
            return Path(markdown_path)
        return None

    def create_prfaq_metadata(
        self,
        exec_id: str,
        model: str,
        markdown_path: str,
        headline: str | None = None,
        one_liner: str | None = None,
        faq_count: int = 0,
        validation_status: str = "valid",
        confidence_score: float | None = None,
    ) -> None:
        """
        Create or update PR-FAQ metadata.

        Args:
            exec_id: Execution ID.
            model: LLM model used.
            markdown_path: Path to markdown file.
            headline: Press release headline.
            one_liner: One-line summary.
            faq_count: Number of FAQ items.
            validation_status: Validation status.
            confidence_score: Confidence score.
        """
        # Use REPLACE to handle both insert and update
        query = """
            INSERT OR REPLACE INTO prfaq_metadata
            (exec_id, generated_at, model, markdown_path, headline, one_liner,
             faq_count, validation_status, confidence_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute(
            query,
            (
                exec_id,
                datetime.now().isoformat(),
                model,
                markdown_path,
                headline,
                one_liner,
                faq_count,
                validation_status,
                confidence_score,
            ),
        )

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
            confidence_score=row["confidence_score"],
        )


if __name__ == "__main__":
    import sys

    from synth_lab.infrastructure.config import DB_PATH
    from synth_lab.infrastructure.database import DatabaseManager

    # Validation with real data
    all_validation_failures = []
    total_tests = 0

    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}. Run migration first.")
        sys.exit(1)

    db = DatabaseManager(DB_PATH)
    repo = PRFAQRepository(db)

    # Test 1: List PR-FAQs
    total_tests += 1
    try:
        result = repo.list_prfaqs(PaginationParams(limit=10))
        print(f"  Found {result.pagination.total} PR-FAQs")
        if result.pagination.total < 1:
            all_validation_failures.append("No PR-FAQs found")
    except Exception as e:
        all_validation_failures.append(f"List PR-FAQs failed: {e}")

    # Test 2: Get PR-FAQ by exec_id
    total_tests += 1
    try:
        result = repo.list_prfaqs(PaginationParams(limit=1))
        if result.data:
            exec_id = result.data[0].exec_id
            prfaq = repo.get_by_exec_id(exec_id)
            if prfaq.exec_id != exec_id:
                all_validation_failures.append(f"Exec ID mismatch: {prfaq.exec_id}")
            print(f"  Got PR-FAQ: {exec_id}")
            print(f"    - Topic: {prfaq.topic_name}")
            print(f"    - Headline: {prfaq.headline}")
    except Exception as e:
        all_validation_failures.append(f"Get PR-FAQ failed: {e}")

    # Test 3: Get non-existent PR-FAQ
    total_tests += 1
    try:
        repo.get_by_exec_id("nonexistent_12345678")
        all_validation_failures.append("Should raise PRFAQNotFoundError")
    except PRFAQNotFoundError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Wrong exception: {e}")

    # Test 4: Get markdown path
    total_tests += 1
    try:
        result = repo.list_prfaqs(PaginationParams(limit=1))
        if result.data:
            exec_id = result.data[0].exec_id
            markdown_path = repo.get_markdown_path(exec_id)
            if markdown_path:
                print(f"  Markdown path: {markdown_path}")
                if not markdown_path.exists():
                    print("    (file does not exist)")
            else:
                print(f"  No markdown path for {exec_id}")
    except Exception as e:
        all_validation_failures.append(f"Get markdown path failed: {e}")

    # Test 5: Pagination works
    total_tests += 1
    try:
        result = repo.list_prfaqs(PaginationParams(limit=1, offset=0))
        if result.pagination.limit != 1:
            all_validation_failures.append(f"Limit should be 1: {result.pagination.limit}")
    except Exception as e:
        all_validation_failures.append(f"Pagination test failed: {e}")

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
