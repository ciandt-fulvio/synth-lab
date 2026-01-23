"""Unit tests for OAuth client wrapper.

Tests OAuth client initialization and authorization URL generation.
Must FAIL before implementation.
"""
import pytest
from synth_lab.infrastructure.auth.oauth_client import OAuthClient


@pytest.fixture
def oauth_config():
    """OAuth configuration for testing."""
    return {
        "client_id": "test_client_id.apps.googleusercontent.com",
        "client_secret": "test_client_secret",
        "redirect_uri": "http://localhost:8000/auth/callback",
    }


class TestOAuthClientInitialization:
    """Test OAuth client initialization."""

    def test_create_oauth_client(self, oauth_config):
        """Should create OAuth client with valid config."""
        client = OAuthClient(
            client_id=oauth_config["client_id"],
            client_secret=oauth_config["client_secret"],
            redirect_uri=oauth_config["redirect_uri"],
        )

        assert client is not None
        assert client.client_id == oauth_config["client_id"]
        assert client.redirect_uri == oauth_config["redirect_uri"]

    def test_create_without_client_id(self, oauth_config):
        """Should raise error if client_id is missing."""
        with pytest.raises(ValueError, match="client_id"):
            OAuthClient(
                client_id="",
                client_secret=oauth_config["client_secret"],
                redirect_uri=oauth_config["redirect_uri"],
            )

    def test_create_without_client_secret(self, oauth_config):
        """Should raise error if client_secret is missing."""
        with pytest.raises(ValueError, match="client_secret"):
            OAuthClient(
                client_id=oauth_config["client_id"],
                client_secret="",
                redirect_uri=oauth_config["redirect_uri"],
            )

    def test_create_without_redirect_uri(self, oauth_config):
        """Should raise error if redirect_uri is missing."""
        with pytest.raises(ValueError, match="redirect_uri"):
            OAuthClient(
                client_id=oauth_config["client_id"],
                client_secret=oauth_config["client_secret"],
                redirect_uri="",
            )

    def test_create_from_env(self, monkeypatch, oauth_config):
        """Should create client from environment variables."""
        monkeypatch.setenv("GOOGLE_CLIENT_ID", oauth_config["client_id"])
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", oauth_config["client_secret"])
        monkeypatch.setenv("BACKEND_URL", "http://localhost:8000")

        client = OAuthClient.from_env()

        assert client.client_id == oauth_config["client_id"]
        assert client.redirect_uri == "http://localhost:8000/auth/callback"


class TestAuthorizationURLGeneration:
    """Test OAuth authorization URL generation."""

    def test_generate_authorization_url(self, oauth_config):
        """Should generate valid authorization URL."""
        client = OAuthClient(
            client_id=oauth_config["client_id"],
            client_secret=oauth_config["client_secret"],
            redirect_uri=oauth_config["redirect_uri"],
        )

        auth_url, state = client.get_authorization_url()

        assert auth_url is not None
        assert isinstance(auth_url, str)
        assert len(auth_url) > 0
        assert state is not None
        assert isinstance(state, str)
        assert len(state) > 0

    def test_authorization_url_contains_client_id(self, oauth_config):
        """Authorization URL should contain client_id."""
        client = OAuthClient(
            client_id=oauth_config["client_id"],
            client_secret=oauth_config["client_secret"],
            redirect_uri=oauth_config["redirect_uri"],
        )

        auth_url, _ = client.get_authorization_url()

        assert oauth_config["client_id"] in auth_url

    def test_authorization_url_contains_redirect_uri(self, oauth_config):
        """Authorization URL should contain redirect_uri."""
        client = OAuthClient(
            client_id=oauth_config["client_id"],
            client_secret=oauth_config["client_secret"],
            redirect_uri=oauth_config["redirect_uri"],
        )

        auth_url, _ = client.get_authorization_url()

        # URL encode check
        assert "redirect_uri" in auth_url
        assert "localhost" in auth_url

    def test_authorization_url_contains_scopes(self, oauth_config):
        """Authorization URL should request openid, email, and profile scopes."""
        client = OAuthClient(
            client_id=oauth_config["client_id"],
            client_secret=oauth_config["client_secret"],
            redirect_uri=oauth_config["redirect_uri"],
        )

        auth_url, _ = client.get_authorization_url()

        # Check for required scopes
        assert "scope" in auth_url
        assert "openid" in auth_url
        assert "email" in auth_url
        assert "profile" in auth_url

    def test_authorization_url_contains_state(self, oauth_config):
        """Authorization URL should contain state parameter for CSRF protection."""
        client = OAuthClient(
            client_id=oauth_config["client_id"],
            client_secret=oauth_config["client_secret"],
            redirect_uri=oauth_config["redirect_uri"],
        )

        auth_url, state = client.get_authorization_url()

        assert "state=" in auth_url
        assert state in auth_url

    def test_state_is_random(self, oauth_config):
        """Each authorization URL should have unique state."""
        client = OAuthClient(
            client_id=oauth_config["client_id"],
            client_secret=oauth_config["client_secret"],
            redirect_uri=oauth_config["redirect_uri"],
        )

        _, state1 = client.get_authorization_url()
        _, state2 = client.get_authorization_url()

        assert state1 != state2

    def test_authorization_url_points_to_google(self, oauth_config):
        """Authorization URL should point to Google's OAuth endpoint."""
        client = OAuthClient(
            client_id=oauth_config["client_id"],
            client_secret=oauth_config["client_secret"],
            redirect_uri=oauth_config["redirect_uri"],
        )

        auth_url, _ = client.get_authorization_url()

        assert auth_url.startswith("https://accounts.google.com/o/oauth2")

    def test_custom_scopes(self, oauth_config):
        """Should allow custom scopes."""
        client = OAuthClient(
            client_id=oauth_config["client_id"],
            client_secret=oauth_config["client_secret"],
            redirect_uri=oauth_config["redirect_uri"],
            scopes=["openid", "email"],  # No profile
        )

        auth_url, _ = client.get_authorization_url()

        assert "email" in auth_url
        # Profile might not be explicitly in URL if not requested
