"""enriched dag node types

Adds node_metadata JSONB to causal_models, and edge_type/weight columns
to causal_edges. Makes user_var and options nullable for fixed edges.

Revision ID: a1b2c3d4e5f6
Revises: e56227c697c2
Create Date: 2026-02-21 16:30:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "e56227c697c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # causal_models: add node_metadata JSONB column
    op.add_column("causal_models", sa.Column("node_metadata", JSONB, nullable=True))

    # causal_edges: add edge_type with server default
    op.add_column(
        "causal_edges",
        sa.Column("edge_type", sa.String(20), nullable=False, server_default="likert"),
    )

    # causal_edges: add weight column
    op.add_column("causal_edges", sa.Column("weight", sa.Float, nullable=True))

    # causal_edges: make user_var nullable (product/interaction edges have no user_var)
    op.alter_column("causal_edges", "user_var", existing_type=sa.String(30), nullable=True)

    # causal_edges: make options nullable (fixed edges have no options)
    op.alter_column("causal_edges", "options", existing_type=JSONB, nullable=True)


def downgrade() -> None:
    # Reverse: make options NOT NULL again (set empty array for NULLs first)
    op.execute("UPDATE causal_edges SET options = '[]'::jsonb WHERE options IS NULL")
    op.alter_column("causal_edges", "options", existing_type=JSONB, nullable=False)

    # Reverse: make user_var NOT NULL (set empty string for NULLs first)
    op.execute("UPDATE causal_edges SET user_var = '' WHERE user_var IS NULL")
    op.alter_column("causal_edges", "user_var", existing_type=sa.String(30), nullable=False)

    # Drop new columns
    op.drop_column("causal_edges", "weight")
    op.drop_column("causal_edges", "edge_type")
    op.drop_column("causal_models", "node_metadata")
