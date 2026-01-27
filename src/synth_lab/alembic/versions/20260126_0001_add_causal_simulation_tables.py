"""Add causal simulation tables

Revision ID: 20260126_0001
Revises: 20260123_1423_b8f290df49e8
Create Date: 2026-01-26 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260126_0001'
down_revision: Union[str, None] = 'cb21bd0e1556'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create 8 tables for causal simulation system:
    - simulations: Main simulation records
    - causal_dags: DAG structures with JSONB nodes/edges
    - variables: Individual variables in DAGs
    - hypotheses: Quantified distributions and ranges
    - hypothesis_versions: Versioned hypothesis snapshots
    - simulated_worlds: Individual world simulation results
    - insights: Generated insights with traceability
    - audit_trails: Complete reproducibility audit trails
    """

    # Table 1: simulations - Main simulation records
    op.create_table(
        'simulations',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('problem_decomposition', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('random_seed', sa.Integer(), nullable=True),
        sa.Column('n_worlds', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_simulations_created_at'), 'simulations', ['created_at'], unique=False)
    op.create_index(op.f('ix_simulations_status'), 'simulations', ['status'], unique=False)

    # Table 2: causal_dags - DAG structures
    op.create_table(
        'causal_dags',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('simulation_id', sa.String(length=255), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('nodes', postgresql.JSONB(astext_type=sa.Text()), nullable=False),  # {node_id: {type, scope, ...}}
        sa.Column('edges', postgresql.JSONB(astext_type=sa.Text()), nullable=False),  # [{source, target}]
        sa.Column('assumptions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('risks', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['simulation_id'], ['simulations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_causal_dags_simulation_id'), 'causal_dags', ['simulation_id'], unique=False)

    # Table 3: variables - Individual variables (denormalized for querying)
    op.create_table(
        'variables',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('dag_id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),  # observable, latent, friction, failure, temporal
        sa.Column('scope', sa.String(length=50), nullable=False),  # world, user
        sa.Column('controllable', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['dag_id'], ['causal_dags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_variables_dag_id'), 'variables', ['dag_id'], unique=False)

    # Table 4: hypotheses - Quantified distributions
    op.create_table(
        'hypotheses',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('simulation_id', sa.String(length=255), nullable=False),
        sa.Column('variable_id', sa.String(length=255), nullable=False),
        sa.Column('distribution_type', sa.String(length=50), nullable=False),  # normal, uniform, beta, categorical
        sa.Column('distribution_params', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('range_min', sa.Float(), nullable=True),
        sa.Column('range_max', sa.Float(), nullable=True),
        sa.Column('correlations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),  # {var_id: correlation_coef}
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['simulation_id'], ['simulations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['variable_id'], ['variables.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_hypotheses_simulation_id'), 'hypotheses', ['simulation_id'], unique=False)

    # Table 5: hypothesis_versions - Versioned hypothesis snapshots
    op.create_table(
        'hypothesis_versions',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('simulation_id', sa.String(length=255), nullable=False),
        sa.Column('version_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('dag_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('hypotheses_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['simulation_id'], ['simulations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('simulation_id', 'version_name', name='uq_simulation_version')
    )
    op.create_index(op.f('ix_hypothesis_versions_simulation_id'), 'hypothesis_versions', ['simulation_id'], unique=False)

    # Table 6: simulated_worlds - Individual world results (summary only, not all 500 worlds stored)
    op.create_table(
        'simulated_worlds',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('simulation_id', sa.String(length=255), nullable=False),
        sa.Column('world_index', sa.Integer(), nullable=False),
        sa.Column('world_params', postgresql.JSONB(astext_type=sa.Text()), nullable=False),  # World-level variable draws
        sa.Column('outcome_value', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['simulation_id'], ['simulations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_simulated_worlds_simulation_id'), 'simulated_worlds', ['simulation_id'], unique=False)

    # Table 7: insights - Generated insights with traceability
    op.create_table(
        'insights',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('simulation_id', sa.String(length=255), nullable=False),
        sa.Column('insight_type', sa.String(length=50), nullable=False),  # primary_forecast, driver_analysis, failure_mode, cluster, recommendation
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('evidence', postgresql.JSONB(astext_type=sa.Text()), nullable=False),  # Links to variables, worlds, stats
        sa.Column('recommendations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['simulation_id'], ['simulations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_insights_simulation_id'), 'insights', ['simulation_id'], unique=False)

    # Table 8: audit_trails - Complete reproducibility audit trails
    op.create_table(
        'audit_trails',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('simulation_id', sa.String(length=255), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('dag_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('hypotheses_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('random_seed', sa.Integer(), nullable=False),
        sa.Column('evidence_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('insights_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['simulation_id'], ['simulations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_trails_simulation_id'), 'audit_trails', ['simulation_id'], unique=False)


def downgrade() -> None:
    """Drop all causal simulation tables"""
    op.drop_index(op.f('ix_audit_trails_simulation_id'), table_name='audit_trails')
    op.drop_table('audit_trails')

    op.drop_index(op.f('ix_insights_simulation_id'), table_name='insights')
    op.drop_table('insights')

    op.drop_index(op.f('ix_simulated_worlds_simulation_id'), table_name='simulated_worlds')
    op.drop_table('simulated_worlds')

    op.drop_index(op.f('ix_hypothesis_versions_simulation_id'), table_name='hypothesis_versions')
    op.drop_table('hypothesis_versions')

    op.drop_index(op.f('ix_hypotheses_simulation_id'), table_name='hypotheses')
    op.drop_table('hypotheses')

    op.drop_index(op.f('ix_variables_dag_id'), table_name='variables')
    op.drop_table('variables')

    op.drop_index(op.f('ix_causal_dags_simulation_id'), table_name='causal_dags')
    op.drop_table('causal_dags')

    op.drop_index(op.f('ix_simulations_status'), table_name='simulations')
    op.drop_index(op.f('ix_simulations_created_at'), table_name='simulations')
    op.drop_table('simulations')
