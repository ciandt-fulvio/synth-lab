"""
Integration tests for document-related services.

Tests document storage, retrieval, and generation workflows.
Uses real database and tests Service → Repository → Database flow.

Executar: pytest -m integration tests/integration/services/test_document_services.py
"""

import pytest
from datetime import datetime

from synth_lab.services.document_service import DocumentService
from synth_lab.repositories.experiment_document_repository import (
    ExperimentDocumentRepository,
    DocumentNotFoundError,
)
from synth_lab.models.orm.experiment import Experiment
from synth_lab.models.orm.document import ExperimentDocument
from synth_lab.domain.entities.experiment_document import DocumentType, DocumentStatus


def create_document_service(session) -> DocumentService:
    """Create a DocumentService with test session."""
    repository = ExperimentDocumentRepository(session=session)
    return DocumentService(repository=repository)


@pytest.mark.integration
class TestDocumentServiceIntegration:
    """Integration tests for document_service.py - Document CRUD operations."""

    def test_save_document_persists_to_database(self, db_session):
        """Test that saving a document persists it to the database."""
        # Setup: Create parent experiment (ID must match ^exp_[a-f0-9]{8}$)
        experiment = Experiment(
            id="exp_b1c2d3e4",
            name="Document Test Experiment",
            hypothesis="Testing document creation",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        db_session.add(experiment)
        db_session.commit()

        # Execute: Save document
        service = create_document_service(db_session)
        document = service.save_document(
            experiment_id="exp_b1c2d3e4",
            document_type=DocumentType.RESEARCH_SUMMARY,
            markdown_content="# Summary\n\nThis is a test summary document content.",
            metadata={"synth_count": 50},
        )

        # Verify
        assert document.id is not None, "Document should have ID after creation"
        assert document.experiment_id == "exp_b1c2d3e4"
        assert document.document_type == DocumentType.RESEARCH_SUMMARY
        assert "test summary" in document.markdown_content.lower()
        assert document.status == DocumentStatus.COMPLETED

        # Verify in database
        db_document = db_session.query(ExperimentDocument).filter_by(id=document.id).first()
        assert db_document is not None
        assert "test summary" in db_document.markdown_content.lower()

    def test_list_documents_returns_documents_for_experiment(self, db_session):
        """Test that list_documents returns documents for specified experiment."""
        # Setup: Create experiment with documents (ID must match ^exp_[a-f0-9]{8}$)
        exp = Experiment(
            id="exp_c2d3e4f5", name="Exp 1", hypothesis="H1", status="active", created_at=datetime.now().isoformat()
        )
        db_session.add(exp)

        # Create documents for experiment (ID must match ^doc_[a-f0-9]{8}$)
        for i, doc_type in enumerate(["research_summary", "research_prfaq"]):
            doc = ExperimentDocument(
                id=f"doc_a1b2c3d{i}",
                experiment_id="exp_c2d3e4f5",
                document_type=doc_type,
                markdown_content=f"# Content {i}",
                status="completed",
                generated_at=datetime.now().isoformat(),
            )
            db_session.add(doc)

        db_session.commit()

        # Execute: List documents for experiment
        service = create_document_service(db_session)
        docs = service.list_documents("exp_c2d3e4f5")

        # Verify
        assert len(docs) == 2, "Should have 2 documents for experiment"

    def test_get_document_retrieves_correct_document(self, db_session):
        """Test that get_document retrieves the right document by type."""
        # Setup (IDs must match patterns)
        experiment = Experiment(
            id="exp_d3e4f5a6",
            name="Type Test",
            hypothesis="Testing type filtering",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        db_session.add(experiment)

        # Create documents of different types
        summary_doc = ExperimentDocument(
            id="doc_b2c3d4e5",
            experiment_id="exp_d3e4f5a6",
            document_type="research_summary",
            markdown_content="# Summary content",
            status="completed",
            generated_at=datetime.now().isoformat(),
        )
        prfaq_doc = ExperimentDocument(
            id="doc_c3d4e5f6",
            experiment_id="exp_d3e4f5a6",
            document_type="research_prfaq",
            markdown_content="# PRFAQ content",
            status="completed",
            generated_at=datetime.now().isoformat(),
        )
        db_session.add_all([summary_doc, prfaq_doc])
        db_session.commit()

        # Execute
        service = create_document_service(db_session)
        retrieved_summary = service.get_document("exp_d3e4f5a6", DocumentType.RESEARCH_SUMMARY)

        # Verify
        assert retrieved_summary is not None
        assert retrieved_summary.id == "doc_b2c3d4e5"
        assert retrieved_summary.document_type == DocumentType.RESEARCH_SUMMARY
        assert "Summary content" in retrieved_summary.markdown_content

    def test_get_markdown_retrieves_content(self, db_session):
        """Test that get_markdown retrieves just the markdown content."""
        # Setup
        experiment = Experiment(
            id="exp_e4f5a6b7",
            name="Markdown Test",
            hypothesis="Testing markdown retrieval",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        document = ExperimentDocument(
            id="doc_d4e5f6a7",
            experiment_id="exp_e4f5a6b7",
            document_type="research_summary",
            markdown_content="# Test Markdown\n\nOriginal content here.",
            status="completed",
            generated_at=datetime.now().isoformat(),
        )
        db_session.add_all([experiment, document])
        db_session.commit()

        # Execute: Get markdown
        service = create_document_service(db_session)
        markdown = service.get_markdown("exp_e4f5a6b7", DocumentType.RESEARCH_SUMMARY)

        # Verify
        assert markdown == "# Test Markdown\n\nOriginal content here."

    def test_delete_document_removes_from_database(self, db_session):
        """Test that deleting a document removes it from database."""
        # Setup
        experiment = Experiment(
            id="exp_f5a6b7c8",
            name="Delete Test",
            hypothesis="Testing deletion",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        document = ExperimentDocument(
            id="doc_e5f6a7b8",
            experiment_id="exp_f5a6b7c8",
            document_type="research_summary",
            markdown_content="# To be deleted",
            status="completed",
            generated_at=datetime.now().isoformat(),
        )
        db_session.add_all([experiment, document])
        db_session.commit()

        # Execute
        service = create_document_service(db_session)
        result = service.delete_document("exp_f5a6b7c8", DocumentType.RESEARCH_SUMMARY)

        # Verify
        assert result is True
        db_document = db_session.query(ExperimentDocument).filter_by(id="doc_e5f6a7b8").first()
        assert db_document is None, "Document should be deleted"


@pytest.mark.integration
class TestDocumentServiceErrorHandling:
    """Integration tests for error handling in document services."""

    def test_get_document_raises_not_found(self, db_session):
        """Test that service raises appropriate error for non-existent document."""
        # Setup: Create experiment without documents
        experiment = Experiment(
            id="exp_a6b7c8d9",
            name="No Docs",
            hypothesis="No documents",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        db_session.add(experiment)
        db_session.commit()

        service = create_document_service(db_session)

        with pytest.raises(DocumentNotFoundError):
            service.get_document("exp_a6b7c8d9", DocumentType.RESEARCH_SUMMARY)

    def test_get_document_status_returns_none_when_not_found(self, db_session):
        """Test that get_document_status returns None when document doesn't exist."""
        # Setup: Create experiment without documents
        experiment = Experiment(
            id="exp_b7c8d9e0",
            name="No Docs",
            hypothesis="No documents",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        db_session.add(experiment)
        db_session.commit()

        # Execute
        service = create_document_service(db_session)
        result = service.get_document_status("exp_b7c8d9e0", DocumentType.RESEARCH_SUMMARY)

        # Verify
        assert result is None, "Should return None when document doesn't exist"

    def test_generation_workflow(self, db_session):
        """Test the document generation workflow: start -> complete."""
        # Setup: Create experiment
        experiment = Experiment(
            id="exp_c8d9e0f1",
            name="Generation Test",
            hypothesis="Testing generation workflow",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        db_session.add(experiment)
        db_session.commit()

        service = create_document_service(db_session)

        # Start generation
        pending = service.start_generation("exp_c8d9e0f1", DocumentType.RESEARCH_SUMMARY)
        assert pending is not None
        assert pending.status == DocumentStatus.GENERATING

        # Complete generation
        service.complete_generation(
            "exp_c8d9e0f1",
            DocumentType.RESEARCH_SUMMARY,
            markdown_content="# Generated Summary\n\nContent here.",
            metadata={"model": "gpt-4o-mini"},
        )

        # Verify completed
        doc = service.get_document("exp_c8d9e0f1", DocumentType.RESEARCH_SUMMARY)
        assert doc.status == DocumentStatus.COMPLETED
        assert "Generated Summary" in doc.markdown_content
