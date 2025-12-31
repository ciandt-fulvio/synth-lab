# Feature Specification: Simulation-Driven Scenario Exploration (LLM-Assisted)

**Feature Branch**: `024-llm-scenario-exploration`
**Created**: 2025-12-31
**Status**: Draft
**Input**: FEAT 024 — Sistema de exploracao de cenarios de produto via simulacoes iterativas com propostas de mudanca geradas por LLM, traduzidas em impactos numericos e avaliadas automaticamente

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Iniciar Exploracao de Cenarios (Priority: P1)

O product manager quer iniciar uma exploracao automatizada de cenarios a partir de um experimento que ja possui uma analise (simulacao) executada. O scorecard vem embutido no experimento e o cenario da primeira analise serve como baseline para as demais exploracoes. O PM define uma meta de performance (ex: success_rate >= 40%) que o sistema tentara atingir atraves de simulacoes iterativas.

**Why this priority**: Esta e a entrada principal do fluxo de exploracao. Sem definir o ponto de partida, meta e configuracao de busca (beam width, profundidade maxima), nenhuma exploracao pode ser executada.

**Independent Test**: Pode ser testado criando uma exploracao a partir de um experimento com analise baseline ja executada, meta de 40% success_rate e verificando que a arvore e inicializada com o no raiz contendo os resultados da analise baseline como ponto de partida.

**Acceptance Scenarios**:

1. **Given** experimento com scorecard_data preenchido e analise baseline executada, **When** PM inicia exploracao com meta success_rate >= 0.40, **Then** sistema cria arvore com no raiz usando parametros do scorecard e resultados da analise baseline
2. **Given** exploracao iniciada, **When** simulacao do cenario inicial completa, **Then** no raiz contem success_rate, fail_rate, did_not_try medidos
3. **Given** cenario inicial com success_rate >= meta, **When** exploracao e iniciada, **Then** sistema sinaliza que meta ja foi atingida e encerra exploracao com sucesso
4. **Given** parametros de busca invalidos (beam_width < 1 ou max_depth < 1), **When** PM tenta iniciar, **Then** sistema rejeita com erro claro

---

### User Story 2 - Gerar Propostas de Melhoria via LLM (Priority: P1)

Para cada cenario nao-dominado na fronteira de exploracao, o LLM deve propor ate 2 acoes concretas e incrementais que possam melhorar os resultados, mapeando cada acao para impactos estimados nos parametros do scorecard.

**Why this priority**: A geracao de propostas pelo LLM e o motor principal da exploracao. Sem propostas de melhoria, nao ha como expandir a arvore e buscar cenarios melhores.

**Independent Test**: Pode ser testado enviando um cenario com success_rate de 25% para o LLM e verificando que retorna 1-2 acoes concretas, cada uma com categoria, rationale e impactos estimados em formato estruturado.

**Acceptance Scenarios**:

1. **Given** cenario com resultados abaixo da meta, **When** LLM e consultado, **Then** retorna lista de 1-2 acoes no formato estruturado (action, category, rationale, impacts)
2. **Given** proposta gerada pelo LLM, **When** sistema valida formato, **Then** cada acao tem categoria valida do catalogo (UX/Interface, Onboarding, Fluxo, Comunicacao, Operacional)
3. **Given** proposta com impactos, **When** sistema valida valores, **Then** cada impacto esta no intervalo [-0.10, +0.10] para mudancas incrementais
4. **Given** LLM retorna formato invalido, **When** sistema processa resposta, **Then** descarta proposta e loga erro sem interromper exploracao

---

### User Story 3 - Traduzir Propostas em Novos Cenarios (Priority: P1)

Cada proposta do LLM deve ser traduzida em um novo cenario filho, aplicando os impactos estimados aos parametros do scorecard pai e executando uma nova simulacao para medir os resultados.

**Why this priority**: A traducao de propostas em cenarios simulaveis e o que conecta as ideias do LLM aos resultados quantitativos. Sem isso, propostas ficam apenas conceituais.

**Independent Test**: Pode ser testado aplicando uma proposta com impacts {complexity: -0.02, time_to_value: -0.01} a um scorecard com complexity=0.50 e verificando que o scorecard filho tem complexity=0.48.

**Acceptance Scenarios**:

1. **Given** proposta com impacts, **When** sistema cria cenario filho, **Then** parametros do scorecard sao atualizados conforme impacts (clampados em [0,1])
2. **Given** cenario filho criado, **When** simulacao e executada, **Then** resultados (success_rate, fail_rate, did_not_try) sao registrados no no
3. **Given** cenario filho, **When** sistema registra metadados, **Then** no contem referencia ao pai, acao aplicada, rationale e depth na arvore
4. **Given** proposta que resultaria em parametro fora de [0,1], **When** sistema aplica impacto, **Then** valor e clampado para o limite mais proximo

