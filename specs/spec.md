# Feature Specification: Experiment Hub - Reorganizacao da Navegacao

**Feature Branch**: `Experiment Hub`
**Created**: 2025-12-26
**Status**: Draft
**Input**: Reorganizacao da arquitetura de navegacao do frontend para centralizar o conceito de "Experimento" como container principal de simulacoes e entrevistas

## Visao Geral

### Problema
A navegacao atual do SynthLab apresenta abas separadas para "Entrevistas" e "Synths", mas com a adicao do sistema de simulacao (feature 016), o fluxo de trabalho do usuario ficou fragmentado. Usuarios pensam em termos de "features a testar" ou "experimentos", nao em "simulacoes" ou "entrevistas" como conceitos independentes.

### Solucao
Implementar o modelo "Single Hub" onde:
- **Experimento** e o conceito central (feature/hipotese a testar)
- **Simulacoes** e **Entrevistas** existem apenas dentro de um Experimento

### Fluxo Conceitual
```
Experimento (Feature/Hipotese)
    |
    +-- Simulacao(oes) --> Insights/Analises (quantitativo)
    |
    +-- Entrevista(s) --> Summary/PR-FAQ (qualitativo)
```

---

## Modelo de Dados

### Diagrama de Entidades (ERD)

```
+------------------+
|   experiments    |
+------------------+
| id (PK)          |
| name             |
| hypothesis       |
| description      |
| created_at       |
| updated_at       |
+------------------+
        |
        | 1
        |
        +---------------------------+
        |                           |
        | N                         | N
        v                           v
+------------------+       +----------------------+
| feature_scorecards|       | research_executions  |
+------------------+       +----------------------+
| id (PK)          |       | exec_id (PK)         |
| experiment_id(FK)|       | experiment_id (FK)   |
| data (JSON)      |       | topic_name           |
| created_at       |       | status               |
| updated_at       |       | synth_count          |
+------------------+       | ...                  |
        |                  +----------------------+
        | 1                         |
        |                           | 1
        | N                         |
        v                           | N
+------------------+                v
| simulation_runs  |       +------------------+
+------------------+       |   transcripts    |
| id (PK)          |       +------------------+
| scorecard_id(FK) |       | id (PK)          |
| scenario_id      |       | exec_id (FK)     |
| config (JSON)    |       | synth_id (FK)    |
| status           |       | content (JSON)   |
| ...              |       | ...              |
+------------------+       +------------------+
        |
        | 1
        |
        +---------------------------+
        |                           |
        | N                         | N
        v                           v
+------------------+       +------------------+
|  synth_outcomes  |       | region_analyses  |
+------------------+       +------------------+
| simulation_id(FK)|       | simulation_id(FK)|
| synth_id (FK)    |       | rules (JSON)     |
| did_not_try_rate |       | synth_count      |
| failed_rate      |       | ...              |
| success_rate     |       +------------------+
+------------------+


+------------------+       +------------------+
|   synth_groups   |       |   scenarios      |
+------------------+       +------------------+
| id (PK)          |       | id (PK)          |
| name             |       | name             |
| description      |       | description      |
| created_at       |       | modifiers (JSON) |
+------------------+       +------------------+
        |                  (Carregados de JSON,
        | 1                 nao persistidos)
        |
        | N
        v
+------------------+
|      synths      |
+------------------+
| id (PK)          |
| synth_group_id   |
|   (FK, NOT NULL) |
| nome             |
| descricao        |
| data (JSON)      |
| avatar_path      |
| created_at       |
| ...              |
+------------------+
```

### Relacionamentos

| Origem | Destino | Cardinalidade | Descricao |
|--------|---------|---------------|-----------|
| Experiment | FeatureScorecard | 1:N | Um experimento pode ter multiplos scorecards |
| Experiment | ResearchExecution | 1:N | Um experimento pode ter multiplas entrevistas |
| FeatureScorecard | SimulationRun | 1:N | Um scorecard pode ter multiplas simulacoes |
| SimulationRun | SynthOutcome | 1:N | Uma simulacao gera outcome para cada synth |
| SimulationRun | RegionAnalysis | 1:N | Uma simulacao pode ter multiplas analises de regiao |
| ResearchExecution | Transcript | 1:N | Uma entrevista tem multiplas transcricoes |
| SynthGroup | Synth | 1:N | Um grupo contem multiplos synths |

### Notas sobre o Modelo

