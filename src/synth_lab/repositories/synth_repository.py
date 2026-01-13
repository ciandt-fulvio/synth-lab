"""
Synth repository for synth-lab.

Data access layer for synth persona data in PostgreSQL database.

References:
    - Schema: specs/010-rest-api/data-model.md
    - ORM models: synth_lab.models.orm.synth
"""

import json
from pathlib import Path

from sqlalchemy import func as sqlfunc
from sqlalchemy import select
from sqlalchemy.orm import Session

from synth_lab.models.orm.analysis import AnalysisRun as AnalysisRunORM
from synth_lab.models.orm.analysis import SynthOutcome as SynthOutcomeORM
from synth_lab.models.orm.synth import Synth as SynthORM
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
    VisualDisability)
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
    """Repository for synth data access.

    Uses SQLAlchemy ORM for database operations.
    """

    def __init__(
        self,
session: Session | None = None):
        super().__init__( session=session)

    def list_synths(
        self,
        params: PaginationParams,
        fields: list[str] | None = None,
        synth_group_id: str | None = None) -> PaginatedResponse[SynthSummary]:
        """
        List synths with pagination.

        Args:
            params: Pagination parameters.
            fields: Optional list of fields to include.
            synth_group_id: Optional filter by synth group ID.

        Returns:
            Paginated response with synth summaries.
        """
        stmt = select(SynthORM)
        count_stmt = select(sqlfunc.count()).select_from(SynthORM)

        if synth_group_id:
            stmt = stmt.where(SynthORM.synth_group_id == synth_group_id)
            count_stmt = count_stmt.where(SynthORM.synth_group_id == synth_group_id)

        # Get total count
        total = self.session.execute(count_stmt).scalar() or 0

        # Apply pagination
        stmt = stmt.limit(params.limit).offset(params.offset)
        orm_synths = list(self.session.execute(stmt).scalars().all())

        synths = [self._orm_to_summary(s) for s in orm_synths]
        from synth_lab.models.pagination import PaginationMeta

        meta = PaginationMeta.from_params(total, params)
        return PaginatedResponse(data=synths, pagination=meta)
    def list_by_group_id(
        self,
        synth_group_id: str,
        params: PaginationParams | None = None) -> PaginatedResponse[SynthSummary]:
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
        orm_synth = self.session.get(SynthORM, synth_id)
        if orm_synth is None:
            raise SynthNotFoundError(synth_id)
        return self._orm_to_detail(orm_synth)
    def search(
        self,
        where_clause: str | None = None,
        query: str | None = None,
        params: PaginationParams | None = None) -> PaginatedResponse[SynthSummary]:
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
        orm_synth = self.session.get(SynthORM, synth_id)
        if orm_synth is None:
            raise SynthNotFoundError(synth_id)

        if orm_synth.avatar_path:
            return Path(orm_synth.avatar_path)

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
        from synth_lab.models.orm.analysis import AnalysisRun as AnalysisRunORM
        from synth_lab.models.orm.analysis import SynthOutcome as SynthOutcomeORM

        # Get analysis_id for this experiment
        stmt = select(AnalysisRunORM).where(
            AnalysisRunORM.experiment_id == experiment_id,
            AnalysisRunORM.status == "completed"
        )
        analysis = self.session.execute(stmt).scalar_one_or_none()
        if not analysis:
            raise ValueError(f"No completed analysis found for experiment {experiment_id}")

        analysis_id = analysis.id

        # Get top performers (highest success_rate)
        top_stmt = select(SynthOutcomeORM.synth_id).where(
            SynthOutcomeORM.analysis_id == analysis_id
        ).order_by(SynthOutcomeORM.success_rate.desc()).limit(top_n)
        top_results = self.session.execute(top_stmt).scalars().all()

        # Get bottom performers (lowest success_rate)
        bottom_stmt = select(SynthOutcomeORM.synth_id).where(
            SynthOutcomeORM.analysis_id == analysis_id
        ).order_by(SynthOutcomeORM.success_rate.asc()).limit(top_n)
        bottom_results = self.session.execute(bottom_stmt).scalars().all()

        # Validate we have enough synths
        total_synths = len(top_results) + len(bottom_results)
        if total_synths < top_n * 2:
            raise ValueError(
                f"Insufficient synths for extreme cases: need {top_n * 2}, found {total_synths}"
            )

        return (list(top_results), list(bottom_results))

    def get_synths_for_simulation(
        self,
        experiment_id: str,
        limit: int = 200) -> list[dict]:
        """
        Get synths for Monte Carlo simulation with derived simulation_attributes.

        Retrieves synths from the experiment's synth_group_id and
        derives their simulation_attributes from observables (v2.3.0+) or
        Big Five personality traits (legacy synths).

        Args:
            experiment_id: Experiment ID to get synths for.
            limit: Maximum number of synths to return (default: 200).

        Returns:
            List of dicts with 'id' and 'simulation_attributes' keys.
            simulation_attributes contains 'observables' and 'latent_traits'.

        Raises:
            ValueError: If experiment not found or has no synth group.
        """
        from synth_lab.domain.entities.simulation_attributes import SimulationObservables
        from synth_lab.gen_synth.simulation_attributes import derive_latent_traits
        from synth_lab.models.orm.experiment import Experiment as ExperimentORM

        # Get experiment's synth_group_id
        stmt = select(ExperimentORM).where(ExperimentORM.id == experiment_id)
        experiment = self.session.execute(stmt).scalar_one_or_none()
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        synth_group_id = experiment.synth_group_id
        if not synth_group_id:
            raise ValueError(f"Experiment {experiment_id} has no synth_group_id")

        # Get synths from the experiment's group
        stmt = (
            select(SynthORM)
            .where(
                SynthORM.synth_group_id == synth_group_id,
                SynthORM.data.isnot(None)
            )
            .limit(limit)
        )
        orm_synths = list(self.session.execute(stmt).scalars().all())

        synths = []
        for orm_synth in orm_synths:
            data = orm_synth.data if isinstance(orm_synth.data, dict) else {}

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

            synths.append({"id": orm_synth.id, "simulation_attributes": sim_attrs})

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
                ]),
            SynthFieldInfo(
                name="data.psicografia",
                type="object",
                description="Psychographic data. Access via json_extract(data, '$.psicografia...')",
                nested_fields=["interesses", "contrato_cognitivo"]),
            SynthFieldInfo(
                name="data.deficiencias",
                type="object",
                description="Disability information (IBGE PNS 2019). Access via json_extract(data, '$.deficiencias...')",
                nested_fields=["visual", "auditiva", "motora", "cognitiva"]),
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
                ]),
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
                where_clause[:100] + "...")

        clause_upper = where_clause.upper()

        # Check for blocked keywords
        for keyword in BLOCKED_KEYWORDS:
            if keyword in clause_upper:
                raise InvalidQueryError(
                    f"Keyword '{keyword}' is not allowed in WHERE clause",
                    where_clause)

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
            version=row["version"] if "version" in row.keys() else "2.0.0")

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
                domain_expertise=observables_data.get("domain_expertise", 0.5))

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
                raw=sim_attrs_data)
        except Exception:
            # If formatting fails, return raw only
            return SimulationAttributesForDisplay(
                observables_formatted=[],
                raw=sim_attrs_data)

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
                composicao_familiar=family)

        # Parse psychographics from data
        psicografia = None
        psico_data = data.get("psicografia")
        if psico_data:
            # Cognitive contract
            contract_data = psico_data.get("contrato_cognitivo")
            contract = CognitiveContract(**contract_data) if contract_data else None

            psicografia = Psychographics(
                interesses=psico_data.get("interesses", []),
                contrato_cognitivo=contract)

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
                cognitiva=cognitive)

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
            simulation_attributes=simulation_attributes)

    # =========================================================================
    # ORM conversion methods
    # =========================================================================

    def _orm_to_summary(self, orm_synth: SynthORM) -> SynthSummary:
        """Convert ORM model to SynthSummary."""
        from datetime import datetime

        created_at = orm_synth.created_at
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return SynthSummary(
            id=orm_synth.id,
            synth_group_id=orm_synth.synth_group_id,
            nome=orm_synth.nome or "",
            descricao=orm_synth.descricao,
            link_photo=orm_synth.link_photo,
            avatar_path=orm_synth.avatar_path,
            created_at=created_at or datetime.now(),
            version=orm_synth.version or "2.0.0")

    def _orm_to_detail(self, orm_synth: SynthORM) -> SynthDetail:
        """Convert ORM model to SynthDetail with nested objects."""
        from datetime import datetime

        created_at = orm_synth.created_at
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        # Parse the consolidated 'data' JSON field
        # ORM model stores data as dict already
        data = orm_synth.data or {}

        # Parse demographics from data
        demografia = None
        demo_data = data.get("demografia")
        if demo_data:
            location_data = demo_data.get("localizacao")
            location = Location(**location_data) if location_data else None

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
                composicao_familiar=family)

        # Parse psychographics from data
        psicografia = None
        psico_data = data.get("psicografia")
        if psico_data:
            contract_data = psico_data.get("contrato_cognitivo")
            contract = CognitiveContract(**contract_data) if contract_data else None

            psicografia = Psychographics(
                interesses=psico_data.get("interesses", []),
                contrato_cognitivo=contract)

        # Parse disabilities from data
        deficiencias = None
        def_data = data.get("deficiencias")
        if def_data:
            visual_data = def_data.get("visual")
            visual = VisualDisability(**visual_data) if visual_data else None

            hearing_data = def_data.get("auditiva")
            hearing = HearingDisability(**hearing_data) if hearing_data else None

            motor_data = def_data.get("motora")
            motor = MotorDisability(**motor_data) if motor_data else None

            cognitive_data = def_data.get("cognitiva")
            cognitive = CognitiveDisability(**cognitive_data) if cognitive_data else None

            deficiencias = Disabilities(
                visual=visual,
                auditiva=hearing,
                motora=motor,
                cognitiva=cognitive)

        # Parse observables from data (v2.3.0+)
        observables = data.get("observables")

        # Parse and format simulation attributes
        simulation_attributes = None
        sim_attrs_data = data.get("simulation_attributes")
        if sim_attrs_data:
            simulation_attributes = self._format_simulation_attributes(sim_attrs_data)

        return SynthDetail(
            id=orm_synth.id,
            synth_group_id=orm_synth.synth_group_id,
            nome=orm_synth.nome,
            descricao=orm_synth.descricao,
            link_photo=orm_synth.link_photo,
            avatar_path=orm_synth.avatar_path,
            created_at=created_at,
            version=orm_synth.version or "2.3.0",
            demografia=demografia,
            psicografia=psicografia,
            deficiencias=deficiencias,
            observables=observables,
            simulation_attributes=simulation_attributes)


if __name__ == "__main__":
    import os
    import sys

    # Validation with real database
    all_validation_failures = []
    total_tests = 0

    if not os.getenv("DATABASE_URL"):
        print("DATABASE_URL environment variable is required.")
        print("Set it to your PostgreSQL connection string:")
        print("  export DATABASE_URL='postgresql://user:pass@localhost:5432/synthlab'")
        sys.exit(1)

    from synth_lab.infrastructure.database_v2 import init_database_v2
    init_database_v2()
    repo = SynthRepository()

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

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
