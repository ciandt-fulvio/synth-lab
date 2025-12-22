# Feature Specification: Frontend Dashboard para Synth-Lab

**Feature Branch**: `012-frontend-dashboard`
**Created**: 2025-12-20
**Status**: Draft
**Input**: User description: "Criar frontend React com duas tabs (Interviews e Synths) para consumir a API REST do synth-lab"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Visualizar Lista de Entrevistas (Priority: P1)

O usuário pesquisador acessa a aplicação e visualiza uma lista de todas as pesquisas (entrevistas) já realizadas. Cada card mostra informações essenciais como o tópico da pesquisa, data de criação, status e quantidade de synths participantes.

**Why this priority**: Esta é a funcionalidade principal que permite ao usuário ter uma visão geral de todas as pesquisas realizadas. Sem isso, o usuário não consegue acessar nenhum dado histórico.

**Independent Test**: Pode ser testado acessando a aba "Interviews" e verificando se a lista é carregada corretamente com os dados da API.

**Acceptance Scenarios**:

1. **Given** o usuário acessa a aplicação, **When** clica na aba "Interviews", **Then** visualiza uma lista de cards com todas as pesquisas realizadas ordenadas por data (mais recentes primeiro)
2. **Given** existem pesquisas no sistema, **When** a lista é carregada, **Then** cada card mostra: tópico, data de criação, status (pending/running/completed/failed) e quantidade de synths
3. **Given** não existem pesquisas, **When** a lista é carregada, **Then** uma mensagem de estado vazio é exibida com orientação para criar uma nova pesquisa

---

### User Story 2 - Visualizar Detalhes da Entrevista (Priority: P1)

O usuário clica em um card de entrevista e é levado a uma página de detalhes que mostra todas as informações da execução: tópico, data, parâmetros utilizados, lista de synths participantes (clicáveis), o relatório final (summary) e link para o PR/FAQ quando disponível.

**Why this priority**: É fundamental para o usuário poder analisar os resultados de uma pesquisa específica. Complementa diretamente a listagem.

**Independent Test**: Pode ser testado clicando em qualquer card de entrevista e verificando se todos os detalhes são exibidos corretamente.

**Acceptance Scenarios**:

1. **Given** o usuário está na lista de entrevistas, **When** clica em um card, **Then** é navegado para a página de detalhes dessa entrevista
2. **Given** o usuário está na página de detalhes, **When** a página carrega, **Then** visualiza: tópico, data de início/fim, status, modelo usado, max_turns, contagem de sucesso/falha
3. **Given** a entrevista tem synths participantes, **When** a página carrega, **Then** visualiza a lista de synths com nome e avatar, cada um clicável para abrir popup de detalhes
4. **Given** o summary está disponível, **When** o usuário clica em "Ver Relatório", **Then** um popup markdown é aberto mostrando o conteúdo do relatório
5. **Given** o PR/FAQ está disponível, **When** o usuário clica em "Ver PR/FAQ", **Then** um popup markdown é aberto mostrando o conteúdo do PR/FAQ
6. **Given** o PR/FAQ NÃO está disponível mas o summary SIM, **When** a página carrega, **Then** um botão "Gerar PR/FAQ" é exibido

---

### User Story 3 - Visualizar Lista de Synths (Priority: P1)

O usuário acessa a aba "Synths" e visualiza uma galeria/lista de todos os synths disponíveis no sistema. Cada card mostra avatar, nome e informações demográficas básicas.

**Why this priority**: Esta é a segunda funcionalidade principal da aplicação, permitindo ao usuário explorar a base de personas sintéticas.

**Independent Test**: Pode ser testado acessando a aba "Synths" e verificando se a lista de synths é exibida com avatares e informações básicas.

**Acceptance Scenarios**:

1. **Given** o usuário acessa a aplicação, **When** clica na aba "Synths", **Then** visualiza uma grade de cards com todos os synths disponíveis
2. **Given** a lista é carregada, **When** os synths aparecem, **Then** cada card mostra: avatar (imagem), nome, arquétipo e região/cidade
3. **Given** a lista tem muitos synths, **When** o usuário rola a página, **Then** mais synths são carregados (paginação ou infinite scroll)

---

### User Story 4 - Visualizar Detalhes do Synth (Priority: P2)

O usuário clica em um card de synth e um popup/modal é aberto mostrando todos os dados detalhados dessa persona: avatar grande, dados demográficos completos, psicografia (Big Five, interesses, contrato cognitivo), comportamento e capacidades tecnológicas.

