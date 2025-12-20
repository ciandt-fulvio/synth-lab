"""Unit tests for query validator module."""

import pytest

from synth_lab.query import QueryMode


# T011: Unit test for QueryMode.BASIC
@pytest.mark.unit
def test_query_mode_basic():
    """Test QueryMode.BASIC enum value."""
    assert QueryMode.BASIC.value == "basic"
    assert QueryMode.BASIC == QueryMode.BASIC


# T012: Unit test for QueryRequest with BASIC mode
@pytest.mark.unit
def test_query_request_basic_mode():
    """Test QueryRequest creation with BASIC mode."""
    from synth_lab.query.validator import QueryRequest

    request = QueryRequest(mode=QueryMode.BASIC)

    assert request.mode == QueryMode.BASIC
    assert request.where_clause is None
    assert request.full_query is None


# T013: Unit test for QueryRequest.to_sql() basic mode
@pytest.mark.unit
def test_query_request_to_sql_basic():
    """Test QueryRequest.to_sql() for BASIC mode."""
    from synth_lab.query.validator import QueryRequest

    request = QueryRequest(mode=QueryMode.BASIC)
    sql = request.to_sql()

    assert sql == "SELECT * FROM synths"


# T037: Unit test for mutual exclusivity validation (US2)
@pytest.mark.unit
def test_query_request_mutual_exclusivity():
    """Test that providing both where_clause and full_query raises error."""
    from synth_lab.query.validator import QueryRequest

    with pytest.raises(ValueError, match="Cannot specify both"):
        QueryRequest(
            mode=QueryMode.WHERE,
            where_clause="age > 30",
            full_query="SELECT * FROM synths"
        )


# Additional validation tests for Mode-Clause consistency
@pytest.mark.unit
def test_query_request_basic_mode_no_clauses():
    """Test BASIC mode cannot have where_clause or full_query."""
    from synth_lab.query.validator import QueryRequest

    with pytest.raises(ValueError, match="BASIC mode cannot have"):
        QueryRequest(mode=QueryMode.BASIC, where_clause="age > 30")

    with pytest.raises(ValueError, match="BASIC mode cannot have"):
        QueryRequest(mode=QueryMode.BASIC, full_query="SELECT * FROM synths")
