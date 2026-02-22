# Análises de Batch Simulation

Guia de referência para análises quantitativas com dados de batch.

## Estrutura de dados relevante

```
simulation_batches          -- 1 batch por experimento/rodada
  └── simulation_runs       -- 1 run por cenário
        ├── product_values  -- JSONB: {"Facilidade": "high", "Transparência": "low"}
        ├── stats           -- JSONB: {mean, median, std, p10, p90}
        └── per_synth_outcomes -- JSONB: {"syn_abc": 0.72, "syn_def": 0.31, ...}

synths
  └── data                  -- JSONB com demographics + sensitivities
        ├── demografia.idade, renda_mensal, escolaridade, ...
        └── sensitivities.risk_aversion, digital_capability, ...
```

---

## Análises disponíveis

### 1. Ranking de cenários

**Pergunta:** Qual combinação de calibrações de produto gera maior adoção?

**Dados necessários:** `simulation_runs` do batch (só `stats` + `product_values`)

**Como fazer:**

```python
# API
GET /quantitative/scenario-batch/{batch_id}?experiment_id=...
# Retorna todos os runs com stats e product_values

# Código
runs = sorted(batch.runs, key=lambda r: r.stats["mean"], reverse=True)
best  = runs[0]   # maior mean
worst = runs[-1]  # menor mean
```

**Campos úteis:** `stats.mean`, `stats.p10`, `stats.p90`, `stats.std`

---

### 2. Sensibilidade por produto

**Pergunta:** Qual nó de produto tem mais impacto na adoção?

**Dados necessários:** `simulation_runs` do batch

**Como fazer:**

```python
# Para cada nó de produto, calcular variação média de adoção
# entre runs onde o nó está em "high" vs "low"

from collections import defaultdict

by_node_level = defaultdict(list)
for run in batch_runs:
    for node, level in run.product_values.items():
        by_node_level[(node, level)].append(run.stats["mean"])

for node in product_nodes:
    mean_high = avg(by_node_level[(node, "high")])
    mean_low  = avg(by_node_level[(node, "low")])
    impact    = mean_high - mean_low  # pp de impacto
```

---

### 3. Synths sensíveis a cenário

**Pergunta:** Quais synths mudam mais de comportamento entre o melhor e o pior cenário?

**Dados necessários:** `per_synth_outcomes` de 2 runs + tabela `synths`

**Como fazer:**

```python
# 1. Pegar best e worst run
best_outcomes  = best_run.per_synth_outcomes   # {synth_id: float}
worst_outcomes = worst_run.per_synth_outcomes

# 2. Calcular delta por synth
deltas = {
    sid: best_outcomes[sid] - worst_outcomes[sid]
    for sid in best_outcomes
}

# 3. Ordenar
most_sensitive = sorted(deltas.items(), key=lambda x: abs(x[1]), reverse=True)

# 4. Buscar perfil dos top-N
top_ids = [sid for sid, _ in most_sensitive[:20]]
# SELECT * FROM synths WHERE id = ANY(:ids)
```

---

### 4. Segmentação por demografia

**Pergunta:** Qual segmento demográfico se beneficia mais do melhor cenário?

**Dados necessários:** `per_synth_outcomes` do best run + `synths.data`

**Como fazer:**

```python
# JOIN em Python (ou SQL via JSONB)
for synth_id, outcome in best_run.per_synth_outcomes.items():
    synth = synths_by_id[synth_id]
    idade = synth["data"]["demografia"]["idade"]
    renda = synth["data"]["demografia"]["renda_mensal"]
    # agrupar por faixa e calcular média de outcome

# SQL equivalente (PostgreSQL JSONB)
SELECT
    data->'demografia'->>'escolaridade' AS escolaridade,
    AVG((per_synth_outcomes->>s.id)::float) AS mean_outcome
FROM simulation_runs sr
CROSS JOIN synths s
WHERE sr.id = :run_id
  AND s.synth_group_id = :group_id
GROUP BY 1
ORDER BY 2 DESC
```

---

### 5. Correlação produto × perfil

**Pergunta:** Synths com alto `risk_aversion` respondem diferente quando `Transparência = high`?

**Dados necessários:** `per_synth_outcomes` de runs filtrados + `synths.data.sensitivities`

**Como fazer:**

