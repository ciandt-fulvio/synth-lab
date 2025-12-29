# Feature Specification: Analysis Tabs Refactor

**Feature Branch**: `001-analysis-tabs-refactor`
**Created**: 2025-12-29
**Status**: Draft
**Input**: User description: "Reorganizar abas de análise, mover gráficos entre fases, simplificar casos especiais e adicionar entrevistas automáticas"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Visualizar Influência de Features (Priority: P1)

Usuário navega até a aba "Influência" e vê diretamente os gráficos que explicam quais atributos impactam o resultado (SHAP Summary) e como cada atributo afeta a probabilidade de sucesso (PDP). Não há mais gráficos genéricos que não agregam valor.

**Why this priority**: Este é o core value da aba Influência - entender quais fatores realmente importam. Sem isso, a aba não tem propósito.

**Independent Test**: Usuário clica na aba "Influência" e imediatamente vê os dois gráficos (SHAP Summary e PDP) sem precisar configurar nada. Pode analisar a importância das features e suas dependências parciais.

**Acceptance Scenarios**:

1. **Given** usuário está na página de resultados de experimento, **When** clica na aba "Influência", **Then** vê o gráfico "Importância de Features (SHAP)" e o gráfico "Dependência Parcial (PDP)"
2. **Given** usuário está na aba Influência, **When** observa os gráficos, **Then** NÃO vê os antigos gráficos "Importância dos Atributos" e "Correlação de Atributos"

---

### User Story 2 - Investigar Casos Extremos com Explicação Individual (Priority: P1)

Usuário navega até a aba "Especiais", vê os cards de casos extremos (top 5 melhores e piores) e, ao clicar em um card, vê imediatamente a explicação individual (SHAP Waterfall) daquele synth específico, sem precisar selecionar em uma lista dropdown.

**Why this priority**: Entender POR QUE casos extremos se comportam diferente é essencial para insights acionáveis. O click-to-explain torna a jornada mais fluida.

**Independent Test**: Usuário clica em qualquer card de caso extremo e vê o SHAP Waterfall correspondente aparecer logo abaixo, explicando os fatores que levaram àquele resultado.

**Acceptance Scenarios**:

1. **Given** usuário está na aba "Especiais", **When** vê a seção "Casos Extremos", **Then** NÃO vê perguntas sugeridas nem coluna "Casos Inesperados"
2. **Given** usuário vê os cards de casos extremos, **When** clica em um card (qualquer um dos top 5 melhores ou piores), **Then** o gráfico "Explicação Individual (SHAP Waterfall)" aparece logo abaixo mostrando os fatores daquele synth específico
3. **Given** gráfico de explicação individual está visível, **When** usuário clica em outro card de caso extremo, **Then** o gráfico atualiza para mostrar a explicação do novo synth selecionado
4. **Given** usuário está vendo explicação individual, **Then** NÃO vê o dropdown "Selecione um synth" (a seleção é feita pelo click no card)

---

### User Story 3 - Entrevistar Casos Extremos Automaticamente (Priority: P2)

Usuário, ao visualizar os casos extremos (5 melhores e 5 piores), pode clicar em um botão para criar uma entrevista automática com esses 10 synths. Após a criação, recebe um link direto para acompanhar a entrevista.

**Why this priority**: Complementa a análise quantitativa com insights qualitativos, mas é secundário à visualização dos dados. Pode ser implementado após a reorganização básica estar completa.

**Independent Test**: Usuário clica no botão de entrevista, aguarda a criação (com feedback visual), e recebe link clicável que o leva à página da entrevista criada.

**Acceptance Scenarios**:

1. **Given** usuário está na seção "Casos Extremos" da aba "Especiais", **When** vê os 10 cards (5 melhores + 5 piores), **Then** vê um botão "Entrevistar Casos Extremos" (ou similar)
2. **Given** usuário clica no botão de entrevista, **When** o sistema cria a entrevista, **Then** vê um indicador de loading seguido de um link "Ver Entrevista" ou similar
3. **Given** entrevista foi criada com sucesso, **When** usuário clica no link, **Then** é navegado para a página de detalhes da entrevista criada
4. **Given** criação da entrevista falha, **When** ocorre erro, **Then** usuário vê mensagem de erro clara

---