---

### User Story 4 - Filtrar Cenarios por Dominancia de Pareto (Priority: P1)

Apos cada iteracao de expansao, cenarios que sao dominados por outros devem ser descartados, mantendo apenas a fronteira de Pareto para as proximas iteracoes.

**Why this priority**: O filtro de Pareto e essencial para manter a exploracao focada e evitar explosao combinatoria. Cenarios dominados consomem recursos sem potencial de melhoria.

**Independent Test**: Pode ser testado com 3 cenarios onde A domina B (A >= B em todas dimensoes e A > B em pelo menos uma) e verificando que B e removido da fronteira.

**Acceptance Scenarios**:

1. **Given** dois cenarios A e B onde A tem success_rate maior E complexity/risk menores ou iguais, **When** filtro e aplicado, **Then** B e descartado como dominado
2. **Given** cenarios na fronteira apos filtro, **When** sistema seleciona para proxima iteracao, **Then** apenas cenarios nao-dominados continuam
3. **Given** cenario que nao aumenta success_rate E aumenta complexity ou risk, **When** filtro pragmatico e aplicado, **Then** cenario e descartado imediatamente
4. **Given** fronteira com mais de K cenarios (beam_width), **When** sistema aplica beam search, **Then** mantém apenas os K melhores por criterio (Δsuccess_rate, menor risk, menor distancia do inicial)

---

### User Story 5 - Controlar Profundidade e Custo da Exploracao (Priority: P2)

A exploracao deve respeitar limites de profundidade maxima (numero de iteracoes) e custo (chamadas LLM, tempo), encerrando quando atingir a meta ou esgotar recursos.

**Why this priority**: Controles de custo sao importantes para uso pratico, mas a exploracao pode funcionar com limites default enquanto esse refinamento nao esta pronto.

**Independent Test**: Pode ser testado iniciando exploracao com max_depth=2 e verificando que apos 2 niveis de expansao a exploracao encerra mesmo sem atingir a meta.

**Acceptance Scenarios**:

1. **Given** exploracao com max_depth=3, **When** arvore atinge depth=3 sem atingir meta, **Then** exploracao encerra com status "depth_limit_reached"
2. **Given** exploracao em execucao, **When** algum cenario atinge meta, **Then** exploracao encerra com status "goal_achieved" e identifica cenario vencedor
3. **Given** limite de chamadas LLM configurado, **When** limite e atingido, **Then** exploracao encerra com status "cost_limit_reached"
4. **Given** todos cenarios da fronteira dominados ou descartados, **When** sistema verifica, **Then** exploracao encerra com status "no_viable_paths"

---

### User Story 6 - Visualizar Arvore de Exploracao (Priority: P2)

O product manager quer visualizar a arvore de cenarios explorados, entendendo quais caminhos foram tentados, quais funcionaram e quais foram descartados.

**Why this priority**: A visualizacao transforma dados brutos em insights acionaveis, mas a exploracao pode funcionar via API/logs enquanto a UI nao esta pronta.

**Independent Test**: Pode ser testado exportando arvore de exploracao e verificando que JSON contem todos os nos com seus relacionamentos pai-filho, acoes aplicadas e resultados.

**Acceptance Scenarios**:

1. **Given** exploracao concluida, **When** PM solicita arvore, **Then** recebe estrutura com todos os nos, relacionamentos e resultados
2. **Given** arvore exportada, **When** PM analisa no, **Then** ve parametros do cenario, acao que o gerou, resultados simulados e status (ativo, dominado, vencedor)
3. **Given** arvore com caminho vencedor, **When** PM solicita caminho, **Then** sistema retorna sequencia de acoes do cenario inicial ate o cenario que atingiu a meta
4. **Given** arvore via API, **When** frontend renderiza, **Then** exibe estrutura hierarquica navegavel com cores indicando status de cada no

---

### User Story 7 - Catalogo de Acoes para Ancoragem do LLM (Priority: P2)

O sistema deve fornecer um catalogo de categorias de acoes com exemplos e faixas de impacto tipicos para ancorar as propostas do LLM na realidade do produto.

**Why this priority**: O catalogo melhora a qualidade das propostas do LLM, mas o sistema pode funcionar com prompts bem estruturados enquanto o catalogo formal nao esta persistido.

**Independent Test**: Pode ser testado verificando que catalogo contem pelo menos 5 categorias, cada uma com exemplos de acoes e faixas de impacto tipicas.

**Acceptance Scenarios**:

