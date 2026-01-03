# Data Model: Exploration Summary and PRFAQ Generation

**Date**: 2026-01-02
**Status**: Complete
**Pattern**: Reutiliza `experiment_documents` existente (NÃO cria tabela nova)

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
│  ExperimentDocument     │                          │
│ ─────────────────────── │                          │
│ id: str (PK)            │                          │
│ experiment_id: str (FK) │ ─────────────────────────┤
│ document_type: enum     │                          │
│ metadata: JSON          │ ← {"exploration_id": "expl_...", "winning_path_nodes": [...]}
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

## Princípio Fundamental

**Explorations pertencem a Experiments. Documentos de explorations vão em `experiment_documents` usando o `experiment_id` da exploration.**

```python
# Exploration tem experiment_id
exploration = Exploration(
    id="expl_12345678",
    experiment_id="exp_abcdef12",  # ← FK para experiment
    ...
)

# Documento vai em experiment_documents (tabela existente!)
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
```

---

## O Que Já Existe (Não Modificar)

### ExperimentDocument Entity

**File**: `src/synth_lab/domain/entities/experiment_document.py` (EXISTENTE)

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

### DocumentType Enum

**File**: `src/synth_lab/domain/entities/experiment_document.py` (EXISTENTE)

```python
class DocumentType(str, Enum):
    SUMMARY = "summary"
    PRFAQ = "prfaq"
    EXECUTIVE_SUMMARY = "executive_summary"
```

### DocumentStatus Enum

**File**: `src/synth_lab/domain/entities/experiment_document.py` (EXISTENTE)

```python
class DocumentStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"
```

### experiment_documents Table

**File**: `src/synth_lab/models/orm/document.py` (EXISTENTE)

```sql
-- JÁ EXISTE! Não criar nova tabela!
CREATE TABLE experiment_documents (
    id VARCHAR(50) PRIMARY KEY,
    experiment_id VARCHAR(50) REFERENCES experiments(id),
    document_type VARCHAR(50),
    markdown_content TEXT,
    metadata JSONB,  -- ← Aqui vai exploration_id + winning_path_nodes
    generated_at VARCHAR(50),
    model VARCHAR(50),
    status VARCHAR(20),
    error_message TEXT,
    UNIQUE (experiment_id, document_type)
);
```

---

## O Que Criar (Novo)

### 1. Metadata Schema para Exploration Documents

**Não é entity nova - é estrutura do campo `metadata` JSON**

```python
# Estrutura do metadata quando documento vem de exploration
exploration_document_metadata = {
    "source": "exploration",                    # Identifica origem
    "exploration_id": "expl_12345678",          # Qual exploration gerou
    "winning_path_nodes": [                     # Caminho vencedor
        "node_00000001",
        "node_00000005",
        "node_0000000a"
    ],
    "path_length": 3,
    "baseline_success_rate": 0.48,
    "final_success_rate": 0.55,
    "improvement_percentage": 14.6
}
```

### 2. Service de Geração

**File**: `src/synth_lab/services/exploration_summary_generator_service.py` (NOVO)

```python
class ExplorationSummaryGeneratorService:
    """Gera summary para exploration, salva em experiment_documents."""

    def __init__(
        self,
        exploration_repo: ExplorationRepository,
        node_repo: ScenarioNodeRepository,
        document_repo: ExperimentDocumentRepository,  # ← Repo existente!
        llm_client: LLMClient
    ):
        ...

    async def generate_for_exploration(
        self,
        exploration_id: str
    ) -> ExperimentDocument:  # ← Entity existente!
        # 1. Buscar exploration
        exploration = self.exploration_repo.get_by_id(exploration_id)

        # 2. Buscar winning path
        winning_path = self._get_winning_path(exploration_id)

        # 3. Gerar conteúdo via LLM
        content = await self._generate_content(exploration, winning_path)

        # 4. Criar documento no EXPERIMENT (não na exploration!)
        doc = ExperimentDocument(
            id=generate_document_id(),
            experiment_id=exploration.experiment_id,  # ← EXPERIMENT_ID!
            document_type=DocumentType.SUMMARY,
            markdown_content=content,
            metadata={
                "source": "exploration",
                "exploration_id": exploration_id,
                "winning_path_nodes": [n.id for n in winning_path],
                "path_length": len(winning_path),
                "final_success_rate": winning_path[-1].get_success_rate()
            },
            status=DocumentStatus.COMPLETED
        )

        # 5. Salvar usando repo existente
        return self.document_repo.create(doc)
```

### 3. Service de PRFAQ

**File**: `src/synth_lab/services/exploration_prfaq_generator_service.py` (NOVO)

