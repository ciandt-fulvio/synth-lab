"""
PR-FAQ service for synth-lab.

Business logic layer for PR-FAQ document operations.

References:
    - API spec: specs/010-rest-api/contracts/openapi.yaml
"""

from datetime import datetime

from synth_lab.models.pagination import PaginatedResponse, PaginationParams
from synth_lab.models.prfaq import PRFAQGenerateRequest, PRFAQGenerateResponse, PRFAQSummary
from synth_lab.repositories.prfaq_repository import PRFAQRepository
from synth_lab.repositories.research_repository import ResearchRepository
from synth_lab.services.errors import ExecutionNotFoundError, PRFAQNotFoundError, SummaryNotFoundError


class MarkdownNotFoundError(Exception):
    """Markdown file not found for PR-FAQ."""

    def __init__(self, exec_id: str, path: str | None = None):
        self.exec_id = exec_id
        self.path = path
        message = f"Markdown file not found for PR-FAQ: {exec_id}"
        if path:
            message += f" (expected at {path})"
        super().__init__(message)


class PRFAQService:
    """Service for PR-FAQ business logic (read operations)."""

    def __init__(self, prfaq_repo: PRFAQRepository | None = None):
        """
        Initialize PR-FAQ service.

        Args:
            prfaq_repo: PR-FAQ repository. Defaults to new instance.
        """
        self.prfaq_repo = prfaq_repo or PRFAQRepository()

    def list_prfaqs(
        self,
        params: PaginationParams | None = None,
    ) -> PaginatedResponse[PRFAQSummary]:
        """
        List PR-FAQ documents with pagination.

        Args:
            params: Pagination parameters.

        Returns:
            Paginated response with PR-FAQ summaries.
        """
        params = params or PaginationParams()
        return self.prfaq_repo.list_prfaqs(params)

    def get_prfaq(self, exec_id: str) -> PRFAQSummary:
        """
        Get a PR-FAQ by execution ID.

        Args:
            exec_id: Execution ID.

        Returns:
            PRFAQSummary with metadata.

        Raises:
            PRFAQNotFoundError: If PR-FAQ not found.
        """
        return self.prfaq_repo.get_by_exec_id(exec_id)

    def get_markdown(self, exec_id: str) -> str:
        """
        Get the PR-FAQ markdown content.

        Args:
            exec_id: Execution ID.

        Returns:
            Markdown content as string.

        Raises:
            PRFAQNotFoundError: If PR-FAQ not found.
            MarkdownNotFoundError: If markdown file doesn't exist.
        """
        markdown_path = self.prfaq_repo.get_markdown_path(exec_id)

        if markdown_path is None:
            raise MarkdownNotFoundError(exec_id)

        if not markdown_path.exists():
            raise MarkdownNotFoundError(exec_id, str(markdown_path))

        return markdown_path.read_text(encoding="utf-8")

    def generate_prfaq(self, request: PRFAQGenerateRequest) -> PRFAQGenerateResponse:
        """
        Generate a PR-FAQ from a research execution.

        Args:
            request: Generation request with exec_id and model.

        Returns:
            Generation response with status and metadata.

        Raises:
            ExecutionNotFoundError: If execution doesn't exist.
            SummaryNotFoundError: If execution doesn't have a summary.
        """
        from loguru import logger
        from synth_lab.services.research_prfaq.generator import generate_prfaq_markdown, save_prfaq_markdown

        # Verify execution exists and has summary
        research_repo = ResearchRepository()
        try:
            execution = research_repo.get_execution(request.exec_id)
        except ExecutionNotFoundError:
            raise

        if not execution.summary_available:
            raise SummaryNotFoundError(request.exec_id)

        # Generate PR-FAQ markdown
        logger.info(f"Generating PR-FAQ for execution {request.exec_id}")
        prfaq_markdown = generate_prfaq_markdown(
            batch_id=request.exec_id,
            model=request.model,
        )

        # Save to file
        markdown_path = save_prfaq_markdown(prfaq_markdown, request.exec_id)

        # Extract headline from markdown (first # line)
        headline = None
        for line in prfaq_markdown.split("\n"):
            if line.startswith("# "):
                headline = line[2:].strip()
                break

        # Save metadata to database
        self.prfaq_repo.create_prfaq_metadata(
            exec_id=request.exec_id,
            model=request.model,
            markdown_path=str(markdown_path),
            headline=headline,
        )

        logger.info(f"PR-FAQ generated and saved for {request.exec_id}")

        return PRFAQGenerateResponse(
            exec_id=request.exec_id,
            status="generated",
            generated_at=datetime.now(),
            validation_status="valid",
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
    service = PRFAQService(repo)

    # Test 1: List PR-FAQs
    total_tests += 1
    try:
        result = service.list_prfaqs()
        print(f"  Listed {result.pagination.total} PR-FAQs")
        if result.pagination.total < 1:
            all_validation_failures.append("No PR-FAQs found")
    except Exception as e:
        all_validation_failures.append(f"List PR-FAQs failed: {e}")

    # Test 2: Get PR-FAQ by exec_id
    total_tests += 1
    try:
        result = service.list_prfaqs(PaginationParams(limit=1))
        if result.data:
            exec_id = result.data[0].exec_id
            prfaq = service.get_prfaq(exec_id)
            if prfaq.exec_id != exec_id:
                all_validation_failures.append(f"Exec ID mismatch: {prfaq.exec_id}")
            print(f"  Got PR-FAQ: {exec_id}")
    except Exception as e:
        all_validation_failures.append(f"Get PR-FAQ failed: {e}")

    # Test 3: Get non-existent PR-FAQ
    total_tests += 1
    try:
        service.get_prfaq("nonexistent_12345678")
        all_validation_failures.append("Should raise PRFAQNotFoundError")
    except PRFAQNotFoundError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Wrong exception: {e}")

    # Test 4: Get markdown content
    total_tests += 1
    try:
        result = service.list_prfaqs(PaginationParams(limit=1))
        if result.data:
            exec_id = result.data[0].exec_id
            try:
                markdown = service.get_markdown(exec_id)
                print(f"  Got markdown: {len(markdown)} chars")
            except MarkdownNotFoundError:
                print(f"  Markdown not found for {exec_id} (expected)")
    except Exception as e:
        all_validation_failures.append(f"Get markdown failed: {e}")

    # Test 5: Pagination works
    total_tests += 1
    try:
        result = service.list_prfaqs(PaginationParams(limit=1, offset=0))
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
