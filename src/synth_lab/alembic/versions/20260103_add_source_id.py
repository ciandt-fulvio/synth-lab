"""add source_id column to experiment_documents

Adds source_id column to support multiple documents of the same type per experiment.
Each exploration or research execution can have its own documents.

- source_id: Contains exploration_id or exec_id (research_execution_id)
- NULL for executive_summary (unique per experiment)
- New unique constraint: (experiment_id, document_type, source_id)

Revision ID: add_source_id
Revises: migrate_doc_types
Create Date: 2026-01-03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision: str = "add_source_id"
down_revision: Union[str, None] = "migrate_doc_types"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add source_id column and update constraints."""

    # 1. Add source_id column (nullable)
    op.add_column(
        "experiment_documents",
        sa.Column("source_id", sa.String(50), nullable=True)
    )

    # 2. Populate source_id from metadata for existing documents
    # For exploration documents: extract exploration_id from metadata
    op.execute("""
        UPDATE experiment_documents
        SET source_id = metadata::jsonb->>'exploration_id'
        WHERE document_type IN ('exploration_summary', 'exploration_prfaq')
          AND metadata IS NOT NULL
          AND metadata::jsonb->>'exploration_id' IS NOT NULL
    """)

    # For research documents: extract exec_id from metadata
    op.execute("""
        UPDATE experiment_documents
        SET source_id = metadata::jsonb->>'exec_id'
        WHERE document_type IN ('research_summary', 'research_prfaq')
          AND metadata IS NOT NULL
          AND metadata::jsonb->>'exec_id' IS NOT NULL
    """)

    # 3. Drop old unique constraint (experiment_id, document_type)
    op.drop_constraint(
        "uq_experiment_documents_exp_type",
        "experiment_documents",
        type_="unique"
    )

    # 4. Add new unique constraint (experiment_id, document_type, source_id)
    op.create_unique_constraint(
        "uq_experiment_documents_exp_type_source",
        "experiment_documents",
        ["experiment_id", "document_type", "source_id"]
    )

    # 5. Add index on source_id for faster lookups
    op.create_index(
        "idx_experiment_documents_source",
        "experiment_documents",
        ["source_id"]
    )


def downgrade() -> None:
    """Remove source_id column and restore old constraint."""

    # 1. Drop new index
    op.drop_index("idx_experiment_documents_source", "experiment_documents")

    # 2. Drop new unique constraint
    op.drop_constraint(
        "uq_experiment_documents_exp_type_source",
        "experiment_documents",
        type_="unique"
    )

    # 3. Restore old unique constraint
    op.create_unique_constraint(
        "uq_experiment_documents_exp_type",
        "experiment_documents",
        ["experiment_id", "document_type"]
    )

    # 4. Drop source_id column
    op.drop_column("experiment_documents", "source_id")
