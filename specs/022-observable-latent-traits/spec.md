# Feature Specification: Observable vs. Latent Traits Model

**Feature Branch**: `022-observable-latent-traits`
**Created**: 2025-12-29
**Status**: Draft
**Input**: Refatorar modelo de synths para separar claramente características observáveis de latentes, melhorando coerência entre simulações e entrevistas

---

## Contexto do Problema

O sistema atual de synths possui atributos de simulação (`simulation_attributes`) que misturam dois tipos distintos de informação:

1. **Características Observáveis**: Atributos que um PM (Product Manager) pode identificar em uma pessoa real para recrutar para entrevistas (ex: literacia digital, experiência com ferramentas similares)

2. **Características Latentes**: Traços derivados matematicamente que influenciam o comportamento em simulações, mas não são diretamente observáveis (ex: capability_mean, trust_mean)

**Problemas atuais:**
- O frontend exibe variáveis latentes que o PM não consegue usar para encontrar equivalentes humanos
- As entrevistas não recebem contexto das simulações (taxas de sucesso/falha)
- Não há conexão clara entre atributos demográficos (idade, escolaridade, PCD) e os atributos observáveis
- O PM não consegue descrever um synth de forma que encontre uma pessoa real equivalente

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Entender Perfil de Synth para Recrutamento (Priority: P1)

Como PM, quero ver as características observáveis de um synth em linguagem clara para que eu possa recrutar uma pessoa real equivalente para validar as descobertas.

**Why this priority**: Este é o objetivo principal da feature - permitir que PMs encontrem humanos equivalentes aos synths para entrevistas reais. Sem isso, os synths ficam abstratos demais para uso prático.

**Independent Test**: Pode ser testado visualizando um synth no frontend e verificando que todas as características exibidas são observáveis e descritas de forma que permitam encontrar uma pessoa equivalente.

**Acceptance Scenarios**:

1. **Given** um synth gerado, **When** visualizo seus detalhes no frontend, **Then** vejo apenas características observáveis com valores numéricos [0-1] E descrições textuais curtas (ex: "Literacia Digital: 0.35 - Baixa familiaridade com tecnologia")

2. **Given** um synth com características observáveis exibidas, **When** leio a descrição, **Then** consigo identificar critérios de recrutamento claros (ex: "pessoa com baixa experiência digital, sem deficiências motoras, com pouco tempo disponível")

3. **Given** um synth gerado, **When** visualizo seus detalhes, **Then** NÃO vejo variáveis latentes (capability_mean, trust_mean, etc.) na interface

---

### User Story 2 - Coerência entre Simulação e Entrevista (Priority: P1)

Como PM, quero que o synth em uma entrevista tenha consciência de seu desempenho na simulação prévia para que suas respostas sejam coerentes com seu comportamento simulado.

**Why this priority**: Sem essa conexão, simulações e entrevistas são mundos separados. O synth pode responder "adoro usar o produto" mesmo tendo falhado 80% das vezes na simulação.

**Independent Test**: Pode ser testado executando uma simulação, depois uma entrevista com o mesmo synth, e verificando que as respostas da entrevista refletem o desempenho na simulação.

**Acceptance Scenarios**:

1. **Given** um synth que teve 80% de falhas em uma simulação, **When** inicio uma entrevista ligada a essa simulação, **Then** o system prompt do entrevistado inclui "Taxa de sucesso: 20%, Taxa de falha: 80%, Taxa de não-tentativa: 0%"

2. **Given** um synth que não tentou usar a feature em 60% das simulações, **When** ele é entrevistado, **Then** suas respostas refletem hesitação/desinteresse consistente com a baixa taxa de tentativa

3. **Given** uma entrevista conectada a uma simulação, **When** o synth responde perguntas, **Then** as respostas são coerentes com suas características observáveis E seu desempenho na simulação

---

### User Story 3 - Geração de Observáveis a partir de Demográficos (Priority: P2)

Como sistema, preciso derivar atributos observáveis a partir de características demográficas (idade, escolaridade, PCD) usando distribuições Beta ajustadas para manter coerência estatística.

**Why this priority**: Isso garante que os atributos observáveis façam sentido em relação ao perfil demográfico do synth. Uma pessoa idosa com baixa escolaridade não deveria ter alta literacia digital por padrão.

**Independent Test**: Pode ser testado gerando múltiplos synths e verificando que a distribuição de atributos observáveis correlaciona corretamente com os demográficos.

**Acceptance Scenarios**:

1. **Given** um synth com escolaridade alta, **When** gerado, **Then** `digital_literacy` é amostrado de Beta com parâmetros ajustados pela escolaridade (maior escolaridade → distribuição deslocada para valores mais altos)

