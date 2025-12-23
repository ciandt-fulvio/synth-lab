"""
Centralized LLM client for synth-lab.

Single source of truth for all OpenAI API operations with:
- Retry logic with exponential backoff
- Timeout handling
- Model selection
- Token usage tracking

References:
    - OpenAI Python SDK: https://github.com/openai/openai-python
    - Tenacity retry: https://tenacity.readthedocs.io/
"""

import base64
import os
from typing import Any

from loguru import logger
from openai import OpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from synth_lab.infrastructure.config import (
    DEFAULT_MODEL,
    LLM_MAX_RETRIES,
    LLM_TIMEOUT,
    OPENAI_API_KEY,
)
from synth_lab.infrastructure.phoenix_tracing import get_tracer

# Phoenix/OpenTelemetry tracer for observability
_tracer = get_tracer("llm-client")


class LLMClient:
    """Centralized LLM operations with retry logic and logging."""

    def __init__(
        self,
        api_key: str | None = None,
        default_model: str | None = None,
        default_timeout: float | None = None,
        max_retries: int | None = None,
    ):
        """
        Initialize LLM client.

        Args:
            api_key: OpenAI API key. Defaults to OPENAI_API_KEY env var.
            default_model: Default model for completions. Defaults to config.DEFAULT_MODEL.
            default_timeout: Request timeout in seconds. Defaults to config.LLM_TIMEOUT.
            max_retries: Maximum retry attempts. Defaults to config.LLM_MAX_RETRIES.
        """
        self.api_key = api_key or OPENAI_API_KEY
        self.default_model = default_model or DEFAULT_MODEL
        self.default_timeout = default_timeout or LLM_TIMEOUT
        self.max_retries = max_retries or LLM_MAX_RETRIES

        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set. LLM operations will fail.")

        self.client = OpenAI(
            api_key=self.api_key,
            timeout=self.default_timeout,
        )
        self.logger = logger.bind(component="llm_client")

        # Token usage tracking
        self._total_prompt_tokens = 0
        self._total_completion_tokens = 0

    def _create_retry_decorator(self) -> Any:
        """Create a retry decorator with current settings."""
        return retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type((Exception,)),
            before_sleep=lambda rs: self.logger.warning(
                f"LLM retry attempt {rs.attempt_number} after {rs.outcome.exception()}"
            ),
        )

    def complete(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 1.0,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate a chat completion with retry logic.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            model: Model to use. Defaults to default_model.
            temperature: Sampling temperature. Defaults to 1.0.
            max_tokens: Maximum tokens in response.
            **kwargs: Additional OpenAI API parameters.

        Returns:
            str: The completion text.

        Raises:
            Exception: If all retries fail.
        """
        model = model or self.default_model
        self.logger.debug(f"Completion request: model={model}, messages={len(messages)}")

        with _tracer.start_as_current_span(
            "llm_completion",
            attributes={
                "model": model,
                "message_count": len(messages),
                "temperature": temperature,
            },
        ) as span:
            @self._create_retry_decorator()
            def _call() -> str:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_completion_tokens=max_tokens,
                    **kwargs,
                )

                # Track token usage
                if response.usage:
                    self._total_prompt_tokens += response.usage.prompt_tokens
                    self._total_completion_tokens += response.usage.completion_tokens
                    if span:
                        span.set_attribute("prompt_tokens", response.usage.prompt_tokens)
                        span.set_attribute("completion_tokens", response.usage.completion_tokens)

                content = response.choices[0].message.content
                self.logger.debug(f"Completion response: {len(content or '')} chars")
                if span:
                    span.set_attribute("response_length", len(content or ""))
                return content or ""

            return _call()

    def complete_json(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 1.0,
        **kwargs: Any,
    ) -> str:
        """
        Generate a JSON completion with retry logic.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            model: Model to use. Defaults to default_model.
            temperature: Sampling temperature. Defaults to 1.0.
            **kwargs: Additional OpenAI API parameters.

        Returns:
            str: The JSON completion text.
        """
        return self.complete(
            messages=messages,
            model=model,
            temperature=temperature,
            response_format={"type": "json_object"},
            **kwargs,
        )

    def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "hd",
        model: str = "dall-e-3",
    ) -> bytes:
        """
        Generate an image with retry logic.

        Args:
            prompt: Image generation prompt.
            size: Image size. Defaults to "1024x1024".
            quality: Image quality. Defaults to "hd".
            model: Image model. Defaults to "dall-e-3".

        Returns:
            bytes: Image data as bytes.

        Raises:
            Exception: If all retries fail.
        """
        self.logger.debug(f"Image generation: prompt={prompt[:50]}...")

        with _tracer.start_as_current_span(
            "llm_image_generation",
            attributes={
                "model": model,
                "size": size,
                "quality": quality,
                "prompt_preview": prompt[:100],
            },
        ) as span:
            @retry(
                stop=stop_after_attempt(self.max_retries),
                wait=wait_exponential(multiplier=2, min=2, max=30),
                retry=retry_if_exception_type((Exception,)),
                before_sleep=lambda rs: self.logger.warning(
                    f"Image generation retry {rs.attempt_number}"
                ),
            )
            def _call() -> bytes:
                response = self.client.images.generate(
                    model=model,
                    prompt=prompt,
                    size=size,
                    quality=quality,
                    n=1,
                    response_format="b64_json",
                )
                image_data = base64.b64decode(response.data[0].b64_json)
                self.logger.debug(f"Image generated: {len(image_data)} bytes")
                if span:
                    span.set_attribute("image_bytes", len(image_data))
                return image_data

            return _call()

    @property
    def total_tokens(self) -> dict[str, int]:
        """Get total token usage statistics."""
        return {
            "prompt_tokens": self._total_prompt_tokens,
            "completion_tokens": self._total_completion_tokens,
            "total_tokens": self._total_prompt_tokens + self._total_completion_tokens,
        }

    def reset_token_tracking(self) -> None:
        """Reset token usage counters."""
        self._total_prompt_tokens = 0
        self._total_completion_tokens = 0


# Global LLM client instance
_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """
    Get or create the global LLM client.

    Returns:
        LLMClient: Global LLM client instance.
    """
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


if __name__ == "__main__":
    import sys

    # Validation (without making actual API calls)
    all_validation_failures = []
    total_tests = 0

    # Test 1: Client instantiation - API key from env or None
    total_tests += 1
    try:
        # The client should use OPENAI_API_KEY if available, otherwise None
        original_key = os.environ.get("OPENAI_API_KEY")
        client = LLMClient()  # Use default (from env)
        expected_key = original_key  # Should match env
        if client.api_key != expected_key:
            all_validation_failures.append(
                f"Client api_key should be from env, got {client.api_key is not None}"
            )
    except Exception as e:
        all_validation_failures.append(f"Client instantiation failed: {e}")

    # Test 2: Client instantiation with API key
    total_tests += 1
    try:
        client = LLMClient(api_key="test-key")
        if client.api_key != "test-key":
            all_validation_failures.append(f"API key not set correctly: {client.api_key}")
    except Exception as e:
        all_validation_failures.append(f"Client with key failed: {e}")

    # Test 3: Default model
    total_tests += 1
    try:
        client = LLMClient(api_key="test-key")
        if client.default_model != DEFAULT_MODEL:
            all_validation_failures.append(
                f"Default model mismatch: {client.default_model} != {DEFAULT_MODEL}"
            )
    except Exception as e:
        all_validation_failures.append(f"Default model test failed: {e}")

    # Test 4: Custom model
    total_tests += 1
    try:
        client = LLMClient(api_key="test-key", default_model="gpt-4")
        if client.default_model != "gpt-4":
            all_validation_failures.append(f"Custom model not set: {client.default_model}")
    except Exception as e:
        all_validation_failures.append(f"Custom model test failed: {e}")

    # Test 5: Token tracking
    total_tests += 1
    try:
        client = LLMClient(api_key="test-key")
        tokens = client.total_tokens
        if tokens["total_tokens"] != 0:
            all_validation_failures.append(f"Initial token count not zero: {tokens}")
        client._total_prompt_tokens = 100
        client._total_completion_tokens = 50
        tokens = client.total_tokens
        if tokens["total_tokens"] != 150:
            all_validation_failures.append(f"Token count mismatch: {tokens}")
        client.reset_token_tracking()
        if client.total_tokens["total_tokens"] != 0:
            all_validation_failures.append("Token reset failed")
    except Exception as e:
        all_validation_failures.append(f"Token tracking test failed: {e}")

    # Test 6: get_llm_client singleton
    total_tests += 1
    try:
        # Reset global instance via module globals
        import synth_lab.infrastructure.llm_client as llm_module

        llm_module._llm_client = None

        os.environ["OPENAI_API_KEY"] = "test-singleton-key"
        client1 = get_llm_client()
        client2 = get_llm_client()
        if client1 is not client2:
            all_validation_failures.append("get_llm_client not returning singleton")
    except Exception as e:
        all_validation_failures.append(f"Singleton test failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
