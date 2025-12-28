# Feature Specification: Refatoração do Modelo Experimento-Análise-Entrevista

**Feature Branch**: `019-experiment-refactor`
**Created**: 2025-12-27
**Status**: Draft
**Input**: User description: "existe uma confusao entre experimento - simulacao e entrevista. a coisa deve ser assim: o experimento deve ter nome, descricao e dimensoes do scorecard (como hj esta na simulacao). Inclusive o servico de 'Estimar com IA' que usa a descricao. Cada experimento tem apenas 1 simulacao (que deve ser chamada de chamada de analise quantitativa). Cada experimento pode ter N entrevistas; que pode ser sugeridas por uma das analises quant, mas que o usuário pode resolver não seguir e pedir apenas o disparo de mais um conjunto de entrevistas. inclusive, a pagina de entrevistas tinha (quando a url era http://localhost:8080/interviews/{id}) uma parte streaming SSE que parece não existir mais e devo voltar"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Criar Experimento Completo com Scorecard (Priority: P1)

O usuário deseja criar um novo experimento de pesquisa. Ao criar o experimento, ele define o nome, descrição da feature/hipótese, e as dimensões do scorecard diretamente no experimento. As dimensões do scorecard incluem métricas de adoção, experiência e capacidades necessárias.

**Why this priority**: É a base de todo o sistema. Sem um experimento com scorecard embutido, não é possível rodar análises quantitativas nem entrevistas. Move o scorecard para ser parte integral do experimento (não mais uma entidade separada associada a simulação).

**Independent Test**: Pode ser testado criando um experimento novo, verificando que o scorecard é salvo junto, e que a estimativa com IA funciona para preencher as dimensões automaticamente.

**Acceptance Scenarios**:

1. **Given** o usuário está na página de criação de experimento, **When** preenche nome, descrição e clica em "Estimar com IA", **Then** as dimensões do scorecard são preenchidas automaticamente baseadas na descrição.
2. **Given** o usuário tem as dimensões do scorecard preenchidas (manual ou via IA), **When** salva o experimento, **Then** o experimento é criado com o scorecard embutido e aparece na lista de experimentos.
3. **Given** o usuário acessa um experimento existente, **When** visualiza os detalhes, **Then** vê as dimensões do scorecard no próprio experimento (não em entidade separada).

---

### User Story 2 - Executar Análise Quantitativa Única (Priority: P2)

Cada experimento tem uma única análise quantitativa (anteriormente chamada de "simulação"). O usuário pode executar ou re-executar essa análise para obter métricas agregadas de adoção baseadas nas dimensões do scorecard do experimento.

**Why this priority**: A análise quantitativa é o primeiro passo para entender o impacto potencial da feature. Simplifica o modelo ao ter 1:1 entre experimento e análise quantitativa.

**Independent Test**: Pode ser testado executando a análise quantitativa de um experimento e verificando que os resultados (taxas de adoção, falha, não-tentativa) são gerados e persistidos.

**Acceptance Scenarios**:

1. **Given** o usuário tem um experimento com scorecard preenchido, **When** clica em "Executar Análise Quantitativa", **Then** a análise é executada e os resultados aparecem na página do experimento.
2. **Given** uma análise quantitativa já foi executada, **When** o usuário clica em "Re-executar Análise", **Then** uma nova execução é iniciada, substituindo os resultados anteriores.
3. **Given** a análise está em execução, **When** o usuário visualiza a página do experimento, **Then** vê o status de progresso da análise.

---

### User Story 3 - Disparar Entrevistas a partir de Sugestões da Análise (Priority: P2)

Após a análise quantitativa identificar regiões de alto risco (clusters de synths com alta taxa de falha), o sistema sugere entrevistas com synths representativos dessas regiões. O usuário pode aceitar as sugestões ou ignorá-las.

**Why this priority**: Conecta a análise quantitativa com a pesquisa qualitativa, permitindo investigar por que certos perfis têm dificuldade com a feature.

**Independent Test**: Pode ser testado executando uma análise quantitativa que identifica regiões de alto risco, verificando que sugestões de entrevista aparecem, e disparando entrevistas a partir dessas sugestões.

**Acceptance Scenarios**:

1. **Given** uma análise quantitativa foi completada e identificou regiões de alto risco, **When** o usuário visualiza os resultados, **Then** vê sugestões de entrevistas com synths representativos dessas regiões.
2. **Given** sugestões de entrevista estão disponíveis, **When** o usuário aceita uma sugestão, **Then** uma nova rodada de entrevistas é criada com os synths sugeridos.
3. **Given** sugestões de entrevista estão disponíveis, **When** o usuário ignora e cria uma entrevista manual, **Then** pode selecionar seus próprios critérios de synths.

---

### User Story 4 - Disparar Múltiplas Rodadas de Entrevistas (Priority: P2)

O usuário pode disparar quantas rodadas de entrevistas quiser para um experimento. Cada rodada pode ter diferentes tópicos, contextos ou grupos de synths. O histórico de todas as rodadas fica associado ao experimento.

**Why this priority**: Permite exploração qualitativa iterativa sem limitação de uma única entrevista por experimento.

**Independent Test**: Pode ser testado criando múltiplas rodadas de entrevista para o mesmo experimento e verificando que todas aparecem listadas na página do experimento.

**Acceptance Scenarios**:

