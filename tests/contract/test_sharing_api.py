"""Contract tests for sharing API endpoints.

Tests sharing endpoints match the new email-based sharing API contract.
Uses MagicMock for service layer isolation.
"""
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from synth_lab.api.main import app
from synth_lab.api.routers.auth import get_sharing_service

# Test user constant - matches conftest.py
TEST_USER_ID = "00000001-0000-0000-0000-000000000001"


@pytest.fixture
def unauthenticated_client():
    """Create test client WITHOUT authentication."""
    return TestClient(app)


@pytest.fixture
def authenticated_client(auth_token):
    """Create test client WITH authentication."""
    client = TestClient(app)
    client.cookies.set("auth_token", auth_token)
    return client


@pytest.fixture
def mock_sharing_service():
    """Create a mock sharing service with new email-based methods."""
    mock_service = MagicMock()
    mock_service.share_experiment_by_email = MagicMock()
    mock_service.revoke_experiment_share = MagicMock()
    mock_service.list_experiment_shares = MagicMock(
        return_value={"shares": [], "pending": []}
    )
    mock_service.share_synth_group_by_email = MagicMock()
    mock_service.revoke_synth_group_share = MagicMock()
    mock_service.list_synth_group_shares = MagicMock(
        return_value={"shares": [], "pending": []}
    )
    mock_service.accept_pending_invites = MagicMock(return_value=0)
    return mock_service


@pytest.fixture
def authenticated_client_with_mock_service(auth_token, mock_sharing_service):
    """Create authenticated client with mocked sharing service dependency."""
    def override_get_sharing_service():
        return mock_sharing_service

    app.dependency_overrides[get_sharing_service] = override_get_sharing_service

    client = TestClient(app)
    client.cookies.set("auth_token", auth_token)

    yield client, mock_sharing_service

    app.dependency_overrides.clear()


# =============================================================================
# Experiment Sharing API
# =============================================================================


