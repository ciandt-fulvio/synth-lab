"""
Dependency injection for synth-lab API.

Provides FastAPI dependencies for services and repositories.

References:
    - FastAPI dependencies: https://fastapi.tiangolo.com/tutorial/dependencies/
"""

from functools import lru_cache

from synth_lab.infrastructure.database import DatabaseManager, get_database
from synth_lab.infrastructure.llm_client import LLMClient, get_llm_client


@lru_cache
def get_db() -> DatabaseManager:
    """Get the database manager instance."""
    return get_database()


@lru_cache
def get_llm() -> LLMClient:
    """Get the LLM client instance."""
    return get_llm_client()


# Service dependencies will be added as services are implemented
# Example:
# def get_synth_service() -> SynthService:
#     """Get synth service with dependencies."""
#     return SynthService(
#         synth_repo=SynthRepository(get_db()),
#     )


if __name__ == "__main__":
    import sys

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Test 1: get_db returns DatabaseManager
    total_tests += 1
    try:
        db = get_db()
        if not isinstance(db, DatabaseManager):
            all_validation_failures.append(f"get_db should return DatabaseManager: {type(db)}")
    except Exception as e:
        all_validation_failures.append(f"get_db test failed: {e}")

    # Test 2: get_db is cached (same instance)
    total_tests += 1
    try:
        db1 = get_db()
        db2 = get_db()
        if db1 is not db2:
            all_validation_failures.append("get_db should return same instance (cached)")
    except Exception as e:
        all_validation_failures.append(f"get_db caching test failed: {e}")

    # Test 3: get_llm returns LLMClient
    total_tests += 1
    try:
        llm = get_llm()
        if not isinstance(llm, LLMClient):
            all_validation_failures.append(f"get_llm should return LLMClient: {type(llm)}")
    except Exception as e:
        all_validation_failures.append(f"get_llm test failed: {e}")

    # Test 4: get_llm is cached
    total_tests += 1
    try:
        llm1 = get_llm()
        llm2 = get_llm()
        if llm1 is not llm2:
            all_validation_failures.append("get_llm should return same instance (cached)")
    except Exception as e:
        all_validation_failures.append(f"get_llm caching test failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
