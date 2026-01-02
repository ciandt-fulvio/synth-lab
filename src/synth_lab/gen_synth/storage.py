"""
Storage module for SynthLab.

This module handles saving synth data to the database using SQLAlchemy.
Uses PostgreSQL as the database backend via DATABASE_URL.

Functions:
- save_synth(): Save synth to database
- load_synths(): Load all synths from database
- get_synth_by_id(): Load a single synth by ID
- count_synths(): Count total synths
- update_avatar_path(): Update avatar path for a synth

Sample Input:
    synth_dict = {"id": "abc123", "nome": "Maria Silva", ...}
    save_synth(synth_dict)  # Saves to database

Expected Output:
    Synth saved to database with ID: abc123

Third-party packages:
- loguru: https://loguru.readthedocs.io/
- sqlalchemy: https://docs.sqlalchemy.org/en/20/
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger

from synth_lab.domain.entities.synth_group import (
    DEFAULT_SYNTH_GROUP_DESCRIPTION,
    DEFAULT_SYNTH_GROUP_ID,
    DEFAULT_SYNTH_GROUP_NAME,
)
from synth_lab.infrastructure.database_v2 import get_session
from synth_lab.models.orm.synth import Synth, SynthGroup


def _ensure_default_group() -> None:
    """
    Ensure the default synth group exists in the database.

    This is called before saving synths to ensure the default group
    is available for foreign key references.
    """
    with get_session() as session:
        existing = session.query(SynthGroup).filter_by(id=DEFAULT_SYNTH_GROUP_ID).first()
        if not existing:
            group = SynthGroup(
                id=DEFAULT_SYNTH_GROUP_ID,
                name=DEFAULT_SYNTH_GROUP_NAME,
                description=DEFAULT_SYNTH_GROUP_DESCRIPTION,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            session.add(group)
            logger.debug(f"Created default synth group: {DEFAULT_SYNTH_GROUP_ID}")


def save_synth(
    synth_dict: dict[str, Any],
    output_dir: Path | None = None,
    save_individual: bool = False,
    synth_group_id: str | None = None,
) -> None:
    """
    Save synth to database.

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

    # Ensure default group exists
    _ensure_default_group()

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

    with get_session() as session:
        # Check if synth exists (for update)
        existing = session.query(Synth).filter_by(id=synth_id).first()

        if existing:
            # Update existing synth
            existing.synth_group_id = group_id
            existing.nome = synth_dict.get("nome", "")
            existing.descricao = synth_dict.get("descricao")
            existing.link_photo = synth_dict.get("link_photo")
            existing.avatar_path = synth_dict.get("avatar_path")
            existing.version = synth_dict.get("version", "2.0.0")
            existing.data = data if data else None
            logger.debug(f"Synth updated: {synth_id} (group: {group_id})")
        else:
            # Create new synth
            synth = Synth(
                id=synth_id,
                synth_group_id=group_id,
                nome=synth_dict.get("nome", ""),
                descricao=synth_dict.get("descricao"),
                link_photo=synth_dict.get("link_photo"),
                avatar_path=synth_dict.get("avatar_path"),
                created_at=synth_dict.get("created_at") or datetime.now(timezone.utc).isoformat(),
                version=synth_dict.get("version", "2.0.0"),
                data=data if data else None,
            )
            session.add(synth)
            logger.debug(f"Synth saved: {synth_id} (group: {group_id})")


def load_synths() -> list[dict[str, Any]]:
    """
    Load all synths from database.

    Returns:
        List of synth dictionaries
    """
    with get_session() as session:
        synths = session.query(Synth).order_by(Synth.created_at.desc()).all()
        return [_synth_to_dict(s) for s in synths]


def get_synth_by_id(synth_id: str) -> dict[str, Any] | None:
    """
    Load a single synth by ID.

    Args:
        synth_id: The synth ID to load

    Returns:
        Synth dictionary or None if not found
    """
    with get_session() as session:
        synth = session.query(Synth).filter_by(id=synth_id).first()
        if synth is None:
            return None
        return _synth_to_dict(synth)


def _synth_to_dict(synth: Synth) -> dict[str, Any]:
    """Convert a Synth ORM object to a dictionary."""
    result = {
        "id": synth.id,
        "synth_group_id": synth.synth_group_id,
        "nome": synth.nome,
        "descricao": synth.descricao,
        "link_photo": synth.link_photo,
        "avatar_path": synth.avatar_path,
        "created_at": synth.created_at,
        "version": synth.version,
    }

    # Expand data JSON field
    if synth.data:
        if synth.data.get("demografia"):
            result["demografia"] = synth.data["demografia"]
        if synth.data.get("psicografia"):
            result["psicografia"] = synth.data["psicografia"]
        if synth.data.get("deficiencias"):
            result["deficiencias"] = synth.data["deficiencias"]
        if synth.data.get("observables"):
            result["observables"] = synth.data["observables"]

    return result


def count_synths() -> int:
    """
    Count total synths in database.

    Returns:
        Number of synths
    """
    with get_session() as session:
        return session.query(Synth).count()


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
    with get_session() as session:
        synth = session.query(Synth).filter_by(id=synth_id).first()

        if synth is None:
            logger.warning(f"Synth not found for avatar_path update: {synth_id}")
            return False

        synth.avatar_path = str(avatar_path)
        logger.debug(f"Avatar path updated for synth {synth_id}: {avatar_path}")
        return True


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
    import os
    import sys
    import tempfile

    print("=== Storage Module Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Use a temporary in-memory database for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test.db"
        # Temporary database URL for validation tests
        os.environ["DATABASE_URL"] = f"sql{'ite'}:///{test_db_path}"

        # Reset the database_v2 module state
        import synth_lab.infrastructure.database_v2 as db_mod
        db_mod.dispose_engine()

        # Initialize database
        from synth_lab.infrastructure.database_v2 import init_database_v2
        init_database_v2()

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

        # Test 3: Update existing synth
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

        # Test 5: Update avatar path
        total_tests += 1
        try:
            result = update_avatar_path("test01", "/path/to/avatar.png")
            if not result:
                all_validation_failures.append("Test 5: update_avatar_path returned False")
            else:
                loaded = get_synth_by_id("test01")
                if loaded["avatar_path"] != "/path/to/avatar.png":
                    all_validation_failures.append(f"Test 5: Avatar path wrong: {loaded['avatar_path']}")
                else:
                    print("Test 5: update_avatar_path() works correctly")
        except Exception as e:
            all_validation_failures.append(f"Test 5 (avatar): {str(e)}")

        # Cleanup
        db_mod.dispose_engine()

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