1. **Synth Groups**: Synths sao organizados em grupos (`synth_groups`). Cada grupo tem:
   - `id`: Identificador unico (ex: `grp_abc123`)
   - `name`: Nome descritivo (ex: "Geracao Dezembro 2025")
   - `description`: Breve descricao do proposito/contexto da geracao
   - `created_at`: Data de criacao do grupo

   Cada synth pertence obrigatoriamente a um grupo via `synth_group_id`. Isso permite:
   - Rastrear quando/como synths foram gerados
   - Agrupar synths por "safra" ou contexto de geracao
   - Filtrar synths por grupo no catalogo

4. **FeatureScorecard vs Experiment**: O scorecard e a definicao das dimensoes da feature. O experimento e o container que explica a feature (descricao da hipotese, contexto, anexos).

5. **Experimentos sem status**: Nesta versao, experimentos nao tem campo de status. O estado e inferido pela existencia de simulacoes/entrevistas vinculadas (futuro: pode ser adicionado).

---
---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Visualizar Lista de Experimentos (Priority: P0)

O usuario acessa o SynthLab e ve imediatamente a lista de todos os seus experimentos, com informacoes resumidas sobre o estado de cada um. 

**Why this priority**: E a pagina inicial do sistema - sem ela, nao ha navegacao.

**Independent Test**: Pode ser testado acessando a home e verificando que experimentos existentes sao listados com contadores corretos.

**Acceptance Scenarios**:

1. **Given** usuario acessa a home, **When** existem experimentos cadastrados, **Then** ve grid de cards com nome, hipotese truncada, contadores (simulacoes/entrevistas) e data de criacao
2. **Given** usuario acessa a home, **When** nao existem experimentos, **Then** ve empty state com CTA para criar primeiro experimento
3. **Given** lista de experimentos, **When** usuario clica em um card, **Then** navega para pagina de detalhe do experimento
4. **Given** lista de experimentos, **When** usuario clica em "+ Novo Experimento", **Then** abre modal/drawer de criacao

---

### User Story 2 - Criar Novo Experimento (Priority: P0)

O usuario cria um novo experimento definindo a feature/hipotese que deseja testar.

**Why this priority**: Sem criar experimentos, nao ha como usar o sistema.

**Campos do Experimento**:
- **Nome** (obrigatorio): Nome curto da feature (max 100 chars)
- **Hipotese** (obrigatorio): Descricao da hipotese a ser testada (max 500 chars)
- **Descricao** (opcional): Contexto adicional, links, referencias (max 2000 chars)

**Independent Test**: Pode ser testado criando um experimento e verificando que aparece na lista.

**Acceptance Scenarios**:

1. **Given** usuario na home, **When** clica em "+ Novo Experimento", **Then** abre modal com formulario
2. **Given** formulario aberto, **When** preenche nome e hipotese e salva, **Then** experimento e criado e salvo no banco
3. **Given** formulario aberto, **When** tenta salvar sem nome ou hipotese, **Then** mostra validacao de campos obrigatorios
4. **Given** experimento criado, **When** volta para home, **Then** novo experimento aparece na lista

---

### User Story 3 - Visualizar Detalhe do Experimento (Priority: P0)

O usuario acessa o detalhe de um experimento e ve todas as simulacoes e entrevistas vinculadas, com acoes para criar novas.

**Why this priority**: E a pagina central de trabalho do usuario.

