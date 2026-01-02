# Research: Experiment Hub - Reorganização da Navegação

**Feature**: 018-experiment-hub
**Date**: 2025-12-27

## Contexto

Esta pesquisa documenta as decisões técnicas para implementação do Experiment Hub, incluindo análise da estrutura existente do projeto e padrões a serem seguidos.

---

## 1. Estrutura de Tabelas no PostgreSQL

### Decisão
Adicionar 2 novas tabelas (`experiments`, `synth_groups`) e modificar 3 tabelas existentes (`feature_scorecards`, `research_executions`, `synths`).

### Racional
- O projeto já usa PostgreSQL com WAL mode e JSON1 extension
- Padrão existente: tabelas com `id TEXT PRIMARY KEY`, campos `created_at/updated_at TEXT`, e dados complexos em `data TEXT CHECK(json_valid(data))`
- Foreign keys estão habilitadas (`PRAGMA foreign_keys=ON`)

### Alternativas Consideradas
1. **DuckDB**: Rejeitado - projeto migrou de DuckDB para PostgreSQL (ver CLAUDE.md: "2025-12-22: Removed DuckDB dependency")
2. **PostgreSQL**: Rejeitado - escopo single-user, dados locais, PostgreSQL é suficiente

### Implementação

**Nova tabela `experiments`:**
```sql
CREATE TABLE IF NOT EXISTS experiments (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    hypothesis TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_experiments_created ON experiments(created_at DESC);
```

**Nova tabela `synth_groups`:**
```sql
CREATE TABLE IF NOT EXISTS synth_groups (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_synth_groups_created ON synth_groups(created_at DESC);
```

**Modificação `feature_scorecards` (adiciona experiment_id):**
```sql
ALTER TABLE feature_scorecards ADD COLUMN experiment_id TEXT NOT NULL;
CREATE INDEX IF NOT EXISTS idx_scorecards_experiment ON feature_scorecards(experiment_id);
```

**Modificação `research_executions` (adiciona experiment_id):**
```sql
ALTER TABLE research_executions ADD COLUMN experiment_id TEXT NOT NULL;
CREATE INDEX IF NOT EXISTS idx_executions_experiment ON research_executions(experiment_id);
```

**Modificação `synths` (adiciona synth_group_id):**
```sql
ALTER TABLE synths ADD COLUMN synth_group_id TEXT NOT NULL;
CREATE INDEX IF NOT EXISTS idx_synths_group ON synths(synth_group_id);
```

**Nota sobre migração**: Conforme spec, "Banco de dados será recriado do zero antes da implementação (sem migração)". O schema completo será atualizado em `database.py`.

---

## 2. Padrão de Repository

### Decisão
Seguir o padrão existente em `SynthRepository` e `BaseRepository`.

### Racional
- `BaseRepository` fornece `_paginate_query`, `_row_to_dict`, `_rows_to_dicts`
- Repositories recebem `DatabaseManager` opcional no construtor
- Conversão de rows para models via métodos `_row_to_*`
- Tratamento de erros com exceções customizadas

### Implementação
```python
class ExperimentRepository(BaseRepository):
    def list_experiments(self, params: PaginationParams) -> PaginatedResponse[ExperimentSummary]:
        ...
    def get_by_id(self, experiment_id: str) -> ExperimentDetail:
        ...
    def create(self, experiment: ExperimentCreate) -> ExperimentDetail:
        ...
    def update(self, experiment_id: str, data: ExperimentUpdate) -> ExperimentDetail:
        ...
```

---

## 3. Padrão de API Routes

### Decisão
Seguir o padrão existente em `synths.py` router.

### Racional
- Routes usam `APIRouter()` com funções async
- Injeção de serviço via função helper (`get_synth_service()`)
- Pydantic models para request/response
- Query params para paginação (limit, offset, sort_by, sort_order)

### Implementação
```python
router = APIRouter()

@router.get("/list", response_model=PaginatedResponse[ExperimentSummary])
async def list_experiments(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    ...
) -> PaginatedResponse[ExperimentSummary]:
    service = ExperimentService()
    return service.list_experiments(...)
```

---

## 4. Geração de IDs

### Decisão
Usar prefixo semântico + UUID curto para novos IDs.

### Racional
- Synths usam IDs de 6 caracteres (ex: `abc123`)
- Simulations usam `sim_` prefix (ex: `sim_abc123`)
- Scorecards usam `sc_` prefix
- Consistência com padrão existente

### Implementação
- `experiments`: `exp_` + 8 chars hex (ex: `exp_a1b2c3d4`)
- `synth_groups`: `grp_` + 8 chars hex (ex: `grp_a1b2c3d4`)

```python
import uuid
def generate_experiment_id() -> str:
    return f"exp_{uuid.uuid4().hex[:8]}"
```

---

## 5. Estrutura do Frontend

### Decisão
Adicionar novas páginas e componentes seguindo padrões existentes.

### Racional
- React Router já configurado em `App.tsx`
- TanStack Query para data fetching (hooks `useQuery`, `useMutation`)
- Componentes shadcn/ui disponíveis
- Tailwind CSS para styling

