"""
Document service for synth-lab.

Orchestrates document retrieval and generation for experiments.
Delegates to specialized services for each document type.

References:
    - Repository: synth_lab.repositories.experiment_document_repository
    - Entity: synth_lab.domain.entities.experiment_document
"""

from loguru import logger

from synth_lab.domain.entities.experiment_document import (
    DocumentStatus,
    DocumentType,
    ExperimentDocument,
    ExperimentDocumentSummary,
)
from synth_lab.repositories.experiment_document_repository import (
    DocumentNotFoundError,
    ExperimentDocumentRepository,
)


class DocumentService:
    """
    Service for managing experiment documents.

    Provides a unified interface for document operations across all types.
    Generation is delegated to specialized services via async background tasks.
    """

    def __init__(
        self,
        repository: ExperimentDocumentRepository | None = None,
    ):
        self.repository = repository or ExperimentDocumentRepository()
        self.logger = logger.bind(component="document_service")

    def get_document(
        self,
        experiment_id: str,
        document_type: DocumentType,
    ) -> ExperimentDocument:
        """
        Get a specific document for an experiment.

        Args:
            experiment_id: Experiment ID.
            document_type: Type of document to retrieve.

        Returns:
            ExperimentDocument.

        Raises:
            DocumentNotFoundError: If document doesn't exist.
        """
        doc = self.repository.get_by_experiment(experiment_id, document_type)
        if doc is None:
            raise DocumentNotFoundError(experiment_id, document_type)
        return doc

    def get_markdown(
        self,
        experiment_id: str,
        document_type: DocumentType,
    ) -> str:
        """
        Get markdown content for a document.

        Args:
            experiment_id: Experiment ID.
            document_type: Type of document.

        Returns:
            Markdown content string.

        Raises:
            DocumentNotFoundError: If document doesn't exist or not completed.
        """
        markdown = self.repository.get_markdown(experiment_id, document_type)
        if markdown is None:
            raise DocumentNotFoundError(experiment_id, document_type)
        return markdown

    def list_documents(
        self,
        experiment_id: str,
    ) -> list[ExperimentDocumentSummary]:
        """
        List all documents for an experiment.

        Args:
            experiment_id: Experiment ID.

        Returns:
            List of document summaries.
        """
        return self.repository.list_by_experiment(experiment_id)

    def get_document_status(
        self,
        experiment_id: str,
        document_type: DocumentType,
    ) -> DocumentStatus | None:
        """
        Get the current status of a document.

        Args:
            experiment_id: Experiment ID.
            document_type: Type of document.

        Returns:
            DocumentStatus or None if document doesn't exist.
        """
        return self.repository.get_status(experiment_id, document_type)

    def check_availability(
        self,
        experiment_id: str,
    ) -> dict[DocumentType, dict]:
        """
        Check availability of all document types for an experiment.

        Args:
            experiment_id: Experiment ID.

        Returns:
            Dict mapping DocumentType to status info:
            {
                DocumentType.SUMMARY: {
                    "available": True,
                    "status": "completed",
                    "generated_at": "2024-01-15T10:30:00"
                },
                DocumentType.PRFAQ: {
                    "available": False,
                    "status": None,
                    "generated_at": None
                },
                ...
            }
        """
        result = {}
        for doc_type in DocumentType:
            # Get full document to access both status and generated_at
            doc = self.repository.get_by_experiment(experiment_id, doc_type)
            if doc:
                result[doc_type] = {
                    "available": doc.status == DocumentStatus.COMPLETED,
                    "status": doc.status.value,
                    "generated_at": doc.generated_at.isoformat() if doc.generated_at else None,
                }
            else:
                result[doc_type] = {
                    "available": False,
                    "status": None,
                    "generated_at": None,
                }
        return result

    def save_document(
        self,
        experiment_id: str,
        document_type: DocumentType,
        markdown_content: str,
        model: str = "gpt-4o-mini",
        metadata: dict | None = None,
    ) -> ExperimentDocument:
        """
        Save a completed document.

        Args:
            experiment_id: Experiment ID.
            document_type: Type of document.
            markdown_content: Full markdown content.
            model: LLM model used.
            metadata: Optional metadata.

        Returns:
            Saved ExperimentDocument.
        """
        from synth_lab.domain.entities.experiment_document import generate_document_id

        # Check if document already exists
        existing = self.repository.get_by_experiment(experiment_id, document_type)
        doc_id = existing.id if existing else generate_document_id()

        doc = ExperimentDocument(
            id=doc_id,
            experiment_id=experiment_id,
            document_type=document_type,
            markdown_content=markdown_content,
            metadata=metadata,
            model=model,
            status=DocumentStatus.COMPLETED,
        )

        self.repository.save(doc)
        self.logger.info(
            f"Saved {document_type.value} for {experiment_id} "
            f"({len(markdown_content)} chars)"
        )
        return doc

    def start_generation(
        self,
        experiment_id: str,
        document_type: DocumentType,
        model: str = "gpt-4o-mini",
    ) -> ExperimentDocument | None:
        """
        Mark a document as generating (to prevent concurrent generation).

        Args:
            experiment_id: Experiment ID.
            document_type: Type of document.
            model: LLM model to use.

        Returns:
            Pending document, or None if already generating.
        """
        return self.repository.create_pending(experiment_id, document_type, model)

    def complete_generation(
        self,
        experiment_id: str,
        document_type: DocumentType,
        markdown_content: str,
        metadata: dict | None = None,
    ) -> None:
        """
        Mark a document generation as completed with content.

        Args:
            experiment_id: Experiment ID.
            document_type: Type of document.
            markdown_content: Generated content.
            metadata: Optional metadata.
        """
        self.repository.update_status(
            experiment_id,
            document_type,
            DocumentStatus.COMPLETED,
            markdown_content=markdown_content,
            metadata=metadata,
        )
        self.logger.info(
            f"Completed {document_type.value} for {experiment_id} "
            f"({len(markdown_content)} chars)"
        )

    def fail_generation(
        self,
        experiment_id: str,
        document_type: DocumentType,
        error_message: str,
    ) -> None:
        """
        Mark a document generation as failed.

        Args:
            experiment_id: Experiment ID.
            document_type: Type of document.
            error_message: Error details.
        """
        self.repository.update_status(
            experiment_id,
            document_type,
            DocumentStatus.FAILED,
            error_message=error_message,
        )
        self.logger.error(
            f"Failed {document_type.value} for {experiment_id}: {error_message}"
        )

    def delete_document(
        self,
        experiment_id: str,
        document_type: DocumentType,
    ) -> bool:
        """
        Delete a document.

        Args:
            experiment_id: Experiment ID.
            document_type: Type of document.

        Returns:
            True if deleted, False if not found.
        """
        return self.repository.delete(experiment_id, document_type)


