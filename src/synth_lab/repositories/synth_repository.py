"""
Synth repository for synth-lab.

Data access layer for synth persona data in SQLite database.

References:
    - Schema: specs/010-rest-api/data-model.md
"""

import json
from pathlib import Path

from synth_lab.infrastructure.database import DatabaseManager
from synth_lab.models.pagination import PaginatedResponse, PaginationParams
from synth_lab.models.synth import (
    CognitiveContract,
    CognitiveDisability,
    Demographics,
    Disabilities,
    FamilyComposition,
    HearingDisability,
    Location,
    MotorDisability,
    Psychographics,
    SimulationAttributesForDisplay,
    SynthDetail,
    SynthFieldInfo,
    SynthSummary,
    VisualDisability,
)
from synth_lab.repositories.base import BaseRepository
from synth_lab.services.errors import InvalidQueryError, SynthNotFoundError

# Dangerous SQL keywords that should not be in WHERE clauses
# This is a blacklist approach for power-user WHERE clause functionality
# WARNING: This feature should only be exposed to trusted users
BLOCKED_KEYWORDS = frozenset(
    [
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "CREATE",
        "ALTER",
        "TRUNCATE",
        "EXEC",
        "EXECUTE",
        "GRANT",
        "REVOKE",
        "UNION",
        "INTO",
        "LOAD",
        "ATTACH",
        "DETACH",
        "PRAGMA",
        "VACUUM",
        "REINDEX",
        "--",
        ";",
        "/*",
        "*/",
        "@@",
        "CHAR(",
        "0x",
    ]
)

# Maximum length for WHERE clauses to prevent DoS
MAX_WHERE_CLAUSE_LENGTH = 1000


