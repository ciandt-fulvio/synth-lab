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

# Database schema SQL
SCHEMA_SQL = """
-- Enable recommended settings
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
PRAGMA synchronous=NORMAL;

-- Synths table
CREATE TABLE IF NOT EXISTS synths (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    arquetipo TEXT,
    descricao TEXT,
    link_photo TEXT,
    avatar_path TEXT,
    created_at TEXT NOT NULL,
    version TEXT DEFAULT '2.0.0',
    demografia TEXT CHECK(json_valid(demografia) OR demografia IS NULL),
    psicografia TEXT CHECK(json_valid(psicografia) OR psicografia IS NULL),
    deficiencias TEXT CHECK(json_valid(deficiencias) OR deficiencias IS NULL),
    capacidades_tecnologicas TEXT CHECK(json_valid(capacidades_tecnologicas) OR capacidades_tecnologicas IS NULL)
);

CREATE INDEX IF NOT EXISTS idx_synths_arquetipo ON synths(arquetipo);
CREATE INDEX IF NOT EXISTS idx_synths_created_at ON synths(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_synths_nome ON synths(nome);

-- Research executions table
CREATE TABLE IF NOT EXISTS research_executions (
    exec_id TEXT PRIMARY KEY,
    topic_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'completed',
    synth_count INTEGER NOT NULL,
    successful_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    model TEXT DEFAULT 'gpt-5-mini',
    max_turns INTEGER DEFAULT 6,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    summary_content TEXT,
    CHECK(status IN ('pending', 'running', 'generating_summary', 'completed', 'failed'))
);

CREATE INDEX IF NOT EXISTS idx_executions_topic ON research_executions(topic_name);
CREATE INDEX IF NOT EXISTS idx_executions_status ON research_executions(status);
CREATE INDEX IF NOT EXISTS idx_executions_started ON research_executions(started_at DESC);

-- Transcripts table
CREATE TABLE IF NOT EXISTS transcripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exec_id TEXT NOT NULL,
    synth_id TEXT NOT NULL,
    synth_name TEXT,
    status TEXT NOT NULL DEFAULT 'completed',
    turn_count INTEGER DEFAULT 0,
    timestamp TEXT NOT NULL,
    messages TEXT CHECK(json_valid(messages) OR messages IS NULL),
    UNIQUE(exec_id, synth_id)
);

CREATE INDEX IF NOT EXISTS idx_transcripts_exec ON transcripts(exec_id);
CREATE INDEX IF NOT EXISTS idx_transcripts_synth ON transcripts(synth_id);

-- PR-FAQ metadata table
CREATE TABLE IF NOT EXISTS prfaq_metadata (
    exec_id TEXT PRIMARY KEY,
    generated_at TEXT,
    model TEXT DEFAULT 'gpt-5-mini',
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

-- Topic guides cache table
CREATE TABLE IF NOT EXISTS topic_guides_cache (
    name TEXT PRIMARY KEY,
    display_name TEXT,
    description TEXT,
    question_count INTEGER DEFAULT 0,
    file_count INTEGER DEFAULT 0,
    script_hash TEXT,
    created_at TEXT,
    updated_at TEXT
);

-- Schema migrations table
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL,
    description TEXT
);

INSERT OR IGNORE INTO schema_migrations (version, applied_at, description)
VALUES (1, datetime('now'), 'Initial schema creation');

INSERT OR IGNORE INTO schema_migrations (version, applied_at, description)
VALUES (2, datetime('now'), 'Add status, error_message, started_at to prfaq_metadata');
"""


# Migration SQL for existing databases
MIGRATION_V2_SQL = """
-- Migration V2: Add status columns to prfaq_metadata
-- This handles existing databases that don't have these columns

-- Add status column if not exists
ALTER TABLE prfaq_metadata ADD COLUMN status TEXT DEFAULT 'completed';

-- Add error_message column if not exists
ALTER TABLE prfaq_metadata ADD COLUMN error_message TEXT;

-- Add started_at column if not exists
ALTER TABLE prfaq_metadata ADD COLUMN started_at TEXT;

-- Update existing records to have 'completed' status
UPDATE prfaq_metadata SET status = 'completed' WHERE status IS NULL;

-- Create index on status
CREATE INDEX IF NOT EXISTS idx_prfaq_status ON prfaq_metadata(status);

-- Record migration
INSERT OR IGNORE INTO schema_migrations (version, applied_at, description)
VALUES (2, datetime('now'), 'Add status, error_message, started_at to prfaq_metadata');
"""


