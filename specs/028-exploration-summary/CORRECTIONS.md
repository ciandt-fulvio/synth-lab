# Correções Aplicadas: Exploration Summary & PRFAQ

**Data**: 2026-01-02
**Status**: ✅ CORRIGIDO

---

## Histórico de Correções

### v1 (Errado)
- Criava 2 tabelas separadas: `exploration_summary`, `exploration_prfaq`
- Criava 2 entities separadas: `ExplorationSummary`, `ExplorationPRFAQ`
- Criava enum novo: `GenerationStatus`

### v2 (Ainda errado)
- Criava 1 tabela: `exploration_documents`
- Criava 1 entity: `ExplorationDocument`
- Ainda não usava infraestrutura existente

### v3 (CORRETO) ✅
- **NÃO cria tabela**: Usa `experiment_documents` existente
- **NÃO cria entity**: Usa `ExperimentDocument` existente
- **NÃO cria enums**: Usa `DocumentType` e `DocumentStatus` existentes
- **NÃO cria migration**: Tabela já existe
- **NÃO cria repository**: Usa `ExperimentDocumentRepository` existente

---

## Princípio Fundamental

**Explorations pertencem a Experiments. Documentos de exploration vão em `experiment_documents` usando `exploration.experiment_id`.**

```python
# Exploration tem experiment_id
exploration = Exploration(id="expl_12345678", experiment_id="exp_abcdef12")

# Documento vai em experiment_documents (EXISTENTE!)
doc = ExperimentDocument(
    id=generate_document_id(),
    experiment_id=exploration.experiment_id,  # ← USA EXPERIMENT_ID!
    document_type=DocumentType.SUMMARY,
    markdown_content="...",
    metadata={
        "source": "exploration",              # ← Identifica origem
        "exploration_id": exploration.id,     # ← Qual exploration gerou
        "winning_path_nodes": ["node_...", ...],
    }
)
```

---

## Arquivos Corrigidos

| Arquivo | Status |
|---------|--------|
| `plan.md` | ✅ Corrigido |
| `research.md` | ✅ Corrigido |
| `data-model.md` | ✅ Corrigido |
| `quickstart.md` | ✅ Corrigido |
| `contracts/exploration-summary-api.yaml` | ✅ Corrigido |

---

## Validação Final

- [x] Reutiliza tabela `experiment_documents` (NÃO cria tabela nova)
- [x] Reutiliza `ExperimentDocument` entity
- [x] Reutiliza `DocumentType` e `DocumentStatus` enums
- [x] Reutiliza `ExperimentDocumentRepository`
- [x] Metadata JSON identifica origem (`source: "exploration"`)
- [x] Zero migrations necessárias
- [x] Apenas 2 services novos no backend

---

**Ready for**: `/speckit.tasks` (Phase 2 - Task Generation)
