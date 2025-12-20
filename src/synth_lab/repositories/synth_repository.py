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
    AccessibilityPrefs,
    Demographics,
    DeviceInfo,
    Disabilities,
    Location,
    PlatformFamiliarity,
    Psychographics,
    SynthDetail,
    SynthFieldInfo,
    SynthSummary,
    TechCapabilities,
)
from synth_lab.repositories.base import BaseRepository
from synth_lab.services.errors import InvalidQueryError, SynthNotFoundError


# Dangerous SQL keywords that should not be in WHERE clauses
BLOCKED_KEYWORDS = frozenset([
    "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE",
    "EXEC", "EXECUTE", "GRANT", "REVOKE", "--", ";", "/*", "*/",
])


class SynthRepository(BaseRepository):
    """Repository for synth data access."""

    def __init__(self, db: DatabaseManager | None = None):
        super().__init__(db)

    def list_synths(
        self,
        params: PaginationParams,
        fields: list[str] | None = None,
    ) -> PaginatedResponse[SynthSummary]:
        """
        List synths with pagination.

        Args:
            params: Pagination parameters.
            fields: Optional list of fields to include.

        Returns:
            Paginated response with synth summaries.
        """
        # Build field list
        select_fields = self._build_select_fields(fields)
        base_query = f"SELECT {select_fields} FROM synths"

        rows, meta = self._paginate_query(base_query, params)

        synths = [self._row_to_summary(row) for row in rows]
        return PaginatedResponse(data=synths, pagination=meta)

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

    def get_fields(self) -> list[SynthFieldInfo]:
        """Get available synth field metadata."""
        return [
            SynthFieldInfo(name="id", type="string", description="6-character unique ID"),
            SynthFieldInfo(name="nome", type="string", description="Display name"),
            SynthFieldInfo(name="arquetipo", type="string", description="Archetype classification"),
            SynthFieldInfo(name="descricao", type="string", description="Brief description"),
            SynthFieldInfo(name="created_at", type="datetime", description="Creation timestamp"),
            SynthFieldInfo(
                name="demografia",
                type="object",
                description="Demographic data",
                nested_fields=["idade", "genero", "localizacao", "educacao", "ocupacao", "renda_familiar"],
            ),
            SynthFieldInfo(
                name="psicografia",
                type="object",
                description="Psychographic data",
                nested_fields=["valores", "interesses", "estilo_vida", "personalidade"],
            ),
            SynthFieldInfo(
                name="capacidades_tecnologicas",
                type="object",
                description="Tech capabilities",
                nested_fields=["nivel_geral", "dispositivos", "apps_frequentes", "comportamento_digital"],
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
        """Validate that a WHERE clause is safe."""
        clause_upper = where_clause.upper()

        # Check for blocked keywords
        for keyword in BLOCKED_KEYWORDS:
            if keyword in clause_upper:
                raise InvalidQueryError(f"Keyword '{keyword}' is not allowed in WHERE clause", where_clause)

    def _row_to_summary(self, row) -> SynthSummary:
        """Convert a database row to SynthSummary."""
        from datetime import datetime

        created_at = row["created_at"] if "created_at" in row.keys() else None
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return SynthSummary(
            id=row["id"],
            nome=row["nome"] if "nome" in row.keys() else "",
            arquetipo=row["arquetipo"] if "arquetipo" in row.keys() else None,
            descricao=row["descricao"] if "descricao" in row.keys() else None,
            link_photo=row["link_photo"] if "link_photo" in row.keys() else None,
            avatar_path=row["avatar_path"] if "avatar_path" in row.keys() else None,
            created_at=created_at or datetime.now(),
            version=row["version"] if "version" in row.keys() else "2.0.0",
        )

    def _row_to_detail(self, row) -> SynthDetail:
        """Convert a database row to SynthDetail with nested objects."""
        from datetime import datetime

        created_at = row["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        # Parse JSON columns
        demografia = None
        if row["demografia"]:
            demo_data = json.loads(row["demografia"])
            location_data = demo_data.get("localizacao")
            location = Location(**location_data) if location_data else None
            demografia = Demographics(
                idade=demo_data.get("idade"),
                genero=demo_data.get("genero"),
                localizacao=location,
                educacao=demo_data.get("educacao"),
                ocupacao=demo_data.get("ocupacao"),
                renda_familiar=demo_data.get("renda_familiar"),
            )

        psicografia = None
        if row["psicografia"]:
            psico_data = json.loads(row["psicografia"])
            psicografia = Psychographics(
                valores=psico_data.get("valores", []),
                interesses=psico_data.get("interesses", []),
                estilo_vida=psico_data.get("estilo_vida"),
                personalidade=psico_data.get("personalidade"),
            )

        deficiencias = None
        if row["deficiencias"]:
            def_data = json.loads(row["deficiencias"])
            deficiencias = Disabilities(
                tipo=def_data.get("tipo"),
                descricao=def_data.get("descricao"),
                nivel=def_data.get("nivel"),
            )

        capacidades_tecnologicas = None
        if row["capacidades_tecnologicas"]:
            tech_data = json.loads(row["capacidades_tecnologicas"])

            # Handle dispositivos - can be dict, list, or None
            dispositivos = tech_data.get("dispositivos")
            if isinstance(dispositivos, dict):
                dispositivos = DeviceInfo(**dispositivos)
            elif isinstance(dispositivos, list):
                pass  # Keep as list

            # Handle nested objects
            prefs = tech_data.get("preferencias_acessibilidade")
            if isinstance(prefs, dict):
                prefs = AccessibilityPrefs(**prefs)

            familiarity = tech_data.get("familiaridade_plataformas")
            if isinstance(familiarity, dict):
                familiarity = PlatformFamiliarity(**familiarity)

            capacidades_tecnologicas = TechCapabilities(
                nivel_geral=tech_data.get("nivel_geral"),
                apps_frequentes=tech_data.get("apps_frequentes", []),
                comportamento_digital=tech_data.get("comportamento_digital"),
                alfabetizacao_digital=tech_data.get("alfabetizacao_digital"),
                dispositivos=dispositivos,
                preferencias_acessibilidade=prefs,
                velocidade_digitacao=tech_data.get("velocidade_digitacao"),
                frequencia_internet=tech_data.get("frequencia_internet"),
                familiaridade_plataformas=familiarity,
            )

        return SynthDetail(
            id=row["id"],
            nome=row["nome"],
            arquetipo=row["arquetipo"],
            descricao=row["descricao"],
            link_photo=row["link_photo"],
            avatar_path=row["avatar_path"],
            created_at=created_at,
            version=row["version"] or "2.0.0",
            demografia=demografia,
            psicografia=psicografia,
            deficiencias=deficiencias,
            capacidades_tecnologicas=capacidades_tecnologicas,
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
