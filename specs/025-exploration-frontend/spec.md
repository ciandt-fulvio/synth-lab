# Feature Specification: Frontend para Exploracao de Cenarios com Visualizacao de Arvore

**Feature Branch**: `025-exploration-frontend`
**Created**: 2025-12-31
**Status**: Draft
**Input**: User description: "Criar tela frontend para exploração de cenários com visualização de árvore"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Iniciar Nova Exploracao (Priority: P1)

O product manager acessa a pagina de um experimento que ja possui analise baseline executada e deseja iniciar uma exploracao automatizada de cenarios. Ele define a meta de success_rate desejada e configuracoes opcionais (beam_width, max_depth) e inicia a exploracao.

**Why this priority**: Esta e a entrada do fluxo - sem iniciar uma exploracao, nao ha arvore para visualizar. E o primeiro ponto de interacao do usuario com a feature.

**Independent Test**: Pode ser testado acessando um experimento com analise baseline, clicando em "Iniciar Exploracao", preenchendo meta de 40% e verificando que a exploracao e criada e aparece na lista.

**Acceptance Scenarios**:

1. **Given** experimento com analise baseline executada, **When** PM acessa pagina do experimento, **Then** ve botao "Iniciar Exploracao" habilitado
2. **Given** experimento sem analise baseline, **When** PM acessa pagina, **Then** botao "Iniciar Exploracao" esta desabilitado com tooltip explicativo
3. **Given** formulario de nova exploracao, **When** PM define meta e configuracoes, **Then** sistema valida valores e habilita botao "Iniciar"
4. **Given** exploracao iniciada, **When** sistema processa, **Then** PM ve indicador de progresso e status da exploracao

---

### User Story 2 - Visualizar Arvore de Cenarios (Priority: P1)

O product manager quer visualizar a arvore completa de cenarios explorados para entender os caminhos tentados, quais funcionaram e quais foram descartados. A arvore mostra a hierarquia de nos com cores indicando status.

**Why this priority**: A visualizacao da arvore e o core value desta feature - transforma dados de exploracao em insights visuais navegaveis.

**Independent Test**: Pode ser testado acessando uma exploracao concluida e verificando que a arvore renderiza todos os nos com cores corretas por status e conexoes pai-filho visiveis.

**Acceptance Scenarios**:

1. **Given** exploracao com arvore de cenarios, **When** PM abre visualizacao, **Then** ve arvore hierarquica com no raiz no topo
2. **Given** arvore renderizada, **When** PM observa nos, **Then** cada no tem cor indicando status (verde=winner, azul=active, cinza=dominated, vermelho=failed)
3. **Given** arvore com multiplos niveis, **When** PM navega, **Then** consegue expandir/colapsar ramos da arvore
4. **Given** arvore grande, **When** PM usa zoom/pan, **Then** consegue navegar pela arvore completa

---

### User Story 3 - Inspecionar Detalhes de um No (Priority: P1)

O product manager clica em um no da arvore para ver detalhes: acao aplicada, parametros do scorecard, resultados da simulacao e rationale da mudanca.

**Why this priority**: Sem ver detalhes dos nos, o PM nao consegue entender o que cada cenario representa e por que foi gerado.

**Independent Test**: Pode ser testado clicando em um no da arvore e verificando que painel lateral exibe todos os campos: acao, categoria, rationale, parametros e resultados.

**Acceptance Scenarios**:

1. **Given** arvore renderizada, **When** PM clica em um no, **Then** painel de detalhes abre mostrando informacoes do no
2. **Given** no selecionado, **When** PM ve detalhes, **Then** exibe: acao aplicada, categoria, rationale, parametros do scorecard
3. **Given** no com simulacao, **When** PM ve detalhes, **Then** exibe: success_rate, fail_rate, did_not_try_rate com formatacao percentual
4. **Given** no raiz, **When** PM ve detalhes, **Then** exibe "Cenario Inicial (Baseline)" sem acao aplicada

---

### User Story 4 - Visualizar Caminho Vencedor (Priority: P2)

Quando a exploracao atinge a meta, o PM quer ver o caminho vencedor destacado - a sequencia de acoes do cenario inicial ate o cenario que atingiu a meta.

**Why this priority**: O caminho vencedor e o resultado principal de uma exploracao bem-sucedida, mas depende da arvore estar visualizada primeiro.

**Independent Test**: Pode ser testado em exploracao com status "goal_achieved" e verificando que o caminho do raiz ate o no vencedor esta destacado visualmente e listado sequencialmente.

**Acceptance Scenarios**:

1. **Given** exploracao com status "goal_achieved", **When** PM visualiza arvore, **Then** caminho vencedor esta destacado com cor/espessura diferente
2. **Given** caminho vencedor destacado, **When** PM clica em "Ver Caminho", **Then** painel lista sequencia de acoes com delta de success_rate por passo
3. **Given** lista de passos do caminho, **When** PM analisa, **Then** ve melhoria total (success_rate inicial para final) e numero de iteracoes
4. **Given** caminho vencedor, **When** PM clica em um passo da lista, **Then** no correspondente e selecionado na arvore

