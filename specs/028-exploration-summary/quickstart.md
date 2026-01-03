# Quickstart: Exploration Summary and PRFAQ Generation

**Date**: 2026-01-02
**Audience**: Developers implementing this feature
**Prerequisites**: Python 3.13+, PostgreSQL 14+, Node 18+

## Overview

Esta feature adiciona geração de documentos via LLM para explorations completas:
- **Summary**: Narrativa descrevendo o estado final do winning path (não sequencial)
- **PRFAQ**: Documento formal Press Release + FAQ + Recomendações

**Padrão**: Reutiliza `experiment_documents` existente (NÃO cria tabela nova)

---

## Arquitetura Correta

```
┌─────────────────────────┐
│      Experiment         │
│ ─────────────────────── │
│ id: str (PK)            │  ←───────────────────────┐
│ ...                     │                          │
└────────────┬────────────┘                          │
             │ 1:N                                   │
             │                                       │
             ▼                                       │
┌─────────────────────────┐                          │
│  ExperimentDocument     │  ← TABELA EXISTENTE!     │
│ ─────────────────────── │                          │
│ id: str (PK)            │                          │
│ experiment_id: str (FK) │ ─────────────────────────┤
│ document_type: enum     │                          │
│ metadata: JSON          │ ← {"source": "exploration", "exploration_id": "..."}
│ ...                     │                          │
└─────────────────────────┘                          │
                                                     │
┌─────────────────────────┐                          │
│     Exploration         │                          │
│ ─────────────────────── │                          │
│ id: str (PK)            │                          │
│ experiment_id: str (FK) │ ─────────────────────────┘
│ ...                     │
└─────────────────────────┘
```

**Princípio**: Explorations pertencem a Experiments. Documentos de exploration vão em `experiment_documents` usando `exploration.experiment_id`.

---

## Quick Reference: Implementation Order

```
1. Backend Service Layer (APENAS NOVOS)
   ├── services/exploration_summary_generator_service.py  # NOVO
   ├── services/exploration_prfaq_generator_service.py    # NOVO
   └── Tests: test_*_service.py

2. Backend API Layer (MODIFICAR)
   └── api/routers/exploration.py  # ADICIONAR endpoints wrapper

3. Frontend Data Layer
   ├── services/exploration.ts (MODIFICAR: add API calls)
   ├── hooks/useGenerateExplorationSummary.ts  # NOVO
   ├── hooks/useGenerateExplorationPRFAQ.ts    # NOVO
   ├── hooks/useExplorationSummary.ts          # NOVO
   └── hooks/useExplorationPRFAQ.ts            # NOVO

4. Frontend UI Layer
   ├── components/exploration/ExplorationSummaryCard.tsx    # NOVO
   ├── components/exploration/ExplorationPRFAQCard.tsx      # NOVO
   ├── components/exploration/GenerateDocumentButton.tsx    # NOVO
   └── pages/ExplorationDetail.tsx  # MODIFICAR: integrar componentes
```

**IMPORTANTE**: NÃO criar:
- ❌ Nova tabela
- ❌ Nova entity
- ❌ Nova migration
- ❌ Novo repository

---

## O Que Já Existe (REUTILIZAR)

### ExperimentDocument Entity

**File**: `src/synth_lab/domain/entities/experiment_document.py`

```python
class ExperimentDocument(BaseModel):
    id: str                      # doc_XXXXXXXX
    experiment_id: str           # exp_XXXXXXXX
    document_type: DocumentType  # summary, prfaq, executive_summary
    markdown_content: str
    metadata: dict | None        # JSON flexível para dados específicos
    generated_at: datetime
    model: str
    status: DocumentStatus
    error_message: str | None
```

### DocumentType e DocumentStatus Enums

```python
class DocumentType(str, Enum):
    SUMMARY = "summary"
    PRFAQ = "prfaq"
    EXECUTIVE_SUMMARY = "executive_summary"

class DocumentStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"
```

### ExperimentDocumentRepository

**File**: `src/synth_lab/repositories/experiment_document_repository.py`

