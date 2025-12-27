# Feature Specification: Experiment Hub - Reorganização da Navegação

**Feature Branch**: `018-experiment-hub`
**Created**: 2025-12-27
**Status**: Draft
**Input**: Reorganização da arquitetura de navegação do frontend para centralizar o conceito de "Experimento" como container principal de simulações e entrevistas

## Visão Geral

### Problema
A navegação atual do SynthLab apresenta abas separadas para "Entrevistas" e "Synths", mas com a adição do sistema de simulação (feature 016), o fluxo de trabalho do usuário ficou fragmentado. Usuários pensam em termos de "features a testar" ou "experimentos", não em "simulações" ou "entrevistas" como conceitos independentes.

### Solução
Implementar o modelo "Single Hub" onde:
- **Experimento** é o conceito central (feature/hipótese a testar)
- **Simulações** e **Entrevistas** existem apenas dentro de um Experimento
- Navegação simplificada sem abas - a home É a lista de experimentos
- **Synths** movido para menu secundário (não é parte do fluxo principal)

### Fluxo Conceitual
```
Experimento (Feature/Hipótese)
    |
    +-- Simulação(ões) --> Insights/Análises (quantitativo)
    |
    +-- Entrevista(s) --> Summary/PR-FAQ (qualitativo)
```

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Visualizar Lista de Experimentos (Priority: P0)

O usuário acessa o SynthLab e vê imediatamente a lista de todos os seus experimentos, com informações resumidas sobre o estado de cada um.

**Why this priority**: É a página inicial do sistema - sem ela, não há navegação.

**Independent Test**: Pode ser testado acessando a home e verificando que experimentos existentes são listados com contadores corretos.

**Acceptance Scenarios**:

1. **Given** usuário acessa a home, **When** existem experimentos cadastrados, **Then** vê grid de cards com nome, hipótese truncada, contadores (simulações/entrevistas) e data de criação
2. **Given** usuário acessa a home, **When** não existem experimentos, **Then** vê empty state com CTA para criar primeiro experimento
3. **Given** lista de experimentos, **When** usuário clica em um card, **Then** navega para página de detalhe do experimento
4. **Given** lista de experimentos, **When** usuário clica em "+ Novo Experimento", **Then** abre modal/drawer de criação

---

### User Story 2 - Criar Novo Experimento (Priority: P0)

O usuário cria um novo experimento definindo a feature/hipótese que deseja testar.

**Why this priority**: Sem criar experimentos, não há como usar o sistema.

**Campos do Experimento**:
- **Nome** (obrigatório): Nome curto da feature (max 100 chars)
- **Hipótese** (obrigatório): Descrição da hipótese a ser testada (max 500 chars)
- **Descrição** (opcional): Contexto adicional, links, referências (max 2000 chars)

**Independent Test**: Pode ser testado criando um experimento e verificando que aparece na lista.

**Acceptance Scenarios**:

1. **Given** usuário na home, **When** clica em "+ Novo Experimento", **Then** abre modal com formulário
2. **Given** formulário aberto, **When** preenche nome e hipótese e salva, **Then** experimento é criado e salvo no banco
3. **Given** formulário aberto, **When** tenta salvar sem nome ou hipótese, **Then** mostra validação de campos obrigatórios
4. **Given** experimento criado, **When** volta para home, **Then** novo experimento aparece na lista

---

### User Story 3 - Visualizar Detalhe do Experimento (Priority: P0)

O usuário acessa o detalhe de um experimento e vê todas as simulações e entrevistas vinculadas, com ações para criar novas.

**Why this priority**: É a página central de trabalho do usuário.

**Layout da Página**:
```
+--------------------------------------------------+
| <- Experimentos                    [Synths] [Cog]|
+--------------------------------------------------+
| [Nome do Experimento]                   [Editar] |
| Hipótese: "..."                                  |
| Criado: 20 dez 2025                              |
+--------------------------------------------------+
| Simulações                    [+ Nova Simulação] |
| +----------------+ +----------------+            |
| | Cenário Base   | | Cenário Crisis |            |
| | Score: 72/100  | | Score: 65/100  |            |
| | Com insights   | | Processando... |            |
| +----------------+ +----------------+            |
+--------------------------------------------------+
| Entrevistas                  [+ Nova Entrevista] |
| +----------------+                               |
| | Rodada 1       |                               |
| | 15 synths      |                               |
| | Summary pronto |                               |
| +----------------+                               |
+--------------------------------------------------+
```

**Independent Test**: Pode ser testado acessando experimento existente e verificando que simulações e entrevistas vinculadas aparecem.

**Acceptance Scenarios**:

