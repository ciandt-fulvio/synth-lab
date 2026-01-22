"""
Synth service for synth-lab.

Business logic layer for synth operations.

References:
    - API spec: specs/010-rest-api/contracts/openapi.yaml
"""

from pathlib import Path

from synth_lab.infrastructure.storage_client import check_object_exists, generate_view_url
from synth_lab.models.pagination import PaginatedResponse, PaginationParams
from synth_lab.models.synth import SynthDetail, SynthFieldInfo, SynthSummary
from synth_lab.repositories.synth_repository import SynthRepository
from synth_lab.services.errors import AvatarNotFoundError


class SynthService:
    """Service for synth business logic."""

    def __init__(self, synth_repo: SynthRepository | None = None):
        """
        Initialize synth service.

        Args:
            synth_repo: Synth repository. Defaults to new instance.
        """
        self.synth_repo = synth_repo or SynthRepository()

    def list_synths(
        self,
        params: PaginationParams | None = None,
        fields: list[str] | None = None,
        synth_group_id: str | None = None) -> PaginatedResponse[SynthSummary]:
        """
        List synths with pagination.

        Args:
            params: Pagination parameters.
            fields: Optional list of fields to include.
            synth_group_id: Optional filter by synth group ID.

        Returns:
            Paginated response with synth summaries.
        """
        params = params or PaginationParams()
        return self.synth_repo.list_synths(params, fields, synth_group_id=synth_group_id)

    def get_synth(self, synth_id: str) -> SynthDetail:
        """
        Get a synth by ID with full details.

        Args:
            synth_id: 6-character synth ID.

        Returns:
            SynthDetail with all nested data.

        Raises:
            SynthNotFoundError: If synth not found.
        """
        return self.synth_repo.get_by_id(synth_id)

    def search_synths(
        self,
        where_clause: str | None = None,
        query: str | None = None,
        params: PaginationParams | None = None) -> PaginatedResponse[SynthSummary]:
        """
        Search synths with WHERE clause or full query.

        Args:
            where_clause: SQL WHERE clause (e.g., "idade > 30").
            query: Full SELECT query (limited to SELECT only).
            params: Pagination parameters.

        Returns:
            Paginated response with matching synths.

        Raises:
            InvalidQueryError: If query is invalid or unsafe.
        """
        params = params or PaginationParams()
        return self.synth_repo.search(where_clause, query, params)

    def get_avatar_url(self, synth_id: str, expires_in: int = 3600) -> str:
        """
        Get a presigned S3 URL for the synth's avatar.

        Args:
            synth_id: 6-character synth ID.
            expires_in: URL expiration time in seconds (default: 1 hour).

        Returns:
            Presigned S3 URL for the avatar image.

        Raises:
            SynthNotFoundError: If synth not found.
            AvatarNotFoundError: If avatar doesn't exist in S3.
        """
        # Get the S3 key from repository (validates synth exists)
        s3_key = self.synth_repo.get_avatar_s3_key(synth_id)

        # Check if avatar exists in S3
        if not s3_key or not check_object_exists(s3_key):
            raise AvatarNotFoundError(synth_id)

        # Generate presigned URL
        return generate_view_url(s3_key, expires_in)

    def get_avatar(self, synth_id: str) -> Path:
        """
        DEPRECATED: Use get_avatar_url() instead.

        Get the avatar file path for a synth.
        This method is deprecated as avatars are now stored in S3.

        Args:
            synth_id: 6-character synth ID.

        Returns:
            Path object with S3 key (not a real local path).

        Raises:
            SynthNotFoundError: If synth not found.
            AvatarNotFoundError: If avatar doesn't exist in S3.
        """
        s3_key = self.synth_repo.get_avatar_s3_key(synth_id)

        if not s3_key or not check_object_exists(s3_key):
            raise AvatarNotFoundError(synth_id)

        return Path(s3_key)

    def get_fields(self) -> list[SynthFieldInfo]:
        """
        Get available synth field metadata.

        Returns:
            List of field information.
        """
        return self.synth_repo.get_fields()


if __name__ == "__main__":
    import sys

    from synth_lab.infrastructure.config import DB_PATH
    from synth_lab.services.errors import AvatarNotFoundError, SynthNotFoundError

    # Validation with real database
    all_validation_failures = []
    total_tests = 0

    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}. Run migration first.")
        sys.exit(1)

    db = DatabaseManager(DB_PATH)
    repo = SynthRepository()
    service = SynthService(repo)

    # Test 1: List synths
    total_tests += 1
    try:
        result = service.list_synths()
        if len(result.data) == 0:
            all_validation_failures.append("No synths found")
        print(f"  Listed {result.pagination.total} synths")
    except Exception as e:
        all_validation_failures.append(f"List synths failed: {e}")

    # Test 2: Get synth by ID
    total_tests += 1
    try:
        result = service.list_synths(PaginationParams(limit=1))
        if result.data:
            synth_id = result.data[0].id
            synth = service.get_synth(synth_id)
            if synth.id != synth_id:
                all_validation_failures.append(f"ID mismatch: {synth.id}")
            print(f"  Got synth: {synth.nome}")
    except Exception as e:
        all_validation_failures.append(f"Get synth failed: {e}")

    # Test 3: Get non-existent synth
    total_tests += 1
    try:
        service.get_synth("zzz999")
        all_validation_failures.append("Should raise SynthNotFoundError")
    except SynthNotFoundError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Wrong exception: {e}")

    # Test 4: Search synths
    total_tests += 1
    try:
        result = service.search_synths(where_clause="1=1")
        if result.pagination.total < 1:
            all_validation_failures.append("Search should find synths")
    except Exception as e:
        all_validation_failures.append(f"Search synths failed: {e}")

    # Test 5: Get fields
    total_tests += 1
    try:
        fields = service.get_fields()
        if len(fields) < 5:
            all_validation_failures.append(f"Expected at least 5 fields: {len(fields)}")
    except Exception as e:
        all_validation_failures.append(f"Get fields failed: {e}")

    # Test 6: Get avatar (may or may not exist)
    total_tests += 1
    try:
        result = service.list_synths(PaginationParams(limit=1))
        if result.data:
            synth_id = result.data[0].id
            try:
                avatar_path = service.get_avatar(synth_id)
                if not str(avatar_path).endswith(".png"):
                    all_validation_failures.append(
                        f"Avatar path should end with .png: {avatar_path}"
                    )
                print(f"  Avatar path: {avatar_path}")
            except AvatarNotFoundError:
                print(f"  Avatar not found for {synth_id} (expected if no avatar file)")
    except Exception as e:
        all_validation_failures.append(f"Get avatar failed: {e}")


    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