**Métodos disponíveis**:
- `create(doc)` - Criar documento
- `get_by_experiment(experiment_id, doc_type)` - Buscar por experiment + tipo
- `get_markdown(experiment_id, doc_type)` - Buscar só markdown
- `list_by_experiment(experiment_id)` - Listar todos do experiment
- `update_status(doc_id, status, ...)` - Atualizar status

---

## Backend Implementation

### 1. Service de Geração de Summary

**File**: `src/synth_lab/services/exploration_summary_generator_service.py` (NOVO)

```python
"""
Service para geração de summaries de exploration.

Gera narrativa não-sequencial descrevendo o estado final otimizado
após aplicação de todas as melhorias do winning path.

Usa LLM com Phoenix tracing para gerar conteúdo.
Salva em experiment_documents usando exploration.experiment_id.
"""

from datetime import datetime, timezone

from opentelemetry import trace

from synth_lab.domain.entities.experiment_document import (
    DocumentStatus,
    DocumentType,
    ExperimentDocument,
    generate_document_id,
)
from synth_lab.domain.entities.exploration import Exploration
from synth_lab.domain.entities.scenario_node import ScenarioNode
from synth_lab.infrastructure.llm_client import LLMClient
from synth_lab.repositories.experiment_document_repository import (
    ExperimentDocumentRepository,
)
from synth_lab.repositories.exploration_repository import ExplorationRepository
from synth_lab.repositories.scenario_node_repository import ScenarioNodeRepository


_tracer = trace.get_tracer(__name__)


class ExplorationSummaryGeneratorService:
    """Gera summary para exploration, salva em experiment_documents."""

    def __init__(
        self,
        exploration_repo: ExplorationRepository,
        node_repo: ScenarioNodeRepository,
        document_repo: ExperimentDocumentRepository,  # ← Repo existente!
        llm_client: LLMClient,
    ):
        self._exploration_repo = exploration_repo
        self._node_repo = node_repo
        self._document_repo = document_repo
        self._llm_client = llm_client

    async def generate_for_exploration(
        self,
        exploration_id: str,
    ) -> ExperimentDocument:  # ← Entity existente!
        """
        Gera summary para exploration.

        Args:
            exploration_id: ID da exploration

        Returns:
            ExperimentDocument com summary gerado

        Raises:
            ValueError: Se exploration não existe ou não está completa
            ConflictError: Se já tem geração em progresso
        """
        with _tracer.start_as_current_span("generate_exploration_summary") as span:
            span.set_attribute("exploration_id", exploration_id)

            # 1. Buscar exploration
            exploration = self._exploration_repo.get_by_id(exploration_id)
            if not exploration:
                raise ValueError(f"Exploration {exploration_id} not found")

            # 2. Validar status (deve estar completa)
            completed_statuses = {"GOAL_ACHIEVED", "DEPTH_LIMIT_REACHED", "COST_LIMIT_REACHED"}
            if exploration.status not in completed_statuses:
                raise ValueError(
                    f"Exploration must be completed. Current status: {exploration.status}"
                )

            # 3. Verificar se já existe summary em progresso
            existing = self._document_repo.get_by_experiment(
                exploration.experiment_id,
                DocumentType.SUMMARY,
            )
            if existing and existing.status == DocumentStatus.GENERATING:
                raise ConflictError("Summary generation already in progress")

            # 4. Buscar winning path
            winning_path = self._get_winning_path(exploration_id)
            span.set_attribute("path_length", len(winning_path))

            # 5. Criar documento com status GENERATING
            doc = ExperimentDocument(
                id=generate_document_id(),
                experiment_id=exploration.experiment_id,  # ← USA EXPERIMENT_ID!
                document_type=DocumentType.SUMMARY,
                markdown_content="",
                metadata={
                    "source": "exploration",
                    "exploration_id": exploration_id,
                    "winning_path_nodes": [n.id for n in winning_path],
                    "path_length": len(winning_path),
                },
                generated_at=datetime.now(timezone.utc),
                model="gpt-4o-mini",
                status=DocumentStatus.GENERATING,
            )

            # Upsert (sobrescreve se existir)
            if existing:
                self._document_repo.delete(existing.id)
            self._document_repo.create(doc)

            try:
                # 6. Gerar conteúdo via LLM
                prompt = self._build_prompt(exploration, winning_path)
                content = await self._llm_client.complete(
                    prompt=prompt,
                    temperature=0.7,
                )

                # 7. Atualizar documento com conteúdo
                root_node = winning_path[0]
                final_node = winning_path[-1]
                baseline_rate = root_node.get_success_rate() or 0
                final_rate = final_node.get_success_rate() or 0
                improvement = ((final_rate - baseline_rate) / baseline_rate * 100) if baseline_rate > 0 else 0

                self._document_repo.update_status(
                    doc.id,
                    status=DocumentStatus.COMPLETED,
                    markdown_content=content,
                    metadata={
                        **doc.metadata,
                        "baseline_success_rate": baseline_rate,
                        "final_success_rate": final_rate,
                        "improvement_percentage": round(improvement, 1),
                    },
                )

                return self._document_repo.get_by_id(doc.id)

            except Exception as e:
                # 8. Marcar como falha
                self._document_repo.update_status(
                    doc.id,
                    status=DocumentStatus.FAILED,
                    error_message=str(e),
                )
                raise

    def _get_winning_path(self, exploration_id: str) -> list[ScenarioNode]:
        """
        Encontra o winning path (root → best leaf).

        Tiebreaker: success_rate DESC → depth ASC → created_at ASC
        """
        # Buscar todos os nós
        all_nodes = self._node_repo.list_by_exploration(exploration_id)

        # Encontrar leaf nodes (sem filhos)
        node_ids = {n.id for n in all_nodes}
        parent_ids = {n.parent_id for n in all_nodes if n.parent_id}
        leaf_ids = node_ids - parent_ids

        leaf_nodes = [n for n in all_nodes if n.id in leaf_ids]

        # Ordenar por tiebreaker
        leaf_nodes.sort(
            key=lambda n: (
                -(n.get_success_rate() or 0),  # DESC
                n.depth,                        # ASC
                n.created_at,                   # ASC
            )
        )

        if not leaf_nodes:
            raise ValueError("No leaf nodes found")

        # Construir path do winner até root
        winner = leaf_nodes[0]
        path = []
        current = winner
        nodes_by_id = {n.id: n for n in all_nodes}

        while current:
            path.insert(0, current)  # Prepend
            if current.parent_id:
                current = nodes_by_id.get(current.parent_id)
            else:
                break

        return path

    def _build_prompt(
        self,
        exploration: Exploration,
        winning_path: list[ScenarioNode],
    ) -> str:
        """Constrói prompt para geração de summary."""
        root_node = winning_path[0]
        final_node = winning_path[-1]

        # Formatar melhorias (excluindo root)
        improvements = []
        for node in winning_path[1:]:
            improvements.append(
                f"- {node.action_applied}\n"
                f"  Justificativa: {node.rationale}\n"
                f"  Impacto: success_rate {root_node.get_success_rate():.0%} → {node.get_success_rate():.0%}"
            )

        improvements_text = "\n".join(improvements) if improvements else "Nenhuma melhoria aplicada."

        return f"""Você é um especialista em UX Research e Product Management.

CENÁRIO ORIGINAL:
{exploration.experiment_description or "N/A"}

Scorecard Baseline:
- Taxa de Sucesso Inicial: {root_node.get_success_rate():.0%}

MELHORIAS EXPLORADAS:
{improvements_text}

RESULTADO FINAL:
- Taxa de Sucesso Final: {final_node.get_success_rate():.0%}

TAREFA:
Escreva um sumário narrativo descrevendo como o experimento ficaria APÓS a aplicação de todas essas melhorias. Não descreva as melhorias como passos sequenciais ("primeiro fazer X, depois Y"), mas sim como características integradas do experimento otimizado. Foque em:

1. **Visão Geral** (2-3 frases): Como o experimento otimizado se apresenta ao usuário?
2. **Características Principais** (3-5 itens): Que aspectos definem esta versão melhorada?
3. **Impacto Esperado**: Como essas mudanças afetam a experiência e os resultados?

Responda em formato markdown, em português, com tom profissional mas acessível."""
```

