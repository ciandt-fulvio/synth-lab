"""
Unit tests for AnalysisRun, SynthOutcome, and AnalysisCache ORM models.

Tests validate SQLAlchemy model structure, table names, column definitions,
relationships, and basic CRUD operations.

References:
    - ORM Models: synth_lab.models.orm.analysis
    - Data Model: specs/027-postgresql-migration/data-model.md
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from synth_lab.models.orm.base import Base
from synth_lab.models.orm.experiment import Experiment
from synth_lab.models.orm.analysis import AnalysisRun, SynthOutcome, AnalysisCache


@pytest.fixture(scope="function")
def engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def session(engine):
    """Create a session for testing."""
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="function")
def sample_experiment(session: Session) -> Experiment:
    """Create a sample experiment for testing."""
    experiment = Experiment(
        id="exp_test0001",
        name="Test Experiment",
        hypothesis="Test hypothesis",
        status="active",
        created_at=datetime.now().isoformat(),
    )
    session.add(experiment)
    session.commit()
    return experiment


class TestAnalysisRunModel:
    """Tests for AnalysisRun ORM model structure."""

    def test_table_name(self):
        """AnalysisRun should map to 'analysis_runs' table."""
        assert AnalysisRun.__tablename__ == "analysis_runs"

    def test_required_columns_exist(self):
        """AnalysisRun should have all required columns."""
        columns = set(AnalysisRun.__table__.columns.keys())
        required = {"id", "experiment_id", "scenario_id", "config", "status",
                   "started_at", "completed_at", "total_synths",
                   "aggregated_outcomes", "execution_time_seconds"}
        assert required.issubset(columns)

    def test_primary_key(self):
        """AnalysisRun id should be primary key."""
        pk_columns = [c.name for c in AnalysisRun.__table__.primary_key.columns]
        assert pk_columns == ["id"]

    def test_has_foreign_key_to_experiments(self):
        """AnalysisRun should have foreign key to experiments table."""
        fks = [fk.target_fullname for fk in AnalysisRun.__table__.foreign_keys]
        assert "experiments.id" in fks

    def test_unique_experiment_id(self):
        """experiment_id should be unique (1:1 relationship)."""
        # Find the unique constraint
        for constraint in AnalysisRun.__table__.constraints:
            if hasattr(constraint, "columns"):
                col_names = [c.name for c in constraint.columns]
                if "experiment_id" in col_names and len(col_names) == 1:
                    # Found unique or primary key constraint on experiment_id
                    return
        # Check for unique attribute on column
        exp_col = AnalysisRun.__table__.columns["experiment_id"]
        assert exp_col.unique is True


class TestAnalysisRunCRUD:
    """Tests for AnalysisRun CRUD operations."""

    def test_create_analysis_run(self, session: Session, sample_experiment: Experiment):
        """Create a new analysis run."""
        analysis = AnalysisRun(
            id="ana_12345678",
            experiment_id=sample_experiment.id,
            scenario_id="baseline",
            config={"method": "scoring", "threshold": 0.5},
            status="pending",
            started_at=datetime.now().isoformat(),
        )
        session.add(analysis)
        session.commit()

        result = session.get(AnalysisRun, "ana_12345678")
        assert result is not None
        assert result.experiment_id == sample_experiment.id
        assert result.scenario_id == "baseline"
        assert result.config["method"] == "scoring"

    def test_update_analysis_status(self, session: Session, sample_experiment: Experiment):
        """Update analysis run status."""
        analysis = AnalysisRun(
            id="ana_22222222",
            experiment_id=sample_experiment.id,
            config={},
            status="pending",
            started_at=datetime.now().isoformat(),
        )
        session.add(analysis)
        session.commit()

        # Update status
        analysis.status = "completed"
        analysis.completed_at = datetime.now().isoformat()
        analysis.total_synths = 150
        analysis.execution_time_seconds = 45.5
        session.commit()

        result = session.get(AnalysisRun, "ana_22222222")
        assert result.status == "completed"
        assert result.completed_at is not None
        assert result.total_synths == 150
        assert result.execution_time_seconds == 45.5

    def test_analysis_experiment_relationship(self, session: Session, sample_experiment: Experiment):
        """Test 1:1 relationship between AnalysisRun and Experiment."""
        analysis = AnalysisRun(
            id="ana_33333333",
            experiment_id=sample_experiment.id,
            config={},
            status="pending",
            started_at=datetime.now().isoformat(),
        )
        session.add(analysis)
        session.commit()

        # Access via relationship
        analysis = session.get(AnalysisRun, "ana_33333333")
        assert analysis.experiment is not None
        assert analysis.experiment.name == "Test Experiment"

        # Access from experiment side
        experiment = session.get(Experiment, sample_experiment.id)
        assert experiment.analysis_run is not None
        assert experiment.analysis_run.id == "ana_33333333"


class TestSynthOutcomeModel:
    """Tests for SynthOutcome ORM model structure."""

    def test_table_name(self):
        """SynthOutcome should map to 'synth_outcomes' table."""
        assert SynthOutcome.__tablename__ == "synth_outcomes"

    def test_required_columns_exist(self):
        """SynthOutcome should have all required columns."""
        columns = set(SynthOutcome.__table__.columns.keys())
        required = {"id", "analysis_id", "synth_id", "did_not_try_rate",
                   "failed_rate", "success_rate", "synth_attributes"}
        assert required.issubset(columns)

    def test_has_foreign_key_to_analysis_runs(self):
        """SynthOutcome should have foreign key to analysis_runs table."""
        fks = [fk.target_fullname for fk in SynthOutcome.__table__.foreign_keys]
        assert "analysis_runs.id" in fks


class TestSynthOutcomeCRUD:
    """Tests for SynthOutcome CRUD operations."""

    def test_create_synth_outcome(self, session: Session, sample_experiment: Experiment):
        """Create synth outcome within an analysis."""
        # Create analysis first
        analysis = AnalysisRun(
            id="ana_44444444",
            experiment_id=sample_experiment.id,
            config={},
            status="running",
            started_at=datetime.now().isoformat(),
        )
        session.add(analysis)
        session.commit()

        # Create outcome
        outcome = SynthOutcome(
            id="out_11111111",
            analysis_id="ana_44444444",
            synth_id="syn001",
            did_not_try_rate=0.2,
            failed_rate=0.3,
            success_rate=0.5,
            synth_attributes={"age": 35, "income": "high"},
        )
        session.add(outcome)
        session.commit()

        result = session.get(SynthOutcome, "out_11111111")
        assert result is not None
        assert result.success_rate == 0.5
        assert result.synth_attributes["age"] == 35

    def test_outcome_analysis_relationship(self, session: Session, sample_experiment: Experiment):
        """Test N:1 relationship between SynthOutcome and AnalysisRun."""
        analysis = AnalysisRun(
            id="ana_55555555",
            experiment_id=sample_experiment.id,
            config={},
            status="completed",
            started_at=datetime.now().isoformat(),
        )
        session.add(analysis)
        session.commit()

        # Add multiple outcomes
        for i in range(3):
            outcome = SynthOutcome(
                id=f"out_2{i}",
                analysis_id="ana_55555555",
                synth_id=f"syn00{i}",
                did_not_try_rate=0.1,
                failed_rate=0.2,
                success_rate=0.7,
            )
            session.add(outcome)
        session.commit()

        # Access outcomes from analysis
        analysis = session.get(AnalysisRun, "ana_55555555")
        assert len(analysis.synth_outcomes) == 3

    def test_cascade_delete_outcomes_with_analysis(self, session: Session, sample_experiment: Experiment):
        """Outcomes should be deleted when parent analysis is deleted."""
        analysis = AnalysisRun(
            id="ana_66666666",
            experiment_id=sample_experiment.id,
            config={},
            status="completed",
            started_at=datetime.now().isoformat(),
        )
        session.add(analysis)
        session.commit()

        outcome = SynthOutcome(
            id="out_delete1",
            analysis_id="ana_66666666",
            synth_id="syn001",
            did_not_try_rate=0.0,
            failed_rate=0.0,
            success_rate=1.0,
        )
        session.add(outcome)
        session.commit()

        # Delete analysis
        session.delete(analysis)
        session.commit()

        # Outcome should be gone
        result = session.get(SynthOutcome, "out_delete1")
        assert result is None


class TestAnalysisCacheModel:
    """Tests for AnalysisCache ORM model structure."""

    def test_table_name(self):
        """AnalysisCache should map to 'analysis_cache' table."""
        assert AnalysisCache.__tablename__ == "analysis_cache"

    def test_required_columns_exist(self):
        """AnalysisCache should have all required columns."""
        columns = set(AnalysisCache.__table__.columns.keys())
        required = {"analysis_id", "cache_key", "data", "params", "computed_at"}
        assert required.issubset(columns)

    def test_composite_primary_key(self):
        """AnalysisCache should have composite primary key (analysis_id, cache_key)."""
        pk_columns = sorted([c.name for c in AnalysisCache.__table__.primary_key.columns])
        assert pk_columns == ["analysis_id", "cache_key"]


class TestAnalysisCacheCRUD:
    """Tests for AnalysisCache CRUD operations."""

    def test_create_cache_entry(self, session: Session, sample_experiment: Experiment):
        """Create cache entry for analysis."""
        analysis = AnalysisRun(
            id="ana_77777777",
            experiment_id=sample_experiment.id,
            config={},
            status="completed",
            started_at=datetime.now().isoformat(),
        )
        session.add(analysis)
        session.commit()

        cache = AnalysisCache(
            analysis_id="ana_77777777",
            cache_key="outcome_distribution",
            data={"histogram": [10, 20, 30, 25, 15]},
            params={"bins": 5},
            computed_at=datetime.now().isoformat(),
        )
        session.add(cache)
        session.commit()

        result = session.get(AnalysisCache, ("ana_77777777", "outcome_distribution"))
        assert result is not None
        assert result.data["histogram"] == [10, 20, 30, 25, 15]

    def test_multiple_cache_entries_per_analysis(self, session: Session, sample_experiment: Experiment):
        """An analysis can have multiple cache entries with different keys."""
        analysis = AnalysisRun(
            id="ana_88888888",
            experiment_id=sample_experiment.id,
            config={},
            status="completed",
            started_at=datetime.now().isoformat(),
        )
        session.add(analysis)
        session.commit()

        cache1 = AnalysisCache(
            analysis_id="ana_88888888",
            cache_key="chart_1",
            data={"type": "bar"},
            computed_at=datetime.now().isoformat(),
        )
        cache2 = AnalysisCache(
            analysis_id="ana_88888888",
            cache_key="chart_2",
            data={"type": "pie"},
            computed_at=datetime.now().isoformat(),
        )
        session.add_all([cache1, cache2])
        session.commit()

        # Access via relationship
        analysis = session.get(AnalysisRun, "ana_88888888")
        assert len(analysis.analysis_cache) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
