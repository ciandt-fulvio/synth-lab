# Implementation Plan: Sistema de Análise para UX Research

**Branch**: `017-analysis-ux-research` | **Date**: 2025-12-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/017-analysis-ux-research/spec.md`
**Dependency**: 016-feature-impact-simulation

## Summary

Sistema de análise quantitativa para UX Researchers que fornece visualizações de dados, clustering de personas, detecção de outliers e geração de insights via LLM. O sistema segue uma jornada de 6 fases: Visão Geral → Localização → Segmentação → Casos Especiais → Explicação Profunda → Insights LLM.

A implementação extende a API de simulação existente com novos endpoints para gráficos e análises ML, seguindo a arquitetura existente do projeto (services, entities, routers).

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**:
- FastAPI (já existente)
- scikit-learn (novo - K-Means, Isolation Forest, StandardScaler)
- scipy (novo - Hierarchical Clustering, correlações)
- shap (novo - SHAP values, TreeExplainer)
- numpy (já existente)
- OpenAI SDK (já existente - para LLM insights)

**Storage**: SQLite 3 com JSON1 extension (output/synthlab.db) - reutiliza tabelas existentes (synth_outcomes, region_analyses, sensitivity_results)

**Testing**: pytest (já existente)

**Target Platform**: Linux/macOS server (API REST)

**Project Type**: Web application (backend-only nesta feature)

**Performance Goals**:
- Endpoints de gráficos: < 500ms p95
- Clustering (500 synths): < 2s
- SHAP explanation (single synth): < 30s
- LLM insights: < 5s (depende do modelo)

**Constraints**:
- Simulação deve estar completa antes de qualquer análise
- Clustering requer mínimo 10 synths
- SHAP requer treinamento de modelo (lazy, cacheado)

**Scale/Scope**:
- Até 10.000 synths por simulação
- 24 endpoints novos organizados em 6 fases

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Status | Observação |
|-----------|--------|------------|
| I. Test-First Development (TDD/BDD) | ✅ | Testes escritos antes de cada serviço |
| II. Fast Test Battery (<5s) | ✅ | Unit tests para services isolados |
| III. Complete Test Battery before PR | ✅ | Integration tests para endpoints |
| IV. Frequent Commits | ✅ | Commit por fase de implementação |
| V. Simplicity (<500 linhas/arquivo) | ✅ | Serviços separados por responsabilidade |
| VI. Language (EN code, PT docs) | ✅ | Seguir padrão existente |
| VII. Architecture | ✅ | Segue estrutura existente (services/, entities/, routers/) |
| IX. Tracing | ✅ | Phoenix já configurado no projeto |

## Project Structure

### Documentation (this feature)

```text
specs/017-analysis-ux-research/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI schemas)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/synth_lab/
├── domain/entities/
│   ├── cluster_result.py     # (novo) ClusterProfile, KMeansResult, HierarchicalResult
│   ├── outlier_result.py     # (novo) OutlierSynth, OutlierResult
│   ├── explainability.py     # (novo) ShapExplanation, PDPResult
│   └── chart_insight.py      # (novo) ChartCaption, ChartInsight
│
├── services/simulation/
│   ├── analyzer.py           # (existe) Decision Tree regions
│   ├── sensitivity.py        # (existe) OAT
│   ├── chart_data_service.py # (novo) dados para gráficos Fase 1-2
│   ├── clustering_service.py # (novo) K-Means, Hierarchical
│   ├── outlier_service.py    # (novo) Isolation Forest, Extreme Cases
│   ├── explainability_service.py # (novo) SHAP, PDP
│   └── insight_service.py    # (novo) LLM captions/insights
│
├── api/routers/
│   └── simulation.py         # (expandir) novos endpoints de análise
│
└── api/schemas/
    └── analysis.py           # (novo) Pydantic request/response schemas

tests/
├── unit/
│   └── services/simulation/
│       ├── test_chart_data_service.py
│       ├── test_clustering_service.py
│       ├── test_outlier_service.py
│       ├── test_explainability_service.py
│       └── test_insight_service.py
│
└── integration/
    └── api/
        └── test_analysis_endpoints.py
