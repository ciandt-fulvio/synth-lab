# Research: Frontend para Exploracao de Cenarios

**Feature**: 025-exploration-frontend
**Date**: 2025-12-31

## Decisoes Tecnicas

### 1. Biblioteca de Visualizacao de Arvore

**Decisao**: `react-d3-tree` v3.6.6

**Rationale**:
- Suporte nativo a zoom/pan (requisitos FR-010)
- Nodes colapsaveis (FR-009)
- Customizacao de nodes via `renderCustomNodeElement`
- Layout hierarquico vertical (raiz no topo - FR-006)
- Tipagem TypeScript incluida
- Manutencao ativa (ultima versao dez/2024)
- ~200k downloads/semana no npm

**Alternativas Consideradas**:

| Biblioteca | Pros | Cons | Por que rejeitada |
|------------|------|------|-------------------|
| React Flow | Excelente para diagramas de fluxo | Mais complexo, focado em edges editaveis | Over-engineering para arvore simples |
| React Arborist | Otimo para file explorers | Nao tem zoom/pan nativo | Falta recursos visuais chave |
| MUI Tree View | Familiar para quem usa MUI | Nao tem zoom/pan, estilo diferente | Inconsistente com shadcn/ui |
| D3 puro | Maximo controle | Muito codigo boilerplate | Complexidade desnecessaria |

**Referencias**:
- [react-d3-tree GitHub](https://github.com/bkrem/react-d3-tree)
- [react-d3-tree npm](https://www.npmjs.com/package/react-d3-tree)

---

### 2. Estrategia de Atualizacao em Tempo Real

**Decisao**: Polling com React Query (refetchInterval)

**Rationale**:
- Simplicidade de implementacao
- Consistente com padrao existente no projeto (use-sse.ts ja existe mas polling e mais simples)
- React Query ja gerencia cache e deduplicacao
- Intervalo de 3-5 segundos atende SC-005

**Implementacao**:
```typescript
useQuery({
  queryKey: queryKeys.explorationDetail(id),
  queryFn: () => getExploration(id),
  refetchInterval: (data) =>
    data?.status === 'running' ? 3000 : false, // 3s apenas se running
  refetchOnWindowFocus: true,
});
```

**Alternativas Consideradas**:

| Metodo | Pros | Cons | Por que rejeitada |
|--------|------|------|-------------------|
| WebSocket | Tempo real verdadeiro | Complexidade de setup, overkill | Backend nao tem WS implementado |
| SSE (Server-Sent Events) | Unidirecional, simples | Requer mudanca no backend | Escopo adicional |
| Long Polling | Menos requests | Mais complexo que polling simples | Beneficio marginal |

---

### 3. Layout do Painel de Detalhes

**Decisao**: Painel lateral direito (Sheet/Drawer)

**Rationale**:
- Padrao consistente com outras areas do app (ex: SynthChat usa drawer)
- Permite ver arvore e detalhes simultaneamente
- Componente Sheet ja disponivel via shadcn/ui
- Responsivo em telas menores

**Implementacao**:
- Desktop: Sheet lateral direito (width: 400px)
- Mobile: Sheet bottom drawer

---

### 4. Coloracao de Nos por Status

**Decisao**: Usar classes CSS customizadas com cores do design system

| Status | Cor | Classe Tailwind | Hex |
|--------|-----|-----------------|-----|
| winner | Verde | `bg-green-500` | #22c55e |
| active | Azul | `bg-blue-500` | #3b82f6 |
| dominated | Cinza | `bg-slate-400` | #94a3b8 |
| expansion_failed | Vermelho | `bg-red-500` | #ef4444 |

**Rationale**:
- Cores semanticas consistentes com o design system existente
- Verde para sucesso, vermelho para falha sao convencoes universais
- Azul para ativo indica "em progresso"
- Cinza para dominado indica "descartado"

---

### 5. Estrutura da Pagina de Exploracao

**Decisao**: Pagina separada acessivel via rota `/experiments/:id/explorations/:explorationId`

**Rationale**:
- Separacao clara de contexto
- URL compartilhavel para exploracao especifica
- Nao sobrecarrega a pagina de experimento existente

**Fluxo de Navegacao**:
```
ExperimentDetail (/experiments/:id)
  └── Aba "Exploracoes" (lista)
       └── Click em exploracao
            └── ExplorationDetail (/experiments/:id/explorations/:explorationId)
```

---

### 6. Integracao com Pagina de Experimento

**Decisao**: Adicionar aba/secao "Exploracoes" na pagina ExperimentDetail existente

**Rationale**:
- Consistente com estrutura existente (Entrevistas, Analise)
- Permite iniciar exploracao a partir do experimento
- Mostra lista de exploracoes anteriores

**Implementacao**:
- Adicionar componente `ExplorationSection` em ExperimentDetail
- Botao "Iniciar Exploracao" quando analise baseline existe
- Lista de exploracoes com status e link para detalhe

---

## Dependencias a Adicionar

```json
{
  "dependencies": {
    "react-d3-tree": "^3.6.6"
  }
}
```

**Instalacao**:
```bash
cd frontend && npm install react-d3-tree
```

---

## APIs Backend Disponiveis

Todas implementadas em spec 024:

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| `/api/explorations` | POST | Criar nova exploracao |
| `/api/explorations/{id}` | GET | Obter exploracao |
| `/api/explorations/{id}/run` | POST | Executar exploracao em background |
| `/api/explorations/{id}/tree` | GET | Arvore completa com todos os nos |
| `/api/explorations/{id}/winning-path` | GET | Caminho vencedor (se existir) |
| `/api/explorations/catalog/actions` | GET | Catalogo de acoes |

**Observacao**: Falta endpoint para listar exploracoes por experimento. Sera necessario:
- Adicionar endpoint `GET /api/experiments/{id}/explorations`

---

## Riscos e Mitigacoes

| Risco | Impacto | Mitigacao |
|-------|---------|-----------|
| react-d3-tree nao suporta customizacao necessaria | Alto | Fallback para D3 puro ou React Flow |
| Performance com arvores grandes (>100 nos) | Medio | Virtualizacao ou limit no backend |
| Polling excessivo impacta backend | Baixo | Conditional refetch + debounce |
| Layout quebra em mobile | Medio | Design mobile-first com breakpoints |

---

## Proximos Passos

1. ✅ Validar estrutura de dados da API (schemas ja documentados)
2. ⏳ Criar types TypeScript frontend
3. ⏳ Implementar service API
4. ⏳ Implementar hooks React Query
5. ⏳ Criar componentes de visualizacao
6. ⏳ Integrar com pagina de experimento
