"""
Storage module for SynthLab.

This module handles saving synth data directly to SQLite database.

Functions:
- save_synth(): Save synth to database
- load_synths(): Load all synths from database
- get_synth_by_id(): Load a single synth by ID

Sample Input:
    synth_dict = {"id": "abc123", "nome": "Maria Silva", ...}
    save_synth(synth_dict)  # Saves to SQLite database

Expected Output:
    Synth saved to database with ID: abc123

Third-party packages:
- loguru: https://loguru.readthedocs.io/
"""

import json
import sqlite3
from pathlib import Path
from typing import Any

from loguru import logger

import synth_lab.infrastructure.config as config_module
from synth_lab.domain.entities.synth_group import (
    DEFAULT_SYNTH_GROUP_DESCRIPTION,
    DEFAULT_SYNTH_GROUP_ID,
    DEFAULT_SYNTH_GROUP_NAME,
)


def _get_db_path():
    """Get current DB_PATH from config (allows runtime override for tests)."""
    return config_module.DB_PATH


def _ensure_database() -> None:
    """Ensure database exists and has schema."""
    db_path = _get_db_path()
    if not db_path.exists():
        from synth_lab.infrastructure.database import init_database

        init_database(db_path)


def _get_connection() -> sqlite3.Connection:
    """Get database connection with proper settings."""
    _ensure_database()

    conn = sqlite3.connect(str(_get_db_path()))
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_default_group(conn: sqlite3.Connection) -> None:
    """
    Ensure the default synth group exists in the database.

    This is called before saving synths to ensure the default group
    is available for foreign key references.

    Args:
        conn: Active database connection.
    """
    from datetime import datetime, timezone

    conn.execute(
        """
        INSERT OR IGNORE INTO synth_groups (id, name, description, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            DEFAULT_SYNTH_GROUP_ID,
            DEFAULT_SYNTH_GROUP_NAME,
            DEFAULT_SYNTH_GROUP_DESCRIPTION,
            datetime.now(timezone.utc).isoformat(),
        ),
    )


def save_synth(
    synth_dict: dict[str, Any],
    output_dir: Path | None = None,
    save_individual: bool = False,
    synth_group_id: str | None = None,
) -> None:
    """
    Save synth to SQLite database.

    Args:
        synth_dict: Dictionary containing complete synth data (must have "id" key)
        output_dir: Deprecated, ignored (kept for API compatibility)
        save_individual: Deprecated, ignored (kept for API compatibility)
        synth_group_id: Optional synth group ID to link this synth to.
                        If not provided, uses DEFAULT_SYNTH_GROUP_ID.

    Raises:
        KeyError: If synth_dict doesn't contain "id" key
    """
    synth_id = synth_dict["id"]

    # Use synth_group_id from parameter, synth_dict, or DEFAULT
    group_id = synth_group_id or synth_dict.get("synth_group_id") or DEFAULT_SYNTH_GROUP_ID

    # Build data object with nested fields
    data = {}
    if synth_dict.get("demografia"):
        data["demografia"] = synth_dict["demografia"]
    if synth_dict.get("psicografia"):
        data["psicografia"] = synth_dict["psicografia"]
    if synth_dict.get("deficiencias"):
        data["deficiencias"] = synth_dict["deficiencias"]
    if synth_dict.get("observables"):
        data["observables"] = synth_dict["observables"]

    conn = _get_connection()
    try:
        # Ensure default group exists before inserting synth with foreign key
        _ensure_default_group(conn)

        conn.execute(
            """
            INSERT OR REPLACE INTO synths
            (id, synth_group_id, nome, descricao, link_photo, avatar_path, created_at, version, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                synth_id,
                group_id,
                synth_dict.get("nome", ""),
                synth_dict.get("descricao"),
                synth_dict.get("link_photo"),
                synth_dict.get("avatar_path"),
                synth_dict.get("created_at"),
                synth_dict.get("version", "2.0.0"),
                json.dumps(data) if data else None,
            ),
        )
        conn.commit()
        logger.debug(f"Synth saved: {synth_id} (group: {group_id})")
    finally:
        conn.close()


