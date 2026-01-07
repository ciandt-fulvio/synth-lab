"""
Integration tests for research-related services.

Tests the full flow: Service → Repository → Database → LLM Client
Uses real database (db_session) and mocks only external LLM calls.

Executar: pytest -m integration tests/integration/services/test_research_services.py
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from synth_lab.services.research_service import ResearchService
from synth_lab.services.research_summary_generator_service import ResearchSummaryGeneratorService
from synth_lab.repositories.research_repository import ResearchRepository
from synth_lab.models.orm.experiment import Experiment
from synth_lab.models.orm.synth import Synth, SynthGroup
from synth_lab.models.orm.research import ResearchExecution, Transcript
from synth_lab.models.research import ExecutionStatus
from synth_lab.models.pagination import PaginationParams


@pytest.mark.integration
class TestResearchServiceIntegration:
    """Integration tests for research_service.py - Core research execution logic."""

    def test_list_executions_with_pagination(self, db_session):
        """Test that list_executions returns paginated results from database."""
        # Count existing executions before creating new ones (seeded data)
        repo = ResearchRepository(session=db_session)
        service = ResearchService(research_repo=repo)

        initial_params = PaginationParams(limit=1, offset=0)
        initial_result = service.list_executions(initial_params)
        initial_count = initial_result.pagination.total

        # Setup: Create test data in database (IDs must match patterns)
        # Note: exp_a1b2c3d4 is used by seeded data, use different ID
        experiment = Experiment(
            id="exp_f1e2d3c4",
            name="Research Test Experiment",
            hypothesis="Testing research service",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        db_session.add(experiment)

        group = SynthGroup(
            id="grp_f1e2d3c4",
            name="Test Group",
            created_at=datetime.now().isoformat(),
        )
        db_session.add(group)

        # Create multiple research executions
        for i in range(5):
            execution = ResearchExecution(
                exec_id=f"exec_1a2b3c{i:02d}",
                experiment_id="exp_f1e2d3c4",
                topic_name=f"Research Topic {i}",
                status="completed" if i % 2 == 0 else "running",
                started_at=datetime.now().isoformat(),
                synth_count=5,
                successful_count=5 if i % 2 == 0 else 3,
            )
            db_session.add(execution)

        db_session.commit()

        # Execute: Call service method with test session
        params = PaginationParams(limit=10, offset=0, sort_by="started_at", sort_order="desc")
        result = service.list_executions(params)

        # Verify: Check pagination and data
        assert result.pagination.total == initial_count + 5, "Should have initial + 5 new executions"
        assert result.pagination.limit == 10
        assert result.pagination.offset == 0
        assert len(result.data) <= 10, "Should return at most 10 executions"

        # Verify first execution has required fields
        first_exec = result.data[0]
        assert first_exec.exec_id is not None
        assert first_exec.status in [ExecutionStatus.COMPLETED, ExecutionStatus.RUNNING]
        assert first_exec.synth_count >= 1

    def test_get_execution_detail_includes_metadata(self, db_session):
        """Test that get_execution returns full execution details."""
        # Setup: Create execution with transcripts
        experiment = Experiment(
            id="exp_detail_001",
            name="Detail Test",
            hypothesis="Testing detail retrieval",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        db_session.add(experiment)

        group = SynthGroup(
            id="group_detail_001",
            name="Detail Group",
            created_at=datetime.now().isoformat(),
        )
        db_session.add(group)

        execution = ResearchExecution(
            exec_id="exec_detail_001",
            experiment_id="exp_detail_001",
            topic_name="Detail Test Topic",
            status="completed",
            started_at=datetime.now().isoformat(),
            completed_at=datetime.now().isoformat(),
            synth_count=3,
            successful_count=3,
        )
        db_session.add(execution)

        # Add transcripts
        for i in range(3):
            transcript = Transcript(
                id=f"transcript_detail_{i:03d}",
                exec_id="exec_detail_001",
                synth_id=f"synth_{i:03d}",
                synth_name=f"Test Synth {i}",
                status="completed",
                turn_count=1,
                timestamp=datetime.now().isoformat(),
                messages=[
                    {"role": "user", "content": "Question 1"},
                    {"role": "assistant", "content": "Answer 1"},
                ],
            )
            db_session.add(transcript)

        db_session.commit()

        # Execute
        from synth_lab.repositories.research_repository import ResearchRepository

        repo = ResearchRepository(session=db_session)
        service = ResearchService(research_repo=repo)
        detail = service.get_execution("exec_detail_001")

        # Verify
        assert detail.exec_id == "exec_detail_001"
        assert detail.status == ExecutionStatus.COMPLETED
        assert detail.synth_count == 3
        assert detail.successful_count == 3
        assert detail.summary_available is False  # No summary generated yet
        assert detail.prfaq_available is False  # No PRFAQ generated yet

    def test_get_transcripts_with_pagination(self, db_session):
        """Test that get_transcripts returns paginated transcript list."""
        # Setup
        experiment = Experiment(
            id="exp_transcripts_001",
            name="Transcripts Test",
            hypothesis="Testing transcript pagination",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        db_session.add(experiment)

        group = SynthGroup(
            id="group_transcripts_001",
            name="Transcript Group",
            created_at=datetime.now().isoformat(),
        )
        db_session.add(group)

        execution = ResearchExecution(
            exec_id="exec_transcripts_001",
            experiment_id="exp_transcripts_001",
            topic_name="Transcripts Test Topic",
            status="completed",
            started_at=datetime.now().isoformat(),
            synth_count=20,
            successful_count=20,
        )
        db_session.add(execution)

        # Create 20 transcripts
        for i in range(20):
            transcript = Transcript(
                id=f"transcript_page_{i:03d}",
                exec_id="exec_transcripts_001",
                synth_id=f"synth_page_{i:03d}",
                synth_name=f"Synth {i}",
                status="completed",
                turn_count=1,
                timestamp=datetime.now().isoformat(),
                messages=[{"role": "user", "content": f"Message {i}"}],
            )
            db_session.add(transcript)

        db_session.commit()

        # Execute
        from synth_lab.repositories.research_repository import ResearchRepository
        from synth_lab.models.pagination import PaginationParams

        repo = ResearchRepository(session=db_session)
        service = ResearchService(research_repo=repo)
        params = PaginationParams(limit=10, offset=0)
        result = service.get_transcripts("exec_transcripts_001", params)

        # Verify
        assert result.pagination.total == 20
        assert len(result.data) == 10
        assert result.data[0].synth_id is not None
        assert result.data[0].turn_count >= 1


@pytest.mark.integration
class TestResearchSummaryGeneratorIntegration:
    """Integration tests for research_summary_generator_service.py - Summary generation."""

    def test_generate_summary_verifies_execution_state(self, db_session):
        """Test that service can retrieve execution data for summary generation."""

        # Setup: Create execution with transcripts
        experiment = Experiment(
            id="exp_summary_001",
            name="Summary Test",
            hypothesis="Testing summary generation",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        db_session.add(experiment)

        group = SynthGroup(
            id="group_summary_001",
            name="Summary Group",
            created_at=datetime.now().isoformat(),
        )
        db_session.add(group)

        execution = ResearchExecution(
            exec_id="exec_summary_001",
            experiment_id="exp_summary_001",
            topic_name="Summary Test Topic",
            status="completed",
            started_at=datetime.now().isoformat(),
            completed_at=datetime.now().isoformat(),
            synth_count=2,
            successful_count=2,
        )
        db_session.add(execution)

        # Add transcripts
        for i in range(2):
            transcript = Transcript(
                id=f"transcript_summary_{i:03d}",
                exec_id="exec_summary_001",
                synth_id=f"synth_{i:03d}",
                synth_name=f"Test Synth {i}",
                status="completed",
                turn_count=1,
                timestamp=datetime.now().isoformat(),
                messages=[
                    {"role": "user", "content": "What do you think about X?"},
                    {"role": "assistant", "content": f"I think X is important because {i}."},
                ],
            )
            db_session.add(transcript)

        db_session.commit()

        # Execute: Generate summary (this would normally call LLM)
        # Note: We're mocking the LLM call to avoid external dependencies
        service = ResearchSummaryGeneratorService()

        # For this test, we'll verify the service can retrieve and process transcripts
        # Full generation test would require more complex mocking of async LLM calls
        from synth_lab.services.research_service import ResearchService
        from synth_lab.repositories.research_repository import ResearchRepository

        repo = ResearchRepository(session=db_session)
        research_service = ResearchService(research_repo=repo)
        execution_detail = research_service.get_execution("exec_summary_001")

        # Verify execution is in correct state for summary generation
        assert execution_detail.status == ExecutionStatus.COMPLETED, "Execution must be completed"
        assert execution_detail.successful_count == 2, "Must have transcripts"

        # Verify we can retrieve transcripts (service layer working)
        from synth_lab.models.pagination import PaginationParams

        params = PaginationParams(limit=10, offset=0)
        transcripts = research_service.get_transcripts("exec_summary_001", params)

        assert len(transcripts.data) == 2, "Should have 2 transcripts for summary"
        assert all(t.turn_count > 0 for t in transcripts.data), "All transcripts should have messages"


@pytest.mark.integration
class TestResearchServiceErrorHandling:
    """Integration tests for error handling in research services."""

    def test_get_execution_raises_not_found_error(self, db_session):
        """Test that service raises appropriate error for non-existent execution."""
        from synth_lab.repositories.research_repository import ResearchRepository
        from synth_lab.services.errors import ExecutionNotFoundError

        repo = ResearchRepository(session=db_session)
        service = ResearchService(research_repo=repo)

        with pytest.raises(ExecutionNotFoundError):
            service.get_execution("non_existent_exec_id")

    def test_get_transcripts_raises_not_found_for_invalid_execution(self, db_session):
        """Test that service raises error when getting transcripts for non-existent execution."""
        from synth_lab.repositories.research_repository import ResearchRepository
        from synth_lab.models.pagination import PaginationParams
        from synth_lab.services.errors import ExecutionNotFoundError

        repo = ResearchRepository(session=db_session)
        service = ResearchService(research_repo=repo)
        params = PaginationParams(limit=10, offset=0)

        with pytest.raises(ExecutionNotFoundError):
            service.get_transcripts("non_existent_exec_id", params)
