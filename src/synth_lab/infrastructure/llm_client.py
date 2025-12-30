"""
Centralized LLM client for synth-lab.

Single source of truth for all OpenAI API operations with:
- Retry logic with exponential backoff
- Timeout handling
- Model selection
- Token usage tracking
- Model capability detection (reasoning_effort, max_tokens params)

References:
    - OpenAI Python SDK: https://github.com/openai/openai-python
    - Tenacity retry: https://tenacity.readthedocs.io/
"""

import base64
import os
from typing import Any

from loguru import logger


# =============================================================================
# Model Capability Detection
# =============================================================================

def supports_reasoning_effort(model: str) -> bool:
    """
    Check if a model supports the reasoning_effort parameter.

    Args:
        model: Model name/identifier (e.g., "gpt-5", "gpt-4.1-mini")

    Returns:
        True if model supports reasoning_effort, False otherwise.

    Note:
        - gpt-5.x models: support reasoning_effort (optional)
        - gpt-4.x models: do NOT support reasoning_effort
        - o1/o3 models: support reasoning_effort
    """
    model_lower = model.lower()
    # gpt-5.x and o1/o3 models support reasoning_effort
    if model_lower.startswith("gpt-5") or model_lower.startswith("o1") or model_lower.startswith("o3"):
        return True
    # gpt-4.x and other models do not support reasoning_effort
    return False


def get_max_tokens_param_name(model: str) -> str:
    """
    Get the correct parameter name for max tokens based on model.

    Args:
        model: Model name/identifier (e.g., "gpt-5", "gpt-4.1-mini")

    Returns:
        "max_completion_tokens" for gpt-5.x models, "max_tokens" for others.

    Note:
        - gpt-5.x models: use max_completion_tokens
        - gpt-4.x models: use max_tokens
        - o1/o3 models: use max_completion_tokens
    """
    model_lower = model.lower()
    if model_lower.startswith("gpt-5") or model_lower.startswith("o1") or model_lower.startswith("o3"):
        return "max_completion_tokens"
    return "max_tokens"