def apply_migrations(db_path: Path | None = None) -> None:
    """
    Apply pending database migrations.

    Args:
        db_path: Path to database file. Defaults to config.DB_PATH.
    """
    import sqlite3

    target_path = db_path or DB_PATH

    if not target_path.exists():
        logger.info(f"Database not found at {target_path}, initializing...")
        init_database(db_path)
        return

    logger.info(f"Checking migrations for {target_path}")

    conn = sqlite3.connect(target_path)
    try:
        # Check current version
        try:
            cursor = conn.execute("SELECT MAX(version) FROM schema_migrations")
            current_version = cursor.fetchone()[0] or 0
        except sqlite3.OperationalError:
            # schema_migrations table doesn't exist, run init
            conn.executescript(SCHEMA_SQL)
            return

        logger.info(f"Current schema version: {current_version}")

        # Apply V2 migration if needed
        if current_version < 2:
            logger.info("Applying migration V2: Add prfaq_metadata status columns")
            try:
                # Try to add columns (may fail if already exist)
                conn.execute(
                    "ALTER TABLE prfaq_metadata ADD COLUMN status TEXT DEFAULT 'completed'"
                )
            except sqlite3.OperationalError:
                pass  # Column already exists

            try:
                conn.execute("ALTER TABLE prfaq_metadata ADD COLUMN error_message TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists

            try:
                conn.execute("ALTER TABLE prfaq_metadata ADD COLUMN started_at TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists

            # Update existing records
            conn.execute("UPDATE prfaq_metadata SET status = 'completed' WHERE status IS NULL")

            # Create index
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_prfaq_status ON prfaq_metadata(status)"
            )

            # Record migration
            conn.execute(
                "INSERT OR IGNORE INTO schema_migrations (version, applied_at, description) "
                "VALUES (2, datetime('now'), 'Add status, error_message, started_at to prfaq_metadata')"
            )
            conn.commit()
            logger.info("Migration V2 applied successfully")
            current_version = 2

        # Apply V3 migration if needed - Remove NOT NULL constraint from generated_at
        if current_version < 3:
            logger.info("Applying migration V3: Remove NOT NULL constraint from prfaq_metadata.generated_at")
            try:
                # SQLite doesn't support ALTER COLUMN, need to recreate table
                conn.executescript("""
                    -- Create new table without NOT NULL on generated_at
                    CREATE TABLE IF NOT EXISTS prfaq_metadata_new (
                        exec_id TEXT PRIMARY KEY,
                        generated_at TEXT,
                        model TEXT DEFAULT 'gpt-5-mini',
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

                    -- Copy data from old table
                    INSERT OR IGNORE INTO prfaq_metadata_new
                    SELECT exec_id, generated_at, model, validation_status, confidence_score,
                           headline, one_liner, faq_count, markdown_content, json_content,
                           status, error_message, started_at
                    FROM prfaq_metadata;

                    -- Drop old table
                    DROP TABLE prfaq_metadata;

                    -- Rename new table
                    ALTER TABLE prfaq_metadata_new RENAME TO prfaq_metadata;

                    -- Recreate indexes
                    CREATE INDEX IF NOT EXISTS idx_prfaq_generated ON prfaq_metadata(generated_at DESC);
                    CREATE INDEX IF NOT EXISTS idx_prfaq_status ON prfaq_metadata(status);
                """)

                # Record migration
                conn.execute(
                    "INSERT OR IGNORE INTO schema_migrations (version, applied_at, description) "
                    "VALUES (3, datetime('now'), 'Remove NOT NULL constraint from prfaq_metadata.generated_at')"
                )
                conn.commit()
                logger.info("Migration V3 applied successfully")
            except sqlite3.OperationalError as e:
                logger.warning(f"Migration V3 warning (may be already applied): {e}")

    finally:
        conn.close()


def init_database(db_path: Path | None = None) -> None:
    """
    Initialize database with schema.

    Args:
        db_path: Path to database file. Defaults to config.DB_PATH.
    """
    target_path = db_path or DB_PATH

    logger.info(f"Initializing database at {target_path}")

    # Ensure parent directory exists
    target_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(target_path)
    try:
        conn.executescript(SCHEMA_SQL)
        logger.info("Database schema created successfully")
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
