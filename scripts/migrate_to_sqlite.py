"""
Migration script: JSON to SQLite database.

Migrates existing JSON data to SQLite database per data-model.md schema.
Creates the database with all required tables and indexes.

Usage:
    uv run python scripts/migrate_to_sqlite.py

References:
    - Schema definition: specs/010-rest-api/data-model.md
"""

import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

from loguru import logger

from synth_lab.infrastructure.config import (
    AVATARS_DIR,
    DB_PATH,
    OUTPUT_DIR,
    REPORTS_DIR,
    SYNTHS_JSON_PATH,
    TRANSCRIPTS_DIR,
)


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
    model TEXT DEFAULT 'gpt-4.1-mini',
    max_turns INTEGER DEFAULT 6,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    summary_path TEXT,
    CHECK(status IN ('pending', 'running', 'completed', 'failed'))
);

CREATE INDEX IF NOT EXISTS idx_executions_topic ON research_executions(topic_name);
CREATE INDEX IF NOT EXISTS idx_executions_status ON research_executions(status);
CREATE INDEX IF NOT EXISTS idx_executions_started ON research_executions(started_at DESC);

-- Transcripts table
CREATE TABLE IF NOT EXISTS transcripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exec_id TEXT NOT NULL,
    synth_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'completed',
    turn_count INTEGER DEFAULT 0,
    timestamp TEXT NOT NULL,
    file_path TEXT,
    messages TEXT CHECK(json_valid(messages) OR messages IS NULL),
    UNIQUE(exec_id, synth_id)
);

CREATE INDEX IF NOT EXISTS idx_transcripts_exec ON transcripts(exec_id);
CREATE INDEX IF NOT EXISTS idx_transcripts_synth ON transcripts(synth_id);

-- PR-FAQ metadata table
CREATE TABLE IF NOT EXISTS prfaq_metadata (
    exec_id TEXT PRIMARY KEY,
    generated_at TEXT NOT NULL,
    model TEXT DEFAULT 'gpt-4.1-mini',
    validation_status TEXT DEFAULT 'valid',
    confidence_score REAL,
    headline TEXT,
    one_liner TEXT,
    faq_count INTEGER DEFAULT 0,
    markdown_path TEXT,
    json_path TEXT,
    CHECK(validation_status IN ('valid', 'invalid', 'pending'))
);

CREATE INDEX IF NOT EXISTS idx_prfaq_generated ON prfaq_metadata(generated_at DESC);

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
"""


def create_schema(conn: sqlite3.Connection) -> None:
    """Create database schema."""
    logger.info("Creating database schema...")
    conn.executescript(SCHEMA_SQL)
    logger.info("Schema created successfully")


def migrate_synths(conn: sqlite3.Connection) -> int:
    """Migrate synths from JSON to SQLite."""
    if not SYNTHS_JSON_PATH.exists():
        logger.warning(f"Synths JSON not found: {SYNTHS_JSON_PATH}")
        return 0

    logger.info(f"Loading synths from {SYNTHS_JSON_PATH}")
    with open(SYNTHS_JSON_PATH) as f:
        synths = json.load(f)

    count = 0
    for synth in synths:
        synth_id = synth.get("id", "")
        avatar_path = AVATARS_DIR / f"{synth_id}.png"
        avatar_path_str = str(avatar_path) if avatar_path.exists() else None

        conn.execute(
            """
            INSERT OR REPLACE INTO synths
            (id, nome, arquetipo, descricao, link_photo, avatar_path, created_at, version,
             demografia, psicografia, deficiencias, capacidades_tecnologicas)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                synth_id,
                synth.get("nome", ""),
                synth.get("arquetipo"),
                synth.get("descricao"),
                synth.get("link_photo"),
                avatar_path_str,
                synth.get("created_at", datetime.now().isoformat()),
                synth.get("version", "2.0.0"),
                json.dumps(synth.get("demografia")) if synth.get("demografia") else None,
                json.dumps(synth.get("psicografia")) if synth.get("psicografia") else None,
                json.dumps(synth.get("deficiencias")) if synth.get("deficiencias") else None,
                json.dumps(synth.get("capacidades_tecnologicas"))
                if synth.get("capacidades_tecnologicas")
                else None,
            ),
        )
        count += 1

    logger.info(f"Migrated {count} synths")
    return count


def parse_exec_id_from_path(path: Path) -> tuple[str, str] | None:
    """
    Parse execution ID and topic from transcript path.

    Expected formats:
    - batch_{topic}_{timestamp}/{synth_id}.json
    - {topic}_{synth_id}_{timestamp}.json
    """
    # Check if it's a batch directory
    if path.is_dir() and path.name.startswith("batch_"):
        match = re.match(r"batch_(.+?)_(\d{8}_\d{6})", path.name)
        if match:
            topic = match.group(1)
            exec_id = path.name
            return exec_id, topic

    # Check file pattern
    if path.suffix == ".json" and not path.parent.name.startswith("batch_"):
        match = re.match(r"(.+?)_([a-z]{6})_(\d{8}_\d{6})\.json", path.name)
        if match:
            topic = match.group(1)
            timestamp = match.group(3)
            exec_id = f"batch_{topic}_{timestamp}"
            return exec_id, topic

    return None


