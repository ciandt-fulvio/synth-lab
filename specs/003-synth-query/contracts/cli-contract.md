# CLI Contract: listsynth Command

**Feature**: 003-synth-query
**Date**: 2025-12-15
**Status**: Design Complete

## Command Overview

The `listsynth` command queries synthetic data stored in `data/synths/synths.json` using DuckDB and displays results in formatted tables.

---

## Command Signature

```bash
synthlab listsynth [OPTIONS]
```

### Global Access

The command is accessible through the main `synthlab` CLI entry point:

```bash
# Direct invocation
synthlab listsynth

# With options
synthlab listsynth --where "age > 30"
synthlab listsynth --full-query "SELECT city, COUNT(*) FROM synths GROUP BY city"
```

---

## Parameters

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--where` | TEXT | None | SQL WHERE clause condition (without the WHERE keyword) |
| `--full-query` | TEXT | None | Complete SQL SELECT query |

### Parameter Rules

1. **Mutual Exclusivity**: Cannot use `--where` and `--full-query` together
2. **Optional Both**: If neither parameter is provided, displays all records
3. **Case Sensitivity**: Parameter names are case-sensitive

---

## Behavior Modes

### Mode 1: Basic Listing (No Parameters)

**Command**:
```bash
synthlab listsynth
```

**Behavior**:
- Executes: `SELECT * FROM synths`
- Displays all synth records
- Shows all columns
- Applies display limit (1,000 rows max)

**Example Output**:
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
│          Query Results              │
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ id      │ name      │ age │ city   │
├─────────┼───────────┼─────┼────────┤
│ uuid-1  │ João      │ 34  │ SP     │
│ uuid-2  │ Maria     │ 28  │ RJ     │
...
└─────────┴───────────┴─────┴────────┘

50 rows returned
```

---

### Mode 2: Filtered Query (--where)

**Command**:
```bash
synthlab listsynth --where "age > 30 AND city = 'São Paulo'"
```

**Behavior**:
- Executes: `SELECT * FROM synths WHERE <condition>`
- WHERE keyword automatically added
- User provides only the condition
- SQL syntax in condition must be valid

**Valid Conditions Examples**:
```bash
# Numeric comparison
--where "age >= 25"
--where "age BETWEEN 20 AND 40"

# String comparison (use single quotes for strings)
--where "city = 'São Paulo'"
--where "gender IN ('M', 'F')"

# Complex conditions
--where "age > 30 AND city = 'Rio de Janeiro'"
--where "demographics.openness > 0.7 OR psychographics.extraversion > 0.8"
```

**Invalid Conditions** (will error):
```bash
# Missing quotes around string
--where "city = São Paulo"  # ❌ Syntax error

# Using WHERE keyword (redundant)
--where "WHERE age > 30"  # ❌ "WHERE WHERE age > 30" invalid

# Non-SELECT operations
--where "age > 30; DROP TABLE synths"  # ❌ Injection attempt (rejected)
```

---

### Mode 3: Custom SQL Query (--full-query)

**Command**:
```bash
synthlab listsynth --full-query "SELECT city, COUNT(*) as total FROM synths GROUP BY city ORDER BY total DESC"
```

**Behavior**:
- Executes user's complete SQL query
- Must be a valid SELECT statement
- Can include: WHERE, GROUP BY, ORDER BY, LIMIT, joins, aggregations
- Cannot include: INSERT, UPDATE, DELETE, DROP, ALTER

**Valid Queries Examples**:
```bash
# Aggregation
--full-query "SELECT city, AVG(age) as avg_age FROM synths GROUP BY city"

# Sorting and limiting
--full-query "SELECT * FROM synths ORDER BY age DESC LIMIT 10"

# Column selection
--full-query "SELECT name, age, city FROM synths WHERE age > 50"

# Complex analytics
--full-query "SELECT gender, AVG(psychographics.openness) as avg_openness FROM synths GROUP BY gender"
```

**Invalid Queries** (will be rejected):
```bash
# Non-SELECT operation
--full-query "INSERT INTO synths VALUES (...)"  # ❌ Only SELECT allowed

# Multiple statements
--full-query "SELECT * FROM synths; DROP TABLE synths"  # ❌ Single statement only

# Missing FROM clause
--full-query "SELECT COUNT(*)"  # ❌ Must reference synths table (or valid SQL)
```

---

## Exit Codes

