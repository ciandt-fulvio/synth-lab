"""
Integration tests for Materials API endpoints.

Tests the full material upload flow from API request to response.

References:
    - Materials Router: src/synth_lab/api/routers/materials.py
    - Material Service: src/synth_lab/services/material_service.py
    - Spec: specs/001-experiment-materials/spec.md
"""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from synth_lab.api.main import app

# Import all ORM models to register them with SQLAlchemy
import synth_lab.models.orm  # noqa: F401
from synth_lab.models.orm.experiment import Experiment


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def create_test_experiment(experiment_id: str, name: str = "Test Experiment"):
    """Helper to create experiment with all required fields including timestamps."""
    return Experiment(
        id=experiment_id,
        name=name,
        hypothesis="Test hypothesis",
        description="Test",
        status="draft",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def create_test_material(material_id: str, experiment_id: str, **kwargs):
    """Helper to create material with all required fields including timestamps."""
    from synth_lab.models.orm.material import ExperimentMaterial

    defaults = {
        "id": material_id,
        "experiment_id": experiment_id,
        "file_type": "image",
        "file_url": "https://s3.com/file.png",
        "file_name": "test.png",
        "file_size": 1000000,
        "mime_type": "image/png",
        "material_type": "design",
        "description_status": "pending",
        "display_order": 0,
        "created_at": datetime.now(timezone.utc),
    }
    defaults.update(kwargs)
    return ExperimentMaterial(**defaults)


class TestUploadUrlEndpoint:
    """Integration tests for POST /upload-url endpoint (T016)."""

    @patch("synth_lab.services.material_service.generate_upload_url")
    @patch("synth_lab.services.material_service.generate_material_id")
    def test_request_upload_url_returns_presigned_url(
        self, mock_gen_id, mock_gen_url, client, db_session
    ):
        """Should return presigned URL for valid file upload request."""
        # Create test experiment
        experiment = create_test_experiment("exp_abc12345")
        db_session.add(experiment)
        db_session.commit()

        # Setup mocks
        mock_gen_id.return_value = "mat_a1b2c3d4e5f6"
        mock_gen_url.return_value = "https://presigned-upload-url.com"

        response = client.post(
            "/api/experiments/exp_abc12345/materials/upload-url",
            json={
                "file_name": "test.png",
                "file_size": 1024000,
                "mime_type": "image/png",
                "material_type": "design",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["material_id"] == "mat_a1b2c3d4e5f6"
        assert data["upload_url"] == "https://presigned-upload-url.com"
        assert "object_key" in data
        assert "expires_in" in data

    @patch("synth_lab.services.material_service.generate_upload_url")
    @patch("synth_lab.services.material_service.generate_material_id")
    def test_rejects_unsupported_file_type(
        self, mock_gen_id, mock_gen_url, client, db_session
    ):
        """Should return 400 for unsupported file types."""
        # Create test experiment
        experiment = create_test_experiment("exp_11223344")
        db_session.add(experiment)
        db_session.commit()

        response = client.post(
            "/api/experiments/exp_11223344/materials/upload-url",
            json={
                "file_name": "malware.exe",
                "file_size": 1000000,
                "mime_type": "application/x-msdownload",
                "material_type": "other",
            },
        )

        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]

    @patch("synth_lab.services.material_service.generate_upload_url")
    @patch("synth_lab.services.material_service.generate_material_id")
    def test_rejects_file_too_large(
        self, mock_gen_id, mock_gen_url, client, db_session
    ):
        """Should return 400 when file exceeds size limit."""
        # Create test experiment
        experiment = create_test_experiment("exp_22334455")
        db_session.add(experiment)
        db_session.commit()

        response = client.post(
            "/api/experiments/exp_22334455/materials/upload-url",
            json={
                "file_name": "huge.png",
                "file_size": 30_000_000,  # 30MB, exceeds 25MB limit
                "mime_type": "image/png",
                "material_type": "design",
            },
        )

        assert response.status_code == 400
        assert "too large" in response.json()["detail"].lower()

    @patch("synth_lab.services.material_service.generate_upload_url")
    @patch("synth_lab.services.material_service.generate_material_id")
    def test_rejects_when_material_count_limit_reached(
        self, mock_gen_id, mock_gen_url, client, db_session
    ):
        """Should return 400 when experiment has 10 materials already."""
        from synth_lab.models.orm.material import ExperimentMaterial

        # Create test experiment
        experiment = create_test_experiment("exp_33445566")
        db_session.add(experiment)
        db_session.commit()

        # Add 10 materials (max limit)
        for i in range(10):
            material = create_test_material(
                f"mat_{i:012x}",
                "exp_33445566",
                file_url=f"https://s3.com/file{i}.png",
                file_name=f"file{i}.png",
                display_order=i,
            )
            db_session.add(material)
        db_session.commit()

        mock_gen_id.return_value = "mat_aabbccddeeff"
        mock_gen_url.return_value = "https://presigned.com"

        response = client.post(
            "/api/experiments/exp_33445566/materials/upload-url",
            json={
                "file_name": "test.png",
                "file_size": 1000000,
                "mime_type": "image/png",
                "material_type": "design",
            },
        )

        assert response.status_code == 400
        assert "maximum" in response.json()["detail"].lower()


class TestConfirmEndpoint:
    """Integration tests for POST /confirm endpoint (T017)."""

    @patch("synth_lab.services.material_service.check_object_exists")
    def test_confirm_upload_updates_material(
        self, mock_check_exists, client, db_session
    ):
        """Should confirm upload and return updated material."""
        from synth_lab.models.orm.material import ExperimentMaterial

        # Create test experiment
        experiment = create_test_experiment("exp_44556677")
        db_session.add(experiment)

        # Create pending material
        material = ExperimentMaterial(
            id="mat_fedcba987654",
            experiment_id="exp_44556677",
            file_type="image",
            file_url="",  # Empty until confirmed
            file_name="test.png",
            file_size=1024000,
            mime_type="image/png",
            material_type="design",
            description_status="pending",
            display_order=0,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(material)
        db_session.commit()

        # Mock S3 existence check
        mock_check_exists.return_value = True

        # Mock thumbnail and description generation
        with patch("synth_lab.services.material_service.MaterialService.generate_thumbnail"):
            with patch("synth_lab.services.material_service.MaterialService.generate_description"):
                response = client.post(
                    "/api/experiments/exp_44556677/materials/confirm",
                    json={
                        "material_id": "mat_fedcba987654",
                        "object_key": "materials/exp_44556677/mat_fedcba987654.png",
                    },
                )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "mat_fedcba987654"
        assert data["experiment_id"] == "exp_44556677"
        assert data["file_url"] != ""  # Should be updated
        assert "materials/exp_44556677/mat_fedcba987654.png" in data["file_url"]

    @patch("synth_lab.services.material_service.check_object_exists")
    def test_confirm_fails_if_material_not_found(
        self, mock_check_exists, client, db_session
    ):
        """Should return 404 if material doesn't exist."""
        # Create test experiment
        experiment = create_test_experiment("exp_55667788")
        db_session.add(experiment)
        db_session.commit()

        response = client.post(
            "/api/experiments/exp_55667788/materials/confirm",
            json={
                "material_id": "mat_000000000000",
                "object_key": "materials/exp_55667788/mat_000000000000.png",
            },
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch("synth_lab.services.material_service.check_object_exists")
    def test_confirm_fails_if_object_not_in_s3(
        self, mock_check_exists, client, db_session
    ):
        """Should return 400 if S3 object doesn't exist."""
        from synth_lab.models.orm.material import ExperimentMaterial

        # Create test experiment
        experiment = create_test_experiment("exp_66778899")
        db_session.add(experiment)

        # Create pending material
        material = ExperimentMaterial(
            id="mat_112233445566",
            experiment_id="exp_66778899",
            file_type="image",
            file_url="",
            file_name="test.png",
            file_size=1024000,
            mime_type="image/png",
            material_type="design",
            description_status="pending",
            display_order=0,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(material)
        db_session.commit()

        # Mock S3 existence check to return False
        mock_check_exists.return_value = False

        response = client.post(
            "/api/experiments/exp_66778899/materials/confirm",
            json={
                "material_id": "mat_112233445566",
                "object_key": "materials/exp_66778899/mat_112233445566.png",
            },
        )

        assert response.status_code == 400
        assert "not found in s3" in response.json()["detail"].lower()

    @patch("synth_lab.services.material_service.check_object_exists")
    def test_confirm_fails_if_experiment_mismatch(
        self, mock_check_exists, client, db_session
    ):
        """Should return 400 if material doesn't belong to experiment."""
        from synth_lab.models.orm.material import ExperimentMaterial

        # Create test experiments
        experiment1 = create_test_experiment("exp_77889900", "Test Experiment 1")
        experiment2 = create_test_experiment("exp_00998877", "Test Experiment 2")
        db_session.add(experiment1)
        db_session.add(experiment2)

        # Create material for experiment1
        material = ExperimentMaterial(
            id="mat_223344556677",
            experiment_id="exp_77889900",
            file_type="image",
            file_url="",
            file_name="test.png",
            file_size=1024000,
            mime_type="image/png",
            material_type="design",
            description_status="pending",
            display_order=0,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(material)
        db_session.commit()

        # Try to confirm with wrong experiment
        response = client.post(
            "/api/experiments/exp_00998877/materials/confirm",
            json={
                "material_id": "mat_223344556677",
                "object_key": "materials/exp_77889900/mat_223344556677.png",
            },
        )

        assert response.status_code == 400
        assert "does not belong" in response.json()["detail"].lower()


class TestListMaterialsEndpoint:
    """Integration tests for GET /materials endpoint."""

    def test_list_materials_returns_empty_list(self, client, db_session):
        """Should return empty list for experiment with no materials."""
        # Create test experiment
        experiment = create_test_experiment("exp_aabbccdd")
        db_session.add(experiment)
        db_session.commit()

        response = client.get("/api/experiments/exp_aabbccdd/materials")

        assert response.status_code == 200
        data = response.json()
        assert data["materials"] == []
        assert data["total"] == 0
        assert data["total_size"] == 0

    def test_list_materials_returns_materials_in_order(self, client, db_session):
        """Should return materials ordered by display_order."""
        from synth_lab.models.orm.material import ExperimentMaterial

        # Create test experiment
        experiment = create_test_experiment("exp_ddeeffaa")
        db_session.add(experiment)
        db_session.commit()

        # Add materials in non-sequential order
        materials_data = [
            ("mat_111111111111", "file2.png", 2),
            ("mat_222222222222", "file0.png", 0),
            ("mat_333333333333", "file1.png", 1),
        ]

        for mat_id, filename, order in materials_data:
            material = ExperimentMaterial(
                id=mat_id,
                experiment_id="exp_ddeeffaa",
                file_type="image",
                file_url=f"https://s3.com/{filename}",
                file_name=filename,
                file_size=1000000,
                mime_type="image/png",
                material_type="design",
                description_status="completed",
                display_order=order,
            created_at=datetime.now(timezone.utc),
            )
            db_session.add(material)
        db_session.commit()

        response = client.get("/api/experiments/exp_ddeeffaa/materials")

        assert response.status_code == 200
        data = response.json()
        assert len(data["materials"]) == 3
        assert data["total"] == 3
        # Should be ordered by display_order
        assert data["materials"][0]["file_name"] == "file0.png"
        assert data["materials"][1]["file_name"] == "file1.png"
        assert data["materials"][2]["file_name"] == "file2.png"


class TestGetViewUrlEndpoint:
    """Integration tests for GET /materials/{material_id}/view-url endpoint (T037)."""

    @patch("synth_lab.services.material_service.generate_view_url")
    def test_get_view_url_returns_presigned_urls(
        self, mock_gen_view_url, client, db_session
    ):
        """Should return presigned URLs for viewing material and thumbnail."""
        from synth_lab.models.orm.material import ExperimentMaterial

        # Create test experiment
        experiment = create_test_experiment("exp_view1234")
        db_session.add(experiment)

        # Create material with file and thumbnail
        material = ExperimentMaterial(
            id="mat_view12345678",
            experiment_id="exp_view1234",
            file_type="image",
            file_url="https://s3.com/bucket/materials/exp_view1234/mat_view12345678.png",
            thumbnail_url="https://s3.com/bucket/thumbnails/exp_view1234/mat_view12345678.png",
            file_name="test.png",
            file_size=1024000,
            mime_type="image/png",
            material_type="design",
            description_status="completed",
            display_order=0,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(material)
        db_session.commit()

        # Mock presigned URL generation
        mock_gen_view_url.side_effect = [
            "https://presigned-view-url.com",
            "https://presigned-thumb-url.com",
        ]

        response = client.get(
            "/api/experiments/exp_view1234/materials/mat_view12345678/view-url"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["material_id"] == "mat_view12345678"
        assert data["view_url"] == "https://presigned-view-url.com"
        assert data["thumbnail_url"] == "https://presigned-thumb-url.com"
        assert "expires_in" in data

    def test_get_view_url_returns_404_for_nonexistent_material(
        self, client, db_session
    ):
        """Should return 404 if material doesn't exist."""
        # Create test experiment
        experiment = create_test_experiment("exp_view5678")
        db_session.add(experiment)
        db_session.commit()

        response = client.get(
            "/api/experiments/exp_view5678/materials/mat_000000000000/view-url"
        )

        assert response.status_code == 404

    @patch("synth_lab.services.material_service.generate_view_url")
    def test_get_view_url_works_without_thumbnail(
        self, mock_gen_view_url, client, db_session
    ):
        """Should work even if material doesn't have thumbnail."""
        from synth_lab.models.orm.material import ExperimentMaterial

        # Create test experiment
        experiment = create_test_experiment("exp_view9abc")
        db_session.add(experiment)

        # Create material WITHOUT thumbnail
        material = ExperimentMaterial(
            id="mat_view9abcdef0",
            experiment_id="exp_view9abc",
            file_type="document",
            file_url="https://s3.com/bucket/materials/exp_view9abc/mat_view9abcdef0.pdf",
            thumbnail_url=None,  # No thumbnail
            file_name="test.pdf",
            file_size=500000,
            mime_type="application/pdf",
            material_type="spec",
            description_status="pending",
            display_order=0,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(material)
        db_session.commit()

        # Mock presigned URL generation (only for file, not thumbnail)
        mock_gen_view_url.return_value = "https://presigned-view-url.com"

        response = client.get(
            "/api/experiments/exp_view9abc/materials/mat_view9abcdef0/view-url"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["view_url"] == "https://presigned-view-url.com"
        assert data["thumbnail_url"] is None  # Should be None


class TestDeleteMaterialEndpoint:
    """Integration tests for DELETE /materials/{material_id} endpoint."""

    @patch("synth_lab.services.material_service.delete_object")
    def test_delete_material_removes_from_database(
        self, mock_delete, client, db_session
    ):
        """Should delete material from database and S3."""
        from synth_lab.models.orm.material import ExperimentMaterial

        # Create test experiment
        experiment = create_test_experiment("exp_eeaabbcc")
        db_session.add(experiment)

        # Create material
        material = ExperimentMaterial(
            id="mat_445566778899",
            experiment_id="exp_eeaabbcc",
            file_type="image",
            file_url="https://s3.com/bucket/file.png",
            file_name="test.png",
            file_size=1024000,
            mime_type="image/png",
            material_type="design",
            description_status="completed",
            display_order=0,
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(material)
        db_session.commit()

        response = client.delete(
            "/api/experiments/exp_eeaabbcc/materials/mat_445566778899"
        )

        assert response.status_code == 204

        # Verify material is deleted
        deleted_material = (
            db_session.query(ExperimentMaterial)
            .filter_by(id="mat_445566778899")
            .first()
        )
        assert deleted_material is None

    def test_delete_nonexistent_material_returns_404(self, client, db_session):
        """Should return 404 for nonexistent material."""
        # Create test experiment
        experiment = create_test_experiment("exp_ffeeddcc")
        db_session.add(experiment)
        db_session.commit()

        response = client.delete(
            "/api/experiments/exp_ffeeddcc/materials/mat_000000000000"
        )

        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