1. **Given** um experimento tem 2 rodadas de entrevistas já concluídas, **When** o usuário clica em "Nova Entrevista", **Then** pode criar uma terceira rodada independente.
2. **Given** um experimento tem múltiplas rodadas, **When** o usuário visualiza o experimento, **Then** vê todas as rodadas listadas com seus respectivos status e resumos.
3. **Given** uma rodada de entrevista está em andamento, **When** o usuário acessa a página da entrevista, **Then** vê o streaming SSE das conversas em tempo real.

---

### User Story 5 - Acompanhar Entrevistas em Tempo Real via SSE (Priority: P3)

Quando entrevistas estão sendo executadas, o usuário pode acompanhar as conversas em tempo real através de streaming SSE. Cada mensagem do entrevistador e do synth aparece conforme é gerada.

**Why this priority**: Melhora a experiência do usuário durante entrevistas longas, permitindo acompanhamento em tempo real sem necessidade de refresh.

**Independent Test**: Pode ser testado disparando uma entrevista e verificando que as mensagens aparecem em tempo real na interface sem refresh manual.

**Acceptance Scenarios**:

1. **Given** uma entrevista está em execução, **When** o usuário acessa a página da entrevista, **Then** vê as mensagens aparecendo em tempo real via SSE.
2. **Given** uma entrevista foi completada e o usuário acessa depois, **When** a página carrega, **Then** vê todas as mensagens já transcritas (replay do histórico).
3. **Given** múltiplos synths estão sendo entrevistados, **When** o usuário visualiza, **Then** pode ver o progresso de cada entrevista simultaneamente em um grid.

---

### Edge Cases

- O que acontece quando a análise quantitativa é re-executada enquanto entrevistas estão em andamento? As entrevistas continuam normalmente; os resultados da nova análise não afetam entrevistas em andamento.
- Como o sistema lida quando o usuário tenta criar uma entrevista sem ter completado o scorecard do experimento? Exibe mensagem orientando a completar o scorecard primeiro.
- O que acontece se a conexão SSE é perdida durante uma entrevista? O cliente reconecta automaticamente e recebe replay das mensagens perdidas.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sistema DEVE permitir criar experimentos com nome, descrição e dimensões do scorecard em uma única operação.
- **FR-002**: Sistema DEVE estimar dimensões do scorecard automaticamente usando IA baseada na descrição do experimento.
- **FR-003**: Sistema DEVE suportar exatamente uma análise quantitativa (anteriormente "simulação") por experimento.
- **FR-004**: Sistema DEVE permitir re-executar a análise quantitativa, substituindo resultados anteriores.
- **FR-005**: Sistema DEVE suportar múltiplas rodadas de entrevistas por experimento (relação 1:N).
- **FR-006**: Sistema DEVE sugerir entrevistas baseadas em regiões de alto risco identificadas pela análise quantitativa.
- **FR-007**: Sistema DEVE permitir ao usuário ignorar sugestões e criar entrevistas com critérios próprios.
- **FR-008**: Sistema DEVE transmitir mensagens de entrevista em tempo real via SSE durante execução.
- **FR-009**: Sistema DEVE suportar replay de mensagens históricas via SSE quando usuário acessa entrevista já em andamento.
- **FR-010**: Sistema DEVE persistir todas as rodadas de entrevista associadas ao experimento.
- **FR-011**: Sistema DEVE exibir grid de entrevistas simultâneas quando múltiplos synths estão sendo entrevistados.
- **FR-012**: Sistema DEVE renomear "Simulação" para "Análise Quantitativa" em toda interface.

### Key Entities

- **Experimento**: Hub central contendo nome, descrição/hipótese, dimensões do scorecard (métricas de adoção, experiência, capacidades). Possui uma análise quantitativa e N rodadas de entrevista.
- **Análise Quantitativa**: Execução única por experimento que calcula taxas de adoção agregadas baseadas nas dimensões do scorecard. Inclui configuração (n_synths, n_executions, sigma, seed) e resultados (taxas, insights, clustering).
- **Rodada de Entrevista**: Conjunto de entrevistas com synths selecionados. Cada rodada tem tópico, contexto, lista de synths, transcrições e pode gerar resumo e PR-FAQ.
- **Sugestão de Entrevista**: Recomendação gerada pela análise quantitativa para investigar regiões de alto risco, com synths representativos sugeridos.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Usuários podem criar experimento completo (com scorecard) em menos de 3 minutos.
- **SC-002**: Estimativa de scorecard via IA retorna resultados em menos de 10 segundos.
- **SC-003**: Análise quantitativa completa em menos de 2 minutos para configuração padrão (500 synths).
- **SC-004**: SSE transmite mensagens de entrevista com latência máxima de 2 segundos após geração.
- **SC-005**: Sistema suporta até 50 synths sendo entrevistados simultaneamente em uma rodada.
- **SC-006**: 95% dos usuários conseguem disparar nova rodada de entrevista na primeira tentativa.
- **SC-007**: Todas as rodadas de entrevista de um experimento são visíveis e acessíveis na página do experimento.

## Assumptions

- O scorecard atual associado a simulações será migrado para ficar embutido no experimento.
- A URL de entrevistas individuais `/interviews/{id}` será redirecionada para `/experiments/{expId}/interviews/{id}`.
- O streaming SSE já existe no backend (`/research/{exec_id}/stream`) e será mantido; o problema é que o frontend pode não estar conectando corretamente.
- A relação 1:1 entre experimento e análise quantitativa simplifica o modelo - não haverá mais múltiplas simulações por experimento.
- Experimentos existentes com múltiplas simulações terão apenas a mais recente mantida como "análise quantitativa"; as demais ficam acessíveis apenas como histórico.
