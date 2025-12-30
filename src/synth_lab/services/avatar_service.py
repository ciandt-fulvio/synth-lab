"""
Avatar generation service for synth-lab.

Ensures synths have avatars generated before interviews or other operations.

References:
    - Avatar Generator: synth_lab.gen_synth.avatar_generator
    - Config: synth_lab.infrastructure.config.AVATARS_DIR

Sample Input:
    synth_ids = ["synth_001", "synth_002", "synth_003"]

Expected Output:
    Avatars generated for synths without existing avatar files.
    Returns dict of {synth_id: avatar_path} for generated avatars.
"""

import math
from pathlib import Path
from typing import Any, Awaitable, Callable

from loguru import logger

from synth_lab.infrastructure.config import AVATARS_DIR


class AvatarService:
    """Service for ensuring synths have avatar images."""

    def __init__(self, avatars_dir: Path | None = None):
        """
        Initialize avatar service.

        Args:
            avatars_dir: Directory for avatar files (default: AVATARS_DIR from config)
        """
        self.avatars_dir = avatars_dir or AVATARS_DIR
        self.logger = logger.bind(component="avatar_service")

    async def ensure_avatars_for_synths(
        self,
        synths: list[dict[str, Any]],
        on_generation_start: Callable[[int], Awaitable[None]] | None = None,
        on_generation_complete: Callable[[int], Awaitable[None]] | None = None,
    ) -> dict[str, Path]:
        """
        Ensure all synths have avatars generated.

        Checks which synths are missing avatar files and generates them automatically.
        Existing avatars are not overwritten.

        Args:
            synths: List of synth dictionaries (must have 'id' field)
            on_generation_start: Async callback when generation starts (receives count)
            on_generation_complete: Async callback when generation completes (receives count)

        Returns:
            Dict mapping synth_id to avatar file path for newly generated avatars.

        Note:
            - Avatars are generated in batches of 9 (OpenAI API optimization)
            - Synths without 'id' field are skipped
            - Avatar generation errors are logged but don't fail the operation
        """
        # Ensure avatar directory exists
        self.avatars_dir.mkdir(parents=True, exist_ok=True)

        # Check which synths need avatars
        synths_without_avatar = []
        for synth in synths:
            synth_id = synth.get("id")
            if not synth_id:
                continue

            avatar_file = self.avatars_dir / f"{synth_id}.png"
            if not avatar_file.exists():
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

        generated_paths: dict[str, Path] = {}

        try:
            # Run avatar generation in a separate thread to avoid blocking the event loop
            # generate_avatars uses time.sleep() and synchronous API calls
            paths = await asyncio.to_thread(generate_avatars, synths=synths_without_avatar)
            self.logger.info(f"Successfully generated {len(paths)} avatar files")

            # Build result dict
            for path in paths:
                synth_id = path.stem  # filename without extension
                generated_paths[synth_id] = path

            # Notify generation complete
            if on_generation_complete:
                await on_generation_complete(len(generated_paths))

        except Exception as e:
            # Log error but don't fail - avatars are helpful but not essential
            self.logger.warning(
                f"Error generating avatars (operation will continue): {e}"
            )

        return generated_paths

    def get_avatar_path(self, synth_id: str) -> Path | None:
        """
        Get avatar file path for a synth.

        Args:
            synth_id: Synth ID.

        Returns:
            Path to avatar file if it exists, None otherwise.
        """
        avatar_file = self.avatars_dir / f"{synth_id}.png"
        return avatar_file if avatar_file.exists() else None

    def has_avatar(self, synth_id: str) -> bool:
        """
        Check if synth has an avatar file.

        Args:
            synth_id: Synth ID.

        Returns:
            True if avatar file exists.
        """
        return self.get_avatar_path(synth_id) is not None


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
