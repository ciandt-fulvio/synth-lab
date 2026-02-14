# API Contracts: Análise Quantitativa

**Phase 1 Output** | **Date**: 2026-02-14 | **Branch**: `042-quantitative-analysis`

## Base Path

`/experiments/{experiment_id}/quantitative-analysis`

Router: `src/synth_lab/api/routers/quantitative_analysis.py`
Schemas: `src/synth_lab/api/schemas/quantitative_analysis.py`

---

## Endpoints

### POST `/generate` — Gerar Modelo Causal

Gera o DAG causal a partir do contexto do experimento via LLM (gpt-5.1).

**Request**: Sem body (usa dados do experimento).

**Response** (201 Created):
```json
{
  "id": "cm_a1b2c3d4",
  "experiment_id": "exp_12345678",
  "label": "Modelo Causal: Adoção do Pix Parcelado",
  "intercept_mu": 0.1,
  "intercept_sigma": 0.4,
  "nodes": ["Idade", "Renda", "Escolaridade", "Familiaridade Digital", "Confiança", "Percepção de Valor", "Adoção"],
  "edges": [
    {
      "id": "e1",
      "from_node": "Idade",
      "to_node": "Familiaridade Digital",
      "user_var": "ageNorm",
      "direction": -1,
      "header": "A respeito de quanto a Familiaridade Digital é influenciada pela idade",
      "options": [
        {"text": "Pessoas mais jovens têm familiaridade digital significativamente maior...", "mu": 0.80, "sigma": 0.15},
        {"text": "A idade tem influência relevante na familiaridade digital...", "mu": 0.65, "sigma": 0.25},
        {"text": "Não sei dizer se a idade impacta a familiaridade digital.", "mu": 0.50, "sigma": 0.50},
        {"text": "Pode haver alguma relação fraca entre idade e familiaridade digital...", "mu": 0.30, "sigma": 0.25},
        {"text": "A idade não influencia a familiaridade digital das pessoas.", "mu": 0.15, "sigma": 0.15}
      ],
      "default_option": 0,
      "selected_option": null
    }
  ],
  "created_at": "2026-02-14T10:30:00Z"
}
```

**Errors**:
- `404`: Experimento não encontrado
- `422`: Experimento sem título/hipótese suficientes
- `500`: Erro LLM (JSON inválido após 2 retries)

**Notas**:
- Se já existir um CausalModel para o experimento, ele é deletado (CASCADE nas edges) e um novo é gerado
- Todas as `selected_option` começam como `null`

---

### GET `/model` — Obter Modelo Causal Atual

Retorna o modelo causal atual do experimento com seleções do PM.

**Response** (200 OK): Mesmo schema do POST `/generate`.

**Errors**:
- `404`: Experimento não encontrado ou sem modelo causal gerado

---

### PATCH `/edges` — Atualizar Seleções Likert

Salva seleções do PM para uma ou mais arestas. Chamado com debounce do frontend.

**Request**:
```json
{
  "selections": {
    "e1": 0,
    "e3": 2,
    "e5": 4
  }
}
```

**Response** (200 OK):
```json
{
  "updated_count": 3,
  "all_answered": false,
  "answered_count": 5,
  "total_edges": 8
}
```

**Errors**:
- `404`: Experimento ou modelo não encontrado
- `422`: edge_id inválido ou selected_option fora de [0, 4]

---

### POST `/simulate` — Rodar Simulação Monte Carlo

Executa simulação com as seleções atuais do PM. Retorna resultados completos.

**Request**: Sem body (usa seleções salvas no modelo).