```

**Structure Decision**: Backend-only feature que extende a estrutura existente de simulation services. Novos serviços seguem o padrão existente (analyzer.py, sensitivity.py) com responsabilidades bem separadas.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

Nenhuma violação identificada. A feature segue padrões existentes do projeto.

---

## Phase 0: Research Summary

### Decisões Técnicas

#### 1. Biblioteca de ML para Clustering e Outliers

**Decisão**: scikit-learn
**Rationale**:
- Padrão da indústria, API estável e bem documentada
- KMeans, IsolationForest, StandardScaler nativamente disponíveis
- Compatível com numpy arrays existentes no projeto
**Alternativas consideradas**:
- HDBSCAN (mais robusto para clustering, mas dependência adicional)
- PyOD (especializado em outliers, mas overkill para Isolation Forest básico)

#### 2. Biblioteca para Hierarchical Clustering

**Decisão**: scipy.cluster.hierarchy
**Rationale**:
- linkage(), fcluster(), dendrogram() são funções maduras e eficientes
- Retorna matriz de linkage compatível com visualização
- Já é dependência transitiva do projeto
**Alternativas consideradas**:
- scikit-learn AgglomerativeClustering (não retorna dendrograma)

#### 3. Biblioteca para SHAP

**Decisão**: shap (biblioteca oficial)
**Rationale**:
- Única biblioteca oficial para SHAP values
- TreeExplainer otimizado para modelos tree-based
- Integração nativa com GradientBoosting
**Alternativas consideradas**:
- Nenhuma alternativa viável para SHAP

#### 4. Modelo para SHAP

**Decisão**: GradientBoostingRegressor (sklearn)
**Rationale**:
- Suportado nativamente por TreeExplainer (rápido)
- Boa capacidade preditiva sem tuning extensivo
- Interpretável com SHAP values
**Alternativas consideradas**:
- RandomForest (similar, mas menos preciso)
- XGBoost (requer dependência adicional)

#### 5. Cálculo de Correlações

**Decisão**: scipy.stats.pearsonr + numpy
**Rationale**:
- Retorna coeficiente e p-value em uma chamada
- Eficiente para datasets médios
- Já disponível no projeto

#### 6. LLM para Insights

**Decisão**: OpenAI SDK (já existente no projeto)
**Rationale**:
- Infraestrutura já configurada (infrastructure/llm_client.py)
- Tracing com Phoenix já funciona
- Consistência com resto do projeto
**Alternativas consideradas**:
- Modelos locais (latência e custo de hosting)

#### 7. Cache de LLM

**Decisão**: Cache em memória (dicionário por simulation_id + chart_type)
**Rationale**:
- Simples de implementar
- Suficiente para escopo atual
- Evita dependência de Redis/Memcached
**Alternativas consideradas**:
- Persistir em SQLite (complexidade adicional)
- Redis (infra adicional)

### Dependências Novas

| Pacote | Versão | Propósito |
|--------|--------|-----------|
| scikit-learn | >=1.4.0 | Clustering, Isolation Forest, StandardScaler |
| shap | >=0.44.0 | SHAP values e TreeExplainer |

**Nota**: scipy já é dependência transitiva. Verificar versão mínima para `scipy.cluster.hierarchy`.

---

## Phase 1: Design

### Arquitetura de Serviços

```
┌─────────────────────────────────────────────────────────────────────┐
│                          API Layer                                   │
│  /simulation/simulations/{id}/charts/*                              │
│  /simulation/simulations/{id}/clusters/*                            │
│  /simulation/simulations/{id}/outliers                              │
│  /simulation/simulations/{id}/shap                                  │
│  /simulation/simulations/{id}/insights/*                            │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
┌────────────────────────────────┼────────────────────────────────────┐
│                         Service Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ChartData     │  │Clustering    │  │Outlier       │              │
│  │Service       │  │Service       │  │Service       │              │
│  │- try_success │  │- kmeans      │  │- isolation   │              │
│  │- heatmap     │  │- elbow       │  └──────────────┘              │
│  │- boxplot     │  │- radar       │                                 │
│  │- scatter     │  └──────────────┘  ┌──────────────┐              │
│  │- tornado     │                    │Explainability│              │
│  └──────────────┘  ┌──────────────┐  │Service       │              │
│                    │Insight       │  │- shap        │              │
│                    │Service       │  │- pdp         │              │
│                    │- caption     │  └──────────────┘              │
│                    │- insight     │                                 │
│                    └──────────────┘                                 │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
┌────────────────────────────────┼────────────────────────────────────┐
│                        Domain Layer                                  │
│  entities/chart_data.py  entities/cluster_result.py                 │
│  entities/outlier_result.py  entities/explainability.py             │
│  entities/chart_insight.py                                          │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
┌────────────────────────────────┼────────────────────────────────────┐
│                      Repository Layer                                │
│  SynthOutcomeRepository (existente)                                 │
│  RegionAnalysisRepository (existente)                               │
│  SensitivityResultRepository (existente)                            │
└─────────────────────────────────────────────────────────────────────┘
```

### Fluxo de Dados

```
synth_outcomes (DB) ──┬──► ChartDataService ──► TryVsSuccessChart
                      │                     └──► OutcomeDistributionChart
                      │                     └──► FailureHeatmapChart
                      │                     └──► BoxPlotChart
                      │                     └──► ScatterCorrelationChart
                      │
                      ├──► ClusteringService ──► KMeansResult
                      │                      └──► HierarchicalResult
                      │                      └──► RadarChart
                      │
                      ├──► OutlierService ──► OutlierResult
                      │                   └──► ExtremeCasesTable
                      │
                      └──► ExplainabilityService ──► ShapExplanation
                                               └──► PDPResult

sensitivity_result (DB) ──► ChartDataService ──► TornadoChart

chart_data (any) ──► InsightService ──► ChartCaption
                                    └──► ChartInsight
```

### Endpoints Organizados por Fase

#### FASE 1 - Visão Geral (3 endpoints)
```
GET /simulation/simulations/{id}/charts/try-vs-success
    ?x_threshold=0.5&y_threshold=0.5

GET /simulation/simulations/{id}/charts/distribution
    ?mode=by_synth|by_percentile&sort_by=success_rate&order=desc&limit=50

```

#### FASE 2 - Localização (4 endpoints)
```
GET /simulation/simulations/{id}/charts/failure-heatmap
    ?x_axis=capability_mean&y_axis=trust_mean&bins=5&metric=failed_rate

GET /simulation/simulations/{id}/charts/box-plot
    ?metric=success_rate&include_baseline=true

GET /simulation/simulations/{id}/charts/scatter
    ?x_axis=trust_mean&y_axis=success_rate&show_trendline=true

GET /simulation/simulations/{id}/charts/tornado
```

#### FASE 3 - Segmentação (6 endpoints)
```
POST /simulation/simulations/{id}/clusters
    body: {method: "kmeans"|"hierarchical", n_clusters: 4, features: [...]}

GET /simulation/simulations/{id}/clusters

GET /simulation/simulations/{id}/clusters/elbow

GET /simulation/simulations/{id}/clusters/dendrogram
    ?max_depth=5&color_threshold=2.5

GET /simulation/simulations/{id}/clusters/{cluster_id}/radar

GET /simulation/simulations/{id}/clusters/radar-comparison

POST /simulation/simulations/{id}/clusters/cut
    body: {n_clusters: 4}
```

#### FASE 4 - Casos Especiais (2 endpoints)
```
GET /simulation/simulations/{id}/extreme-cases
    ?type=all|failures|successes|unexpected&limit=10&include_interview_suggestions=true

GET /simulation/simulations/{id}/outliers
    ?contamination=0.1&include_outcomes=true
```

#### FASE 5 - Explicabilidade (4 endpoints)
```
GET /simulation/simulations/{id}/shap
    ?synth_id=xxx

GET /simulation/simulations/{id}/shap/summary

GET /simulation/simulations/{id}/pdp
    ?feature=capability_mean&grid_resolution=20

GET /simulation/simulations/{id}/pdp/comparison
    ?features=capability_mean,trust_mean
```

#### FASE 6 - Insights LLM (3 endpoints)
```
GET /simulation/simulations/{id}/charts/{chart_type}/caption

GET /simulation/simulations/{id}/charts/{chart_type}/insight

GET /simulation/simulations/{id}/insights
```

**Total: 22 endpoints** (alguns agrupados no pre-work original)

---

## Próximos Passos

1. Criar `research.md` com detalhes das dependências
2. Criar `data-model.md` com todas as entidades Pydantic
3. Criar `contracts/` com OpenAPI schemas
4. Criar `quickstart.md` com exemplos de uso
5. Executar `/speckit.tasks` para gerar tasks.md
