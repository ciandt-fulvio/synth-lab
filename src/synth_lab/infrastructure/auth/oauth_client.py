"""Google OAuth 2.0 Client for user authentication.

This module provides OAuth 2.0 integration with Google for user authentication.
Uses authlib for OAuth flow implementation.

Documentation:
- Authlib: https://docs.authlib.org/
- Google OAuth 2.0: https://developers.google.com/identity/protocols/oauth2
- Google userinfo endpoint: https://www.googleapis.com/oauth2/v3/userinfo

Example OAuth Flow:
    1. Generate authorization URL:
       >>> client = GoogleOAuthClient(client_id, client_secret, redirect_uri)
       >>> auth_url, state = client.generate_authorization_url()
       >>> # Redirect user to auth_url

    2. Handle callback and exchange code for token:
       >>> token = client.exchange_code_for_token(code="auth-code-from-callback")

    3. Fetch user information:
       >>> user_info = client.get_user_info(access_token=token["access_token"])
       >>> print(user_info["email"])
"""

import secrets
from authlib.integrations.requests_client import OAuth2Session


# Google OAuth 2.0 endpoints
GOOGLE_AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v3/userinfo"

# Required scopes for user authentication
GOOGLE_SCOPES = ["openid", "email", "profile"]


class GoogleOAuthClient:
    """Google OAuth 2.0 client for user authentication.

    Handles the complete OAuth flow:
    1. Generate authorization URL with state for CSRF protection
    2. Exchange authorization code for access token
    3. Fetch user information from Google

    Attributes:
        client_id: Google OAuth client ID
        client_secret: Google OAuth client secret
        redirect_uri: Callback URI registered in Google Console
    """

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        """Initialize the Google OAuth client.

        Args:
            client_id: Google OAuth client ID (from Google Cloud Console)
            client_secret: Google OAuth client secret
            redirect_uri: Callback URI (must match Google Console configuration)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def generate_authorization_url(self) -> tuple[str, str]:
        """Generate the Google OAuth authorization URL.

        Creates an authorization URL where the user will sign in with Google.
        Also generates a random state parameter for CSRF protection.

        Returns:
            Tuple of (authorization_url, state)
            - authorization_url: URL to redirect the user to
            - state: Random state value for CSRF protection (verify on callback)

        Example:
            >>> client = GoogleOAuthClient(client_id, client_secret, redirect_uri)
            >>> auth_url, state = client.generate_authorization_url()
            >>> # Store state in session, redirect user to auth_url
        """
        # Generate random state for CSRF protection
        state = secrets.token_urlsafe(32)

        # Create OAuth2 session
        session = OAuth2Session(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=GOOGLE_SCOPES,
        )

        # Generate authorization URL
        authorization_url, _ = session.create_authorization_url(
            GOOGLE_AUTHORIZATION_ENDPOINT, state=state
        )

        return authorization_url, state

    def exchange_code_for_token(self, code: str) -> dict:
        """Exchange authorization code for access token.

        After the user authorizes, Google redirects back with an authorization code.
        This method exchanges that code for an access token.

        Args:
            code: Authorization code from Google's callback

        Returns:
            Token response dictionary containing:
            - access_token: OAuth access token
            - token_type: Token type (usually "Bearer")
            - expires_in: Token expiration time in seconds
            - id_token: JWT ID token with user claims

        Example:
            >>> token = client.exchange_code_for_token(code="auth-code-from-callback")
            >>> access_token = token["access_token"]
        """
        # Create OAuth2 session
        session = OAuth2Session(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
        )

        # Exchange code for token
        token = session.fetch_token(
            url=GOOGLE_TOKEN_ENDPOINT,
            code=code,
            grant_type="authorization_code",
        )

        return token

    def get_user_info(self, access_token: str) -> dict:
        """Fetch user information from Google.

        Uses the access token to retrieve the user's profile information
        from Google's userinfo endpoint.

        Args:
            access_token: OAuth access token

        Returns:
            User information dictionary containing:
            - sub: Google user ID (unique identifier)
            - email: User's email address
            - email_verified: Whether email is verified
            - name: Full name
            - given_name: First name
            - family_name: Last name
            - picture: Profile picture URL
            - locale: User's locale

        Example:
            >>> user_info = client.get_user_info(access_token="ya29....")
            >>> print(f"User: {user_info['email']}")
        """
        # Create OAuth2 session with token
        session = OAuth2Session(
            client_id=self.client_id,
            client_secret=self.client_secret,
            token={"access_token": access_token, "token_type": "Bearer"},
        )

        # Fetch user info from Google
        response = session.get(GOOGLE_USERINFO_ENDPOINT)
        user_info = response.json()

        return user_info
