"""Authentication middleware for FastAPI.

Validates JWT tokens and injects current user into request state.
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
from loguru import logger

from synth_lab.infrastructure.auth.session_manager import get_session_manager
from synth_lab.services.auth_service import AuthService
from synth_lab.repositories.user_repository import UserRepository


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate JWT tokens and inject current user."""

    # Paths that don't require authentication
    PUBLIC_PATHS = [
        "/auth/login",
        "/auth/callback",
        "/auth/logout",  # Logout is idempotent - can be called without auth
        "/auth/test-login",  # Test-only endpoint for E2E tests
        "/docs",
        "/openapi.json",
        "/redoc",
        "/health",
    ]

    def __init__(self, app):
        """Initialize middleware."""
        super().__init__(app)
        self.session_manager = get_session_manager()

    async def dispatch(self, request: Request, call_next):
        """Process request and validate authentication.

        Args:
            request: FastAPI request
            call_next: Next middleware in chain

        Returns:
            Response from next middleware or error response
        """
        # Let CORS preflight requests through (OPTIONS)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Check if path requires authentication
        if self._is_public_path(request.url.path):
            return await call_next(request)

        # Get session token from Authorization header or cookie
        # Priority: Authorization header (cross-domain) > cookie (same-domain dev)
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            session_token = auth_header[7:]
        else:
            session_token = request.cookies.get("auth_token")

        if not session_token:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Not authenticated"},
            )

        # Validate token
        payload = self.session_manager.validate_token(session_token)
        if not payload:
            # Invalid or expired token
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or expired session"},
            )

        # Extract user info from token
        user_id = payload.get("sub")
        email = payload.get("email")

        # Inject user info into request state
        request.state.user_id = user_id
        request.state.email = email
        request.state.authenticated = True

        # Continue to next middleware/endpoint
        return await call_next(request)

    def _is_public_path(self, path: str) -> bool:
        """Check if path is public (doesn't require auth).

        Args:
            path: Request path

        Returns:
            True if path is public, False otherwise
        """
        # Exact match
        if path in self.PUBLIC_PATHS:
            return True

        # Prefix match for /docs, /openapi.json, etc.
        for public_path in self.PUBLIC_PATHS:
            if path.startswith(public_path):
                return True

        return False


def get_current_user_id(request: Request) -> Optional[str]:
    """Get current user ID from request state.

    Args:
        request: FastAPI request

    Returns:
        User ID if authenticated, None otherwise
    """
    return getattr(request.state, "user_id", None)


def require_auth(request: Request) -> str:
    """Require authentication and return user ID.

    Args:
        request: FastAPI request

    Returns:
        User ID

    Raises:
        HTTPException: If not authenticated
    """
    user_id = get_current_user_id(request)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user_id