1. **Given** usuário na home, **When** clica em um experimento, **Then** navega para /experiments/:id com detalhes completos
2. **Given** página de detalhe, **When** experimento tem simulações, **Then** mostra cards das simulações com cenário, score e status
3. **Given** página de detalhe, **When** experimento tem entrevistas, **Then** mostra cards das entrevistas com contagem de synths e status de artefatos
4. **Given** página de detalhe, **When** experimento não tem simulações nem entrevistas, **Then** mostra empty states com CTAs
5. **Given** página de detalhe, **When** usuário clica em "Editar", **Then** abre modal para editar nome/hipótese/descrição
6. **Given** página de detalhe, **When** usuário clica em "<- Experimentos", **Then** volta para home

---

### User Story 4 - Criar Simulação Vinculada ao Experimento (Priority: P1)

O usuário cria uma nova simulação diretamente da página do experimento, já vinculada automaticamente.

**Why this priority**: Permite o fluxo quantitativo do experimento.

**Independent Test**: Pode ser testado criando simulação e verificando que aparece na lista do experimento.

**Acceptance Scenarios**:

1. **Given** página de detalhe do experimento, **When** clica em "+ Nova Simulação", **Then** abre fluxo de criação de scorecard (conforme feature 016)
2. **Given** fluxo de criação, **When** completa scorecard e executa simulação, **Then** scorecard e simulação são criados com experiment_id vinculado
3. **Given** simulação criada, **When** volta para detalhe do experimento, **Then** nova simulação aparece na seção "Simulações"
4. **Given** card de simulação, **When** usuário clica, **Then** navega para detalhe da simulação (/experiments/:id/simulations/:simId)

---

### User Story 5 - Criar Entrevista Vinculada ao Experimento (Priority: P1)

O usuário cria uma nova entrevista diretamente da página do experimento, já vinculada automaticamente.

**Why this priority**: Permite o fluxo qualitativo do experimento.

**Independent Test**: Pode ser testado criando entrevista e verificando que aparece na lista do experimento.

**Acceptance Scenarios**:

1. **Given** página de detalhe do experimento, **When** clica em "+ Nova Entrevista", **Then** abre dialog de criação (similar ao atual NewInterviewDialog)
2. **Given** dialog de criação, **When** seleciona tópico e configura parâmetros, **Then** entrevista é criada com experiment_id vinculado
3. **Given** entrevista criada, **When** volta para detalhe do experimento, **Then** nova entrevista aparece na seção "Entrevistas"
4. **Given** card de entrevista, **When** usuário clica, **Then** navega para detalhe da entrevista (/experiments/:id/interviews/:execId)

---

### User Story 6 - Navegar para Detalhe de Simulação (Priority: P1)

O usuário acessa o detalhe de uma simulação específica para ver resultados, insights e análises.

**Why this priority**: Permite consumir os resultados quantitativos.

**Independent Test**: Pode ser testado clicando em simulação e verificando que detalhe é exibido.

**Acceptance Scenarios**:

1. **Given** usuário clica em card de simulação, **When** simulação tem resultados, **Then** vê página com scorecard, resultados e insights
2. **Given** página de simulação, **When** insights estão disponíveis, **Then** exibe análises geradas (charts, regras de região, sensibilidade)
3. **Given** página de simulação, **When** usuário clica em "<- [Nome do Experimento]", **Then** volta para detalhe do experimento
4. **Given** página de simulação, **When** insights ainda não gerados, **Then** mostra botão para gerar/status de processamento

---

### User Story 7 - Navegar para Detalhe de Entrevista (Priority: P1)

O usuário acessa o detalhe de uma entrevista específica para ver transcrições, summary e PR-FAQ.

**IMPORTANTE**: O comportamento e layout da página de detalhe da entrevista (InterviewDetail) permanece INALTERADO. Apenas a rota de acesso muda (de /interviews/:id para /experiments/:expId/interviews/:execId) e o breadcrumb é ajustado para voltar ao experimento.

**Why this priority**: Permite consumir os resultados qualitativos.

**Independent Test**: Pode ser testado clicando em entrevista e verificando que detalhe é exibido com mesmo comportamento atual.

**Acceptance Scenarios**:

1. **Given** usuário clica em card de entrevista, **When** entrevista foi executada, **Then** vê página InterviewDetail existente (sem alterações de layout/funcionalidade)
2. **Given** página de entrevista, **When** summary está pronto, **Then** comportamento existente é mantido
3. **Given** página de entrevista, **When** usuário clica em "<- [Nome do Experimento]", **Then** volta para detalhe do experimento (única mudança: breadcrumb)

---

### User Story 8 - Acessar Catálogo de Synths (Priority: P1)

O usuário acessa o catálogo de synths através do menu secundário, fora do fluxo principal de experimentos.

**Why this priority**: Synths são recurso essencial para entender a base de personas disponíveis.

