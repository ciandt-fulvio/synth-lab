"""
Topic repository for synth-lab.

Data access layer for topic guide data (filesystem + optional DB cache).

References:
    - Schema: specs/010-rest-api/data-model.md
"""

import json
from datetime import datetime
from pathlib import Path

from synth_lab.infrastructure.config import TOPIC_GUIDES_DIR
from synth_lab.infrastructure.database import DatabaseManager
from synth_lab.models.pagination import PaginatedResponse, PaginationParams
from synth_lab.models.topic import TopicDetail, TopicFile, TopicQuestion, TopicSummary
from synth_lab.repositories.base import BaseRepository
from synth_lab.services.errors import TopicNotFoundError


class TopicRepository(BaseRepository):
    """Repository for topic guide data access."""

    def __init__(
        self,
        db: DatabaseManager | None = None,
        topic_guides_dir: Path | None = None,
    ):
        super().__init__(db)
        self.topic_guides_dir = topic_guides_dir or TOPIC_GUIDES_DIR

    def list_topics(
        self,
        params: PaginationParams,
    ) -> PaginatedResponse[TopicSummary]:
        """
        List topic guides with pagination.

        Scans the filesystem for topic directories and returns summaries.

        Args:
            params: Pagination parameters.

        Returns:
            Paginated response with topic summaries.
        """
        if not self.topic_guides_dir.exists():
            return PaginatedResponse(
                data=[],
                pagination=PaginatedResponse.create([], 0, params).pagination,
            )

        # Get all topic directories
        all_topics = []
        for topic_dir in self.topic_guides_dir.iterdir():
            if topic_dir.is_dir() and not topic_dir.name.startswith("."):
                summary = self._dir_to_summary(topic_dir)
                if summary:
                    all_topics.append(summary)

        # Sort by name
        if params.sort_by == "name":
            reverse = params.sort_order == "desc"
            all_topics.sort(key=lambda t: t.name, reverse=reverse)
        elif params.sort_by == "question_count":
            reverse = params.sort_order == "desc"
            all_topics.sort(key=lambda t: t.question_count, reverse=reverse)

        # Apply pagination
        total = len(all_topics)
        start = params.offset
        end = params.offset + params.limit
        paginated = all_topics[start:end]

        return PaginatedResponse.create(paginated, total, params)

    def get_by_name(self, topic_name: str) -> TopicDetail:
        """
        Get a topic guide by name.

        Args:
            topic_name: Topic directory name.

        Returns:
            TopicDetail with full script and files.

        Raises:
            TopicNotFoundError: If topic not found.
        """
        topic_dir = self.topic_guides_dir / topic_name

        if not topic_dir.exists() or not topic_dir.is_dir():
            raise TopicNotFoundError(topic_name)

        return self._dir_to_detail(topic_dir)

    def get_executions_for_topic(
        self,
        topic_name: str,
        params: PaginationParams | None = None,
    ) -> PaginatedResponse:
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
        # Verify topic exists
        topic_dir = self.topic_guides_dir / topic_name
        if not topic_dir.exists():
            raise TopicNotFoundError(topic_name)

        params = params or PaginationParams()

        # Query executions from database
        base_query = "SELECT * FROM research_executions WHERE topic_name = ?"
        count_query = "SELECT COUNT(*) as count FROM research_executions WHERE topic_name = ?"

        rows, meta = self._paginate_query(
            base_query,
            params,
            count_query=count_query,
            query_params=(topic_name,),
        )

        # Import here to avoid circular import
        from synth_lab.repositories.research_repository import ResearchRepository

        research_repo = ResearchRepository(self.db)
        executions = [research_repo._row_to_summary(row) for row in rows]

        return PaginatedResponse(data=executions, pagination=meta)

    def _dir_to_summary(self, topic_dir: Path) -> TopicSummary | None:
        """Convert a topic directory to TopicSummary."""
        script_path = topic_dir / "script.json"

        # Load script to get question count
        question_count = 0
        if script_path.exists():
            try:
                with open(script_path) as f:
                    script_data = json.load(f)
                    question_count = len(script_data) if isinstance(script_data, list) else 0
            except (json.JSONDecodeError, IOError):
                pass

        # Count files (excluding script.json and hidden files)
        file_count = sum(
            1 for f in topic_dir.iterdir()
            if f.is_file() and not f.name.startswith(".") and f.name != "script.json"
        )

        # Get timestamps from directory
        stat = topic_dir.stat()
        created_at = datetime.fromtimestamp(stat.st_ctime)
        updated_at = datetime.fromtimestamp(stat.st_mtime)

        # Generate display name from directory name
        display_name = topic_dir.name.replace("-", " ").replace("_", " ").title()

        return TopicSummary(
            name=topic_dir.name,
            display_name=display_name,
            description=None,  # Could be extracted from summary.md if exists
            question_count=question_count,
            file_count=file_count,
            created_at=created_at,
            updated_at=updated_at,
        )

    def _dir_to_detail(self, topic_dir: Path) -> TopicDetail:
        """Convert a topic directory to TopicDetail."""
        script_path = topic_dir / "script.json"
        summary_path = topic_dir / "summary.md"

        # Load script
        script = []
        if script_path.exists():
            try:
                with open(script_path) as f:
                    script_data = json.load(f)
                    if isinstance(script_data, list):
                        for item in script_data:
                            script.append(TopicQuestion(
                                id=item.get("id", 0),
                                ask=item.get("ask", ""),
                                context_examples=item.get("context_examples"),
                            ))
            except (json.JSONDecodeError, IOError):
                pass

        # Load summary
        summary_content = None
        if summary_path.exists():
            try:
                summary_content = {"content": summary_path.read_text(encoding="utf-8")}
            except IOError:
                pass

        # Get files (excluding script.json, summary.md, and hidden files)
        files = []
        for f in sorted(topic_dir.iterdir()):
            if (
                f.is_file()
                and not f.name.startswith(".")
                and f.name not in ("script.json", "summary.md")
            ):
                files.append(TopicFile(
                    filename=f.name,
                    description=None,
                ))

        # Get timestamps
        stat = topic_dir.stat()
        created_at = datetime.fromtimestamp(stat.st_ctime)
        updated_at = datetime.fromtimestamp(stat.st_mtime)

        display_name = topic_dir.name.replace("-", " ").replace("_", " ").title()

        return TopicDetail(
            name=topic_dir.name,
            display_name=display_name,
            description=None,
            question_count=len(script),
            file_count=len(files),
            created_at=created_at,
            updated_at=updated_at,
            summary=summary_content,
            script=script,
            files=files,
        )