1. **Given** sistema inicializado, **When** catalogo e consultado, **Then** retorna categorias (UX/Interface, Onboarding, Fluxo, Comunicacao, Operacional) com exemplos
2. **Given** categoria do catalogo, **When** PM visualiza detalhes, **Then** ve lista de acoes exemplo e faixas de impacto tipicas para complexity, risk, time_to_value
3. **Given** proposta do LLM com categoria, **When** sistema valida, **Then** categoria deve existir no catalogo
4. **Given** novo projeto SynthLab, **When** catalogo e carregado, **Then** usa catalogo default mas permite customizacao futura

---

### Edge Cases

- O que acontece quando experimento nao tem scorecard_data? Sistema rejeita exploracao com erro "Experimento sem scorecard preenchido"
- O que acontece quando experimento nao tem analise baseline? Sistema rejeita exploracao com erro "Experimento sem analise baseline executada"
- O que acontece quando cenario inicial ja atinge a meta? Sistema encerra imediatamente com sucesso e retorna cenario inicial como vencedor
- O que acontece quando LLM falha repetidamente? Apos 3 falhas consecutivas, sistema marca cenario como "expansion_failed" e continua com outros
- O que acontece quando todos os cenarios gerados sao dominados? Sistema encerra com status "no_improvement_possible"
- O que acontece quando beam_width e maior que numero de cenarios na fronteira? Sistema usa todos os cenarios disponiveis
- O que acontece quando scorecard tem parametro proximo de 0 e LLM propoe reducao? Valor e clampado em 0.0, nao vai negativo

## Requirements *(mandatory)*

### Functional Requirements

**Exploracao**
- **FR-001**: Sistema DEVE permitir iniciar exploracao a partir de experiment_id (que contem scorecard_data embutido) e meta de performance (success_rate >= X)
- **FR-002**: Sistema DEVE usar a primeira AnalysisRun do experimento como baseline, extraindo scenario_id e resultados iniciais para o no raiz
- **FR-003**: Sistema DEVE rejeitar exploracao se experimento nao tiver scorecard_data preenchido ou nao tiver analise baseline executada
- **FR-004**: Sistema DEVE aceitar configuracao de beam_width (default: 3), max_depth (default: 5) e max_llm_calls (default: 20)
- **FR-005**: Sistema DEVE encerrar exploracao quando meta for atingida, limite de profundidade for atingido, ou nao houver cenarios viaveis

**Geracao de Propostas (LLM)**
- **FR-006**: Sistema DEVE consultar LLM para gerar 1-2 propostas de melhoria para cada cenario na fronteira
- **FR-007**: LLM DEVE receber prompt estruturado com: nome do experimento, hipotese, parametros atuais do scorecard, resultados observados e contexto do catalogo de acoes
- **FR-008**: LLM DEVE retornar propostas no formato JSON: [{action, category, rationale, impacts: {param: delta}}]
- **FR-009**: Sistema DEVE validar que categoria pertence ao catalogo e impactos estao em faixa razoavel [-0.10, +0.10]
- **FR-010**: Sistema DEVE usar tracing Phoenix para todas as chamadas LLM
- **FR-010a**: Sistema DEVE aplicar timeout de 30 segundos para cada chamada LLM individual, marcando como falha apos esse limite

**Traducao de Propostas**
- **FR-011**: Sistema DEVE criar cenario filho aplicando impacts aos parametros do scorecard pai
- **FR-012**: Sistema DEVE clampar valores resultantes no intervalo [0, 1]
- **FR-013**: Sistema DEVE executar simulacao do cenario filho usando MonteCarloEngine existente
- **FR-013a**: Sistema DEVE executar simulacoes de nos irmaos (mesmo nivel/pai) de forma assincrona e paralela para otimizar tempo de exploracao
- **FR-014**: Sistema DEVE registrar no arvore: parent_id, action_applied, rationale, parameters, results, depth

**Filtragem Pareto**
- **FR-015**: Sistema DEVE implementar dominancia de Pareto: A domina B se A >= B em todas dimensoes E A > B em pelo menos uma
- **FR-016**: Vetor de avaliacao DEVE incluir: success_rate (maior melhor), complexity (menor melhor), perceived_risk (menor melhor)
- **FR-017**: Sistema DEVE descartar imediatamente cenarios que nao aumentem success_rate E aumentem complexity ou risk
- **FR-018**: Sistema DEVE aplicar beam search mantendo apenas K melhores cenarios (por Δsuccess_rate, depois menor risk acumulado)

**Arvore de Cenarios**
- **FR-019**: Sistema DEVE persistir arvore de exploracao com todos os nos e relacionamentos
- **FR-020**: Sistema DEVE permitir consultar arvore completa ou caminho ate no especifico
- **FR-021**: Sistema DEVE marcar status de cada no: active, dominated, winner, expansion_failed