### 2. Service de Geração de PRFAQ

**File**: `src/synth_lab/services/exploration_prfaq_generator_service.py` (NOVO)

Mesmo padrão que summary, muda apenas:
- `document_type=DocumentType.PRFAQ`
- Prompt diferente (formato PRFAQ)

---

### 3. API Endpoints (Wrapper)

**File**: `src/synth_lab/api/routers/exploration.py` (MODIFICAR)

```python
# Adicionar imports
from synth_lab.domain.entities.experiment_document import DocumentType
from synth_lab.repositories.experiment_document_repository import ExperimentDocumentRepository
from synth_lab.services.exploration_summary_generator_service import (
    ExplorationSummaryGeneratorService,
)

# Adicionar endpoints

@router.post("/{exploration_id}/documents/summary/generate")
async def generate_exploration_summary(
    exploration_id: str,
    summary_service: ExplorationSummaryGeneratorService = Depends(get_summary_service),
) -> ExperimentDocumentResponse:  # ← Schema existente!
    """Gera summary para exploration."""
    doc = await summary_service.generate_for_exploration(exploration_id)
    return ExperimentDocumentResponse.model_validate(doc)


@router.get("/{exploration_id}/documents/summary")
async def get_exploration_summary(
    exploration_id: str,
    exploration_repo: ExplorationRepository = Depends(get_exploration_repo),
    document_repo: ExperimentDocumentRepository = Depends(get_document_repo),
) -> ExperimentDocumentResponse:
    """Busca summary de exploration."""
    exploration = exploration_repo.get_by_id(exploration_id)
    if not exploration:
        raise HTTPException(404, "Exploration not found")

    doc = document_repo.get_by_experiment(
        exploration.experiment_id,
        DocumentType.SUMMARY,
    )
    if not doc:
        raise HTTPException(404, "Summary not found")

    # Verificar se é de exploration
    if doc.metadata and doc.metadata.get("source") != "exploration":
        raise HTTPException(404, "Summary not found for this exploration")

    return ExperimentDocumentResponse.model_validate(doc)


@router.delete("/{exploration_id}/documents/summary", status_code=204)
async def delete_exploration_summary(
    exploration_id: str,
    exploration_repo: ExplorationRepository = Depends(get_exploration_repo),
    document_repo: ExperimentDocumentRepository = Depends(get_document_repo),
) -> None:
    """Deleta summary de exploration."""
    exploration = exploration_repo.get_by_id(exploration_id)
    if not exploration:
        raise HTTPException(404, "Exploration not found")

    doc = document_repo.get_by_experiment(
        exploration.experiment_id,
        DocumentType.SUMMARY,
    )
    if not doc:
        raise HTTPException(404, "Summary not found")

    document_repo.delete(doc.id)


# Mesmos endpoints para PRFAQ...
```

