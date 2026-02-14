"""add quantitative analysis tables

Creates tables for causal models, edges, simulation runs, and analysis
interpretations used by the quantitative analysis feature.

Revision ID: e56227c697c2
Revises: c4d5e6f7a8b9
Create Date: 2026-02-14 04:41:14.460290
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic
revision: str = "e56227c697c2"
down_revision: Union[str, None] = "c4d5e6f7a8b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create quantitative analysis tables."""
    # --- causal_models ---
    op.create_table(
        "causal_models",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column(
            "experiment_id",
            sa.String(50),
            sa.ForeignKey("experiments.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("intercept_mu", sa.Float, nullable=False),
        sa.Column("intercept_sigma", sa.Float, nullable=False),
        sa.Column("nodes", sa.JSON, nullable=False),
        sa.Column("raw_llm_response", sa.JSON, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_causal_models_experiment", "causal_models", ["experiment_id"])

    # --- causal_edges ---
    op.create_table(
        "causal_edges",
        sa.Column("id", sa.String(50), nullable=False),
        sa.Column(
            "causal_model_id",
            sa.String(50),
            sa.ForeignKey("causal_models.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("from_node", sa.String(50), nullable=False),
        sa.Column("to_node", sa.String(50), nullable=False),
        sa.Column("user_var", sa.String(30), nullable=False),
        sa.Column(
            "direction",
            sa.SmallInteger,
            nullable=False,
        ),
        sa.Column("header", sa.Text, nullable=False),
        sa.Column("options", sa.JSON, nullable=False),
        sa.Column(
            "default_option",
            sa.SmallInteger,
            nullable=False,
        ),
        sa.Column("selected_option", sa.SmallInteger, nullable=True),
        sa.PrimaryKeyConstraint("id", "causal_model_id"),
    )
    op.create_index("idx_causal_edges_model", "causal_edges", ["causal_model_id"])

    # --- simulation_runs ---
    op.create_table(
        "simulation_runs",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column(
            "experiment_id",
            sa.String(50),
            sa.ForeignKey("experiments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "causal_model_id",
            sa.String(50),
            sa.ForeignKey("causal_models.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("n_iterations", sa.Integer, nullable=False, server_default="3000"),
        sa.Column("n_synths", sa.Integer, nullable=False),
        sa.Column("selections", sa.JSON, nullable=False),
        sa.Column("stats", sa.JSON, nullable=False),
        sa.Column("distribution", sa.JSON, nullable=False),
        sa.Column("segments", sa.JSON, nullable=False),
        sa.Column("sensitivity", sa.JSON, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_simulation_runs_experiment", "simulation_runs", ["experiment_id"])
    op.create_index(
        "idx_simulation_runs_created",
        "simulation_runs",
        [sa.text("created_at DESC")],
    )

    # --- analysis_interpretations ---
    op.create_table(
        "analysis_interpretations",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column(
            "simulation_run_id",
            sa.String(50),
            sa.ForeignKey("simulation_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("section", sa.String(20), nullable=False),
        sa.Column("raw_text", sa.Text, nullable=False),
        sa.Column("ai_text", sa.Text, nullable=False),
        sa.Column("model", sa.String(50), nullable=False, server_default="gpt-4o-mini"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "simulation_run_id", "section", name="uq_interpretations_run_section"
        ),
    )
    op.create_index(
        "idx_interpretations_run", "analysis_interpretations", ["simulation_run_id"]
    )


def downgrade() -> None:
    """Drop quantitative analysis tables."""
    op.drop_table("analysis_interpretations")
    op.drop_table("simulation_runs")
    op.drop_table("causal_edges")
    op.drop_table("causal_models")
