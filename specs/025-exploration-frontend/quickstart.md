# Quickstart: Exploracao de Cenarios

**Feature**: 025-exploration-frontend
**Date**: 2025-12-31

## Pre-requisitos

1. Backend rodando (spec 024 implementado)
2. Experimento com scorecard configurado
3. Analise baseline executada (pelo menos uma)

## Fluxo Basico

### 1. Acessar Experimento

```
URL: /experiments/{experiment_id}
```

Na pagina do experimento, voce vera a secao "Exploracoes" apos a secao de Analise.

### 2. Iniciar Nova Exploracao

1. Clique em **"Iniciar Exploracao"**
2. No formulario, defina:
   - **Meta de Success Rate**: % desejado (ex: 40%)
   - **Beam Width**: numero de cenarios a manter por iteracao (default: 3)
   - **Profundidade Maxima**: niveis de profundidade da arvore (default: 5)
3. Clique em **"Iniciar"**

A exploracao comeca a rodar em background.

### 3. Visualizar Arvore

```
URL: /experiments/{experiment_id}/explorations/{exploration_id}
```

A pagina exibe:
- **Arvore hierarquica** com nos coloridos por status
- **Indicadores de progresso** (iteracao atual, nos criados, melhor taxa)
- **Painel de detalhes** ao clicar em um no

### 4. Interpretar Cores dos Nos

| Cor | Status | Significado |
|-----|--------|-------------|
| 🟢 Verde | Winner | Atingiu a meta |
| 🔵 Azul | Active | Na fronteira de expansao |
| ⚪ Cinza | Dominated | Descartado (superado por outro) |
| 🔴 Vermelho | Failed | Falha na expansao |

### 5. Inspecionar Detalhes

Clique em qualquer no para ver:
- **Acao aplicada** e categoria
- **Rationale** (justificativa da mudanca)
- **Parametros do scorecard** (complexity, effort, risk, time)
- **Resultados** (success_rate, fail_rate, did_not_try_rate)
- **Delta** em relacao ao no pai

### 6. Ver Caminho Vencedor

Quando a exploracao atinge a meta:
1. O caminho do raiz ate o vencedor fica destacado
2. Clique em **"Ver Caminho Vencedor"** para lista sequencial
3. Cada passo mostra a acao e delta de success_rate

## Navegacao

```
┌─────────────────────────────────────────────────────┐
│  Home (/)                                           │
│    └── Experimentos                                 │
│         └── Detalhe (/experiments/:id)              │
│              ├── Entrevistas                        │
│              ├── Analise                            │
│              └── Exploracoes ← NOVO                 │
│                   └── Detalhe (/experiments/:id/    │
│                        explorations/:explorationId) │
└─────────────────────────────────────────────────────┘
```

## Exemplos de Uso

### Cenario 1: Melhorar Taxa de Sucesso de 25% para 40%

1. Acessar experimento com analise baseline mostrando 25%
2. Clicar "Iniciar Exploracao"
3. Definir meta: 40%
4. Aguardar exploracao concluir
5. Se status = "goal_achieved", ver caminho vencedor
6. Implementar acoes sugeridas no produto real

### Cenario 2: Explorar Alternativas

1. Iniciar exploracao com beam_width=5 (mais cenarios)
2. Mesmo se nao atingir meta, explorar nos "active"
3. Comparar parametros de scorecard entre nos
4. Identificar trade-offs (ex: menos complexity mas mais effort)

### Cenario 3: Consultar Catalogo

1. Clicar em "Ver Catalogo de Acoes"
2. Navegar categorias:
   - UX / Interface
   - Onboarding / Educacao
   - Fluxo / Processo
   - Comunicacao / Feedback
   - Operacional / Feature Control
3. Ver exemplos de acoes e impactos tipicos

## Troubleshooting

| Problema | Causa Provavel | Solucao |
|----------|----------------|---------|
| Botao "Iniciar" desabilitado | Sem analise baseline | Execute analise primeiro |
| Exploracao parou sem atingir meta | Limite de profundidade/custo | Aumente max_depth ou max_llm_calls |
| Todos nos "dominated" | Cenarios nao melhoram | Revise scorecard inicial |
| Arvore muito grande | beam_width alto | Reduza beam_width |

## API Reference

| Acao | Endpoint |
|------|----------|
| Criar exploracao | `POST /api/explorations` |
| Ver status | `GET /api/explorations/{id}` |
| Ver arvore | `GET /api/explorations/{id}/tree` |
| Ver caminho vencedor | `GET /api/explorations/{id}/winning-path` |
| Catalogo de acoes | `GET /api/explorations/catalog/actions` |