---

## Frontend Implementation

### 1. API Service

**File**: `frontend/src/services/exploration.ts` (MODIFICAR)

```typescript
// Usar ExperimentDocumentResponse existente
import { ExperimentDocumentResponse } from "./documents";

export const generateExplorationSummary = async (
  explorationId: string
): Promise<ExperimentDocumentResponse> => {
  return fetchAPI<ExperimentDocumentResponse>(
    `/explorations/${explorationId}/documents/summary/generate`,
    { method: "POST" }
  );
};

export const getExplorationSummary = async (
  explorationId: string
): Promise<ExperimentDocumentResponse> => {
  return fetchAPI<ExperimentDocumentResponse>(
    `/explorations/${explorationId}/documents/summary`
  );
};

export const deleteExplorationSummary = async (
  explorationId: string
): Promise<void> => {
  return fetchAPI<void>(
    `/explorations/${explorationId}/documents/summary`,
    { method: "DELETE" }
  );
};

// Similar para PRFAQ...
```

### 2. Query Keys

**File**: `frontend/src/lib/query-keys.ts` (MODIFICAR)

```typescript
export const explorationKeys = {
  // ... existing keys
  summary: (explorationId: string) =>
    ["explorations", explorationId, "documents", "summary"] as const,
  prfaq: (explorationId: string) =>
    ["explorations", explorationId, "documents", "prfaq"] as const,
};
```

### 3. React Query Hooks

**File**: `frontend/src/hooks/useGenerateExplorationSummary.ts` (NOVO)

