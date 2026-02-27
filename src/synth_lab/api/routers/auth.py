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
    ShareByEmailRequest,
    ShareListResponse,
    ShareResultResponse,
)
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
    """Dependency to get AuthService instance."""
    user_repository = UserRepository(db)
    return AuthService(user_repository=user_repository)


def get_sharing_service(db: Session = Depends(get_db_session)) -> SharingService:
    """Dependency to get SharingService instance."""
    return SharingService(db)


async def get_current_user_id(request: Request) -> str:
    """Get current user ID from session."""
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


# ── Auth endpoints ──────────────────────────────────────────────────────


@router.get("/login")
async def login(request: Request):
    """Initiate Google OAuth login flow."""
    oauth_client = get_oauth_client()
    auth_url, state = oauth_client.get_authorization_url()
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
    sharing_service: SharingService = Depends(get_sharing_service),
):
    """Handle OAuth callback from Google.

    After login, automatically accepts any pending invites for the user's email.
    """
    stored_state = request.session.get("oauth_state")
    if state != stored_state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter - potential CSRF attack",
        )

    oauth_client = get_oauth_client()
    try:
        tokens = await oauth_client.exchange_code_for_tokens(code)
        access_token = tokens["access_token"]
        user_info = await oauth_client.get_user_info(access_token)
        user, session_token = auth_service.handle_oauth_callback(user_info)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth authentication failed: {str(e)}",
        )

    # Accept pending invites for this user's email
    try:
        accepted = sharing_service.accept_pending_invites(str(user.id), user.email)
        if accepted > 0:
            logger.info(f"Accepted {accepted} pending invite(s) for {user.email}")
    except Exception as e:
        logger.warning(f"Failed to accept pending invites for {user.email}: {e}")

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    environment = os.getenv("ENVIRONMENT", "development")

    if environment == "development":
        response = RedirectResponse(url=frontend_url, status_code=status.HTTP_302_FOUND)
        response.set_cookie(
            key="auth_token",
            value=session_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=480 * 60,
            path="/",
        )
        return response
    else:
        redirect_url = f"{frontend_url}/auth/callback?token={session_token}"
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)


@router.post("/test-login")
async def test_login(
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
    sharing_service: SharingService = Depends(get_sharing_service),
):
    """Test-only endpoint to bypass OAuth for E2E tests.

    Only available in test/development/staging environments.
    Also accepts pending invites for the test user.
    """
    environment = os.getenv("ENVIRONMENT", "development")
    if environment not in ["test", "development", "staging"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )

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

    # Accept pending invites
    try:
        accepted = sharing_service.accept_pending_invites(str(user.id), user.email)
        if accepted > 0:
            logger.info(f"Accepted {accepted} pending invite(s) for test user {test_email}")
    except Exception as e:
        logger.warning(f"Failed to accept pending invites for test user: {e}")

    session_token = auth_service.session_manager.create_access_token(
        user_id=str(user.id),
        email=user.email,
    )

    if environment in ["production", "staging"]:
        return {
            **user.to_dict(),
            "token": session_token,
        }
    else:
        response.set_cookie(
            key="auth_token",
            value=session_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=480 * 60,
            path="/",
        )
        logger.debug(f"[/auth/test-login] Set auth cookie for test user {user.id}")
        return user.to_dict()


@router.get("/me")
async def get_me(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Get current authenticated user."""
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
    """Logout current user."""
    response.delete_cookie("auth_token")
    return {"message": "Logged out successfully"}


# ── Experiment sharing endpoints ────────────────────────────────────────


@router.post("/experiments/{experiment_id}/shares", response_model=ShareResultResponse)
async def share_experiment(
    experiment_id: str,
    request_body: ShareByEmailRequest,
    current_user_id: str = Depends(get_current_user_id),
    sharing_service: SharingService = Depends(get_sharing_service),
):
    """Share an experiment by email.

    If user exists, creates direct share. Otherwise creates pending invite.
    Automatically shares the associated synth_group.
    """
    try:
        result = sharing_service.share_experiment_by_email(
            experiment_id=experiment_id,
            owner_id=current_user_id,
            email=request_body.email,
        )
        return ShareResultResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/experiments/{experiment_id}/shares", response_model=ShareListResponse)
async def list_experiment_shares(
    experiment_id: str,
    current_user_id: str = Depends(get_current_user_id),
    sharing_service: SharingService = Depends(get_sharing_service),
):
    """List all users and pending invites for an experiment."""
    try:
        result = sharing_service.list_experiment_shares(experiment_id, current_user_id)
        return ShareListResponse(resource_id=experiment_id, **result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/experiments/{experiment_id}/shares")
async def revoke_experiment_share(
    experiment_id: str,
    email: str,
    current_user_id: str = Depends(get_current_user_id),
    sharing_service: SharingService = Depends(get_sharing_service),
):
    """Revoke experiment access by email (handles active shares and pending invites)."""
    try:
        success = sharing_service.revoke_experiment_share(
            experiment_id=experiment_id,
            owner_id=current_user_id,
            target_email=email,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Share not found for {email}",
            )

        return {"message": f"Access revoked for {email}"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise


# ── Synth group sharing endpoints ──────────────────────────────────────


@router.post("/synth-groups/{synth_group_id}/shares", response_model=ShareResultResponse)
async def share_synth_group(
    synth_group_id: str,
    request_body: ShareByEmailRequest,
    current_user_id: str = Depends(get_current_user_id),
    sharing_service: SharingService = Depends(get_sharing_service),
):
    """Share a synth_group by email."""
    try:
        result = sharing_service.share_synth_group_by_email(
            synth_group_id=synth_group_id,
            owner_id=current_user_id,
            email=request_body.email,
        )
        return ShareResultResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/synth-groups/{synth_group_id}/shares", response_model=ShareListResponse)
async def list_synth_group_shares(
    synth_group_id: str,
    current_user_id: str = Depends(get_current_user_id),
    sharing_service: SharingService = Depends(get_sharing_service),
):
    """List all users and pending invites for a synth_group."""
    try:
        result = sharing_service.list_synth_group_shares(synth_group_id, current_user_id)
        return ShareListResponse(resource_id=synth_group_id, **result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/synth-groups/{synth_group_id}/shares")
async def revoke_synth_group_share(
    synth_group_id: str,
    email: str,
    current_user_id: str = Depends(get_current_user_id),
    sharing_service: SharingService = Depends(get_sharing_service),
):
    """Revoke synth_group access by email."""
    try:
        success = sharing_service.revoke_synth_group_share(
            synth_group_id=synth_group_id,
            owner_id=current_user_id,
            target_email=email,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Share not found for {email}",
            )

        return {"message": f"Access revoked for {email}"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except HTTPException:
        raise
