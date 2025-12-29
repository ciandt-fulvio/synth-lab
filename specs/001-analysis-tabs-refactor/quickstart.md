# Quickstart: Analysis Tabs Refactor

**Feature**: 001-analysis-tabs-refactor
**Date**: 2025-12-29

## Overview

Este guia mostra a nova jornada de análise quantitativa após a reorganização das abas.

## Nova Estrutura de Abas (5 Fases)

```
┌─────────────────────────────────────────────────────────────┐
│  Análise Quantitativa - 5 fases de investigação            │
├─────────────────────────────────────────────────────────────┤
│  [Geral] [Influência] [Segmentos] [Especiais] [Insights]   │
└─────────────────────────────────────────────────────────────┘
```

**Mudanças**:
- ❌ Removido: Aba "Deep Dive" (6ª fase)
- ✅ Mantido: 5 abas principais

---

## Fase 2: Influência (Reorganizada)

### O que mudou?
- ✅ **Adicionado**: Importância de Features (SHAP Summary)
- ✅ **Adicionado**: Dependência Parcial (PDP)
- ❌ **Removido**: Importância dos Atributos (antigo)
- ❌ **Removido**: Correlação de Atributos (antigo)

### Como usar?

1. **Navegue** até a aba "Influência"
2. **Visualize** os 2 gráficos principais:
   - **SHAP Summary**: Mostra quais atributos mais impactam o resultado
   - **PDP**: Mostra como cada atributo afeta a probabilidade de sucesso

**Não há configuração necessária** - os gráficos aparecem automaticamente.

---

## Fase 4: Especiais (Redesenhada)

### Casos Extremos - Click to Explain

**O que mudou?**:
- ❌ **Removido**: Perguntas sugeridas
- ❌ **Removido**: Coluna "Casos Inesperados"
- ✅ **Adicionado**: Explicação Individual (SHAP Waterfall) na mesma página
- ✅ **Adicionado**: Click-to-explain nos cards
- ✅ **Adicionado**: Botão de entrevista automática

**Como usar?**:

1. **Visualize** os casos extremos:
   - **Top 5 Performers**: Cards dos 5 melhores synths
   - **Bottom 5 Performers**: Cards dos 5 piores synths

2. **Clique** em qualquer card para ver explicação individual:
   ```
   Card (Synth A - 85% sucesso)
         ↓ [Click]
   SHAP Waterfall aparece abaixo mostrando:
   - Quais atributos contribuíram para o resultado
   - Direção do impacto (positivo/negativo)
   ```

3. **Entreviste automaticamente** os casos extremos:
   ```
   [Entrevistar Casos Extremos] ← Click no botão
         ↓
   Sistema cria entrevista com 10 synths (5 top + 5 bottom)
         ↓
   "Ver Entrevista" ← Link para acompanhar
   ```

### Outliers Estatísticos - Simplificados

**O que mudou?**:
- ✅ **Renomeado**: Slider agora tem nome claro ("Sensibilidade de Detecção")
- ❌ **Removido**: Barra de anomalia dentro dos cards
- ❌ **Removido**: Número laranja confuso no topo
- ❌ **Removido**: Tag "Perfil Atípico"
- ✅ **Adicionado**: Click-to-explain nos cards

**Como usar?**:

1. **Ajuste** a sensibilidade:
   ```
   Sensibilidade de Detecção: [────●─────] 0.8
   ```
   - Mover para direita: Detecta outliers mais extremos (menos resultados)
   - Mover para esquerda: Detecta outliers mais sutis (mais resultados)

2. **Clique** em qualquer card de outlier para ver explicação individual:
   ```
   Card (Synth B - Outlier)
         ↓ [Click]
   SHAP Waterfall aparece abaixo
   ```

---

## Fluxo Completo de Uso

### Cenário 1: Investigar por que alguns usuários falham

```
1. Aba "Especiais" → Seção "Casos Extremos"
2. Olhe os Bottom 5 Performers
3. Clique em um card
4. Veja SHAP Waterfall: "Ah, baixa confiança é o problema!"
5. [Opcional] Clique em "Entrevistar Casos Extremos"
6. Acesse entrevista para insights qualitativos
```

### Cenário 2: Entender quais atributos importam

```
1. Aba "Influência"
2. SHAP Summary: "Confiança é o atributo #1"
3. PDP: "Confiança > 0.7 aumenta sucesso em 40%"
4. Ação: Focar em melhorar confiança do produto
```

### Cenário 3: Encontrar comportamentos anômalos

```
1. Aba "Especiais" → Seção "Outliers"
2. Ajuste sensibilidade para 0.9 (detectar apenas extremos)
3. Sistema mostra 3 outliers
4. Clique em cada um para entender POR QUÊ são anômalos
5. SHAP Waterfall revela: "Atributos contraditórios"
```

---

## Atalhos de Navegação

| Ação | Como fazer |
|------|------------|
| Ver atributos que importam | Aba "Influência" |
| Entender casos extremos | Aba "Especiais" → Click no card |
| Criar entrevista rápida | Aba "Especiais" → "Entrevistar Casos Extremos" |
| Detectar anomalias | Aba "Especiais" → Ajustar slider de outliers |

---

## Troubleshooting

### "Não vejo os gráficos na aba Influência"
- Verifique se a análise de Monte Carlo foi executada
- Empty state deve explicar que análise é necessária

### "Click no card não mostra explicação"
- Aguarde loading state
- Se erro persistir, verifique console do navegador

### "Entrevista automática falhou"
- Verifique se há pelo menos 10 synths no experimento
- Toast de erro deve mostrar mensagem clara

### "Não há outliers detectados"
- Ajuste o slider de sensibilidade para esquerda (menos restritivo)
- Empty state deve explicar que não há outliers com sensibilidade atual
