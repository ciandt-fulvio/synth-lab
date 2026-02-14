# Research: Análise Quantitativa

**Phase 0 Output** | **Date**: 2026-02-14 | **Branch**: `042-quantitative-analysis`

## 1. Monte Carlo Simulation in Python

**Decision**: NumPy vectorized operations para simulação Monte Carlo.

**Rationale**: NumPy opera em arrays C-level, eliminando loops Python. Para 3.000 iterações × 500 synths × 10 edges, a versão vetorizada completa em ~1s vs ~30s com loops puros. Já está disponível como dependência transitiva do projeto.

**Alternatives Considered**:
- **Pure Python loops**: Muito lento para 1.5M+ cálculos por simulação.
- **SciPy stats**: Overhead desnecessário — `numpy.random.normal()` e sigmoid manual são suficientes.
- **Polars/Pandas**: Overkill para operação numérica pura sem DataFrames.

**Implementation Notes**:
```python
# Vetorizado: 3000 iterations × N synths em uma chamada
rng = np.random.default_rng(seed)
intercepts = rng.normal(intercept_mu, intercept_sigma, n_iterations)
# coefs shape: (n_iterations, n_edges)
coefs = rng.normal(beta_mus, beta_sigmas, (n_iterations, n_edges))
# user_vars shape: (n_synths, n_edges) — pré-computado
# logits shape: (n_iterations, n_synths)
logits = intercepts[:, None] + coefs @ user_vars.T
probs = 1 / (1 + np.exp(-logits))
adopted = rng.random(probs.shape) < probs
rates = adopted.mean(axis=1)  # shape: (n_iterations,)
```

## 2. DAG Visualization no Frontend

**Decision**: SVG manual com posicionamento por camadas (sem biblioteca de grafos).

**Rationale**: O DAG tem estrutura fixa (3 camadas, 7-10 nós, 7-10 arestas) — não precisa de layout automático. SVG inline permite controle total de estilos (espessura, cor por direção) e integração com Tailwind. O JSX de referência já usa esta abordagem.

**Alternatives Considered**:
- **D3.js**: Poderoso mas pesado (200KB+). DAG fixo não precisa de force-directed layout.
- **React Flow**: Excelente para grafos interativos, mas overkill para visualização read-only com 3 camadas.
- **Cytoscape.js**: Foco em grafos complexos. Overhead injustificável.
- **dagre**: Layout automático de DAGs. Possível fallback se posicionamento manual ficar complexo, mas 3 camadas são triviais.

**Implementation Notes**:
- Nós posicionados em 3 colunas (x fixo por layer)
- Arestas como `<path>` com curva quadrática
- Espessura = `1 + mu * 4` pixels
- Cor = azul (direction=1) / laranja (direction=-1)
- Highlight ao hover para aresta correspondente à Likert focada

## 3. Parallel LLM Calls para Interpretações

**Decision**: `asyncio.gather()` com 3 tasks para gpt-4o-mini (distribuição, segmentos, sensibilidade).

**Rationale**: As 3 interpretações são independentes. Chamar em paralelo reduz latência de ~9s (3×3s) para ~3s. FastAPI já roda em event loop async.

**Alternatives Considered**:
- **Sequential calls**: Simples mas 3× mais lento. Sem vantagem.
- **ThreadPoolExecutor**: Desnecessário — OpenAI SDK já é async.
- **Background task + polling**: Complexidade sem benefício — latência de 3s é aceitável para feedback síncrono.

**Implementation Notes**:
```python
async def generate_interpretations(stats, experiment_context):
    tasks = [
        _interpret_section("Distribuição", distribution_raw, stats, experiment_context),
        _interpret_section("Segmentos", segments_raw, stats, experiment_context),
        _interpret_section("Sensibilidade", sensitivity_raw, stats, experiment_context),
    ]
    return await asyncio.gather(*tasks)
```

## 4. Persistência do Modelo Causal

**Decision**: Tabelas dedicadas `causal_models` e `causal_edges` (normalized) com JSON para opções Likert.

**Rationale**: Modelo causal tem estrutura relacional clara (model → edges). Edges têm campos fixos (from, to, userVar, direction) que precisam de queries diretas. Opções Likert (5 items fixos por edge) são arrays constantes — JSON é ideal.

**Alternatives Considered**:
- **Tudo em JSON blob**: Simples para write, péssimo para queries (ex: "quais edges usam ageNorm?").
- **Opções em tabela separada**: 3 tabelas para 1 feature. Over-normalized para 5 opções fixas.
- **Document store (MongoDB-style)**: Fora do stack. PostgreSQL JSON resolve.

**Implementation Notes**:
- `causal_models`: id (cm_xxx), experiment_id (FK, unique), label, intercept_mu, intercept_sigma, nodes (JSON array), raw_llm_response (JSON), created_at
- `causal_edges`: id (PK), causal_model_id (FK), from_node, to_node, user_var, direction, header, options (JSON array of 5), default_option, selected_option (nullable — PM selection)