| Code | Meaning | Scenarios |
|------|---------|-----------|
| 0 | Success | Query executed successfully, results displayed |
| 1 | User Error | Invalid parameters, SQL syntax error, invalid WHERE clause |
| 2 | System Error | Data file missing, database initialization failed, DuckDB error |

### Exit Code Examples

**Exit 0 (Success)**:
```bash
$ synthlab listsynth
# (displays results)
$ echo $?
0
```

**Exit 1 (User Error)**:
```bash
$ synthlab listsynth --where "age >"
Error: Invalid SQL syntax: incomplete WHERE condition
$ echo $?
1
```

```bash
$ synthlab listsynth --where "age > 30" --full-query "SELECT * FROM synths"
Error: Cannot use both --where and --full-query
$ echo $?
1
```

**Exit 2 (System Error)**:
```bash
$ synthlab listsynth
Error: Synth data file not found: data/synths/synths.json
Tip: Run 'synthlab generate' to create synthetic data first.
$ echo $?
2
```

---

## Output Format

### Table Display (Success)

Results displayed using Rich table formatting:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
│          Query Results              │
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ column1  │ column2  │ column3       │
├──────────┼──────────┼───────────────┤
│ value1   │ value2   │ value3        │
│ ...      │ ...      │ ...           │
└──────────┴──────────┴───────────────┘

N rows returned
```

### Table Characteristics

- **Header**: Bold magenta column names
- **Data**: Cyan-colored values
- **Box Style**: Rounded corners
- **Overflow**: Long values wrapped (fold) at 30 characters max
- **Width**: Adaptive to terminal width, max 30 chars per column

### Empty Result Display

```bash
$ synthlab listsynth --where "age > 200"
```

**Output**:
```
No results found

0 rows returned
```

### Truncated Result Display

When result set exceeds 1,000 rows:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
│          Query Results              │
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ id       │ name     │ age           │
├──────────┼──────────┼───────────────┤
│ uuid-1   │ João     │ 34            │
│ ...      │ ...      │ ...           │
└──────────┴──────────┴───────────────┘

Warning: Showing first 1,000 of 5,432 rows
Tip: Use --full-query with LIMIT clause to control result size

1,000 rows displayed (5,432 total)
```

---

## Error Messages

### User Error Messages (Exit 1)

**Mutual Exclusivity Violation**:
```
Error: Cannot use both --where and --full-query
Choose one: use --where for simple filters or --full-query for custom SQL
```

**SQL Syntax Error**:
```
Error: Invalid SQL syntax in your query
Details: Parser error: syntax error at or near ">"
Please check for typos, missing quotes, or incorrect SQL keywords
```

**Invalid Column Reference**:
```
Error: Column not found in query
Details: Column 'invalidcolumn' does not exist
Make sure column names are spelled correctly and exist in the synths table
```

**Non-SELECT Query** :
```
Error: Only SELECT queries are allowed
Found: INSERT operation
This tool is read-only; use --full-query with SELECT statements only
```

### System Error Messages (Exit 2)

**Data File Not Found**:
```
Error: Synth data file not found: data/synths/synths.json
Tip: Run 'synthlab generate' to create synthetic data first
```

**Invalid JSON**:
```
Error: Invalid JSON in data/synths/synths.json
Details: Expecting ',' delimiter at line 42 column 5
The synth data file may be corrupted. Try regenerating with 'synthlab generate'
```

**Database Initialization Failed**:
```
Error: Failed to initialize database
Details: DuckDB could not read JSON file: <error details>
Please ensure data/synths/synths.json is valid JSON
```

---

## Help Text

```bash
$ synthlab listsynth --help
```

**Output**:
```
Usage: synthlab listsynth [OPTIONS]

  Query synthetic data from the synths database.

  Display modes:
    - No options: Show all records
    - --where: Filter records with SQL WHERE condition
    - --full-query: Execute custom SQL SELECT query

  Examples:
    synthlab listsynth
    synthlab listsynth --where "age > 30"
    synthlab listsynth --where "city = 'São Paulo' AND age BETWEEN 25 AND 40"
    synthlab listsynth --full-query "SELECT city, COUNT(*) FROM synths GROUP BY city"

Options:
  --where TEXT       SQL WHERE clause condition (without WHERE keyword)
                     Cannot be used with --full-query

  --full-query TEXT  Complete SQL SELECT query
                     Cannot be used with --where

  --help             Show this message and exit
```

