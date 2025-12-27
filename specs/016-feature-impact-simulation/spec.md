# Feature Specification: Sistema de Simulacao de Impacto de Features

**Feature Branch**: `016-feature-impact-simulation`
**Created**: 2025-12-23
**Status**: Draft
**Input**: PRD detalhado para sistema de simulacao Monte Carlo que avalia impacto de features sobre diferentes perfis de synths

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Estender Gensynth com Atributos de Simulacao (Priority: P1)

Durante o processo de geracao de synths (gensynth), cada synth deve ser criado com atributos observaveis adicionais e variaveis latentes derivadas, permitindo uso direto em simulacoes de impacto.

**Atributos observaveis** (gerados via distribuicoes Beta, depois mapeados para campos existentes):
- `digital_literacy`: Beta(2,4) - maioria baixa-media → traduzido para `capacidades_tecnologicas.alfabetizacao_digital` (escala 0-100)
- `similar_tool_experience`: Beta(3,3) - distribuicao simetrica
- `motor_ability`: derivado de `deficiencias.motora.tipo` (nenhuma=1.0, leve=0.8, moderada=0.5, severa=0.2)
- `time_availability`: Beta(2,3) - maioria com pouco tempo
- `domain_expertise`: Beta(3,3) - simetrica

**Variaveis latentes** (derivadas automaticamente dos observaveis):
- `capability_mean`: 0.40*digital_literacy + 0.35*similar_tool_experience + 0.15*motor_ability + 0.10*domain_expertise
- `trust_mean`: 0.60*similar_tool_experience + 0.40*digital_literacy
- `friction_tolerance_mean`: 0.40*time_availability + 0.35*digital_literacy + 0.25*similar_tool_experience
- `exploration_prob`: 0.50*digital_literacy + 0.30*(1-similar_tool_experience) + 0.20*time_availability

**Why this priority**: Sem esses atributos no synth, nenhuma simulacao pode ser executada. Este e o fundamento de todo o sistema e deve estar integrado ao processo de geracao existente.

**Independent Test**: Pode ser testado gerando um synth via gensynth e verificando que o JSON resultante contem todos os atributos observaveis e latentes com valores no intervalo [0,1].

**Acceptance Scenarios**:

1. **Given** processo de gensynth em execucao, **When** um novo synth e criado, **Then** o JSON inclui secao `simulation_attributes` com observaveis gerados via Beta e latentes derivados
2. **Given** synth gerado, **When** usuario inspeciona JSON, **Then** ve atributos observaveis (digital_literacy, similar_tool_experience, motor_ability, time_availability, domain_expertise) e latentes (capability_mean, trust_mean, friction_tolerance_mean, exploration_prob)
3. **Given** `digital_literacy` gerado via Beta(2,4), **When** synth e finalizado, **Then** `capacidades_tecnologicas.alfabetizacao_digital` e populado com valor traduzido (0-100)
4. **Given** synth com `deficiencias.motora.tipo` definido, **When** synth e gerado, **Then** `motor_ability` e derivado da severidade da deficiencia (nenhuma=1.0, severa=0.2)

---

### User Story 2 - Criar Feature Scorecard (Priority: P1)

O product manager quer cadastrar um scorecard completo para uma feature, combinando input humano (descricao, midia) com assistencia de LLM (estimativas, justificativas, hipoteses).

**Estrutura do Scorecard:**

1. **Identificacao** (humano)
   - Nome da feature
   - Cenario de uso
   - Data de criacao
   - Avaliadores (Produto, UX, Engenharia)
   - Descricao rica (texto, video, fotos)

2. **Dimensoes com scores** (humano + LLM)
   - Complexity [0,1]: com regras objetivas aplicadas (ex: "2 conceitos novos", "estados invisiveis")
   - Initial Effort [0,1]: com regras (ex: "uso imediato sem configuracao")
   - Perceived Risk [0,1]: com regras (ex: "afeta dados mas e reversivel")
   - Time to Value [0,1]: com regras (ex: "valor percebido no primeiro erro")

3. **Justificativa curta** (LLM-assistido)
   - Texto explicando o racional dos scores

4. **Incerteza assumida** (humano + LLM)
   - Intervalos [min, max] para cada dimensao

5. **Output para simulacao** (calculado)
   - Formato estruturado para uso direto na simulacao

6. **Insights esperados** (LLM-assistido)
   - Hipoteses pre-simulacao sobre quais grupos serao afetados
   - Sugestoes de ajustes que podem mudar o resultado

