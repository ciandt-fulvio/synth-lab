"""Authentication API router.

Provides endpoints for Google OAuth login flow, session management, and sharing.
"""
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from synth_lab.api.schemas.sharing import (
    ShareExperimentRequest,
    ShareListResponse,
    ShareResponse,
)
from synth_lab.domain.entities.share import PermissionLevel
from synth_lab.infrastructure.auth.oauth_client import get_oauth_client
from synth_lab.infrastructure.auth.session_manager import SessionManager
from synth_lab.infrastructure.database_v2 import get_db_session
from synth_lab.repositories.user_repository import UserRepository
from synth_lab.services.auth_service import AuthService
from synth_lab.services.sharing_service import SharingService

router = APIRouter(prefix="/auth", tags=["auth"])

# Rate limiter for auth endpoints
limiter = Limiter(key_func=get_remote_address)


def get_auth_service(db: Session = Depends(get_db_session)) -> AuthService:
    """Dependency to get AuthService instance.

    Args:
        db: Database session

    Returns:
        Configured AuthService
    """
    user_repository = UserRepository(db)
    return AuthService(user_repository=user_repository)


def get_sharing_service(db: Session = Depends(get_db_session)) -> SharingService:
    """Dependency to get SharingService instance.

    Args:
        db: Database session

    Returns:
        Configured SharingService
    """
    return SharingService(db)


async def get_current_user_id(request: Request) -> str:
    """Get current user ID from session.

    Args:
        request: FastAPI request with session cookie

    Returns:
        User ID from session

    Raises:
        HTTPException: If not authenticated or session invalid
    """
    # Check Authorization header first (cross-domain), then cookie (same-domain dev)
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        session_token = auth_header[7:]
    else:
        session_token = request.cookies.get("auth_token")

    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    session_manager = SessionManager()
    payload = session_manager.validate_token(session_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session payload",
        )

    return user_id


@router.get("/login")
async def login(request: Request):
    """Initiate Google OAuth login flow.

    Redirects user to Google OAuth consent screen.

    Returns:
        Redirect to Google OAuth authorization URL
    """
    oauth_client = get_oauth_client()
    auth_url, state = oauth_client.get_authorization_url()

    # Store state in session for CSRF protection
    request.session["oauth_state"] = state

    return RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)