---

## Data Source

### Location

- **JSON Source**: `data/synths/synths.json`
- **DuckDB Database**: `data/synths/synths.duckdb` (created automatically)

### Database Initialization

On each invocation:
1. Connect to `synths.duckdb` (creates if doesn't exist)
2. Drop existing `synths` table (if any)
3. Recreate table from `data/synths/synths.json`
4. Execute user query

**Rationale**: Always fresh data, handles schema changes automatically.

### Performance

- **Cold Start**: <500ms (includes JSON parsing and table creation)
- **Query Execution**: <2s for 10,000 records
- **Table Display**: <1s for 1,000 rows

---

## Security Considerations

### SQL Injection Prevention

1. **Read-Only**: Only SELECT queries allowed
2. **Validation**: Reject non-SELECT operations (INSERT, UPDATE, DELETE, DROP, etc.)
3. **Local Scope**: Queries execute against local DuckDB database, no network access

### Implementation

```python
def validate_query_security(sql: str) -> None:
    """Ensure query is SELECT-only."""
    sql_upper = sql.strip().upper()

    # Check for forbidden operations
    forbidden = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE"]
    for operation in forbidden:
        if operation in sql_upper:
            raise QuerySyntaxError(
                f"Only SELECT queries are allowed\n"
                f"Found: {operation} operation\n"
                f"This tool is read-only"
            )

    # Ensure query starts with SELECT
    if not sql_upper.startswith("SELECT"):
        raise QuerySyntaxError(
            "Query must be a SELECT statement\n"
            f"Found: {sql[:20]}..."
        )
```

---

## Integration with Main CLI

### Entry Point Integration

The `listsynth` command integrates into the main `synthlab` CLI:

**File**: `src/synth_lab/__main__.py`

```python
import typer
from synth_lab.gen_synth.cli import app as gen_app
from synth_lab.query.cli import app as query_app

app = typer.Typer()

# Register command groups
app.add_typer(gen_app, name="generate", help="Generate synthetic data")
app.add_typer(query_app, name="listsynth", help="Query synthetic data")

if __name__ == "__main__":
    app()
```

Alternatively, if `listsynth` is a single command:

```python
from synth_lab.query.cli import listsynth

app = typer.Typer()
app.command()(listsynth)  # Register as direct command
```

---

## Testing Contract

### Unit Tests

Test each mode independently:

```python
@pytest.mark.unit
def test_basic_mode_query_building():
    """Test basic mode creates correct SQL."""
    request = QueryRequest(mode=QueryMode.BASIC)
    assert request.to_sql() == "SELECT * FROM synths"

@pytest.mark.unit
def test_where_mode_query_building():
    """Test WHERE mode creates correct SQL."""
    request = QueryRequest(mode=QueryMode.WHERE, where_clause="age > 30")
    assert request.to_sql() == "SELECT * FROM synths WHERE age > 30"

@pytest.mark.unit
def test_mutual_exclusivity_validation():
    """Test that both --where and --full-query raises error."""
    with pytest.raises(ValueError, match="Cannot specify both"):
        QueryRequest(
            mode=QueryMode.WHERE,
            where_clause="age > 30",
            full_query="SELECT * FROM synths"
        )
```

### Integration Tests

Test with real DuckDB:

```python
@pytest.mark.integration
def test_basic_query_execution(sample_synth_data):
    """Test basic query returns all records."""
    config = DatabaseConfig.default()
    request = QueryRequest(mode=QueryMode.BASIC)

    result = execute_query(config, request)

    assert result.row_count > 0
    assert len(result.columns) > 0
    assert not result.is_empty

@pytest.mark.integration
def test_where_query_filtering(sample_synth_data):
    """Test WHERE clause correctly filters records."""
    config = DatabaseConfig.default()
    request = QueryRequest(mode=QueryMode.WHERE, where_clause="age > 30")

    result = execute_query(config, request)

    # Verify all returned rows match filter
    for row in result.rows:
        age_index = result.columns.index("age")
        assert row[age_index] > 30
```

---

## Next Steps

1. Implement CLI in `src/synth_lab/query/cli.py`
2. Implement query execution in `src/synth_lab/query/database.py`
3. Implement table formatting in `src/synth_lab/query/formatter.py`
4. Follow TDD approach: write tests first, then implementation
