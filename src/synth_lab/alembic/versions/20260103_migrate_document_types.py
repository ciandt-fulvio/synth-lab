"""migrate document_type to specific enum values

Migrates generic document types (summary, prfaq) to specific types based on
their source (exploration vs research/interview).

- summary → exploration_summary (if metadata.source = 'exploration')
- summary → research_summary (otherwise)
- prfaq → exploration_prfaq (if metadata.source = 'exploration')
- prfaq → research_prfaq (otherwise)
- executive_summary → no change

Revision ID: migrate_doc_types
Revises: c65e0b6ff583
Create Date: 2026-01-03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision: str = "migrate_doc_types"
down_revision: Union[str, None] = "c65e0b6ff583"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Migrate document_type values to specific types based on source."""

    # Update exploration documents (metadata contains source='exploration')
    # Using JSON operators for PostgreSQL
    op.execute("""
        UPDATE experiment_documents
        SET document_type = 'exploration_summary'
        WHERE document_type = 'summary'
          AND metadata IS NOT NULL
          AND metadata::jsonb->>'source' = 'exploration'
    """)

    op.execute("""
        UPDATE experiment_documents
        SET document_type = 'exploration_prfaq'
        WHERE document_type = 'prfaq'
          AND metadata IS NOT NULL
          AND metadata::jsonb->>'source' = 'exploration'
    """)

    # Update remaining summary/prfaq to research types (from interviews)
    op.execute("""
        UPDATE experiment_documents
        SET document_type = 'research_summary'
        WHERE document_type = 'summary'
    """)

    op.execute("""
        UPDATE experiment_documents
        SET document_type = 'research_prfaq'
        WHERE document_type = 'prfaq'
    """)

    # executive_summary remains unchanged


def downgrade() -> None:
    """Revert document_type values to generic types."""

    # Revert exploration types
    op.execute("""
        UPDATE experiment_documents
        SET document_type = 'summary'
        WHERE document_type = 'exploration_summary'
    """)

    op.execute("""
        UPDATE experiment_documents
        SET document_type = 'prfaq'
        WHERE document_type = 'exploration_prfaq'
    """)

    # Revert research types
    op.execute("""
        UPDATE experiment_documents
        SET document_type = 'summary'
        WHERE document_type = 'research_summary'
    """)

    op.execute("""
        UPDATE experiment_documents
        SET document_type = 'prfaq'
        WHERE document_type = 'research_prfaq'
    """)