Mesmo padrão que summary, muda só o prompt e `document_type=DocumentType.PRFAQ`

---

## Repository - Usar Existente

### ExperimentDocumentRepository (JÁ EXISTE)

**File**: `src/synth_lab/repositories/experiment_document_repository.py` (EXISTENTE)

**Métodos disponíveis**:
- `create(doc)` - Criar documento
- `get_by_experiment(experiment_id, doc_type)` - Buscar por experiment + tipo
- `get_markdown(experiment_id, doc_type)` - Buscar só markdown
- `list_by_experiment(experiment_id)` - Listar todos do experiment
- `update_status(doc_id, status, ...)` - Atualizar status

**Uso para Exploration**:
```python
# Buscar summary gerado por exploration
doc = repo.get_by_experiment(
    experiment_id=exploration.experiment_id,
    doc_type=DocumentType.SUMMARY
)

# Verificar se veio de exploration
if doc.metadata and doc.metadata.get("source") == "exploration":
    exploration_id = doc.metadata.get("exploration_id")
    winning_path = doc.metadata.get("winning_path_nodes")
```

---

## API Endpoints

### Usar Endpoints Existentes ou Criar Wrapper

**Opção A: Usar endpoints existentes de /experiments/{id}/documents**

```
# Já existem em api/routers/documents.py
GET  /experiments/{experiment_id}/documents/{type}
POST /experiments/{experiment_id}/documents/{type}/generate
```

**Opção B: Criar wrapper em /explorations/{id}/documents** (Recomendado)

```
# Novos em api/routers/exploration.py
POST /explorations/{exploration_id}/documents/summary/generate
GET  /explorations/{exploration_id}/documents/summary
POST /explorations/{exploration_id}/documents/prfaq/generate
GET  /explorations/{exploration_id}/documents/prfaq

# Internamente: busca exploration.experiment_id e usa document_repo existente
```

**Implementação do wrapper**:
```python
@router.post("/{exploration_id}/documents/summary/generate")
async def generate_exploration_summary(
    exploration_id: str,
    summary_service: ExplorationSummaryGeneratorService = Depends()
) -> ExperimentDocumentResponse:  # ← Schema existente!
    doc = await summary_service.generate_for_exploration(exploration_id)
    return ExperimentDocumentResponse.model_validate(doc)

@router.get("/{exploration_id}/documents/summary")
async def get_exploration_summary(
    exploration_id: str,
    exploration_repo: ExplorationRepository = Depends(),
    document_repo: ExperimentDocumentRepository = Depends()
) -> ExperimentDocumentResponse:
    exploration = exploration_repo.get_by_id(exploration_id)
    doc = document_repo.get_by_experiment(
        exploration.experiment_id,
        DocumentType.SUMMARY
    )
    return ExperimentDocumentResponse.model_validate(doc)
```

---

## Database Migration

### NÃO PRECISA DE MIGRATION!

A tabela `experiment_documents` já existe e suporta:
- Campo `metadata` JSONB (flexível para qualquer JSON)
- Todos os `document_type` necessários (summary, prfaq)
- Status tracking completo

**Única mudança**: Lógica nos services para popular `metadata` com dados de exploration.

---

## Arquivos para Criar/Modificar

### CRIAR (Novos)

| Arquivo | Propósito |
|---------|-----------|
| `services/exploration_summary_generator_service.py` | Gera summary usando LLM |
| `services/exploration_prfaq_generator_service.py` | Gera PRFAQ usando LLM |

### MODIFICAR (Existentes)

| Arquivo | Mudança |
|---------|---------|
| `api/routers/exploration.py` | Adicionar endpoints wrapper para documents |
| `api/schemas/exploration.py` | Adicionar response schemas (ou reusar de documents) |

### NÃO CRIAR

- ❌ `exploration_documents` table
- ❌ `ExplorationDocument` entity
- ❌ `ExplorationDocumentRepository`
- ❌ Novos enums
- ❌ Migration

---

## Resumo

| Item | Status |
|------|--------|
| Tabela | ✅ Usar `experiment_documents` existente |
| Entity | ✅ Usar `ExperimentDocument` existente |
| Enums | ✅ Usar `DocumentType`, `DocumentStatus` existentes |
| Repository | ✅ Usar `ExperimentDocumentRepository` existente |
| Metadata | ✅ JSON com `exploration_id` + `winning_path_nodes` |
| Migration | ✅ Não precisa |
| Novos Services | ⏳ Criar generator services para exploration |
| API Wrapper | ⏳ Criar endpoints em `/explorations/{id}/documents/` |

**Princípio**: Documentos de exploration são documentos do experiment pai. A exploration apenas **gera** o documento, mas ele **pertence** ao experiment.
