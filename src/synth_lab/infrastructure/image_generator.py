"""
Image generation client for synth-lab.

Centralized image generation using OpenAI's image models with:
- Configurable model (default: gpt-image-1.5)
- Retry logic with exponential backoff
- Timeout handling
- Base64 output
- Phoenix/OpenTelemetry tracing

Sample Input:
    prompt = "A futuristic city at sunset with flying cars"
    generator = ImageGenerator()
    base64_image = generator.generate(prompt)

Expected Output:
    Base64-encoded string of the generated image

References:
    - OpenAI Images API: https://platform.openai.com/docs/guides/images
    - Tenacity retry: https://tenacity.readthedocs.io/
"""

import base64
from typing import Literal

from loguru import logger
from openai import OpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from synth_lab.infrastructure.config import LLM_MAX_RETRIES, LLM_TIMEOUT, OPENAI_API_KEY
from synth_lab.infrastructure.phoenix_tracing import get_tracer

# Phoenix/OpenTelemetry tracer for observability
_tracer = get_tracer("image-generator")

# Type definitions for image parameters (gpt-image-1.5 specific)
ImageSize = Literal["1024x1024", "1024x1536", "1536x1024", "auto"]
ImageQuality = Literal["auto", "hd"]
OutputFormat = Literal["png", "jpeg", "webp"]


