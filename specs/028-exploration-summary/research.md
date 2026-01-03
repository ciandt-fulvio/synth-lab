# Phase 0: Research - Exploration Summary and PRFAQ Generation

**Date**: 2026-01-02
**Status**: Complete

## Research Questions

Based on the Technical Context section in plan.md, the following areas required research:

1. How to construct winning path from exploration tree?
2. What LLM prompt structure works best for narrative summary (non-sequential format)?
3. What PRFAQ structure matches interview guide pattern?
4. How to handle ties in success_rate (multiple winning paths)?
5. Database schema design for summary/PRFAQ entities

## Findings

### 1. Winning Path Construction

**Decision**: Traverse from best leaf node back to root using parent_id relationships

**Rationale**:
- ScenarioNode entity already has parent_id field (see `src/synth_lab/domain/entities/scenario_node.py`)
- Best leaf = node with max success_rate AND max depth (to avoid root node)
- Path traversal: Start at leaf, follow parent_id chain until depth=0

**Implementation Pattern**:
```python
def get_winning_path(exploration_id: str) -> list[ScenarioNode]:
    # 1. Get all leaf nodes (nodes with no children)
    # 2. Filter by highest success_rate
    # 3. If tie, use lowest depth (shortest path)
    # 4. If still tied, use earliest created_at
    # 5. Traverse from winner to root via parent_id
    path = []
    current = winning_leaf
    while current:
        path.insert(0, current)  # Prepend to build root→leaf order
        current = get_node_by_id(current.parent_id)
    return path
```

**Alternatives Considered**:
- Store path explicitly in exploration table → Rejected: Redundant with parent_id graph
- Store only winner node_id → Rejected: Requires client-side path reconstruction

**References**:
- Existing pattern: `src/synth_lab/services/exploration/exploration_service.py` (tree navigation)
- Entity: `src/synth_lab/domain/entities/scenario_node.py` (parent_id relationship)

---

### 2. LLM Prompt Structure for Narrative Summary

**Decision**: Composite prompt with baseline + transformations → final state description

**Rationale**:
- User requirement: "não precisa falar começa assim, depois assado" (no sequential steps)
- Want: Final state after all actions applied (like a product vision)
- Need: Original scenario + all actions + rationales → integrated narrative

**Prompt Template** (Portuguese, per spec):
```
Você é um especialista em UX Research e Product Management.

CENÁRIO ORIGINAL:
{experiment.description}

Scorecard Baseline:
- Complexidade: {root_node.scorecard_params.complexity}
- Esforço Inicial: {root_node.scorecard_params.initial_effort}
- Risco Percebido: {root_node.scorecard_params.perceived_risk}
- Tempo até Valor: {root_node.scorecard_params.time_to_value}
Taxa de Sucesso Inicial: {root_node.simulation_results.success_rate}%

MELHORIAS EXPLORADAS:
{for each non-root node in path:}
- {node.action_applied}
  Justificativa: {node.rationale}
  Impacto: {scorecard deltas}

RESULTADO FINAL:
Scorecard Otimizado:
- Complexidade: {final_node.scorecard_params.complexity}
- Esforço Inicial: {final_node.scorecard_params.initial_effort}
- Risco Percebido: {final_node.scorecard_params.perceived_risk}
- Tempo até Valor: {final_node.scorecard_params.time_to_value}
Taxa de Sucesso Final: {final_node.simulation_results.success_rate}%

TAREFA:
Escreva um sumário narrativo descrevendo como o experimento ficaria APÓS a aplicação de todas essas melhorias. Não descreva as melhorias como passos sequenciais ("primeiro fazer X, depois Y"), mas sim como características integradas do experimento otimizado. Foque em:

1. **Visão Geral** (2-3 frases): Como o experimento otimizado se apresenta ao usuário?
2. **Características Principais** (3-5 itens): Que aspectos definem esta versão melhorada?
3. **Impacto Esperado**: Como essas mudanças afetam a experiência e os resultados?

Responda em formato markdown, em português, com tom profissional mas acessível.
```

**Alternatives Considered**:
- Sequential format ("Etapa 1, Etapa 2") → Rejected: User explicitly requested against this
- Action list only → Rejected: Doesn't synthesize into coherent vision
- English prompt → Rejected: Documentation must be in Portuguese (Constitution VII)

**References**:
- Similar pattern: `src/synth_lab/services/interview_guide_generator_service.py:_build_prompt()` (Portuguese prompts)
- LLM client: `src/synth_lab/infrastructure/llm_client.py:complete()` (text completion)

---

### 3. PRFAQ Structure

**Decision**: Adapt Amazon PRFAQ format with 3 sections (Press Release + FAQ + Recommendations)

**Rationale**:
- User specified: "análogo ao que rola hoje nas entrevistas" (similar to interview guides)
- Interview guides have 3 sections (questions, context_def, context_examples)
- PRFAQ should have similar weight: formal + actionable

