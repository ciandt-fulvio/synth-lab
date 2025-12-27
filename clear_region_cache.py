"""
Script para limpar cache de análises de região.
Execute: uv run python clear_region_cache.py [SIMULATION_ID]
"""

import sys
from synth_lab.infrastructure.database import DatabaseManager

db = DatabaseManager("output/synthlab.db")

if len(sys.argv) > 1:
    # Limpar apenas uma simulação específica
    simulation_id = sys.argv[1]
    sql = "DELETE FROM region_analyses WHERE simulation_id = ?"
    cursor = db.execute(sql, (simulation_id,))
    deleted = cursor.rowcount
    print(f"✅ Deletadas {deleted} regiões da simulação {simulation_id}")
else:
    # Limpar todas as regiões
    sql = "DELETE FROM region_analyses"
    cursor = db.execute(sql)
    deleted = cursor.rowcount
    print(f"✅ Deletadas {deleted} regiões (todas as simulações)")

print("   Cache limpo! Próxima análise usará os novos parâmetros.")