def normalize_api_params(model: str, **kwargs: Any) -> dict[str, Any]:
    """
    Normalize API parameters based on model capabilities.

    This function ensures parameters are compatible with the specified model:
    - Removes reasoning_effort for models that don't support it
    - Converts max_tokens to max_completion_tokens for gpt-5.x models
    - Converts max_completion_tokens to max_tokens for gpt-4.x models

    Args:
        model: Model name/identifier
        **kwargs: API parameters to normalize

    Returns:
        Normalized parameters dict compatible with the model.

    Example:
        >>> normalize_api_params("gpt-4.1-mini", reasoning_effort="low", max_tokens=1000)
        {'max_tokens': 1000}  # reasoning_effort removed

        >>> normalize_api_params("gpt-5", max_tokens=1000)
        {'max_completion_tokens': 1000}  # renamed for gpt-5
    """
    normalized = dict(kwargs)

    # Handle reasoning_effort
    if "reasoning_effort" in normalized:
        if not supports_reasoning_effort(model):
            logger.debug(
                f"Removing unsupported 'reasoning_effort' param for model {model}"
            )
            del normalized["reasoning_effort"]

    # Handle max tokens parameter name
    max_tokens_param = get_max_tokens_param_name(model)

    if max_tokens_param == "max_completion_tokens":
        # Convert max_tokens to max_completion_tokens for gpt-5.x
        if "max_tokens" in normalized and "max_completion_tokens" not in normalized:
            normalized["max_completion_tokens"] = normalized.pop("max_tokens")
            logger.debug(
                f"Converted 'max_tokens' to 'max_completion_tokens' for model {model}"
            )
    else:
        # Convert max_completion_tokens to max_tokens for gpt-4.x
        if "max_completion_tokens" in normalized and "max_tokens" not in normalized:
            normalized["max_tokens"] = normalized.pop("max_completion_tokens")
            logger.debug(
                f"Converted 'max_completion_tokens' to 'max_tokens' for model {model}"
            )

    return normalized


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
        operation_name: str | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate a chat completion with retry logic.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            model: Model to use. Defaults to default_model.
            temperature: Sampling temperature. Defaults to 1.0.
            max_tokens: Maximum tokens in response.
            operation_name: Custom name for tracing span. Defaults to "LLM Completion: {model}".
            **kwargs: Additional OpenAI API parameters.

        Returns:
            str: The completion text.

        Raises:
            Exception: If all retries fail.
        """
        model = model or self.default_model
        self.logger.debug(f"Completion request: model={model}, messages={len(messages)}")

        span_name = operation_name or f"LLM Completion: {model}"
        with _tracer.start_as_current_span(
            span_name,
            attributes={
                "openinference.span.kind": "LLM",
                "model": model,
                "message_count": len(messages),
                "temperature": temperature,
            },
        ) as span:

            @self._create_retry_decorator()
            def _call() -> str:
                # Build kwargs for API call
                api_kwargs = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    **kwargs,
                }
                # Only add max_tokens if specified
                if max_tokens:
                    api_kwargs["max_tokens"] = max_tokens

                response = self.client.chat.completions.create(**api_kwargs)

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

    def complete_stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 1.0,
        max_tokens: int | None = None,
        operation_name: str | None = None,
        **kwargs: Any,
    ):
        """
        Generate a streaming chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            model: Model to use. Defaults to default_model.
            temperature: Sampling temperature. Defaults to 1.0.
            max_tokens: Maximum tokens in response.
            operation_name: Custom name for tracing span. Defaults to "LLM Stream: {model}".
            **kwargs: Additional OpenAI API parameters.

        Yields:
            str: Chunks of the completion text.
        """
        model = model or self.default_model
        self.logger.debug(f"Streaming completion request: model={model}, messages={len(messages)}")

        # Build kwargs for API call
        api_kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
            **kwargs,
        }
        # Only add max_tokens if specified
        if max_tokens:
            api_kwargs["max_tokens"] = max_tokens

        span_name = operation_name or f"LLM Stream: {model}"
        with _tracer.start_as_current_span(
            span_name,
            attributes={
                "openinference.span.kind": "LLM",
                "model": model,
                "message_count": len(messages),
                "temperature": temperature,
            },
        ):
            response = self.client.chat.completions.create(**api_kwargs)

            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

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
            f"LLM Image: {model}",
            attributes={
                "openinference.span.kind": "LLM",
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

    # Test 7: supports_reasoning_effort - gpt-5 models
    total_tests += 1
    try:
        if not supports_reasoning_effort("gpt-5"):
            all_validation_failures.append("gpt-5 should support reasoning_effort")
        if not supports_reasoning_effort("gpt-5-turbo"):
            all_validation_failures.append("gpt-5-turbo should support reasoning_effort")
        if not supports_reasoning_effort("GPT-5"):
            all_validation_failures.append("GPT-5 (uppercase) should support reasoning_effort")
    except Exception as e:
        all_validation_failures.append(f"supports_reasoning_effort gpt-5 test failed: {e}")

    # Test 8: supports_reasoning_effort - gpt-4 models (should NOT support)
    total_tests += 1
    try:
        if supports_reasoning_effort("gpt-4"):
            all_validation_failures.append("gpt-4 should NOT support reasoning_effort")
        if supports_reasoning_effort("gpt-4.1-mini"):
            all_validation_failures.append("gpt-4.1-mini should NOT support reasoning_effort")
        if supports_reasoning_effort("gpt-4o"):
            all_validation_failures.append("gpt-4o should NOT support reasoning_effort")
    except Exception as e:
        all_validation_failures.append(f"supports_reasoning_effort gpt-4 test failed: {e}")

    # Test 9: supports_reasoning_effort - o1/o3 models
    total_tests += 1
    try:
        if not supports_reasoning_effort("o1"):
            all_validation_failures.append("o1 should support reasoning_effort")
        if not supports_reasoning_effort("o1-preview"):
            all_validation_failures.append("o1-preview should support reasoning_effort")
        if not supports_reasoning_effort("o3"):
            all_validation_failures.append("o3 should support reasoning_effort")
    except Exception as e:
        all_validation_failures.append(f"supports_reasoning_effort o1/o3 test failed: {e}")

    # Test 10: get_max_tokens_param_name
    total_tests += 1
    try:
        if get_max_tokens_param_name("gpt-4.1-mini") != "max_tokens":
            all_validation_failures.append("gpt-4.1-mini should use max_tokens")
        if get_max_tokens_param_name("gpt-5") != "max_completion_tokens":
            all_validation_failures.append("gpt-5 should use max_completion_tokens")
        if get_max_tokens_param_name("o1") != "max_completion_tokens":
            all_validation_failures.append("o1 should use max_completion_tokens")
    except Exception as e:
        all_validation_failures.append(f"get_max_tokens_param_name test failed: {e}")

    # Test 11: normalize_api_params - remove reasoning_effort for gpt-4
    total_tests += 1
    try:
        params = normalize_api_params("gpt-4.1-mini", reasoning_effort="low", max_tokens=1000)
        if "reasoning_effort" in params:
            all_validation_failures.append("reasoning_effort should be removed for gpt-4.1-mini")
        if params.get("max_tokens") != 1000:
            all_validation_failures.append("max_tokens should be preserved for gpt-4.1-mini")
    except Exception as e:
        all_validation_failures.append(f"normalize_api_params gpt-4 test failed: {e}")

    # Test 12: normalize_api_params - keep reasoning_effort for gpt-5
    total_tests += 1
    try:
        params = normalize_api_params("gpt-5", reasoning_effort="high", max_tokens=1000)
        if params.get("reasoning_effort") != "high":
            all_validation_failures.append("reasoning_effort should be kept for gpt-5")
        if params.get("max_completion_tokens") != 1000:
            all_validation_failures.append("max_tokens should be converted to max_completion_tokens for gpt-5")
        if "max_tokens" in params:
            all_validation_failures.append("max_tokens should be removed after conversion for gpt-5")
    except Exception as e:
        all_validation_failures.append(f"normalize_api_params gpt-5 test failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