**PRFAQ Template**:
```markdown
# Press Release: {Experiment Name} - Versão Otimizada

## Resumo Executivo
[2-3 parágrafos descrevendo a versão melhorada como se já estivesse implementada]

## O Problema
[Qual problema o experimento original enfrentava (baseado no baseline)]

## A Solução
[Como as melhorias aplicadas resolvem esse problema]

## Benefícios
- [Melhoria 1 com métrica]
- [Melhoria 2 com métrica]
- [Melhoria 3 com métrica]

---

# FAQ (Perguntas Frequentes)

## 1. Por que essas mudanças específicas foram escolhidas?
[Resposta baseada nas justificativas dos nós]

## 2. Qual foi o impacto nas métricas de scorecard?
[Comparação before/after dos 4 parâmetros]

## 3. Que riscos ainda existem?
[Análise do perceived_risk final]

## 4. Quanto esforço é necessário para implementar?
[Análise do initial_effort final]

## 5. Quando veremos resultados?
[Análise do time_to_value final]

---

# Recomendações para Implementação

## Próximos Passos
1. [Ação concreta 1]
2. [Ação concreta 2]
3. [Ação concreta 3]

## Métricas de Sucesso
- [Métrica 1 para validar melhorias]
- [Métrica 2 para validar melhorias]

## Considerações de Longo Prazo
[Insights sobre escalabilidade, manutenção, evolução]
```

**Prompt for PRFAQ**:
```
Você é um Product Manager experiente escrevendo um documento PRFAQ (Press Release / FAQ).

[Include same context as summary prompt: baseline, actions, final state]

TAREFA:
Escreva um documento PRFAQ profissional que formalize as recomendações desta exploração. O documento deve ter 3 seções:

1. **Press Release**: Anuncie a versão otimizada como se já estivesse implementada (estilo jornalístico)
2. **FAQ**: Responda 5 perguntas-chave sobre as mudanças propostas
3. **Recomendações**: Liste próximos passos concretos para implementação

Use o formato markdown e mantenha tom executivo mas acessível.
```

**Alternatives Considered**:
- Single narrative (like summary) → Rejected: Less actionable for stakeholders
- Technical spec format → Rejected: Not business-friendly
- Separate documents for PR/FAQ → Rejected: User requested "um PRFAQ" (single doc)

**References**:
- Similar structure: Interview guide has questions + context + examples (3 sections)
- Amazon PRFAQ format: https://www.allthingsdistributed.com/2006/11/working_backwards.html

---

### 4. Handling Ties in Success Rate

**Decision**: Three-level tiebreaker: success_rate → depth (lower wins) → created_at (earlier wins)

**Rationale**:
- Primary goal: Maximize success_rate
- Secondary goal: Prefer shorter paths (simpler solutions = lower depth)
- Tertiary goal: Deterministic selection (timestamp prevents randomness)

**Implementation**:
```sql
SELECT * FROM scenario_nodes
WHERE exploration_id = ?
  AND node_id NOT IN (SELECT DISTINCT parent_id FROM scenario_nodes WHERE parent_id IS NOT NULL)
ORDER BY
  simulation_results->>'success_rate' DESC,
  depth ASC,
  created_at ASC
LIMIT 1;
```

**Edge Cases Addressed**:
- Root node is best (depth=0, no actions) → Summary indicates "no improvements found"
- Multiple paths with exact same metrics → Earliest created_at wins (stable sorting)
- No simulation results (null success_rate) → Filter out nodes without simulation_results

**Alternatives Considered**:
- Random selection on tie → Rejected: Non-deterministic, breaks reproducibility
- Prefer higher depth (more actions) → Rejected: Violates simplicity principle
- Manual user selection → Rejected: Adds UX complexity, breaks automation

**References**:
- Spec edge case section (line 66-68): Explicitly requires this tiebreaker logic

---

### 5. Database Schema Design

**Decision**: Reutilizar tabela `experiment_documents` existente (NÃO criar tabela nova)

**Rationale**:
- **Explorations pertencem a Experiments**: Campo `exploration.experiment_id` é FK para experiments
- **Documentos do experiment**: Summaries/PRFAQs gerados por exploration são documentos do experiment pai
- **Metadata JSON**: Campo `metadata` armazena `exploration_id` + `winning_path_nodes` para identificar origem
- **Zero migration**: Tabela já existe com estrutura flexível
- **Reutilização total**: Entity, enums, repository, schemas tudo já existe

**Tabela Existente** (`experiment_documents`):
```sql
-- JÁ EXISTE! Não criar nova tabela!
CREATE TABLE experiment_documents (
    id VARCHAR(50) PRIMARY KEY,
    experiment_id VARCHAR(50) REFERENCES experiments(id),  -- ← exploration.experiment_id vai aqui!
    document_type VARCHAR(50),
    markdown_content TEXT,
    metadata JSONB,  -- ← exploration_id + winning_path_nodes vão aqui!
    generated_at VARCHAR(50),
    model VARCHAR(50),
    status VARCHAR(20),
    error_message TEXT,
    UNIQUE (experiment_id, document_type)
);
```