**Independent Test**: Pode ser testado clicando no ícone de synths no header e verificando que catálogo abre.

**Acceptance Scenarios**:

1. **Given** usuário em qualquer página, **When** clica no ícone de Synths no header, **Then** navega para /synths (página dedicada)
2. **Given** catálogo de synths, **When** usuário busca ou filtra, **Then** funcionalidade existente é mantida
3. **Given** catálogo de synths, **When** usuário clica em synth, **Then** vê detalhe do synth (modal)
4. **Given** página de synths, **When** usuário quer voltar, **Then** usa navegação do browser ou link no header

---

### User Story 9 - Editar Experimento (Priority: P2)

O usuário edita os dados de um experimento existente.

**Why this priority**: Permite corrigir/atualizar informações.

**Independent Test**: Pode ser testado editando nome de experimento e verificando que persiste.

**Acceptance Scenarios**:

1. **Given** página de detalhe do experimento, **When** clica em "Editar", **Then** abre modal com campos preenchidos
2. **Given** modal de edição, **When** altera nome e salva, **Then** nome é atualizado na página e na home
3. **Given** modal de edição, **When** altera hipótese e salva, **Then** hipótese é atualizada

---

### Edge Cases

- O que acontece quando usuário acessa URL de experimento inexistente? Mostra 404 com link para home
- O que acontece quando simulação/entrevista está em execução e usuário tenta excluir experimento? Bloqueia exclusão até conclusão ou exige confirmação extra
- O que acontece quando usuário tenta criar experimento com nome duplicado? Permite (nomes não são únicos)

---

## Requirements *(mandatory)*

### Functional Requirements

**Entidade Experimento**
- **FR-001**: Sistema DEVE permitir criar experimento com nome (obrigatório), hipótese (obrigatório) e descrição (opcional)
- **FR-002**: Sistema DEVE permitir editar nome, hipótese e descrição de experimento existente
- **FR-003**: Sistema DEVE registrar created_at e updated_at automaticamente

**Navegação**
- **FR-004**: Home (/) DEVE exibir lista de experimentos em grid de cards
- **FR-005**: Card de experimento DEVE mostrar: nome, hipótese truncada, contadores (simulações/entrevistas), data de criação
- **FR-006**: Home DEVE ter botão "+ Novo Experimento" visível
- **FR-007**: Home DEVE mostrar empty state quando não há experimentos
- **FR-008**: Todas as páginas DEVEM ter header com ícone para acessar Synths

**Vinculação de Scorecards/Simulações**
- **FR-009**: Tabela feature_scorecards DEVE ter coluna experiment_id (FK, NOT NULL)
- **FR-010**: Criação de scorecard via página de experimento DEVE preencher experiment_id automaticamente
- **FR-011**: Página de detalhe do experimento DEVE listar todos scorecards/simulações com experiment_id correspondente
- **FR-012**: Detalhe de simulação DEVE ter breadcrumb para voltar ao experimento pai

**Vinculação de Entrevistas**
- **FR-013**: Tabela research_executions DEVE ter coluna experiment_id (FK, NOT NULL)
- **FR-014**: Criação de entrevista via página de experimento DEVE preencher experiment_id automaticamente
- **FR-015**: Página de detalhe do experimento DEVE listar todas entrevistas com experiment_id correspondente
- **FR-016**: Detalhe de entrevista DEVE manter comportamento existente, apenas alterando breadcrumb

**Synth Groups**
- **FR-017**: Tabela synth_groups DEVE ter: id (PK), name, description, created_at
- **FR-018**: Tabela synths DEVE ter coluna synth_group_id (FK, NOT NULL)
- **FR-019**: Geração de synths DEVE aceitar synth_group_id como parâmetro opcional
- **FR-020**: Se synth_group_id informado e grupo NÃO existir, sistema DEVE criar o grupo automaticamente
- **FR-021**: Se synth_group_id NÃO informado, sistema DEVE criar novo grupo com nome baseado em data/hora
- **FR-022**: Catálogo de synths DEVE permitir filtrar por grupo

**Synths (Menu Secundário)**
- **FR-023**: Header DEVE ter ícone/botão para acessar catálogo de synths (/synths)
- **FR-024**: Catálogo de synths DEVE manter funcionalidade existente (listagem, busca, detalhe)
- **FR-025**: Catálogo de synths DEVE exibir informação do grupo de cada synth

### Key Entities

**Experiment**
- Representa uma feature/hipótese a ser testada
- Atributos: id, name, hypothesis, description, created_at, updated_at
- Relacionamentos: possui N scorecards/simulações, possui N entrevistas

**SynthGroup**
- Representa um agrupamento de synths gerados em conjunto
- Atributos: id, name, description, created_at
- Relacionamentos: contém N synths