### Estrutura de Rotas
```
/                                      -> Index.tsx (ExperimentList)
/experiments/:id                       -> ExperimentDetail.tsx (novo)
/experiments/:id/simulations/:simId    -> SimulationDetail.tsx (novo)
/experiments/:id/interviews/:execId    -> InterviewDetail.tsx (existente, nova rota)
/synths                                -> Synths.tsx (novo, move conteúdo atual)
```

### Componentes Novos
- `ExperimentCard.tsx`: Card para lista de experimentos
- `ExperimentForm.tsx`: Modal/drawer para criar/editar experimento
- `EmptyState.tsx`: Estado vazio com CTA

---

## 6. API Endpoints

### Decisão
Seguir convenção REST existente com prefixo semântico.

### Racional
- Endpoints existentes: `/synths/list`, `/synths/{id}`, `/research/...`, `/simulation/...`
- Response wrapper: `PaginatedResponse[T]` para listas
- Status codes: 200 (ok), 201 (created), 404 (not found), 422 (validation error)

### Endpoints Experiments
| Method | Path | Description |
|--------|------|-------------|
| GET | /experiments/list | Lista paginada de experimentos |
| GET | /experiments/{id} | Detalhe com simulações e entrevistas |
| POST | /experiments | Criar experimento |
| PUT | /experiments/{id} | Atualizar experimento |
| POST | /experiments/{id}/scorecards | Criar scorecard vinculado |
| POST | /experiments/{id}/interviews | Criar entrevista vinculada |

### Endpoints Synth Groups
| Method | Path | Description |
|--------|------|-------------|
| GET | /synth-groups | Lista todos os grupos |
| GET | /synth-groups/{id} | Detalhe de um grupo |
| POST | /synth-groups | Criar grupo (interno) |

---

## 7. Modificações em Endpoints Existentes

### Decisão
Modificar `/simulation` e `/research` para aceitar experiment_id.

### Racional
- Endpoints existentes continuam funcionando
- Novo parâmetro `experiment_id` obrigatório para criação
- Queries existentes filtram por experiment_id quando fornecido

### Implementação
- `POST /simulation/scorecards`: Adiciona `experiment_id` no body
- `POST /research/execute`: Adiciona `experiment_id` no body
- Validação: experiment_id deve existir

---

## 8. Tratamento de Empty States

### Decisão
Implementar empty states com CTAs contextuais.

### Racional
- UX guidelines na spec definem mensagens específicas
- Padrão existente em componentes shadcn/ui (Card vazio com texto + botão)

### Implementação
```tsx
// Home sem experimentos
<EmptyState
  title="Nenhum experimento ainda"
  description="Crie seu primeiro experimento para começar a testar hipóteses"
  action={{ label: "Criar primeiro experimento", onClick: openCreateModal }}
/>

// Experimento sem simulações
<EmptyState
  title="Nenhuma simulação ainda"
  description="Crie sua primeira para testar quantitativamente"
  action={{ label: "+ Nova Simulação", onClick: openSimulationFlow }}
/>
```

---

## 9. Header Global com Acesso a Synths

### Decisão
Modificar header existente ou criar componente de layout global.

### Racional
- FR-008: "Todas as páginas DEVEM ter header com ícone para acessar Synths"
- FR-023: "Header DEVE ter ícone/botão para acessar catálogo de synths"
- Lucide icons disponível (já instalado)

### Implementação
```tsx
<header className="sticky top-0 z-50 w-full border-b bg-background/95">
  <nav className="container flex h-14 items-center justify-between">
    <Link to="/" className="font-semibold">SynthLab</Link>
    <div className="flex items-center gap-2">
      <Link to="/synths">
        <Button variant="ghost" size="icon">
          <Users className="h-5 w-5" />
        </Button>
      </Link>
      <Button variant="ghost" size="icon">
        <Settings className="h-5 w-5" />
      </Button>
    </div>
  </nav>
</header>
```

---

## 10. Breadcrumb Navigation

### Decisão
Implementar breadcrumb contextual em páginas de detalhe.

### Racional
- FR-012: "Detalhe de simulação DEVE ter breadcrumb para voltar ao experimento pai"
- FR-016: "Detalhe de entrevista DEVE manter comportamento existente, apenas alterando breadcrumb"

### Implementação
```tsx
// Em SimulationDetail
<Breadcrumb>
  <BreadcrumbLink to="/">Experimentos</BreadcrumbLink>
  <BreadcrumbSeparator />
  <BreadcrumbLink to={`/experiments/${experimentId}`}>
    {experimentName}
  </BreadcrumbLink>
  <BreadcrumbSeparator />
  <BreadcrumbPage>Simulação</BreadcrumbPage>
</Breadcrumb>
```

---

## Resumo de Decisões

| Área | Decisão | Justificativa |
|------|---------|---------------|
| Database | PostgreSQL + novas tabelas | Padrão existente, sem migração |
| Repository | Herdar BaseRepository | Padrão existente de pagination |
| API Routes | FastAPI + Pydantic | Padrão existente |
| IDs | Prefixo semântico + hex | Consistência com scorecards |
| Frontend | React + TanStack Query | Stack existente |
| Navegação | Header global + breadcrumb | Requisitos FR-008, FR-012 |