**Layout da Pagina**:
```
+--------------------------------------------------+
| <- Experimentos                    [Synths] [Cog]|
+--------------------------------------------------+
| [Nome do Experimento]                   [Editar] |
| Hipotese: "..."                                  |
| Criado: 20 dez 2025                              |
+--------------------------------------------------+
| Simulacoes                    [+ Nova Simulacao] |
| +----------------+ +----------------+            |
| | Cenario Base   | | Cenario Crisis |            |
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

**Independent Test**: Pode ser testado acessando experimento existente e verificando que simulacoes e entrevistas vinculadas aparecem.

**Acceptance Scenarios**:

1. **Given** usuario na home, **When** clica em um experimento, **Then** navega para /experiments/:id com detalhes completos
2. **Given** pagina de detalhe, **When** experimento tem simulacoes, **Then** mostra cards das simulacoes com cenario, score e status
3. **Given** pagina de detalhe, **When** experimento tem entrevistas, **Then** mostra cards das entrevistas com contagem de synths e status de artefatos
4. **Given** pagina de detalhe, **When** experimento nao tem simulacoes nem entrevistas, **Then** mostra empty states com CTAs
5. **Given** pagina de detalhe, **When** usuario clica em "Editar", **Then** abre modal para editar nome/hipotese/descricao
6. **Given** pagina de detalhe, **When** usuario clica em "<- Experimentos", **Then** volta para home

---

### User Story 4 - Criar Simulacao Vinculada ao Experimento (Priority: P1)

O usuario cria uma nova simulacao diretamente da pagina do experimento, ja vinculada automaticamente.

**Why this priority**: Permite o fluxo quantitativo do experimento.

**Independent Test**: Pode ser testado criando simulacao e verificando que aparece na lista do experimento.

**Acceptance Scenarios**:

1. **Given** pagina de detalhe do experimento, **When** clica em "+ Nova Simulacao", **Then** abre fluxo de criacao de scorecard (conforme feature 016)
2. **Given** fluxo de criacao, **When** completa scorecard e executa simulacao, **Then** scorecard e simulacao sao criados com experiment_id vinculado
3. **Given** simulacao criada, **When** volta para detalhe do experimento, **Then** nova simulacao aparece na secao "Simulacoes"
4. **Given** card de simulacao, **When** usuario clica, **Then** navega para detalhe da simulacao (/experiments/:id/simulations/:simId)

---

### User Story 5 - Criar Entrevista Vinculada ao Experimento (Priority: P1)

O usuario cria uma nova entrevista diretamente da pagina do experimento, ja vinculada automaticamente.

**Why this priority**: Permite o fluxo qualitativo do experimento.

**Independent Test**: Pode ser testado criando entrevista e verificando que aparece na lista do experimento.

**Acceptance Scenarios**:

1. **Given** pagina de detalhe do experimento, **When** clica em "+ Nova Entrevista", **Then** abre dialog de criacao (similar ao atual NewInterviewDialog)
2. **Given** dialog de criacao, **When** seleciona topico e configura parametros, **Then** entrevista e criada com experiment_id vinculado
3. **Given** entrevista criada, **When** volta para detalhe do experimento, **Then** nova entrevista aparece na secao "Entrevistas"
4. **Given** card de entrevista, **When** usuario clica, **Then** navega para detalhe da entrevista (/experiments/:id/interviews/:execId)

---

### User Story 6 - Navegar para Detalhe de Simulacao (Priority: P1)

O usuario acessa o detalhe de uma simulacao especifica para ver resultados, insights e analises.

**Why this priority**: Permite consumir os resultados quantitativos.

**Independent Test**: Pode ser testado clicando em simulacao e verificando que detalhe e exibido.

**Acceptance Scenarios**:

1. **Given** usuario clica em card de simulacao, **When** simulacao tem resultados, **Then** ve pagina com scorecard, resultados e insights
2. **Given** pagina de simulacao, **When** insights estao disponiveis, **Then** exibe analises geradas (charts, regras de regiao, sensibilidade)
3. **Given** pagina de simulacao, **When** usuario clica em "<- [Nome do Experimento]", **Then** volta para detalhe do experimento
4. **Given** pagina de simulacao, **When** insights ainda nao gerados, **Then** mostra botao para gerar/status de processamento

---

### User Story 7 - Navegar para Detalhe de Entrevista (Priority: P1)

O usuario acessa o detalhe de uma entrevista especifica para ver transcricoes, summary e PR-FAQ.

**IMPORTANTE**: O comportamento e layout da pagina de detalhe da entrevista (InterviewDetail) permanece INALTERADO. Apenas a rota de acesso muda (de /interviews/:id para /experiments/:expId/interviews/:execId) e o breadcrumb e ajustado para voltar ao experimento.

**Why this priority**: Permite consumir os resultados qualitativos.

**Independent Test**: Pode ser testado clicando em entrevista e verificando que detalhe e exibido com mesmo comportamento atual.

**Acceptance Scenarios**:

1. **Given** usuario clica em card de entrevista, **When** entrevista foi executada, **Then** ve pagina InterviewDetail existente (sem alteracoes de layout/funcionalidade)
2. **Given** pagina de entrevista, **When** summary esta pronto, **Then** comportamento existente e mantido
3. **Given** pagina de entrevista, **When** usuario clica em "<- [Nome do Experimento]", **Then** volta para detalhe do experimento (unica mudanca: breadcrumb)

---

### User Story 8 - Acessar Catalogo de Synths (Priority: P1)

O usuario acessa o catalogo de synths atraves do menu secundario, fora do fluxo principal de experimentos.

**Why this priority**: Synths sao recurso essencial para entender a base de personas disponiveis.

**Independent Test**: Pode ser testado clicando no icone de synths no header e verificando que catalogo abre.

**Acceptance Scenarios**:

1. **Given** usuario em qualquer pagina, **When** clica no icone de Synths no header, **Then** navega para /synths (pagina dedicada)
2. **Given** catalogo de synths, **When** usuario busca ou filtra, **Then** funcionalidade existente e mantida
3. **Given** catalogo de synths, **When** usuario clica em synth, **Then** ve detalhe do synth (modal)
4. **Given** pagina de synths, **When** usuario quer voltar, **Then** usa navegacao do browser ou link no header

---

### User Story 9 - Editar Experimento (Priority: P2)

O usuario edita os dados de um experimento existente.

**Why this priority**: Permite corrigir/atualizar informacoes.

**Independent Test**: Pode ser testado editando nome de experimento e verificando que persiste.

**Acceptance Scenarios**:

1. **Given** pagina de detalhe do experimento, **When** clica em "Editar", **Then** abre modal com campos preenchidos
2. **Given** modal de edicao, **When** altera nome e salva, **Then** nome e atualizado na pagina e na home
3. **Given** modal de edicao, **When** altera hipotese e salva, **Then** hipotese e atualizada

---


### Edge Cases

- O que acontece quando usuario acessa URL de experimento inexistente? Mostra 404 com link para home
- O que acontece quando simulacao/entrevista esta em execucao e usuario tenta excluir experimento? Bloqueia exclusao ate conclusao ou exige confirmacao extra
- O que acontece quando usuario tenta criar experimento com nome duplicado? Permite (nomes nao sao unicos)

---

## Requirements *(mandatory)*

### Functional Requirements

**Entidade Experimento**
- **FR-001**: Sistema DEVE permitir criar experimento com nome (obrigatorio), hipotese (obrigatorio) e descricao (opcional)
- **FR-002**: Sistema DEVE permitir editar nome, hipotese e descricao de experimento existente
- **FR-003**: Sistema DEVE registrar created_at e updated_at automaticamente

**Navegacao**
- **FR-004**: Home (/) DEVE exibir lista de experimentos em grid de cards
- **FR-005**: Card de experimento DEVE mostrar: nome, hipotese truncada, contadores (simulacoes/entrevistas), data de criacao
- **FR-006**: Home DEVE ter botao "+ Novo Experimento" visivel
- **FR-007**: Home DEVE mostrar empty state quando nao ha experimentos
- **FR-008**: Todas as paginas DEVE ter header com icone para acessar Synths

**Vinculacao de Scorecards/Simulacoes**
- **FR-009**: Tabela feature_scorecards DEVE ter coluna experiment_id (FK, NOT NULL)
- **FR-010**: Criacao de scorecard via pagina de experimento DEVE preencher experiment_id automaticamente
- **FR-011**: Pagina de detalhe do experimento DEVE listar todos scorecards/simulacoes com experiment_id correspondente
- **FR-012**: Detalhe de simulacao DEVE ter breadcrumb para voltar ao experimento pai

**Vinculacao de Entrevistas**
- **FR-013**: Tabela research_executions DEVE ter coluna experiment_id (FK, NOT NULL)
- **FR-014**: Criacao de entrevista via pagina de experimento DEVE preencher experiment_id automaticamente
- **FR-015**: Pagina de detalhe do experimento DEVE listar todas entrevistas com experiment_id correspondente
- **FR-016**: Detalhe de entrevista DEVE manter comportamento existente, apenas alterando breadcrumb

**Synth Groups**
- **FR-017**: Tabela synth_groups DEVE ter: id (PK), name, description, created_at
- **FR-018**: Tabela synths DEVE ter coluna synth_group_id (FK, NOT NULL)
- **FR-019**: Geracao de synths DEVE aceitar synth_group_id como parametro opcional
- **FR-020**: Se synth_group_id informado e grupo NAO existir, sistema DEVE criar o grupo automaticamente
- **FR-021**: Se synth_group_id NAO informado, sistema DEVE criar novo grupo com nome baseado em data/hora
- **FR-022**: Catalogo de synths DEVE permitir filtrar por grupo

**Synths (Menu Secundario)**
- **FR-023**: Header DEVE ter icone/botao para acessar catalogo de synths (/synths)
- **FR-024**: Catalogo de synths DEVE manter funcionalidade existente (listagem, busca, detalhe)
- **FR-025**: Catalogo de synths DEVE exibir informacao do grupo de cada synth

### API Endpoints

**Experimentos**
- `GET /experiments/list` - Lista todos experimentos com paginacao e contadores
- `GET /experiments/{id}` - Detalhe de um experimento com simulacoes e entrevistas
- `POST /experiments` - Criar novo experimento
- `PUT /experiments/{id}` - Atualizar experimento

**Synth Groups**
- `GET /synth-groups` - Lista todos os grupos de synths
- `GET /synth-groups/{id}` - Detalhe de um grupo com lista de synths
- `POST /synth-groups` - Criar novo grupo (usado internamente pela geracao)

**Geracao de Synths (extensao)**
- `POST /synths/generate` - Aceita `synth_group_id` opcional no body
  - Se grupo existe: adiciona synths ao grupo
  - Se grupo NAO existe: cria grupo com o id fornecido
  - Se nao informado: cria novo grupo automaticamente

**Extensoes aos endpoints existentes**
- `POST /experiments/{id}/scorecards` - Criar scorecard vinculado ao experimento
- `POST /experiments/{id}/interviews` - Criar entrevista vinculada ao experimento
- Endpoints existentes de simulation e research continuam funcionando, mas agora requerem experiment_id

### Rotas Frontend

```
/                                      -> ExperimentList (home)
/experiments/:id                       -> ExperimentDetail
/experiments/:id/simulations/:simId    -> SimulationDetail (nova pagina)
/experiments/:id/interviews/:execId    -> InterviewDetail (componente existente, nova rota)
/synths                                -> SynthCatalog (pagina existente, movida)
```

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% das novas simulacoes sao criadas vinculadas a um experimento
- **SC-002**: 100% das novas entrevistas sao criadas vinculadas a um experimento
- **SC-003**: Usuario consegue criar experimento e executar primeira simulacao em menos de 2 minutos
- **SC-004**: Navegacao de home ate detalhe de simulacao requer maximo 2 cliques
- **SC-005**: Navegacao de home ate detalhe de entrevista requer maximo 2 cliques
- **SC-006**: Zero abas na navegacao principal (apenas Experimentos como home)
- **SC-007**: Comportamento de InterviewDetail 100% identico ao atual (apenas breadcrumb diferente)
- **SC-008**: 100% dos synths gerados pertencem a um synth_group
- **SC-009**: Catalogo de synths exibe grupo de cada synth

---

## Assumptions

- Banco de dados sera recriado do zero antes da implementacao (sem migracao)
- Nao ha necessidade de mover simulacao/entrevista entre experimentos
- Um experimento pode ter multiplos scorecards e multiplas entrevistas
- Experimentos nao tem hierarquia (nao ha sub-experimentos)
- Synths pertencem a grupos (synth_groups), mas grupos sao recursos globais (nao vinculados a experimentos)
- Todo synth deve pertencer a exatamente um grupo
- Grupos de synths sao imutaveis apos criacao (synths nao podem mudar de grupo)
- Topicos de pesquisa continuam existindo como templates, nao vinculados a experimentos
- Scenarios continuam sendo carregados de JSON, nao persistidos

---

## UI/UX Guidelines

### Visual Hierarchy

1. **Home**: Grid de cards, CTA proeminente para criar
2. **Detalhe**: Header com info do experimento, secoes claras para Simulacoes e Entrevistas
3. **Navegacao**: Breadcrumb simples, header persistente com acesso a Synths
4. **Catalogo de Synths**: Lista com filtro por grupo, badge indicando grupo de cada synth

### Empty States

- Home vazia: Ilustracao + texto explicativo + CTA "Criar primeiro experimento"
- Experimento sem simulacoes: "Nenhuma simulacao ainda. Crie sua primeira para testar quantitativamente."
- Experimento sem entrevistas: "Nenhuma entrevista ainda. Crie sua primeira para coletar feedback qualitativo."

### Cards de Experimento

- Nome em destaque
- Hipotese truncada (max 2 linhas)
- Contadores: "X simulacoes | Y entrevistas"
- Data de criacao (formato relativo: "ha 2 dias" ou absoluto: "20 dez 2025")

---

## Out of Scope

- Status calculado de experimentos (draft/in_progress/completed) - futuro
- Comparacao entre experimentos
- Dashboard com metricas agregadas
- Colaboracao multi-usuario em experimentos
- Versionamento de experimentos
- Integracao com ferramentas externas (Jira, Notion, etc.)
- Experimentos aninhados ou hierarquicos
- Qualquer alteracao no comportamento/layout de InterviewDetail
- Mover synths entre grupos apos geracao
