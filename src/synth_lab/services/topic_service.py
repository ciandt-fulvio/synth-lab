"""
Topic service for synth-lab.

Business logic layer for topic guide operations.

References:
    - API spec: specs/010-rest-api/contracts/openapi.yaml
"""

from synth_lab.models.pagination import PaginatedResponse, PaginationParams
from synth_lab.models.research import ResearchExecutionSummary
from synth_lab.models.topic import TopicDetail, TopicSummary
from synth_lab.repositories.topic_repository import TopicRepository


class TopicService:
    """Service for topic guide business logic."""

    def __init__(self, topic_repo: TopicRepository | None = None):
        """
        Initialize topic service.

        Args:
            topic_repo: Topic repository. Defaults to new instance.
        """
        self.topic_repo = topic_repo or TopicRepository()

    def list_topics(
        self,
        params: PaginationParams | None = None,
    ) -> PaginatedResponse[TopicSummary]:
        """
        List topic guides with pagination.

        Args:
            params: Pagination parameters.

        Returns:
            Paginated response with topic summaries.
        """
        params = params or PaginationParams()
        return self.topic_repo.list_topics(params)

    def get_topic(self, topic_name: str) -> TopicDetail:
        """
        Get a topic guide by name.

        Args:
            topic_name: Topic directory name.

        Returns:
            TopicDetail with full script and files.

        Raises:
            TopicNotFoundError: If topic not found.
        """
        return self.topic_repo.get_by_name(topic_name)

    def get_topic_executions(
        self,
        topic_name: str,
        params: PaginationParams | None = None,
    ) -> PaginatedResponse[ResearchExecutionSummary]:
        """
        Get research executions for a topic.

        Args:
            topic_name: Topic name.
            params: Pagination parameters.

        Returns:
            Paginated response with execution summaries.

        Raises:
            TopicNotFoundError: If topic not found.
        """
        params = params or PaginationParams()
        return self.topic_repo.get_executions_for_topic(topic_name, params)


if __name__ == "__main__":
    import sys

    from synth_lab.infrastructure.config import DB_PATH
    from synth_lab.infrastructure.database import DatabaseManager
    from synth_lab.services.errors import TopicNotFoundError

    # Validation with real data
    all_validation_failures = []
    total_tests = 0

    db = DatabaseManager(DB_PATH) if DB_PATH.exists() else None
    repo = TopicRepository(db)
    service = TopicService(repo)

    # Test 1: List topics
    total_tests += 1
    try:
        result = service.list_topics()
        print(f"  Listed {result.pagination.total} topics")
        if result.pagination.total < 1:
            all_validation_failures.append("No topics found")
    except Exception as e:
        all_validation_failures.append(f"List topics failed: {e}")

    # Test 2: Get topic by name
    total_tests += 1
    try:
        result = service.list_topics(PaginationParams(limit=1))
        if result.data:
            topic_name = result.data[0].name
            topic = service.get_topic(topic_name)
            if topic.name != topic_name:
                all_validation_failures.append(f"Name mismatch: {topic.name}")
            print(f"  Got topic: {topic.display_name}")
    except Exception as e:
        all_validation_failures.append(f"Get topic failed: {e}")

    # Test 3: Get non-existent topic
    total_tests += 1
    try:
        service.get_topic("nonexistent-topic")
        all_validation_failures.append("Should raise TopicNotFoundError")
    except TopicNotFoundError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Wrong exception: {e}")

    # Test 4: Get executions for topic
    total_tests += 1
    try:
        result = service.list_topics(PaginationParams(limit=1))
        if result.data:
            topic_name = result.data[0].name
            executions = service.get_topic_executions(topic_name)
            print(f"  Found {executions.pagination.total} executions for {topic_name}")
    except Exception as e:
        all_validation_failures.append(f"Get topic executions failed: {e}")

    if db:
        db.close()

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