**Why this priority**: O scorecard e a entrada principal da simulacao - sem ele, nao ha como quantificar a feature a ser avaliada.

**Independent Test**: Pode ser testado criando um scorecard completo e verificando que todas as secoes estao preenchidas, scores tem regras objetivas associadas, e LLM gera justificativas e hipoteses coerentes.

**Acceptance Scenarios**:

1. **Given** PM inicia criacao de scorecard, **When** preenche identificacao e descricao (texto/video/fotos), **Then** sistema aceita midia e persiste
2. **Given** PM define scores das dimensoes, **When** seleciona regras objetivas aplicaveis, **Then** sistema associa regras aos scores como evidencia
3. **Given** scores definidos, **When** PM solicita assistencia LLM, **Then** sistema gera justificativa curta e hipoteses de impacto
4. **Given** PM define intervalos de incerteza, **When** min > max ou valores fora de [0,1], **Then** sistema rejeita com erro claro
5. **Given** scorecard completo, **When** PM salva, **Then** sistema gera output estruturado para simulacao e permite exportar JSON

---

### User Story 3 - Executar Simulacao de Impacto (Priority: P1)

O product manager quer executar uma simulacao Monte Carlo para avaliar como uma feature impacta diferentes segmentos da populacao de synths, gerando outcomes (did_not_try, failed, success) para cada synth.

**Mecanica da simulacao:**

Para cada synth, em cada execucao:
1. **Amostrar estado** via `sample_user_state(synth.latent_traits, scenario, sigma)`:
   - capability = Normal(capability_mean, sigma) + cenario ajustes
   - trust = Normal(trust_mean, sigma) + scenario.trust_modifier
   - friction_tolerance = Normal(friction_tolerance_mean, sigma) + scenario.friction_modifier + criticality_boost
   - motivation = Normal(0.5, 0.15) + scenario.motivation_modifier + criticality_boost
   - exploration = Bernoulli(exploration_prob * (1 - scenario.task_criticality * 0.5))

2. **Calcular probabilidade de tentativa** (modelo multiplicativo):
   - motivation_factor = sigmoid(motivation - feature.initial_effort)
   - trust_factor = sigmoid(trust - feature.perceived_risk)
   - friction_factor = sigmoid(friction_tolerance - feature.complexity * 0.5)
   - p_attempt = motivation_factor * trust_factor * friction_factor * exploration_boost

3. **Calcular probabilidade de sucesso** (se tentou):
   - capability_match = sigmoid(capability - feature.complexity)
   - patience_match = sigmoid(patience - feature.time_to_value)
   - p_success = capability_match * patience_match

4. **Amostrar outcome**: did_not_try | failed | success

**Why this priority**: Esta e a funcionalidade central do sistema - sem simulacao, nao ha insights.

**Independent Test**: Pode ser testado executando simulacao com 500 synths x 100 execucoes e verificando que outcomes sao gerados para todos os synths com proporcoes validas [0,1].

**Acceptance Scenarios**:

1. **Given** populacao de synths e scorecard de feature, **When** PM executa simulacao com cenario baseline, **Then** sistema gera outcomes agregados por synth em segundos (nao minutos)
2. **Given** simulacao em execucao, **When** PM monitora progresso, **Then** ve indicador de progresso e tempo estimado
3. **Given** simulacao concluida, **When** PM visualiza resultados, **Then** ve proporcoes de did_not_try, failed, success para cada synth
4. **Given** mesmo synth e mesma seed, **When** executa multiplas vezes, **Then** resultados sao identicos (reproducibilidade)

---

### User Story 4 - Analisar Resultados por Regiao do Espaco (Priority: P2)

O product manager quer identificar quais regioes do espaco de synths se beneficiam ou sofrem com a feature, descobrindo grupos emergentes baseados em combinacoes de variaveis.

**Why this priority**: Transformar dados brutos em insights acionaveis e o valor principal do sistema, mas depende da simulacao estar funcionando.

**Independent Test**: Pode ser testado analisando resultados de simulacao e verificando que grupos emergentes sao identificados com regras claras (ex: capability < 0.5 AND trust < 0.4 -> falha > 50%).

**Acceptance Scenarios**:

1. **Given** resultados de simulacao, **When** PM solicita analise por regiao, **Then** sistema identifica grupos com altas taxas de falha ou nao-tentativa
2. **Given** grupos identificados, **When** PM visualiza detalhes, **Then** ve regras claras (ex: "capability < 0.48 AND complexity > 0.6 -> falha > 55%")
3. **Given** analise completa, **When** PM exporta insights, **Then** recebe formato estruturado com grupos, taxas e recomendacoes

