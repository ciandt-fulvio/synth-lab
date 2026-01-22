"""
Avatar generation service for synth-lab.

Ensures synths have avatars generated before interviews or other operations.
Avatars are stored in S3 and accessed via presigned URLs.

References:
    - Avatar Generator: synth_lab.gen_synth.avatar_generator
    - S3 Storage: synth_lab.infrastructure.storage_client

Sample Input:
    synth_ids = ["synth_001", "synth_002", "synth_003"]

Expected Output:
    Avatars generated for synths without existing avatar files in S3.
    Returns dict of {synth_id: s3_object_key} for generated avatars.
"""

import math
from pathlib import Path
from typing import Any, Awaitable, Callable

from loguru import logger

from synth_lab.infrastructure.config import AVATARS_DIR
from synth_lab.infrastructure.storage_client import (
    check_object_exists,
    generate_view_url,
)


class AvatarService:
    """Service for ensuring synths have avatar images in S3."""

    def __init__(self, avatars_dir: Path | None = None):
        """
        Initialize avatar service.

        Args:
            avatars_dir: DEPRECATED - avatars are now stored in S3.
                         Kept for backwards compatibility.
        """
        self.avatars_dir = avatars_dir or AVATARS_DIR
        self.logger = logger.bind(component="avatar_service")

    async def ensure_avatars_for_synths(
        self,
        synths: list[dict[str, Any]],
        on_generation_start: Callable[[int], Awaitable[None]] | None = None,
        on_generation_complete: Callable[[int], Awaitable[None]] | None = None) -> dict[str, str]:
        """
        Ensure all synths have avatars generated in S3.

        Checks which synths are missing avatar files in S3 and generates them automatically.
        Existing avatars are not overwritten.

        Args:
            synths: List of synth dictionaries (must have 'id' field)
            on_generation_start: Async callback when generation starts (receives count)
            on_generation_complete: Async callback when generation completes (receives count)

        Returns:
            Dict mapping synth_id to S3 object key for newly generated avatars.

        Note:
            - Avatars are generated in batches of 9 (OpenAI API optimization)
            - Synths without 'id' field are skipped
            - Avatar generation errors are logged but don't fail the operation
            - Avatars are stored in S3 at "avatars/{synth_id}.png"
        """
        # Check which synths need avatars (check S3 instead of local)
        synths_without_avatar = []
        for synth in synths:
            synth_id = synth.get("id")
            if not synth_id:
                continue

            s3_key = f"avatars/{synth_id}.png"
            if not check_object_exists(s3_key):
                synths_without_avatar.append(synth)

        if not synths_without_avatar:
            self.logger.debug("All synths already have avatars")
            return {}

        # Calculate batches (9 avatars per batch for OpenAI optimization)
        num_blocks = math.ceil(len(synths_without_avatar) / 9)
        count_to_generate = len(synths_without_avatar)

        self.logger.info(
            f"Generating avatars for {count_to_generate} synths "
            f"in {num_blocks} batch(es) of up to 9"
        )

        # Notify generation start
        if on_generation_start:
            await on_generation_start(count_to_generate)

        # Import avatar generator
        import asyncio

        from synth_lab.gen_synth.avatar_generator import generate_avatars

        generated_keys: dict[str, str] = {}

        try:
            # Run avatar generation in a separate thread to avoid blocking the event loop
            # generate_avatars uses time.sleep() and synchronous API calls
            s3_keys = await asyncio.to_thread(generate_avatars, synths=synths_without_avatar)
            self.logger.info(f"Successfully generated {len(s3_keys)} avatar files in S3")

            # Build result dict - keys are S3 object keys like "avatars/synth_001.png"
            for s3_key in s3_keys:
                # Extract synth_id from key (e.g., "avatars/synth_001.png" -> "synth_001")
                synth_id = s3_key.replace("avatars/", "").replace(".png", "")
                generated_keys[synth_id] = s3_key

            # Notify generation complete
            if on_generation_complete:
                await on_generation_complete(len(generated_keys))

        except Exception as e:
            # Log error but don't fail - avatars are helpful but not essential
            self.logger.warning(
                f"Error generating avatars (operation will continue): {e}"
            )

        return generated_keys

    def get_avatar_s3_key(self, synth_id: str) -> str | None:
        """
        Get S3 object key for a synth's avatar if it exists.

        Args:
            synth_id: Synth ID.

        Returns:
            S3 object key if avatar exists, None otherwise.
        """
        s3_key = f"avatars/{synth_id}.png"
        return s3_key if check_object_exists(s3_key) else None

    def get_avatar_url(self, synth_id: str, expires_in: int = 3600) -> str | None:
        """
        Get presigned URL for a synth's avatar.

        Args:
            synth_id: Synth ID.
            expires_in: URL expiration time in seconds (default: 1 hour).

        Returns:
            Presigned URL if avatar exists, None otherwise.
        """
        s3_key = f"avatars/{synth_id}.png"
        if check_object_exists(s3_key):
            return generate_view_url(s3_key, expires_in)
        return None

    def has_avatar(self, synth_id: str) -> bool:
        """
        Check if synth has an avatar in S3.

        Args:
            synth_id: Synth ID.

        Returns:
            True if avatar exists in S3.
        """
        s3_key = f"avatars/{synth_id}.png"
        return check_object_exists(s3_key)

    # Deprecated method kept for backwards compatibility
    def get_avatar_path(self, synth_id: str) -> Path | None:
        """
        DEPRECATED: Use get_avatar_url() instead.

        This method now checks S3 and returns a dummy path for backwards
        compatibility. Use get_avatar_url() for the actual S3 presigned URL.

        Args:
            synth_id: Synth ID.

        Returns:
            Path object with the S3 key if avatar exists, None otherwise.
        """
        s3_key = self.get_avatar_s3_key(synth_id)
        return Path(s3_key) if s3_key else None


