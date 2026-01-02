"""
ExperimentDocument repository for synth-lab.

Data access layer for experiment documents (summary, prfaq, executive_summary).
Uses SQLAlchemy ORM for database operations.

References:
    - Entity: synth_lab.domain.entities.experiment_document
    - Schema: database.py (v16)
    - ORM model: synth_lab.models.orm.document
"""

import json
from datetime import datetime

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from synth_lab.domain.entities.experiment_document import (
    DocumentStatus,
    DocumentType,
    ExperimentDocument,
    ExperimentDocumentSummary,
    generate_document_id)
from synth_lab.models.orm.document import ExperimentDocument as ExperimentDocumentORM
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
    """Repository for experiment document data access.

    Uses SQLAlchemy ORM for database operations.

    Usage:
        # ORM mode
        repo = ExperimentDocumentRepository(db=database_manager)

        # ORM mode (SQLAlchemy)
        repo = ExperimentDocumentRepository(session=session)
    """

    def __init__(
        self,
session: Session | None = None):
        super().__init__( session=session)
        self.logger = logger.bind(component="experiment_document_repository")

    def get_by_id(self, document_id: str) -> ExperimentDocument | None:
        """
        Get a document by its ID.

        Args:
            document_id: Document ID (doc_XXXXXXXX format).

        Returns:
            ExperimentDocument or None if not found.
        """
        orm_doc = self._get_by_id(ExperimentDocumentORM, document_id)
        if orm_doc is None:
            return None
        return self._orm_to_document(orm_doc)
    def get_by_experiment(
        self,
        experiment_id: str,
        document_type: DocumentType) -> ExperimentDocument | None:
        """
        Get a specific document for an experiment.

        Args:
            experiment_id: Experiment ID.
            document_type: Type of document to retrieve.

        Returns:
            ExperimentDocument or None if not found.
        """
        stmt = select(ExperimentDocumentORM).where(
            ExperimentDocumentORM.experiment_id == experiment_id,
            ExperimentDocumentORM.document_type == document_type.value)
        orm_doc = self.session.execute(stmt).scalar_one_or_none()
        if orm_doc is None:
            return None
        return self._orm_to_document(orm_doc)
    def list_by_experiment(self, experiment_id: str) -> list[ExperimentDocumentSummary]:
        """
        List all documents for an experiment.

        Args:
            experiment_id: Experiment ID.

        Returns:
            List of document summaries.
        """
        stmt = (
            select(ExperimentDocumentORM)
            .where(ExperimentDocumentORM.experiment_id == experiment_id)
            .order_by(ExperimentDocumentORM.generated_at.desc())
        )
        orm_docs = list(self.session.execute(stmt).scalars().all())
        return [
            ExperimentDocumentSummary(
                id=orm_doc.id,
                document_type=DocumentType(orm_doc.document_type),
                status=DocumentStatus(orm_doc.status),
                generated_at=datetime.fromisoformat(orm_doc.generated_at)
                if isinstance(orm_doc.generated_at, str)
                else orm_doc.generated_at,
                model=orm_doc.model or "gpt-4o-mini")
            for orm_doc in orm_docs
        ]
    def get_markdown(
        self,
        experiment_id: str,
        document_type: DocumentType) -> str | None:
        """
        Get only the markdown content for a document.

        Args:
            experiment_id: Experiment ID.
            document_type: Type of document.

        Returns:
            Markdown content or None if not found.
        """
        stmt = select(ExperimentDocumentORM.markdown_content).where(
            ExperimentDocumentORM.experiment_id == experiment_id,
            ExperimentDocumentORM.document_type == document_type.value,
            ExperimentDocumentORM.status == "completed")
        result = self.session.execute(stmt).scalar_one_or_none()
        return result
    def save(self, document: ExperimentDocument) -> ExperimentDocument:
        """
        Save or update a document.

        Uses INSERT OR REPLACE based on unique(experiment_id, document_type) constraint.

        Args:
            document: Document to save.

        Returns:
            Saved document.
        """
        # Check if document exists
        stmt = select(ExperimentDocumentORM).where(
            ExperimentDocumentORM.experiment_id == document.experiment_id,
            ExperimentDocumentORM.document_type == document.document_type.value)
        existing = self.session.execute(stmt).scalar_one_or_none()

        metadata_dict = document.metadata if document.metadata else None

        if existing:
            # Update existing document
            existing.id = document.id
            existing.markdown_content = document.markdown_content
            existing.doc_metadata = metadata_dict
            existing.generated_at = document.generated_at.isoformat()
            existing.model = document.model
            existing.status = document.status.value
            existing.error_message = document.error_message
        else:
            # Create new document
            orm_doc = ExperimentDocumentORM(
                id=document.id,
                experiment_id=document.experiment_id,
                document_type=document.document_type.value,
                markdown_content=document.markdown_content,
                doc_metadata=metadata_dict,
                generated_at=document.generated_at.isoformat(),
                model=document.model,
                status=document.status.value,
                error_message=document.error_message)
            self._add(orm_doc)

        self._flush()
        self._commit()

        self.logger.info(
            f"Saved document {document.id} ({document.document_type.value}) "
            f"for experiment {document.experiment_id}"
        )

        return document
    def create_pending(
        self,
        experiment_id: str,
        document_type: DocumentType,
        model: str = "gpt-4o-mini") -> ExperimentDocument | None:
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
        stmt = select(ExperimentDocumentORM).where(
            ExperimentDocumentORM.experiment_id == experiment_id,
            ExperimentDocumentORM.document_type == document_type.value)
        existing = self.session.execute(stmt).scalar_one_or_none()

        if existing and existing.status == DocumentStatus.GENERATING.value:
            self.logger.warning(
                f"Document {document_type.value} for {experiment_id} "
                "already generating, skipping"
            )
            return None

        doc_id = existing.id if existing else generate_document_id()
        generated_at = datetime.now().isoformat()

        if existing:
            # Update existing to generating status
            previous_status = existing.status
            existing.id = doc_id
            existing.markdown_content = ""
            existing.doc_metadata = None
            existing.generated_at = generated_at
            existing.model = model
            existing.status = DocumentStatus.GENERATING.value
            existing.error_message = None
        else:
            # Create new pending document
            previous_status = "none"
            orm_doc = ExperimentDocumentORM(
                id=doc_id,
                experiment_id=experiment_id,
                document_type=document_type.value,
                markdown_content="",
                doc_metadata=None,
                generated_at=generated_at,
                model=model,
                status=DocumentStatus.GENERATING.value,
                error_message=None)
            self._add(orm_doc)

        self._flush()
        self._commit()

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
            model=model)
    def update_status(
        self,
        experiment_id: str,
        document_type: DocumentType,
        status: DocumentStatus,
        markdown_content: str | None = None,
        metadata: dict | None = None,
        error_message: str | None = None) -> None:
        """
        Update document status and optionally content.

        Args:
            experiment_id: Experiment ID.
            document_type: Type of document.
            status: New status.
            markdown_content: Content if status is completed.
            metadata: Optional metadata to update.
            error_message: Error message if status is failed.
        """
        stmt = select(ExperimentDocumentORM).where(
            ExperimentDocumentORM.experiment_id == experiment_id,
            ExperimentDocumentORM.document_type == document_type.value)
        orm_doc = self.session.execute(stmt).scalar_one_or_none()
        if orm_doc is None:
            return

        orm_doc.status = status.value

        if status == DocumentStatus.COMPLETED:
            orm_doc.generated_at = datetime.now().isoformat()

        if markdown_content is not None:
            orm_doc.markdown_content = markdown_content

        if metadata is not None:
            orm_doc.doc_metadata = metadata

        if error_message is not None:
            orm_doc.error_message = error_message

        self._flush()
        self._commit()

        content_size = len(markdown_content) if markdown_content else 0
        self.logger.info(
            f"Document {document_type.value} for {experiment_id}: "
            f"-> {status.value} (content: {content_size} chars)"
        )
        return
    def delete(self, experiment_id: str, document_type: DocumentType) -> bool:
        """
        Delete a specific document.

        Args:
            experiment_id: Experiment ID.
            document_type: Type of document to delete.

        Returns:
            True if document was deleted, False if not found.
        """
        stmt = select(ExperimentDocumentORM).where(
            ExperimentDocumentORM.experiment_id == experiment_id,
            ExperimentDocumentORM.document_type == document_type.value)
        orm_doc = self.session.execute(stmt).scalar_one_or_none()
        if orm_doc is None:
            return False

        self._delete(orm_doc)
        self._flush()
        self._commit()
        self.logger.info(
            f"Deleted document {document_type.value} for experiment {experiment_id}"
        )
        return True
    def check_documents_exist(
        self,
        experiment_id: str) -> dict[DocumentType, bool]:
        """
        Check which document types exist for an experiment.

        Args:
            experiment_id: Experiment ID.

        Returns:
            Dict mapping DocumentType to existence (True if completed).
        """
        stmt = select(ExperimentDocumentORM.document_type).where(
            ExperimentDocumentORM.experiment_id == experiment_id,
            ExperimentDocumentORM.status == "completed")
        result = self.session.execute(stmt).scalars().all()
        existing = {DocumentType(doc_type) for doc_type in result}
        return {dt: dt in existing for dt in DocumentType}
    def get_status(
        self,
        experiment_id: str,
        document_type: DocumentType) -> DocumentStatus | None:
        """
        Get the current status of a document.

        Args:
            experiment_id: Experiment ID.
            document_type: Type of document.

        Returns:
            DocumentStatus or None if document doesn't exist.
        """
        stmt = select(ExperimentDocumentORM.status).where(
            ExperimentDocumentORM.experiment_id == experiment_id,
            ExperimentDocumentORM.document_type == document_type.value)
        result = self.session.execute(stmt).scalar_one_or_none()
        if result is None:
            return None
        return DocumentStatus(result)
    def _orm_to_document(self, orm_doc: ExperimentDocumentORM) -> ExperimentDocument:
        """Convert ORM model to ExperimentDocument entity."""
        generated_at = orm_doc.generated_at
        if isinstance(generated_at, str):
            generated_at = datetime.fromisoformat(generated_at)

        return ExperimentDocument(
            id=orm_doc.id,
            experiment_id=orm_doc.experiment_id,
            document_type=DocumentType(orm_doc.document_type),
            markdown_content=orm_doc.markdown_content,
            metadata=orm_doc.doc_metadata,
            generated_at=generated_at,
            model=orm_doc.model or "gpt-4o-mini",
            status=DocumentStatus(orm_doc.status),
            error_message=orm_doc.error_message)


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

        repo = ExperimentDocumentRepository()

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
                metadata={"synth_count": 50})
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
                metadata={"headline": "Test Headline"})
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