---

### User Story 5 - Comparar Resultados entre Cenarios (Priority: P2)

O product manager quer comparar como a mesma feature performa em diferentes situacoes de uso, utilizando cenarios pre-definidos em JSON.

**Estrutura de um Cenario (JSON):**

```json
{
  "id": "baseline",
  "name": "Baseline",
  "description": "Condicoes tipicas de uso",
  "motivation_modifier": 0,
  "trust_modifier": 0,
  "friction_modifier": 0,
  "task_criticality": 0.5
}
```

**Cenarios pre-definidos disponiveis:**

| Cenario | motivation | trust | friction | criticality | Descricao |
|---------|------------|-------|----------|-------------|-----------|
| baseline | 0 | 0 | 0 | 0.5 | Condicoes tipicas de uso |
| crisis | +0.2 | -0.1 | -0.15 | 0.85 | Urgencia, precisa resolver rapido |
| first-use | +0.1 | -0.2 | 0 | 0.2 | Exploracao inicial do produto |

**Nota sobre task_criticality:** Representa a situacao, nao o synth. Um contador e um estagiario podem ambos estar em cenario de "crise" com alta criticality, ou em cenario de "exploracao" com baixa criticality.

**Why this priority**: Cenarios revelam como a feature se comporta em condicoes variadas, mas e uma extensao da simulacao basica.

**Independent Test**: Pode ser testado executando a mesma feature em 3 cenarios diferentes e comparando distribuicoes de outcomes.

**Acceptance Scenarios**:

1. **Given** sistema inicializado, **When** PM lista cenarios, **Then** ve cenarios pre-definidos (baseline, crisis, first-use) disponiveis como JSON
2. **Given** feature scorecard, **When** PM executa simulacao selecionando um cenario, **Then** sistema aplica modificadores do cenario
3. **Given** feature scorecard, **When** PM executa simulacao com multiplos cenarios, **Then** ve resultados lado a lado
4. **Given** resultados multi-cenario, **When** PM analisa diferencas, **Then** identifica quais grupos de synths sao mais sensiveis a contexto

---

### User Story 6 - Explorar Sensibilidade de Variaveis (Priority: P3)

O product manager quer entender qual variavel do scorecard tem maior impacto no resultado, variando uma por vez e observando o delta.

**Why this priority**: Analise de sensibilidade ajuda a priorizar ajustes de design, mas e refinamento apos insights iniciais.

**Independent Test**: Pode ser testado variando complexity em +/-0.1 e verificando que o delta de outcomes e calculado corretamente.

**Acceptance Scenarios**:

1. **Given** resultados de simulacao, **When** PM seleciona variavel para analise de sensibilidade, **Then** sistema mostra impacto de variar +/-0.05 e +/-0.1
2. **Given** analise de sensibilidade, **When** PM compara variaveis, **Then** ve ranking de quais tem maior efeito
3. **Given** variavel com alto impacto identificada, **When** PM ajusta scorecard, **Then** pode re-simular e comparar

---

### User Story 7 - Registrar Decisoes e Premissas (Priority: P3)

O product manager quer manter um log auditavel de todos os scorecards, simulacoes e decisoes tomadas para referencia futura e discussoes em equipe.

**Why this priority**: Auditabilidade e importante para decisoes de produto, mas nao bloqueia uso inicial do sistema.

**Independent Test**: Pode ser testado criando scorecard, executando simulacao, e verificando que todas as acoes sao registradas com timestamp.

**Acceptance Scenarios**:

1. **Given** qualquer acao no sistema (criar scorecard, simular, analisar), **When** acao e executada, **Then** e registrada no assumption log com timestamp
2. **Given** log com historico, **When** PM busca por feature ou data, **Then** encontra todas as decisoes relacionadas
3. **Given** decisao passada, **When** PM quer revisar premissas, **Then** ve scorecard original e justificativas usadas

---

### Edge Cases

- O que acontece quando um synth tem todos os atributos observaveis em zero? Sistema deve calcular variaveis latentes como zero e incluir nos alertas de sanity check
- O que acontece quando scorecard tem intervalo invertido (min > max)? Sistema deve rejeitar com erro claro
- Como sistema lida com populacao vazia (nenhum synth no banco)? Deve informar que nao ha synths para simular
- O que acontece se simulacao e interrompida no meio? Resultados parciais nao devem ser salvos como completos
- O que acontece se PM seleciona cenario inexistente? Sistema deve retornar erro com lista de cenarios validos

