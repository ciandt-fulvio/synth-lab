"""Unit tests for Google OAuth Client.

Following Test-First Development:
- Tests are written BEFORE implementation
- Tests MUST fail initially (no implementation exists yet)
- Implementation in src/synth_lab/infrastructure/auth/oauth_client.py

The GoogleOAuthClient handles OAuth 2.0 flow with Google:
1. Generate authorization URL (user clicks "Sign in with Google")
2. Exchange authorization code for access token (callback)
3. Fetch user information from Google
"""

import pytest
from unittest.mock import Mock, patch


class TestOAuthClientInitialization:
    """Test OAuth client initialization (T018)."""

    def test_client_initialization_stores_credentials(self):
        """Test that GoogleOAuthClient stores client credentials."""
        from synth_lab.infrastructure.auth.oauth_client import GoogleOAuthClient

        client_id = "test-client-id.apps.googleusercontent.com"
        client_secret = "test-client-secret"
        redirect_uri = "http://localhost:8000/auth/callback"

        client = GoogleOAuthClient(
            client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri
        )

        assert client.client_id == client_id
        assert client.client_secret == client_secret
        assert client.redirect_uri == redirect_uri

    def test_client_requires_all_parameters(self):
        """Test that GoogleOAuthClient requires all initialization parameters."""
        from synth_lab.infrastructure.auth.oauth_client import GoogleOAuthClient

        # Should work with all parameters
        client = GoogleOAuthClient(
            client_id="test-id", client_secret="test-secret", redirect_uri="http://localhost"
        )
        assert client is not None


class TestOAuthAuthorizationURL:
    """Test OAuth authorization URL generation (T019)."""

    def test_generate_authorization_url_returns_url_and_state(self):
        """Test that generate_authorization_url returns a URL and state."""
        from synth_lab.infrastructure.auth.oauth_client import GoogleOAuthClient

        client = GoogleOAuthClient(
            client_id="test-id",
            client_secret="test-secret",
            redirect_uri="http://localhost:8000/auth/callback",
        )

        auth_url, state = client.generate_authorization_url()

        # Should return a URL string
        assert isinstance(auth_url, str)
        assert auth_url.startswith("https://")
        assert "accounts.google.com" in auth_url

        # Should return a state string for CSRF protection
        assert isinstance(state, str)
        assert len(state) > 0

    def test_authorization_url_includes_redirect_uri(self):
        """Test that the authorization URL includes the redirect_uri."""
        from synth_lab.infrastructure.auth.oauth_client import GoogleOAuthClient

        redirect_uri = "http://localhost:8000/auth/callback"
        client = GoogleOAuthClient(
            client_id="test-id", client_secret="test-secret", redirect_uri=redirect_uri
        )

        auth_url, _ = client.generate_authorization_url()

        # URL should include the redirect_uri as a parameter
        from urllib.parse import quote
        assert quote(redirect_uri, safe="") in auth_url or redirect_uri in auth_url

    def test_authorization_url_includes_required_scopes(self):
        """Test that the authorization URL requests required Google scopes."""
        from synth_lab.infrastructure.auth.oauth_client import GoogleOAuthClient

        client = GoogleOAuthClient(
            client_id="test-id",
            client_secret="test-secret",
            redirect_uri="http://localhost:8000/auth/callback",
        )

        auth_url, _ = client.generate_authorization_url()

        # Should request openid, email, and profile scopes
        assert "openid" in auth_url
        assert "email" in auth_url or "userinfo.email" in auth_url
        assert "profile" in auth_url or "userinfo.profile" in auth_url


class TestOAuthTokenExchange:
    """Test OAuth token exchange and user info retrieval (T020)."""

    @patch("synth_lab.infrastructure.auth.oauth_client.OAuth2Session")
    def test_exchange_code_for_token_calls_oauth_session(self, mock_oauth_session):
        """Test that exchange_code_for_token uses OAuth2Session to get token."""
        from synth_lab.infrastructure.auth.oauth_client import GoogleOAuthClient

        # Mock the OAuth2Session
        mock_session = Mock()
        mock_session.fetch_token.return_value = {
            "access_token": "mock-access-token",
            "token_type": "Bearer",
        }
        mock_oauth_session.return_value = mock_session

        client = GoogleOAuthClient(
            client_id="test-id",
            client_secret="test-secret",
            redirect_uri="http://localhost:8000/auth/callback",
        )

        # Exchange code for token
        token = client.exchange_code_for_token(code="test-auth-code")

        # Should have called fetch_token
        assert mock_session.fetch_token.called
        assert token["access_token"] == "mock-access-token"

    @patch("synth_lab.infrastructure.auth.oauth_client.OAuth2Session")
    def test_get_user_info_fetches_from_google(self, mock_oauth_session):
        """Test that get_user_info fetches user data from Google."""
        from synth_lab.infrastructure.auth.oauth_client import GoogleOAuthClient

        # Mock the OAuth2Session
        mock_session = Mock()
        mock_session.get.return_value.json.return_value = {
            "sub": "1234567890",
            "email": "alice@example.com",
            "name": "Alice Smith",
            "picture": "https://example.com/photo.jpg",
        }
        mock_oauth_session.return_value = mock_session

        client = GoogleOAuthClient(
            client_id="test-id",
            client_secret="test-secret",
            redirect_uri="http://localhost:8000/auth/callback",
        )

        # Get user info
        user_info = client.get_user_info(access_token="mock-access-token")

        # Should have called Google's userinfo endpoint
        assert mock_session.get.called
        assert user_info["email"] == "alice@example.com"
        assert user_info["sub"] == "1234567890"

    @patch("synth_lab.infrastructure.auth.oauth_client.OAuth2Session")
    def test_get_user_info_includes_required_fields(self, mock_oauth_session):
        """Test that get_user_info returns required user fields."""
        from synth_lab.infrastructure.auth.oauth_client import GoogleOAuthClient

        # Mock the OAuth2Session
        mock_session = Mock()
        mock_session.get.return_value.json.return_value = {
            "sub": "google-user-id-123",
            "email": "alice@example.com",
            "name": "Alice Smith",
            "picture": "https://example.com/photo.jpg",
            "email_verified": True,
        }
        mock_oauth_session.return_value = mock_session

        client = GoogleOAuthClient(
            client_id="test-id",
            client_secret="test-secret",
            redirect_uri="http://localhost:8000/auth/callback",
        )

        user_info = client.get_user_info(access_token="mock-access-token")

        # Must include these fields
        assert "sub" in user_info  # Google user ID
        assert "email" in user_info
        assert "name" in user_info or "given_name" in user_info