**Catalogo de Acoes**
- **FR-022**: Sistema DEVE fornecer catalogo de categorias: UX/Interface, Onboarding/Educacao, Fluxo/Processo, Comunicacao/Feedback, Operacional/Feature Control
- **FR-023**: Cada categoria DEVE ter lista de acoes exemplo e faixas de impacto tipicas
- **FR-024**: Catalogo DEVE ser incluido no prompt do LLM para ancoragem das propostas

### Key Entities

- **Exploration**: Sessao de exploracao contendo:
  - Identificacao: id, experiment_id, baseline_analysis_id, goal (ex: success_rate >= 0.40)
  - Nota: scorecard vem de Experiment.scorecard_data; scenario_id vem de AnalysisRun.scenario_id da analise baseline
  - Configuracao: beam_width, max_depth, max_llm_calls, n_executions por simulacao
  - Estado: status (running, goal_achieved, depth_limit_reached, cost_limit_reached, no_viable_paths), current_depth
  - Timestamps: started_at, completed_at
  - Estatisticas: total_nodes, total_llm_calls, best_success_rate_achieved

- **ScenarioNode**: No na arvore de exploracao contendo:
  - Identificacao: id, exploration_id, parent_id (null para raiz), depth
  - Acao: action_applied (texto), category, rationale (null para raiz)
  - Parametros: scorecard_params {complexity, initial_effort, perceived_risk, time_to_value}
  - Resultados: simulation_results {success_rate, fail_rate, did_not_try_rate}, execution_time
  - Status: node_status (active, dominated, winner, expansion_failed)

- **ActionProposal**: Proposta gerada pelo LLM contendo:
  - action: descricao da acao concreta
  - category: categoria do catalogo
  - rationale: justificativa curta
  - impacts: dicionario {param: delta}

- **ActionCatalog**: Catalogo de categorias contendo:
  - Categorias: UX/Interface, Onboarding, Fluxo, Comunicacao, Operacional
  - Por categoria: lista de acoes exemplo, faixas de impacto tipicas {param: [min_delta, max_delta]}

- **ExplorationResult**: Resultado final da exploracao contendo:
  - status: final status da exploracao
  - winner_node_id: id do no que atingiu a meta (se houver)
  - winning_path: lista ordenada de acoes do inicial ate o vencedor
  - total_iterations: numero de iteracoes executadas
  - frontier_at_end: nos na fronteira quando exploracao encerrou

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Exploracao de 3 iteracoes (depth=3) com beam_width=3 completa em menos de 5 minutos
- **SC-002**: Sistema identifica caminho de melhoria (sequencia de acoes) que aumenta success_rate em pelo menos 5 pontos percentuais em 80% das exploracoes
- **SC-003**: 100% das propostas do LLM seguem formato estruturado e tem categoria valida do catalogo
- **SC-004**: Arvore de exploracao contem historico completo de todos os cenarios tentados com relacionamentos e status
- **SC-005**: PM consegue reconstruir decisoes tomadas navegando do cenario vencedor ate o cenario inicial
- **SC-006**: Sistema reduz numero de propostas descartadas por dominancia em 50% ao longo das iteracoes (LLM aprende do contexto)
- **SC-007**: Re-execucao da mesma exploracao com mesma seed produz arvore identica (reproducibilidade 100%)

## Clarifications

### Session 2025-12-31

- Q: What timeout should apply to individual LLM calls before marking them as failed? → A: 30 seconds (balanced, standard for LLM API calls)
- Q: How should sibling node expansions be executed? → A: Async/parallel execution for all sibling nodes
- Q: Which LLM model should be used initially? → A: gpt-4.1-mini

## Assumptions

- Sistema reutiliza MonteCarloEngine e SimulationService existentes (spec 016)
- Experimento deve ter scorecard_data preenchido (Experiment.scorecard_data != null)
- Experimento deve ter pelo menos uma AnalysisRun executada que serve como baseline
- Scorecard vem de Experiment.scorecard_data (embutido, nao entidade separada)
- Cenario (scenario_id) vem da primeira AnalysisRun do experimento (serve como baseline)
- Resultados iniciais do no raiz vem de AnalysisRun.aggregated_outcomes da analise baseline
- LLM inicial: gpt-4.1-mini com suporte a JSON mode (pode ser atualizado conforme necessidade)
- Chamadas LLM sao rastreadas via Phoenix tracing
- Interface inicial sera via API REST, sem UI grafica no MVP
- Catalogo de acoes e definido em JSON estatico inicialmente
- Beam search usa criterio simples: maior Δsuccess_rate, depois menor risk acumulado
- Sigma padrao de 0.1 e 100 execucoes por simulacao, consistente com spec 016
- Limites default: beam_width=3, max_depth=5, max_llm_calls=20