## Requirements *(mandatory)*

### Functional Requirements

**Extensao do Gensynth**
- **FR-001**: Gensynth DEVE gerar atributos observaveis (digital_literacy, similar_tool_experience, time_availability, domain_expertise) usando distribuicoes Beta configuradas durante criacao de cada synth
- **FR-002**: Gensynth DEVE traduzir `digital_literacy` [0,1] para `capacidades_tecnologicas.alfabetizacao_digital` (escala 0-100) apos geracao
- **FR-003**: Gensynth DEVE derivar `motor_ability` a partir de `deficiencias.motora.tipo` (nenhuma=1.0, leve=0.8, moderada=0.5, severa=0.2)
- **FR-004**: Gensynth DEVE calcular variaveis latentes (capability_mean, trust_mean, friction_tolerance_mean, exploration_prob) usando funcao de derivacao com pesos configurados
- **FR-005**: Gensynth DEVE armazenar todos os atributos de simulacao em secao `simulation_attributes` do JSON do synth
- **FR-006**: Sistema DEVE validar que todos os valores de atributos estao no intervalo [0,1]

**Feature Scorecard**
- **FR-007**: Sistema DEVE permitir cadastrar identificacao da feature (nome, cenario, data, avaliadores)
- **FR-008**: Sistema DEVE aceitar descricao rica com texto, videos e fotos
- **FR-009**: Sistema DEVE permitir definir scores [0,1] para cada dimensao (complexity, initial_effort, perceived_risk, time_to_value) com regras objetivas associadas
- **FR-010**: Sistema DEVE fornecer catalogo de regras objetivas pre-definidas para cada dimensao (ex: "conceitos novos", "estados invisiveis", "afeta dados")
- **FR-011**: Sistema DEVE permitir definir intervalos de incerteza [min, max] para cada dimensao e validar que min <= max e valores em [0,1]
- **FR-012**: Sistema DEVE integrar com LLM para gerar justificativa curta baseada nos scores e regras selecionadas
- **FR-013**: Sistema DEVE integrar com LLM para gerar hipoteses de impacto pre-simulacao (quais grupos serao afetados, sugestoes de ajustes)
- **FR-014**: Sistema DEVE gerar output estruturado para simulacao a partir do scorecard completo
- **FR-015**: Sistema DEVE armazenar scorecards em formato exportavel (JSON) e permitir versionamento

**Cenarios**
- **FR-016**: Sistema DEVE fornecer cenarios pre-definidos em JSON (baseline, crisis, first-use) com modificadores e criticality configurados
- **FR-017**: Sistema DEVE permitir selecionar um ou mais cenarios pre-definidos para execucao de simulacao
- **FR-018**: Sistema DEVE aplicar modificadores do cenario ao estado do synth durante sample_user_state:
  - trust += scenario.trust_modifier
  - friction_tolerance += scenario.friction_modifier + (criticality * 0.1)
  - motivation += scenario.motivation_modifier + (criticality * 0.2)
  - exploration_prob *= (1 - criticality * 0.5)

**Simulacao**
- **FR-019**: Sistema DEVE executar simulacao Monte Carlo com N synths x M execucoes configuravel
- **FR-020**: Sistema DEVE calcular probabilidade de tentativa baseado em modelo multiplicativo (motivacao vs esforco, confianca vs risco, tolerancia vs complexidade)
- **FR-021**: Sistema DEVE calcular probabilidade de sucesso dado que tentou (capability vs complexidade, paciencia vs tempo ate valor)
- **FR-022**: Sistema DEVE amostrar estado do synth com ruido controlado (sigma configuravel) sobre variaveis latentes
- **FR-023**: Sistema DEVE produzir outcomes discretos (did_not_try, failed, success) para cada execucao
- **FR-024**: Sistema DEVE agregar outcomes por synth como proporcoes [0,1]

**Analise**
- **FR-025**: Sistema DEVE identificar regioes do espaco de synths com altas taxas de falha ou nao-tentativa
- **FR-026**: Sistema DEVE expressar grupos emergentes como regras interpretaveis (ex: "capability < X AND Y > Z")
- **FR-027**: Sistema DEVE permitir comparacao de resultados entre cenarios diferentes
- **FR-028**: Sistema DEVE calcular analise de sensibilidade variando uma dimensao do scorecard por vez