@router.get("/callback")
@limiter.limit("10/minute")
async def callback(
    request: Request,
    response: Response,
    code: str,
    state: Optional[str] = None,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Handle OAuth callback from Google.

    Exchanges authorization code for tokens, validates user, creates session.

    Args:
        request: FastAPI request
        response: FastAPI response (for setting cookie)
        code: Authorization code from Google
        state: CSRF state token
        auth_service: Auth service dependency

    Returns:
        Redirect to frontend with session cookie set

    Raises:
        HTTPException: If OAuth flow fails or user not whitelisted
    """
    # Verify CSRF state
    stored_state = request.session.get("oauth_state")
    if state != stored_state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter - potential CSRF attack",
        )

    # Exchange code for tokens
    oauth_client = get_oauth_client()
    try:
        tokens = await oauth_client.exchange_code_for_tokens(code)
        access_token = tokens["access_token"]

        # Get user info from Google
        user_info = await oauth_client.get_user_info(access_token)

        # Handle OAuth callback (create/update user, validate whitelist)
        user, session_token = auth_service.handle_oauth_callback(user_info)

    except ValueError as e:
        # User not whitelisted or validation error
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        # OAuth or API error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth authentication failed: {str(e)}",
        )

    # Redirect to frontend with token
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    environment = os.getenv("ENVIRONMENT", "development")

    # For local development: set cookie directly (same domain via proxy)
    # For staging/production: send token in URL for frontend to set
    if environment == "development":
        response = RedirectResponse(url=frontend_url, status_code=status.HTTP_302_FOUND)
        response.set_cookie(
            key="auth_token",
            value=session_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=480 * 60,  # 8 hours
            path="/",
        )
        return response
    else:
        # Staging/Production: redirect to frontend with token in URL
        # Frontend will set the cookie locally
        redirect_url = f"{frontend_url}/auth/callback?token={session_token}"
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)


@router.post("/test-login")
async def test_login(
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Test-only endpoint to bypass OAuth for E2E tests.

    Only available in test/development/staging environments.
    Creates or retrieves a test user and sets auth cookie.

    Returns:
        User profile data

    Raises:
        HTTPException: If in production environment
    """
    environment = os.getenv("ENVIRONMENT", "development")
    if environment not in ["test", "development", "staging"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )

    # Get or create test user (matches tests/fixtures/seed_test.py)
    test_email = "testuser@example.com"
    test_user_id = "00000001-0000-0000-0000-000000000001"
    test_google_id = "google-test-user-001"

    user = auth_service.user_repository.get_by_email(test_email)

    if not user:
        from synth_lab.domain.entities.user import User
        user = User(
            id=test_user_id,
            google_user_id=test_google_id,
            email=test_email,
            display_name="Test User",
            profile_picture_url=None,
        )
        user = auth_service.user_repository.create(user)
        logger.info(f"Created test user: {user.id} ({test_email})")

    # Generate session token
    session_token = auth_service.session_manager.create_access_token(
        user_id=str(user.id),
        email=user.email,
    )

    # Set auth cookie (for staging/production, return token in response body)
    if environment in ["production", "staging"]:
        # For staging/production with separate domains, return token
        # Frontend will set cookie locally via document.cookie
        return {
            **user.to_dict(),
            "token": session_token,
        }
    else:
        # For development (same domain via proxy), set cookie directly
        response.set_cookie(
            key="auth_token",
            value=session_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=480 * 60,  # 8 hours
            path="/",
        )
        logger.debug(f"[/auth/test-login] Set auth cookie for test user {user.id}")
        return user.to_dict()


@router.get("/me")
async def get_me(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Get current authenticated user.

    Returns:
        User profile data

    Raises:
        HTTPException: If not authenticated
    """
    # Check Authorization header first (cross-domain), then cookie (same-domain dev)
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        session_token = auth_header[7:]
    else:
        session_token = request.cookies.get("auth_token")

    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    user = auth_service.get_current_user(session_token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    return user.to_dict()


@router.post("/logout")
async def logout(response: Response):
    """Logout current user.

    Clears session cookie.

    Returns:
        Success message
    """
    response.delete_cookie("auth_token")
    return {"message": "Logged out successfully"}


@router.post("/experiments/{experiment_id}/shares", response_model=ShareResponse)
async def share_experiment(
    experiment_id: str,
    request_body: ShareExperimentRequest,
    current_user_id: str = Depends(get_current_user_id),
    sharing_service: SharingService = Depends(get_sharing_service),
):
    """Share an experiment with another user.

    Automatically shares the associated synth_group with the same permission level.

    Args:
        experiment_id: Experiment ID to share
        request_body: Share request with user_id and permission_level
        current_user_id: Current authenticated user (owner)
        sharing_service: Sharing service dependency

    Returns:
        Created share information

    Raises:
        HTTPException: If validation fails or user not authorized
    """
    try:
        permission_level = PermissionLevel(request_body.permission_level)
        share = sharing_service.share_experiment(
            experiment_id=experiment_id,
            owner_id=current_user_id,
            target_user_id=request_body.user_id,
            permission_level=permission_level,
        )

        # Get user info for response
        shares_list = sharing_service.list_experiment_shares(
            experiment_id, current_user_id
        )

        # Find the newly created share
        for share_data in shares_list:
            if share_data["user_id"] == request_body.user_id:
                return ShareResponse(**share_data, experiment_id=experiment_id)

        # Fallback if not found in list
        return ShareResponse(
            share_id=str(share.id),
            experiment_id=experiment_id,
            user_id=str(share.user_id),
            permission_level=share.permission_level.value,
            granted_at=share.granted_at,
            granted_by_id=str(share.granted_by_id),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to share experiment: {str(e)}",
        )


@router.get("/experiments/{experiment_id}/shares", response_model=ShareListResponse)
async def list_experiment_shares(
    experiment_id: str,
    current_user_id: str = Depends(get_current_user_id),
    sharing_service: SharingService = Depends(get_sharing_service),
):
    """List all users who have access to an experiment.

    Args:
        experiment_id: Experiment ID
        current_user_id: Current authenticated user (owner)
        sharing_service: Sharing service dependency

    Returns:
        List of shares with user information

    Raises:
        HTTPException: If validation fails or user not authorized
    """
    try:
        shares_list = sharing_service.list_experiment_shares(
            experiment_id, current_user_id
        )

        share_responses = [
            ShareResponse(**share_data, experiment_id=experiment_id)
            for share_data in shares_list
        ]

        return ShareListResponse(
            experiment_id=experiment_id,
            shares=share_responses,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list shares: {str(e)}",
        )


@router.delete("/experiments/{experiment_id}/shares/{user_id}")
async def revoke_experiment_share(
    experiment_id: str,
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    sharing_service: SharingService = Depends(get_sharing_service),
):
    """Revoke experiment access from a user.

    Args:
        experiment_id: Experiment ID
        user_id: User ID to revoke access from
        current_user_id: Current authenticated user (owner)
        sharing_service: Sharing service dependency

    Returns:
        Success message

    Raises:
        HTTPException: If validation fails or user not authorized
    """
    try:
        success = sharing_service.revoke_experiment_share(
            experiment_id=experiment_id,
            owner_id=current_user_id,
            target_user_id=user_id,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Share not found for user {user_id}",
            )

        return {"message": f"Access revoked for user {user_id}"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke share: {str(e)}",
        )


@router.post("/synth-groups/{synth_group_id}/shares", response_model=ShareResponse)
async def share_synth_group(
    synth_group_id: str,
    request_body: ShareExperimentRequest,
    current_user_id: str = Depends(get_current_user_id),
    sharing_service: SharingService = Depends(get_sharing_service),
):
    """Share a synth_group with another user independently.

    Args:
        synth_group_id: Synth group ID to share
        request_body: Share request with user_id and permission_level
        current_user_id: Current authenticated user (owner)
        sharing_service: Sharing service dependency

    Returns:
        Created share information

    Raises:
        HTTPException: If validation fails or user not authorized
    """
    try:
        permission_level = PermissionLevel(request_body.permission_level)
        share = sharing_service.share_synth_group(
            synth_group_id=synth_group_id,
            owner_id=current_user_id,
            target_user_id=request_body.user_id,
            permission_level=permission_level,
        )

        # Get user info for response
        shares_list = sharing_service.list_synth_group_shares(
            synth_group_id, current_user_id
        )

        # Find the newly created share
        for share_data in shares_list:
            if share_data["user_id"] == request_body.user_id:
                return ShareResponse(
                    **share_data,
                    experiment_id=synth_group_id,  # Reuse field for synth_group_id
                )

        # Fallback if not found in list
        return ShareResponse(
            share_id=str(share.id),
            experiment_id=synth_group_id,  # Reuse field for synth_group_id
            user_id=str(share.user_id),
            permission_level=share.permission_level.value,
            granted_at=share.granted_at,
            granted_by_id=str(share.granted_by_id),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to share synth_group: {str(e)}",
        )


@router.get("/synth-groups/{synth_group_id}/shares", response_model=ShareListResponse)
async def list_synth_group_shares(
    synth_group_id: str,
    current_user_id: str = Depends(get_current_user_id),
    sharing_service: SharingService = Depends(get_sharing_service),
):
    """List all users who have access to a synth_group.

    Args:
        synth_group_id: Synth group ID
        current_user_id: Current authenticated user (owner)
        sharing_service: Sharing service dependency

    Returns:
        List of shares with user information

    Raises:
        HTTPException: If validation fails or user not authorized
    """
    try:
        shares_list = sharing_service.list_synth_group_shares(
            synth_group_id, current_user_id
        )

        share_responses = [
            ShareResponse(
                **share_data,
                experiment_id=synth_group_id,  # Reuse field for synth_group_id
            )
            for share_data in shares_list
        ]

        return ShareListResponse(
            experiment_id=synth_group_id,  # Reuse field for synth_group_id
            shares=share_responses,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list shares: {str(e)}",
        )


@router.delete("/synth-groups/{synth_group_id}/shares/{user_id}")
async def revoke_synth_group_share(
    synth_group_id: str,
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    sharing_service: SharingService = Depends(get_sharing_service),
):
    """Revoke synth_group access from a user.

    Args:
        synth_group_id: Synth group ID
        user_id: User ID to revoke access from
        current_user_id: Current authenticated user (owner)
        sharing_service: Sharing service dependency

    Returns:
        Success message

    Raises:
        HTTPException: If validation fails or user not authorized
    """
    try:
        success = sharing_service.revoke_synth_group_share(
            synth_group_id=synth_group_id,
            owner_id=current_user_id,
            target_user_id=user_id,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Share not found for user {user_id}",
            )

        return {"message": f"Access revoked for user {user_id}"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke share: {str(e)}",
        )