---

### User Story 5 - Acompanhar Progresso da Exploracao (Priority: P2)

Enquanto a exploracao esta em execucao, o PM quer acompanhar o progresso em tempo real: iteracao atual, nos criados, melhor success_rate encontrado.

**Why this priority**: Feedback de progresso melhora a experiencia do usuario, mas a exploracao pode funcionar sem isso (usuario pode atualizar pagina).

**Independent Test**: Pode ser testado iniciando exploracao e verificando que indicadores de progresso atualizam a cada iteracao sem precisar recarregar a pagina.

**Acceptance Scenarios**:

1. **Given** exploracao em execucao, **When** PM observa tela, **Then** ve indicadores: iteracao atual/max, nos criados, melhor success_rate
2. **Given** exploracao em progresso, **When** iteracao completa, **Then** indicadores atualizam automaticamente
3. **Given** exploracao em execucao, **When** PM observa arvore, **Then** novos nos aparecem conforme sao criados
4. **Given** exploracao que termina, **When** status muda, **Then** interface indica conclusao e mostra resultado final

---

### User Story 6 - Listar Exploracoes do Experimento (Priority: P2)

O PM quer ver historico de exploracoes executadas para um experimento, podendo acessar exploracoes anteriores e comparar resultados.

**Why this priority**: O historico permite analise comparativa, mas cada exploracao pode ser acessada individualmente sem lista.

**Independent Test**: Pode ser testado acessando experimento com multiplas exploracoes e verificando que lista mostra todas com status, meta e resultado.

**Acceptance Scenarios**:

1. **Given** experimento com exploracoes, **When** PM acessa aba de exploracoes, **Then** ve lista com todas exploracoes ordenadas por data
2. **Given** lista de exploracoes, **When** PM observa item, **Then** ve: data, meta, status, melhor success_rate, total de nos
3. **Given** lista de exploracoes, **When** PM clica em uma, **Then** navega para visualizacao da arvore dessa exploracao
4. **Given** exploracao em execucao, **When** PM ve lista, **Then** item mostra indicador de "em progresso"

---

### User Story 7 - Consultar Catalogo de Acoes (Priority: P3)

O PM quer consultar o catalogo de categorias de acoes disponiveis para entender que tipos de melhorias o sistema pode propor.

**Why this priority**: O catalogo e informativo e ajuda o PM a entender as propostas, mas nao e essencial para usar a exploracao.

**Independent Test**: Pode ser testado acessando catalogo e verificando que lista 5 categorias com exemplos e faixas de impacto.

**Acceptance Scenarios**:

1. **Given** tela de exploracao, **When** PM clica em "Ver Catalogo de Acoes", **Then** modal/drawer abre com lista de categorias
2. **Given** catalogo aberto, **When** PM ve categoria, **Then** exibe: nome, descricao, exemplos de acoes
3. **Given** categoria no catalogo, **When** PM expande, **Then** ve faixas de impacto tipicas por parametro
4. **Given** catalogo, **When** PM busca por termo, **Then** filtra categorias/acoes que contem o termo

---

### Edge Cases

- O que acontece quando experimento nao tem analise baseline? Botao "Iniciar Exploracao" desabilitado com mensagem "Execute uma analise primeiro"
- O que acontece quando exploracao falha completamente? Interface mostra status de erro com mensagem explicativa
- O que acontece quando arvore tem muitos nos (>100)? Sistema usa virtualizacao para performance e oferece filtros
- O que acontece quando usuario perde conexao durante exploracao? Ao reconectar, busca estado atual da exploracao
- O que acontece quando duas exploracoes rodam simultaneamente? Sistema permite, cada uma tem sua arvore independente
- O que acontece quando no tem rationale muito longo? Texto e truncado com opcao "ver mais"

## Requirements *(mandatory)*

### Functional Requirements

**Iniciar Exploracao**
- **FR-001**: Interface DEVE exibir botao "Iniciar Exploracao" na pagina do experimento quando analise baseline existe
- **FR-002**: Interface DEVE desabilitar botao quando experimento nao tem analise baseline, com tooltip explicativo
- **FR-003**: Formulario DEVE permitir definir: meta de success_rate (0-100%), beam_width (1-10), max_depth (1-10)
- **FR-004**: Formulario DEVE ter valores default: meta=40%, beam_width=3, max_depth=5
- **FR-005**: Interface DEVE validar campos antes de permitir envio (meta entre 0-100%, beam_width e max_depth >= 1)

**Visualizacao da Arvore**
- **FR-006**: Interface DEVE renderizar arvore hierarquica com no raiz no topo e filhos abaixo
- **FR-007**: Interface DEVE colorir nos por status: verde (winner), azul (active), cinza (dominated), vermelho (expansion_failed)
- **FR-008**: Interface DEVE desenhar conexoes (arestas) entre nos pai e filhos
- **FR-009**: Interface DEVE permitir expandir/colapsar ramos da arvore
- **FR-010**: Interface DEVE suportar zoom (scroll/pinch) e pan (arrastar) para navegar em arvores grandes
- **FR-011**: Interface DEVE exibir label resumido em cada no (success_rate e acao truncada)