**Response** (201 Created):
```json
{
  "id": "sr_e5f6g7h8",
  "experiment_id": "exp_12345678",
  "causal_model_id": "cm_a1b2c3d4",
  "n_iterations": 3000,
  "n_synths": 150,
  "stats": {
    "mean": 42.3,
    "median": 41.8,
    "std": 3.2,
    "p10": 38.1,
    "p90": 46.5
  },
  "segments": {
    "age": {
      "18-29": {"rate": 55.2, "count": 45},
      "30-49": {"rate": 42.1, "count": 62},
      "50+": {"rate": 28.7, "count": 43}
    },
    "income": {
      "baixa": {"rate": 35.4, "count": 50},
      "media": {"rate": 43.8, "count": 55},
      "alta": {"rate": 51.2, "count": 45}
    },
    "education": {
      "baixa": {"rate": 33.1, "count": 48},
      "media": {"rate": 44.5, "count": 58},
      "alta": {"rate": 52.3, "count": 44}
    }
  },
  "sensitivity": [
    {
      "edge_id": "e1",
      "header": "A respeito de quanto a Familiaridade Digital é influenciada pela idade",
      "impact": 12.5,
      "mean_low": 48.8,
      "mean_high": 36.3
    }
  ],
  "interpretations": {
    "distribution": {
      "raw_text": "Com 80% de confiança, a taxa de adoção fica entre 38.1% e 46.5%. A estimativa central é 42.3%.",
      "ai_text": "Com 80% de confiança, a taxa de adoção do Pix Parcelado fica entre 38% e 47%. A incerteza moderada é puxada principalmente pela premissa sobre familiaridade digital — se os dados confirmarem alta correlação com idade, o intervalo estreita para ±3pp."
    },
    "segments": {
      "raw_text": "Melhor segmento: Jovens 18-29 (55.2%). Pior: 50+ (28.7%). Ratio: 1.9x.",
      "ai_text": "Jovens (18-29) têm quase o dobro da taxa de adoção dos 50+. Recomendo lançamento faseado priorizando millennials, com programa de educação financeira para o segmento sênior."
    },
    "sensitivity": {
      "raw_text": "Premissa mais impactante: Familiaridade Digital × Idade (12.5pp). Segunda: Confiança × Renda (8.3pp).",
      "ai_text": "A premissa sobre familiaridade digital é a que mais move a agulha. Para validar, analise dados de uso do app atual filtrado por faixa etária — se a adoção de features digitais cai >30% nos 50+, a premissa é sólida."
    }
  },
  "created_at": "2026-02-14T10:35:00Z"
}
```

**Errors**:
- `404`: Experimento ou modelo não encontrado
- `422`: Nem todas as arestas foram respondidas (pode usar defaults do LLM)
- `504`: Simulação excedeu timeout de 30s

**Notas**:
- Gera interview_guide automaticamente após simulação (async, não bloqueia response)
- Runs anteriores são preservados (histórico)
- A última run é a "ativa"

---

### GET `/results` — Obter Resultados da Última Simulação

Retorna a última SimulationRun com interpretações.

**Response** (200 OK): Mesmo schema do POST `/simulate`.

**Errors**:
- `404`: Experimento sem simulação ou sem modelo causal

---

## Schemas (TypeScript — Frontend)

```typescript
// types/quantitative-analysis.ts

interface LikertOption {
  text: string;
  mu: number;
  sigma: number;
}

interface CausalEdge {
  id: string;
  from_node: string;
  to_node: string;
  user_var: string;
  direction: 1 | -1;
  header: string;
  options: [LikertOption, LikertOption, LikertOption, LikertOption, LikertOption];
  default_option: number;
  selected_option: number | null;
}

interface CausalModel {
  id: string;
  experiment_id: string;
  label: string;
  intercept_mu: number;
  intercept_sigma: number;
  nodes: string[];
  edges: CausalEdge[];
  created_at: string;
}

interface EdgeSelections {
  selections: Record<string, number>;
}

interface EdgeUpdateResponse {
  updated_count: number;
  all_answered: boolean;
  answered_count: number;
  total_edges: number;
}

interface SimulationStats {
  mean: number;
  median: number;
  std: number;
  p10: number;
  p90: number;
}

interface SegmentResult {
  rate: number;
  count: number;
}

interface Segments {
  age: Record<string, SegmentResult>;
  income: Record<string, SegmentResult>;
  education: Record<string, SegmentResult>;
}

interface SensitivityItem {
  edge_id: string;
  header: string;
  impact: number;
  mean_low: number;
  mean_high: number;
}

interface Interpretation {
  raw_text: string;
  ai_text: string;
}

interface SimulationRun {
  id: string;
  experiment_id: string;
  causal_model_id: string;
  n_iterations: number;
  n_synths: number;
  stats: SimulationStats;
  segments: Segments;
  sensitivity: SensitivityItem[];
  interpretations: {
    distribution: Interpretation;
    segments: Interpretation;
    sensitivity: Interpretation;
  };
  created_at: string;
}
```

## Query Keys (Frontend)

```typescript
// Adicionar em lib/query-keys.ts
quantitativeAnalysis: {
  model: (experimentId: string) => ['quantitative-analysis', experimentId, 'model'] as const,
  results: (experimentId: string) => ['quantitative-analysis', experimentId, 'results'] as const,
},
```
