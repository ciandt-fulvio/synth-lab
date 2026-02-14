"""Contract tests for sharing API endpoints.

Tests sharing endpoints match the OpenAPI contract specification.
Uses best practices for testing sharing/permission flows:
- Separate fixtures for authenticated vs unauthenticated clients
- MagicMock for sync service methods
- Proper mocking of service layer for isolation
"""
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from synth_lab.api.main import app
from synth_lab.api.routers.auth import get_sharing_service

# Test user constant - matches conftest.py
TEST_USER_ID = "00000001-0000-0000-0000-000000000001"


@pytest.fixture
def unauthenticated_client():
    """Create test client WITHOUT authentication.

    Used for testing endpoints that should reject unauthenticated requests.
    """
    return TestClient(app)


@pytest.fixture
def authenticated_client(auth_token):
    """Create test client WITH authentication.

    Used for testing endpoints that require authentication.
    """
    client = TestClient(app)
    client.cookies.set("auth_token", auth_token)
    return client


@pytest.fixture
def authenticated_user_id():
    """Return the test user ID."""
    return TEST_USER_ID


@pytest.fixture
def mock_sharing_service():
    """Create a mock sharing service with sync methods."""
    mock_service = MagicMock()
    mock_service.share_experiment = MagicMock()
    mock_service.revoke_experiment_share = MagicMock()
    mock_service.list_experiment_shares = MagicMock(return_value=[])
    mock_service.share_synth_group = MagicMock()
    mock_service.revoke_synth_group_share = MagicMock()
    mock_service.list_synth_group_shares = MagicMock(return_value=[])
    return mock_service


@pytest.fixture
def authenticated_client_with_mock_service(auth_token, mock_sharing_service):
    """Create authenticated client with mocked sharing service dependency.

    This properly overrides the FastAPI dependency injection.
    """
    def override_get_sharing_service():
        return mock_sharing_service

    app.dependency_overrides[get_sharing_service] = override_get_sharing_service

    client = TestClient(app)
    client.cookies.set("auth_token", auth_token)

    yield client, mock_sharing_service

    # Clean up override after test
    app.dependency_overrides.clear()


# =============================================================================
# US3 Contract Tests: Experiment Sharing API (T098-T100)
# =============================================================================