**Why this priority**: Complementa a visualização da lista de synths, permitindo análise profunda de cada persona.

**Independent Test**: Pode ser testado clicando em qualquer synth da lista e verificando se o popup mostra todas as informações corretas.

**Acceptance Scenarios**:

1. **Given** o usuário está na lista de synths, **When** clica em um card, **Then** um modal/popup abre com os detalhes completos do synth
2. **Given** o modal está aberto, **When** os dados carregam, **Then** o avatar é exibido em tamanho maior no topo
3. **Given** o modal está aberto, **When** visualiza demografia, **Then** vê: idade, gênero, raça/etnia, localização, escolaridade, renda, ocupação, estado civil, composição familiar
4. **Given** o modal está aberto, **When** visualiza psicografia, **Then** vê: gráfico/barra do Big Five, lista de interesses, tipo e regras do contrato cognitivo
5. **Given** o modal está aberto, **When** clica fora do modal ou no botão fechar, **Then** o modal fecha

---

### User Story 5 - Disparar Nova Entrevista (Priority: P2)

O usuário clica no botão "Nova Entrevista" na aba Interviews, preenche um formulário com o tópico, seleciona synths (ou quantidade aleatória) e parâmetros, e dispara a execução.

**Why this priority**: Permite ao usuário criar novas pesquisas diretamente pela interface, sem precisar usar a API diretamente.

**Independent Test**: Pode ser testado clicando em "Nova Entrevista", preenchendo o formulário e verificando se a execução é iniciada.

**Acceptance Scenarios**:

1. **Given** o usuário está na aba Interviews, **When** clica em "Nova Entrevista", **Then** um modal/formulário abre para configurar a pesquisa
2. **Given** o formulário está aberto, **When** o usuário visualiza os campos, **Then** vê: seleção de tópico (dropdown), seleção de synths (multi-select ou quantidade), max_turns, modelo
3. **Given** o formulário está preenchido corretamente, **When** o usuário clica em "Iniciar", **Then** a entrevista é criada e o usuário é redirecionado para a página de detalhes
4. **Given** a entrevista foi iniciada, **When** a página de detalhes carrega, **Then** o status mostra "running" e as mensagens começam a aparecer em tempo real (SSE)

---

### User Story 6 - Acompanhar Entrevista em Tempo Real (Priority: P3)

O usuário visualiza uma entrevista em andamento e vê as mensagens chegando em tempo real via Server-Sent Events (SSE).

**Why this priority**: Funcionalidade avançada que melhora a experiência do usuário ao permitir acompanhamento live.

**Independent Test**: Pode ser testado iniciando uma nova entrevista e verificando se as mensagens aparecem em tempo real na interface.

**Acceptance Scenarios**:

1. **Given** uma entrevista está em andamento, **When** o usuário acessa a página de detalhes, **Then** vê as mensagens aparecendo em tempo real
2. **Given** as mensagens estão chegando, **When** uma nova mensagem chega, **Then** ela aparece na lista com animação suave
3. **Given** todas as entrevistas terminaram, **When** o evento transcription_completed chega, **Then** o status muda para "generating_summary"
4. **Given** o summary foi gerado, **When** o evento execution_completed chega, **Then** o status muda para "completed" e o botão "Ver Relatório" aparece

---

### User Story 7 - Gerar PR/FAQ (Priority: P3)

O usuário visualiza uma entrevista completa com summary disponível e clica em "Gerar PR/FAQ" para criar o documento automaticamente.

**Why this priority**: Funcionalidade complementar que agrega valor à pesquisa realizada.

**Independent Test**: Pode ser testado em uma entrevista completa clicando em "Gerar PR/FAQ" e verificando se o documento é gerado.

**Acceptance Scenarios**:

1. **Given** a entrevista está completa e tem summary, **When** o usuário clica em "Gerar PR/FAQ", **Then** um loading é exibido enquanto o documento é gerado
2. **Given** o PR/FAQ foi gerado com sucesso, **When** a geração termina, **Then** o botão muda para "Ver PR/FAQ" e o popup pode ser aberto

---

### Edge Cases