2. **Given** um synth com deficiência motora severa, **When** gerado, **Then** `motor_ability` é amostrado de Beta com parâmetros ajustados pela severidade (maior severidade → distribuição deslocada para valores mais baixos). Aqui pode ser debilidade motora, mas também visual.

3. **Given** configuração de população, **When** gero 100 synths, **Then** a distribuição de observáveis reflete as correlações esperadas com idade, escolaridade e deficiências

---

### User Story 4 - Exibição Textual de Características (Priority: P2)

Como PM, quero ver cada característica observável com um label descritivo além do valor numérico para entender rapidamente o perfil do synth.

**Why this priority**: Valores numéricos como "0.35" são abstratos. Labels como "Baixa" ou "Alta" tornam a informação imediatamente compreensível.

**Independent Test**: Pode ser testado verificando que cada valor numérico [0-1] tem um label correspondente na interface.

**Acceptance Scenarios**:

1. **Given** um atributo observável com valor 0.2, **When** exibido, **Then** mostra label "Muito Baixo" (0-0.2)

2. **Given** um atributo observável com valor 0.5, **When** exibido, **Then** mostra label "Médio" (0.4-0.6)

3. **Given** um atributo observável com valor 0.9, **When** exibido, **Then** mostra label "Muito Alto" (0.8-1.0)

---

### User Story 5 - Derivação Transparente de Latentes (Priority: P3)

Como desenvolvedor/pesquisador, quero que as variáveis latentes sejam calculadas de forma transparente a partir das observáveis com pesos documentados.

**Why this priority**: Permite auditoria e ajuste fino do modelo de simulação. Não impacta diretamente o PM, mas é essencial para manutenção e evolução do sistema.

**Independent Test**: Pode ser testado calculando manualmente as variáveis latentes a partir das observáveis e comparando com os valores do sistema.

**Acceptance Scenarios**:

1. **Given** um synth com observáveis conhecidas, **When** calculo `capability_mean` manualmente usando a fórmula documentada, **Then** o valor corresponde ao armazenado no sistema

2. **Given** mudança nos pesos de derivação, **When** regenero latentes, **Then** os valores são recalculados corretamente

---

### Edge Cases

- O que acontece quando um synth não tem simulação prévia durante entrevista? Resposta: entrevista procede sem contexto de simulação, usando apenas características observáveis e demográficos
- Como o sistema lida com valores extremos (0.0 ou 1.0) nos observáveis? Resposta: clamp garante [0,1], labels cobrem extremos
- O que acontece se um synth antigo não tem os novos atributos observáveis? Resposta: migração calcula valores a partir dos dados existentes

---

## Requirements *(mandatory)*

### Functional Requirements

#### Modelo de Dados

- **FR-001**: Sistema DEVE separar `simulation_attributes` em dois grupos distintos: `observables` (5 atributos) e `latent_traits` (4 atributos derivados)

- **FR-002**: Sistema DEVE manter os 5 atributos observáveis:
  - `digital_literacy`: [0,1] - Familiaridade com tecnologia
  - `similar_tool_experience`: [0,1] - Experiência com ferramentas similares
  - `motor_ability`: [0,1] - Capacidade motora/física
  - `time_availability`: [0,1] - Tempo disponível típico
  - `domain_expertise`: [0,1] - Conhecimento do domínio do produto

- **FR-003**: Sistema DEVE manter os 4 atributos latentes (derivados):
  - `capability_mean`: derivado de digital_literacy, similar_tool_experience, motor_ability, domain_expertise
  - `trust_mean`: derivado de similar_tool_experience, digital_literacy
  - `friction_tolerance_mean`: derivado de time_availability, digital_literacy, similar_tool_experience
  - `exploration_prob`: derivado de digital_literacy, similar_tool_experience, time_availability

- **FR-004**: Sistema NÃO DEVE remover nenhuma variável usada atualmente nas simulações (backward compatibility)

#### Geração de Observáveis

- **FR-005**: Sistema DEVE gerar `digital_literacy` usando distribuição Beta com parâmetros ajustados pela escolaridade do synth

- **FR-006**: Sistema DEVE gerar `motor_ability` usando distribuição Beta com parâmetros ajustados pelo tipo de deficiência motora (nenhuma → alta, severa → baixa)

- **FR-007**: Sistema DEVE gerar `time_availability` usando distribuição Beta com parâmetros ajustados por fatores como composição familiar e ocupação

- **FR-008**: Sistema DEVE gerar `similar_tool_experience` e `domain_expertise` usando distribuições Beta simétricas (3,3) como baseline, podendo ser ajustadas por ocupação/interesses