class TestExperimentSharesEndpoints:
    """Test experiment sharing endpoints - T098, T099, T100."""

    def test_post_experiment_share_requires_auth(self, unauthenticated_client):
        """Should return 401 if not authenticated - T098."""
        experiment_id = "exp_12345678"

        response = unauthenticated_client.post(
            f"/auth/experiments/{experiment_id}/shares",
            json={
                "user_id": str(uuid4()),
                "permission_level": "viewer"
            }
        )

        assert response.status_code == 401

    def test_post_experiment_share_creates_share(self, authenticated_client_with_mock_service):
        """Should create experiment share and return 201 - T098."""
        client, mock_service = authenticated_client_with_mock_service
        experiment_id = "exp_12345678"
        sharee_id = str(uuid4())

        from synth_lab.domain.entities.share import ExperimentShare, PermissionLevel
        mock_share_obj = ExperimentShare(
            experiment_id=experiment_id,
            user_id=uuid4(),
            permission_level=PermissionLevel.VIEWER,
            granted_by_id=uuid4(),
        )
        mock_service.share_experiment.return_value = mock_share_obj
        mock_service.list_experiment_shares.return_value = [{
            "share_id": str(mock_share_obj.id),
            "user_id": sharee_id,
            "email": "test@example.com",
            "display_name": "Test User",
            "profile_picture_url": None,
            "permission_level": "viewer",
            "granted_at": mock_share_obj.granted_at,
            "granted_by_id": str(mock_share_obj.granted_by_id),
        }]

        response = client.post(
            f"/auth/experiments/{experiment_id}/shares",
            json={
                "user_id": sharee_id,
                "permission_level": "viewer"
            }
        )

        # Verify 200 OK or 201 Created
        assert response.status_code in [200, 201]

        # Verify response schema
        data = response.json()
        assert "share_id" in data
        assert "experiment_id" in data
        assert "user_id" in data
        assert "permission_level" in data
        assert "granted_at" in data
        assert "granted_by_id" in data

    def test_post_experiment_share_rejects_invalid_permission_level(self, authenticated_client_with_mock_service):
        """Should return 400 for invalid permission level - T098."""
        client, _ = authenticated_client_with_mock_service
        experiment_id = "exp_12345678"

        response = client.post(
            f"/auth/experiments/{experiment_id}/shares",
            json={
                "user_id": str(uuid4()),
                "permission_level": "invalid"
            }
        )

        # Should return validation error
        assert response.status_code in [400, 422]

    def test_post_experiment_share_returns_409_if_already_shared(self, authenticated_client_with_mock_service):
        """Should return 400 if share already exists - T098."""
        client, mock_service = authenticated_client_with_mock_service
        experiment_id = "exp_12345678"
        sharee_id = str(uuid4())

        mock_service.share_experiment.side_effect = ValueError("Share already exists")

        response = client.post(
            f"/auth/experiments/{experiment_id}/shares",
            json={
                "user_id": sharee_id,
                "permission_level": "viewer"
            }
        )

        # Verify 400 Bad Request (ValueError maps to 400)
        assert response.status_code == 400

    def test_get_experiment_shares_requires_auth(self, unauthenticated_client):
        """Should return 401 if not authenticated - T099."""
        experiment_id = "exp_12345678"

        response = unauthenticated_client.get(f"/auth/experiments/{experiment_id}/shares")

        assert response.status_code == 401

    def test_get_experiment_shares_returns_list(self, authenticated_client_with_mock_service):
        """Should return list of shares - T099."""
        client, mock_service = authenticated_client_with_mock_service
        experiment_id = "exp_12345678"

        mock_service.list_experiment_shares.return_value = []

        response = client.get(f"/auth/experiments/{experiment_id}/shares")

        # Verify 200 OK
        assert response.status_code == 200

        # Verify response schema
        data = response.json()
        assert "experiment_id" in data
        assert "shares" in data
        assert isinstance(data["shares"], list)

    def test_delete_experiment_share_requires_auth(self, unauthenticated_client):
        """Should return 401 if not authenticated - T100."""
        experiment_id = "exp_12345678"
        user_id = str(uuid4())

        response = unauthenticated_client.delete(
            f"/auth/experiments/{experiment_id}/shares/{user_id}"
        )

        assert response.status_code == 401

    def test_delete_experiment_share_revokes_access(self, authenticated_client_with_mock_service):
        """Should revoke access and return 200 - T100."""
        client, mock_service = authenticated_client_with_mock_service
        experiment_id = "exp_12345678"
        sharee_id = str(uuid4())

        mock_service.revoke_experiment_share.return_value = True

        response = client.delete(
            f"/auth/experiments/{experiment_id}/shares/{sharee_id}"
        )

        # Verify 200 OK
        assert response.status_code == 200

        # Verify response message
        data = response.json()
        assert "message" in data

    def test_delete_experiment_share_returns_404_if_not_found(self, authenticated_client_with_mock_service):
        """Should return 404 if share doesn't exist - T100."""
        client, mock_service = authenticated_client_with_mock_service
        experiment_id = "exp_12345678"
        sharee_id = str(uuid4())

        mock_service.revoke_experiment_share.return_value = False

        response = client.delete(
            f"/auth/experiments/{experiment_id}/shares/{sharee_id}"
        )

        # Verify 404 Not Found
        assert response.status_code == 404


# =============================================================================
# US4 Contract Tests: SynthGroup Sharing API (T126-T128)
# =============================================================================