def load_synths() -> list[dict[str, Any]]:
    """
    Load all synths from database.

    Returns:
        List of synth dictionaries
    """
    conn = _get_connection()
    try:
        cursor = conn.execute("SELECT * FROM synths ORDER BY created_at DESC")
        rows = cursor.fetchall()

        synths = []
        for row in rows:
            synth = _row_to_dict(row)
            synths.append(synth)

        return synths
    finally:
        conn.close()


def get_synth_by_id(synth_id: str) -> dict[str, Any] | None:
    """
    Load a single synth by ID.

    Args:
        synth_id: The synth ID to load

    Returns:
        Synth dictionary or None if not found
    """
    conn = _get_connection()
    try:
        cursor = conn.execute("SELECT * FROM synths WHERE id = ?", (synth_id,))
        row = cursor.fetchone()

        if row is None:
            return None

        return _row_to_dict(row)
    finally:
        conn.close()


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    """Convert a database row to a synth dictionary."""
    synth = {
        "id": row["id"],
        "synth_group_id": row["synth_group_id"] if "synth_group_id" in row.keys() else None,
        "nome": row["nome"],
        "descricao": row["descricao"],
        "link_photo": row["link_photo"],
        "avatar_path": row["avatar_path"],
        "created_at": row["created_at"],
        "version": row["version"],
    }

    # Parse data JSON field (contains all nested data)
    if row["data"]:
        data = json.loads(row["data"])
        if data.get("demografia"):
            synth["demografia"] = data["demografia"]
        if data.get("psicografia"):
            synth["psicografia"] = data["psicografia"]
        if data.get("deficiencias"):
            synth["deficiencias"] = data["deficiencias"]
        if data.get("observables"):
            synth["observables"] = data["observables"]

    return synth


def count_synths() -> int:
    """
    Count total synths in database.

    Returns:
        Number of synths
    """
    conn = _get_connection()
    try:
        cursor = conn.execute("SELECT COUNT(*) FROM synths")
        return cursor.fetchone()[0]
    finally:
        conn.close()


def update_avatar_path(synth_id: str, avatar_path: str | Path) -> bool:
    """
    Update the avatar_path field for a synth.

    Called after avatar image is generated and saved to disk.

    Args:
        synth_id: The synth ID to update
        avatar_path: Path to the avatar image file

    Returns:
        True if update was successful, False if synth not found

    Example:
        >>> update_avatar_path("abc123", "output/synths/avatar/abc123.png")
        True
    """
    conn = _get_connection()
    try:
        cursor = conn.execute(
            "UPDATE synths SET avatar_path = ? WHERE id = ?",
            (str(avatar_path), synth_id),
        )
        conn.commit()

        if cursor.rowcount > 0:
            logger.debug(f"Avatar path updated for synth {synth_id}: {avatar_path}")
            return True
        else:
            logger.warning(f"Synth not found for avatar_path update: {synth_id}")
            return False
    finally:
        conn.close()


# Deprecated functions kept for backward compatibility
def load_consolidated_synths(output_dir: Path | None = None) -> list[dict[str, Any]]:
    """
    Deprecated: Use load_synths() instead.

    Load all synths from database.

    Args:
        output_dir: Deprecated, ignored

    Returns:
        List of synth dictionaries
    """
    logger.warning("load_consolidated_synths is deprecated, use load_synths() instead")
    return load_synths()


def save_consolidated_synths(synths: list[dict[str, Any]], output_dir: Path | None = None) -> None:
    """
    Deprecated: Use save_synth() for each synth instead.

    Save list of synths to database.

    Args:
        synths: List of synth dictionaries
        output_dir: Deprecated, ignored
    """
    logger.warning("save_consolidated_synths is deprecated, use save_synth() for each synth")
    for synth in synths:
        save_synth(synth)