## 5. Resultados de Simulação

**Decision**: Tabela `simulation_runs` com JSON para resultados agregados + tabela `analysis_interpretations` para textos AI.

**Rationale**: Cada run é imutável (snapshot de resultados). Stats, distribuição e segmentos são denormalizados em JSON porque são lidos como bloco. Interpretações AI ficam em tabela separada porque são geradas assincronamente e podem ser re-geradas.

**Alternatives Considered**:
- **Armazenar iterações individuais (3.000 rows por run)**: Extremamente wasteful. Só precisamos dos agregados.
- **Tudo em uma tabela**: Mistura dados numéricos com textos AI. Dificulta re-geração de interpretações.

## 6. Interview Guide Fusion

**Decision**: Reutilizar `InterviewGuideGeneratorService` com novo prompt (QUESTIONNAIRE_SYSTEM adaptado). Chamado automaticamente após simulação, não mais na criação do experimento.

**Rationale**: A tabela `interview_guide` já existe e é consumida pelo pipeline de entrevistas. O serviço já tem tracing e error handling. Basta trocar o prompt e o trigger.

**Alternatives Considered**:
- **Novo serviço separado**: Duplicação de infraestrutura (tracing, error handling, DB access) sem benefício.
- **Chamar direto do simulation service**: Violaria separação de responsabilidades.

**Implementation Notes**:
- Remover chamada automática em `ExperimentService.create_experiment()` (ou onde estiver)
- Adicionar chamada em `QuantitativeAnalysisService.run_simulation()` após salvar resultados
- Novo prompt template baseado no QUESTIONNAIRE_SYSTEM do Apêndice C da spec
- Output JSON: `{ context_definition, questions, context_examples }`

## 7. userVar Extractors

**Decision**: 10 funções puras em módulo dedicado (`simulation_engine.py`), sem configuração dinâmica.

**Rationale**: O mapeamento é fixo por decisão do ADR #8. Funções puras são triviais de testar com dados reais de synths. Normalização inline evita over-engineering.

**Alternatives Considered**:
- **Config file com extractors dinâmicos**: Flexível mas complexo. O ADR define que não é configurável pelo PM.
- **Extractors como lambdas em dict**: Menos legível que funções nomeadas com docstrings.

**Implementation Notes**:
```python
def extract_user_vars(synth_data: dict) -> dict[str, float]:
    """Extract and normalize 10 userVars from synth data."""
    demo = synth_data.get("demografia", {})
    sens = synth_data.get("sensitivities", {})
    disab = synth_data.get("deficiencias", {})
    return {
        "ageNorm": _clamp((demo.get("idade", 40) - 18) / 62),
        "incomeNorm": _normalize_income(demo.get("renda_mensal", 3000)),
        "eduNorm": _edu_ordinal(demo.get("escolaridade", "medio_completo")),
        "familySizeNorm": _clamp(demo.get("composicao_familiar", {}).get("numero_pessoas", 3) / 5),
        "hasVisualDisab": 1.0 if disab.get("visual", {}).get("tipo", "nenhuma") != "nenhuma" else 0.0,
        "hasMotorDisab": 1.0 if disab.get("motora", {}).get("tipo", "nenhuma") != "nenhuma" else 0.0,
        "digitalCapability": sens.get("digital_capability", 0.5),
        "riskAversion": sens.get("risk_aversion", 0.5),
        "institutionalTrust": sens.get("institutional_trust_level", 0.5),
        "frictionTolerance": sens.get("friction_tolerance", 0.5),
    }
```

## 8. Frontend State Management

**Decision**: React Query para server state + useState local para seleções Likert (com debounced save).

**Rationale**: Seleções Likert mudam frequentemente (a cada clique). Salvá-las imediatamente via mutation causaria excesso de requests. Debounce de 2s agrupa mudanças. React Query invalida cache após simulação para refrescar resultados.

**Alternatives Considered**:
- **Zustand/Redux**: Global state desnecessário — tudo está scoped a 1 experimento.
- **React Context**: Viável mas sem cache/invalidation que React Query já fornece.
- **Optimistic updates**: Complexidade sem benefício — save em background é suficiente.

## 9. Dependência: NumPy

**Decision**: Adicionar `numpy` ao `pyproject.toml` como dependência de produção.

**Rationale**: Essencial para performance da simulação Monte Carlo. Não é substituível por stdlib. Já é dependência transitiva de várias libs científicas.

**Package Details**:
- **Version**: `>=1.26,<3` (compatível com Python 3.13)
- **Size**: ~15MB wheel
- **License**: BSD-3-Clause
- **Docs**: https://numpy.org/doc/stable/
