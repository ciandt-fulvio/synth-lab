"""
ExperimentDocument entity for synth-lab.

Centralized storage for experiment documents: summary, prfaq, executive_summary.

References:
    - Schema: database.py (v16)
    - Plan: docs/plans/experiment-documents.md
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Types of documents that can be attached to an experiment."""

    SUMMARY = "summary"
    PRFAQ = "prfaq"
    EXECUTIVE_SUMMARY = "executive_summary"


class DocumentStatus(str, Enum):
    """Status of document generation."""

    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


def generate_document_id() -> str:
    """
    Generate a unique document ID.

    Returns:
        str: Document ID in format 'doc_XXXXXXXX' (8 hex chars).

    Example:
        >>> doc_id = generate_document_id()
        >>> doc_id.startswith('doc_')
        True
        >>> len(doc_id)
        12
    """
    return f"doc_{uuid.uuid4().hex[:8]}"


class ExperimentDocument(BaseModel):
    """
    Document attached to an experiment.

    Stores markdown content for summaries, PRFAQs, and executive summaries.
    All documents use free-form markdown format for consistency.

    Attributes:
        id: Unique document ID (doc_XXXXXXXX format).
        experiment_id: Parent experiment ID.
        document_type: Type of document (summary, prfaq, executive_summary).
        markdown_content: Full markdown content of the document.
        metadata: Optional type-specific metadata (JSON).
        generated_at: Timestamp when document was generated.
        model: LLM model used for generation.
        status: Current generation status.
        error_message: Error details if status is failed.
    """

    id: str = Field(
        pattern=r"^doc_[a-f0-9]{8}$",
        description="Document ID in format doc_XXXXXXXX",
    )
    experiment_id: str = Field(
        pattern=r"^exp_[a-f0-9]{8}$",
        description="Parent experiment ID",
    )
    document_type: DocumentType = Field(
        description="Type of document",
    )
    markdown_content: str = Field(
        description="Full markdown content of the document",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional type-specific metadata",
    )
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when document was generated",
    )
    model: str = Field(
        default="gpt-4o-mini",
        description="LLM model used for generation",
    )
    status: DocumentStatus = Field(
        default=DocumentStatus.COMPLETED,
        description="Current generation status",
    )
    error_message: str | None = Field(
        default=None,
        description="Error details if status is failed",
    )

    def to_db_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary for database storage.

        Returns:
            dict: Database-ready dictionary with serialized fields.
        """
        import json

        return {
            "id": self.id,
            "experiment_id": self.experiment_id,
            "document_type": self.document_type.value,
            "markdown_content": self.markdown_content,
            "metadata": json.dumps(self.metadata) if self.metadata else None,
            "generated_at": self.generated_at.isoformat(),
            "model": self.model,
            "status": self.status.value,
            "error_message": self.error_message,
        }

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> "ExperimentDocument":
        """
        Create from database row.

        Args:
            row: Database row as dictionary.

        Returns:
            ExperimentDocument: Parsed document entity.
        """
        import json

        metadata = None
        if row.get("metadata"):
            metadata = json.loads(row["metadata"])

        generated_at = row["generated_at"]
        if isinstance(generated_at, str):
            generated_at = datetime.fromisoformat(generated_at)

        return cls(
            id=row["id"],
            experiment_id=row["experiment_id"],
            document_type=DocumentType(row["document_type"]),
            markdown_content=row["markdown_content"],
            metadata=metadata,
            generated_at=generated_at,
            model=row.get("model", "gpt-4o-mini"),
            status=DocumentStatus(row.get("status", "completed")),
            error_message=row.get("error_message"),
        )


class ExperimentDocumentSummary(BaseModel):
    """
    Summary view of a document for listing.

    Lightweight representation without full markdown content.
    """

    id: str = Field(description="Document ID")
    document_type: DocumentType = Field(description="Type of document")
    status: DocumentStatus = Field(description="Current generation status")
    generated_at: datetime = Field(description="Timestamp when document was generated")
    model: str = Field(default="gpt-4o-mini", description="LLM model used")

    @classmethod
    def from_document(cls, doc: ExperimentDocument) -> "ExperimentDocumentSummary":
        """Create summary from full document."""
        return cls(
            id=doc.id,
            document_type=doc.document_type,
            status=doc.status,
            generated_at=doc.generated_at,
            model=doc.model,
        )


# Document type display names (for UI)
DOCUMENT_TYPE_LABELS = {
    DocumentType.SUMMARY: "Resumo da Pesquisa",
    DocumentType.PRFAQ: "PR-FAQ",
    DocumentType.EXECUTIVE_SUMMARY: "Resumo Executivo",
}


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Generate document ID
    total_tests += 1
    try:
        doc_id = generate_document_id()
        if not doc_id.startswith("doc_"):
            all_validation_failures.append(f"ID should start with 'doc_': {doc_id}")
        if len(doc_id) != 12:
            all_validation_failures.append(f"ID should be 12 chars: {len(doc_id)}")
    except Exception as e:
        all_validation_failures.append(f"Generate document ID failed: {e}")

    # Test 2: Create document
    total_tests += 1
    try:
        doc = ExperimentDocument(
            id="doc_12345678",
            experiment_id="exp_abcdef12",
            document_type=DocumentType.SUMMARY,
            markdown_content="# Summary\n\nTest content",
        )
        if doc.status != DocumentStatus.COMPLETED:
            all_validation_failures.append(f"Default status should be COMPLETED: {doc.status}")
        if doc.model != "gpt-4o-mini":
            all_validation_failures.append(f"Default model should be gpt-4o-mini: {doc.model}")
    except Exception as e:
        all_validation_failures.append(f"Create document failed: {e}")

    # Test 3: Document with metadata
    total_tests += 1
    try:
        doc = ExperimentDocument(
            id="doc_12345678",
            experiment_id="exp_abcdef12",
            document_type=DocumentType.PRFAQ,
            markdown_content="# PR-FAQ\n\nTest",
            metadata={"headline": "Test Headline", "faq_count": 5},
        )
        if doc.metadata.get("headline") != "Test Headline":
            all_validation_failures.append("Metadata not preserved correctly")
    except Exception as e:
        all_validation_failures.append(f"Document with metadata failed: {e}")

    # Test 4: to_db_dict and from_db_row roundtrip
    total_tests += 1
    try:
        original = ExperimentDocument(
            id="doc_12345678",
            experiment_id="exp_abcdef12",
            document_type=DocumentType.EXECUTIVE_SUMMARY,
            markdown_content="## Visão Geral\n\nTest",
            metadata={"included_chart_types": ["try_vs_success", "shap_summary"]},
            model="gpt-4o",
            status=DocumentStatus.COMPLETED,
        )
        db_dict = original.to_db_dict()
        restored = ExperimentDocument.from_db_row(db_dict)

        if restored.id != original.id:
            all_validation_failures.append(f"ID mismatch: {restored.id} != {original.id}")
        if restored.document_type != original.document_type:
            all_validation_failures.append("Document type mismatch")
        if restored.metadata != original.metadata:
            all_validation_failures.append("Metadata mismatch after roundtrip")
    except Exception as e:
        all_validation_failures.append(f"Roundtrip test failed: {e}")

    # Test 5: DocumentStatus enum values
    total_tests += 1
    try:
        expected_statuses = ["pending", "generating", "completed", "failed", "partial"]
        actual_statuses = [s.value for s in DocumentStatus]
        if set(actual_statuses) != set(expected_statuses):
            all_validation_failures.append(
                f"Status values mismatch: {actual_statuses} vs {expected_statuses}"
            )
    except Exception as e:
        all_validation_failures.append(f"Status enum test failed: {e}")

    # Test 6: DocumentType enum values
    total_tests += 1
    try:
        expected_types = ["summary", "prfaq", "executive_summary"]
        actual_types = [t.value for t in DocumentType]
        if set(actual_types) != set(expected_types):
            all_validation_failures.append(
                f"Type values mismatch: {actual_types} vs {expected_types}"
            )
    except Exception as e:
        all_validation_failures.append(f"Type enum test failed: {e}")

    # Test 7: ExperimentDocumentSummary
    total_tests += 1
    try:
        doc = ExperimentDocument(
            id="doc_12345678",
            experiment_id="exp_abcdef12",
            document_type=DocumentType.SUMMARY,
            markdown_content="# Summary\n\nLong content here...",
        )
        summary = ExperimentDocumentSummary.from_document(doc)
        if summary.id != doc.id:
            all_validation_failures.append("Summary ID mismatch")
        if summary.document_type != doc.document_type:
            all_validation_failures.append("Summary document_type mismatch")
    except Exception as e:
        all_validation_failures.append(f"DocumentSummary test failed: {e}")

    # Test 8: DOCUMENT_TYPE_LABELS
    total_tests += 1
    try:
        if DOCUMENT_TYPE_LABELS[DocumentType.SUMMARY] != "Resumo da Pesquisa":
            all_validation_failures.append("SUMMARY label mismatch")
        if DOCUMENT_TYPE_LABELS[DocumentType.PRFAQ] != "PR-FAQ":
            all_validation_failures.append("PRFAQ label mismatch")
        if DOCUMENT_TYPE_LABELS[DocumentType.EXECUTIVE_SUMMARY] != "Resumo Executivo":
            all_validation_failures.append("EXECUTIVE_SUMMARY label mismatch")
    except Exception as e:
        all_validation_failures.append(f"Labels test failed: {e}")

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
        print("ExperimentDocument entity is validated and ready for use")
        sys.exit(0)
