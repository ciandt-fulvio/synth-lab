# Quickstart: Unified Experiment Documents

Este guia mostra como usar a API de documentos unificados para experimentos.

## Pré-requisitos

1. Servidor API rodando: `uv run uvicorn synth_lab.api.main:app --reload`
2. Um experimento existente com análise quantitativa completa
3. Pelo menos 2 chart insights gerados

## Verificar Disponibilidade de Documentos

```bash
# Verificar quais documentos estão disponíveis
curl http://localhost:8000/experiments/{experiment_id}/documents/availability

# Resposta esperada:
{
  "summary": {"available": false, "status": null},
  "prfaq": {"available": false, "status": null},
  "executive_summary": {"available": false, "status": null}
}
```

## Listar Documentos Existentes

```bash
# Listar todos os documentos de um experimento
curl http://localhost:8000/experiments/{experiment_id}/documents

# Resposta (lista vazia se não houver documentos):
[]

# Resposta (com documentos):
[
  {
    "id": "doc_12345678",
    "document_type": "executive_summary",
    "status": "completed",
    "generated_at": "2025-12-31T10:00:00Z",
    "model": "o1-mini"
  }
]
```

## Gerar Resumo Executivo

```bash
# Iniciar geração (assíncrona)
curl -X POST http://localhost:8000/experiments/{experiment_id}/documents/executive_summary/generate

# Resposta:
{
  "document_id": null,
  "status": "generating",
  "message": "Started generation of executive_summary"
}

# Verificar status (polling)
curl http://localhost:8000/experiments/{experiment_id}/documents/executive_summary

# Resposta quando completo:
{
  "id": "doc_12345678",
  "experiment_id": "exp_abcdef12",
  "document_type": "executive_summary",
  "markdown_content": "## Visão Geral\n\n...",
  "metadata": {
    "analysis_id": "ana_12345678",
    "included_chart_types": ["try_vs_success", "shap_summary"],
    "total_insights": 4,
    "completed_insights": 3
  },
  "generated_at": "2025-12-31T10:05:00Z",
  "model": "o1-mini",
  "status": "completed",
  "error_message": null
}
```

## Obter Conteúdo Markdown

```bash
# Obter apenas o markdown (para renderização no frontend)
curl http://localhost:8000/experiments/{experiment_id}/documents/executive_summary/markdown

# Resposta (text/markdown):
## Visão Geral

O experimento testou a aceitação de usuários para...

## Explicabilidade

Os principais drivers de sucesso foram...

## Segmentação

Identificamos 3 grupos de usuários...

## Casos Extremos

Observamos comportamento anômalo em...

## Recomendações

- **Recomendação 1:** Priorizar melhorias na interface de onboarding
- **Recomendação 2:** Implementar suporte ao idioma nativo
```

## Deletar Documento

```bash
# Deletar um documento específico
curl -X DELETE http://localhost:8000/experiments/{experiment_id}/documents/executive_summary

# Resposta:
{
  "deleted": true,
  "document_type": "executive_summary"
}
```

## Erros Comuns

### Erro 400: Sem análise completa

```json
{
  "detail": "No completed analysis found for this experiment. Run quantitative analysis first."
}
```

**Solução**: Execute a análise quantitativa antes de gerar o resumo executivo.

### Erro 404: Documento não encontrado

```json
{
  "detail": "Document 'executive_summary' not found for experiment exp_12345678"
}
```

**Solução**: Gere o documento primeiro usando o endpoint `/generate`.

## Uso no Frontend

```typescript
import { checkAvailability, generateDocument, getDocument } from '@/services/documents-api';

// Verificar disponibilidade
const availability = await checkAvailability('exp_12345678');
if (!availability.executive_summary.available) {
  // Gerar documento
  await generateDocument('exp_12345678', 'executive_summary');

  // Polling para verificar conclusão
  let doc = await getDocument('exp_12345678', 'executive_summary');
  while (doc.status === 'generating') {
    await new Promise(r => setTimeout(r, 2000));
    doc = await getDocument('exp_12345678', 'executive_summary');
  }
}

// Documento disponível
console.log(doc.markdown_content);
```
