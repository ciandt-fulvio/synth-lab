"""
ExperimentDocument repository for synth-lab.

Data access layer for experiment documents (summary, prfaq, executive_summary).

References:
    - Entity: synth_lab.domain.entities.experiment_document
    - Schema: database.py (v16)
"""

from datetime import datetime

from loguru import logger

from synth_lab.domain.entities.experiment_document import (
    DocumentStatus,
    DocumentType,
    ExperimentDocument,
    ExperimentDocumentSummary,
    generate_document_id,
)
from synth_lab.infrastructure.database import DatabaseManager
from synth_lab.repositories.base import BaseRepository


class DocumentNotFoundError(Exception):
    """Raised when a document is not found."""

    def __init__(self, experiment_id: str, document_type: DocumentType | None = None):
        self.experiment_id = experiment_id
        self.document_type = document_type
        if document_type:
            msg = f"Document '{document_type.value}' not found for experiment {experiment_id}"
        else:
            msg = f"No documents found for experiment {experiment_id}"
        super().__init__(msg)


class ExperimentDocumentRepository(BaseRepository):
    """Repository for experiment document data access."""

    def __init__(self, db: DatabaseManager | None = None):
        super().__init__(db)
        self.logger = logger.bind(component="experiment_document_repository")

    def get_by_id(self, document_id: str) -> ExperimentDocument | None:
        """
        Get a document by its ID.

        Args:
            document_id: Document ID (doc_XXXXXXXX format).

        Returns:
            ExperimentDocument or None if not found.
        """
        row = self.db.fetchone(
            "SELECT * FROM experiment_documents WHERE id = ?",
            (document_id,),
        )
        if row is None:
            return None
        return ExperimentDocument.from_db_row(dict(row))

    def get_by_experiment(
        self,
        experiment_id: str,
        document_type: DocumentType,
    ) -> ExperimentDocument | None:
        """
        Get a specific document for an experiment.

        Args:
            experiment_id: Experiment ID.
            document_type: Type of document to retrieve.

        Returns:
            ExperimentDocument or None if not found.
        """
        row = self.db.fetchone(
            """
            SELECT * FROM experiment_documents
            WHERE experiment_id = ? AND document_type = ?
            """,
            (experiment_id, document_type.value),
        )
        if row is None:
            return None
        return ExperimentDocument.from_db_row(dict(row))

    def list_by_experiment(self, experiment_id: str) -> list[ExperimentDocumentSummary]:
        """
        List all documents for an experiment.

        Args:
            experiment_id: Experiment ID.

        Returns:
            List of document summaries.
        """
        rows = self.db.fetchall(
            """
            SELECT id, document_type, status, generated_at, model
            FROM experiment_documents
            WHERE experiment_id = ?
            ORDER BY generated_at DESC
            """,
            (experiment_id,),
        )
        return [
            ExperimentDocumentSummary(
                id=row["id"],
                document_type=DocumentType(row["document_type"]),
                status=DocumentStatus(row["status"]),
                generated_at=datetime.fromisoformat(row["generated_at"])
                if isinstance(row["generated_at"], str)
                else row["generated_at"],
                model=row["model"] or "gpt-4o-mini",
            )
            for row in rows
        ]

    def get_markdown(
        self,
        experiment_id: str,
        document_type: DocumentType,
    ) -> str | None:
        """
        Get only the markdown content for a document.

        Args:
            experiment_id: Experiment ID.
            document_type: Type of document.

        Returns:
            Markdown content or None if not found.
        """
        row = self.db.fetchone(
            """
            SELECT markdown_content FROM experiment_documents
            WHERE experiment_id = ? AND document_type = ? AND status = 'completed'
            """,
            (experiment_id, document_type.value),
        )
        if row is None:
            return None
        return row["markdown_content"]

    def save(self, document: ExperimentDocument) -> ExperimentDocument:
        """
        Save or update a document.

        Uses INSERT OR REPLACE based on unique(experiment_id, document_type) constraint.

        Args:
            document: Document to save.

        Returns:
            Saved document.
        """
        db_dict = document.to_db_dict()

        self.db.execute(
            """
            INSERT OR REPLACE INTO experiment_documents
            (id, experiment_id, document_type, markdown_content, metadata,
             generated_at, model, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                db_dict["id"],
                db_dict["experiment_id"],
                db_dict["document_type"],
                db_dict["markdown_content"],
                db_dict["metadata"],
                db_dict["generated_at"],
                db_dict["model"],
                db_dict["status"],
                db_dict["error_message"],
            ),
        )

        self.logger.info(
            f"Saved document {document.id} ({document.document_type.value}) "
            f"for experiment {document.experiment_id}"
        )

        return document

    def create_pending(
        self,
        experiment_id: str,
        document_type: DocumentType,
        model: str = "gpt-4o-mini",
    ) -> ExperimentDocument | None:
        """
        Create a pending document record to track generation state.

        Prevents concurrent generation by checking existing status.

        Args:
            experiment_id: Experiment ID.
            document_type: Type of document to generate.
            model: LLM model to use.

        Returns:
            Created pending document, or None if already generating.
        """
        # Check if already generating
        existing = self.db.fetchone(
            """
            SELECT id, status FROM experiment_documents
            WHERE experiment_id = ? AND document_type = ?
            """,
            (experiment_id, document_type.value),
        )

        if existing and existing["status"] == DocumentStatus.GENERATING.value:
            self.logger.warning(
                f"Document {document_type.value} for {experiment_id} "
                "already generating, skipping"
            )
            return None

        # Create or update to generating status
        doc_id = existing["id"] if existing else generate_document_id()

        self.db.execute(
            """
            INSERT OR REPLACE INTO experiment_documents
            (id, experiment_id, document_type, markdown_content, metadata,
             generated_at, model, status, error_message)
            VALUES (?, ?, ?, '', NULL, ?, ?, 'generating', NULL)
            """,
            (
                doc_id,
                experiment_id,
                document_type.value,
                datetime.now().isoformat(),
                model,
            ),
        )

        previous_status = existing["status"] if existing else "none"
        self.logger.info(
            f"Document {document_type.value} for {experiment_id}: "
            f"{previous_status} -> generating"
        )

        return ExperimentDocument(
            id=doc_id,
            experiment_id=experiment_id,
            document_type=document_type,
            markdown_content="",
            status=DocumentStatus.GENERATING,
            model=model,
        )

    def update_status(
        self,
        experiment_id: str,
        document_type: DocumentType,
        status: DocumentStatus,
        markdown_content: str | None = None,
        metadata: dict | None = None,
        error_message: str | None = None,
    ) -> None:
        """
        Update document status and optionally content.

        Args:
            experiment_id: Experiment ID.
            document_type: Type of document.
            status: New status.
            markdown_content: Content if status is completed.
            metadata: Optional metadata to update.
            error_message: Error message if status is failed.

        Security Note:
            This method uses dynamic SQL generation for the SET clause,
            but it's safe because:
            1. Field names are from a controlled whitelist (not user input)
            2. All values use proper `?` parameterization
            3. Whitelist prevents future modifications from introducing vulnerabilities
        """
        import json

        # Whitelist of allowed fields for UPDATE operations
        # This prevents SQL injection if this code is modified in the future
        ALLOWED_UPDATE_FIELDS = {
            "status",
            "generated_at",
            "markdown_content",
            "metadata",
            "error_message",
        }

        # Build dynamic SET clause with parameterized values
        # All field names must be in the whitelist
        update_clauses: list[str] = []
        params: list = []

        # Helper to safely add field updates
        def add_update(field: str, value: any) -> None:
            if field not in ALLOWED_UPDATE_FIELDS:
                raise ValueError(f"Security: Invalid field name '{field}' not in whitelist")
            update_clauses.append(f"{field} = ?")
            params.append(value)

        # Always update status
        add_update("status", status.value)

        # Update generated_at when completing
        if status == DocumentStatus.COMPLETED:
            add_update("generated_at", datetime.now().isoformat())

        # Update optional fields if provided
        if markdown_content is not None:
            add_update("markdown_content", markdown_content)

        if metadata is not None:
            add_update("metadata", json.dumps(metadata))

        if error_message is not None:
            add_update("error_message", error_message)

        # Add WHERE clause parameters
        params.extend([experiment_id, document_type.value])

        # Execute parameterized query
        # Note: Field names in SET clause are validated against whitelist
        # All values use ? placeholders for proper parameterization
        query = f"""
            UPDATE experiment_documents
            SET {', '.join(update_clauses)}
            WHERE experiment_id = ? AND document_type = ?
        """
        self.db.execute(query, tuple(params))

        content_size = len(markdown_content) if markdown_content else 0
        self.logger.info(
            f"Document {document_type.value} for {experiment_id}: "
            f"-> {status.value} (content: {content_size} chars)"
        )

    def delete(self, experiment_id: str, document_type: DocumentType) -> bool:
        """
        Delete a specific document.

        Args:
            experiment_id: Experiment ID.
            document_type: Type of document to delete.

        Returns:
            True if document was deleted, False if not found.
        """
        cursor = self.db.execute(
            """
            DELETE FROM experiment_documents
            WHERE experiment_id = ? AND document_type = ?
            """,
            (experiment_id, document_type.value),
        )
        deleted = cursor.rowcount > 0
        if deleted:
            self.logger.info(
                f"Deleted document {document_type.value} for experiment {experiment_id}"
            )
        return deleted

    def check_documents_exist(
        self,
        experiment_id: str,
    ) -> dict[DocumentType, bool]:
        """
        Check which document types exist for an experiment.

        Args:
            experiment_id: Experiment ID.

        Returns:
            Dict mapping DocumentType to existence (True if completed).
        """
        rows = self.db.fetchall(
            """
            SELECT document_type FROM experiment_documents
            WHERE experiment_id = ? AND status = 'completed'
            """,
            (experiment_id,),
        )
        existing = {DocumentType(row["document_type"]) for row in rows}
        return {dt: dt in existing for dt in DocumentType}

    def get_status(
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
        row = self.db.fetchone(
            """
            SELECT status FROM experiment_documents
            WHERE experiment_id = ? AND document_type = ?
            """,
            (experiment_id, document_type.value),
        )
        if row is None:
            return None
        return DocumentStatus(row["status"])


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

        # Test 1: Create pending document
        total_tests += 1
        try:
            doc = repo.create_pending("exp_12345678", DocumentType.SUMMARY)
            if doc is None:
                all_validation_failures.append("create_pending returned None")
            elif doc.status != DocumentStatus.GENERATING:
                all_validation_failures.append(f"Expected GENERATING status: {doc.status}")
        except Exception as e:
            all_validation_failures.append(f"create_pending failed: {e}")

        # Test 2: Prevent concurrent generation
        total_tests += 1
        try:
            doc2 = repo.create_pending("exp_12345678", DocumentType.SUMMARY)
            if doc2 is not None:
                all_validation_failures.append("Should return None for concurrent generation")
        except Exception as e:
            all_validation_failures.append(f"Concurrent prevention test failed: {e}")

        # Test 3: Update status to completed
        total_tests += 1
        try:
            repo.update_status(
                "exp_12345678",
                DocumentType.SUMMARY,
                DocumentStatus.COMPLETED,
                markdown_content="# Summary\n\nTest content",
                metadata={"synth_count": 50},
            )
            status = repo.get_status("exp_12345678", DocumentType.SUMMARY)
            if status != DocumentStatus.COMPLETED:
                all_validation_failures.append(f"Expected COMPLETED: {status}")
        except Exception as e:
            all_validation_failures.append(f"update_status failed: {e}")

        # Test 4: Get document
        total_tests += 1
        try:
            doc = repo.get_by_experiment("exp_12345678", DocumentType.SUMMARY)
            if doc is None:
                all_validation_failures.append("get_by_experiment returned None")
            elif doc.markdown_content != "# Summary\n\nTest content":
                all_validation_failures.append(f"Content mismatch: {doc.markdown_content}")
        except Exception as e:
            all_validation_failures.append(f"get_by_experiment failed: {e}")

        # Test 5: Get markdown only
        total_tests += 1
        try:
            markdown = repo.get_markdown("exp_12345678", DocumentType.SUMMARY)
            if markdown != "# Summary\n\nTest content":
                all_validation_failures.append(f"get_markdown mismatch: {markdown}")
        except Exception as e:
            all_validation_failures.append(f"get_markdown failed: {e}")

        # Test 6: Save new document directly
        total_tests += 1
        try:
            new_doc = ExperimentDocument(
                id=generate_document_id(),
                experiment_id="exp_12345678",
                document_type=DocumentType.PRFAQ,
                markdown_content="# PR-FAQ\n\nTest PRFAQ",
                metadata={"headline": "Test Headline"},
            )
            saved = repo.save(new_doc)
            if saved.id != new_doc.id:
                all_validation_failures.append("save returned different ID")
        except Exception as e:
            all_validation_failures.append(f"save failed: {e}")

        # Test 7: List documents
        total_tests += 1
        try:
            docs = repo.list_by_experiment("exp_12345678")
            if len(docs) != 2:
                all_validation_failures.append(f"Expected 2 documents, got {len(docs)}")
        except Exception as e:
            all_validation_failures.append(f"list_by_experiment failed: {e}")

        # Test 8: Check documents exist
        total_tests += 1
        try:
            exists = repo.check_documents_exist("exp_12345678")
            if not exists[DocumentType.SUMMARY]:
                all_validation_failures.append("SUMMARY should exist")
            if not exists[DocumentType.PRFAQ]:
                all_validation_failures.append("PRFAQ should exist")
            if exists[DocumentType.EXECUTIVE_SUMMARY]:
                all_validation_failures.append("EXECUTIVE_SUMMARY should not exist")
        except Exception as e:
            all_validation_failures.append(f"check_documents_exist failed: {e}")

        # Test 9: Delete document
        total_tests += 1
        try:
            deleted = repo.delete("exp_12345678", DocumentType.PRFAQ)
            if not deleted:
                all_validation_failures.append("delete should return True")
            docs = repo.list_by_experiment("exp_12345678")
            if len(docs) != 1:
                all_validation_failures.append(f"Expected 1 document after delete, got {len(docs)}")
        except Exception as e:
            all_validation_failures.append(f"delete failed: {e}")

        # Test 10: Get non-existent document
        total_tests += 1
        try:
            doc = repo.get_by_experiment("exp_12345678", DocumentType.EXECUTIVE_SUMMARY)
            if doc is not None:
                all_validation_failures.append("Should return None for non-existent document")
        except Exception as e:
            all_validation_failures.append(f"Non-existent document test failed: {e}")

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
        print("ExperimentDocumentRepository is validated and ready for use")
        sys.exit(0)
