"""
SQLite database connection manager for synth-lab.

Provides connection management with WAL mode, foreign keys, and connection pooling.
Uses context manager pattern for safe connection handling.

References:
    - SQLite WAL mode: https://www.sqlite.org/wal.html
    - Python sqlite3: https://docs.python.org/3/library/sqlite3.html
"""

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from loguru import logger

from synth_lab.infrastructure.config import DB_PATH

# Database schema SQL - Version 12 (2025-12)
# Changes:
#   - v4: synths.data: single JSON field for all nested data
#   - v5: Added simulation tables (feature_scorecards, simulation_runs, synth_outcomes,
#         region_analyses, assumption_log)
#   - v6: Added experiments table, synth_groups table, added experiment_id to
#         feature_scorecards and research_executions, added synth_group_id to synths
#   - v7: Refactored experiment model - scorecard embedded in experiments,
#         analysis_runs replaces simulation_runs with 1:1 relationship to experiment,
#         synth_outcomes now references analysis_runs
#   - v8: Removed topic_guides_cache, added interview_guide table (1:1 with experiment)
#   - v9: Added sensitivity_results and chart_insights tables
#   - v10: Added status field to experiments table for soft delete
#   - v11: Added scenario_id field to analysis_runs table
#   - v12: Added analysis_cache table for pre-computed chart data
SCHEMA_SQL = """
-- Enable recommended settings
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
PRAGMA synchronous=NORMAL;

-- Experiments table (MODIFIED in v10 - added status for soft delete)
CREATE TABLE IF NOT EXISTS experiments (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL CHECK(length(name) <= 100),
    hypothesis TEXT NOT NULL CHECK(length(hypothesis) <= 500),
    description TEXT CHECK(length(description) <= 2000),
    scorecard_data TEXT CHECK(json_valid(scorecard_data) OR scorecard_data IS NULL),
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT,
    CHECK(status IN ('active', 'deleted'))
);

CREATE INDEX IF NOT EXISTS idx_experiments_created ON experiments(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_experiments_name ON experiments(name);
-- idx_experiments_status is created by migration v10

-- Analysis Runs table (MODIFIED in v11 - added scenario_id)
CREATE TABLE IF NOT EXISTS analysis_runs (
    id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL UNIQUE,
    scenario_id TEXT NOT NULL DEFAULT 'baseline',
    config TEXT NOT NULL CHECK(json_valid(config)),
    status TEXT NOT NULL DEFAULT 'pending',
    started_at TEXT NOT NULL,
    completed_at TEXT,
    total_synths INTEGER DEFAULT 0,
    aggregated_outcomes TEXT CHECK(json_valid(aggregated_outcomes) OR aggregated_outcomes IS NULL),
    execution_time_seconds REAL,
    CHECK(status IN ('pending', 'running', 'completed', 'failed')),
    FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_analysis_runs_experiment ON analysis_runs(experiment_id);
CREATE INDEX IF NOT EXISTS idx_analysis_runs_status ON analysis_runs(status);

-- Synth Outcomes (MODIFIED in v7 - references analysis_runs instead of simulation_runs)
CREATE TABLE IF NOT EXISTS synth_outcomes (
    id TEXT PRIMARY KEY,
    analysis_id TEXT NOT NULL,
    synth_id TEXT NOT NULL,
    did_not_try_rate REAL NOT NULL,
    failed_rate REAL NOT NULL,
    success_rate REAL NOT NULL,
    synth_attributes TEXT CHECK(json_valid(synth_attributes)),
    UNIQUE(analysis_id, synth_id),
    FOREIGN KEY (analysis_id) REFERENCES analysis_runs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_outcomes_analysis ON synth_outcomes(analysis_id);

-- Synth Groups table
CREATE TABLE IF NOT EXISTS synth_groups (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_synth_groups_created ON synth_groups(created_at DESC);

-- Synths table
CREATE TABLE IF NOT EXISTS synths (
    id TEXT PRIMARY KEY,
    synth_group_id TEXT,
    nome TEXT NOT NULL,
    descricao TEXT,
    link_photo TEXT,
    avatar_path TEXT,
    created_at TEXT NOT NULL,
    version TEXT DEFAULT '2.0.0',
    data TEXT CHECK(json_valid(data) OR data IS NULL),
    FOREIGN KEY (synth_group_id) REFERENCES synth_groups(id)
);

CREATE INDEX IF NOT EXISTS idx_synths_created_at ON synths(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_synths_nome ON synths(nome);
CREATE INDEX IF NOT EXISTS idx_synths_group ON synths(synth_group_id);

-- Research executions table (interviews, N:1 with experiment)
CREATE TABLE IF NOT EXISTS research_executions (
    exec_id TEXT PRIMARY KEY,
    experiment_id TEXT,
    topic_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    synth_count INTEGER NOT NULL DEFAULT 0,
    successful_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    model TEXT DEFAULT 'gpt-4o-mini',
    max_turns INTEGER DEFAULT 6,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    summary_content TEXT,
    additional_context TEXT,
    CHECK(status IN ('pending', 'running', 'generating_summary', 'completed', 'failed')),
    FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_executions_topic ON research_executions(topic_name);
CREATE INDEX IF NOT EXISTS idx_executions_status ON research_executions(status);
CREATE INDEX IF NOT EXISTS idx_executions_started ON research_executions(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_executions_experiment ON research_executions(experiment_id);

-- Transcripts table
CREATE TABLE IF NOT EXISTS transcripts (
    id TEXT PRIMARY KEY,
    exec_id TEXT NOT NULL,
    synth_id TEXT NOT NULL,
    synth_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    turn_count INTEGER DEFAULT 0,
    timestamp TEXT NOT NULL,
    messages TEXT CHECK(json_valid(messages)),
    UNIQUE(exec_id, synth_id),
    FOREIGN KEY (exec_id) REFERENCES research_executions(exec_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_transcripts_exec ON transcripts(exec_id);
CREATE INDEX IF NOT EXISTS idx_transcripts_synth ON transcripts(synth_id);

-- PR-FAQ metadata table
CREATE TABLE IF NOT EXISTS prfaq_metadata (
    exec_id TEXT PRIMARY KEY,
    generated_at TEXT,
    model TEXT DEFAULT 'gpt-4o-mini',
    validation_status TEXT DEFAULT 'valid',
    confidence_score REAL,
    headline TEXT,
    one_liner TEXT,
    faq_count INTEGER DEFAULT 0,
    markdown_content TEXT,
    json_content TEXT CHECK(json_valid(json_content) OR json_content IS NULL),
    status TEXT DEFAULT 'completed',
    error_message TEXT,
    started_at TEXT,
    CHECK(validation_status IN ('valid', 'invalid', 'pending')),
    CHECK(status IN ('generating', 'completed', 'failed'))
);

CREATE INDEX IF NOT EXISTS idx_prfaq_generated ON prfaq_metadata(generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_prfaq_status ON prfaq_metadata(status);

-- Interview Guide table (1:1 with experiment)
CREATE TABLE IF NOT EXISTS interview_guide (
    experiment_id TEXT PRIMARY KEY,
    context_definition TEXT,
    questions TEXT,
    context_examples TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
);

-- Legacy tables (kept for backward compatibility, will be removed in future)
-- Feature Scorecards (legacy - scorecard now embedded in experiments)
CREATE TABLE IF NOT EXISTS feature_scorecards (
    id TEXT PRIMARY KEY,
    experiment_id TEXT,
    data TEXT NOT NULL CHECK(json_valid(data)),
    created_at TEXT NOT NULL,
    updated_at TEXT,
    FOREIGN KEY (experiment_id) REFERENCES experiments(id)
);

CREATE INDEX IF NOT EXISTS idx_scorecards_created ON feature_scorecards(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scorecards_experiment ON feature_scorecards(experiment_id);

-- Simulation Runs (legacy - replaced by analysis_runs)
CREATE TABLE IF NOT EXISTS simulation_runs (
    id TEXT PRIMARY KEY,
    scorecard_id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    config TEXT NOT NULL CHECK(json_valid(config)),
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    total_synths INTEGER DEFAULT 0,
    aggregated_outcomes TEXT CHECK(json_valid(aggregated_outcomes) OR aggregated_outcomes IS NULL),
    execution_time_seconds REAL,
    CHECK(status IN ('pending', 'running', 'completed', 'failed')),
    FOREIGN KEY (scorecard_id) REFERENCES feature_scorecards(id)
);

CREATE INDEX IF NOT EXISTS idx_simulations_scorecard ON simulation_runs(scorecard_id);
CREATE INDEX IF NOT EXISTS idx_simulations_status ON simulation_runs(status);

-- Region Analyses (simulation analysis results)
CREATE TABLE IF NOT EXISTS region_analyses (
    id TEXT PRIMARY KEY,
    simulation_id TEXT NOT NULL,
    rules TEXT NOT NULL CHECK(json_valid(rules)),
    rule_text TEXT NOT NULL,
    synth_count INTEGER NOT NULL,
    synth_percentage REAL NOT NULL,
    did_not_try_rate REAL NOT NULL,
    failed_rate REAL NOT NULL,
    success_rate REAL NOT NULL,
    failure_delta REAL NOT NULL,
    FOREIGN KEY (simulation_id) REFERENCES simulation_runs(id)
);

CREATE INDEX IF NOT EXISTS idx_regions_simulation ON region_analyses(simulation_id);

-- Sensitivity Results table (OAT sensitivity analysis)
CREATE TABLE IF NOT EXISTS sensitivity_results (
    id TEXT PRIMARY KEY,
    simulation_id TEXT NOT NULL,
    analyzed_at TEXT NOT NULL,
    deltas_used TEXT NOT NULL CHECK(json_valid(deltas_used)),
    baseline_success REAL NOT NULL,
    most_sensitive_dimension TEXT NOT NULL,
    dimensions TEXT NOT NULL CHECK(json_valid(dimensions)),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (simulation_id) REFERENCES simulation_runs(id)
);

CREATE INDEX IF NOT EXISTS idx_sensitivity_simulation ON sensitivity_results(simulation_id);
CREATE INDEX IF NOT EXISTS idx_sensitivity_analyzed_at ON sensitivity_results(analyzed_at);

-- Chart Insights table (LLM-generated insights for charts)
CREATE TABLE IF NOT EXISTS chart_insights (
    id TEXT PRIMARY KEY,
    simulation_id TEXT NOT NULL,
    insight_type TEXT NOT NULL,
    response_json TEXT NOT NULL CHECK(json_valid(response_json)),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(simulation_id, insight_type)
);

CREATE INDEX IF NOT EXISTS idx_chart_insights_simulation ON chart_insights(simulation_id);
CREATE INDEX IF NOT EXISTS idx_chart_insights_type ON chart_insights(insight_type);

-- Analysis Cache table (pre-computed chart data, v12)
CREATE TABLE IF NOT EXISTS analysis_cache (
    analysis_id TEXT NOT NULL,
    cache_key TEXT NOT NULL,
    data TEXT NOT NULL CHECK(json_valid(data)),
    params TEXT CHECK(json_valid(params) OR params IS NULL),
    computed_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (analysis_id, cache_key),
    FOREIGN KEY (analysis_id) REFERENCES analysis_runs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_analysis_cache_analysis ON analysis_cache(analysis_id);
"""


