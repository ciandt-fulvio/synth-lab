"""Google OAuth 2.0 client wrapper.

Provides a simplified interface for Google OAuth authentication flow using authlib.
Handles authorization URL generation and token exchange.
"""
import os
import secrets
from typing import Tuple, List, Optional, Dict, Any
from urllib.parse import urlencode


class OAuthClient:
    """Google OAuth 2.0 client for user authentication."""

    # Google OAuth 2.0 endpoints
    AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
    USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v3/userinfo"

    # Default scopes for user authentication
    DEFAULT_SCOPES = ["openid", "email", "profile"]

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scopes: Optional[List[str]] = None,
    ):
        """Initialize OAuth client.

        Args:
            client_id: Google OAuth client ID
            client_secret: Google OAuth client secret
            redirect_uri: Callback URL for OAuth flow
            scopes: OAuth scopes to request (default: openid, email, profile)

        Raises:
            ValueError: If any required parameter is empty

        Example:
            >>> client = OAuthClient(
            ...     client_id="your-client-id.apps.googleusercontent.com",
            ...     client_secret="your-client-secret",
            ...     redirect_uri="http://localhost:8000/auth/callback"
            ... )
        """
        if not client_id or not client_id.strip():
            raise ValueError("client_id is required")
        if not client_secret or not client_secret.strip():
            raise ValueError("client_secret is required")
        if not redirect_uri or not redirect_uri.strip():
            raise ValueError("redirect_uri is required")

        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = scopes or self.DEFAULT_SCOPES

    @classmethod
    def from_env(cls) -> "OAuthClient":
        """Create OAuth client from environment variables.

        Returns:
            Configured OAuthClient instance

        Environment Variables:
            GOOGLE_CLIENT_ID: Required
            GOOGLE_CLIENT_SECRET: Required
            BACKEND_URL: Required (used to construct redirect_uri)

        Raises:
            ValueError: If required environment variables are not set

        Example:
            >>> client = OAuthClient.from_env()
        """
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")

        if not client_id:
            raise ValueError("GOOGLE_CLIENT_ID environment variable is required")
        if not client_secret:
            raise ValueError("GOOGLE_CLIENT_SECRET environment variable is required")

        redirect_uri = f"{backend_url.rstrip('/')}/auth/callback"

        return cls(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
        )

    def get_authorization_url(self, state: Optional[str] = None) -> Tuple[str, str]:
        """Generate OAuth authorization URL.

        Args:
            state: Optional CSRF state token. If None, a random one is generated.

        Returns:
            Tuple of (authorization_url, state)

        Example:
            >>> client = OAuthClient.from_env()
            >>> auth_url, state = client.get_authorization_url()
            >>> print(auth_url)
            https://accounts.google.com/o/oauth2/v2/auth?client_id=...
        """
        # Generate random state if not provided (CSRF protection)
        if not state:
            state = secrets.token_urlsafe(32)

        # Build authorization URL parameters
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "state": state,
            "access_type": "offline",  # Request refresh token
            "prompt": "consent",  # Force consent screen to get refresh token
        }

        authorization_url = f"{self.AUTHORIZATION_ENDPOINT}?{urlencode(params)}"

        return (authorization_url, state)

    async def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens.

        Args:
            code: Authorization code from OAuth callback

        Returns:
            Token response dict containing:
                - access_token: OAuth access token
                - refresh_token: OAuth refresh token (if granted)
                - id_token: JWT ID token with user info
                - expires_in: Token expiration time in seconds
                - token_type: Usually "Bearer"

        Raises:
            Exception: If token exchange fails

        Example:
            >>> client = OAuthClient.from_env()
            >>> tokens = await client.exchange_code_for_tokens("auth_code_here")
            >>> print(tokens["access_token"])
        """
        import httpx

        token_data = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(
                self.TOKEN_ENDPOINT,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            return response.json()

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Fetch user information from Google using access token.

        Args:
            access_token: OAuth access token

        Returns:
            User info dict containing:
                - sub: Google user ID
                - email: User email
                - email_verified: Whether email is verified
                - name: User's full name
                - picture: Profile picture URL
                - given_name: First name
                - family_name: Last name

        Raises:
            Exception: If user info request fails

        Example:
            >>> client = OAuthClient.from_env()
            >>> user_info = await client.get_user_info("access_token_here")
            >>> print(user_info["email"])
            user@example.com
        """
        import httpx

        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                self.USERINFO_ENDPOINT,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()

    def decode_id_token(self, id_token: str) -> Dict[str, Any]:
        """Decode ID token JWT to extract user claims.

        Note: This does NOT verify the signature. For production use,
        you should verify the token signature against Google's public keys.

        Args:
            id_token: JWT ID token from Google

        Returns:
            Decoded token payload with user claims

        Example:
            >>> client = OAuthClient.from_env()
            >>> payload = client.decode_id_token(id_token)
            >>> print(payload["email"])
            user@example.com
        """
        from jose import jwt

        # Decode without verification (for development)
        # In production, should verify signature with Google's public keys
        payload = jwt.decode(
            id_token,
            options={
                "verify_signature": False,
                "verify_aud": False,
                "verify_exp": True,
            },
        )
        return payload


def get_oauth_client() -> OAuthClient:
    """Get OAuth client instance configured from environment.

    Returns:
        Configured OAuthClient instance

    Example:
        >>> client = get_oauth_client()
        >>> auth_url, state = client.get_authorization_url()
    """
    return OAuthClient.from_env()
