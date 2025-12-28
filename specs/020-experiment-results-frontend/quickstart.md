# Quickstart: Experiment Results Frontend

**Feature**: 020-experiment-results-frontend
**Date**: 2025-12-28

## Visão Geral

Este guia descreve como usar os resultados de análise de experimentos no frontend do SynthLab. A funcionalidade exibe os resultados de simulação em 6 fases sequenciais, cada uma respondendo a uma pergunta de pesquisa específica.

## Pré-requisitos

1. Backend rodando com endpoints de simulação implementados
2. Experimento com simulação executada (status: `completed`)
3. Frontend development server ativo (`npm run dev`)

## Navegação para Resultados

1. Acesse a lista de experimentos: `/experiments`
2. Clique em um experimento para ver detalhes: `/experiments/{id}`
3. Na seção "Resultados da Análise", use as abas para navegar entre as fases

## Fases de Análise

### Fase 1: Visão Geral

**Pergunta**: "O que aconteceu?"

**Gráficos disponíveis**:
- **Try vs Success**: Scatter plot mostrando tentativa vs sucesso por synth
- **Distribuição**: Barras empilhadas com taxas de sucesso/falha/não tentou
- **Sankey**: Fluxo de synths através das etapas de decisão

**Como usar**:
1. Identifique o quadrante dominante no Try vs Success
2. Verifique a distribuição geral de outcomes
3. Analise onde os synths "se perdem" no fluxo Sankey

### Fase 2: Localização

**Pergunta**: "Onde exatamente a experiência tem mais potencial de problema?"

**Gráficos disponíveis**:
- **Heatmap**: Correlação entre atributos e taxa de falha
- **Box Plot**: Distribuição de valores por categoria de outcome
- **Scatter**: Correlação entre dois atributos
- **Tornado**: Impacto de cada dimensão na taxa de sucesso

**Como usar**:
1. No heatmap, identifique combinações de atributos com alta falha (células vermelhas)
2. Use scatter para explorar correlações específicas
3. No tornado, veja quais dimensões têm maior impacto

### Fase 3: Segmentação

**Pergunta**: "Quem são os grupos distintos de usuários?"

**Funcionalidades**:
- **Gerar Clusters**: Escolha K-Means ou Hierárquico
- **Elbow Chart**: Visualize o número ótimo de clusters
- **Radar**: Compare perfis de clusters
- **Dendrograma**: Visualize hierarquia de clusters

**Como usar**:
1. Clique "Gerar Clusters" com método K-Means
2. Use o elbow chart para escolher k ideal (cotovelo da curva)
3. Compare clusters no radar chart para entender diferenças

### Fase 4: Casos Especiais

**Pergunta**: "Quais synths devo entrevistar?"

**Tabelas disponíveis**:
- **Piores Falhas**: Top N synths com maior taxa de falha
- **Melhores Sucessos**: Top N synths com maior taxa de sucesso
- **Inesperados**: Synths que desafiaram expectativas

**Como usar**:
1. Revise a lista de piores falhas para entender barreiras
2. Analise melhores sucessos para identificar fatores de sucesso
3. Casos inesperados revelam nuances não capturadas pelos modelos

### Fase 5: Aprofundamento

**Pergunta**: "Por que este synth específico falhou/teve sucesso?"

**Visualizações**:
- **SHAP Summary**: Importância global de features
- **SHAP Waterfall**: Contribuição de cada feature para um synth
- **PDP**: Como uma feature afeta a predição
- **PDP Comparison**: Compare efeitos de múltiplas features

**Como usar**:
1. Veja SHAP Summary para features mais importantes
2. Selecione um synth específico para ver sua explicação SHAP
3. Use PDP para entender efeitos marginais de features

### Fase 6: Insights LLM

**Pergunta**: "Como comunico os achados para stakeholders?"

**Funcionalidades**:
- **Gerar Insight**: Cria caption, explicação e recomendação para cada gráfico
- **Lista de Insights**: Visualize todos os insights gerados
- **Sumário Executivo**: Sintetiza todos os insights em um resumo

**Como usar**:
1. Para cada gráfico importante, clique "Gerar Insight"
2. Revise o insight gerado (caption, explicação, evidências)
3. Quando tiver insights suficientes, gere o Sumário Executivo

## Exemplo de Fluxo de Análise

```
1. Visão Geral
   ↓ "60% dos synths tentam, mas só 40% têm sucesso"
2. Localização
   ↓ "Combinação baixa confiança + baixa capacidade tem 80% de falha"
3. Segmentação
   ↓ "3 clusters distintos: Engajados, Hesitantes, Desistentes"
4. Casos Especiais
   ↓ "10 synths do cluster 'Hesitantes' para entrevista"
5. Aprofundamento
   ↓ "trust_mean é o fator mais importante (SHAP = 0.15)"
6. Insights
   → "Resumo: Foco em construir confiança antes do onboarding"
```

## Estados de UI

### Loading
- Skeleton animado enquanto dados carregam
- Spinner para operações longas (clustering, SHAP)

### Error
- Mensagem de erro com botão "Tentar Novamente"
- Detalhes técnicos em modo debug

### Empty
- Mensagem explicativa quando não há dados
- Sugestão de próxima ação

## Atalhos de Teclado

| Tecla | Ação |
|-------|------|
| `←` / `→` | Navegar entre fases |
| `Esc` | Fechar popup/modal |

## Troubleshooting

### Gráfico não carrega
1. Verifique se a simulação está com status `completed`
2. Confira se há dados suficientes (mínimo 10 synths para clustering)
3. Verifique console do browser para erros de API

### SHAP/PDP demora muito
- SHAP e PDP exigem cálculos intensivos
- Para simulações grandes (>1000 synths), pode levar alguns segundos
- Resultados são cacheados após primeira execução

### Insight não gera
- Certifique-se de que há dados no gráfico
- Verifique se a API de LLM está configurada
- Tente com `force_regenerate: true`

## Referências

- **Spec**: [spec.md](./spec.md)
- **Data Model**: [data-model.md](./data-model.md)
- **API Contracts**: [contracts/simulation-api.md](./contracts/simulation-api.md)
- **Arquitetura Frontend**: [docs/arquitetura_front.md](../../docs/arquitetura_front.md)
