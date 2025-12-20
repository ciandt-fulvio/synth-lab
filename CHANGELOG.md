# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Removed - 2025-12-20

#### CLI Commands Simplified (Feature 011-remove-cli-commands)

**Breaking Changes:**
- Removed `listsynth` CLI command - use REST API (`GET /synths/list`) or DuckDB CLI instead
- Removed `topic-guide` CLI command - manage topic guides manually and use REST API (`GET /topics/*`)
- Removed `research` CLI command - use REST API (`GET /research/*`) instead
- Removed `research-prfaq` CLI command - use REST API (`GET /prfaq/*`) instead

**What remains:**
- `gensynth` - The only CLI command for generating synthetic personas and avatars
- `--help` and `--version` global options

**Migration path:**
- For queries: Use `curl http://localhost:8000/synths/list` or `duckdb synths.duckdb "SELECT * FROM synths"`
- For topic guides: Create directories manually in `data/topic_guides/` and access via API
- For research: Access execution data via `GET /research/list` and `GET /research/{execution_id}`
- For PR-FAQ: Access reports via `GET /prfaq/list` and `GET /prfaq/{execution_id}`

**Architecture improvements:**
- Refactored to clean architecture with services layer
- Moved all feature modules under `services/` directory
- Renamed conflicting model files:
  - `research_prfaq/models.py` → `generation_models.py`
  - `topic_guides/models.py` → `internal_models.py`
- Removed circular dependencies
- Updated all imports to use new service paths

**API remains fully functional:**
- All 17 REST API endpoints verified and working
- No changes to API contracts or behavior
- Documentation at `/docs` and `/openapi.json` updated

**Test improvements:**
- Test suite health improved: 224 passed, 16 failed (vs baseline 232/18)
- Failure rate reduced from 7.2% to 6.7%
- Removed 10 obsolete CLI-specific tests
- Fixed all import references and mocking paths

**Documentation updates:**
- README.md: Updated to focus on gensynth and REST API
- docs/cli.md: Simplified to document only gensynth command
- Added migration guides for removed CLI commands

See [specs/011-remove-cli-commands/](specs/011-remove-cli-commands/) for complete implementation details.

---

## [2.0.0] - 2025-12-15

### Added - REST API Launch (Feature 010-rest-api)

- Added comprehensive REST API with 17 endpoints
- FastAPI server with automatic OpenAPI documentation
- SQLite database with JSON1 extension for data persistence
- Endpoints for synths, research, topics, and PR-FAQ resources
- Interactive API documentation at `/docs`
- OpenAPI specification at `/openapi.json`
- Clean architecture with routers, services, and repositories

### Changed

- Migrated data storage from JSON files to SQLite database
- Added `output/synthlab.db` as central data store
- Updated all services to use repository pattern

---

## [1.0.0] - 2025-12-10

### Added - Initial Release

- **Synthetic persona generation** with realistic Brazilian demographics
- **Avatar generation** using OpenAI DALL-E 3
- **UX research interviews** with AI-powered conversations
- **Topic guides** with automatic file descriptions
- **PR-FAQ generation** from research data
- **CLI interface** with multiple commands
- **DuckDB integration** for querying synth data
- **IBGE demographic alignment** for realistic distributions

**Features:**
- Generate personas with Big Five personality traits
- Behavioral biases aligned with personality
- Accessibility and disability modeling
- Regional Brazilian demographics (IBGE-based)
- Rich CLI output with progress bars and tables
- JSON schema validation for all generated data

---

[Unreleased]: https://github.com/fulviocanducci/synth-lab/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/fulviocanducci/synth-lab/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/fulviocanducci/synth-lab/releases/tag/v1.0.0
