"""
Migra edges de DAGs existentes para usar nomes de variáveis ao invés de IDs.

Atualiza edges no formato:
  DE: {"from": "dag_f01234567_var_001", "to": "dag_f01234567_var_002"}
  PARA: {"from": "sistema_checkout_simplificado", "to": "taxa_conversao"}

Usage:
    DATABASE_URL="postgresql://..." uv run python scripts/migrate_dag_edges_to_names.py
"""

import json
import os
import sys

from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def migrate_dag_edges_to_names(database_url: str, dry_run: bool = True) -> None:
    """
    Migra edges de DAGs para usar nomes de variáveis.

    Args:
        database_url: PostgreSQL connection string
        dry_run: Se True, apenas mostra as mudanças sem aplicar
    """
    engine = create_engine(database_url)

    with Session(engine) as session:
        # Get all DAGs
        result = session.execute(
            text("SELECT id, simulation_id, nodes, edges FROM causal_dags")
        )
        dags = result.fetchall()

        logger.info(f"Found {len(dags)} DAGs to process")

        updated_count = 0
        for dag in dags:
            dag_id, simulation_id, nodes, edges = dag

            # Build mapping from variable ID to name
            id_to_name = {}
            for node in nodes:
                if isinstance(node, dict):
                    # Nodes may be stored as dict with 'id' and 'name' fields
                    node_id = node.get("id")
                    node_name = node.get("name")
                    if node_id and node_name:
                        id_to_name[node_id] = node_name

            if not id_to_name:
                logger.warning(
                    f"DAG {dag_id}: No ID-to-name mapping found, skipping"
                )
                continue

            # Check if edges need migration
            needs_migration = False
            new_edges = []

            for edge in edges:
                if isinstance(edge, dict):
                    from_var = edge.get("from") or edge.get("from_var")
                    to_var = edge.get("to") or edge.get("to_var")

                    # Check if edge uses IDs (contains dag_ prefix)
                    if from_var and from_var.startswith("dag_"):
                        needs_migration = True
                        # Map ID to name
                        new_from = id_to_name.get(from_var, from_var)
                        new_to = id_to_name.get(to_var, to_var)

                        logger.debug(
                            f"  Edge: {from_var} → {to_var} => {new_from} → {new_to}"
                        )

                        new_edge = edge.copy()
                        if "from" in new_edge:
                            new_edge["from"] = new_from
                        if "from_var" in new_edge:
                            new_edge["from_var"] = new_from
                        if "to" in new_edge:
                            new_edge["to"] = new_to
                        if "to_var" in new_edge:
                            new_edge["to_var"] = new_to

                        new_edges.append(new_edge)
                    else:
                        # Edge already uses names
                        new_edges.append(edge)

            if needs_migration:
                logger.info(
                    f"DAG {dag_id} (simulation {simulation_id}): Migrating {len(edges)} edges"
                )

                if not dry_run:
                    # Update edges in database (convert to JSONB)
                    session.execute(
                        text("UPDATE causal_dags SET edges = CAST(:edges AS jsonb) WHERE id = :dag_id"),
                        {"edges": json.dumps(new_edges), "dag_id": dag_id},
                    )
                    updated_count += 1
                else:
                    logger.info(f"  DRY RUN: Would update edges to: {new_edges}")
            else:
                logger.debug(f"DAG {dag_id}: Already using variable names, skipping")

        if not dry_run:
            session.commit()
            logger.success(f"✅ Migrated {updated_count} DAGs")
        else:
            logger.info(f"DRY RUN: Would migrate {updated_count} DAGs")


if __name__ == "__main__":
    import sys

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)

    # Check for --apply flag
    dry_run = "--apply" not in sys.argv

    if dry_run:
        logger.info("Running in DRY RUN mode. Use --apply to actually migrate data.")
    else:
        logger.warning("Running in APPLY mode - will modify database!")

    try:
        migrate_dag_edges_to_names(database_url, dry_run=dry_run)
        sys.exit(0)
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)
