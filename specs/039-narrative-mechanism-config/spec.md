# Feature Specification: Narrative Mechanism Configuration

**Feature Branch**: `039-narrative-mechanism-config`
**Created**: 2026-02-04
**Status**: Draft
**Input**: Substituir o Step 2 (Scorecard com sliders) do wizard de criação de experimento por uma interface narrativa com dropdowns contextuais, onde a LLM gera um texto fluido descrevendo a feature e o usuário ajusta intensidades dos mecanismos via seleção de texto.

## Problem Statement

Usuários não entendem como duas features com mesmos scores de scorecard se comportam diferentemente na simulação. Os sliders abstratos (ex: "Complexidade = 0.50") não comunicam o significado real dos parâmetros, dificultando a configuração correta dos experimentos e reduzindo a confiança nos resultados da simulação.

## Solution Overview

Substituir a interface de sliders por uma abordagem narrativa onde:
1. **Mecanismos e suas opções** ficam cadastrados no banco de dados (fonte de verdade)
2. **LLM analisa** a descrição da feature e infere quais mecanismos são relevantes
3. **LLM gera um texto narrativo** com placeholders para os mecanismos selecionados
4. **Usuário ajusta intensidades** via dropdowns inline no texto
5. **Sistema mapeia** texto selecionado → valor numérico (usando dados do banco)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Configurar Mecanismos via Narrativa (Priority: P1)

O Product Manager cria um novo experimento e, no Step 2 do wizard, vê um texto narrativo gerado pela IA descrevendo sua feature. O texto contém trechos clicáveis (dropdowns) onde ele pode ajustar a intensidade de cada mecanismo relevante, escolhendo entre opções como "totalmente reversível", "parcialmente reversível" ou "irreversível".

**Why this priority**: Este é o core da feature - substitui completamente a experiência atual de sliders por algo mais intuitivo e contextual.

**Independent Test**: Criar um experimento com nome "Pix via WhatsApp" e hipótese sobre pagamentos sociais. O sistema deve gerar uma narrativa mencionando irreversibilidade e confiança institucional, com dropdowns funcionais.

**Acceptance Scenarios**:

1. **Given** um PM no Step 1 preencheu nome="Pix via WhatsApp", hipótese="Usuários preferem pagar pelo app de mensagens", **When** ele avança para o Step 2, **Then** o sistema exibe um texto narrativo com 2-4 mecanismos relevantes destacados como dropdowns clicáveis.

2. **Given** a narrativa foi gerada com o mecanismo "irreversibility" selecionado como "irreversível", **When** o PM clica no dropdown e seleciona "parcialmente reversível", **Then** o valor interno do mecanismo muda de 1.0 para 0.5 e o texto exibido atualiza.

3. **Given** o PM terminou de ajustar os dropdowns, **When** ele clica em "Continuar", **Then** os valores numéricos dos mecanismos são salvos no experimento e ele avança para o próximo passo.

---

### User Story 2 - Regenerar Narrativa (Priority: P2)

O PM não está satisfeito com a narrativa gerada ou quer uma abordagem diferente. Ele clica em "Regenerar" e a LLM gera uma nova narrativa, possivelmente com mecanismos diferentes destacados.

**Why this priority**: Permite correção quando a IA não acerta na primeira tentativa, aumentando a confiança do usuário no sistema.

**Independent Test**: Clicar em "Regenerar" 3 vezes e verificar que narrativas diferentes são geradas, potencialmente com mecanismos diferentes selecionados.

**Acceptance Scenarios**:

1. **Given** uma narrativa já foi gerada, **When** o PM clica em "Regenerar", **Then** uma nova chamada à LLM é feita e uma narrativa diferente é exibida (pode ter os mesmos ou diferentes mecanismos).

2. **Given** o PM fez ajustes nos dropdowns, **When** ele clica em "Regenerar", **Then** os ajustes anteriores são descartados e a nova narrativa é exibida com os defaults da LLM.

---

### User Story 3 - Consultar Definições de Mecanismos (Priority: P3)

O PM quer entender melhor o que cada mecanismo significa antes de escolher uma opção. Ele pode ver um tooltip ou expandir uma explicação para cada mecanismo.

**Why this priority**: Auxilia no aprendizado do modelo mental, mas não bloqueia o uso básico da feature.

**Independent Test**: Passar o mouse sobre um dropdown de mecanismo e verificar que um tooltip com a descrição aparece.

**Acceptance Scenarios**:

1. **Given** a narrativa está exibida com dropdowns, **When** o PM passa o mouse sobre um dropdown, **Then** um tooltip aparece com a descrição do mecanismo (ex: "Irreversibilidade: Grau em que a ação não pode ser desfeita").

---

### User Story 4 - Administrar Definições de Mecanismos (Priority: P4)

Um administrador do sistema pode cadastrar novos mecanismos ou editar as opções de texto e valores dos mecanismos existentes, sem necessidade de deploy.

**Why this priority**: Permite evolução do modelo sem código, mas não é necessário para o MVP.

**Independent Test**: Via API ou interface admin, adicionar uma nova opção ao mecanismo "irreversibility" e verificar que ela aparece nos dropdowns.

**Acceptance Scenarios**:

1. **Given** o admin acessa a API de mecanismos, **When** ele adiciona uma opção "quase irreversível" com valor 0.85 ao mecanismo "irreversibility", **Then** essa opção aparece nos dropdowns de futuros experimentos.

---

### Edge Cases

- **Nenhum mecanismo relevante**: Se a LLM não identificar nenhum mecanismo relevante para a feature descrita, o sistema deve exibir uma mensagem orientando o PM a enriquecer a descrição ou usar todos os mecanismos com valores default.