```typescript
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { generateExplorationSummary } from "../services/exploration";
import { explorationKeys } from "../lib/query-keys";

export const useGenerateExplorationSummary = (explorationId: string) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => generateExplorationSummary(explorationId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: explorationKeys.summary(explorationId),
      });
    },
  });
};
```

**File**: `frontend/src/hooks/useExplorationSummary.ts` (NOVO)

```typescript
import { useQuery } from "@tanstack/react-query";
import { getExplorationSummary } from "../services/exploration";
import { explorationKeys } from "../lib/query-keys";

export const useExplorationSummary = (explorationId: string) => {
  return useQuery({
    queryKey: explorationKeys.summary(explorationId),
    queryFn: () => getExplorationSummary(explorationId),
    retry: false, // Don't retry if 404
  });
};
```

### 4. UI Components

**File**: `frontend/src/components/exploration/ExplorationSummaryCard.tsx` (NOVO)

```tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { MarkdownRenderer } from "@/components/MarkdownRenderer";
import { ExperimentDocumentResponse } from "@/services/documents";

interface Props {
  summary: ExperimentDocumentResponse | null;
  isLoading: boolean;
  onRegenerate: () => void;
}

export const ExplorationSummaryCard: React.FC<Props> = ({
  summary,
  isLoading,
  onRegenerate,
}) => {
  if (isLoading) return <Skeleton className="h-48" />;

  if (!summary) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Sumário</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Nenhum sumário gerado ainda.
          </p>
        </CardContent>
      </Card>
    );
  }

  if (summary.status === "failed") {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Sumário (Falhou)</CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertDescription>{summary.error_message}</AlertDescription>
          </Alert>
          <Button onClick={onRegenerate} className="mt-4">
            Tentar Novamente
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (summary.status === "generating") {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Sumário</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2">
            <Skeleton className="h-4 w-4 rounded-full animate-spin" />
            <span>Gerando sumário...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Sumário</CardTitle>
        <Button onClick={onRegenerate} variant="outline" size="sm">
          Regenerar
        </Button>
      </CardHeader>
      <CardContent>
        <MarkdownRenderer content={summary.markdown_content} />
        <div className="mt-4 text-sm text-muted-foreground">
          Gerado em: {new Date(summary.generated_at).toLocaleString()}
        </div>
      </CardContent>
    </Card>
  );
};
```

---

## Testing Strategy

### Backend Tests

**File**: `tests/synth_lab/unit/services/test_exploration_summary_generator_service.py`

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

from synth_lab.domain.entities.experiment_document import (
    DocumentStatus,
    DocumentType,
)
from synth_lab.services.exploration_summary_generator_service import (
    ExplorationSummaryGeneratorService,
)


@pytest.fixture
def mock_exploration_repo():
    repo = MagicMock()
    repo.get_by_id.return_value = MagicMock(
        id="expl_a1b2c3d4",
        experiment_id="exp_12345678",
        status="GOAL_ACHIEVED",
    )
    return repo


@pytest.fixture
def mock_node_repo():
    repo = MagicMock()
    # Mock winning path com 2 nós
    root = MagicMock(
        id="node_00000001",
        parent_id=None,
        depth=0,
        get_success_rate=lambda: 0.48,
    )
    leaf = MagicMock(
        id="node_00000005",
        parent_id="node_00000001",
        depth=1,
        get_success_rate=lambda: 0.55,
    )
    repo.list_by_exploration.return_value = [root, leaf]
    return repo


@pytest.fixture
def mock_document_repo():
    repo = MagicMock()
    repo.get_by_experiment.return_value = None  # No existing doc
    repo.create.return_value = None
    repo.get_by_id.return_value = MagicMock(
        id="doc_a1b2c3d4",
        experiment_id="exp_12345678",
        document_type=DocumentType.SUMMARY,
        status=DocumentStatus.COMPLETED,
    )
    return repo


@pytest.fixture
def mock_llm_client():
    client = AsyncMock()
    client.complete.return_value = "## Visão Geral\n\nO experimento otimizado..."
    return client


