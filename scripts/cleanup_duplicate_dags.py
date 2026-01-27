"""
Clean up duplicate DAG records keeping only the most recent one per simulation.
"""
import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://synthlab:synthlab@localhost:5432/synthlab")
engine = create_engine(DATABASE_URL)

with engine.begin() as conn:
    # Find simulations with multiple DAGs of same version
    result = conn.execute(text("""
        WITH latest_dags AS (
            SELECT DISTINCT ON (simulation_id, version) 
                id,
                simulation_id,
                version
            FROM causal_dags
            ORDER BY simulation_id, version DESC, created_at DESC
        )
        SELECT id FROM latest_dags
    """))
    
    keep_ids = [row[0] for row in result]
    print(f"Keeping {len(keep_ids)} DAGs")
    
    # Delete all DAGs not in the keep list
    result = conn.execute(text("""
        DELETE FROM causal_dags
        WHERE id NOT IN :keep_ids
        RETURNING id, simulation_id
    """), {"keep_ids": tuple(keep_ids)})
    
    deleted = result.fetchall()
    print(f"Deleted {len(deleted)} duplicate DAGs")
    for dag_id, sim_id in deleted[:5]:
        print(f"  - {dag_id} (sim: {sim_id})")
    if len(deleted) > 5:
        print(f"  ... and {len(deleted) - 5} more")

print("✅ Cleanup complete")