- **Erro na geração**: Se a chamada à LLM falhar, o sistema deve exibir mensagem de erro com botão para tentar novamente, sem perder os dados do Step 1.

- **Descrição muito curta**: Se nome + hipótese + descrição tiverem menos de 20 palavras, exibir sugestão para adicionar mais contexto antes de gerar a narrativa.

- **Mecanismo sem opção selecionada**: Se o usuário tentar avançar sem ter selecionado uma opção para algum mecanismo exibido, bloquear com mensagem indicando qual mecanismo falta configurar.

## Requirements *(mandatory)*

### Functional Requirements

**Dados de Referência (Banco)**

- **FR-001**: Sistema DEVE armazenar definições de mecanismos com: chave única, label em português, descrição explicativa.
- **FR-002**: Sistema DEVE armazenar opções para cada mecanismo com: label textual, valor numérico [0,1], ordem de exibição.
- **FR-003**: Sistema DEVE armazenar definições de tipos de feature com: chave, label, lista de mecanismos que amplifica.
- **FR-004**: Sistema DEVE permitir consulta de todos os mecanismos e suas opções via API pública.

**Geração de Narrativa**

- **FR-005**: Sistema DEVE aceitar nome, hipótese e descrição da feature como entrada para geração de narrativa.
- **FR-006**: Sistema DEVE inferir os tipos de feature aplicáveis (financial, social, aesthetic, flow, infra) baseado na descrição.
- **FR-007**: Sistema DEVE selecionar entre 2 e 4 mecanismos relevantes baseado nos tipos inferidos.
- **FR-008**: Sistema DEVE gerar um texto narrativo fluido em português com placeholders para cada mecanismo selecionado.
- **FR-009**: Sistema DEVE selecionar uma opção default para cada mecanismo baseado no contexto da feature.
- **FR-010**: Sistema DEVE retornar quais mecanismos foram excluídos (não relevantes) para a feature.

**Interface do Usuário**

- **FR-011**: Sistema DEVE exibir a narrativa com os placeholders renderizados como dropdowns clicáveis.
- **FR-012**: Cada dropdown DEVE exibir todas as opções do mecanismo correspondente, ordenadas por display_order.
- **FR-013**: Sistema DEVE pré-selecionar a opção default retornada pela LLM em cada dropdown.
- **FR-014**: Sistema DEVE atualizar o texto exibido imediatamente quando o usuário seleciona uma opção diferente.
- **FR-015**: Sistema DEVE permitir regenerar a narrativa mantendo os dados do Step 1.
- **FR-016**: Sistema DEVE exibir tooltip com descrição do mecanismo ao hover sobre o dropdown.

**Persistência**

- **FR-017**: Sistema DEVE converter as opções selecionadas em valores numéricos usando o mapeamento do banco.
- **FR-018**: Sistema DEVE persistir os valores dos mecanismos no campo `scorecard_data.mechanisms` do experimento.
- **FR-019**: Mecanismos não selecionados (excluídos) DEVEM ter valor 0.0 persistido.

### Key Entities

- **MechanismDefinition**: Define um mecanismo de feature (ex: irreversibility). Contém chave única, label localizado, descrição. Possui múltiplas opções.

- **MechanismOption**: Uma opção textual para um mecanismo (ex: "totalmente reversível"). Contém label, valor numérico [0,1], ordem de exibição. Pertence a um MechanismDefinition.

- **FeatureType**: Categoria de feature que amplifica certos mecanismos (ex: financial amplifica irreversibility e institutional_trust). Contém chave, label, lista de mecanismos amplificados.

- **NarrativeTemplate**: Resultado da geração pela LLM. Contém o texto com placeholders, lista de mecanismos selecionados com opção default, lista de mecanismos excluídos, tipos inferidos.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 80% dos PMs conseguem configurar mecanismos no Step 2 em menos de 2 minutos (vs. tempo atual com sliders).

- **SC-002**: Taxa de abandono no Step 2 do wizard reduz em 30% comparado ao baseline com sliders.

- **SC-003**: Em pesquisa qualitativa, 70% dos PMs reportam que a narrativa ajuda a entender o impacto dos mecanismos na simulação.

- **SC-004**: 90% das narrativas geradas são consideradas "adequadas" ou "muito adequadas" pelos PMs (sem necessidade de regenerar).

- **SC-005**: Tempo de resposta da geração de narrativa é inferior a 5 segundos em 95% das requisições.

- **SC-006**: Sistema suporta adição de novos mecanismos ou opções sem necessidade de alteração de código.

## Assumptions

- Os 6 mecanismos existentes (irreversibility, network_effect, institutional_trust, habit_displacement, learning_curve, social_visibility) são suficientes para o MVP.
- Cada mecanismo terá 5 opções (correspondendo a valores 0.0, 0.25, 0.5, 0.75, 1.0).
- Os 5 tipos de feature (financial, social, aesthetic, flow, infra) cobrem as categorias relevantes para o domínio.
- A LLM (gpt-4o-mini) é capaz de inferir tipos e gerar narrativas adequadas em português.
- O prompt da LLM incluirá as definições de mecanismos e tipos carregadas do banco.

## Out of Scope

- Interface administrativa visual para gerenciar mecanismos (será feito via API/seeds).
- Geração de scorecard completo (complexidade, esforço inicial, risco percebido, tempo até valor) - mantém o fluxo atual ou será tratado em spec separada.
- Tradução para outros idiomas além de português.
- Histórico de narrativas geradas para um experimento.
- A/B testing entre interface de sliders e narrativa.
