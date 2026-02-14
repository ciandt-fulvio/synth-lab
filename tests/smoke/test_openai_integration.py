"""
Smoke tests for real OpenAI API integration.

These tests make REAL API calls to verify:
1. OpenAI API key is valid
2. Basic connectivity works
3. Critical endpoints are accessible

⚠️  IMPORTANT:
- These tests incur API costs (~$0.001 per run)
- Only run in CI or when explicitly requested
- Skip automatically if OPENAI_API_KEY not configured

Run with: pytest -m "slow and real_api" tests/smoke/test_openai_integration.py

Cost breakdown:
- test_openai_hello_world: ~$0.0001 (5 tokens with gpt-4o-mini)
- test_openai_avatar_generation: ~$0.02 (1 DALL-E image)
Total: ~$0.02 per run
"""

import os
from io import BytesIO

import pytest


@pytest.mark.slow
@pytest.mark.real_api
@pytest.mark.smoke
class TestOpenAISmoke:
    """Smoke tests for OpenAI API integration (REAL API CALLS)."""

    def test_openai_hello_world(self):
        """
        Minimal smoke test: verify OpenAI API key works with 'hello world'.

        Cost: ~$0.0001 (5 tokens with gpt-4o-mini)
        Time: ~1-2 seconds

        This is the ONLY test that should make a real LLM text completion call.
        All other tests should use mocks.
        """
        # Check if API key is configured
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not configured - skipping real API test")

        from openai import OpenAI

        # Create client
        client = OpenAI(api_key=api_key)

        # Make minimal API call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5,  # Minimal response to reduce cost
        )

        # Verify response structure
        assert response is not None
        assert response.choices is not None
        assert len(response.choices) > 0
        assert response.choices[0].message is not None
        assert response.choices[0].message.content is not None
        assert isinstance(response.choices[0].message.content, str)
        assert len(response.choices[0].message.content) > 0

        # Verify model responded
        assert response.model.startswith("gpt-4o-mini")

        print(f"✅ OpenAI API is working. Response: '{response.choices[0].message.content}'")

    def test_openai_avatar_generation_smoke(self):
        """
        Smoke test for OpenAI DALL-E image generation.

        Cost: ~$0.016 (1 DALL-E 2 256x256 image - 4x cheaper than DALL-E 3)
        Time: ~2-3 seconds (3x faster than DALL-E 3)

        Tests:
        1. DALL-E API is accessible
        2. Image generation works
        3. Returns valid image URL
        4. Image can be downloaded

        Note: Uses DALL-E 2 for speed and cost. DALL-E 3 is tested separately if needed.
        """
        # Check if API key is configured
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not configured - skipping real API test")

        from openai import OpenAI

        # Create client
        client = OpenAI(api_key=api_key)

        # Make minimal DALL-E call using DALL-E 2 (faster and cheaper)
        response = client.images.generate(
            model="dall-e-2",  # DALL-E 2 is 4x cheaper and 3x faster
            prompt="white square",  # Minimal prompt (faster processing)
            size="256x256",  # Smallest size for speed
            n=1,  # Just 1 image
        )

        # Verify response structure
        assert response is not None
        assert response.data is not None
        assert len(response.data) > 0
        assert response.data[0].url is not None

        # Verify image URL is valid
        image_url = response.data[0].url
        assert isinstance(image_url, str)
        assert image_url.startswith("https://")

        # Try to download image (verify URL works)
        import requests

        img_response = requests.get(image_url, timeout=10)
        assert img_response.status_code == 200
        assert img_response.headers["Content-Type"].startswith("image/")
        assert len(img_response.content) > 0

        # Verify it's a valid PNG image
        from PIL import Image

        img = Image.open(BytesIO(img_response.content))
        assert img.format == "PNG"
        assert img.width == 256  # DALL-E 2 256x256
        assert img.height == 256

        print(f"✅ DALL-E API is working (DALL-E 2, 256x256). Image URL: {image_url[:50]}...")


@pytest.mark.slow
@pytest.mark.real_api
@pytest.mark.smoke
class TestRealAvatarGenerationE2E:
    """
    End-to-end smoke test for avatar generation with real APIs.

    This test uses REAL:
    - OpenAI DALL-E API
    - S3 storage
    - Database

    ⚠️  Cost: ~$0.02 per run
    ⚠️  Time: ~10-15 seconds
    ⚠️  Requires: OPENAI_API_KEY, DATABASE_URL, S3_ENDPOINT_URL

    Run only in CI or when explicitly testing production readiness.
    """

    def test_real_avatar_generation_single_synth(self):
        """
        E2E test: Generate 1 real avatar through complete pipeline.

        Tests:
        1. Synth validation
        2. OpenAI DALL-E call (real)
        3. Image download
        4. Image processing (resize)
        5. S3 upload (real)
        6. Returns S3 key

        Cost: ~$0.02 (1 DALL-E image)
        Time: ~10 seconds
        """
        import shutil
        import tempfile

        # Check if all required configs are present
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not configured - skipping real API test")

        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            pytest.skip("DATABASE_URL not configured - skipping real API test")

        s3_endpoint = os.environ.get("S3_ENDPOINT_URL")
        if not s3_endpoint:
            pytest.skip("S3_ENDPOINT_URL not configured - skipping real API test")

        from pathlib import Path

        from synth_lab.gen_synth.avatar_generator import generate_avatars
        from synth_lab.infrastructure.storage_client import check_object_exists, get_object_bytes

        # Create minimal synth (just 1 to reduce cost)
        test_synth = [
            {
                "id": "smoke01",
                "demografia": {
                    "idade": 30,
                    "genero_biologico": "masculino",
                    "raca_etnia": "branco",
                    "ocupacao": "engenheiro",
                },
            }
        ]

        # Create temp directory
        temp_dir = Path(tempfile.mkdtemp())

        try:
            # Generate avatar (REAL API CALL)
            result = generate_avatars(
                test_synth, blocks=None, avatar_dir=temp_dir, api_key=api_key
            )

            # Verify result
            assert len(result) == 1, f"Expected 1 avatar, got {len(result)}"
            s3_key = result[0]
            assert s3_key.startswith("avatars/"), f"Invalid S3 key format: {s3_key}"

            # Verify avatar exists in S3
            assert check_object_exists(s3_key), f"Avatar not found in S3: {s3_key}"

            # Verify avatar is valid PNG with correct dimensions
            avatar_bytes = get_object_bytes(s3_key)
            assert avatar_bytes is not None, f"Could not download avatar: {s3_key}"

            from PIL import Image

            img = Image.open(BytesIO(avatar_bytes))
            assert img.width == 200 and img.height == 200, (
                f"Incorrect dimensions: {img.size}, expected (200, 200)"
            )

            print(f"✅ Real avatar generation working. S3 key: {s3_key}")

        finally:
            # Cleanup temp directory
            shutil.rmtree(temp_dir)