### User Story 4 - Simplificar Outliers Estatísticos (Priority: P2)

Usuário navega até a seção de Outliers Estatísticos e consegue facilmente ajustar a sensibilidade, ver quais synths são outliers e, ao clicar em um, ver a explicação individual (SHAP Waterfall). O card é limpo, sem informações confusas ou redundantes.

**Why this priority**: Melhora a usabilidade de uma feature existente, mas não é crítico para o core value da aba Especiais (que é focar em casos extremos).

**Independent Test**: Usuário ajusta o slider de sensibilidade, vê a lista de outliers atualizar, clica em um outlier e vê a explicação individual aparecer.

**Acceptance Scenarios**:

1. **Given** usuário está na seção "Outliers Estatísticos", **When** vê o card, **Then** o slider tem um nome claro (ex: "Sensibilidade de Detecção" ou "Limite de Anomalia")
2. **Given** usuário vê os cards de outliers, **When** observa cada card, **Then** NÃO vê barra de anomalia, NÃO vê número laranja no topo (ou está claramente explicado), NÃO vê tag "Perfil Atípico"
3. **Given** usuário clica em um card de outlier, **When** seleção é feita, **Then** o gráfico "Explicação Individual (SHAP Waterfall)" aparece mostrando os fatores daquele synth outlier
4. **Given** usuário ajusta o slider de sensibilidade, **When** move o slider, **Then** a lista de outliers atualiza em tempo real

---

### User Story 5 - Navegação Simplificada com 5 Fases (Priority: P1)

Usuário navega entre as abas de análise e vê claramente "5 fases de investigação" (não mais 6). A aba "Deep Dive" não existe mais, simplificando a jornada e removendo redundância.

**Why this priority**: Afeta a estrutura geral da navegação e deve ser implementado junto com a reorganização das abas. É fundamental para a coerência da UI.

**Independent Test**: Usuário conta as abas disponíveis e confirma que são exatamente 5: Geral, Influência, Segmentos, Especiais, Insights.

**Acceptance Scenarios**:

1. **Given** usuário está na página de resultados do experimento, **When** observa as abas de análise, **Then** vê exatamente 5 abas: "Geral", "Influência", "Segmentos", "Especiais", "Insights"
2. **Given** usuário observa o indicador de fases, **When** lê o texto, **Then** vê "5 fases de investigação" (não mais "6 fases")
3. **Given** usuário navega entre as abas, **When** tenta encontrar "Deep Dive", **Then** NÃO encontra essa aba

---

### Edge Cases

- O que acontece se não houver dados suficientes para gerar os gráficos SHAP ou PDP na aba Influência? (Mostrar mensagem de empty state explicando que análise de Monte Carlo é necessária)
- Como o sistema se comporta se um usuário clica rapidamente em múltiplos cards de casos extremos? (Debounce ou loading state para evitar múltiplas requisições simultâneas)
- O que acontece se a criação da entrevista automática falha por timeout ou erro de API? (Mostrar toast de erro com opção de tentar novamente)
- Como lidar com outliers quando o slider está em sensibilidade máxima ou mínima e não há outliers detectados? (Mostrar empty state explicando que não há outliers com a sensibilidade atual)
- O que acontece se o usuário clica em um card de outlier/caso extremo enquanto outro SHAP Waterfall ainda está carregando? (Cancelar requisição anterior e mostrar loading state do novo)

## Requirements *(mandatory)*

### Functional Requirements

#### Reorganização de Abas

- **FR-001**: Sistema DEVE remover a aba "Deep Dive" da navegação de análise
- **FR-002**: Sistema DEVE atualizar o indicador de fases de "6 fases" para "5 fases"
- **FR-003**: Sistema DEVE manter as abas: "Geral", "Influência", "Segmentos", "Especiais", "Insights" nessa ordem

#### Aba Influência

- **FR-004**: Sistema DEVE remover os gráficos "Importância dos Atributos" e "Correlação de Atributos" da aba Influência
- **FR-005**: Sistema DEVE mover o gráfico "Importância de Features (SHAP Summary)" para a aba Influência
- **FR-006**: Sistema DEVE mover o gráfico "Dependência Parcial (PDP)" para a aba Influência
- **FR-007**: Sistema DEVE exibir SHAP Summary e PDP na aba Influência sem necessidade de configuração manual