@pytest.mark.asyncio
async def test_generate_summary_saves_to_experiment_documents(
    mock_exploration_repo,
    mock_node_repo,
    mock_document_repo,
    mock_llm_client,
):
    """Verifica que summary é salvo em experiment_documents com experiment_id correto."""
    service = ExplorationSummaryGeneratorService(
        exploration_repo=mock_exploration_repo,
        node_repo=mock_node_repo,
        document_repo=mock_document_repo,
        llm_client=mock_llm_client,
    )

    await service.generate_for_exploration("expl_a1b2c3d4")

    # Verificar que create foi chamado com experiment_id (não exploration_id)
    create_call = mock_document_repo.create.call_args
    doc = create_call[0][0]
    assert doc.experiment_id == "exp_12345678"
    assert doc.document_type == DocumentType.SUMMARY
    assert doc.metadata["source"] == "exploration"
    assert doc.metadata["exploration_id"] == "expl_a1b2c3d4"
```

---

## Manual Testing Checklist

### Backend API

- [ ] POST /explorations/{id}/documents/summary/generate retorna 422 se exploration não completa
- [ ] POST /explorations/{id}/documents/summary/generate retorna 409 se geração já em progresso
- [ ] POST /explorations/{id}/documents/summary/generate cria documento em experiment_documents
- [ ] GET /explorations/{id}/documents/summary retorna 404 se não existe
- [ ] GET /explorations/{id}/documents/summary retorna documento com metadata correta
- [ ] DELETE /explorations/{id}/documents/summary remove documento

### Verificar Armazenamento Correto

```sql
-- Após gerar summary para exploration expl_a1b2c3d4:
SELECT * FROM experiment_documents
WHERE experiment_id = 'exp_12345678'
  AND document_type = 'summary';

-- Verificar metadata
SELECT metadata FROM experiment_documents
WHERE experiment_id = 'exp_12345678'
  AND document_type = 'summary';
-- Deve retornar: {"source": "exploration", "exploration_id": "expl_a1b2c3d4", ...}
```

### Frontend UI

- [ ] Generate button disabled quando exploration.status=RUNNING
- [ ] Generate button enabled quando exploration.status=GOAL_ACHIEVED
- [ ] Clicking "Gerar Sumário" mostra loading
- [ ] Summary card exibe markdown após geração
- [ ] "Regenerar" atualiza documento existente
- [ ] Estado de erro mostra mensagem e botão "Tentar Novamente"

---

## Key Files Reference

| Component | File | Status |
|-----------|------|--------|
| Entity | `domain/entities/experiment_document.py` | ✅ EXISTENTE |
| Enums | `DocumentType`, `DocumentStatus` | ✅ EXISTENTE |
| Repository | `repositories/experiment_document_repository.py` | ✅ EXISTENTE |
| Table | `experiment_documents` | ✅ EXISTENTE |
| Migration | N/A | ✅ NÃO PRECISA |
| Service Summary | `services/exploration_summary_generator_service.py` | ⏳ CRIAR |
| Service PRFAQ | `services/exploration_prfaq_generator_service.py` | ⏳ CRIAR |
| Router | `api/routers/exploration.py` | ⏳ MODIFICAR |
| Hook Generate | `hooks/useGenerateExplorationSummary.ts` | ⏳ CRIAR |
| Component | `components/exploration/ExplorationSummaryCard.tsx` | ⏳ CRIAR |

---

## Common Pitfalls

1. **CRIAR TABELA NOVA**: NÃO crie tabela. Use `experiment_documents` existente.
2. **Usar exploration_id no documento**: Use `exploration.experiment_id` como FK.
3. **Esquecer metadata source**: Sempre incluir `source: "exploration"` no metadata.
4. **Phoenix Tracing**: Todas chamadas LLM DEVEM usar `_tracer.start_as_current_span()`.
5. **SQL Injection**: Use queries parametrizadas (`?` placeholders).
6. **Race Conditions**: Verificar status=generating antes de permitir regeneração.

---

## Next Steps

1. Run `/speckit.tasks` para gerar tasks de implementação
2. Seguir TDD: Write tests → Run (fail) → Implement → Run (pass) → Refactor
3. Commitar frequentemente em milestones lógicos
4. Rodar fast test battery antes de cada commit
5. Rodar full test battery antes de criar PR

**Ready for Implementation!**