if __name__ == "__main__":
    import sys

    from synth_lab.infrastructure.config import DB_PATH
    from synth_lab.infrastructure.database import DatabaseManager

    # Validation with real data
    all_validation_failures = []
    total_tests = 0

    db = DatabaseManager(DB_PATH) if DB_PATH.exists() else None
    repo = TopicRepository(db)

    # Test 1: List topics
    total_tests += 1
    try:
        result = repo.list_topics(PaginationParams(limit=10))
        print(f"  Found {result.pagination.total} topics")
        if result.pagination.total < 1:
            all_validation_failures.append("No topics found")
    except Exception as e:
        all_validation_failures.append(f"List topics failed: {e}")

    # Test 2: Get topic by name
    total_tests += 1
    try:
        result = repo.list_topics(PaginationParams(limit=1))
        if result.data:
            topic_name = result.data[0].name
            topic = repo.get_by_name(topic_name)
            if topic.name != topic_name:
                all_validation_failures.append(f"Name mismatch: {topic.name}")
            print(f"  Got topic: {topic.display_name}")
            print(f"    - {topic.question_count} questions")
            print(f"    - {topic.file_count} files")
    except Exception as e:
        all_validation_failures.append(f"Get topic failed: {e}")

    # Test 3: Get non-existent topic
    total_tests += 1
    try:
        repo.get_by_name("nonexistent-topic")
        all_validation_failures.append("Should raise TopicNotFoundError")
    except TopicNotFoundError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Wrong exception: {e}")

    # Test 4: Get executions for topic
    total_tests += 1
    try:
        result = repo.list_topics(PaginationParams(limit=1))
        if result.data:
            topic_name = result.data[0].name
            executions = repo.get_executions_for_topic(topic_name)
            print(f"  Found {executions.pagination.total} executions for {topic_name}")
    except Exception as e:
        all_validation_failures.append(f"Get executions for topic failed: {e}")

    # Test 5: Topic detail includes script
    total_tests += 1
    try:
        result = repo.list_topics(PaginationParams(limit=1))
        if result.data:
            topic_name = result.data[0].name
            topic = repo.get_by_name(topic_name)
            if len(topic.script) > 0:
                print(f"  Script has {len(topic.script)} questions")
                print(f"    First question: {topic.script[0].ask[:50]}...")
            else:
                all_validation_failures.append("Topic should have script questions")
    except Exception as e:
        all_validation_failures.append(f"Topic detail test failed: {e}")

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