def init_database(db_path: Path | None = None) -> None:
    """
    Initialize database with schema.

    Args:
        db_path: Path to database file. Defaults to config.DB_PATH.
    """
    from synth_lab.domain.entities.synth_group import (
        DEFAULT_SYNTH_GROUP_DESCRIPTION,
        DEFAULT_SYNTH_GROUP_ID,
        DEFAULT_SYNTH_GROUP_NAME,
    )

    target_path = db_path or DB_PATH

    logger.info(f"Initializing database at {target_path}")

    # Ensure parent directory exists
    target_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(target_path)
    try:
        conn.executescript(SCHEMA_SQL)
        logger.info("Database schema created successfully")

        # Migration v10: Add status column to experiments if not exists
        cursor = conn.execute("PRAGMA table_info(experiments)")
        columns = [row[1] for row in cursor.fetchall()]
        if "status" not in columns:
            logger.info("Migrating experiments table: adding status column")
            conn.execute(
                "ALTER TABLE experiments ADD COLUMN status TEXT NOT NULL DEFAULT 'active'"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments(status)"
            )
            conn.commit()
            logger.info("Migration v10 completed: status column added")

        # Migration v11: Add scenario_id column to analysis_runs if not exists
        cursor = conn.execute("PRAGMA table_info(analysis_runs)")
        columns = [row[1] for row in cursor.fetchall()]
        if "scenario_id" not in columns:
            logger.info("Migrating analysis_runs table: adding scenario_id column")
            conn.execute(
                "ALTER TABLE analysis_runs ADD COLUMN scenario_id TEXT NOT NULL DEFAULT 'baseline'"
            )
            conn.commit()
            logger.info("Migration v11 completed: scenario_id column added")

        # Ensure default synth group exists (ID=1, always present)
        conn.execute(
            """
            INSERT OR IGNORE INTO synth_groups (id, name, description, created_at)
            VALUES (?, ?, ?, datetime('now'))
            """,
            (DEFAULT_SYNTH_GROUP_ID, DEFAULT_SYNTH_GROUP_NAME, DEFAULT_SYNTH_GROUP_DESCRIPTION),
        )
        conn.commit()
        logger.info(f"Default synth group ensured: {DEFAULT_SYNTH_GROUP_ID}")
    finally:
        conn.close()


