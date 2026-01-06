"""
Integration tests for document-related services.

Tests document storage, retrieval, and generation workflows.
Uses real database and tests Service → Repository → Database flow.

Executar: pytest -m integration tests/integration/services/test_document_services.py
"""

import pytest
from datetime import datetime

from synth_lab.services.document_service import DocumentService
from synth_lab.models.orm.experiment import Experiment
from synth_lab.models.orm.document import ExperimentDocument
from synth_lab.domain.entities.experiment_document import DocumentType, DocumentStatus
from synth_lab.repositories.experiment_document_repository import DocumentNotFoundError


@pytest.mark.integration
class TestDocumentServiceIntegration:
    """Integration tests for document_service.py - Document CRUD operations."""

    def test_save_document_persists_to_database(self, isolated_db_session):
        """Test that saving a document persists it to the database."""
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

        # Execute: Save document
        service = DocumentService()
        document = service.save_document(
            experiment_id="exp_doc_001",
            document_type=DocumentType.RESEARCH_SUMMARY,
            markdown_content="# Summary\n\nThis is a test summary document content.",
            metadata={"synth_count": 50},
        )

        # Verify
        assert document.id is not None, "Document should have ID after creation"
        assert document.experiment_id == "exp_doc_001"
        assert document.document_type == DocumentType.RESEARCH_SUMMARY
        assert "test summary" in document.markdown_content.lower()
        assert document.status == DocumentStatus.COMPLETED

        # Verify in database
        db_document = isolated_db_session.query(ExperimentDocument).filter_by(id=document.id).first()
        assert db_document is not None
        assert "test summary" in db_document.markdown_content.lower()

    def test_list_documents_returns_documents_for_experiment(self, isolated_db_session):
        """Test that list_documents returns documents for specified experiment."""
        # Setup: Create experiment with documents
        exp = Experiment(
            id="exp_docs_001", name="Exp 1", hypothesis="H1", status="active", created_at=datetime.now().isoformat()
        )
        isolated_db_session.add(exp)

        # Create documents for experiment
        for i, doc_type in enumerate(["research_summary", "research_prfaq"]):
            doc = ExperimentDocument(
                id=f"doc_exp1_{i:03d}",
                experiment_id="exp_docs_001",
                document_type=doc_type,
                markdown_content=f"# Content {i}",
                status="completed",
                generated_at=datetime.now().isoformat(),
            )
            isolated_db_session.add(doc)

        isolated_db_session.commit()

        # Execute: List documents for experiment
        service = DocumentService()
        docs = service.list_documents("exp_docs_001")

        # Verify
        assert len(docs) == 2, "Should have 2 documents for experiment"

    def test_get_document_retrieves_correct_document(self, isolated_db_session):
        """Test that get_document retrieves the right document by type."""
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
            markdown_content="# Summary content",
            status="completed",
            generated_at=datetime.now().isoformat(),
        )
        prfaq_doc = ExperimentDocument(
            id="doc_prfaq_001",
            experiment_id="exp_type_001",
            document_type="research_prfaq",
            markdown_content="# PRFAQ content",
            status="completed",
            generated_at=datetime.now().isoformat(),
        )
        isolated_db_session.add_all([summary_doc, prfaq_doc])
        isolated_db_session.commit()

        # Execute
        service = DocumentService()
        retrieved_summary = service.get_document("exp_type_001", DocumentType.RESEARCH_SUMMARY)

        # Verify
        assert retrieved_summary is not None
        assert retrieved_summary.id == "doc_summary_001"
        assert retrieved_summary.document_type == DocumentType.RESEARCH_SUMMARY
        assert "Summary content" in retrieved_summary.markdown_content

    def test_get_markdown_retrieves_content(self, isolated_db_session):
        """Test that get_markdown retrieves just the markdown content."""
        # Setup
        experiment = Experiment(
            id="exp_markdown_001",
            name="Markdown Test",
            hypothesis="Testing markdown retrieval",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        document = ExperimentDocument(
            id="doc_markdown_001",
            experiment_id="exp_markdown_001",
            document_type="research_summary",
            markdown_content="# Test Markdown\n\nOriginal content here.",
            status="completed",
            generated_at=datetime.now().isoformat(),
        )
        isolated_db_session.add_all([experiment, document])
        isolated_db_session.commit()

        # Execute: Get markdown
        service = DocumentService()
        markdown = service.get_markdown("exp_markdown_001", DocumentType.RESEARCH_SUMMARY)

        # Verify
        assert markdown == "# Test Markdown\n\nOriginal content here."

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
            markdown_content="# To be deleted",
            status="completed",
            generated_at=datetime.now().isoformat(),
        )
        isolated_db_session.add_all([experiment, document])
        isolated_db_session.commit()

        # Execute
        service = DocumentService()
        result = service.delete_document("exp_delete_doc_001", DocumentType.RESEARCH_SUMMARY)

        # Verify
        assert result is True
        db_document = isolated_db_session.query(ExperimentDocument).filter_by(id="doc_delete_001").first()
        assert db_document is None, "Document should be deleted"


@pytest.mark.integration
class TestDocumentServiceErrorHandling:
    """Integration tests for error handling in document services."""

    def test_get_document_raises_not_found(self, isolated_db_session):
        """Test that service raises appropriate error for non-existent document."""
        # Setup: Create experiment without documents
        experiment = Experiment(
            id="exp_no_docs_error",
            name="No Docs",
            hypothesis="No documents",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        isolated_db_session.add(experiment)
        isolated_db_session.commit()

        service = DocumentService()

        with pytest.raises(DocumentNotFoundError):
            service.get_document("exp_no_docs_error", DocumentType.RESEARCH_SUMMARY)

    def test_get_document_status_returns_none_when_not_found(self, isolated_db_session):
        """Test that get_document_status returns None when document doesn't exist."""
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
        result = service.get_document_status("exp_no_docs_001", DocumentType.RESEARCH_SUMMARY)

        # Verify
        assert result is None, "Should return None when document doesn't exist"

    def test_generation_workflow(self, isolated_db_session):
        """Test the document generation workflow: start -> complete."""
        # Setup: Create experiment
        experiment = Experiment(
            id="exp_gen_workflow",
            name="Generation Test",
            hypothesis="Testing generation workflow",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        isolated_db_session.add(experiment)
        isolated_db_session.commit()

        service = DocumentService()

        # Start generation
        pending = service.start_generation("exp_gen_workflow", DocumentType.RESEARCH_SUMMARY)
        assert pending is not None
        assert pending.status == DocumentStatus.GENERATING

        # Complete generation
        service.complete_generation(
            "exp_gen_workflow",
            DocumentType.RESEARCH_SUMMARY,
            markdown_content="# Generated Summary\n\nContent here.",
            metadata={"model": "gpt-4o-mini"},
        )

        # Verify completed
        doc = service.get_document("exp_gen_workflow", DocumentType.RESEARCH_SUMMARY)
        assert doc.status == DocumentStatus.COMPLETED
        assert "Generated Summary" in doc.markdown_content