if __name__ == "__main__":
    """
    Validation tests for AvatarService.

    Tests basic functionality without making actual API calls.
    """
    import asyncio
    import sys

    async def run_tests():
        all_validation_failures = []
        total_tests = 0

        # Test 1: Service initialization
        total_tests += 1
        try:
            service = AvatarService()
            assert service.avatars_dir == AVATARS_DIR
            print("✓ AvatarService: initializes with default avatars_dir")
        except Exception as e:
            all_validation_failures.append(f"Service init: {e}")

        # Test 2: Custom avatars_dir
        total_tests += 1
        try:
            custom_dir = Path("/tmp/test_avatars")
            service = AvatarService(avatars_dir=custom_dir)
            assert service.avatars_dir == custom_dir
            print("✓ AvatarService: accepts custom avatars_dir")
        except Exception as e:
            all_validation_failures.append(f"Custom dir: {e}")

        # Test 3: Empty synth list
        total_tests += 1
        try:
            service = AvatarService()
            result = await service.ensure_avatars_for_synths([])
            assert result == {}
            print("✓ ensure_avatars_for_synths: handles empty list")
        except Exception as e:
            all_validation_failures.append(f"Empty list: {e}")

        # Test 4: Synths without 'id' field
        total_tests += 1
        try:
            service = AvatarService()
            synths_no_id = [{"nome": "Test"}, {"nome": "Test2"}]
            result = await service.ensure_avatars_for_synths(synths_no_id)
            assert result == {}
            print("✓ ensure_avatars_for_synths: skips synths without id")
        except Exception as e:
            all_validation_failures.append(f"Synths without id: {e}")

        # Test 5: has_avatar for non-existent avatar
        total_tests += 1
        try:
            service = AvatarService()
            has_avatar = service.has_avatar("nonexistent_synth")
            assert has_avatar is False
            print("✓ has_avatar: returns False for non-existent avatar")
        except Exception as e:
            all_validation_failures.append(f"has_avatar (non-existent): {e}")

        # Test 6: get_avatar_path for non-existent avatar
        total_tests += 1
        try:
            service = AvatarService()
            path = service.get_avatar_path("nonexistent_synth")
            assert path is None
            print("✓ get_avatar_path: returns None for non-existent avatar")
        except Exception as e:
            all_validation_failures.append(f"get_avatar_path (non-existent): {e}")

        # Test 7: Check if existing avatars are detected
        total_tests += 1
        try:
            service = AvatarService()
            if AVATARS_DIR.exists():
                avatar_files = list(AVATARS_DIR.glob("*.png"))
                if avatar_files:
                    synth_id = avatar_files[0].stem
                    has_avatar = service.has_avatar(synth_id)
                    path = service.get_avatar_path(synth_id)
                    assert has_avatar is True
                    assert path == avatar_files[0]
                    print(f"✓ has_avatar/get_avatar_path: detects existing avatar ({synth_id})")
                else:
                    print("○ has_avatar/get_avatar_path: no existing avatars to test")
            else:
                print("○ has_avatar/get_avatar_path: avatars dir doesn't exist")
        except Exception as e:
            all_validation_failures.append(f"Existing avatars: {e}")

        # Return results
        return all_validation_failures, total_tests

    # Run async tests
    failures, tests = asyncio.run(run_tests())

    # Final validation result
    print()
    if failures:
        print(f"❌ VALIDATION FAILED - {len(failures)} of {tests} tests failed:")
        for failure in failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {tests} tests produced expected results")
        print("AvatarService is validated and ready for use")
        sys.exit(0)