class TestExperimentSharesEndpoints:
    """Test experiment sharing endpoints."""

    def test_post_experiment_share_requires_auth(self, unauthenticated_client):
        """Should return 401 if not authenticated."""
        response = unauthenticated_client.post(
            "/auth/experiments/exp_12345678/shares",
            json={"email": "test@example.com"},
        )
        assert response.status_code == 401

    def test_post_experiment_share_creates_share(
        self, authenticated_client_with_mock_service
    ):
        """Should create share and return result."""
        client, mock_service = authenticated_client_with_mock_service

        mock_service.share_experiment_by_email.return_value = {
            "status": "shared",
            "email": "sharee@example.com",
            "permission_level": "editor",
            "share_id": "abc-123",
            "user_id": "user-456",
            "granted_at": "2026-01-01T00:00:00",
        }

        response = client.post(
            "/auth/experiments/exp_12345678/shares",
            json={"email": "sharee@example.com"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "shared"
        assert data["email"] == "sharee@example.com"
        assert data["permission_level"] == "editor"

    def test_post_experiment_share_creates_pending_invite(
        self, authenticated_client_with_mock_service
    ):
        """Should create pending invite for non-registered user."""
        client, mock_service = authenticated_client_with_mock_service

        mock_service.share_experiment_by_email.return_value = {
            "status": "pending",
            "email": "new@example.com",
            "permission_level": "editor",
            "invite_id": "inv-789",
            "created_at": "2026-01-01T00:00:00",
        }

        response = client.post(
            "/auth/experiments/exp_12345678/shares",
            json={"email": "new@example.com"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert data["email"] == "new@example.com"

    def test_post_experiment_share_rejects_invalid_email(
        self, authenticated_client_with_mock_service
    ):
        """Should return 422 for invalid email."""
        client, _ = authenticated_client_with_mock_service

        response = client.post(
            "/auth/experiments/exp_12345678/shares",
            json={"email": "not-an-email"},
        )
        assert response.status_code == 422

    def test_post_experiment_share_rejects_already_shared(
        self, authenticated_client_with_mock_service
    ):
        """Should return 400 if already shared."""
        client, mock_service = authenticated_client_with_mock_service
        mock_service.share_experiment_by_email.side_effect = ValueError(
            "Experiment already shared with test@example.com"
        )

        response = client.post(
            "/auth/experiments/exp_12345678/shares",
            json={"email": "test@example.com"},
        )
        assert response.status_code == 400

    def test_get_experiment_shares_requires_auth(self, unauthenticated_client):
        """Should return 401 if not authenticated."""
        response = unauthenticated_client.get(
            "/auth/experiments/exp_12345678/shares"
        )
        assert response.status_code == 401

    def test_get_experiment_shares_returns_list(
        self, authenticated_client_with_mock_service
    ):
        """Should return shares and pending invites."""
        client, mock_service = authenticated_client_with_mock_service

        mock_service.list_experiment_shares.return_value = {
            "shares": [
                {
                    "share_id": "s1",
                    "user_id": "u1",
                    "email": "active@example.com",
                    "display_name": "Active User",
                    "profile_picture_url": None,
                    "permission_level": "editor",
                    "granted_at": "2026-01-01T00:00:00",
                    "status": "active",
                }
            ],
            "pending": [
                {
                    "invite_id": "i1",
                    "email": "pending@example.com",
                    "permission_level": "editor",
                    "created_at": "2026-01-01T00:00:00",
                    "status": "pending",
                }
            ],
        }

        response = client.get("/auth/experiments/exp_12345678/shares")

        assert response.status_code == 200
        data = response.json()
        assert data["resource_id"] == "exp_12345678"
        assert len(data["shares"]) == 1
        assert data["shares"][0]["status"] == "active"
        assert len(data["pending"]) == 1
        assert data["pending"][0]["status"] == "pending"

    def test_delete_experiment_share_requires_auth(self, unauthenticated_client):
        """Should return 401 if not authenticated."""
        response = unauthenticated_client.delete(
            "/auth/experiments/exp_12345678/shares?email=test@example.com"
        )
        assert response.status_code == 401

    def test_delete_experiment_share_revokes_access(
        self, authenticated_client_with_mock_service
    ):
        """Should revoke access and return 200."""
        client, mock_service = authenticated_client_with_mock_service
        mock_service.revoke_experiment_share.return_value = True

        response = client.delete(
            "/auth/experiments/exp_12345678/shares?email=test@example.com"
        )

        assert response.status_code == 200
        assert "message" in response.json()

    def test_delete_experiment_share_returns_404_if_not_found(
        self, authenticated_client_with_mock_service
    ):
        """Should return 404 if share doesn't exist."""
        client, mock_service = authenticated_client_with_mock_service
        mock_service.revoke_experiment_share.return_value = False

        response = client.delete(
            "/auth/experiments/exp_12345678/shares?email=test@example.com"
        )
        assert response.status_code == 404


# =============================================================================
# SynthGroup Sharing API
# =============================================================================


class TestSynthGroupSharesEndpoints:
    """Test synth_group sharing endpoints."""

    def test_post_synth_group_share_requires_auth(self, unauthenticated_client):
        """Should return 401 if not authenticated."""
        response = unauthenticated_client.post(
            "/auth/synth-groups/grp_abcd1234/shares",
            json={"email": "test@example.com"},
        )
        assert response.status_code == 401

    def test_post_synth_group_share_creates_share(
        self, authenticated_client_with_mock_service
    ):
        """Should create synth_group share and return result."""
        client, mock_service = authenticated_client_with_mock_service

        mock_service.share_synth_group_by_email.return_value = {
            "status": "shared",
            "email": "sharee@example.com",
            "permission_level": "editor",
            "share_id": "abc-123",
            "user_id": "user-456",
            "granted_at": "2026-01-01T00:00:00",
        }

        response = client.post(
            "/auth/synth-groups/grp_abcd1234/shares",
            json={"email": "sharee@example.com"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "shared"
        assert data["email"] == "sharee@example.com"

    def test_get_synth_group_shares_requires_auth(self, unauthenticated_client):
        """Should return 401 if not authenticated."""
        response = unauthenticated_client.get(
            "/auth/synth-groups/grp_abcd1234/shares"
        )
        assert response.status_code == 401

    def test_get_synth_group_shares_returns_list(
        self, authenticated_client_with_mock_service
    ):
        """Should return list of shares."""
        client, mock_service = authenticated_client_with_mock_service

        mock_service.list_synth_group_shares.return_value = {
            "shares": [],
            "pending": [],
        }

        response = client.get("/auth/synth-groups/grp_abcd1234/shares")

        assert response.status_code == 200
        data = response.json()
        assert "shares" in data
        assert "pending" in data

    def test_delete_synth_group_share_requires_auth(self, unauthenticated_client):
        """Should return 401 if not authenticated."""
        response = unauthenticated_client.delete(
            "/auth/synth-groups/grp_abcd1234/shares?email=test@example.com"
        )
        assert response.status_code == 401

    def test_delete_synth_group_share_revokes_access(
        self, authenticated_client_with_mock_service
    ):
        """Should revoke access and return 200."""
        client, mock_service = authenticated_client_with_mock_service
        mock_service.revoke_synth_group_share.return_value = True

        response = client.delete(
            "/auth/synth-groups/grp_abcd1234/shares?email=test@example.com"
        )

        assert response.status_code == 200
        assert "message" in response.json()

    def test_delete_synth_group_share_returns_404_if_not_found(
        self, authenticated_client_with_mock_service
    ):
        """Should return 404 if share doesn't exist."""
        client, mock_service = authenticated_client_with_mock_service
        mock_service.revoke_synth_group_share.return_value = False

        response = client.delete(
            "/auth/synth-groups/grp_abcd1234/shares?email=test@example.com"
        )
        assert response.status_code == 404
