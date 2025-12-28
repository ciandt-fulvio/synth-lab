# Research Notes: 019-experiment-refactor

**Date**: 2025-12-27
**Purpose**: Resolver decisões técnicas e investigar estado atual do SSE

## Decisões Técnicas

### 1. Estratégia de Embedding do Scorecard

**Decision**: Armazenar scorecard como JSON column no experimento

**Rationale**:
- SQLite tem excelente suporte JSON1 (já em uso no projeto)
- Evita JOINs complexos para operações comuns
- Mantém atomicidade - experimento e scorecard são criados/atualizados juntos
- Scorecard nunca é compartilhado entre experimentos

**Alternatives Considered**:
1. **Manter tabela separada com FK**: Rejeitado porque adiciona complexidade sem benefício (scorecard é sempre 1:1 com experimento)
2. **Normalizar dimensões em tabela própria**: Rejeitado porque dimensões são sempre lidas/escritas em conjunto
3. **Duas tabelas com CASCADE DELETE**: Mais complexo sem ganho

**Implementation**: Coluna `scorecard_data` criada junto com tabela experiments (estrutura nova do zero)

### 2. Relação Experimento-Análise (1:1)

**Decision**: Criar tabela `analysis_runs` com `experiment_id` direto e UNIQUE constraint

**Rationale**:
- Estrutura nova do zero - podemos modelar corretamente
- UNIQUE constraint em `experiment_id` garante 1:1 no banco
- Referência direta ao experimento (sem passar por scorecard)
- Re-execução substitui análise anterior

**Alternatives Considered**:
1. **Embedded analysis results no experiment**: Rejeitado porque resultados podem ser grandes (synth_outcomes)
2. **Múltiplas análises (manter histórico)**: Rejeitado - spec pede exatamente 1 análise por experimento

**Implementation Approach**:
```python
class ExperimentService:
    def run_analysis(self, experiment_id: str, config: AnalysisConfig) -> AnalysisRun:
        experiment = self.repository.get_by_id(experiment_id)
        if not experiment.scorecard_data:
            raise ValueError("Experiment must have scorecard before running analysis")

        # Deleta análise anterior se existir
        self.analysis_repo.delete_by_experiment(experiment_id)

        # Cria nova análise
        return self.analysis_repo.create(experiment_id, config)
```

### 3. Nomenclatura (Análise Quantitativa)

**Decision**: Usar nomenclatura consistente "analysis" em todo o código (estrutura nova do zero)

**Rationale**:
- Estrutura nova - podemos nomear corretamente desde o início
- Evita confusão entre termos diferentes em camadas diferentes
- Código mais legível e autodocumentado

**Nomenclatura Completa**:

| Camada | Nome |
|--------|------|
| UI (PT) | "Análise Quantitativa" |
| UI (EN) | "Quantitative Analysis" |
| API endpoints | `/experiments/{id}/analysis` |
| API fields | `analysis`, `analysis_status` |
| Table | `analysis_runs` |
| Entity | `AnalysisRun` |
| Repository | `AnalysisRepository` |
| Service | `AnalysisService` |
| Files | `analysis_run.py`, `analysis_repository.py`

### 4. Estado do SSE no Frontend

**Investigation Result**: SSE backend está funcional, frontend precisa verificação

**Backend Status** (Verified):
- Endpoint: `GET /api/research/{exec_id}/stream`
- Implementação: `src/synth_lab/api/routers/research.py` (lines 192-304)
- Usa `StreamingResponse` com `text/event-stream`
- Eventos: `message`, `interview_completed`, `transcription_completed`, `execution_completed`
- Replay de mensagens históricas funciona

**Frontend Status** (To Verify):
- Hook: `frontend/src/hooks/use-sse.ts`
- Component: `frontend/src/components/interviews/LiveInterviewGrid.tsx`
- Page: `frontend/src/pages/InterviewDetail.tsx`

**Potential Issues to Check**:
1. URL base incorreta (deve usar `/api` prefix via proxy Vite)
2. EventSource não sendo criado quando `enabled=true`
3. Cleanup de conexões não funcionando
4. Page não passando props corretas para LiveInterviewGrid

**Action Items**:
- [ ] Verificar se InterviewDetail passa `enabled=true` para LiveInterviewGrid
- [ ] Verificar se use-sse.ts cria EventSource com URL correta
- [ ] Testar manualmente abrindo DevTools Network e verificando SSE connection
- [ ] Verificar se há erros de CORS ou proxy

### 5. Estrutura de Banco de Dados (Nova)

**Decision**: Criar estrutura nova do zero (DB vazio, sem migração)

**Nova Estrutura**:
- `experiments`: Com `scorecard_data` JSON embutido
- `analysis_runs`: Referencia `experiment_id` diretamente (1:1)
- `synth_outcomes`: Resultados por synth
- `research_executions`: Entrevistas (N:1 com experiment)
- `transcripts`: Transcrições

**Tabelas Obsoletas** (não serão criadas):
- `feature_scorecards`: Scorecard agora é parte do experiment
- `simulation_runs`: Substituída por `analysis_runs`

## Padrões a Seguir

### Backend Architecture (from docs/arquitetura.md)

```python
# Router - ONLY request → service → response
@router.post("/{experiment_id}/analysis")
async def run_analysis(experiment_id: str, config: AnalysisConfig):
    service = get_experiment_service()
    return service.run_analysis(experiment_id, config)  # ✅

# Service - Business logic + LLM calls
class ExperimentService:
    def run_analysis(self, experiment_id: str, config: AnalysisConfig):
        with _tracer.start_as_current_span("run_analysis"):  # ✅ Tracing
            experiment = self.repository.get_by_id(experiment_id)
            # Business logic here
            return self.analysis_repo.create(...)

# Repository - SQL only
class ExperimentRepository:
    def get_by_id(self, exp_id: str) -> Experiment | None:
        row = self.db.fetchone(
            "SELECT * FROM experiments WHERE id = ?",  # ✅ Parametrized
            (exp_id,)
        )
```

### Frontend Architecture (from docs/arquitetura_front.md)

```typescript
// Service - API calls only
export async function runAnalysis(experimentId: string, config: AnalysisConfig) {
  return fetchAPI(`/experiments/${experimentId}/analysis`, {
    method: 'POST',
    body: JSON.stringify(config),
  });
}

// Hook - React Query wrapper
export function useRunAnalysis() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ experimentId, config }) => runAnalysis(experimentId, config),
    onSuccess: (_, { experimentId }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.experimentDetail(experimentId) });
    },
  });
}

// Component - Pure (props → JSX)
function AnalysisCard({ analysis, onRerun }: Props) {
  return <Card>...</Card>;  // No fetch inside
}

// Page - Composition + hooks
function ExperimentDetail() {
  const { data } = useExperiment(id);  // ✅ Hook for data
  const { mutate } = useRunAnalysis();
  return <AnalysisCard analysis={data.analysis} onRerun={mutate} />;
}
```

## Próximos Passos

1. **Phase 1**: Criar data-model.md com schema atualizado
2. **Phase 1**: Criar contracts/ com OpenAPI specs
3. **Phase 1**: Criar quickstart.md
4. **Phase 2**: Gerar tasks.md via /speckit.tasks