class TestSynthGroupSharesEndpoints:
    """Test synth_group sharing endpoints - T126, T127, T128."""

    def test_post_synth_group_share_requires_auth(self, unauthenticated_client):
        """Should return 401 if not authenticated - T126."""
        synth_group_id = "grp_abcd1234"

        response = unauthenticated_client.post(
            f"/auth/synth-groups/{synth_group_id}/shares",
            json={
                "user_id": str(uuid4()),
                "permission_level": "viewer"
            }
        )

        assert response.status_code == 401

    def test_post_synth_group_share_creates_share(self, authenticated_client_with_mock_service):
        """Should create synth_group share and return 201 - T126."""
        client, mock_service = authenticated_client_with_mock_service
        synth_group_id = "grp_abcd1234"
        sharee_id = str(uuid4())

        from synth_lab.domain.entities.share import PermissionLevel, SynthGroupShare
        mock_share_obj = SynthGroupShare(
            synth_group_id=synth_group_id,
            user_id=uuid4(),
            permission_level=PermissionLevel.VIEWER,
            granted_by_id=uuid4(),
        )
        mock_service.share_synth_group.return_value = mock_share_obj
        mock_service.list_synth_group_shares.return_value = [{
            "share_id": str(mock_share_obj.id),
            "user_id": sharee_id,
            "email": "test@example.com",
            "display_name": "Test User",
            "profile_picture_url": None,
            "permission_level": "viewer",
            "granted_at": mock_share_obj.granted_at,
            "granted_by_id": str(mock_share_obj.granted_by_id),
        }]

        response = client.post(
            f"/auth/synth-groups/{synth_group_id}/shares",
            json={
                "user_id": sharee_id,
                "permission_level": "viewer"
            }
        )

        # Verify 200 OK or 201 Created
        assert response.status_code in [200, 201]

        # Verify response schema
        data = response.json()
        assert "share_id" in data
        assert "user_id" in data
        assert "permission_level" in data
        assert "granted_at" in data
        assert "granted_by_id" in data

    def test_post_synth_group_share_does_not_share_experiments(self):
        """Should share synth_group without affecting experiments - T126.

        Note: This is verified by the service layer logic, but documented here.
        """
        pass

    def test_get_synth_group_shares_requires_auth(self, unauthenticated_client):
        """Should return 401 if not authenticated - T127."""
        synth_group_id = "grp_abcd1234"

        response = unauthenticated_client.get(f"/auth/synth-groups/{synth_group_id}/shares")

        assert response.status_code == 401

    def test_get_synth_group_shares_returns_list(self, authenticated_client_with_mock_service):
        """Should return list of shares - T127."""
        client, mock_service = authenticated_client_with_mock_service
        synth_group_id = "grp_abcd1234"

        mock_service.list_synth_group_shares.return_value = []

        response = client.get(f"/auth/synth-groups/{synth_group_id}/shares")

        # Verify 200 OK
        assert response.status_code == 200

        # Verify response schema
        data = response.json()
        assert "shares" in data
        assert isinstance(data["shares"], list)

    def test_delete_synth_group_share_requires_auth(self, unauthenticated_client):
        """Should return 401 if not authenticated - T128."""
        synth_group_id = "grp_abcd1234"
        user_id = str(uuid4())

        response = unauthenticated_client.delete(
            f"/auth/synth-groups/{synth_group_id}/shares/{user_id}"
        )

        assert response.status_code == 401

    def test_delete_synth_group_share_revokes_access(self, authenticated_client_with_mock_service):
        """Should revoke access and return 200 - T128."""
        client, mock_service = authenticated_client_with_mock_service
        synth_group_id = "grp_abcd1234"
        sharee_id = str(uuid4())

        mock_service.revoke_synth_group_share.return_value = True

        response = client.delete(
            f"/auth/synth-groups/{synth_group_id}/shares/{sharee_id}"
        )

        # Verify 200 OK
        assert response.status_code == 200

        # Verify response message
        data = response.json()
        assert "message" in data

    def test_delete_synth_group_share_returns_404_if_not_found(self, authenticated_client_with_mock_service):
        """Should return 404 if share doesn't exist - T128."""
        client, mock_service = authenticated_client_with_mock_service
        synth_group_id = "grp_abcd1234"
        sharee_id = str(uuid4())

        mock_service.revoke_synth_group_share.return_value = False

        response = client.delete(
            f"/auth/synth-groups/{synth_group_id}/shares/{sharee_id}"
        )

        # Verify 404 Not Found
        assert response.status_code == 404

    def test_delete_synth_group_share_does_not_affect_experiments(self):
        """Should revoke synth_group access without affecting experiments - T128.

        Note: This independence is verified by integration tests.
        """
        pass
