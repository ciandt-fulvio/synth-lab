"""
PR-FAQ service for synth-lab.

Business logic layer for PR-FAQ document operations.

References:
    - API spec: specs/010-rest-api/contracts/openapi.yaml
"""


from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes

from synth_lab.domain.entities.experiment_document import ExperimentDocument
from synth_lab.infrastructure.phoenix_tracing import get_tracer
from synth_lab.models.pagination import PaginatedResponse, PaginationParams
from synth_lab.models.prfaq import PRFAQGenerateRequest, PRFAQSummary
from synth_lab.repositories.prfaq_repository import PRFAQRepository
from synth_lab.repositories.research_repository import ResearchRepository
from synth_lab.services.errors import (
    ExecutionNotFoundError,
    PRFAQNotFoundError,
    SummaryNotFoundError,
)


class PRFAQAlreadyGeneratingError(Exception):
    """PR-FAQ is already being generated for this execution."""

    def __init__(self, exec_id: str):
        self.exec_id = exec_id
        message = f"PR-FAQ is already being generated for execution: {exec_id}"
        super().__init__(message)


class MarkdownNotFoundError(Exception):
    """Markdown content not found for PR-FAQ."""

    def __init__(self, exec_id: str):
        self.exec_id = exec_id
        message = f"Markdown content not found for PR-FAQ: {exec_id}"
        super().__init__(message)


# Phoenix/OpenTelemetry tracer for observability
_tracer = get_tracer("prfaq-service")


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
        params: PaginationParams | None = None) -> PaginatedResponse[PRFAQSummary]:
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
            MarkdownNotFoundError: If markdown content doesn't exist.
        """
        markdown_content = self.prfaq_repo.get_markdown_content(exec_id)

        if markdown_content is None:
            raise MarkdownNotFoundError(exec_id)

        return markdown_content

    def generate_prfaq(self, request: PRFAQGenerateRequest) -> "ExperimentDocument":
        """
        Generate a PR-FAQ from a research execution.

        Note: The 'generating' status should be set by the router before calling this method
        via doc_service.start_generation() to prevent race conditions.

        Args:
            request: Generation request with exec_id and model.

        Returns:
            ExperimentDocument with generated PRFAQ.

        Raises:
            ExecutionNotFoundError: If execution doesn't exist.
            SummaryNotFoundError: If execution doesn't have a summary.
        """
        from loguru import logger

        from synth_lab.domain.entities.experiment_document import DocumentType
        from synth_lab.services.document_service import DocumentService
        from synth_lab.services.research_prfaq.generator import generate_prfaq_from_content

        # Verify execution exists
        research_repo = ResearchRepository()
        try:
            execution = research_repo.get_execution(request.exec_id)
        except ExecutionNotFoundError:
            raise

        with _tracer.start_as_current_span(
            f"Generate Research PR-FAQ: {execution.topic_name}",
            attributes={
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.CHAIN.value,
                "exec_id": request.exec_id,
                "topic_name": execution.topic_name,
                "model": request.model,
            },
        ) as span:
            doc_service = DocumentService()

            try:
                # Verify experiment_id is set (required for saving document)
                if not execution.experiment_id:
                    doc_service.fail_generation(
                        execution.experiment_id or "",
                        DocumentType.RESEARCH_PRFAQ,
                        "Execution not linked to an experiment",
                        source_id=request.exec_id)
                    raise SummaryNotFoundError(request.exec_id)

                try:
                    summary_content = doc_service.get_markdown(
                        execution.experiment_id,
                        DocumentType.RESEARCH_SUMMARY,
                        source_id=request.exec_id,
                    )
                except Exception:
                    # Summary not found in experiment_documents
                    doc_service.fail_generation(
                        execution.experiment_id,
                        DocumentType.RESEARCH_PRFAQ,
                        "Summary content not found in experiment_documents",
                        source_id=request.exec_id)
                    raise SummaryNotFoundError(request.exec_id)

                if span:
                    span.set_attribute("summary_length", len(summary_content))

                # Generate PR-FAQ markdown from summary content
                logger.info(f"Generating PR-FAQ for execution {request.exec_id}")
                prfaq_markdown = generate_prfaq_from_content(
                    summary_content=summary_content,
                    batch_id=request.exec_id,
                    model=request.model)

                if span:
                    span.set_attribute("prfaq_length", len(prfaq_markdown))

                # Extract headline from markdown (first # line)
                headline = None
                for line in prfaq_markdown.split("\n"):
                    if line.startswith("# "):
                        headline = line[2:].strip()
                        break

                # Complete generation (update status from "generating" to "completed")
                doc_service.complete_generation(
                    experiment_id=execution.experiment_id,
                    document_type=DocumentType.RESEARCH_PRFAQ,
                    markdown_content=prfaq_markdown,
                    source_id=request.exec_id,
                    metadata={"exec_id": request.exec_id, "headline": headline})

                # Return the document using the same service instance (same session)
                doc = doc_service.get_document(
                    execution.experiment_id,
                    DocumentType.RESEARCH_PRFAQ,
                    source_id=request.exec_id)
                return doc

            except SummaryNotFoundError:
                raise
            except Exception as e:
                # Update with error status
                error_msg = str(e)[:500]  # Limit error message length
                logger.error(f"PR-FAQ generation failed for {request.exec_id}: {error_msg}")
                if execution.experiment_id:
                    doc_service.fail_generation(
                        execution.experiment_id,
                        DocumentType.RESEARCH_PRFAQ,
                        error_msg,
                        source_id=request.exec_id)
                raise

    async def generate_prfaq_background(self, request: PRFAQGenerateRequest) -> None:
        """
        Background task wrapper for PR-FAQ generation.

        This method is designed to be called as a FastAPI background task.
        It catches all exceptions and handles them internally without re-raising,
        as background tasks should not propagate exceptions to the caller.

        Args:
            request: Generation request with exec_id and model.
        """
        from loguru import logger

        try:
            self.generate_prfaq(request)
            logger.info(f"Background task: PR-FAQ generation completed for {request.exec_id}")
        except Exception as e:
            # Error already logged and status updated in generate_prfaq
            logger.error(
                f"Background task: PR-FAQ generation failed for {request.exec_id}: {e}"
            )


if __name__ == "__main__":
    import os
    import sys

    from synth_lab.infrastructure.database_v2 import init_database_v2

    # Validation with real database
    all_validation_failures = []
    total_tests = 0

    if not os.getenv("DATABASE_URL"):
        print("DATABASE_URL environment variable is required.")
        print("Set it to: postgresql://user:pass@localhost:5432/synthlab")
        sys.exit(1)

    init_database_v2()
    repo = PRFAQRepository()
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


    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
