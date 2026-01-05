"""
Test database seeding for synth-lab.

Provides test data for integration and contract tests.
Creates realistic scenarios that cover common use cases.

Usage:
    from tests.fixtures.seed_test import seed_database

    engine = create_engine(DATABASE_TEST_URL)
    seed_database(engine)
"""

from datetime import datetime, timedelta
from typing import Any

from loguru import logger
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from synth_lab.models.orm import (
    Experiment,
    SynthGroup,
    Synth,
    ResearchExecution,
    Transcript,
    Exploration,
    ScenarioNode,
    ExperimentDocument,
)


def seed_database(engine: Engine) -> None:
    """
    Seed test database with sample data.

    Creates:
    - 3 experiments with different states
    - 2 synth groups with synths
    - 2 research executions with transcripts
    - 1 exploration with scenario nodes
    - Sample documents

    Args:
        engine: SQLAlchemy engine connected to test database
    """
    logger.info("Seeding test database...")

    session = Session(engine)

    try:
        # Clear existing data (in correct order due to FK constraints)
        _clear_existing_data(session)

        # Seed in dependency order
        experiments = _seed_experiments(session)
        synth_groups = _seed_synth_groups(session)
        _seed_synths(session, synth_groups)
        _seed_research_executions(session, experiments)
        _seed_explorations(session, experiments)
        _seed_documents(session, experiments)

        session.commit()
        logger.success("Test database seeded successfully")

    except Exception as e:
        session.rollback()
        logger.error(f"Failed to seed database: {e}")
        raise
    finally:
        session.close()


def _clear_existing_data(session: Session) -> None:
    """Clear existing test data."""
    logger.debug("Clearing existing data...")

    # Delete in reverse dependency order
    session.query(Transcript).delete()
    session.query(ResearchExecution).delete()
    session.query(ScenarioNode).delete()
    session.query(Exploration).delete()
    session.query(ExperimentDocument).delete()
    session.query(Synth).delete()
    session.query(SynthGroup).delete()
    session.query(Experiment).delete()

    session.commit()


def _seed_experiments(session: Session) -> list[Experiment]:
    """Seed experiments with different states."""
    logger.debug("Seeding experiments...")

    base_time = datetime.now()

    experiments = [
        Experiment(
            id="exp_test_001",
            name="User Onboarding Improvement",
            hypothesis="Adding guided tour will reduce time-to-first-value",
            description="Test reducing friction in user onboarding flow",
            status="active",
            created_at=(base_time - timedelta(days=7)).isoformat(),
            scorecard_data={
                "feature_name": "Guided Onboarding Tour",
                "scenario": "New user first login",
                "description_text": "Interactive walkthrough of key features",
                "complexity": {"score": 0.4, "reasoning": "Medium complexity"},
                "initial_effort": {"score": 0.6, "reasoning": "Moderate effort"},
                "perceived_risk": {"score": 0.3, "reasoning": "Low risk"},
                "time_to_value": {"score": 0.8, "reasoning": "Quick value"},
            },
        ),
        Experiment(
            id="exp_test_002",
            name="Performance Optimization",
            hypothesis="Caching will reduce API response time by 50%",
            description="Test Redis caching for frequently accessed data",
            status="active",
            created_at=(base_time - timedelta(days=5)).isoformat(),
        ),
        Experiment(
            id="exp_test_003",
            name="Payment Flow Redesign",
            hypothesis="Simplified checkout will increase conversion rate",
            description="Test one-click payment vs multi-step checkout",
            status="completed",
            created_at=(base_time - timedelta(days=10)).isoformat(),
            updated_at=(base_time - timedelta(days=2)).isoformat(),
        ),
    ]

    session.add_all(experiments)
    session.commit()

    logger.debug(f"Created {len(experiments)} experiments")
    return experiments


def _seed_synth_groups(session: Session) -> list[SynthGroup]:
    """Seed synth groups."""
    logger.debug("Seeding synth groups...")

    base_time = datetime.now()

    groups = [
        SynthGroup(
            id="grp_test_001",
            name="Early Adopters",
            description="Tech-savvy users who try new features quickly",
            created_at=(base_time - timedelta(days=30)).isoformat(),
        ),
        SynthGroup(
            id="grp_test_002",
            name="Enterprise Users",
            description="Large organization users with specific needs",
            created_at=(base_time - timedelta(days=25)).isoformat(),
        ),
    ]

    session.add_all(groups)
    session.commit()

    logger.debug(f"Created {len(groups)} synth groups")
    return groups


def _seed_synths(session: Session, groups: list[SynthGroup]) -> list[Synth]:
    """Seed synths in groups."""
    logger.debug("Seeding synths...")

    synths = [
        # Early Adopters group
        Synth(
            id="syn_test_001",
            nome="Alex Chen",
            synth_group_id=groups[0].id,
            persona_data={
                "idade": 28,
                "ocupacao": "Software Developer",
                "tech_savviness": "high",
            },
            created_at=datetime.now().isoformat(),
        ),
        Synth(
            id="syn_test_002",
            nome="Sarah Kim",
            synth_group_id=groups[0].id,
            persona_data={
                "idade": 32,
                "ocupacao": "Product Manager",
                "tech_savviness": "high",
            },
            created_at=datetime.now().isoformat(),
        ),
        # Enterprise Users group
        Synth(
            id="syn_test_003",
            nome="Michael Roberts",
            synth_group_id=groups[1].id,
            persona_data={
                "idade": 45,
                "ocupacao": "IT Director",
                "company_size": "enterprise",
            },
            created_at=datetime.now().isoformat(),
        ),
    ]

    session.add_all(synths)
    session.commit()

    logger.debug(f"Created {len(synths)} synths")
    return synths


