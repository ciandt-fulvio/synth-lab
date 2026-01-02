"""Initial schema for synth-lab v15

This migration creates all tables for the synth-lab application.
Uses PostgreSQL as the database backend.

Revision ID: 001
Revises: None
Create Date: 2026-01-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables for synth-lab v15."""

    # synth_groups table
    op.create_table(
        "synth_groups",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(50), nullable=False),
    )
    op.create_index("idx_synth_groups_created", "synth_groups", ["created_at"])

    # synths table
    op.create_table(
        "synths",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("synth_group_id", sa.String(50), sa.ForeignKey("synth_groups.id", ondelete="SET NULL"), nullable=True),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("link_photo", sa.Text(), nullable=True),
        sa.Column("avatar_path", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(50), nullable=False),
        sa.Column("version", sa.String(20), nullable=False, server_default="2.0.0"),
        sa.Column("data", sa.JSON(), nullable=True),
    )
    op.create_index("idx_synths_created_at", "synths", ["created_at"])
    op.create_index("idx_synths_nome", "synths", ["nome"])
    op.create_index("idx_synths_group", "synths", ["synth_group_id"])

    # experiments table
    op.create_table(
        "experiments",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("hypothesis", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("scorecard_data", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.String(50), nullable=False),
        sa.Column("updated_at", sa.String(50), nullable=True),
    )
    op.create_index("idx_experiments_created", "experiments", ["created_at"])
    op.create_index("idx_experiments_name", "experiments", ["name"])
    op.create_index("idx_experiments_status", "experiments", ["status"])

    # interview_guide table
    op.create_table(
        "interview_guide",
        sa.Column("experiment_id", sa.String(50), sa.ForeignKey("experiments.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("context_definition", sa.Text(), nullable=True),
        sa.Column("questions", sa.Text(), nullable=True),
        sa.Column("context_examples", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(50), nullable=False),
        sa.Column("updated_at", sa.String(50), nullable=True),
    )

    # analysis_runs table
    op.create_table(
        "analysis_runs",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("experiment_id", sa.String(50), sa.ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("scenario_id", sa.String(50), nullable=False, server_default="baseline"),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.String(50), nullable=False),
        sa.Column("completed_at", sa.String(50), nullable=True),
        sa.Column("total_synths", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("aggregated_outcomes", sa.JSON(), nullable=True),
        sa.Column("execution_time_seconds", sa.Float(), nullable=True),
    )
    op.create_index("idx_analysis_runs_experiment", "analysis_runs", ["experiment_id"])
    op.create_index("idx_analysis_runs_status", "analysis_runs", ["status"])

    # synth_outcomes table
    op.create_table(
        "synth_outcomes",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("analysis_id", sa.String(50), sa.ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("synth_id", sa.String(50), nullable=False),
        sa.Column("did_not_try_rate", sa.Float(), nullable=False),
        sa.Column("failed_rate", sa.Float(), nullable=False),
        sa.Column("success_rate", sa.Float(), nullable=False),
        sa.Column("synth_attributes", sa.JSON(), nullable=True),
        sa.UniqueConstraint("analysis_id", "synth_id", name="uq_synth_outcomes_analysis_synth"),
    )
    op.create_index("idx_outcomes_analysis", "synth_outcomes", ["analysis_id"])

    # analysis_cache table
    op.create_table(
        "analysis_cache",
        sa.Column("analysis_id", sa.String(50), sa.ForeignKey("analysis_runs.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("cache_key", sa.String(100), primary_key=True),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("params", sa.JSON(), nullable=True),
        sa.Column("computed_at", sa.String(50), nullable=False),
    )
    op.create_index("idx_analysis_cache_analysis", "analysis_cache", ["analysis_id"])

    # research_executions table
    op.create_table(
        "research_executions",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("experiment_id", sa.String(50), sa.ForeignKey("experiments.id", ondelete="CASCADE"), nullable=True),
        sa.Column("synth_group_id", sa.String(50), sa.ForeignKey("synth_groups.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.String(50), nullable=False),
        sa.Column("completed_at", sa.String(50), nullable=True),
        sa.Column("total_synths", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_synths", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("idx_research_experiment", "research_executions", ["experiment_id"])
    op.create_index("idx_research_status", "research_executions", ["status"])

    # transcripts table
    op.create_table(
        "transcripts",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("research_id", sa.String(50), sa.ForeignKey("research_executions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("synth_id", sa.String(50), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("metadata_", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.String(50), nullable=False),
        sa.UniqueConstraint("research_id", "synth_id", name="uq_transcripts_research_synth"),
    )
    op.create_index("idx_transcripts_research", "transcripts", ["research_id"])

    # explorations table
    op.create_table(
        "explorations",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("experiment_id", sa.String(50), sa.ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("baseline_analysis_id", sa.String(50), sa.ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.String(50), nullable=False),
        sa.Column("updated_at", sa.String(50), nullable=True),
    )
    op.create_index("idx_explorations_experiment", "explorations", ["experiment_id"])

    # scenario_nodes table
    op.create_table(
        "scenario_nodes",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("exploration_id", sa.String(50), sa.ForeignKey("explorations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_id", sa.String(50), sa.ForeignKey("scenario_nodes.id", ondelete="CASCADE"), nullable=True),
        sa.Column("scenario_type", sa.String(50), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=True),
        sa.Column("results", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.String(50), nullable=False),
    )
    op.create_index("idx_scenario_nodes_exploration", "scenario_nodes", ["exploration_id"])
    op.create_index("idx_scenario_nodes_parent", "scenario_nodes", ["parent_id"])

    # chart_insights table
    op.create_table(
        "chart_insights",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("analysis_id", sa.String(50), sa.ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chart_type", sa.String(50), nullable=False),
        sa.Column("insight_text", sa.Text(), nullable=False),
        sa.Column("data_summary", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.String(50), nullable=False),
    )
    op.create_index("idx_chart_insights_analysis", "chart_insights", ["analysis_id"])

    # sensitivity_results table
    op.create_table(
        "sensitivity_results",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("analysis_id", sa.String(50), sa.ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("feature_name", sa.String(100), nullable=False),
        sa.Column("sensitivity_score", sa.Float(), nullable=False),
        sa.Column("impact_direction", sa.String(20), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.String(50), nullable=False),
    )
    op.create_index("idx_sensitivity_analysis", "sensitivity_results", ["analysis_id"])

    # region_analyses table
    op.create_table(
        "region_analyses",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("analysis_id", sa.String(50), sa.ForeignKey("analysis_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("region_name", sa.String(100), nullable=False),
        sa.Column("synth_count", sa.Integer(), nullable=False),
        sa.Column("success_rate", sa.Float(), nullable=False),
        sa.Column("characteristics", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.String(50), nullable=False),
    )
    op.create_index("idx_region_analysis", "region_analyses", ["analysis_id"])

    # experiment_documents table
    op.create_table(
        "experiment_documents",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("experiment_id", sa.String(50), sa.ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("doc_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("metadata_", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.String(50), nullable=False),
        sa.Column("updated_at", sa.String(50), nullable=True),
        sa.UniqueConstraint("experiment_id", "doc_type", name="uq_experiment_documents_type"),
    )
    op.create_index("idx_experiment_documents_experiment", "experiment_documents", ["experiment_id"])
    op.create_index("idx_experiment_documents_type", "experiment_documents", ["doc_type"])

    # feature_scorecards table (legacy)
    op.create_table(
        "feature_scorecards",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.String(50), nullable=False),
        sa.Column("updated_at", sa.String(50), nullable=True),
    )

    # simulation_runs table (legacy)
    op.create_table(
        "simulation_runs",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("scorecard_id", sa.String(50), sa.ForeignKey("feature_scorecards.id", ondelete="CASCADE"), nullable=True),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("results", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.String(50), nullable=False),
        sa.Column("completed_at", sa.String(50), nullable=True),
    )
    op.create_index("idx_simulation_scorecard", "simulation_runs", ["scorecard_id"])


def downgrade() -> None:
    """Drop all tables for synth-lab v15."""

    # Drop in reverse order (child tables first)
    op.drop_table("simulation_runs")
    op.drop_table("feature_scorecards")
    op.drop_table("experiment_documents")
    op.drop_table("region_analyses")
    op.drop_table("sensitivity_results")
    op.drop_table("chart_insights")
    op.drop_table("scenario_nodes")
    op.drop_table("explorations")
    op.drop_table("transcripts")
    op.drop_table("research_executions")
    op.drop_table("analysis_cache")
    op.drop_table("synth_outcomes")
    op.drop_table("analysis_runs")
    op.drop_table("interview_guide")
    op.drop_table("experiments")
    op.drop_table("synths")
    op.drop_table("synth_groups")