**FeatureScorecard** (extensão)
- Adiciona: experiment_id (FK para Experiment)
- Mantém: todos os atributos existentes

**ResearchExecution** (extensão)
- Adiciona: experiment_id (FK para Experiment)
- Mantém: todos os atributos existentes

**Synth** (extensão)
- Adiciona: synth_group_id (FK para SynthGroup)
- Mantém: todos os atributos existentes

---

## API Endpoints

**Experimentos**
- `GET /experiments/list` - Lista todos experimentos com paginação e contadores
- `GET /experiments/{id}` - Detalhe de um experimento com simulações e entrevistas
- `POST /experiments` - Criar novo experimento
- `PUT /experiments/{id}` - Atualizar experimento

**Synth Groups**
- `GET /synth-groups` - Lista todos os grupos de synths
- `GET /synth-groups/{id}` - Detalhe de um grupo com lista de synths
- `POST /synth-groups` - Criar novo grupo (usado internamente pela geração)

**Geração de Synths (extensão)**
- `POST /synths/generate` - Aceita `synth_group_id` opcional no body
  - Se grupo existe: adiciona synths ao grupo
  - Se grupo NÃO existe: cria grupo com o id fornecido
  - Se não informado: cria novo grupo automaticamente

**Extensões aos endpoints existentes**
- `POST /experiments/{id}/scorecards` - Criar scorecard vinculado ao experimento
- `POST /experiments/{id}/interviews` - Criar entrevista vinculada ao experimento

### Rotas Frontend

```
/                                      -> ExperimentList (home)
/experiments/:id                       -> ExperimentDetail
/experiments/:id/simulations/:simId    -> SimulationDetail (nova página)
/experiments/:id/interviews/:execId    -> InterviewDetail (componente existente, nova rota)
/synths                                -> SynthCatalog (página existente, movida)
```

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% das novas simulações são criadas vinculadas a um experimento
- **SC-002**: 100% das novas entrevistas são criadas vinculadas a um experimento
- **SC-003**: Usuário consegue criar experimento e executar primeira simulação em menos de 2 minutos
- **SC-004**: Navegação de home até detalhe de simulação requer máximo 2 cliques
- **SC-005**: Navegação de home até detalhe de entrevista requer máximo 2 cliques
- **SC-006**: Zero abas na navegação principal (apenas Experimentos como home)
- **SC-007**: Comportamento de InterviewDetail 100% idêntico ao atual (apenas breadcrumb diferente)
- **SC-008**: 100% dos synths gerados pertencem a um synth_group
- **SC-009**: Catálogo de synths exibe grupo de cada synth

---

## Assumptions

- Banco de dados será recriado do zero antes da implementação (sem migração)
- Não há necessidade de mover simulação/entrevista entre experimentos
- Um experimento pode ter múltiplos scorecards e múltiplas entrevistas
- Experimentos não têm hierarquia (não há sub-experimentos)
- Synths pertencem a grupos (synth_groups), mas grupos são recursos globais (não vinculados a experimentos)
- Todo synth deve pertencer a exatamente um grupo
- Grupos de synths são imutáveis após criação (synths não podem mudar de grupo)
- Tópicos de pesquisa continuam existindo como templates, não vinculados a experimentos
- Scenarios continuam sendo carregados de JSON, não persistidos

---

## UI/UX Guidelines

### Visual Hierarchy

1. **Home**: Grid de cards, CTA proeminente para criar
2. **Detalhe**: Header com info do experimento, seções claras para Simulações e Entrevistas
3. **Navegação**: Breadcrumb simples, header persistente com acesso a Synths
4. **Catálogo de Synths**: Lista com filtro por grupo, badge indicando grupo de cada synth

### Empty States

- Home vazia: Ilustração + texto explicativo + CTA "Criar primeiro experimento"
- Experimento sem simulações: "Nenhuma simulação ainda. Crie sua primeira para testar quantitativamente."
- Experimento sem entrevistas: "Nenhuma entrevista ainda. Crie sua primeira para coletar feedback qualitativo."

### Cards de Experimento

- Nome em destaque
- Hipótese truncada (max 2 linhas)
- Contadores: "X simulações | Y entrevistas"
- Data de criação (formato relativo: "há 2 dias" ou absoluto: "20 dez 2025")

---

## Out of Scope

- Status calculado de experimentos (draft/in_progress/completed) - futuro
- Comparação entre experimentos
- Dashboard com métricas agregadas
- Colaboração multi-usuário em experimentos
- Versionamento de experimentos
- Integração com ferramentas externas (Jira, Notion, etc.)
- Experimentos aninhados ou hierárquicos
- Qualquer alteração no comportamento/layout de InterviewDetail
- Mover synths entre grupos após geração
