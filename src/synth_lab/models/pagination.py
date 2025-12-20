"""
Pagination models for synth-lab API.

Provides reusable pagination request/response models for all list endpoints.

References:
    - Pydantic docs: https://docs.pydantic.dev/
"""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination request parameters."""

    limit: int = Field(default=50, ge=1, le=200, description="Maximum items per page")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")
    sort_by: str | None = Field(default=None, description="Field to sort by")
    sort_order: str = Field(
        default="desc",
        pattern="^(asc|desc)$",
        description="Sort order: asc or desc",
    )


class PaginationMeta(BaseModel):
    """Pagination metadata for response."""

    total: int = Field(..., description="Total number of items")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Current offset")
    has_next: bool = Field(..., description="Whether there are more items")

    @classmethod
    def from_params(cls, total: int, params: PaginationParams) -> "PaginationMeta":
        """Create metadata from params and total count."""
        return cls(
            total=total,
            limit=params.limit,
            offset=params.offset,
            has_next=(params.offset + params.limit) < total,
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    data: list[T]
    pagination: PaginationMeta

    @classmethod
    def create(
        cls, items: list[T], total: int, params: PaginationParams
    ) -> "PaginatedResponse[T]":
        """Create a paginated response from items and params."""
        return cls(
            data=items,
            pagination=PaginationMeta.from_params(total, params),
        )


if __name__ == "__main__":
    import sys

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Test 1: Default pagination params
    total_tests += 1
    try:
        params = PaginationParams()
        if params.limit != 50:
            all_validation_failures.append(f"Default limit should be 50, got {params.limit}")
        if params.offset != 0:
            all_validation_failures.append(f"Default offset should be 0, got {params.offset}")
        if params.sort_order != "desc":
            all_validation_failures.append(
                f"Default sort_order should be desc, got {params.sort_order}"
            )
    except Exception as e:
        all_validation_failures.append(f"Default params failed: {e}")

    # Test 2: Custom pagination params
    total_tests += 1
    try:
        params = PaginationParams(limit=10, offset=20, sort_by="nome", sort_order="asc")
        if params.limit != 10:
            all_validation_failures.append(f"Custom limit should be 10, got {params.limit}")
        if params.offset != 20:
            all_validation_failures.append(f"Custom offset should be 20, got {params.offset}")
    except Exception as e:
        all_validation_failures.append(f"Custom params failed: {e}")

    # Test 3: Pagination meta from params
    total_tests += 1
    try:
        params = PaginationParams(limit=10, offset=0)
        meta = PaginationMeta.from_params(total=25, params=params)
        if meta.total != 25:
            all_validation_failures.append(f"Total should be 25, got {meta.total}")
        if meta.has_next is not True:
            all_validation_failures.append(f"has_next should be True, got {meta.has_next}")
    except Exception as e:
        all_validation_failures.append(f"Meta from params failed: {e}")

    # Test 4: has_next = False when no more items
    total_tests += 1
    try:
        params = PaginationParams(limit=10, offset=20)
        meta = PaginationMeta.from_params(total=25, params=params)
        if meta.has_next is not False:
            all_validation_failures.append(f"has_next should be False, got {meta.has_next}")
    except Exception as e:
        all_validation_failures.append(f"has_next False test failed: {e}")

    # Test 5: PaginatedResponse creation
    total_tests += 1
    try:
        params = PaginationParams(limit=2, offset=0)
        items = ["a", "b"]
        response = PaginatedResponse[str].create(items=items, total=5, params=params)
        if len(response.data) != 2:
            all_validation_failures.append(f"Data length should be 2, got {len(response.data)}")
        if response.pagination.total != 5:
            all_validation_failures.append(
                f"Pagination total should be 5, got {response.pagination.total}"
            )
        if response.pagination.has_next is not True:
            all_validation_failures.append(
                f"has_next should be True, got {response.pagination.has_next}"
            )
    except Exception as e:
        all_validation_failures.append(f"PaginatedResponse test failed: {e}")

    # Test 6: Limit validation
    total_tests += 1
    try:
        from pydantic import ValidationError

        try:
            PaginationParams(limit=0)
            all_validation_failures.append("Should reject limit=0")
        except ValidationError:
            pass  # Expected

        try:
            PaginationParams(limit=201)
            all_validation_failures.append("Should reject limit=201")
        except ValidationError:
            pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Limit validation test failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
