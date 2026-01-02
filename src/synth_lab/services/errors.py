"""
Domain exception hierarchy for synth-lab.

Custom exceptions for service-layer errors that can be mapped to HTTP responses.

References:
    - Error handling: specs/010-rest-api/research.md
"""


class SynthLabError(Exception):
    """Base exception for synth-lab domain errors."""

    code: str = "INTERNAL_ERROR"
    message: str = "An internal error occurred"

    def __init__(self, message: str | None = None, details: dict | None = None):
        self.message = message or self.__class__.message
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(SynthLabError):
    """Base for not-found errors."""

    code = "NOT_FOUND"
    message = "Resource not found"


class SynthNotFoundError(NotFoundError):
    """Synth not found."""

    code = "SYNTH_NOT_FOUND"
    message = "Synth not found"

    def __init__(self, synth_id: str):
        super().__init__(f"Synth not found: {synth_id}", {"synth_id": synth_id})


class TopicNotFoundError(NotFoundError):
    """Topic guide not found."""

    code = "TOPIC_NOT_FOUND"
    message = "Topic guide not found"

    def __init__(self, topic_name: str):
        super().__init__(f"Topic guide not found: {topic_name}", {"topic_name": topic_name})


class ExecutionNotFoundError(NotFoundError):
    """Research execution not found."""

    code = "EXECUTION_NOT_FOUND"
    message = "Research execution not found"

    def __init__(self, exec_id: str):
        super().__init__(f"Research execution not found: {exec_id}", {"exec_id": exec_id})


class TranscriptNotFoundError(NotFoundError):
    """Transcript not found."""

    code = "TRANSCRIPT_NOT_FOUND"
    message = "Transcript not found"

    def __init__(self, exec_id: str, synth_id: str):
        super().__init__(
            f"Transcript not found for synth {synth_id} in execution {exec_id}",
            {"exec_id": exec_id, "synth_id": synth_id})


class PRFAQNotFoundError(NotFoundError):
    """PR-FAQ not found."""

    code = "PRFAQ_NOT_FOUND"
    message = "PR-FAQ not found"

    def __init__(self, exec_id: str):
        super().__init__(f"PR-FAQ not found for execution: {exec_id}", {"exec_id": exec_id})


class AvatarNotFoundError(NotFoundError):
    """Avatar not found for synth."""

    code = "AVATAR_NOT_FOUND"
    message = "Avatar not found"

    def __init__(self, synth_id: str):
        super().__init__(f"Avatar not found for synth: {synth_id}", {"synth_id": synth_id})


class SummaryNotFoundError(NotFoundError):
    """Summary not found for execution."""

    code = "SUMMARY_NOT_FOUND"
    message = "Summary not found"

    def __init__(self, exec_id: str):
        super().__init__(f"Summary not found for execution: {exec_id}", {"exec_id": exec_id})


class ValidationError(SynthLabError):
    """Base for validation errors."""

    code = "VALIDATION_ERROR"
    message = "Validation failed"


class InvalidQueryError(ValidationError):
    """Invalid SQL query."""

    code = "INVALID_QUERY"
    message = "Invalid or unsafe query"

    def __init__(self, reason: str, query: str | None = None):
        details = {"reason": reason}
        if query:
            details["query"] = query
        super().__init__(f"Invalid query: {reason}", details)


class InvalidRequestError(ValidationError):
    """Invalid request parameters."""

    code = "INVALID_REQUEST"
    message = "Invalid request parameters"


class GenerationFailedError(SynthLabError):
    """LLM generation failed."""

    code = "GENERATION_FAILED"
    message = "Generation failed"

    def __init__(self, reason: str, details: dict | None = None):
        super().__init__(f"Generation failed: {reason}", details)


class DatabaseError(SynthLabError):
    """Database operation failed."""

    code = "DATABASE_ERROR"
    message = "Database operation failed"


if __name__ == "__main__":
    import sys

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Test 1: SynthLabError base
    total_tests += 1
    try:
        error = SynthLabError("Test error")
        if error.code != "INTERNAL_ERROR":
            all_validation_failures.append(f"Base code mismatch: {error.code}")
        if str(error) != "Test error":
            all_validation_failures.append(f"Message mismatch: {str(error)}")
    except Exception as e:
        all_validation_failures.append(f"SynthLabError test failed: {e}")

    # Test 2: SynthNotFoundError
    total_tests += 1
    try:
        error = SynthNotFoundError("abc123")
        if error.code != "SYNTH_NOT_FOUND":
            all_validation_failures.append(f"SynthNotFoundError code mismatch: {error.code}")
        if error.details.get("synth_id") != "abc123":
            all_validation_failures.append(f"Details mismatch: {error.details}")
        if "abc123" not in str(error):
            all_validation_failures.append(f"ID not in message: {str(error)}")
    except Exception as e:
        all_validation_failures.append(f"SynthNotFoundError test failed: {e}")

    # Test 3: TopicNotFoundError
    total_tests += 1
    try:
        error = TopicNotFoundError("compra-amazon")
        if error.code != "TOPIC_NOT_FOUND":
            all_validation_failures.append(f"TopicNotFoundError code mismatch: {error.code}")
        if "compra-amazon" not in str(error):
            all_validation_failures.append(f"Topic not in message: {str(error)}")
    except Exception as e:
        all_validation_failures.append(f"TopicNotFoundError test failed: {e}")

    # Test 4: TranscriptNotFoundError
    total_tests += 1
    try:
        error = TranscriptNotFoundError("batch_test", "abc123")
        if error.details.get("exec_id") != "batch_test":
            all_validation_failures.append(f"exec_id mismatch: {error.details}")
        if error.details.get("synth_id") != "abc123":
            all_validation_failures.append(f"synth_id mismatch: {error.details}")
    except Exception as e:
        all_validation_failures.append(f"TranscriptNotFoundError test failed: {e}")

    # Test 5: InvalidQueryError
    total_tests += 1
    try:
        error = InvalidQueryError("DROP not allowed", "DROP TABLE synths")
        if error.code != "INVALID_QUERY":
            all_validation_failures.append(f"InvalidQueryError code mismatch: {error.code}")
        if "DROP not allowed" not in str(error):
            all_validation_failures.append(f"Reason not in message: {str(error)}")
        if error.details.get("query") != "DROP TABLE synths":
            all_validation_failures.append(f"Query not in details: {error.details}")
    except Exception as e:
        all_validation_failures.append(f"InvalidQueryError test failed: {e}")

    # Test 6: Inheritance chain
    total_tests += 1
    try:
        error = SynthNotFoundError("test")
        if not isinstance(error, NotFoundError):
            all_validation_failures.append("SynthNotFoundError should inherit NotFoundError")
        if not isinstance(error, SynthLabError):
            all_validation_failures.append("SynthNotFoundError should inherit SynthLabError")
        if not isinstance(error, Exception):
            all_validation_failures.append("SynthNotFoundError should inherit Exception")
    except Exception as e:
        all_validation_failures.append(f"Inheritance test failed: {e}")

    # Test 7: GenerationFailedError
    total_tests += 1
    try:
        error = GenerationFailedError("LLM timeout", {"model": "gpt-4"})
        if error.code != "GENERATION_FAILED":
            all_validation_failures.append(f"GenerationFailedError code mismatch: {error.code}")
        if error.details.get("model") != "gpt-4":
            all_validation_failures.append(f"Details mismatch: {error.details}")
    except Exception as e:
        all_validation_failures.append(f"GenerationFailedError test failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