**Verificacao**
- **FR-029**: Sistema DEVE verificar estabilidade re-executando simulacao com seeds diferentes
- **FR-030**: Sistema DEVE verificar anti-dominancia (nenhuma variavel explica >85% da variancia)

**Auditabilidade**
- **FR-031**: Sistema DEVE registrar todas as acoes em log com timestamp
- **FR-032**: Sistema DEVE permitir busca no historico por feature ou periodo

### Key Entities

- **Synth**: Persona sintetica com schema existente MAIS nova secao `simulation_attributes` contendo:
  - Observaveis: digital_literacy, similar_tool_experience, motor_ability, time_availability, domain_expertise (todos [0,1])
  - Latentes derivados: capability_mean, trust_mean, friction_tolerance_mean, exploration_prob (todos [0,1])
- **SynthPopulation**: Colecao de synths carregados do banco para simulacao, com estatisticas agregadas calculadas em tempo de execucao
- **FeatureScorecard**: Cadastro completo de uma feature contendo:
  - Identificacao: nome, cenario, data, avaliadores
  - Descricao rica: texto, videos, fotos
  - Dimensoes: scores [0,1] com regras objetivas associadas (complexity, initial_effort, perceived_risk, time_to_value)
  - Incerteza: intervalos [min, max] para cada dimensao
  - Justificativa: texto gerado/assistido por LLM
  - Hipoteses: insights pre-simulacao gerados por LLM
  - Output: formato estruturado para simulacao
- **Scenario**: Contexto de uso pre-definido em JSON contendo:
  - Identificacao: id, nome, descricao
  - Modificadores: motivation_modifier, trust_modifier, friction_modifier (todos [-0.3, +0.3])
  - Task criticality: [0,1] representando urgencia/importancia da tarefa no cenario (nao do synth)
  - Tres cenarios disponiveis: baseline (neutro), crisis (urgencia alta), first-use (exploracao)
- **SimulationRun**: Execucao de simulacao com parametros (populacao, scorecard, cenario, execucoes) e resultados agregados
- **SynthOutcome**: Resultado por synth com proporcoes de did_not_try, failed, success
- **RegionAnalysis**: Grupo emergente identificado com regra interpretavel e metricas de impacto
- **AssumptionLog**: Registro historico de scorecards, simulacoes e decisoes com timestamps

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Cada synth gerado via gensynth inclui automaticamente todos os atributos de simulacao (9 campos) com valores validos [0,1]
- **SC-002**: Sistema identifica grupos de synths com taxas de falha > 50% com regras interpretaveis em linguagem natural
- **SC-003**: Simulacao de 500 synths x 100 execucoes completa em menos de 30 segundos
- **SC-004**: 100% das decisoes de design sao documentadas com justificativas rastreaveis no assumption log
- **SC-005**: Analise de sensibilidade revela qual variavel do scorecard tem maior impacto em menos de 10 segundos
- **SC-006**: PMs conseguem comparar 3 cenarios lado a lado e identificar diferencas significativas
- **SC-007**: Re-execucoes da mesma simulacao com mesmo seed produzem resultados identicos (reproducibilidade 100%)
- **SC-008**: Sistema reduz tempo de discussoes subjetivas sobre impacto de features em 50% (medido por feedback qualitativo)
- **SC-009**: 80% dos insights gerados sao considerados "acionaveis" pelos PMs (medido por survey pos-uso)

## Assumptions

- Atributos de simulacao sao gerados automaticamente durante gensynth, nao requerem input manual
- `digital_literacy` e gerado via Beta(2,4) e depois traduzido para `capacidades_tecnologicas.alfabetizacao_digital` (escala 0-100)
- `motor_ability` e derivado de `deficiencias.motora.tipo` que ja existe no schema (conexao com acessibilidade)
- Novos atributos (similar_tool_experience, time_availability, domain_expertise) serao gerados via distribuicoes Beta
- Pesos para derivacao de variaveis latentes serao os definidos no PRD inicialmente, mas configuraveis para ajuste futuro
- Interface inicial sera via CLI/scripts Python, sem UI rica
- Cenarios sao pre-definidos em JSON (baseline, crisis, first-use) - nao ha cadastro de cenarios customizados no MVP
- Sigma padrao de 0.05 para ruido sobre variaveis latentes em estado de execucao
- Schema do synth sera estendido com nova secao `simulation_attributes` (versao v1.1.0)
