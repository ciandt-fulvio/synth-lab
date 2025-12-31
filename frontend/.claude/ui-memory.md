# UI Memory - SynthLab Frontend

Cache de elementos UI para navegação rápida com Chrome DevTools MCP.
**IMPORTANTE**: Usar este arquivo ANTES de fazer snapshots desnecessários.

## Instruções de Uso

1. **Antes de navegar**: Consulte esta memória para saber quais elementos procurar
2. **Use seletores semânticos**: Busque por texto/label, não por UID (UIDs mudam a cada snapshot)
3. **Um snapshot por página**: Faça snapshot apenas para confirmar estado ou pegar UIDs atuais
4. **Atualize este arquivo**: Se a UI mudar, atualize a memória

---

## Páginas e Elementos

### 1. ExperimentDetail (`/experiments/:id`)

**Estrutura da página:**
```
header: "Detalhe do Experimento"
main:
  - heading: nome do experimento (h2)
  - cards de métricas: Complexidade, Esforço Inicial, Risco Percebido, Tempo p/ Valor
  - seção "Entrevistas" (button expandable)
  - seção "Análise Quantitativa" (heading h3)
    - tabs: Geral, Influência, Segmentos, Especiais
    - botões: Anterior, Próxima
  - seção "Explorações de Cenários" (heading h3, COLLAPSIBLE)
```

**Elementos-chave para Exploração:**

| Elemento | Seletor Semântico | Ação |
|----------|-------------------|------|
| Seção Explorações | `heading "Explorações de Cenários"` | Click para expandir |
| Botão Nova Exploração | `button "Iniciar Exploração"` | Abre dialog |
| Contagem | `StaticText "X exploração(ões)"` | Info |
| Status running | `StaticText "• 1 em execução"` | Info |
| Lista de explorações | `link` com texto "Executando" ou "Concluído" | Navega para detalhe |

**Dialog "Nova Exploração de Cenários":**

| Campo | Seletor | Valor Default |
|-------|---------|---------------|
| Meta Success Rate | `spinbutton` primeiro (ou com valuemax=100) | baseline + 15% |
| Slider Meta | `slider` com valuemax=100 | sincronizado |
| Beam Width | `spinbutton "Beam Width"` | 3 |
| Profundidade | `spinbutton "Profundidade Máxima"` | 5 |
| Cancelar | `button "Cancelar"` | - |
| Confirmar | `button "Iniciar Exploração"` (dentro do dialog) | - |
| Fechar | `button "Close"` | - |

---

### 2. ExplorationDetail (`/experiments/:id/explorations/:explorationId`)

**Estrutura da página:**
```
header: "Exploração de Cenários"
main:
  - status badge: "Executando" | "Concluído" | "Falhou"
  - métricas: Meta, Profundidade, Nós Criados, Chamadas LLM, Melhor Taxa
  - mensagem de progresso: "Explorando cenários..."
  - heading "Árvore de Cenários" (h2)
  - controles de zoom: 4 botões
  - canvas da árvore com nós
  - legenda: Baseline, Vencedor, Ativo, Dominado, Falhou
```

**Elementos-chave:**

| Elemento | Seletor Semântico |
|----------|-------------------|
| Status | `StaticText` primeiro após main ("Executando", "Concluído", etc) |
| Meta | `StaticText "Meta:"` seguido de valor |
| Profundidade | `StaticText "Profundidade"` seguido de "X/Y" |
| Nós | `StaticText "Nós Criados"` seguido de número |
| LLM Calls | `StaticText "Chamadas LLM"` seguido de "X/Y" |
| Melhor Taxa | `StaticText "Melhor Taxa"` seguido de percentual |
| Zoom + | `button "Aumentar zoom"` |
| Zoom - | `button "Diminuir zoom"` |
| Fit | `button "Ajustar à tela"` |
| Reset | `button "Resetar posição"` |
| Nó da árvore | `StaticText` com percentual (ex: "47%") |

---

### 3. Padrões Globais

**Header (todas as páginas):**
```
banner:
  - button (menu hamburguer)
  - link "SynthLab Logo" → home
  - link "SynthLab" → home
  - StaticText "Beta"
  - StaticText com título da página atual
```

**Notificações/Toasts:**
```
region "Notifications alt+T"
  list
    listitem
      button "Close toast"
      StaticText (título)
      StaticText (descrição)
```

**Dialogs:**
```
dialog "Título do Dialog"
  heading (h2)
  StaticText (descrição)
  ... campos ...
  button "Cancelar" | button "Close"
  button "Ação Principal"
```

**Botões desabilitados:**
- Atributo `disableable disabled`
- Tooltip aparece ao hover

---

## Fluxos Comuns

### Criar Nova Exploração

```
1. Navegar para /experiments/{id}
2. Scroll/find heading "Explorações de Cenários"
3. Click no heading (expande seção)
4. Click button "Iniciar Exploração"
5. Fill spinbutton Meta (primeiro spinbutton, ou valuemax=100)
6. Fill spinbutton "Beam Width"
7. Fill spinbutton "Profundidade Máxima"
8. Click button "Iniciar Exploração" (dentro do dialog)
9. Aguardar redirect para /experiments/{id}/explorations/{explorationId}
10. Verificar toast "Exploração iniciada"
```

### Verificar Progresso de Exploração

```
1. Navegar para /experiments/{id}/explorations/{explorationId}
2. Ler StaticText após main para status
3. Ler métricas: Profundidade, Nós, LLM Calls, Melhor Taxa
4. Se status = "Executando", aguardar e refresh
```

### Deletar Exploração

```
1. Na página ExperimentDetail, expandir seção Explorações
2. Click button "Deletar" (ainda não implementado individualmente)
```

---

## Última Atualização

- **Data**: 2024-12-31
- **Versão Frontend**: após implementação spec 025-exploration-frontend
- **Páginas documentadas**: ExperimentDetail, ExplorationDetail