**Detalhes do No**
- **FR-012**: Interface DEVE abrir painel de detalhes ao clicar em um no
- **FR-013**: Painel DEVE exibir: acao aplicada, categoria, rationale
- **FR-014**: Painel DEVE exibir parametros do scorecard: complexity, initial_effort, perceived_risk, time_to_value
- **FR-015**: Painel DEVE exibir resultados: success_rate, fail_rate, did_not_try_rate formatados como percentual
- **FR-016**: Painel DEVE indicar delta de cada metrica em relacao ao no pai (quando aplicavel)

**Caminho Vencedor**
- **FR-017**: Interface DEVE destacar visualmente o caminho vencedor quando exploracao atinge meta
- **FR-018**: Interface DEVE oferecer botao "Ver Caminho Vencedor" que lista passos sequencialmente
- **FR-019**: Lista de passos DEVE mostrar: numero do passo, acao, delta_success_rate, success_rate resultante
- **FR-020**: Clicar em passo da lista DEVE selecionar no correspondente na arvore

**Progresso e Status**
- **FR-021**: Interface DEVE exibir status atual da exploracao (running, goal_achieved, depth_limit_reached, etc.)
- **FR-022**: Interface DEVE exibir metricas de progresso: iteracao atual, total de nos, melhor success_rate
- **FR-023**: Interface DEVE atualizar automaticamente durante exploracao em execucao (polling ou websocket)
- **FR-024**: Interface DEVE notificar usuario quando exploracao termina (toast/badge)

**Lista de Exploracoes**
- **FR-025**: Interface DEVE listar exploracoes do experimento em aba dedicada
- **FR-026**: Lista DEVE mostrar: data, meta, status, melhor success_rate, total de nos
- **FR-027**: Lista DEVE ordenar por data de criacao (mais recente primeiro)
- **FR-028**: Clicar em item da lista DEVE navegar para visualizacao da arvore

**Catalogo de Acoes**
- **FR-029**: Interface DEVE permitir acessar catalogo de acoes via botao/link
- **FR-030**: Catalogo DEVE listar categorias com nome, descricao e exemplos
- **FR-031**: Catalogo DEVE mostrar faixas de impacto tipicas por parametro do scorecard

### Key Entities

- **ExplorationView**: Representacao visual de uma exploracao contendo:
  - Metadados: id, experiment_id, status, meta, configuracao
  - Metricas: current_depth, total_nodes, best_success_rate
  - Timestamps: started_at, completed_at

- **TreeNode**: No visual na arvore contendo:
  - Identificacao: id, parent_id, depth
  - Conteudo resumido: success_rate, acao truncada
  - Status visual: cor baseada em node_status
  - Posicao: x, y para layout da arvore

- **NodeDetails**: Detalhes completos de um no contendo:
  - Acao: action_applied, category, rationale
  - Parametros: complexity, initial_effort, perceived_risk, time_to_value
  - Resultados: success_rate, fail_rate, did_not_try_rate
  - Deltas: comparacao com no pai

- **WinningPath**: Caminho vencedor contendo:
  - Lista de passos com acao e metricas
  - Melhoria total (delta success_rate inicio para fim)
  - Numero de iteracoes

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Usuario consegue iniciar nova exploracao em menos de 30 segundos apos acessar experimento
- **SC-002**: Arvore de exploracao renderiza em menos de 2 segundos para exploracoes com ate 50 nos
- **SC-003**: 95% dos usuarios conseguem identificar o caminho vencedor na primeira visualizacao
- **SC-004**: Usuario consegue acessar detalhes de qualquer no em no maximo 2 cliques
- **SC-005**: Interface atualiza status de exploracao em execucao em intervalos de no maximo 5 segundos
- **SC-006**: Usuario consegue navegar em arvore com 100 nos sem degradacao perceptivel de performance
- **SC-007**: 90% dos usuarios conseguem entender a sequencia de acoes que levou ao resultado vencedor

## Assumptions

- Backend da feature 024 (LLM-Scenario-Exploration) esta implementado e disponivel via API REST
- Endpoints disponiveis: POST /api/explorations, GET /api/explorations/{id}, GET /api/explorations/{id}/tree, GET /api/explorations/{id}/winning-path, GET /api/explorations/catalog/actions
- Frontend segue padroes existentes do projeto: React 18, TypeScript, TanStack Query, shadcn/ui
- Visualizacao de arvore pode usar biblioteca existente ou componente custom com canvas/SVG
- Atualizacao em tempo real pode ser implementada via polling (intervalo de 3-5 segundos)
- Design visual segue sistema de design existente do SynthLab
- Pagina de exploracao sera acessivel a partir da pagina de detalhes do experimento