class SynthRepository(BaseRepository):
    """Repository for synth data access."""

    def __init__(self, db: DatabaseManager | None = None):
        super().__init__(db)

    def list_synths(
        self,
        params: PaginationParams,
        fields: list[str] | None = None,
        synth_group_id: str | None = None,
    ) -> PaginatedResponse[SynthSummary]:
        """
        List synths with pagination.

        Args:
            params: Pagination parameters.
            fields: Optional list of fields to include.
            synth_group_id: Optional filter by synth group ID.

        Returns:
            Paginated response with synth summaries.
        """
        # Build field list
        select_fields = self._build_select_fields(fields)
        base_query = f"SELECT {select_fields} FROM synths"

        # Add group filter if specified (using parameterized query)
        query_params = None
        if synth_group_id:
            base_query += " WHERE synth_group_id = ?"
            query_params = (synth_group_id,)

        rows, meta = self._paginate_query(base_query, params, query_params=query_params)

        synths = [self._row_to_summary(row) for row in rows]
        return PaginatedResponse(data=synths, pagination=meta)

    def list_by_group_id(
        self,
        synth_group_id: str,
        params: PaginationParams | None = None,
    ) -> PaginatedResponse[SynthSummary]:
        """
        List synths by group ID with pagination.

        Args:
            synth_group_id: Synth group ID to filter by.
            params: Pagination parameters.

        Returns:
            Paginated response with synth summaries.
        """
        params = params or PaginationParams()
        return self.list_synths(params, synth_group_id=synth_group_id)

    def get_by_id(self, synth_id: str) -> SynthDetail:
        """
        Get a synth by ID with full details.

        Args:
            synth_id: 6-character synth ID.

        Returns:
            SynthDetail with all nested data.

        Raises:
            SynthNotFoundError: If synth not found.
        """
        row = self.db.fetchone(
            "SELECT * FROM synths WHERE id = ?",
            (synth_id,),
        )
        if row is None:
            raise SynthNotFoundError(synth_id)

        return self._row_to_detail(row)

    def search(
        self,
        where_clause: str | None = None,
        query: str | None = None,
        params: PaginationParams | None = None,
    ) -> PaginatedResponse[SynthSummary]:
        """
        Search synths with WHERE clause or full query.

        Args:
            where_clause: SQL WHERE clause (e.g., "idade > 30").
            query: Full SELECT query (limited to SELECT only).
            params: Pagination parameters.

        Returns:
            Paginated response with matching synths.

        Raises:
            InvalidQueryError: If query is invalid or unsafe.
        """
        params = params or PaginationParams()

        if query:
            # Validate and use full query
            self._validate_query(query)
            base_query = query
        elif where_clause:
            # Build query from WHERE clause
            self._validate_where_clause(where_clause)
            base_query = f"SELECT * FROM synths WHERE {where_clause}"
        else:
            base_query = "SELECT * FROM synths"

        rows, meta = self._paginate_query(base_query, params)
        synths = [self._row_to_summary(row) for row in rows]
        return PaginatedResponse(data=synths, pagination=meta)

    def get_avatar_path(self, synth_id: str) -> Path:
        """
        Get the avatar file path for a synth.

        Args:
            synth_id: 6-character synth ID.

        Returns:
            Path to avatar PNG file.

        Raises:
            SynthNotFoundError: If synth not found.
        """
        row = self.db.fetchone(
            "SELECT avatar_path FROM synths WHERE id = ?",
            (synth_id,),
        )
        if row is None:
            raise SynthNotFoundError(synth_id)

        if row["avatar_path"]:
            return Path(row["avatar_path"])

        # Default path if not in database
        from synth_lab.infrastructure.config import AVATARS_DIR

        return AVATARS_DIR / f"{synth_id}.png"

    def get_extreme_cases(self, experiment_id: str, top_n: int = 5) -> tuple[list[str], list[str]]:
        """
        Get extreme case synth IDs for an experiment (top and bottom performers).

        Args:
            experiment_id: Experiment ID to get extreme cases for.
            top_n: Number of top/bottom performers to return (default: 5).

        Returns:
            Tuple of (top_performer_ids, bottom_performer_ids).
            Each list contains synth IDs ordered by success_rate.

        Raises:
            ValueError: If experiment has no analysis or insufficient synths.
        """
        # Get analysis_id for this experiment
        analysis_row = self.db.fetchone(
            "SELECT id FROM analysis_runs WHERE experiment_id = ? AND status = 'completed'",
            (experiment_id,),
        )
        if not analysis_row:
            raise ValueError(f"No completed analysis found for experiment {experiment_id}")

        analysis_id = analysis_row["id"]

        # Get top performers (highest success_rate)
        top_rows = self.db.fetchall(
            """
            SELECT synth_id, success_rate
            FROM synth_outcomes
            WHERE analysis_id = ?
            ORDER BY success_rate DESC
            LIMIT ?
            """,
            (analysis_id, top_n),
        )

        # Get bottom performers (lowest success_rate)
        bottom_rows = self.db.fetchall(
            """
            SELECT synth_id, success_rate
            FROM synth_outcomes
            WHERE analysis_id = ?
            ORDER BY success_rate ASC
            LIMIT ?
            """,
            (analysis_id, top_n),
        )

        # Validate we have enough synths
        total_synths = len(top_rows) + len(bottom_rows)
        if total_synths < top_n * 2:
            raise ValueError(
                f"Insufficient synths for extreme cases: need {top_n * 2}, found {total_synths}"
            )

        top_performer_ids = [row["synth_id"] for row in top_rows]
        bottom_performer_ids = [row["synth_id"] for row in bottom_rows]

        return (top_performer_ids, bottom_performer_ids)

    def get_synths_for_simulation(
        self,
        experiment_id: str,
        limit: int = 200,
    ) -> list[dict]:
        """
        Get synths for Monte Carlo simulation with derived simulation_attributes.

        Retrieves synths that participated in an experiment's analysis and
        derives their simulation_attributes from observables (v2.3.0+) or
        Big Five personality traits (legacy synths).

        Args:
            experiment_id: Experiment ID to get synths for.
            limit: Maximum number of synths to return (default: 200).

        Returns:
            List of dicts with 'id' and 'simulation_attributes' keys.
            simulation_attributes contains 'observables' and 'latent_traits'.

        Raises:
            ValueError: If experiment has no completed analysis.
        """
        import json

        from synth_lab.domain.entities.simulation_attributes import SimulationObservables
        from synth_lab.gen_synth.simulation_attributes import derive_latent_traits

        # Get analysis_id for this experiment
        analysis_row = self.db.fetchone(
            "SELECT id FROM analysis_runs WHERE experiment_id = ? AND status = 'completed'",
            (experiment_id,),
        )
        if not analysis_row:
            raise ValueError(f"No completed analysis found for experiment {experiment_id}")

        analysis_id = analysis_row["id"]

        # Get synths that participated in this analysis
        rows = self.db.fetchall(
            """
            SELECT DISTINCT s.id, s.data
            FROM synths s
            INNER JOIN synth_outcomes so ON s.id = so.synth_id
            WHERE so.analysis_id = ?
              AND s.data IS NOT NULL
            LIMIT ?
            """,
            (analysis_id, limit),
        )

        synths = []
        for row in rows:
            data = json.loads(row["data"]) if row["data"] else {}

            # Check for observables (v2.3.0+ synths)
            existing_observables = data.get("observables")
            if existing_observables and all(
                k in existing_observables
                for k in [
                    "digital_literacy",
                    "similar_tool_experience",
                    "motor_ability",
                    "time_availability",
                    "domain_expertise",
                ]
            ):
                # Use existing observables and derive latent traits
                observables = SimulationObservables.model_validate(existing_observables)
                latent_traits = derive_latent_traits(observables)

                sim_attrs = {
                    "observables": observables.model_dump(),
                    "latent_traits": latent_traits.model_dump(),
                }
            else:
                # Legacy synth - derive from Big Five personality traits
                big_five = data.get("psicografia", {}).get("personalidade_big_five", {})
                openness = big_five.get("abertura", 50) / 100
                conscientiousness = big_five.get("conscienciosidade", 50) / 100
                extraversion = big_five.get("extroversao", 50) / 100
                agreeableness = big_five.get("amabilidade", 50) / 100
                neuroticism = big_five.get("neuroticismo", 50) / 100

                # Derive latent traits from Big Five
                capability_mean = round(0.5 * openness + 0.5 * conscientiousness, 3)
                trust_mean = round(0.6 * agreeableness + 0.4 * (1 - neuroticism), 3)
                friction_tolerance_mean = round(
                    0.5 * conscientiousness + 0.5 * (1 - neuroticism), 3
                )
                exploration_prob = round(0.6 * openness + 0.4 * extraversion, 3)

                sim_attrs = {
                    "observables": {
                        "digital_literacy": round(openness * 0.7 + conscientiousness * 0.3, 3),
                        "similar_tool_experience": 0.5,
                        "motor_ability": 1.0,
                        "time_availability": round(1 - neuroticism * 0.3, 3),
                        "domain_expertise": 0.5,
                    },
                    "latent_traits": {
                        "capability_mean": capability_mean,
                        "trust_mean": trust_mean,
                        "friction_tolerance_mean": friction_tolerance_mean,
                        "exploration_prob": exploration_prob,
                    },
                }

            synths.append({"id": row["id"], "simulation_attributes": sim_attrs})

        return synths

    def get_fields(self) -> list[SynthFieldInfo]:
        """Get available synth field metadata following schema v1.

        Note: All nested fields are stored in a single 'data' JSON column.
        Use json_extract(data, '$.demografia.idade') for SQL queries.
        """
        return [
            SynthFieldInfo(name="id", type="string", description="6-character unique ID"),
            SynthFieldInfo(name="nome", type="string", description="Display name"),
            SynthFieldInfo(name="descricao", type="string", description="Brief description"),
            SynthFieldInfo(name="created_at", type="datetime", description="Creation timestamp"),
            SynthFieldInfo(
                name="data.demografia",
                type="object",
                description="Demographic data (IBGE Censo 2022, PNAD 2023). Access via json_extract(data, '$.demografia...')",
                nested_fields=[
                    "idade",
                    "genero_biologico",
                    "identidade_genero",
                    "raca_etnia",
                    "localizacao",
                    "escolaridade",
                    "renda_mensal",
                    "ocupacao",
                    "estado_civil",
                    "composicao_familiar",
                ],
            ),
            SynthFieldInfo(
                name="data.psicografia",
                type="object",
                description="Psychographic data. Access via json_extract(data, '$.psicografia...')",
                nested_fields=["interesses", "contrato_cognitivo"],
            ),
            SynthFieldInfo(
                name="data.deficiencias",
                type="object",
                description="Disability information (IBGE PNS 2019). Access via json_extract(data, '$.deficiencias...')",
                nested_fields=["visual", "auditiva", "motora", "cognitiva"],
            ),
            SynthFieldInfo(
                name="data.observables",
                type="object",
                description="Observable simulation attributes (v2.3.0+). Access via json_extract(data, '$.observables...')",
                nested_fields=[
                    "digital_literacy",
                    "similar_tool_experience",
                    "motor_ability",
                    "time_availability",
                    "domain_expertise",
                ],
            ),
        ]

    def _build_select_fields(self, fields: list[str] | None) -> str:
        """Build SELECT field list from requested fields."""
        if not fields:
            return "*"

        # Validate field names (alphanumeric and underscore only)
        valid_fields = []
        for field in fields:
            if field.replace("_", "").isalnum():
                valid_fields.append(field)

        # Always include id
        if "id" not in valid_fields:
            valid_fields.insert(0, "id")

        return ", ".join(valid_fields)

    def _validate_query(self, query: str) -> None:
        """Validate that a full query is safe."""
        query_upper = query.upper().strip()

        # Must be a SELECT query
        if not query_upper.startswith("SELECT"):
            raise InvalidQueryError("Only SELECT queries are allowed", query)

        # Check for blocked keywords
        for keyword in BLOCKED_KEYWORDS:
            if keyword in query_upper:
                raise InvalidQueryError(f"Keyword '{keyword}' is not allowed", query)

    def _validate_where_clause(self, where_clause: str) -> None:
        """
        Validate that a WHERE clause is safe.

        WARNING: This is a power-user feature. The blacklist approach cannot
        guarantee 100% protection against SQL injection. Only expose this
        to trusted users.

        Args:
            where_clause: SQL WHERE clause to validate.

        Raises:
            InvalidQueryError: If clause contains blocked keywords or is too long.
        """
        # Check length limit
        if len(where_clause) > MAX_WHERE_CLAUSE_LENGTH:
            raise InvalidQueryError(
                f"WHERE clause exceeds max length of {MAX_WHERE_CLAUSE_LENGTH} characters",
                where_clause[:100] + "...",
            )

        clause_upper = where_clause.upper()

        # Check for blocked keywords
        for keyword in BLOCKED_KEYWORDS:
            if keyword in clause_upper:
                raise InvalidQueryError(
                    f"Keyword '{keyword}' is not allowed in WHERE clause",
                    where_clause,
                )

    def _row_to_summary(self, row) -> SynthSummary:
        """Convert a database row to SynthSummary."""
        from datetime import datetime

        created_at = row["created_at"] if "created_at" in row.keys() else None
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return SynthSummary(
            id=row["id"],
            synth_group_id=row["synth_group_id"] if "synth_group_id" in row.keys() else None,
            nome=row["nome"] if "nome" in row.keys() else "",
            descricao=row["descricao"] if "descricao" in row.keys() else None,
            link_photo=row["link_photo"] if "link_photo" in row.keys() else None,
            avatar_path=row["avatar_path"] if "avatar_path" in row.keys() else None,
            created_at=created_at or datetime.now(),
            version=row["version"] if "version" in row.keys() else "2.0.0",
        )

    def _format_simulation_attributes(
        self, sim_attrs_data: dict
    ) -> SimulationAttributesForDisplay | None:
        """Format simulation attributes with labels for PM display."""
        from synth_lab.domain.entities.simulation_attributes import SimulationObservables
        from synth_lab.services.observable_labels import format_observables_with_labels

        observables_data = sim_attrs_data.get("observables", {})
        if not observables_data:
            return None

        # Create SimulationObservables entity
        try:
            observables = SimulationObservables(
                digital_literacy=observables_data.get("digital_literacy", 0.5),
                similar_tool_experience=observables_data.get("similar_tool_experience", 0.5),
                motor_ability=observables_data.get("motor_ability", 1.0),
                time_availability=observables_data.get("time_availability", 0.5),
                domain_expertise=observables_data.get("domain_expertise", 0.5),
            )

            # Format with labels
            formatted = format_observables_with_labels(observables)
            formatted_dicts = [
                {
                    "key": f.key,
                    "name": f.name,
                    "value": f.value,
                    "label": f.label,
                    "description": f.description,
                }
                for f in formatted
            ]

            return SimulationAttributesForDisplay(
                observables_formatted=formatted_dicts,
                raw=sim_attrs_data,
            )
        except Exception:
            # If formatting fails, return raw only
            return SimulationAttributesForDisplay(
                observables_formatted=[],
                raw=sim_attrs_data,
            )

    def _row_to_detail(self, row) -> SynthDetail:
        """Convert a database row to SynthDetail with nested objects following schema v1."""
        from datetime import datetime

        created_at = row["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        # Parse the consolidated 'data' JSON field
        data = {}
        if row["data"]:
            data = json.loads(row["data"])

        # Parse demographics from data
        demografia = None
        demo_data = data.get("demografia")
        if demo_data:
            # Location
            location_data = demo_data.get("localizacao")
            location = Location(**location_data) if location_data else None

            # Family composition
            family_data = demo_data.get("composicao_familiar")
            family = FamilyComposition(**family_data) if family_data else None

            demografia = Demographics(
                idade=demo_data.get("idade"),
                genero_biologico=demo_data.get("genero_biologico"),
                identidade_genero=demo_data.get("identidade_genero"),
                raca_etnia=demo_data.get("raca_etnia"),
                localizacao=location,
                escolaridade=demo_data.get("escolaridade"),
                renda_mensal=demo_data.get("renda_mensal"),
                ocupacao=demo_data.get("ocupacao"),
                estado_civil=demo_data.get("estado_civil"),
                composicao_familiar=family,
            )

        # Parse psychographics from data
        psicografia = None
        psico_data = data.get("psicografia")
        if psico_data:
            # Cognitive contract
            contract_data = psico_data.get("contrato_cognitivo")
            contract = CognitiveContract(**contract_data) if contract_data else None

            psicografia = Psychographics(
                interesses=psico_data.get("interesses", []),
                contrato_cognitivo=contract,
            )

        # Parse disabilities from data
        deficiencias = None
        def_data = data.get("deficiencias")
        if def_data:
            # Visual disability
            visual_data = def_data.get("visual")
            visual = VisualDisability(**visual_data) if visual_data else None

            # Hearing disability
            hearing_data = def_data.get("auditiva")
            hearing = HearingDisability(**hearing_data) if hearing_data else None

            # Motor disability
            motor_data = def_data.get("motora")
            motor = MotorDisability(**motor_data) if motor_data else None

            # Cognitive disability
            cognitive_data = def_data.get("cognitiva")
            cognitive = CognitiveDisability(**cognitive_data) if cognitive_data else None

            deficiencias = Disabilities(
                visual=visual,
                auditiva=hearing,
                motora=motor,
                cognitiva=cognitive,
            )

        # Parse observables from data (v2.3.0+)
        observables = data.get("observables")

        # Parse and format simulation attributes
        simulation_attributes = None
        sim_attrs_data = data.get("simulation_attributes")
        if sim_attrs_data:
            simulation_attributes = self._format_simulation_attributes(sim_attrs_data)

        return SynthDetail(
            id=row["id"],
            synth_group_id=row["synth_group_id"] if "synth_group_id" in row.keys() else None,
            nome=row["nome"],
            descricao=row["descricao"],
            link_photo=row["link_photo"],
            avatar_path=row["avatar_path"],
            created_at=created_at,
            version=row["version"] or "2.3.0",
            demografia=demografia,
            psicografia=psicografia,
            deficiencias=deficiencias,
            observables=observables,
            simulation_attributes=simulation_attributes,
        )


if __name__ == "__main__":
    import sys

    from synth_lab.infrastructure.config import DB_PATH
    from synth_lab.infrastructure.database import DatabaseManager

    # Validation with real database
    all_validation_failures = []
    total_tests = 0

    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}. Run migration first.")
        sys.exit(1)

    db = DatabaseManager(DB_PATH)
    repo = SynthRepository(db)

    # Test 1: List synths
    total_tests += 1
    try:
        result = repo.list_synths(PaginationParams(limit=10))
        if len(result.data) == 0:
            all_validation_failures.append("No synths found in database")
        if result.pagination.total < 1:
            all_validation_failures.append(f"Total should be at least 1: {result.pagination.total}")
        print(f"  Found {result.pagination.total} synths")
    except Exception as e:
        all_validation_failures.append(f"List synths failed: {e}")

    # Test 2: Get synth by ID
    total_tests += 1
    try:
        # Get first synth ID from list
        result = repo.list_synths(PaginationParams(limit=1))
        if result.data:
            synth_id = result.data[0].id
            synth = repo.get_by_id(synth_id)
            if synth.id != synth_id:
                all_validation_failures.append(f"ID mismatch: {synth.id} != {synth_id}")
            print(f"  Retrieved synth: {synth.nome}")
    except Exception as e:
        all_validation_failures.append(f"Get by ID failed: {e}")

    # Test 3: Get non-existent synth
    total_tests += 1
    try:
        repo.get_by_id("zzz999")
        all_validation_failures.append("Should raise SynthNotFoundError for non-existent synth")
    except SynthNotFoundError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Wrong exception type: {e}")

    # Test 4: Search with WHERE clause
    total_tests += 1
    try:
        result = repo.search(where_clause="1=1")  # Match all
        if result.pagination.total < 1:
            all_validation_failures.append("Search should find synths")
    except Exception as e:
        all_validation_failures.append(f"Search with WHERE failed: {e}")

    # Test 5: Validate dangerous query rejection
    total_tests += 1
    try:
        repo.search(where_clause="1=1; DROP TABLE synths")
        all_validation_failures.append("Should reject dangerous WHERE clause")
    except InvalidQueryError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Wrong exception for dangerous query: {e}")

    # Test 6: Get fields metadata
    total_tests += 1
    try:
        fields = repo.get_fields()
        if len(fields) < 5:
            all_validation_failures.append(f"Expected at least 5 fields, got {len(fields)}")
        field_names = [f.name for f in fields]
        if "id" not in field_names:
            all_validation_failures.append("Fields should include 'id'")
    except Exception as e:
        all_validation_failures.append(f"Get fields failed: {e}")

    # Test 7: Get avatar path
    total_tests += 1
    try:
        result = repo.list_synths(PaginationParams(limit=1))
        if result.data:
            synth_id = result.data[0].id
            path = repo.get_avatar_path(synth_id)
            if not str(path).endswith(".png"):
                all_validation_failures.append(f"Avatar path should end with .png: {path}")
    except Exception as e:
        all_validation_failures.append(f"Get avatar path failed: {e}")

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