- O que acontece quando a API está indisponível? Exibir mensagem de erro amigável com opção de retry
- Como o sistema lida com synths sem avatar? Exibir placeholder/avatar genérico
- O que acontece se o usuário tentar ver uma entrevista que não existe? Exibir página 404 com link para voltar à lista
- Como lidar com entrevistas muito longas (muitas mensagens)? Implementar virtualização ou paginação nas mensagens
- O que acontece se a conexão SSE cair? Tentar reconexão automática com feedback visual
- Como lidar com markdown mal formatado no summary/PR-FAQ? Sanitizar e exibir com fallback para texto plano

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sistema DEVE exibir uma navegação com duas tabs: "Interviews" e "Synths"
- **FR-002**: Sistema DEVE listar todas as pesquisas executadas com paginação
- **FR-003**: Sistema DEVE exibir cards de pesquisa com: tópico, data, status e contagem de synths
- **FR-004**: Sistema DEVE permitir navegação para página de detalhes ao clicar em um card de pesquisa
- **FR-005**: Sistema DEVE exibir todos os detalhes de uma pesquisa: tópico, datas, parâmetros, status, contagens
- **FR-006**: Sistema DEVE listar os synths participantes de uma pesquisa com links clicáveis
- **FR-007**: Sistema DEVE exibir o summary da pesquisa em popup markdown quando disponível
- **FR-008**: Sistema DEVE exibir o PR/FAQ em popup markdown quando disponível
- **FR-009**: Sistema DEVE permitir gerar PR/FAQ quando summary está disponível mas PR/FAQ não
- **FR-010**: Sistema DEVE listar todos os synths com paginação
- **FR-011**: Sistema DEVE exibir cards de synth com: avatar, nome, arquétipo e localização básica
- **FR-012**: Sistema DEVE exibir popup/modal com detalhes completos do synth ao clicar
- **FR-013**: Sistema DEVE exibir avatar do synth em formato de imagem (PNG via API)
- **FR-014**: Sistema DEVE permitir criar nova pesquisa via formulário
- **FR-015**: Sistema DEVE permitir selecionar tópico de uma lista de tópicos disponíveis
- **FR-016**: Sistema DEVE permitir selecionar synths específicos ou quantidade aleatória
- **FR-017**: Sistema DEVE suportar streaming de mensagens em tempo real via SSE
- **FR-018**: Sistema DEVE atualizar status da pesquisa automaticamente baseado em eventos SSE
- **FR-019**: Sistema DEVE exibir estados de loading apropriados durante operações assíncronas
- **FR-020**: Sistema DEVE exibir mensagens de erro amigáveis quando operações falham

### Key Entities

- **Research Execution (Pesquisa/Entrevista)**: Representa uma sessão de pesquisa com múltiplas entrevistas. Contém: exec_id, topic_name, status, synth_count, started_at, completed_at, successful_count, failed_count, model, max_turns, summary_available, prfaq_available
- **Synth (Persona Sintética)**: Representa uma persona sintética com perfil completo. Contém: id, nome, arquétipo, descrição, avatar_path, demographics, psychographics, behavior, disabilities, tech_capabilities
- **Transcript (Transcrição)**: Representa a transcrição de uma entrevista individual. Contém: exec_id, synth_id, synth_name, messages, turn_count, timestamp, status
- **Topic (Tópico)**: Representa um guia de tópico para pesquisas. Contém: name, description, questions, file_count

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Usuários conseguem visualizar a lista de pesquisas em menos de 3 segundos após acessar a aba
- **SC-002**: Usuários conseguem encontrar um synth específico navegando pela lista em menos de 30 segundos
- **SC-003**: O popup de detalhes do synth carrega completamente (incluindo avatar) em menos de 2 segundos
- **SC-004**: Usuários conseguem criar e iniciar uma nova pesquisa em menos de 1 minuto
- **SC-005**: Mensagens de entrevistas em andamento aparecem em tempo real com latência máxima de 1 segundo
- **SC-006**: 95% das operações da interface completam sem erros em condições normais de uso
- **SC-007**: Todas as informações críticas (status, contagens, datas) são exibidas corretamente conforme dados da API
- **SC-008**: O sistema funciona corretamente nos navegadores modernos (Chrome, Firefox, Safari, Edge)

## Assumptions

- A API REST do synth-lab está operacional e acessível via mesma origem ou CORS configurado
- O projeto frontend existente (React + TypeScript + Vite + shadcn/ui + Tailwind) será utilizado como base
- Os synths já possuem avatares gerados e disponíveis via endpoint da API
- O SSE está implementado e funcional no backend para streaming de mensagens
- Os tópicos já estão cadastrados no sistema e disponíveis via API
