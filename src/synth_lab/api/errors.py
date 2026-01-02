"""
Exception handlers for synth-lab API.

Maps domain exceptions to HTTP responses with consistent error format.

References:
    - Error format: specs/010-rest-api/quickstart.md
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from synth_lab.services.errors import (
    DatabaseError,
    GenerationFailedError,
    InvalidQueryError,
    InvalidRequestError,
    NotFoundError,
    SynthLabError,
    ValidationError)


def error_response(
    status_code: int, code: str, message: str, details: dict | None = None
) -> JSONResponse:
    """Create a standardized error response."""
    content = {
        "error": {
            "code": code,
            "message": message,
        }
    }
    if details:
        content["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=content)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI app."""

    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        """Handle not-found errors."""
        logger.debug(f"Not found: {exc.code} - {exc.message}")
        return error_response(404, exc.code, exc.message, exc.details)

    @app.exception_handler(InvalidQueryError)
    async def invalid_query_handler(request: Request, exc: InvalidQueryError) -> JSONResponse:
        """Handle invalid query errors."""
        logger.warning(f"Invalid query: {exc.message}")
        return error_response(422, exc.code, exc.message, exc.details)

    @app.exception_handler(InvalidRequestError)
    async def invalid_request_handler(request: Request, exc: InvalidRequestError) -> JSONResponse:
        """Handle invalid request errors."""
        logger.warning(f"Invalid request: {exc.message}")
        return error_response(422, exc.code, exc.message, exc.details)

    @app.exception_handler(ValidationError)
    async def validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
        """Handle validation errors."""
        logger.warning(f"Validation error: {exc.message}")
        return error_response(422, exc.code, exc.message, exc.details)

    @app.exception_handler(GenerationFailedError)
    async def generation_failed_handler(
        request: Request, exc: GenerationFailedError
    ) -> JSONResponse:
        """Handle generation failure errors."""
        logger.error(f"Generation failed: {exc.message}")
        return error_response(422, exc.code, exc.message, exc.details)

    @app.exception_handler(DatabaseError)
    async def database_handler(request: Request, exc: DatabaseError) -> JSONResponse:
        """Handle database errors."""
        logger.error(f"Database error: {exc.message}")
        return error_response(503, exc.code, exc.message)

    @app.exception_handler(SynthLabError)
    async def synth_lab_handler(request: Request, exc: SynthLabError) -> JSONResponse:
        """Handle generic synth-lab errors."""
        logger.error(f"SynthLabError: {exc.code} - {exc.message}")
        return error_response(500, exc.code, exc.message, exc.details)

    @app.exception_handler(Exception)
    async def generic_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions."""
        logger.exception(f"Unexpected error: {exc}")
        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")


if __name__ == "__main__":
    import sys
    from unittest.mock import MagicMock

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Test 1: error_response format
    total_tests += 1
    try:
        response = error_response(404, "NOT_FOUND", "Resource not found", {"id": "123"})
        if response.status_code != 404:
            all_validation_failures.append(f"Status code mismatch: {response.status_code}")
    except Exception as e:
        all_validation_failures.append(f"error_response test failed: {e}")

    # Test 2: error_response without details
    total_tests += 1
    try:
        response = error_response(500, "ERROR", "Something went wrong")
        if response.status_code != 500:
            all_validation_failures.append(f"Status code mismatch: {response.status_code}")
    except Exception as e:
        all_validation_failures.append(f"error_response no details test failed: {e}")

    # Test 3: Register handlers on mock app
    total_tests += 1
    try:
        mock_app = MagicMock(spec=FastAPI)
        register_exception_handlers(mock_app)
        # Should have registered multiple handlers
        if mock_app.exception_handler.call_count < 5:
            all_validation_failures.append(
                f"Expected at least 5 handlers, got {mock_app.exception_handler.call_count}"
            )
    except Exception as e:
        all_validation_failures.append(f"Register handlers test failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