if __name__ == "__main__":
    import sys
    import tempfile
    from pathlib import Path

    from synth_lab.infrastructure.database import DatabaseManager

    # Validation
    all_validation_failures = []
    total_tests = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test.db"
        db = DatabaseManager(test_db_path)

        # Create tables
        db.execute(
            """
            CREATE TABLE experiments (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                hypothesis TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TEXT NOT NULL
            )
            """
        )
        db.execute(
            """
            CREATE TABLE experiment_documents (
                id TEXT PRIMARY KEY,
                experiment_id TEXT NOT NULL,
                document_type TEXT NOT NULL,
                markdown_content TEXT NOT NULL,
                metadata TEXT,
                generated_at TEXT NOT NULL,
                model TEXT DEFAULT 'gpt-4o-mini',
                status TEXT NOT NULL DEFAULT 'completed',
                error_message TEXT,
                UNIQUE(experiment_id, document_type),
                FOREIGN KEY (experiment_id) REFERENCES experiments(id)
            )
            """
        )

        # Insert test experiment
        db.execute(
            """
            INSERT INTO experiments (id, name, hypothesis, created_at)
            VALUES ('exp_12345678', 'Test Experiment', 'Test hypothesis', datetime('now'))
            """
        )

        repo = ExperimentDocumentRepository(db)
        service = DocumentService(repository=repo)

        # Test 1: Save document
        total_tests += 1
        try:
            doc = service.save_document(
                "exp_12345678",
                DocumentType.SUMMARY,
                "# Summary\n\nTest content",
                metadata={"synth_count": 50},
            )
            if doc.status != DocumentStatus.COMPLETED:
                all_validation_failures.append(f"Expected COMPLETED: {doc.status}")
        except Exception as e:
            all_validation_failures.append(f"save_document failed: {e}")

        # Test 2: Get document
        total_tests += 1
        try:
            doc = service.get_document("exp_12345678", DocumentType.SUMMARY)
            if doc.markdown_content != "# Summary\n\nTest content":
                all_validation_failures.append(f"Content mismatch: {doc.markdown_content}")
        except Exception as e:
            all_validation_failures.append(f"get_document failed: {e}")

        # Test 3: Get markdown
        total_tests += 1
        try:
            markdown = service.get_markdown("exp_12345678", DocumentType.SUMMARY)
            if markdown != "# Summary\n\nTest content":
                all_validation_failures.append(f"Markdown mismatch: {markdown}")
        except Exception as e:
            all_validation_failures.append(f"get_markdown failed: {e}")

        # Test 4: List documents
        total_tests += 1
        try:
            docs = service.list_documents("exp_12345678")
            if len(docs) != 1:
                all_validation_failures.append(f"Expected 1 document: {len(docs)}")
        except Exception as e:
            all_validation_failures.append(f"list_documents failed: {e}")

        # Test 5: Check availability
        total_tests += 1
        try:
            avail = service.check_availability("exp_12345678")
            if not avail[DocumentType.SUMMARY]["available"]:
                all_validation_failures.append("SUMMARY should be available")
            if avail[DocumentType.PRFAQ]["available"]:
                all_validation_failures.append("PRFAQ should not be available")
        except Exception as e:
            all_validation_failures.append(f"check_availability failed: {e}")

        # Test 6: Generation workflow
        total_tests += 1
        try:
            # Start generation
            pending = service.start_generation("exp_12345678", DocumentType.PRFAQ)
            if pending is None:
                all_validation_failures.append("start_generation returned None")
            elif pending.status != DocumentStatus.GENERATING:
                all_validation_failures.append(f"Expected GENERATING: {pending.status}")

            # Complete generation
            service.complete_generation(
                "exp_12345678",
                DocumentType.PRFAQ,
                "# PR-FAQ\n\nGenerated content",
                metadata={"headline": "Test"},
            )

            # Verify
            doc = service.get_document("exp_12345678", DocumentType.PRFAQ)
            if doc.status != DocumentStatus.COMPLETED:
                all_validation_failures.append(f"Expected COMPLETED: {doc.status}")
        except Exception as e:
            all_validation_failures.append(f"Generation workflow failed: {e}")

        # Test 7: Failed generation
        total_tests += 1
        try:
            service.start_generation("exp_12345678", DocumentType.EXECUTIVE_SUMMARY)
            service.fail_generation(
                "exp_12345678",
                DocumentType.EXECUTIVE_SUMMARY,
                "Test error",
            )
            status = service.get_document_status(
                "exp_12345678", DocumentType.EXECUTIVE_SUMMARY
            )
            if status != DocumentStatus.FAILED:
                all_validation_failures.append(f"Expected FAILED: {status}")
        except Exception as e:
            all_validation_failures.append(f"Failed generation test failed: {e}")

        # Test 8: Document not found
        total_tests += 1
        try:
            service.get_document("exp_nonexistent", DocumentType.SUMMARY)
            all_validation_failures.append("Should raise DocumentNotFoundError")
        except DocumentNotFoundError:
            pass  # Expected
        except Exception as e:
            all_validation_failures.append(f"Wrong exception: {e}")

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
        print("DocumentService is validated and ready for use")
        sys.exit(0)
