# Feature Specification: Grupos de Synths Customizados

**Feature Branch**: `030-custom-synth-groups`
**Created**: 2026-01-12
**Status**: Draft
**Input**: User description: "Permitir que PMs criem grupos de synths com distribuições customizadas dos Fatores Raiz para simular públicos específicos (ex: aposentados, PcD, universitários, especialistas)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Criar Grupo de Synths Customizado (Priority: P1)

Como PM, quero criar um grupo de synths com distribuições demográficas customizadas para simular públicos específicos (ex: aposentados, pessoas com deficiência, universitários) em meus experimentos de pesquisa.

**Why this priority**: Esta é a funcionalidade core da feature - sem ela, não há valor entregue. Permite que PMs testem produtos/serviços com audiências representativas de segmentos específicos da população brasileira.

**Independent Test**: Pode ser testado criando um grupo com configurações customizadas e verificando que 500 synths são gerados com as distribuições especificadas.

**Acceptance Scenarios**:

1. **Given** um PM na tela de grupos, **When** ele clica em "Criar Grupo" e preenche nome, descrição e ajusta os sliders de distribuição, **Then** um novo grupo é criado com 500 synths seguindo as distribuições configuradas
2. **Given** um PM criando um grupo, **When** ele ajusta o slider de Idade "60+" para 80%, **Then** os outros sliders de idade se redistribuem automaticamente para manter soma = 100%
3. **Given** um PM criando um grupo, **When** ele seleciona "Baseado em: Aposentados 60+", **Then** os sliders carregam a configuração do grupo selecionado como ponto de partida

---

### User Story 2 - Visualizar Grupos Existentes (Priority: P2)

Como PM, quero ver a lista de grupos de synths disponíveis (incluindo o Default e grupos customizados) para escolher qual usar em minhas simulações.

**Why this priority**: Necessário para que PMs possam selecionar grupos existentes e usar como base para novos grupos. Complementa a funcionalidade de criação.

**Independent Test**: Pode ser testado acessando a listagem e verificando que todos os grupos são exibidos com nome, descrição e data de criação.

**Acceptance Scenarios**:

1. **Given** um PM na área de grupos, **When** ele acessa a listagem, **Then** vê todos os grupos disponíveis com nome, descrição e data de criação
2. **Given** a listagem de grupos, **When** o sistema é acessado pela primeira vez, **Then** o grupo "Default" com distribuição IBGE está sempre disponível

---

### User Story 3 - Consultar Detalhes de um Grupo (Priority: P3)

Como PM, quero ver os detalhes de configuração de um grupo específico para entender quais distribuições demográficas ele representa.

**Why this priority**: Permite transparência sobre o que cada grupo representa, facilitando decisões informadas sobre qual grupo usar.

**Independent Test**: Pode ser testado selecionando um grupo e verificando que todas as configurações de distribuição são exibidas corretamente.

**Acceptance Scenarios**:

1. **Given** um PM visualizando a lista de grupos, **When** ele seleciona um grupo específico, **Then** vê todas as configurações de distribuição (idade, escolaridade, deficiências, composição familiar, domain expertise)

---

### Edge Cases

- O que acontece quando o PM tenta criar um grupo sem nome? Sistema deve exigir nome como campo obrigatório
- O que acontece quando o PM tenta ajustar um slider para 100%? Os demais sliders do mesmo grupo devem ir para 0%
- Como o sistema lida com descrições acima de 50 caracteres? Sistema deve truncar ou impedir entrada acima do limite
- O que acontece se a geração de synths falhar no meio do processo? O grupo não deve ser criado parcialmente (transação atômica)
- O que acontece quando o PM clica em "Gerar Synths" com sliders que não somam 100%? Sistema deve normalizar automaticamente ou alertar o usuário

## Requirements *(mandatory)*

### Functional Requirements

**Gerenciamento de Grupos**

- **FR-001**: Sistema DEVE permitir criar grupos de synths com nome obrigatório e descrição opcional (máximo 50 caracteres)
- **FR-002**: Sistema DEVE gerar automaticamente 500 synths ao criar um novo grupo, seguindo as distribuições configuradas
- **FR-003**: Grupos DEVEM ser imutáveis após criação (não é possível editar um grupo existente)
- **FR-004**: Sistema DEVE sempre disponibilizar um grupo "Default" com distribuições baseadas em dados IBGE
- **FR-005**: Sistema DEVE permitir listar todos os grupos disponíveis
- **FR-006**: Sistema DEVE permitir consultar detalhes de configuração de um grupo específico

**Configuração de Distribuições**