if __name__ == "__main__":
    """Validation block - test with real data."""
    import sys
    import tempfile

    print("=== Storage Module Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Use a temporary database for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        # Override DB_PATH for testing
        test_db_path = Path(tmpdir) / "test.db"

        # Patch the config module DB_PATH temporarily
        original_db_path = config_module.DB_PATH
        config_module.DB_PATH = test_db_path

        # Initialize test database
        from synth_lab.infrastructure.database import init_database

        init_database(test_db_path)

        # Test 1: Save synth to database
        total_tests += 1
        try:
            test_synth1 = {
                "id": "test01",
                "nome": "Test Person 1",
                "created_at": "2024-01-01T00:00:00",
                "version": "2.3.0",
                "descricao": "Test description",
                "link_photo": "https://example.com/photo.png",
                "demografia": {"idade": 30, "genero_biologico": "masculino"},
                "psicografia": {"interesses": ["tecnologia"]},
                "observables": {
                    "digital_literacy": 0.75,
                    "similar_tool_experience": 0.5,
                    "motor_ability": 1.0,
                    "time_availability": 0.6,
                    "domain_expertise": 0.5,
                },
            }

            save_synth(test_synth1)

            # Verify it was saved
            loaded = get_synth_by_id("test01")
            if loaded is None:
                all_validation_failures.append("Test 1: Synth not found after save")
            elif loaded["nome"] != "Test Person 1":
                all_validation_failures.append(f"Test 1: Wrong nome: {loaded['nome']}")
            elif loaded["demografia"]["idade"] != 30:
                all_validation_failures.append(f"Test 1: Wrong idade: {loaded['demografia']}")
            elif loaded.get("observables", {}).get("digital_literacy") != 0.75:
                all_validation_failures.append(
                    f"Test 1: Wrong observables: {loaded.get('observables')}"
                )
            else:
                print("Test 1: save_synth() saves to database correctly (with observables)")
        except Exception as e:
            all_validation_failures.append(f"Test 1 (save synth): {str(e)}")

        # Test 2: Save multiple synths and load all
        total_tests += 1
        try:
            test_synth2 = {
                "id": "test02",
                "nome": "Test Person 2",
                "created_at": "2024-01-02T00:00:00",
                "version": "2.0.0",
            }
            save_synth(test_synth2)

            all_synths = load_synths()
            if len(all_synths) != 2:
                all_validation_failures.append(f"Test 2: Expected 2 synths, got {len(all_synths)}")
            else:
                print("Test 2: load_synths() loads all synths correctly")
        except Exception as e:
            all_validation_failures.append(f"Test 2 (load all): {str(e)}")

        # Test 3: Update existing synth (INSERT OR REPLACE)
        total_tests += 1
        try:
            updated_synth = {
                "id": "test01",
                "nome": "Updated Name",
                "created_at": "2024-01-01T00:00:00",
                "version": "2.0.0",
            }
            save_synth(updated_synth)

            loaded = get_synth_by_id("test01")
            if loaded["nome"] != "Updated Name":
                all_validation_failures.append(f"Test 3: Name not updated: {loaded['nome']}")
            else:
                # Verify count is still 2
                count = count_synths()
                if count != 2:
                    all_validation_failures.append(f"Test 3: Count changed to {count}, expected 2")
                else:
                    print("Test 3: save_synth() updates existing synth correctly")
        except Exception as e:
            all_validation_failures.append(f"Test 3 (update): {str(e)}")

        # Test 4: Get non-existent synth
        total_tests += 1
        try:
            result = get_synth_by_id("nonexistent")
            if result is not None:
                all_validation_failures.append("Test 4: Should return None for nonexistent ID")
            else:
                print("Test 4: get_synth_by_id() returns None for nonexistent ID")
        except Exception as e:
            all_validation_failures.append(f"Test 4 (nonexistent): {str(e)}")

        # Restore original DB_PATH
        config_module.DB_PATH = original_db_path

    # Final validation result
    print(f"\n{'=' * 60}")
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Function is validated and formal tests can now be written")
        sys.exit(0)