#### Aba Especiais - Casos Extremos

- **FR-008**: Sistema DEVE remover perguntas sugeridas da seção "Casos Extremos"
- **FR-009**: Sistema DEVE remover a coluna "Casos Inesperados" da seção "Casos Extremos"
- **FR-010**: Sistema DEVE mover o gráfico "Explicação Individual (SHAP Waterfall)" para a aba Especiais, posicionado logo abaixo da seção "Casos Extremos"
- **FR-011**: Sistema DEVE permitir que usuário clique em qualquer card de caso extremo (top 5 melhores ou top 5 piores) para visualizar a explicação individual daquele synth
- **FR-012**: Sistema DEVE remover o dropdown "Selecione um synth" do componente de explicação individual (seleção será via click no card)
- **FR-013**: Sistema DEVE atualizar o gráfico SHAP Waterfall quando usuário clica em um card diferente

#### Aba Especiais - Entrevista Automática

- **FR-014**: Sistema DEVE adicionar um botão para criar entrevista com os casos extremos (5 melhores + 5 piores = 10 synths)
- **FR-015**: Sistema DEVE criar entrevista com 4 turnos (fixo) quando usuário clica no botão
- **FR-016**: Sistema DEVE exibir indicador de loading durante criação da entrevista
- **FR-017**: Sistema DEVE mostrar link clicável para a entrevista criada após conclusão bem-sucedida
- **FR-018**: Sistema DEVE exibir mensagem de erro se criação da entrevista falhar

#### Aba Especiais - Outliers Estatísticos

- **FR-019**: Sistema DEVE renomear o slider de outliers para um nome mais claro (ex: "Sensibilidade de Detecção")
- **FR-020**: Sistema DEVE remover a barra de anomalia de dentro dos cards de outliers
- **FR-021**: Sistema DEVE remover ou clarificar o número laranja que aparece no topo dos cards de outliers
- **FR-022**: Sistema DEVE remover a tag/chip "Perfil Atípico" dos cards de outliers
- **FR-023**: Sistema DEVE permitir que usuário clique em um card de outlier para ver a explicação individual (SHAP Waterfall)
- **FR-024**: Sistema DEVE atualizar dinamicamente a lista de outliers quando usuário ajusta o slider de sensibilidade

#### Backend Cleanup

- **FR-025**: Sistema DEVE remover endpoints de API que serviam APENAS os gráficos "Importância dos Atributos" e "Correlação de Atributos" (se não forem usados em outros lugares)
- **FR-026**: Sistema DEVE remover services, models e outras camadas de backend que existiam APENAS para suportar os endpoints removidos

### Key Entities

- **Synth (Persona Sintética)**: Representa um usuário simulado com atributos (capability, trust, friction_tolerance) e resultados de tentativa/sucesso
- **Caso Extremo**: Synth que está nos top 5 melhores ou top 5 piores em taxa de sucesso
- **Outlier Estatístico**: Synth que apresenta comportamento anômalo detectado por análise estatística (zscore, isolation forest, etc)
- **Entrevista**: Sessão de perguntas e respostas com synths específicos, com número de turnos definido
- **Explicação Individual (SHAP Waterfall)**: Visualização dos fatores que contribuíram para o resultado de um synth específico

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Usuário consegue visualizar a aba "Influência" com os 2 gráficos corretos (SHAP Summary e PDP) em menos de 2 segundos após clicar na aba
- **SC-002**: Usuário consegue clicar em um card de caso extremo e ver a explicação individual (SHAP Waterfall) aparecer em menos de 3 segundos
- **SC-003**: Usuário consegue criar uma entrevista automática com os casos extremos em menos de 10 segundos (incluindo feedback visual de sucesso)
- **SC-004**: Navegação entre as 5 abas de análise é clara e intuitiva, sem abas desnecessárias
- **SC-005**: Card de outliers é simplificado, removendo pelo menos 3 elementos confusos (barra de anomalia, número laranja, tag "Perfil Atípico")
- **SC-006**: 100% dos endpoints de backend que serviam APENAS os gráficos removidos são deletados do código
- **SC-007**: Interface da aba "Especiais" permite interação direta com cards (click-to-explain) sem necessidade de dropdowns ou configurações adicionais