class DatabaseManager:
    """Thread-safe SQLite connection manager with connection pooling."""

    def __init__(self, db_path: Path | str | None = None):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file. Defaults to config.DB_PATH.
        """
        self.db_path = Path(db_path) if db_path else DB_PATH
        self._local = threading.local()
        self._lock = threading.Lock()
        self.logger = logger.bind(component="database")

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create a thread-local connection."""
        # Check if we have a cached connection
        if hasattr(self._local, "connection") and self._local.connection is not None:
            # Verify connection is still valid
            try:
                self._local.connection.execute("SELECT 1")
                # Execute a passive WAL checkpoint to see latest data
                # This ensures we see changes made by other processes/connections
                self._local.connection.execute("PRAGMA wal_checkpoint(PASSIVE)")
                return self._local.connection
            except (sqlite3.ProgrammingError, sqlite3.OperationalError):
                # Connection is invalid, close and recreate
                self.logger.debug("Connection invalid, recreating")
                try:
                    self._local.connection.close()
                except Exception:
                    pass
                self._local.connection = None

        # Create new connection
        self.logger.debug(f"Creating new connection to {self.db_path}")
        self._local.connection = self._create_connection()
        return self._local.connection

    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection with optimal settings."""
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,  # Thread-local connections handle this
            isolation_level=None,  # Autocommit mode; we manage transactions explicitly
        )

        # Enable WAL mode for concurrent reads
        conn.execute("PRAGMA journal_mode=WAL")
        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys=ON")
        # Balance safety and performance
        conn.execute("PRAGMA synchronous=NORMAL")
        # Use memory for temp tables
        conn.execute("PRAGMA temp_store=MEMORY")

        # Return rows as dict-like objects
        conn.row_factory = sqlite3.Row

        return conn

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Get a database connection as a context manager.

        Usage:
            with db.connection() as conn:
                cursor = conn.execute("SELECT * FROM synths")
                rows = cursor.fetchall()

        Yields:
            sqlite3.Connection: Database connection.
        """
        conn = self._get_connection()
        try:
            yield conn
        except Exception:
            self.logger.exception("Database operation failed")
            raise

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Execute operations within a transaction.

        Usage:
            with db.transaction() as conn:
                conn.execute("INSERT INTO synths ...")
                conn.execute("UPDATE synths ...")
            # Auto-commits on success, rolls back on exception

        Yields:
            sqlite3.Connection: Database connection.
        """
        conn = self._get_connection()
        try:
            conn.execute("BEGIN")
            yield conn
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            self.logger.exception("Transaction failed, rolled back")
            raise

    def execute(
        self, sql: str, params: tuple | dict | None = None
    ) -> sqlite3.Cursor:
        """
        Execute a single SQL statement.

        Args:
            sql: SQL statement to execute.
            params: Parameters for the SQL statement.

        Returns:
            sqlite3.Cursor: Cursor with results.
        """
        with self.connection() as conn:
            if params:
                return conn.execute(sql, params)
            return conn.execute(sql)

    def executemany(
        self, sql: str, params_list: list[tuple | dict]
    ) -> sqlite3.Cursor:
        """
        Execute a SQL statement for multiple parameter sets.

        Args:
            sql: SQL statement to execute.
            params_list: List of parameter tuples/dicts.

        Returns:
            sqlite3.Cursor: Cursor with results.
        """
        with self.connection() as conn:
            return conn.executemany(sql, params_list)

    def fetchone(
        self, sql: str, params: tuple | dict | None = None
    ) -> sqlite3.Row | None:
        """
        Execute SQL and fetch one row.

        Args:
            sql: SQL statement to execute.
            params: Parameters for the SQL statement.

        Returns:
            sqlite3.Row | None: First row or None.
        """
        cursor = self.execute(sql, params)
        return cursor.fetchone()

    def fetchall(
        self, sql: str, params: tuple | dict | None = None
    ) -> list[sqlite3.Row]:
        """
        Execute SQL and fetch all rows.

        Args:
            sql: SQL statement to execute.
            params: Parameters for the SQL statement.

        Returns:
            list[sqlite3.Row]: All rows.
        """
        cursor = self.execute(sql, params)
        return cursor.fetchall()

    def close(self) -> None:
        """Close the thread-local connection if it exists."""
        if hasattr(self._local, "connection") and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
            self.logger.debug("Connection closed")

    def refresh_connection(self) -> None:
        """Force refresh of the thread-local connection.

        This closes the current connection and forces a new one to be created
        on the next request. Useful when the database has been modified externally.
        """
        self.close()
        self.logger.debug("Connection refresh requested")


# Global database manager instance
_db: DatabaseManager | None = None


def get_database(db_path: Path | str | None = None) -> DatabaseManager:
    """
    Get or create the global database manager.

    Args:
        db_path: Optional path override. Only used on first call.

    Returns:
        DatabaseManager: Global database manager instance.
    """
    global _db
    if _db is None:
        _db = DatabaseManager(db_path)
    return _db


if __name__ == "__main__":
    import sys
    import tempfile

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Use a temporary database for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test.db"
        db = DatabaseManager(test_db_path)

        # Test 1: Connection creation
        total_tests += 1
        try:
            with db.connection() as conn:
                result = conn.execute("SELECT 1 as test").fetchone()
                if result["test"] != 1:
                    all_validation_failures.append(f"SELECT 1 returned {result['test']}, expected 1")
        except Exception as e:
            all_validation_failures.append(f"Connection creation failed: {e}")

        # Test 2: WAL mode enabled
        total_tests += 1
        try:
            result = db.fetchone("PRAGMA journal_mode")
            if result[0] != "wal":
                all_validation_failures.append(f"WAL mode not enabled: {result[0]}")
        except Exception as e:
            all_validation_failures.append(f"WAL mode check failed: {e}")

        # Test 3: Foreign keys enabled
        total_tests += 1
        try:
            result = db.fetchone("PRAGMA foreign_keys")
            if result[0] != 1:
                all_validation_failures.append(f"Foreign keys not enabled: {result[0]}")
        except Exception as e:
            all_validation_failures.append(f"Foreign keys check failed: {e}")

        # Test 4: Transaction rollback
        total_tests += 1
        try:
            db.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)")
            try:
                with db.transaction() as conn:
                    conn.execute("INSERT INTO test_table (id, name) VALUES (1, 'test')")
                    raise ValueError("Intentional error")
            except ValueError:
                pass  # Expected

            result = db.fetchone("SELECT COUNT(*) FROM test_table")
            if result[0] != 0:
                all_validation_failures.append(f"Transaction not rolled back: {result[0]} rows")
        except Exception as e:
            all_validation_failures.append(f"Transaction test failed: {e}")

        # Test 5: Transaction commit
        total_tests += 1
        try:
            with db.transaction() as conn:
                conn.execute("INSERT INTO test_table (id, name) VALUES (1, 'committed')")

            result = db.fetchone("SELECT name FROM test_table WHERE id = 1")
            if result["name"] != "committed":
                all_validation_failures.append(f"Transaction not committed: {result['name']}")
        except Exception as e:
            all_validation_failures.append(f"Commit test failed: {e}")

        # Test 6: fetchall
        total_tests += 1
        try:
            db.execute("INSERT INTO test_table (id, name) VALUES (2, 'second')")
            rows = db.fetchall("SELECT * FROM test_table ORDER BY id")
            if len(rows) != 2:
                all_validation_failures.append(f"fetchall returned {len(rows)} rows, expected 2")
        except Exception as e:
            all_validation_failures.append(f"fetchall test failed: {e}")

        db.close()

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