- **FR-007**: Sistema DEVE permitir configurar distribuição de Idade com 4 faixas: 15-29, 30-44, 45-59, 60+
- **FR-008**: Sistema DEVE permitir configurar distribuição de Escolaridade com 4 níveis: Sem instrução, Fundamental, Médio, Superior
- **FR-009**: Sistema DEVE permitir configurar taxa de deficiências via slider único (0% a 100%)
- **FR-010**: Sistema DEVE permitir configurar Composição Familiar com 5 tipos: Unipessoal, Casal sem filhos, Casal com filhos, Monoparental, Multigeracional
- **FR-011**: Sistema DEVE permitir configurar Domain Expertise com 3 opções: Baixo, Regular, Alto

**Comportamento dos Sliders**

- **FR-012**: Ao ajustar um slider de peso, os outros sliders do mesmo grupo DEVEM se redistribuir automaticamente para manter soma = 100%
- **FR-013**: Cada slider DEVE permitir valores de 0% a 100%
- **FR-014**: Interface DEVE atualizar visualização do histograma em tempo real conforme sliders são ajustados
- **FR-015**: Sistema DEVE oferecer botão "Resetar para IBGE" para cada seção de configuração

**Funcionalidade "Baseado em"**

- **FR-016**: Sistema DEVE permitir selecionar um grupo existente como base para novo grupo
- **FR-017**: Ao selecionar "Baseado em", todas as configurações do grupo selecionado DEVEM ser carregadas como ponto de partida

**Mapeamento Interno de Escolaridade**

- **FR-018**: Sistema DEVE expandir "Fundamental" internamente para fundamental_incompleto (76.3%) e fundamental_completo (23.7%)
- **FR-019**: Sistema DEVE expandir "Médio" internamente para medio_incompleto (13.4%) e medio_completo (86.6%)
- **FR-020**: Sistema DEVE expandir "Superior" internamente para superior_incompleto (18.3%), superior_completo (60.6%) e pos_graduacao (21.1%)

**Lógica de Deficiências**

- **FR-021**: Quando taxa de deficiência <= 8% (IBGE), sistema DEVE usar distribuição uniforme de severidade (20% cada: nenhuma, leve, moderada, severa, total)
- **FR-022**: Quando taxa de deficiência > 8%, sistema DEVE usar distribuição pesada em severos (leve: 10%, moderada: 25%, severa: 30%, total: 35%)
- **FR-023**: Para deficiências visual e auditiva, severidade "total" DEVE mapear para "cegueira" e "surdez" respectivamente
- **FR-024**: Para deficiências motora e cognitiva, severidade "total" DEVE mapear para "severa"

**Domain Expertise**

- **FR-025**: Opção "Baixo" DEVE usar parâmetros Beta (alpha=2, beta=5) com média esperada ~0.29
- **FR-026**: Opção "Regular" DEVE usar parâmetros Beta (alpha=3, beta=3) com média esperada ~0.50
- **FR-027**: Opção "Alto" DEVE usar parâmetros Beta (alpha=5, beta=2) com média esperada ~0.71

### Key Entities

- **SynthGroup**: Representa um grupo de synths com configuração específica. Contém: id (UUID), name (obrigatório), description (opcional, max 50 chars), created_at, config (configurações de distribuição)
- **GroupConfig**: Configuração de distribuições do grupo. Contém: n_synths (fixo em 500), distributions (idade, escolaridade, deficiências, composição_familiar, domain_expertise)
- **Synth**: Persona sintética individual gerada com base nas distribuições do grupo. Herda atributos demográficos que influenciam latent traits na simulação

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: PMs conseguem criar um novo grupo de synths em menos de 3 minutos
- **SC-002**: Sistema gera 500 synths ao criar um grupo, respeitando as distribuições configuradas com margem de erro estatística aceitável (+-5% por categoria)
- **SC-003**: 100% dos grupos criados são persistidos corretamente e recuperáveis após criação
- **SC-004**: Sliders de redistribuição automática mantêm soma exatamente igual a 100% em todas as interações
- **SC-005**: Grupo "Default" está sempre disponível e contém distribuições IBGE corretas
- **SC-006**: PMs conseguem identificar visualmente a distribuição configurada através dos histogramas em tempo real
- **SC-007**: Estado de loading é exibido durante geração de synths, informando que o processo pode levar alguns segundos

## Assumptions

- Os valores IBGE para distribuições demográficas são os mais recentes disponíveis e foram pré-definidos na especificação
- O número fixo de 500 synths por grupo é adequado para as simulações atuais (pode ser parametrizado futuramente)
- As proporções internas de escolaridade (fundamental_incompleto/completo, etc.) seguem dados IBGE e não precisam ser configuráveis pelo usuário
- A lógica de geração de deficiências segue o modelo especificado (primeiro decide se tem deficiência, depois sorteia severidade por categoria)
- Os parâmetros da distribuição Beta para domain expertise foram validados e produzem as médias esperadas
- A interface modal é adequada para o fluxo de criação de grupos
