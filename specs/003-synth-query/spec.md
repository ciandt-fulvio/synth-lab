# Feature Specification: Synth Data Query Tool

**Feature Branch**: `003-synth-query`
**Created**: 2025-12-15
**Status**: Draft
**Input**: User description: "vamos comecar agora uma funcionalidade de consulta nos synths, para isso usaremos a lib de duckdb. essa funcionalidade, linha de comando, chamara listsynth e podera ter um parametro opcional --where "...", que será usado na clausula where ou então permitira um parametro --full-query "SELECT ..." que dai fornecera um query completo"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Basic Data Listing (Priority: P1)

As a user, I want to view all synthetic data records using a simple command so I can quickly inspect the generated data without needing to know SQL.

**Why this priority**: This is the foundational use case - users need to see their synth data before they can query it. This represents the minimum viable functionality and delivers immediate value.

**Independent Test**: Can be fully tested by running `listsynth` without parameters and verifying that all synth records are displayed in a readable format.

**Acceptance Scenarios**:

1. **Given** synthetic data has been generated and stored, **When** user runs `listsynth` command without parameters, **Then** all synth records are displayed in a formatted table
2. **Given** no synthetic data exists, **When** user runs `listsynth` command, **Then** system displays a message indicating no records found
3. **Given** synthetic data exists, **When** user runs `listsynth` command, **Then** output includes column headers and all data fields

---

### User Story 2 - Filtered Data Query (Priority: P2)

As a user, I want to filter synthetic data using a WHERE clause so I can focus on specific records that match certain criteria without writing a full SQL query.

**Why this priority**: Once users can view data, the next natural need is filtering. This provides significant value while keeping the interface simple for non-SQL users.

**Independent Test**: Can be fully tested by running `listsynth --where "age > 30"` and verifying that only matching records are displayed.

**Acceptance Scenarios**:

1. **Given** synthetic data exists with various ages, **When** user runs `listsynth --where "age > 30"`, **Then** only records where age is greater than 30 are displayed
2. **Given** synthetic data exists, **When** user runs `listsynth --where "city = 'São Paulo'"`, **Then** only records from São Paulo are displayed
3. **Given** synthetic data exists, **When** user provides an invalid WHERE clause, **Then** system displays a helpful error message explaining the syntax issue
4. **Given** no records match the WHERE criteria, **When** user runs the query, **Then** system displays a message indicating no matching records found

---

### User Story 3 - Custom SQL Query (Priority: P3)

As an advanced user, I want to execute custom SQL queries so I can perform complex data analysis, aggregations, and joins that go beyond simple filtering.

**Why this priority**: This serves power users who need advanced querying capabilities. While valuable, it's not essential for basic usage and requires SQL knowledge.

**Independent Test**: Can be fully tested by running `listsynth --full-query "SELECT city, COUNT(*) as total FROM synths GROUP BY city"` and verifying aggregated results are displayed.

**Acceptance Scenarios**:

1. **Given** synthetic data exists, **When** user runs `listsynth --full-query "SELECT * FROM synths LIMIT 10"`, **Then** only the first 10 records are displayed
2. **Given** synthetic data exists, **When** user runs a query with aggregations like `SELECT age, COUNT(*) FROM synths GROUP BY age`, **Then** aggregated results are displayed correctly
3. **Given** synthetic data exists, **When** user runs a query with multiple columns selected, **Then** only the specified columns are displayed
4. **Given** user provides an invalid SQL query, **When** user runs the command, **Then** system displays the SQL error message with context about what went wrong

---

### Edge Cases

- What happens when `data/synths/synths.json` doesn't exist?
- What happens when `data/synths/synths.json` exists but is empty or contains invalid JSON?
- How does the system handle queries that return extremely large result sets (millions of rows)?
- What happens when user provides both `--where` and `--full-query` parameters simultaneously?
- How does the system handle SQL injection attempts in the WHERE clause or full query?
- What happens when the query contains special characters or Unicode in string literals?
- How does the system handle queries that take a very long time to execute?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a command-line interface named `listsynth`
- **FR-002**: System MUST support a `--where` parameter that accepts a SQL WHERE clause condition (without the WHERE keyword)
- **FR-003**: System MUST support a `--full-query` parameter that accepts a complete SQL SELECT statement
- **FR-004**: System MUST prevent execution when both `--where` and `--full-query` parameters are provided simultaneously
- **FR-005**: System MUST display query results in a readable, formatted table structure
- **FR-006**: System MUST display column headers in the output
- **FR-007**: System MUST handle queries that return no results gracefully with an informative message
- **FR-008**: System MUST validate SQL syntax and display helpful error messages when queries fail
- **FR-009**: System MUST access synthetic data stored in `data/synths/synths.json`
- **FR-010**: System MUST handle queries returning large result sets without crashing or excessive memory consumption
- **FR-011**: System MUST display execution errors in a user-friendly format, including the error type and suggested corrections when possible
- **FR-012**: When run without parameters, system MUST display all synthetic records (equivalent to `SELECT * FROM synths`)

### Key Entities

- **Synth Record**: Represents a single synthetic data entry containing all generated fields (e.g., name, age, city, email, etc.). The exact schema depends on the synthetic data generation feature.
- **Query Result**: Represents the output of a query execution, containing selected columns and filtered rows based on user criteria.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can view all synthetic data in under 2 seconds for datasets up to 10,000 records
- **SC-002**: Users can successfully filter data using the `--where` parameter with 100% accuracy for valid SQL conditions
- **SC-003**: Users can execute custom SQL queries and receive correctly formatted results for all valid SELECT statements
- **SC-004**: System displays helpful error messages for 100% of invalid queries, allowing users to correct their syntax
- **SC-005**: Output remains readable and properly formatted for result sets ranging from 0 to 1,000 rows
- **SC-006**: 95% of users can successfully query synthetic data on their first attempt without consulting documentation

## Assumptions

- Synthetic data is stored in JSON format at `data/synths/synths.json`
- DuckDB can read and query JSON files directly
- The synth data schema is consistent and known to the system
- Users have basic understanding of SQL syntax for the advanced `--full-query` option
- The command will be integrated into the existing synth-lab CLI structure
- Default behavior (no parameters) is equivalent to `SELECT * FROM synths`
- The data source will be referenced as a table named "synths" in SQL queries

## Dependencies

- DuckDB library must be installed and available
- Existing synthetic data generation feature must be complete and producing data in JSON format
- Read access to the `data/synths/` directory and `synths.json` file

## Out of Scope

- Modifying or deleting synthetic data (read-only queries only)
- Exporting query results to files (CSV, JSON, etc.)
- Saving frequently used queries or query history
- Interactive query builder or visual query interface
- JOIN operations with external data sources
- Real-time data updates or streaming queries
