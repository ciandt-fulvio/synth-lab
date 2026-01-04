"""
Integration tests for document-related services.

Tests document storage, retrieval, and generation workflows.
Uses real database and tests Service → Repository → Database flow.

Executar: pytest -m integration tests/integration/services/test_document_services.py
"""

import pytest
from datetime import datetime
from unittest.mock import patch, AsyncMock

from synth_lab.services.document_service import DocumentService
from synth_lab.models.orm.experiment import Experiment
from synth_lab.models.orm.document import ExperimentDocument


@pytest.mark.integration
class TestDocumentServiceIntegration:
    """Integration tests for document_service.py - Document CRUD operations."""

    def test_create_document_persists_to_database(self, isolated_db_session):
        """Test that creating a document saves it to the database."""
        # Setup: Create parent experiment
        experiment = Experiment(
            id="exp_doc_001",
            name="Document Test Experiment",
            hypothesis="Testing document creation",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        isolated_db_session.add(experiment)
        isolated_db_session.commit()

        # Execute: Create document
        service = DocumentService()
        from synth_lab.api.schemas.documents import DocumentCreate, DocumentTypeEnum

        create_data = DocumentCreate(
            experiment_id="exp_doc_001",
            document_type=DocumentTypeEnum.RESEARCH_SUMMARY,
            content="This is a test summary document content.",
        )

        document = service.create_document(create_data)

        # Verify
        assert document.id is not None, "Document should have ID after creation"
        assert document.experiment_id == "exp_doc_001"
        assert document.document_type == DocumentTypeEnum.RESEARCH_SUMMARY
        assert document.content == "This is a test summary document content."
        assert document.status == "completed", "Default status should be completed when content provided"

        # Verify in database
        db_document = isolated_db_session.query(ExperimentDocument).filter_by(id=document.id).first()
        assert db_document is not None
        assert db_document.content == document.content

    def test_list_documents_filters_by_experiment(self, isolated_db_session):
        """Test that list_documents returns only documents for specified experiment."""
        # Setup: Create two experiments with documents
        exp1 = Experiment(
            id="exp_docs_001", name="Exp 1", hypothesis="H1", status="active", created_at=datetime.now().isoformat()
        )
        exp2 = Experiment(
            id="exp_docs_002", name="Exp 2", hypothesis="H2", status="active", created_at=datetime.now().isoformat()
        )
        isolated_db_session.add_all([exp1, exp2])

        # Create documents for exp1
        for i in range(3):
            doc = ExperimentDocument(
                id=f"doc_exp1_{i:03d}",
                experiment_id="exp_docs_001",
                document_type="research_summary" if i == 0 else "prfaq",
                content=f"Content {i}",
                status="completed",
                created_at=datetime.now().isoformat(),
            )
            isolated_db_session.add(doc)

        # Create documents for exp2
        doc2 = ExperimentDocument(
            id="doc_exp2_001",
            experiment_id="exp_docs_002",
            document_type="research_summary",
            content="Exp2 content",
            status="completed",
            created_at=datetime.now().isoformat(),
        )
        isolated_db_session.add(doc2)
        isolated_db_session.commit()

        # Execute: List documents for exp1
        service = DocumentService()
        docs_exp1 = service.list_documents_by_experiment("exp_docs_001")

        # Verify
        assert len(docs_exp1) == 3, "Should have 3 documents for exp1"
        assert all(d.experiment_id == "exp_docs_001" for d in docs_exp1)

    def test_get_document_by_type_returns_correct_document(self, isolated_db_session):
        """Test that get_document_by_type retrieves the right document."""
        # Setup
        experiment = Experiment(
            id="exp_type_001",
            name="Type Test",
            hypothesis="Testing type filtering",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        isolated_db_session.add(experiment)

        # Create documents of different types
        summary_doc = ExperimentDocument(
            id="doc_summary_001",
            experiment_id="exp_type_001",
            document_type="research_summary",
            content="Summary content",
            status="completed",
            created_at=datetime.now().isoformat(),
        )
        prfaq_doc = ExperimentDocument(
            id="doc_prfaq_001",
            experiment_id="exp_type_001",
            document_type="research_prfaq",
            content="PRFAQ content",
            status="completed",
            created_at=datetime.now().isoformat(),
        )
        isolated_db_session.add_all([summary_doc, prfaq_doc])
        isolated_db_session.commit()

        # Execute
        service = DocumentService()
        from synth_lab.api.schemas.documents import DocumentTypeEnum

        retrieved_summary = service.get_document_by_type("exp_type_001", DocumentTypeEnum.RESEARCH_SUMMARY)

        # Verify
        assert retrieved_summary is not None
        assert retrieved_summary.id == "doc_summary_001"
        assert retrieved_summary.document_type == "research_summary"
        assert retrieved_summary.content == "Summary content"

    def test_update_document_content(self, isolated_db_session):
        """Test that updating document content persists to database."""
        # Setup
        experiment = Experiment(
            id="exp_update_doc_001",
            name="Update Test",
            hypothesis="Testing updates",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        document = ExperimentDocument(
            id="doc_update_001",
            experiment_id="exp_update_doc_001",
            document_type="research_summary",
            content="Original content",
            status="completed",
            created_at=datetime.now().isoformat(),
        )
        isolated_db_session.add_all([experiment, document])
        isolated_db_session.commit()

        # Execute: Update document
        service = DocumentService()
        from synth_lab.api.schemas.documents import DocumentUpdate

        update_data = DocumentUpdate(content="Updated content", status="completed")

        updated = service.update_document("doc_update_001", update_data)

        # Verify
        assert updated.content == "Updated content"

        # Verify in database
        db_document = isolated_db_session.query(ExperimentDocument).filter_by(id="doc_update_001").first()
        assert db_document.content == "Updated content"

    def test_delete_document_removes_from_database(self, isolated_db_session):
        """Test that deleting a document removes it from database."""
        # Setup
        experiment = Experiment(
            id="exp_delete_doc_001",
            name="Delete Test",
            hypothesis="Testing deletion",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        document = ExperimentDocument(
            id="doc_delete_001",
            experiment_id="exp_delete_doc_001",
            document_type="research_summary",
            content="To be deleted",
            status="completed",
            created_at=datetime.now().isoformat(),
        )
        isolated_db_session.add_all([experiment, document])
        isolated_db_session.commit()

        # Execute
        service = DocumentService()
        service.delete_document("doc_delete_001")

        # Verify
        db_document = isolated_db_session.query(ExperimentDocument).filter_by(id="doc_delete_001").first()
        assert db_document is None, "Document should be deleted"


@pytest.mark.integration
class TestDocumentServiceErrorHandling:
    """Integration tests for error handling in document services."""

    def test_get_document_raises_not_found(self, isolated_db_session):
        """Test that service raises appropriate error for non-existent document."""
        service = DocumentService()

        from synth_lab.services.errors import DocumentNotFoundError

        with pytest.raises(DocumentNotFoundError):
            service.get_document("non_existent_doc_id")

    def test_get_document_by_type_returns_none_when_not_found(self, isolated_db_session):
        """Test that get_document_by_type returns None when document doesn't exist."""
        # Setup: Create experiment without documents
        experiment = Experiment(
            id="exp_no_docs_001",
            name="No Docs",
            hypothesis="No documents",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        isolated_db_session.add(experiment)
        isolated_db_session.commit()

        # Execute
        service = DocumentService()
        from synth_lab.api.schemas.documents import DocumentTypeEnum

        result = service.get_document_by_type("exp_no_docs_001", DocumentTypeEnum.RESEARCH_SUMMARY)

        # Verify
        assert result is None, "Should return None when document doesn't exist"

    def test_create_document_for_nonexistent_experiment_raises_error(self, isolated_db_session):
        """Test that creating document for non-existent experiment raises error."""
        service = DocumentService()
        from synth_lab.api.schemas.documents import DocumentCreate, DocumentTypeEnum

        create_data = DocumentCreate(
            experiment_id="non_existent_exp", document_type=DocumentTypeEnum.RESEARCH_SUMMARY, content="Test content"
        )

        # Should raise foreign key constraint error or ExperimentNotFoundError
        with pytest.raises(Exception):  # Can be either FK constraint or custom error
            service.create_document(create_data)