class ImageGenerator:
    """Centralized image generation operations with retry logic and logging."""

    def __init__(
        self,
        api_key: str | None = None,
        default_model: str = "gpt-image-1.5",
        default_timeout: float | None = None,
        max_retries: int | None = None,
    ):
        """
        Initialize image generator client.

        Args:
            api_key: OpenAI API key. Defaults to OPENAI_API_KEY env var.
            default_model: Default model for image generation. Defaults to "gpt-image-1.5".
            default_timeout: Request timeout in seconds. Defaults to config.LLM_TIMEOUT.
            max_retries: Maximum retry attempts. Defaults to config.LLM_MAX_RETRIES.
        """
        self.api_key = api_key or OPENAI_API_KEY
        self.default_model = default_model
        self.default_timeout = default_timeout or LLM_TIMEOUT
        self.max_retries = max_retries or LLM_MAX_RETRIES

        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set. Image generation will fail.")

        self.client = OpenAI(
            api_key=self.api_key,
            timeout=self.default_timeout,
        )
        self.logger = logger.bind(component="image_generator")

    def generate(
        self,
        prompt: str,
        model: str | None = None,
        n: int = 1,
        size: ImageSize = "1536x1024",
        quality: ImageQuality = "auto",
        output_format: OutputFormat = "png",
    ) -> str:
        """
        Generate an image from a text prompt.

        Args:
            prompt: Text description of the image to generate (required).
            model: Image model to use. Defaults to "gpt-image-1.5".
            n: Number of images to generate. Defaults to 1.
            size: Image dimensions. Defaults to "1536x1024".
            quality: Image quality ("auto" or "hd"). Defaults to "auto".
            output_format: Image format ("png", "jpeg", "webp"). Defaults to "png".

        Returns:
            str: Base64-encoded image string.

        Raises:
            Exception: If all retries fail.
            ValueError: If prompt is empty or invalid parameters.

        Example:
            >>> generator = ImageGenerator()
            >>> base64_img = generator.generate("A sunset over mountains")
            >>> # base64_img can be used in HTML: <img src="data:image/png;base64,{base64_img}">
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        if n < 1 or n > 10:
            raise ValueError("n must be between 1 and 10")

        model = model or self.default_model
        prompt_preview = prompt[:100]

        self.logger.debug(
            f"Image generation request: model={model}, size={size}, quality={quality}, "
            f"output_format={output_format}, prompt={prompt[:50]}..."
        )

        span_name = "Image Generation"
        with _tracer.start_as_current_span(
            span_name,
            attributes={
                "openinference.span.kind": "LLM",
                "operation_type": "image_generation",
                "model": model,
                "size": size,
                "quality": quality,
                "output_format": output_format,
                "n": n,
                "prompt_length": len(prompt),
                "prompt_preview": prompt_preview,
                "input.value": prompt_preview,
                "llm.model_name": model,
            },
        ) as span:

            @retry(
                stop=stop_after_attempt(self.max_retries),
                wait=wait_exponential(multiplier=2, min=2, max=30),
                retry=retry_if_exception_type((Exception,)),
                before_sleep=lambda rs: self.logger.warning(
                    f"Image gen retry {rs.attempt_number}: {rs.outcome.exception()}"
                ),
            )
            def _call() -> str:
                response = self.client.images.generate(
                    model=model,
                    prompt=prompt,
                    n=n,
                    size=size,
                    quality=quality,
                    output_format=output_format,
                )

                # Get the base64 string from the response (gpt-image-1.5 always returns b64_json)
                base64_image = response.data[0].b64_json
                if not base64_image:
                    raise ValueError("No image data returned from API")

                self.logger.debug(f"Image generated: {len(base64_image)} chars (base64)")
                if span:
                    span.set_attribute("base64_length", len(base64_image))
                    span.set_attribute("output.value", f"base64 image ({len(base64_image)} chars)")
                    span.set_attribute("success", True)

                return base64_image

            return _call()

    def generate_bytes(
        self,
        prompt: str,
        model: str | None = None,
        n: int = 1,
        size: ImageSize = "1536x1024",
        quality: ImageQuality = "auto",
        output_format: OutputFormat = "png",
    ) -> bytes:
        """
        Generate an image and return it as bytes (decoded from base64).

        Args:
            prompt: Text description of the image to generate (required).
            model: Image model to use. Defaults to "gpt-image-1.5".
            n: Number of images to generate. Defaults to 1.
            size: Image dimensions. Defaults to "1536x1024".
            quality: Image quality ("auto" or "hd"). Defaults to "auto".
            output_format: Image format ("png", "jpeg", "webp"). Defaults to "png".

        Returns:
            bytes: Decoded image data as bytes.

        Example:
            >>> generator = ImageGenerator()
            >>> image_bytes = generator.generate_bytes("A forest landscape")
            >>> with open("output.png", "wb") as f:
            ...     f.write(image_bytes)
        """
        base64_string = self.generate(
            prompt=prompt,
            model=model,
            n=n,
            size=size,
            quality=quality,
            output_format=output_format,
        )
        return base64.b64decode(base64_string)


# Global image generator instance
_image_generator: ImageGenerator | None = None


def get_image_generator() -> ImageGenerator:
    """
    Get or create the global image generator.

    Returns:
        ImageGenerator: Global image generator instance.
    """
    global _image_generator
    if _image_generator is None:
        _image_generator = ImageGenerator()
    return _image_generator


if __name__ == "__main__":
    import os
    import sys

    # List to track all validation failures
    all_validation_failures = []
    total_tests = 0

    # Test 1: Generator instantiation - API key from env
    total_tests += 1
    try:
        original_key = os.environ.get("OPENAI_API_KEY")
        generator = ImageGenerator()
        expected_key = original_key
        if generator.api_key != expected_key:
            all_validation_failures.append(
                f"Generator api_key should be from env, got {generator.api_key is not None}"
            )
    except Exception as e:
        all_validation_failures.append(f"Generator instantiation failed: {e}")

    # Test 2: Generator with custom API key
    total_tests += 1
    try:
        generator = ImageGenerator(api_key="test-key-12345")
        if generator.api_key != "test-key-12345":
            all_validation_failures.append(f"API key not set correctly: {generator.api_key}")
    except Exception as e:
        all_validation_failures.append(f"Generator with custom key failed: {e}")

    # Test 3: Default model
    total_tests += 1
    try:
        generator = ImageGenerator(api_key="test-key")
        expected_model = "gpt-image-1.5"
        if generator.default_model != expected_model:
            all_validation_failures.append(
                f"Default model mismatch: {generator.default_model} != {expected_model}"
            )
    except Exception as e:
        all_validation_failures.append(f"Default model test failed: {e}")

    # Test 4: Custom model
    total_tests += 1
    try:
        generator = ImageGenerator(api_key="test-key", default_model="dall-e-3")
        expected_model = "dall-e-3"
        if generator.default_model != expected_model:
            all_validation_failures.append(
                f"Custom model not set: {generator.default_model} != {expected_model}"
            )
    except Exception as e:
        all_validation_failures.append(f"Custom model test failed: {e}")

    # Test 5: Empty prompt validation
    total_tests += 1
    try:
        generator = ImageGenerator(api_key="test-key")
        generator.generate("")  # Should raise ValueError
        all_validation_failures.append("Empty prompt should raise ValueError")
    except ValueError:
        # This is expected - test passes
        pass
    except Exception as e:
        all_validation_failures.append(f"Empty prompt raised wrong exception: {type(e).__name__}")

    # Test 6: Invalid n parameter
    total_tests += 1
    try:
        generator = ImageGenerator(api_key="test-key")
        generator.generate("test prompt", n=0)  # Should raise ValueError
        all_validation_failures.append("Invalid n=0 should raise ValueError")
    except ValueError:
        # This is expected - test passes
        pass
    except Exception as e:
        all_validation_failures.append(f"Invalid n test raised wrong exception: {type(e).__name__}")

    # Test 7: Invalid n parameter (too high)
    total_tests += 1
    try:
        generator = ImageGenerator(api_key="test-key")
        generator.generate("test prompt", n=11)  # Should raise ValueError
        all_validation_failures.append("Invalid n=11 should raise ValueError")
    except ValueError:
        # This is expected - test passes
        pass
    except Exception as e:
        all_validation_failures.append(
            f"Invalid n (high) raised wrong exception: {type(e).__name__}"
        )

    # Test 8: get_image_generator singleton
    total_tests += 1
    try:
        # Reset global instance
        import synth_lab.infrastructure.image_generator as img_module

        img_module._image_generator = None

        os.environ["OPENAI_API_KEY"] = "test-singleton-key"
        gen1 = get_image_generator()
        gen2 = get_image_generator()
        if gen1 is not gen2:
            all_validation_failures.append("get_image_generator not returning singleton")
    except Exception as e:
        all_validation_failures.append(f"Singleton test failed: {e}")

    # Test 9: Real API call (only if OPENAI_API_KEY is set)
    total_tests += 1
    if original_key and original_key.startswith("sk-"):
        try:
            generator = ImageGenerator()
            test_prompt = "A simple geometric shape: a blue circle"
            base64_result = generator.generate(test_prompt, size="1024x1024")

            # Verify it's a valid base64 string
            if not base64_result or len(base64_result) < 100:
                result_len = len(base64_result) if base64_result else 0
                all_validation_failures.append(
                    f"Real API returned invalid base64 (length: {result_len})"
                )

            # Try to decode it
            try:
                decoded = base64.b64decode(base64_result)
                if len(decoded) < 100:
                    all_validation_failures.append(
                        f"Decoded image too small (length: {len(decoded)})"
                    )
            except Exception as decode_err:
                all_validation_failures.append(f"Failed to decode base64: {decode_err}")

        except Exception as e:
            all_validation_failures.append(f"Real API call failed: {e}")
    else:
        # Skip real API test if no valid key
        all_validation_failures.append(
            "Skipped real API test: OPENAI_API_KEY not set or invalid (set a valid key to test)"
        )

    # Test 10: generate_bytes method
    total_tests += 1
    if original_key and original_key.startswith("sk-"):
        try:
            generator = ImageGenerator()
            test_prompt = "A red square on white background"
            image_bytes = generator.generate_bytes(test_prompt, size="1024x1024")

            # Verify it's bytes and not empty
            if not isinstance(image_bytes, bytes):
                all_validation_failures.append(
                    f"generate_bytes should return bytes, got {type(image_bytes)}"
                )
            elif len(image_bytes) < 100:
                all_validation_failures.append(
                    f"generate_bytes returned too few bytes: {len(image_bytes)}"
                )

        except Exception as e:
            all_validation_failures.append(f"generate_bytes test failed: {e}")
    else:
        all_validation_failures.append(
            "Skipped generate_bytes test: OPENAI_API_KEY not set or invalid"
        )

    # Final validation result
    if all_validation_failures:
        failed = len(all_validation_failures)
        print(f"❌ VALIDATION FAILED - {failed} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Function is validated and formal tests can now be written")
        sys.exit(0)