#### Derivação de Latentes

- **FR-009**: Sistema DEVE calcular `capability_mean` como combinação ponderada de digital_literacy (40%), similar_tool_experience (35%), motor_ability (15%), domain_expertise (10%)

- **FR-010**: Sistema DEVE calcular `trust_mean` como combinação ponderada de similar_tool_experience (60%), digital_literacy (40%)

- **FR-011**: Sistema DEVE calcular `friction_tolerance_mean` como combinação ponderada de time_availability (40%), digital_literacy (35%), similar_tool_experience (25%)

- **FR-012**: Sistema DEVE calcular `exploration_prob` como combinação ponderada de digital_literacy (50%), inverso de similar_tool_experience (30%), time_availability (20%)

#### Frontend

- **FR-013**: Frontend DEVE exibir APENAS atributos observáveis na visualização de synths

- **FR-014**: Frontend DEVE exibir cada atributo observável com:
  - Nome do atributo em português
  - Valor numérico [0-1]
  - Label textual (Muito Baixo/Baixo/Médio/Alto/Muito Alto)
  - Descrição curta do que significa

- **FR-015**: Frontend NÃO DEVE exibir variáveis latentes para o usuário final (PM)

#### Entrevistas

- **FR-016**: Sistema DEVE passar para o system prompt do entrevistado:
  - Todas as características observáveis com valores e descrições
  - Taxa de tentativa, sucesso e falha da simulação conectada (se houver)

- **FR-017**: Sistema DEVE incluir no prompt do entrevistado instruções para comportar-se de forma coerente com seu desempenho na simulação

- **FR-018**: Sistema DEVE permitir entrevistas sem simulação prévia (usando apenas observáveis e demográficos)

#### Migração

- **FR-019**: Sistema DEVE migrar synths existentes para o novo formato, calculando observáveis a partir dos dados atuais quando possível

---

### Key Entities

- **SimulationObservables**: Conjunto de 5 atributos diretamente observáveis/inferíveis de uma pessoa real. Valores [0,1]. Gerados via distribuições Beta ajustadas por demográficos.

- **SimulationLatentTraits**: Conjunto de 4 atributos derivados matematicamente das observáveis. Usados internamente para cálculos de probabilidade nas simulações. Não expostos ao usuário.

- **ObservableLabel**: Mapeamento de valores numéricos para labels textuais e descrições em português. Cinco níveis: Muito Baixo (0-0.2), Baixo (0.2-0.4), Médio (0.4-0.6), Alto (0.6-0.8), Muito Alto (0.8-1.0).

- **SimulationContext**: Contexto de simulação passado para entrevistas, incluindo taxas de tentativa/sucesso/falha do synth específico.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: PM consegue descrever critérios de recrutamento para encontrar pessoa equivalente a um synth em menos de 2 minutos olhando a interface

- **SC-002**: 100% dos atributos exibidos no frontend são observáveis (nenhuma variável latente visível)

- **SC-003**: Respostas de entrevista refletem coerência com desempenho em simulação prévia (validado por revisão qualitativa de 10 entrevistas)

- **SC-004**: Correlação estatística entre demográficos e observáveis mantida em geração de 100+ synths (ex: escolaridade alta correlaciona com digital_literacy médio-alto)

- **SC-005**: Zero breaking changes em simulações existentes (todas as variáveis atuais mantidas, resultados consistentes)

- **SC-006**: Migração de synths existentes executada sem perda de dados

---

## Assumptions

1. **Pesos de derivação são fixos inicialmente**: Os pesos usados para calcular latentes a partir de observáveis (40%, 35%, etc.) são valores iniciais baseados em hipóteses razoáveis. Podem ser ajustados no futuro com dados reais.

2. **Parâmetros Beta são configurações do modelo**: Os parâmetros das distribuições Beta são configurações do modelo de geração, não constantes universais.

3. **Labels em português**: Interface em português brasileiro, consistente com o resto do sistema.

4. **Simulação prévia é opcional para entrevistas**: Entrevistas podem acontecer sem simulação prévia, usando apenas o perfil do synth.

5. **Backward compatibility é mandatória**: Nenhuma simulação existente pode quebrar. Todas as variáveis atuais devem continuar funcionando.

---

## Out of Scope

- Alteração dos pesos de derivação de latentes via interface (configuração futura)
- Exposição de latentes para pesquisadores avançados (feature futura separada)
- Validação estatística formal das correlações demográficos→observáveis (pesquisa futura)
- Internacionalização dos labels (sistema já é em português)