**Como Usar para Exploration**:
```python
# Exploration tem experiment_id
exploration = Exploration(id="expl_12345678", experiment_id="exp_abcdef12", ...)

# Documento vai em experiment_documents usando experiment_id da exploration
doc = ExperimentDocument(
    id=generate_document_id(),
    experiment_id=exploration.experiment_id,  # ← USA O EXPERIMENT_ID!
    document_type=DocumentType.SUMMARY,
    markdown_content="...",
    metadata={
        "source": "exploration",              # ← Identifica origem
        "exploration_id": exploration.id,     # ← Qual exploration gerou
        "winning_path_nodes": ["node_...", ...],
        "path_length": 3,
        "final_success_rate": 0.55
    }
)

# Salvar usando repository existente
document_repo.create(doc)
```

**Key Design Choices**:
- **Reusar tudo**: Entity, enums, repository, ORM model, tabela - tudo já existe!
- **Metadata JSON**: Identifica que documento veio de exploration via `source: "exploration"`
- **Unique constraint**: Um summary por experiment (se exploration gerar, sobrescreve anterior)
- **Zero migration**: Nenhuma alteração no banco necessária

**Metadata para Documents de Exploration**:
```json
{
  "source": "exploration",
  "exploration_id": "expl_12345678",
  "winning_path_nodes": ["node_00000001", "node_00000005", "node_0000000a"],
  "path_length": 3,
  "baseline_success_rate": 0.48,
  "final_success_rate": 0.55,
  "improvement_percentage": 14.6
}
```

**Alternatives Rejected**:
- ❌ Criar `exploration_documents` table → Desnecessário, exploration pertence a experiment
- ❌ Criar `ExplorationDocument` entity → Desnecessário, usar ExperimentDocument
- ❌ Criar novos enums → Desnecessário, reusar DocumentType/DocumentStatus

**References**:
- **Entity**: `src/synth_lab/domain/entities/experiment_document.py`
- **ORM**: `src/synth_lab/models/orm/document.py`
- **Repository**: `src/synth_lab/repositories/experiment_document_repository.py`
- **Service**: `src/synth_lab/services/document_service.py`
- **Exploration FK**: `src/synth_lab/domain/entities/exploration.py:168` (experiment_id field)

---

## Technology Stack Decisions

### Backend Libraries (No New Dependencies)
- **LLM Client**: Reuse `src/synth_lab/infrastructure/llm_client.py`
- **Tracing**: Reuse Phoenix `_tracer` from infrastructure
- **ORM**: SQLAlchemy 2.0+ (existing)
- **Migrations**: Alembic (existing)
- **Testing**: pytest with async support (existing)

**Rationale**: All required capabilities already exist in codebase

### Frontend Libraries (No New Dependencies)
- **State Management**: TanStack Query (existing)
- **UI Components**: shadcn/ui (existing)
- **API Client**: fetchAPI utility (existing)
- **Type Safety**: TypeScript 5.5+ (existing)

**Rationale**: Follow existing patterns, no new dependencies needed

---

## Best Practices Applied

### 1. Idempotent Generation
- Check for existing summary/PRFAQ before generating
- Return existing content if already generated
- Allow manual regeneration (overwrites previous)

**Pattern** (from interview_guide_generator_service.py):
```python
async def generate_for_exploration(self, exploration_id: str) -> ExplorationSummary:
    # Check existing
    existing = self.summary_repo.get_by_exploration_id(exploration_id)
    if existing and existing.generation_status == 'completed':
        return existing

    # Generate new
    content = await self._generate_content(...)

    # Persist
    summary = ExplorationSummary(...)
    return self.summary_repo.create(summary)
```

### 2. Async Generation with Status Tracking
- Set status='generating' immediately
- Call LLM (async, may take 30+ seconds)
- Update status='completed' or 'failed' based on result
- Store error_message if failed

**Benefits**:
- UI can show loading state
- Prevents concurrent generation requests (check status first)
- Enables retry logic on failure

### 3. Phoenix Tracing for LLM Calls
- All LLM calls wrapped in `_tracer.start_as_current_span()`
- Trace includes: exploration_id, path length, generation time
- Enables observability and debugging

**Pattern**:
```python
with self._tracer.start_as_current_span("generate_exploration_summary") as span:
    span.set_attribute("exploration_id", exploration_id)
    span.set_attribute("path_length", len(winning_path))
    content = await self.llm_client.complete(...)
```

### 4. Parametrized SQL Queries
- All repository queries use `?` placeholders
- Prevents SQL injection
- Required by Constitution (Architecture VII)

---

## Summary

All research questions resolved. Key decisions:

1. **Winning Path**: Traverse from best leaf (max success_rate, min depth, earliest timestamp) to root via parent_id
2. **Summary Prompt**: Composite prompt (baseline → transformations → final state) in Portuguese, non-sequential narrative format
3. **PRFAQ Structure**: 3 sections (Press Release + FAQ + Recommendations) matching interview guide pattern
4. **Tiebreaker Logic**: success_rate DESC → depth ASC → created_at ASC
5. **Database Schema**: Two tables (exploration_summary, exploration_prfaq) with status tracking and winning_path_nodes array

**Ready for Phase 1: Design & Contracts**