def migrate_transcripts(conn: sqlite3.Connection) -> int:
    """Migrate transcripts from filesystem to SQLite."""
    if not TRANSCRIPTS_DIR.exists():
        logger.warning(f"Transcripts directory not found: {TRANSCRIPTS_DIR}")
        return 0

    logger.info(f"Scanning transcripts in {TRANSCRIPTS_DIR}")

    # Track executions to avoid duplicates
    executions: dict[str, dict] = {}
    transcript_count = 0

    # Process batch directories
    for item in TRANSCRIPTS_DIR.iterdir():
        if item.is_dir() and item.name.startswith("batch_"):
            parsed = parse_exec_id_from_path(item)
            if not parsed:
                continue

            exec_id, topic_name = parsed

            # Create execution record if needed
            if exec_id not in executions:
                executions[exec_id] = {
                    "exec_id": exec_id,
                    "topic_name": topic_name,
                    "status": "completed",
                    "synth_count": 0,
                    "successful_count": 0,
                    "started_at": datetime.now().isoformat(),
                }

            # Process transcripts in batch directory
            for transcript_file in item.glob("*.json"):
                synth_id = transcript_file.stem

                try:
                    with open(transcript_file) as f:
                        data = json.load(f)

                    messages = data.get("messages", [])
                    turn_count = len([m for m in messages if m.get("speaker") == "Interviewer"])

                    conn.execute(
                        """
                        INSERT OR REPLACE INTO transcripts
                        (exec_id, synth_id, status, turn_count, timestamp, file_path, messages)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            exec_id,
                            synth_id,
                            "completed",
                            turn_count,
                            data.get("timestamp", datetime.now().isoformat()),
                            str(transcript_file),
                            json.dumps(messages),
                        ),
                    )
                    executions[exec_id]["synth_count"] += 1
                    executions[exec_id]["successful_count"] += 1
                    transcript_count += 1
                except Exception as e:
                    logger.warning(f"Failed to process {transcript_file}: {e}")

    # Insert execution records
    for execution in executions.values():
        conn.execute(
            """
            INSERT OR REPLACE INTO research_executions
            (exec_id, topic_name, status, synth_count, successful_count, started_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                execution["exec_id"],
                execution["topic_name"],
                execution["status"],
                execution["synth_count"],
                execution["successful_count"],
                execution["started_at"],
            ),
        )

    logger.info(f"Migrated {transcript_count} transcripts in {len(executions)} executions")
    return transcript_count


def migrate_prfaqs(conn: sqlite3.Connection) -> int:
    """Migrate PR-FAQ metadata from filesystem to SQLite."""
    if not REPORTS_DIR.exists():
        logger.warning(f"Reports directory not found: {REPORTS_DIR}")
        return 0

    logger.info(f"Scanning PR-FAQs in {REPORTS_DIR}")
    count = 0

    for prfaq_file in REPORTS_DIR.glob("*_prfaq.md"):
        # Parse exec_id from filename: batch_{topic}_{timestamp}_prfaq.md
        match = re.match(r"(batch_.+?_\d{8}_\d{6})_prfaq\.md", prfaq_file.name)
        if not match:
            continue

        exec_id = match.group(1)

        # Try to extract headline from file
        headline = None
        try:
            with open(prfaq_file) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("# "):
                        headline = line[2:]
                        break
        except Exception:
            pass

        conn.execute(
            """
            INSERT OR REPLACE INTO prfaq_metadata
            (exec_id, generated_at, markdown_path, headline)
            VALUES (?, ?, ?, ?)
        """,
            (
                exec_id,
                datetime.fromtimestamp(prfaq_file.stat().st_mtime).isoformat(),
                str(prfaq_file),
                headline,
            ),
        )
        count += 1

    logger.info(f"Migrated {count} PR-FAQs")
    return count


def main() -> None:
    """Run migration."""
    logger.info(f"Starting migration to {DB_PATH}")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    try:
        create_schema(conn)
        synth_count = migrate_synths(conn)
        transcript_count = migrate_transcripts(conn)
        prfaq_count = migrate_prfaqs(conn)
        conn.commit()

        logger.info("=" * 50)
        logger.info("Migration complete:")
        logger.info(f"  - Synths: {synth_count}")
        logger.info(f"  - Transcripts: {transcript_count}")
        logger.info(f"  - PR-FAQs: {prfaq_count}")
        logger.info(f"  - Database: {DB_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
