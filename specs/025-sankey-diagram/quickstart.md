# Quickstart: Sankey Diagram for Outcome Flow Visualization

**Feature**: 025-sankey-diagram
**Date**: 2025-12-31

## Visão Geral

O diagrama Sankey "Fluxo de Resultados" visualiza como a população de synths flui através dos outcomes da simulação até as causas raiz de não-adoção e falha.

```
┌──────────┐
│População │
│   500    │
└────┬─────┘
     │
     ├────────────────┬────────────────┐
     ▼                ▼                ▼
┌─────────┐     ┌─────────┐      ┌─────────┐
│Não tentou│    │ Falhou  │      │ Sucesso │
│   180    │    │   140   │      │   180   │
└────┬─────┘    └────┬────┘      └─────────┘
     │               │
     ├───┬───┐       ├───┐
     ▼   ▼   ▼       ▼   ▼
   ┌───┬───┬───┐   ┌───┬───┐
   │95 │60 │25 │   │90 │50 │
   │   │   │   │   │   │   │
   │Ris│Esf│Com│   │Cap│Pac│
   └───┴───┴───┘   └───┴───┘
```

## Pré-requisitos

1. Um experimento com análise concluída (status = "completed")
2. O experimento deve ter synths com resultados de simulação

## Como Usar

### Via Interface Web

1. Navegue até `/experiments/{id}` (página de detalhes do experimento)
2. Vá para a seção "Análise Quantitativa"
3. Selecione a aba "Geral" (Overview)
4. O diagrama Sankey aparece no topo, acima do gráfico "Tentativa vs Sucesso"

### Via API

```bash
# Obter dados do Sankey
curl -X GET "http://localhost:8000/experiments/{experiment_id}/analysis/charts/sankey-flow"
```

**Resposta de exemplo:**

```json
{
  "analysis_id": "ana_12345678",
  "nodes": [
    {"id": "population", "label": "População", "level": 1, "color": "#6366f1", "value": 500},
    {"id": "did_not_try", "label": "Não tentou", "level": 2, "color": "#f59e0b", "value": 180},
    {"id": "failed", "label": "Falhou", "level": 2, "color": "#ef4444", "value": 140},
    {"id": "success", "label": "Sucesso", "level": 2, "color": "#22c55e", "value": 180},
    {"id": "risk_barrier", "label": "Risco percebido", "level": 3, "color": "#fb923c", "value": 95}
  ],
  "links": [
    {"source": "population", "target": "did_not_try", "value": 180},
    {"source": "population", "target": "failed", "value": 140},
    {"source": "population", "target": "success", "value": 180},
    {"source": "did_not_try", "target": "risk_barrier", "value": 95}
  ],
  "total_synths": 500,
  "outcome_counts": {"did_not_try": 180, "failed": 140, "success": 180}
}
```

## Interpretando os Resultados

### Nível 1 → Nível 2 (Outcomes)

| Outcome | Significado | Cor |
|---------|-------------|-----|
| Não tentou | Synth não tentou usar a feature | Âmbar |
| Falhou | Synth tentou mas não teve sucesso | Vermelho |
| Sucesso | Synth usou a feature com sucesso | Verde |

### Nível 2 → Nível 3 (Causas Raiz)

**Para "Não tentou":**

| Causa | Significado | Ação Sugerida |
|-------|-------------|---------------|
| Esforço inicial alto | O esforço necessário excede a motivação do usuário | Reduzir barreiras de entrada, simplificar onboarding |
| Risco percebido | O risco percebido excede a confiança do usuário | Melhorar comunicação de segurança, adicionar garantias |
| Complexidade aparente | A complexidade aparente excede a tolerância do usuário | Simplificar UI, melhorar primeira impressão |

**Para "Falhou":**

| Causa | Significado | Ação Sugerida |
|-------|-------------|---------------|
| Capability insuficiente | A complexidade real excede a capacidade do usuário | Adicionar tutoriais, simplificar fluxo |
| Desistiu antes do valor | O tempo até o valor excede a paciência do usuário | Acelerar time-to-value, mostrar progresso |

## Código de Exemplo (Frontend)

```tsx
import { useAnalysisSankeyFlow } from '@/hooks/use-analysis-charts';

function SankeyFlowSection({ experimentId }: { experimentId: string }) {
  const { data, isLoading, error } = useAnalysisSankeyFlow(experimentId);

  if (isLoading) return <Skeleton className="h-[400px]" />;
  if (error) return <ErrorState message="Erro ao carregar dados" />;
  if (!data) return <EmptyState message="Nenhum dado disponível" />;

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Fluxo de Resultados</h3>
      <SankeyFlowChart data={data} />
    </div>
  );
}
```

## Validação

Execute os testes unitários para verificar o cálculo de gaps:

```bash
# Backend
pytest tests/unit/test_sankey_flow.py -v

# Verificar endpoint
pytest tests/integration/test_analysis_sankey.py -v
```

## Troubleshooting

### Diagrama não aparece

1. Verifique se a análise está com status "completed"
2. Verifique se há outcomes de synths no banco de dados
3. Confira o console do navegador para erros de API

### Valores zerados em algumas causas

Isso é esperado quando nenhum synth se enquadra naquela causa específica. Fluxos com valor zero são omitidos do diagrama.

### Performance lenta

Para experimentos com mais de 5.000 synths, o cálculo pode levar alguns segundos. Os dados são cacheados por 5 minutos após a primeira requisição.
