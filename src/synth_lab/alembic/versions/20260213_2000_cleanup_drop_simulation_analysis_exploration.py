"""cleanup: drop simulation, analysis, exploration, mechanism tables + scorecard_data

Removes 17 tables that are no longer used:
- Simulation aggregate: simulations, causal_dags, variables, hypotheses,
  hypothesis_versions, simulated_worlds, insights, audit_trails
- Analysis aggregate: analysis_runs, synth_outcomes, analysis_cache
- Exploration aggregate: explorations, scenario_nodes
- Mechanism config: mechanism_definitions, mechanism_options, feature_types
- Insights: chart_insights

Also removes scorecard_data JSONB column from experiments table.

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-02-13 20:00:00.000000
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic
revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, None] = "b3c4d5e6f7a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop simulation/analysis/exploration/mechanism tables and scorecard_data column."""
    # --- Exploration aggregate (children first) ---
    op.drop_table("scenario_nodes")

    # --- Analysis aggregate (children first) ---
    op.drop_table("synth_outcomes")
    op.drop_table("analysis_cache")
    op.drop_table("explorations")
    op.drop_table("analysis_runs")

    # --- Simulation aggregate (children first) ---
    op.drop_table("hypotheses")
    op.drop_table("hypothesis_versions")
    op.drop_table("simulated_worlds")
    op.drop_table("insights")
    op.drop_table("audit_trails")
    op.drop_table("variables")
    op.drop_table("causal_dags")
    op.drop_table("simulations")

    # --- Chart insights (standalone) ---
    op.drop_table("chart_insights")

    # --- Mechanism config ---
    op.drop_table("mechanism_options")
    op.drop_table("mechanism_definitions")
    op.drop_table("feature_types")

    # --- Remove scorecard_data column from experiments ---
    op.drop_column("experiments", "scorecard_data")


def downgrade() -> None:
    """Reverse migration not supported - tables contained significant schema."""
    raise NotImplementedError(
        "Downgrade not supported for this cleanup migration. "
        "Restore from backup if needed."
    )
