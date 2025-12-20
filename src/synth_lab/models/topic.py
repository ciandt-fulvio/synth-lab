"""
Topic guide domain models for synth-lab.

Pydantic models for topic guide (interview script) data.

References:
    - Schema definition: specs/010-rest-api/data-model.md
"""

from datetime import datetime

from pydantic import BaseModel, Field


class TopicFile(BaseModel):
    """Information about a file in a topic guide."""

    filename: str
    content_hash: str | None = None
    description: str | None = None


class TopicQuestion(BaseModel):
    """A single question in an interview script."""

    id: int = Field(..., description="Question sequence number")
    ask: str = Field(..., description="The question text")
    context_examples: dict | None = Field(
        default=None,
        description="Examples and context for the question",
    )


class TopicSummary(BaseModel):
    """Summary topic guide model for list endpoints."""

    name: str = Field(..., description="Topic directory name")
    display_name: str | None = Field(default=None, description="Human-readable name")
    description: str | None = Field(default=None, description="Brief description")
    question_count: int = Field(default=0, description="Number of questions in script")
    file_count: int = Field(default=0, description="Number of associated files")
    created_at: datetime | None = Field(default=None, description="First seen timestamp")
    updated_at: datetime | None = Field(default=None, description="Last updated timestamp")


class TopicDetail(TopicSummary):
    """Full topic guide with script and files."""

    summary: dict | None = Field(default=None, description="Parsed summary.md content")
    script: list[TopicQuestion] = Field(default_factory=list, description="Interview script")
    files: list[TopicFile] = Field(default_factory=list, description="Associated files")


if __name__ == "__main__":
    import sys

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Test 1: TopicQuestion creation
    total_tests += 1
    try:
        q = TopicQuestion(id=1, ask="Como você compra online?")
        if q.id != 1:
            all_validation_failures.append(f"Question ID mismatch: {q.id}")
        if q.context_examples is not None:
            all_validation_failures.append(
                f"context_examples should be None: {q.context_examples}"
            )
    except Exception as e:
        all_validation_failures.append(f"TopicQuestion creation failed: {e}")

    # Test 2: TopicQuestion with context
    total_tests += 1
    try:
        q = TopicQuestion(
            id=2,
            ask="Quais problemas você enfrenta?",
            context_examples={"example": "Pagamento, entrega"},
        )
        if q.context_examples.get("example") != "Pagamento, entrega":
            all_validation_failures.append(
                f"Context example mismatch: {q.context_examples}"
            )
    except Exception as e:
        all_validation_failures.append(f"TopicQuestion with context failed: {e}")

    # Test 3: TopicSummary defaults
    total_tests += 1
    try:
        summary = TopicSummary(name="compra-amazon")
        if summary.name != "compra-amazon":
            all_validation_failures.append(f"Name mismatch: {summary.name}")
        if summary.question_count != 0:
            all_validation_failures.append(
                f"Default question_count should be 0: {summary.question_count}"
            )
        if summary.display_name is not None:
            all_validation_failures.append(
                f"Default display_name should be None: {summary.display_name}"
            )
    except Exception as e:
        all_validation_failures.append(f"TopicSummary defaults failed: {e}")

    # Test 4: TopicSummary with values
    total_tests += 1
    try:
        summary = TopicSummary(
            name="compra-amazon",
            display_name="Compra na Amazon",
            description="Pesquisa sobre experiência de compra",
            question_count=5,
            file_count=3,
        )
        if summary.display_name != "Compra na Amazon":
            all_validation_failures.append(f"Display name mismatch: {summary.display_name}")
        if summary.question_count != 5:
            all_validation_failures.append(f"Question count mismatch: {summary.question_count}")
    except Exception as e:
        all_validation_failures.append(f"TopicSummary with values failed: {e}")

    # Test 5: TopicFile model
    total_tests += 1
    try:
        file = TopicFile(filename="screenshot.png", description="Tela de checkout")
        if file.filename != "screenshot.png":
            all_validation_failures.append(f"Filename mismatch: {file.filename}")
        if file.content_hash is not None:
            all_validation_failures.append(
                f"Default content_hash should be None: {file.content_hash}"
            )
    except Exception as e:
        all_validation_failures.append(f"TopicFile test failed: {e}")

    # Test 6: TopicDetail with nested data
    total_tests += 1
    try:
        detail = TopicDetail(
            name="test-topic",
            question_count=2,
            script=[
                TopicQuestion(id=1, ask="Q1"),
                TopicQuestion(id=2, ask="Q2"),
            ],
            files=[
                TopicFile(filename="file1.png"),
            ],
        )
        if len(detail.script) != 2:
            all_validation_failures.append(f"Script length mismatch: {len(detail.script)}")
        if len(detail.files) != 1:
            all_validation_failures.append(f"Files length mismatch: {len(detail.files)}")
        if detail.script[0].ask != "Q1":
            all_validation_failures.append(f"First question mismatch: {detail.script[0].ask}")
    except Exception as e:
        all_validation_failures.append(f"TopicDetail test failed: {e}")

    # Test 7: Empty script/files defaults
    total_tests += 1
    try:
        detail = TopicDetail(name="empty-topic")
        if detail.script != []:
            all_validation_failures.append(f"Default script should be empty: {detail.script}")
        if detail.files != []:
            all_validation_failures.append(f"Default files should be empty: {detail.files}")
    except Exception as e:
        all_validation_failures.append(f"Empty defaults test failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