```python
# 1. Filtrar runs onde Transparência = high
transparency_high_runs = [
    r for r in batch_runs
    if r.product_values.get("Transparência") == "high"
]

# 2. Agregar outcome médio por synth nesses runs
outcomes_avg = {}
for run in transparency_high_runs:
    for sid, outcome in run.per_synth_outcomes.items():
        outcomes_avg.setdefault(sid, []).append(outcome)
outcomes_avg = {sid: avg(vals) for sid, vals in outcomes_avg.items()}

# 3. Cruzar com risk_aversion
for synth_id, outcome in outcomes_avg.items():
    risk = synths_by_id[synth_id]["data"]["sensitivities"]["risk_aversion"]
    # scatter plot: risk_aversion × outcome
    # correlação de Pearson/Spearman
```

---

### 6. Cluster de synths

**Pergunta:** Existem grupos naturais de synths com padrão de adoção similar entre cenários?

**Dados necessários:** `per_synth_outcomes` de todos os runs do batch

**Como fazer:**

```python
import numpy as np
from sklearn.cluster import KMeans

# Montar matriz: linhas = synths, colunas = cenários (runs)
synth_ids = list(batch_runs[0].per_synth_outcomes.keys())
run_ids   = [r.id for r in batch_runs]

matrix = np.array([
    [run.per_synth_outcomes.get(sid, 0.0) for run in batch_runs]
    for sid in synth_ids
])
# shape: (n_synths, n_scenarios) ex: (1000, 100)

# Clusterizar
kmeans = KMeans(n_clusters=4)
labels = kmeans.fit_predict(matrix)

# Associar cluster → perfil demográfico
for i, sid in enumerate(synth_ids):
    cluster = labels[i]
    demo    = synths_by_id[sid]["data"]["demografia"]
```

---

## Caminho no sistema

### Buscar batch e runs

```
GET /quantitative/scenario-batch/{batch_id}?experiment_id={exp_id}
→ MultiScenarioResponse
  .batch_id, .n_scenarios, .scenarios[]
    cada scenario: .run_id, .product_values, .stats, .n_synths
```

> ⚠️ `per_synth_outcomes` não é retornado aqui (muito grande). Acessar direto no banco.

### Acessar per_synth_outcomes

Direto via ORM (não há endpoint — dados grandes demais para API):

```python
from synth_lab.repositories.simulation_run_repository import SimulationRunRepository

repo = SimulationRunRepository()
batch = repo.get_batch_by_id(batch_id)

for run in batch.runs:
    outcomes = run.per_synth_outcomes  # {synth_id: float}
    product  = run.product_values      # {node_name: "low"|"medium"|"high"}
    stats    = run.stats               # {mean, median, std, p10, p90}
```

### Carregar synths

```python
from sqlalchemy import select
from synth_lab.models.orm.synth import Synth as SynthORM

stmt = select(SynthORM).where(SynthORM.synth_group_id == group_id)
synths = session.execute(stmt).scalars().all()

synths_by_id = {s.id: s.data for s in synths}
# s.data["demografia"], s.data["sensitivities"]
```

---

## Referência de campos

### `synth.data.sensitivities`

| Campo | Range | Significado |
|-------|-------|-------------|
| `risk_aversion` | 0–1 | Quanto evita risco (1 = muito avesso) |
| `digital_capability` | 0–1 | Fluência digital (1 = muito capaz) |
| `friction_tolerance` | 0–1 | Tolerância a fricção/esforço (1 = muito tolerante) |
| `institutional_trust_level` | 0–1 | Confiança em instituições (1 = muito confia) |

### `simulation_run.stats`

| Campo | Tipo | Significado |
|-------|------|-------------|
| `mean` | float | Taxa média de adoção (%) |
| `median` | float | Mediana (%) |
| `std` | float | Desvio padrão (pp) |
| `p10` | float | Percentil 10 — cenário pessimista |
| `p90` | float | Percentil 90 — cenário otimista |

### `simulation_run.product_values`

```json
{"Facilidade de Uso": "high", "Transparência": "low", "1-Clique Ativado": "medium"}
```

Valores possíveis: `"low"` | `"medium"` | `"high"`

### `simulation_run.per_synth_outcomes`

```json
{"syn_a1b2c3d4": 0.72, "syn_e5f6g7h8": 0.31, ...}
```

Float com 2 casas decimais. Representa a probabilidade média de adoção daquele synth naquele cenário.