def _seed_research_executions(session: Session, experiments: list[Experiment]) -> list[ResearchExecution]:
    """Seed research executions with transcripts."""
    logger.debug("Seeding research executions...")

    base_time = datetime.now()

    executions = [
        ResearchExecution(
            exec_id="batch_exp_exp_test_001_20260104_120000",
            experiment_id=experiments[0].id,
            topic_name="onboarding_usability",
            status="completed",
            synth_count=5,
            started_at=(base_time - timedelta(hours=2)).isoformat(),
            completed_at=(base_time - timedelta(hours=1)).isoformat(),
            model="gpt-4",
            max_turns=10,
        ),
        ResearchExecution(
            exec_id="batch_exp_exp_test_002_20260104_130000",
            experiment_id=experiments[1].id,
            topic_name="performance_perception",
            status="in_progress",
            synth_count=3,
            started_at=(base_time - timedelta(minutes=30)).isoformat(),
            model="gpt-4",
            max_turns=10,
        ),
    ]

    session.add_all(executions)
    session.commit()

    # Add transcripts for completed execution
    transcripts = [
        Transcript(
            exec_id=executions[0].exec_id,
            synth_id="syn_test_001",
            messages=[
                {"role": "interviewer", "content": "How did you find the onboarding?"},
                {"role": "synth", "content": "Very intuitive and helpful"},
            ],
            metadata={"duration_seconds": 180, "quality_score": 0.85},
        ),
        Transcript(
            exec_id=executions[0].exec_id,
            synth_id="syn_test_002",
            messages=[
                {"role": "interviewer", "content": "What could be improved?"},
                {"role": "synth", "content": "More examples would help"},
            ],
            metadata={"duration_seconds": 210, "quality_score": 0.78},
        ),
    ]

    session.add_all(transcripts)
    session.commit()

    logger.debug(f"Created {len(executions)} research executions with transcripts")
    return executions


def _seed_explorations(session: Session, experiments: list[Experiment]) -> list[Exploration]:
    """Seed explorations with scenario nodes."""
    logger.debug("Seeding explorations...")

    base_time = datetime.now()

    explorations = [
        Exploration(
            id="expl_test_001",
            experiment_id=experiments[0].id,
            goal="Minimize cognitive load during onboarding",
            current_state="New users face 8-step signup requiring 12 form fields",
            status="goal_achieved",
            created_at=(base_time - timedelta(days=3)).isoformat(),
            updated_at=(base_time - timedelta(days=1)).isoformat(),
        ),
    ]

    session.add_all(explorations)
    session.commit()

    # Add scenario nodes
    nodes = [
        ScenarioNode(
            id="node_test_001",
            exploration_id=explorations[0].id,
            parent_id=None,
            depth=0,
            actions_applied=[],
            resulting_state="Baseline: 8-step signup, 12 fields",
            simulation_data={
                "complexity": 0.8,
                "initial_effort": 0.9,
                "perceived_risk": 0.4,
                "time_to_value": 0.3,
            },
            status="active",
        ),
        ScenarioNode(
            id="node_test_002",
            exploration_id=explorations[0].id,
            parent_id="node_test_001",
            depth=1,
            actions_applied=["Reduce signup to 3 required fields"],
            resulting_state="3-step signup, 3 required fields (email, password, name)",
            simulation_data={
                "complexity": 0.3,
                "initial_effort": 0.4,
                "perceived_risk": 0.3,
                "time_to_value": 0.8,
            },
            status="winner",
        ),
    ]

    session.add_all(nodes)
    session.commit()

    logger.debug(f"Created {len(explorations)} explorations with scenario nodes")
    return explorations


def _seed_documents(session: Session, experiments: list[Experiment]) -> list[ExperimentDocument]:
    """Seed experiment documents."""
    logger.debug("Seeding documents...")

    base_time = datetime.now()

    documents = [
        ExperimentDocument(
            id="doc_test_001",
            experiment_id=experiments[0].id,
            type="research_summary",
            status="completed",
            content="# Onboarding Research Summary\n\nUsers found the guided tour helpful...",
            created_at=(base_time - timedelta(hours=6)).isoformat(),
        ),
        ExperimentDocument(
            id="doc_test_002",
            experiment_id=experiments[0].id,
            type="exploration_summary",
            status="completed",
            content="# Exploration Summary\n\nReducing signup fields improved conversion...",
            created_at=(base_time - timedelta(hours=4)).isoformat(),
        ),
    ]

    session.add_all(documents)
    session.commit()

    logger.debug(f"Created {len(documents)} documents")
    return documents


if __name__ == "__main__":
    """Allow running seed directly for testing."""
    import os
    from synth_lab.infrastructure.database_v2 import create_db_engine

    db_url = os.getenv("DATABASE_TEST_URL")
    if not db_url:
        print("ERROR: DATABASE_TEST_URL not set")
        exit(1)

    engine = create_db_engine(db_url)
    seed_database(engine)
    engine.dispose()
