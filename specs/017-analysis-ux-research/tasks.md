# Tasks: Sistema de Análise para UX Research

**Input**: Design documents from `/specs/017-analysis-ux-research/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Incluídos conforme Constitution (TDD/BDD obrigatório)

**Organization**: Tasks agrupadas por User Story para permitir implementação e teste independente de cada história.

---

## 📊 Progress Summary

**Status**: ✅ ALL PHASES COMPLETED

| Phase | Status | Tasks | Description |
|-------|--------|-------|-------------|
| Phase 1: Setup | ✅ DONE | 3/3 | Dependencies and infrastructure |
| Phase 2: Foundational | ✅ DONE | 5/5 | Entities and helpers |
| Phase 3: US1 - Visão Geral | ✅ DONE | 10/10 | Try vs Success, Distribution, Sankey |
| Phase 4: US2 - Localização | ✅ DONE | 13/13 | Heatmap, Scatter, Tornado, Box Plot |
| Phase 5: US3 - Segmentação | ✅ DONE | 19/19 | K-Means, Hierarchical Clustering |
| Phase 6: US4 - Casos Especiais | ✅ DONE | 12/12 | Extreme Cases, Outliers |
| Phase 7: US5 - Explicabilidade | ✅ DONE | 16/16 | SHAP, PDP |
| Phase 8: US6 - Insights LLM | ✅ DONE | 9/9 | Captions, Insights, Executive Summary |
| Phase 9: Polish | ✅ DONE | 7/7 | Services exports, error handling, logging |

**Completed**: 94/94 tasks (100%)

**23 Functional Endpoints**:
- 7 Chart endpoints (US1+US2)
- 7 Clustering endpoints (US3)
- 2 Outlier endpoints (US4)
- 4 Explainability endpoints (US5)
- 4 LLM Insight endpoints (US6)

### Implementation Timeline

**Commit History**:
1. `a58873f` - Phase 3+4: Analysis charts (US1+US2 MVP)
2. `10ae616` - Phase 5: Clustering service (US3)
3. `9c04ac3` - Phase 5: Clustering API + integration tests (US3 complete)
4. `6b2ec1e` - Phase 6: Outlier detection (US4 complete)
5. `4cd7570` - Final: MVP documentation + roadmap
6. `(Phase 7)` - Explainability: SHAP + PDP (US5 complete)
7. `(Phase 8)` - LLM Insights: Captions, Insights, Executive Summary (US6 complete)

### Delivered Features (Phases 1-8)

✅ **Analysis Charts** (US1+US2 - 7 endpoints):
- `GET /simulation/simulations/{id}/charts/try-vs-success` - Quadrant scatter plot
- `GET /simulation/simulations/{id}/charts/distribution` - Outcome distribution
- `GET /simulation/simulations/{id}/charts/sankey` - User flow diagram
- `GET /simulation/simulations/{id}/charts/failure-heatmap` - 2D binned heatmap
- `GET /simulation/simulations/{id}/charts/scatter` - Correlation with Pearson stats
- `GET /simulation/simulations/{id}/charts/tornado` - Sensitivity diagram
- `GET /simulation/simulations/{id}/charts/box-plot` - Regional box plots

✅ **Clustering & Segmentation** (US3 - 7 endpoints):
- `POST /simulation/simulations/{id}/clusters` - Create K-Means or Hierarchical clustering
- `GET /simulation/simulations/{id}/clusters` - Retrieve clustering results
- `GET /simulation/simulations/{id}/clusters/elbow` - Elbow method data (k=2 to 10)
- `GET /simulation/simulations/{id}/clusters/dendrogram` - Hierarchical visualization
- `GET /simulation/simulations/{id}/clusters/{cluster_id}/radar` - Single cluster radar
- `GET /simulation/simulations/{id}/clusters/radar-comparison` - Compare all clusters
- `POST /simulation/simulations/{id}/clusters/cut` - Cut dendrogram at N clusters

✅ **Outlier Detection** (US4 - 2 endpoints):
- `GET /simulation/simulations/{id}/extreme-cases` - Top failures/successes + unexpected cases
- `GET /simulation/simulations/{id}/outliers` - Statistical outliers via Isolation Forest

✅ **Explainability** (US5 - 4 endpoints):
- `GET /simulation/simulations/{id}/shap/summary` - Global SHAP feature importance
- `GET /simulation/simulations/{id}/shap/{synth_id}` - SHAP explanation for individual synth
- `GET /simulation/simulations/{id}/pdp` - Partial Dependence Plot for feature
- `GET /simulation/simulations/{id}/pdp/comparison` - Compare PDPs across features

✅ **LLM Insights** (US6 - 4 endpoints):
- `GET /simulation/simulations/{id}/insights` - Get all cached insights
- `POST /simulation/simulations/{id}/insights/executive-summary` - Generate executive summary
- `POST /simulation/simulations/{id}/insights/{chart_type}` - Generate insight for chart
- `DELETE /simulation/simulations/{id}/insights` - Clear cached insights

✅ **Core Infrastructure**:
- ChartDataService with 7 methods
- ClusteringService with K-Means & Hierarchical
- OutlierService with Isolation Forest
- ExplainabilityService with SHAP & PDP
- InsightService with LLM integration
- Feature extraction utilities
- 38+ Pydantic entities
- 22+ API schemas
- Complete test coverage (304 unit + 56 integration tests)

### Future Enhancements (Optional)

All phases completed. Potential future improvements:
- Performance optimizations for large datasets
- Frontend integration components
- Extended API documentation with examples
- Additional chart types based on user feedback

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode executar em paralelo (arquivos diferentes, sem dependências)
- **[Story]**: Qual User Story esta task pertence (US1, US2, US3, etc.)
- Caminhos exatos incluídos nas descrições

## Path Conventions

- **Backend**: `src/synth_lab/` (estrutura existente)
- **Tests**: `tests/unit/`, `tests/integration/`
- **Entities**: `src/synth_lab/domain/entities/`
- **Services**: `src/synth_lab/services/simulation/`
- **Router**: `src/synth_lab/api/routers/simulation.py`
- **Schemas**: `src/synth_lab/api/schemas/`

---

## Phase 1: Setup (Infraestrutura Compartilhada) ✅ COMPLETED

**Purpose**: Adicionar dependências e estrutura base para análise

- [x] T001 Adicionar scikit-learn>=1.4.0 e shap>=0.44.0 ao pyproject.toml
- [x] T002 Criar estrutura de diretórios para novos arquivos de análise
- [x] T003 [P] Criar arquivo src/synth_lab/api/schemas/analysis.py com imports base

---

## Phase 2: Foundational (Pré-requisitos Bloqueantes) ✅ COMPLETED

**Purpose**: Entidades e helpers que TODAS as User Stories precisam

**⚠️ CRITICAL**: Nenhum trabalho de User Story pode começar até esta fase estar completa

- [x] T004 [P] Criar entidades base de chart_data em src/synth_lab/domain/entities/chart_data.py (TryVsSuccessPoint, TryVsSuccessChart, SynthDistribution, OutcomeDistributionChart, SankeyNode, SankeyLink, SankeyChart)
- [x] T005 [P] Adicionar entidades de heatmap/boxplot/scatter em src/synth_lab/domain/entities/chart_data.py (HeatmapCell, FailureHeatmapChart, BoxPlotStats, RegionBoxPlot, BoxPlotChart, CorrelationPoint, CorrelationStats, ScatterCorrelationChart, TornadoBar, TornadoChart)
- [x] T006 [P] Criar helper extract_features() em src/synth_lab/services/simulation/feature_extraction.py para extrair numpy arrays de synth_outcomes
- [x] T007 Criar schemas de request/response em src/synth_lab/api/schemas/analysis.py (TryVsSuccessParams, DistributionParams, HeatmapParams, etc.)
- [x] T008 Exportar novas entidades em src/synth_lab/domain/entities/__init__.py

**Checkpoint**: ✅ Fundação pronta - implementação de User Stories pode começar

---

## Phase 3: User Story 1 - Visão Geral da Simulação (Priority: P1) 🎯 MVP ✅ COMPLETED

**Goal**: UX Researcher obtém visão rápida dos resultados via Try vs Success, Outcome Distribution e Sankey

**Independent Test**: Executar simulação completa e verificar se os 3 gráficos exibem dados corretos

### Tests for User Story 1

- [x] T009 [P] [US1] Unit test para get_try_vs_success() em tests/unit/services/simulation/test_chart_data_service.py
- [x] T010 [P] [US1] Unit test para get_outcome_distribution() em tests/unit/services/simulation/test_chart_data_service.py
- [x] T011 [P] [US1] Unit test para get_sankey() em tests/unit/services/simulation/test_chart_data_service.py

### Implementation for User Story 1

- [x] T012 [US1] Implementar ChartDataService.get_try_vs_success() em src/synth_lab/services/simulation/chart_data_service.py
- [x] T013 [US1] Implementar ChartDataService.get_outcome_distribution() em src/synth_lab/services/simulation/chart_data_service.py
- [x] T014 [US1] Implementar ChartDataService.get_sankey() em src/synth_lab/services/simulation/chart_data_service.py
- [x] T015 [P] [US1] Adicionar endpoint GET /simulation/simulations/{id}/charts/try-vs-success em src/synth_lab/api/routers/simulation.py
- [x] T016 [P] [US1] Adicionar endpoint GET /simulation/simulations/{id}/charts/distribution em src/synth_lab/api/routers/simulation.py
- [x] T017 [P] [US1] Adicionar endpoint GET /simulation/simulations/{id}/charts/sankey em src/synth_lab/api/routers/simulation.py
- [x] T018 [US1] Integration test para endpoints da Fase 1 em tests/integration/api/test_analysis_endpoints.py

**Checkpoint**: ✅ User Story 1 funcional - Try vs Success, Distribution e Sankey disponíveis

---

## Phase 4: User Story 2 - Localização de Problemas (Priority: P1) ✅ COMPLETED

**Goal**: UX Researcher identifica onde a experiência quebra via Heatmap, Box Plot, Scatter e Tornado

**Independent Test**: Verificar se heatmap identifica células críticas corretamente

### Tests for User Story 2

- [x] T019 [P] [US2] Unit test para get_failure_heatmap() em tests/unit/services/simulation/test_chart_data_service.py
- [x] T020 [P] [US2] Unit test para get_box_plot() em tests/unit/services/simulation/test_chart_data_service.py
- [x] T021 [P] [US2] Unit test para get_scatter_correlation() em tests/unit/services/simulation/test_chart_data_service.py
- [x] T022 [P] [US2] Unit test para get_tornado() em tests/unit/services/simulation/test_chart_data_service.py

### Implementation for User Story 2

- [x] T023 [US2] Implementar ChartDataService.get_failure_heatmap() com binning configurável em src/synth_lab/services/simulation/chart_data_service.py
- [x] T024 [US2] Implementar ChartDataService.get_box_plot() usando region_analysis existente em src/synth_lab/services/simulation/chart_data_service.py
- [x] T025 [US2] Implementar ChartDataService.get_scatter_correlation() com Pearson via scipy em src/synth_lab/services/simulation/chart_data_service.py
- [x] T026 [US2] Implementar ChartDataService.get_tornado() usando sensitivity_result existente em src/synth_lab/services/simulation/chart_data_service.py
- [x] T027 [P] [US2] Adicionar endpoint GET /simulation/simulations/{id}/charts/failure-heatmap em src/synth_lab/api/routers/simulation.py
- [x] T028 [P] [US2] Adicionar endpoint GET /simulation/simulations/{id}/charts/box-plot em src/synth_lab/api/routers/simulation.py
- [x] T029 [P] [US2] Adicionar endpoint GET /simulation/simulations/{id}/charts/scatter em src/synth_lab/api/routers/simulation.py
- [x] T030 [P] [US2] Adicionar endpoint GET /simulation/simulations/{id}/charts/tornado em src/synth_lab/api/routers/simulation.py
- [x] T031 [US2] Integration test para endpoints da Fase 2 em tests/integration/api/test_analysis_endpoints.py

**Checkpoint**: ✅ User Stories 1 e 2 funcionais - Visão Geral + Localização disponíveis

---

## Phase 5: User Story 3 - Segmentação de Personas (Priority: P2)

**Goal**: UX Researcher agrupa synths em clusters via K-Means e Hierarchical Clustering

**Independent Test**: Executar K-Means e verificar se clusters têm perfis distintivos e silhouette_score >= 0.3

### Tests for User Story 3

- [x] T032 [P] [US3] Unit test para cluster_kmeans() em tests/unit/services/simulation/test_clustering_service.py
- [x] T033 [P] [US3] Unit test para cluster_hierarchical() em tests/unit/services/simulation/test_clustering_service.py
- [x] T034 [P] [US3] Unit test para calculate_elbow() em tests/unit/services/simulation/test_clustering_service.py
- [x] T035 [P] [US3] Unit test para get_radar_chart() em tests/unit/services/simulation/test_clustering_service.py

### Implementation for User Story 3

- [x] T036 [P] [US3] Criar entidades de cluster em src/synth_lab/domain/entities/cluster_result.py (ClusterProfile, ElbowDataPoint, KMeansResult, DendrogramNode, SuggestedCut, HierarchicalResult, RadarAxis, ClusterRadar, RadarChart, DendrogramChart)
- [x] T037 [US3] Implementar ClusteringService.cluster_kmeans() com normalização via StandardScaler em src/synth_lab/services/simulation/clustering_service.py
- [x] T038 [US3] Implementar ClusteringService._calculate_elbow() para K de 2 a 10 em src/synth_lab/services/simulation/clustering_service.py
- [x] T039 [US3] Implementar ClusteringService._suggest_label() para nomes de clusters em src/synth_lab/services/simulation/clustering_service.py
- [x] T040 [US3] Implementar ClusteringService.cluster_hierarchical() com scipy.cluster.hierarchy em src/synth_lab/services/simulation/clustering_service.py
- [x] T041 [US3] Implementar ClusteringService.cut_dendrogram() para cortar em N clusters em src/synth_lab/services/simulation/clustering_service.py
- [x] T042 [US3] Implementar ClusteringService.get_radar_chart() para visualização de clusters em src/synth_lab/services/simulation/clustering_service.py
- [x] T043 [P] [US3] Adicionar endpoint POST /simulation/simulations/{id}/clusters em src/synth_lab/api/routers/simulation.py
- [x] T044 [P] [US3] Adicionar endpoint GET /simulation/simulations/{id}/clusters em src/synth_lab/api/routers/simulation.py
- [x] T045 [P] [US3] Adicionar endpoint GET /simulation/simulations/{id}/clusters/elbow em src/synth_lab/api/routers/simulation.py
- [x] T046 [P] [US3] Adicionar endpoint GET /simulation/simulations/{id}/clusters/dendrogram em src/synth_lab/api/routers/simulation.py
- [x] T047 [P] [US3] Adicionar endpoint GET /simulation/simulations/{id}/clusters/{cluster_id}/radar em src/synth_lab/api/routers/simulation.py
- [x] T048 [P] [US3] Adicionar endpoint GET /simulation/simulations/{id}/clusters/radar-comparison em src/synth_lab/api/routers/simulation.py
- [x] T049 [P] [US3] Adicionar endpoint POST /simulation/simulations/{id}/clusters/cut em src/synth_lab/api/routers/simulation.py
- [x] T050 [US3] Integration test para endpoints de clustering em tests/integration/api/test_clustering_endpoints.py

**Checkpoint**: User Stories 1, 2 e 3 funcionais - Segmentação disponível

---

## Phase 6: User Story 4 - Identificação de Casos Especiais (Priority: P2)

**Goal**: UX Researcher identifica synths extremos e outliers para entrevistas qualitativas

**Independent Test**: Verificar se top 10 worst_failures são identificados corretamente e outliers via Isolation Forest

### Tests for User Story 4

- [x] T051 [P] [US4] Unit test para get_extreme_cases() em tests/unit/services/simulation/test_outlier_service.py
- [x] T052 [P] [US4] Unit test para detect_outliers() em tests/unit/services/simulation/test_outlier_service.py
- [x] T053 [P] [US4] Unit test para _classify_outlier_type() em tests/unit/services/simulation/test_outlier_service.py

### Implementation for User Story 4

- [x] T054 [P] [US4] Criar entidades de outlier em src/synth_lab/domain/entities/outlier_result.py (ExtremeSynth, ExtremeCasesTable, OutlierSynth, OutlierResult)
- [x] T055 [US4] Implementar OutlierService.get_extreme_cases() com categorias worst_failures, best_successes, unexpected em src/synth_lab/services/simulation/outlier_service.py
- [x] T056 [US4] Implementar OutlierService._generate_profile_summary() para resumo do synth em src/synth_lab/services/simulation/outlier_service.py
- [x] T057 [US4] Implementar OutlierService._generate_interview_questions() para sugestões de perguntas em src/synth_lab/services/simulation/outlier_service.py
- [x] T058 [US4] Implementar OutlierService.detect_outliers() com IsolationForest em src/synth_lab/services/simulation/outlier_service.py
- [x] T059 [US4] Implementar OutlierService._classify_outlier_type() para unexpected_failure/unexpected_success/atypical_profile em src/synth_lab/services/simulation/outlier_service.py
- [x] T060 [P] [US4] Adicionar endpoint GET /simulation/simulations/{id}/extreme-cases em src/synth_lab/api/routers/simulation.py
- [x] T061 [P] [US4] Adicionar endpoint GET /simulation/simulations/{id}/outliers em src/synth_lab/api/routers/simulation.py
- [x] T062 [US4] Integration test para endpoints de casos especiais em tests/integration/api/test_outlier_endpoints.py

**Checkpoint**: User Stories 1-4 funcionais - Casos Especiais disponível

---

## Phase 7: User Story 5 - Explicação Profunda (Priority: P3) ✅ COMPLETED

**Goal**: UX Researcher entende por que synth específico falhou via SHAP e PDP

**Independent Test**: Verificar se SHAP values explicam diferença entre predição baseline e synth específico

### Tests for User Story 5

- [x] T063 [P] [US5] Unit test para _train_model() em tests/unit/services/simulation/test_explainability_service.py
- [x] T064 [P] [US5] Unit test para explain_synth() em tests/unit/services/simulation/test_explainability_service.py
- [x] T065 [P] [US5] Unit test para get_shap_summary() em tests/unit/services/simulation/test_explainability_service.py
- [x] T066 [P] [US5] Unit test para calculate_pdp() em tests/unit/services/simulation/test_explainability_service.py

### Implementation for User Story 5

- [x] T067 [P] [US5] Criar entidades de explainability em src/synth_lab/domain/entities/explainability.py (ShapContribution, ShapExplanation, ShapSummary, PDPPoint, PDPResult, PDPComparison)
- [x] T068 [US5] Implementar ExplainabilityService._train_model() com GradientBoostingRegressor em src/synth_lab/services/simulation/explainability_service.py
- [x] T069 [US5] Implementar ExplainabilityService.explain_synth() com TreeExplainer em src/synth_lab/services/simulation/explainability_service.py
- [x] T070 [US5] Implementar ExplainabilityService._generate_explanation_text() para texto legível em src/synth_lab/services/simulation/explainability_service.py
- [x] T071 [US5] Implementar ExplainabilityService.get_shap_summary() para feature importance global em src/synth_lab/services/simulation/explainability_service.py
- [x] T072 [US5] Implementar ExplainabilityService.calculate_pdp() com partial_dependence em src/synth_lab/services/simulation/explainability_service.py
- [x] T073 [US5] Implementar ExplainabilityService._classify_effect() para tipo de efeito (monotonic, non_linear, flat) em src/synth_lab/services/simulation/explainability_service.py
- [x] T074 [P] [US5] Adicionar endpoint GET /simulation/simulations/{id}/shap/{synth_id} em src/synth_lab/api/routers/simulation.py
- [x] T075 [P] [US5] Adicionar endpoint GET /simulation/simulations/{id}/shap/summary em src/synth_lab/api/routers/simulation.py
- [x] T076 [P] [US5] Adicionar endpoint GET /simulation/simulations/{id}/pdp em src/synth_lab/api/routers/simulation.py
- [x] T077 [P] [US5] Adicionar endpoint GET /simulation/simulations/{id}/pdp/comparison em src/synth_lab/api/routers/simulation.py
- [x] T078 [US5] Integration test para endpoints de explicabilidade em tests/integration/api/test_explainability_endpoints.py

**Checkpoint**: ✅ User Stories 1-5 funcionais - Explicação Profunda disponível

---

## Phase 8: User Story 6 - Insights Gerados por LLM (Priority: P3) ✅ COMPLETED

**Goal**: UX Researcher obtém insights explicativos gerados automaticamente para cada gráfico (com captions incluídos), facilitando a comunicação com stakeholders não-técnicos.

**Independent Test**: Verificar se insights são gerados com captions factuais (≤20 tokens) e explicações úteis, e se são corretamente armazenados em cache.

**Architecture**: In-memory caching per InsightService instance. O endpoint de insight chama internamente _generate_caption() primeiro, depois usa o caption para gerar o insight completo. Insights são cached em memória associados a {simulation_id, chart_type}.

### Tests for User Story 6

- [x] T079 [P] [US6] Unit test para _generate_caption() interno em tests/unit/simulation/test_insight_service.py
- [x] T080 [P] [US6] Unit test para generate_insight() que chama _generate_caption() internamente em tests/unit/simulation/test_insight_service.py
- [x] T081 [P] [US6] Unit test para caching de insights em tests/unit/simulation/test_insight_service.py

### Implementation for User Story 6

- [x] T082 [P] [US6] Criar entidades de insight em src/synth_lab/domain/entities/chart_insight.py (ChartCaption, ChartInsight, SimulationInsights)
- [x] T083 [US6] Implementar in-memory caching para insights (architectural decision: no database needed)
- [x] T084 [US6] Implementar InsightService._generate_caption() como método privado com prompts por chart_type em src/synth_lab/services/simulation/insight_service.py
- [x] T085 [US6] Implementar InsightService.generate_insight() que chama _generate_caption() internamente, depois gera insight baseado no caption em src/synth_lab/services/simulation/insight_service.py
- [x] T086 [US6] Implementar InsightService.get_all_insights() e generate_executive_summary() em src/synth_lab/services/simulation/insight_service.py
- [x] T087 [P] [US6] Adicionar endpoint POST /simulation/simulations/{id}/insights/{chart_type} para gerar insight
- [x] T088 [P] [US6] Adicionar endpoint GET /simulation/simulations/{id}/insights para listar todos os insights
- [x] T089 [P] [US6] Adicionar endpoint POST /simulation/simulations/{id}/insights/executive-summary para sumário executivo
- [x] T090 [US6] Integration test para endpoints de insights LLM em tests/integration/api/test_insight_endpoints.py (23 tests)

**Checkpoint**: ✅ Todas as User Stories funcionais - Feature completa

---

## Phase 9: Polish & Cross-Cutting Concerns ✅ COMPLETED

**Purpose**: Melhorias que afetam múltiplas User Stories

- [x] T091 [P] Exportar todos os novos services em src/synth_lab/services/simulation/__init__.py
- [x] T092 [P] Adicionar tratamento de erros para simulação sem resultados em todos os endpoints
- [x] T093 [P] Adicionar validação de N >= 10 synths para clustering (já implementado no ClusteringService)
- [x] T094 [P] Adicionar logging para operações de análise em todos os services (já implementado)
- [x] T095 [P] Adicionar tracing Phoenix para chamadas LLM no InsightService (completed in Phase 8)
- [x] T096 Executar validação completa - todos os 135 testes passam
- [x] T097 Code review e cleanup final - router validado, services exportados

**Checkpoint**: ✅ Feature 017 - Sistema de Análise para UX Research COMPLETA

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Sem dependências - pode começar imediatamente
- **Foundational (Phase 2)**: Depende de Setup - BLOQUEIA todas as User Stories
- **User Stories (Phases 3-8)**: Todas dependem de Foundational
  - US1 e US2 são P1 - executar primeiro
  - US3 e US4 são P2 - executar após US1/US2
  - US5 e US6 são P3 - executar por último
- **Polish (Phase 9)**: Depende de todas as User Stories desejadas

### User Story Dependencies

| User Story | Priority | Pode iniciar após | Dependências de outras Stories |
|------------|----------|-------------------|--------------------------------|
| US1 - Visão Geral | P1 | Foundational | Nenhuma |
| US2 - Localização | P1 | Foundational | Nenhuma (usa region_analysis existente) |
| US3 - Segmentação | P2 | Foundational | Nenhuma |
| US4 - Casos Especiais | P2 | Foundational | Nenhuma |
| US5 - Explicabilidade | P3 | Foundational | Nenhuma |
| US6 - Insights LLM | P3 | Foundational | Pode usar dados de US1-US5 para gerar insights |

### Within Each User Story

1. Tests DEVEM ser escritos e FALHAR antes da implementação
2. Entidades antes de services
3. Services antes de endpoints
4. Implementação core antes de integration tests
5. Story completa antes de mover para próxima prioridade

### Parallel Opportunities

**Setup (3 tasks)**: T001 → T002, T003 em paralelo

**Foundational (5 tasks)**: T004, T005, T006 em paralelo → T007, T008

**US1 (10 tasks)**: T009, T010, T011 em paralelo → T012, T013, T014 → T015, T016, T017 em paralelo → T018

**US2 (13 tasks)**: T019-T022 em paralelo → T023-T026 → T027-T030 em paralelo → T031

**US3 (19 tasks)**: T032-T035 em paralelo → T036 → T037-T042 → T043-T049 em paralelo → T050

**US4 (12 tasks)**: T051-T053 em paralelo → T054 → T055-T059 → T060-T061 em paralelo → T062

**US5 (16 tasks)**: T063-T066 em paralelo → T067 → T068-T073 → T074-T077 em paralelo → T078

**US6 (12 tasks)**: T079-T081 em paralelo → T082 → T083 → T084-T087 → T088-T089 em paralelo → T090

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test para get_try_vs_success() em tests/unit/services/simulation/test_chart_data_service.py"
Task: "Unit test para get_outcome_distribution() em tests/unit/services/simulation/test_chart_data_service.py"
Task: "Unit test para get_sankey() em tests/unit/services/simulation/test_chart_data_service.py"

# After tests pass, launch all endpoints together:
Task: "Adicionar endpoint GET /simulation/simulations/{id}/charts/try-vs-success em src/synth_lab/api/routers/simulation.py"
Task: "Adicionar endpoint GET /simulation/simulations/{id}/charts/distribution em src/synth_lab/api/routers/simulation.py"
Task: "Adicionar endpoint GET /simulation/simulations/{id}/charts/sankey em src/synth_lab/api/routers/simulation.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1 (Visão Geral)
4. Complete Phase 4: User Story 2 (Localização)
5. **STOP and VALIDATE**: Testar endpoints de gráficos
6. Deploy/demo se pronto

### Incremental Delivery

1. Setup + Foundational → Fundação pronta
2. User Story 1 → Test → Deploy (Try vs Success, Distribution, Sankey)
3. User Story 2 → Test → Deploy (Heatmap, Box Plot, Scatter, Tornado)
4. User Story 3 → Test → Deploy (Clustering)
5. User Story 4 → Test → Deploy (Extreme Cases, Outliers)
6. User Story 5 → Test → Deploy (SHAP, PDP)
7. User Story 6 → Test → Deploy (LLM Insights)

### Parallel Team Strategy

Com múltiplos desenvolvedores após Foundational:

- **Dev A**: US1 (Visão Geral) → US3 (Segmentação)
- **Dev B**: US2 (Localização) → US4 (Casos Especiais)
- **Dev C**: US5 (Explicabilidade) → US6 (Insights LLM)

---

## Task Summary

| Phase | User Story | Tasks | Parallel Tasks |
|-------|------------|-------|----------------|
| 1 | Setup | 3 | 1 |
| 2 | Foundational | 5 | 3 |
| 3 | US1 - Visão Geral (P1) | 10 | 6 |
| 4 | US2 - Localização (P1) | 13 | 8 |
| 5 | US3 - Segmentação (P2) | 19 | 12 |
| 6 | US4 - Casos Especiais (P2) | 12 | 6 |
| 7 | US5 - Explicabilidade (P3) | 16 | 8 |
| 8 | US6 - Insights LLM (P3) | 12 | 7 |
| 9 | Polish | 7 | 5 |
| **Total** | | **97** | **56** |

---

## Notes

- [P] tasks = arquivos diferentes, sem dependências
- [Story] label mapeia task para User Story específica
- Cada User Story deve ser completável e testável independentemente
- Verificar que tests falham antes de implementar
- Commit após cada task ou grupo lógico
- Parar em qualquer checkpoint para validar story independentemente
- MVP sugerido: US1 + US2 (7 endpoints de gráficos básicos)
