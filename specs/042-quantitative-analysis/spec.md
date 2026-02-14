# Feature Specification: Análise Quantitativa (Modelagem Causal + Monte Carlo)

**Feature Branch**: `042-quantitative-analysis`
**Created**: 2026-02-14
**Status**: Draft
**Input**: Adaptar o fluxo de análise quantitativa do experiment-simulator-v5.jsx para o synth-lab, com modelagem causal (DAG) e simulação Monte Carlo integradas ao experimento.
**Referência**: `specs/experiment-simulator-v5.jsx` — contém prompts LLM, lógica de simulação e componentes visuais que servem de base.

## Clarifications

### Session 2026-02-14

- Q: Como o questionário de campo se relaciona com o interview_guide? → A: Fusão direta — questionário alimenta os campos `context_definition`, `questions`, `context_examples` da tabela `interview_guide`.
- Q: Layout — tudo na Modelagem ou duas abas? → A: Tudo na aba "Análise Quanti" (fluxo linear único). A aba "Modelagem" não existe.
- Q: userVars — demographics ou sensitivities? → A: Híbrido 10 userVars — 7 demográficas (ageNorm, incomeNorm, eduNorm, familySizeNorm, hasVisualDisab, hasMotorDisab, digitalCapability) + 3 sensitivities (risk_aversion, institutional_trust_level, friction_tolerance).
- Q: Interview guide auto-salvar ou com confirmação? → A: Auto-salvar silenciosamente após simulação.
- Q: Quantitativa substitui o gerador existente de interview_guide? → A: Sim, sobrescreve silenciosamente. `InterviewGuideGeneratorService` agora é chamado apenas pela análise quantitativa (não mais na criação do experimento). Prompt do JSX (QUESTIONNAIRE_SYSTEM) é a base, adaptado para os campos da tabela `interview_guide`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Gerar Modelo Causal a partir do Experimento (Priority: P1)

O PM acessa a aba "Análise Quanti" de um experimento existente e clica em "Gerar Modelo". O sistema usa o título, hipótese e descrição do experimento como input para o LLM (gpt-5.1) usando o prompt DAG_SYSTEM (ver Apêndice A), que retorna um DAG causal com 7-10 nós e 7-10 arestas. O DAG é exibido visualmente com nós em 3 camadas (demográficos → mediadores → outcome). Cada aresta vira uma afirmação com 5 opções Likert que o PM avalia.

**Why this priority**: Sem o modelo causal, nenhuma simulação ou análise é possível. É o alicerce de toda a feature.

**Independent Test**: Pode ser testado criando um experimento, gerando o modelo, e verificando que o DAG aparece com nós, arestas e opções Likert.

**Acceptance Scenarios**:

1. **Given** um experimento com título e hipótese preenchidos, **When** PM clica "Gerar Modelo" na aba Análise Quanti, **Then** o sistema exibe um DAG causal com 7-10 nós e 7-10 arestas, cada aresta com 5 opções Likert em português.
2. **Given** um modelo causal gerado, **When** PM seleciona uma opção Likert para uma aresta, **Then** a visualização do DAG atualiza a espessura e cor da aresta correspondente (grossura = intensidade, azul = relação direta, laranja = relação inversa).
3. **Given** um modelo causal com seleções do PM, **When** PM sai da página e volta, **Then** as seleções anteriores estão preservadas.

---

### User Story 2 - Rodar Simulação e Ver Resultados (Priority: P2)

Após calibrar o modelo (respondendo as afirmações Likert), o PM clica em "Simular" (na mesma aba, abaixo das Likerts). O sistema roda uma simulação Monte Carlo server-side (3.000 cenários × synths do grupo) e exibe na mesma página, abaixo:
- **Distribuição**: histograma + estatísticas (média, mediana, IC 80%, desvio)
- **Segmentos**: adoção por idade (18-29, 30-49, 50+), renda (baixa, média, alta) e escolaridade (baixa, média, alta)
- **Sensibilidade**: barras ordenadas por impacto de cada premissa

Cada seção recebe uma interpretação contextualizada gerada pelo LLM (gpt-4o-mini) usando o prompt INTERP_SYSTEM (ver Apêndice B), em paralelo.

**Why this priority**: A simulação é o produto principal — transforma premissas subjetivas em estimativas quantitativas com intervalos de confiança.

**Independent Test**: Com um modelo já calibrado, rodar simulação e verificar que as 3 seções de resultado aparecem com dados numéricos e interpretações.

**Acceptance Scenarios**:

1. **Given** um modelo causal com todas as arestas respondidas, **When** PM clica "Simular", **Then** o sistema exibe distribuição (histograma + stats), segmentos (9 cards), sensibilidade (barras por impacto) — tudo na mesma página abaixo do modelo.
2. **Given** resultados de simulação exibidos, **When** as interpretações AI terminam de carregar, **Then** cada seção (distribuição, segmentos, sensibilidade) mostra uma interpretação contextualizada em português que referencia o experimento.
3. **Given** o PM altera uma seleção Likert no modelo, **When** roda a simulação novamente, **Then** os resultados refletem a mudança nas premissas.

---

### User Story 3 - Gerar Interview Guide automaticamente (Priority: P3)

Após a simulação completar, o sistema automaticamente gera o `interview_guide` do experimento usando o `InterviewGuideGeneratorService` com um prompt baseado no QUESTIONNAIRE_SYSTEM (ver Apêndice C), adaptado para preencher os campos da tabela `interview_guide` (`context_definition`, `questions`, `context_examples`). O conteúdo é baseado nas 3 premissas mais impactantes da análise de sensibilidade. O interview_guide é salvo automaticamente no banco, sobrescrevendo qualquer guide anterior.

**Why this priority**: Conecta a análise quantitativa diretamente ao pipeline de entrevistas existente — o PM pode rodar entrevistas com synths imediatamente após a simulação.

**Independent Test**: Com resultados de simulação prontos, verificar que o interview_guide do experimento foi criado/atualizado no banco com os 3 campos preenchidos.

**Acceptance Scenarios**:

1. **Given** simulação completou com análise de sensibilidade, **When** resultados são exibidos, **Then** o interview_guide do experimento é automaticamente salvo no banco com `context_definition`, `questions` e `context_examples` preenchidos a partir das 3 premissas mais sensíveis.
2. **Given** o experimento já tinha um interview_guide, **When** simulação completa, **Then** o guide anterior é sobrescrito silenciosamente pelo novo.
3. **Given** o interview_guide foi gerado, **When** PM navega para a aba de entrevistas, **Then** pode criar entrevistas com synths usando o guide gerado pela análise quantitativa.

---

### Edge Cases

- **Experimento sem descrição**: usar apenas título + hipótese como input para o LLM. O modelo gerado pode ser menos rico, mas deve funcionar.
- **LLM retorna JSON inválido**: mostrar mensagem de erro e permitir retry. Máximo 2 tentativas automáticas antes de mostrar erro ao PM.
- **Grupo de synths pequeno (< 50)**: exibir aviso de que resultados podem ter baixa confiabilidade.
- **Synths sem dados demográficos completos**: usar valores padrão (0.5) para atributos faltantes na simulação.
- **Timeout na simulação**: definir timeout de 30s. Se exceder, mostrar erro e sugerir reduzir número de cenários.
- **PM não respondeu todas as arestas**: usar valor default de cada aresta (definido pelo LLM na geração do modelo) para arestas não respondidas.
- **Interview guide existente**: sobrescrito silenciosamente pela análise quantitativa — não há confirmação.

## Requirements *(mandatory)*

### Functional Requirements

**Modelagem Causal (seção superior da aba Análise Quanti)**

- **FR-001**: Sistema DEVE gerar um DAG causal a partir do contexto do experimento (título + hipótese + descrição) via chamada LLM (gpt-5.1) usando o prompt DAG_SYSTEM (Apêndice A).
- **FR-002**: O DAG DEVE ter 7-10 nós e 7-10 arestas, organizados em 3 camadas: raízes demográficas (Idade, Renda, Escolaridade), variáveis mediadoras (comportamentais/psicológicas), e nó de outcome (adoção/conversão).
- **FR-003**: Cada aresta DEVE ter um header contextual, 5 opções Likert com textos auto-contidos em português, valores fixos de mu/sigma (0.80/0.15, 0.65/0.25, 0.50/0.50, 0.30/0.25, 0.15/0.15), e um campo direction (1 ou -1).
- **FR-004**: Sistema DEVE mapear cada aresta a uma das 10 userVars disponíveis, extraídas dos synths do grupo (ver tabela de mapeamento abaixo).
- **FR-005**: Sistema DEVE exibir o DAG visualmente com espessura de aresta proporcional ao mu da opção selecionada e cor indicando direção (azul = direta, laranja = inversa).
- **FR-006**: Sistema DEVE persistir o modelo causal gerado e as seleções do PM no banco de dados, vinculados ao experimento.
- **FR-007**: Sistema DEVE permitir ao PM alterar seleções Likert a qualquer momento e ver o DAG reagir em tempo real.

**Simulação e Resultados (seção inferior da mesma aba, após clique em Simular)**

- **FR-008**: Sistema DEVE rodar simulação Monte Carlo server-side com 3.000 iterações × synths do grupo do experimento.
- **FR-009**: Para cada iteração, o sistema DEVE amostrar coeficientes das arestas usando a fórmula de simulação (Apêndice D) e calcular P(adoção) = sigmoid(intercepto + Σ coeficientes × userVars).
- **FR-010**: Sistema DEVE calcular e exibir: média, mediana, percentis 10 e 90, desvio padrão da distribuição de adoção.
- **FR-011**: Sistema DEVE segmentar resultados por idade (18-29, 30-49, 50+), renda (baixa, média, alta) e escolaridade (baixa, média, alta), exibindo taxa de adoção por segmento.
- **FR-012**: Sistema DEVE calcular sensibilidade por aresta: para cada aresta, fixar as demais nas seleções do PM e variar entre opção 0 (extremo alto) e opção 4 (extremo baixo). Impacto = |média_alta - média_baixa|. Usa 800 iterações por variação.
- **FR-013**: Sistema DEVE gerar interpretações contextualizadas para cada seção (distribuição, segmentos, sensibilidade) via LLM (gpt-4o-mini) usando o prompt INTERP_SYSTEM (Apêndice B), em paralelo (3 chamadas simultâneas).

**Interview Guide (gerado automaticamente após simulação)**

- **FR-014**: Após simulação completar, sistema DEVE automaticamente gerar o interview_guide do experimento via `InterviewGuideGeneratorService`, usando prompt baseado no QUESTIONNAIRE_SYSTEM (Apêndice C) adaptado para os campos da tabela `interview_guide`.
- **FR-015**: O prompt DEVE receber como contexto: descrição do experimento, resultado da simulação (média, IC 80%), e as 3 premissas mais sensíveis com seus impactos.
- **FR-016**: O output DEVE preencher os campos `context_definition` (briefing sobre o cenário de pesquisa), `questions` (3 perguntas focadas nas premissas mais sensíveis), e `context_examples` (exemplos positivos, neutros e negativos derivados do contexto do experimento).
- **FR-017**: Se já existir um interview_guide para o experimento, DEVE ser sobrescrito silenciosamente.
- **FR-018**: A geração automática do interview_guide na criação do experimento DEVE ser removida — o `InterviewGuideGeneratorService` agora é chamado apenas pela análise quantitativa.

**Infraestrutura**

- **FR-019**: Todas as chamadas LLM DEVEM ser instrumentadas com Phoenix tracing via `_tracer.start_as_current_span()`.
- **FR-020**: Sistema DEVE persistir resultados de simulação no banco (distribuição completa, segmentos, sensibilidade, interpretações).
- **FR-021**: Toda a feature (modelagem + simulação + resultados + interview guide) DEVE estar na aba "Análise Quanti" da página de detalhe do experimento, em fluxo linear scrollável.

### userVar → Synth Attribute Mapping

| userVar | Fonte no Synth | Normalização |
|---------|----------------|--------------|
| `ageNorm` | `demografia.idade` | `clamp((idade - 18) / 62, 0, 1)` |
| `incomeNorm` | `demografia.renda_mensal` | `clamp((renda - min) / (max - min), 0, 1)` |
| `eduNorm` | `demografia.escolaridade` | Mapa ordinal: sem_escolaridade=0.0 → doutorado=1.0 |
| `familySizeNorm` | `demografia.composicao_familiar.numero_pessoas` | `clamp(n / 5, 0, 1)` |
| `hasVisualDisab` | `deficiencias.visual.tipo` | `1.0` se != "nenhuma", `0.0` caso contrário |
| `hasMotorDisab` | `deficiencias.motora.tipo` | `1.0` se != "nenhuma", `0.0` caso contrário |
| `digitalCapability` | `sensitivities.digital_capability` | Já normalizado [0, 1] |
| `riskAversion` | `sensitivities.risk_aversion` | Já normalizado [0, 1] |
| `institutionalTrust` | `sensitivities.institutional_trust_level` | Já normalizado [0, 1] |
| `frictionTolerance` | `sensitivities.friction_tolerance` | Já normalizado [0, 1] |

### Key Entities

- **CausalModel**: Modelo causal gerado pelo LLM. Contém: label, interceptMu, interceptSigma, lista de nós (strings), lista de arestas. Vinculado a um experimento (1:1).
- **CausalEdge**: Aresta do DAG causal. Contém: id, from, to, userVar, direction, header, 5 opções (text + mu + sigma), default.
- **ModelingResponse**: Registro das seleções do PM. Contém: experiment_id, causal_model_id, mapa de edge_id → selected_option_index.
- **SimulationRun**: Resultado de uma execução de simulação. Contém: experiment_id, causal_model_id, timestamp, parâmetros (n_iterations, n_synths), resultados agregados (stats), distribuição completa, resultados por segmento, sensibilidade por aresta.
- **AnalysisInterpretation**: Interpretação AI por seção. Contém: simulation_run_id, section (distribuição/segmentos/sensibilidade), raw_text, ai_text.
- **InterviewGuide** (existente, reutilizado): Tabela `interview_guide` com campos `context_definition`, `questions`, `context_examples`. Gerado automaticamente pela análise quantitativa usando as 3 premissas mais sensíveis.

### Assumptions

- O grupo de synths do experimento tem synths com dados demográficos suficientes (idade, renda, escolaridade) para alimentar a simulação.
- Os atributos demográficos dos synths podem ser normalizados para o intervalo [0, 1] conforme tabela de mapeamento.
- O mapeamento entre userVars do DAG e atributos dos synths é fixo (10 variáveis) e definido no backend.
- A metodologia de Malhotra para o questionário é fixa (Q1: aberta, Q2: cenário, Q3: intenção comportamental).
- O `InterviewGuideGeneratorService` existente será adaptado para usar o novo prompt (Apêndice C), não mais chamado automaticamente na criação do experimento.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: PM consegue gerar um modelo causal e calibrá-lo (responder todas as afirmações) em menos de 5 minutos.
- **SC-002**: Simulação de 3.000 cenários completa em menos de 15 segundos para grupos com até 500 synths.
- **SC-003**: Resultados de simulação incluem as 3 seções (distribuição, segmentos, sensibilidade) com dados numéricos verificáveis.
- **SC-004**: Interpretações AI referenciam o contexto específico do experimento (nome do produto/feature) em 90%+ dos casos.
- **SC-005**: Após simulação, o interview_guide do experimento existe no banco com os 3 campos preenchidos, permitindo criação imediata de entrevistas.

---

## Apêndice A: Prompt DAG_SYSTEM (gpt-5.1)

Prompt para geração do modelo causal. Usar as-is, ajustando apenas a lista de userVars disponíveis para as 10 do synth-lab.

```
You are an expert in causal inference, product experimentation, and behavioral modeling for a Brazilian financial institution.

Given an experiment description, generate a causal DAG where each edge is an ASSERTION about how a variable affects another.

RULES:
- 7-10 nodes, 7-10 edges. Last node = outcome (adoption/conversion/engagement).
- CRITICAL DAG STRUCTURE — 3 layers:
  1. DEMOGRAPHIC ROOTS (left): "Idade", "Renda", "Escolaridade" as root nodes (no incoming edges).
  2. MEDIATING VARIABLES (middle): Behavioral/psychological constructs (e.g., "Confiança", "Percepção de Valor").
  3. OUTCOME (right): Final adoption node.
  Every demographic root must have at least 1 outgoing edge.
- Available userVar values (ONLY): ageNorm, incomeNorm, eduNorm, digitalCapability, familySizeNorm, hasVisualDisab, hasMotorDisab, riskAversion, institutionalTrust, frictionTolerance
  ALL are normalized [0,1].
- Demographic→Mediator: ageNorm (for Idade), incomeNorm (for Renda), eduNorm (for Escolaridade).

CRITICAL — EDGE FORMAT:
Each edge is an ASSERTION (statement), NOT a question. The PM responds with agreement level.

CRITICAL — EDGE HEADER:
Instead of "statement", each edge has a "header" field. This is a SHORT contextual intro:
  Format: "A respeito de quanto [target] é influenciado(a) por [source concept]"
  Example: "A respeito de quanto a Familiaridade Digital é influenciada pela idade"

CRITICAL — OPTIONS (5 self-contained sentences):
Each option has: text, mu, sigma.
- "text" is a COMPLETE, self-contained sentence that the PM reads and agrees/disagrees with.
- mu is [0,1] coupling strength. sigma is uncertainty fraction. BOTH ARE HIDDEN from PM.
- The PM sees ONLY the text.

The 5 options MUST follow this exact pattern (strongest agreement first, weakest last):
  Option 0: text = strong effect claim.                      mu=0.80, sigma=0.15
  Option 1: text = significant effect claim.                 mu=0.65, sigma=0.25
  Option 2: text = "Não sei dizer se [X] impacta [Y]"       mu=0.50, sigma=0.50
  Option 3: text = weak/uncertain effect claim.              mu=0.30, sigma=0.25
  Option 4: text = no effect claim.                          mu=0.15, sigma=0.15

THESE mu/sigma VALUES ARE FIXED. Do NOT change them.

RULES FOR OPTION TEXT:
- Option 0 must be the STRONGEST claim, with specificity
- Option 1 is strong but less absolute
- Option 2 ALWAYS starts with "Não sei dizer se..." — this is the uncertainty option
- Option 3 acknowledges some weak relationship but with hedging language
- Option 4 flatly denies the relationship
- ALL options are complete Portuguese sentences.

CRITICAL — "direction" field:
Each edge MUST include a "direction" field: 1 (direct/positive) or -1 (inverse/negative).

CRITICAL — VARIED DEFAULTS:
- "default" is NOT always 2. Be OPINIONATED based on common sense about the experiment.
- At least 2 edges should have default != 2. At least 1 should be 0,1 or 3,4.

Node names SHORT (max 25 chars). Portuguese BR.
interceptMu: -0.3 to 0.5. interceptSigma: 0.3 to 0.5.

Respond with ONLY valid JSON:
{
  "label": "string",
  "interceptMu": number,
  "interceptSigma": number,
  "nodes": ["string"...],
  "edges": [{
    "id": "string",
    "from": "string",
    "to": "string",
    "userVar": "string",
    "direction": 1 or -1,
    "header": "string",
    "options": [{"text":"string","mu":number,"sigma":number}...5 items],
    "default": number
  }...]
}
```

## Apêndice B: Prompt INTERP_SYSTEM (gpt-4o-mini)

Prompt para interpretações contextualizadas. Usar as-is. Chamado 3 vezes em paralelo (uma por seção: Distribuição, Segmentos, Sensibilidade).

```
You are a senior product strategy advisor. You help product managers decide next steps based on simulation results.

You will receive the experiment description, the section type, raw statistics, AND the full sensitivity analysis data.

RULES:
- Write in Portuguese BR. 2-4 sentences max.
- Be SPECIFIC to this experiment — reference the actual product/feature.
- Respond with ONLY the text, no quotes, no markdown.

SECTION-SPECIFIC INSTRUCTIONS:

IF section = "Distribuição":
- ALWAYS start with: "Com 80% de confiança, a taxa de adoção fica entre X% e Y%."
- Then analyze the uncertainty: if high, explain WHICH premisses are driving most uncertainty and what the PM can do about it.
- If uncertainty is low, say it's a good sign and suggest next steps.

IF section = "Segmentos":
- Focus on the practical implication: which segment to target first, whether differences justify a phased rollout.
- Reference specific segments by name.

IF section = "Sensibilidade":
- Focus on the top 1-2 premisses and what specific research or data could resolve the uncertainty.
- Be concrete: "Para validar se [premissa], analise dados de uso do app atual filtrado por faixa etária" — not generic advice.
```

## Apêndice C: Prompt QUESTIONNAIRE_SYSTEM (gpt-5.1) — base para InterviewGuideGeneratorService

Prompt base do JSX. DEVE ser adaptado para que o output preencha os campos da tabela `interview_guide` (`context_definition`, `questions`, `context_examples`) em vez de gerar Markdown livre. A estrutura Malhotra (Q1: aberta, Q2: cenário, Q3: intenção comportamental) é mantida.

```
You are an expert in marketing research following Naresh Malhotra's "Marketing Research: An Applied Orientation".

CONTEXT: A product manager ran a causal simulation for a product experiment. They need a FIELD QUESTIONNAIRE to validate the most critical assumptions with real users BEFORE running the experiment.

CRITICAL CONSTRAINTS:
- The interview is MEDIATED by a trained interviewer who can adapt and probe as needed.
- Each respondent ALREADY has a complete demographic file (age, income, education, family, disabilities). DO NOT include ANY demographic, screening, or profiling questions.
- Output EXACTLY 3 questions — no more, no less.
- Target the TOP 3 most impactful premisses from the sensitivity analysis.

MALHOTRA METHODOLOGY (apply strictly):
- Ch. 10 (Questionnaire Design): Funnel approach — broad to narrow. With 3 questions:
  * Q1: Open-ended / qualitative (ch.9 unstructured)
  * Q2: Scenario-based with forced choice (ch.9 non-comparative scaling)
  * Q3: Behavioral intention scale (ch.9 Likert/intention)
- Ch. 10 (Wording): No leading questions, no double-barreled, no jargon. Simple conversational Portuguese BR.
- Ch. 9 (Triangulation): Each question uses a DIFFERENT measurement technique to cross-validate.

OUTPUT FORMAT — JSON with interview_guide fields:
{
  "context_definition": "2-3 sentences describing the research scenario and what to understand from users",
  "questions": "Central theme + the 3 questions formatted as: Q1 (aberta): [text] | Q2 (cenário): [text] | Q3 (intenção): [text]",
  "context_examples": "positive_1|positive_2|neutral_1|neutral_2|negative_1|negative_2"
}

RULES FOR context_examples:
- 2 POSITIVE examples: realistic good experiences related to the experiment
- 2 NEUTRAL examples: everyday/common experiences
- 2 NEGATIVE examples: frustrating experiences
- Separated by pipe (|)
- Each is a realistic, conversational story in Portuguese BR
```

**Nota**: Este prompt é a base. Na implementação, deve ser ajustado para incluir instruções adicionais do `InterviewGuideGeneratorService` existente (tom, profundidade, etc.) mantendo a estrutura Malhotra.

## Apêndice D: Fórmulas de Simulação Monte Carlo

Lógica extraída do JSX — deve ser portada para Python no backend.

**Simulação principal** (3.000 iterações):
```
BUDGET = 3.0  # total logit swing máximo
perEdgeScale = BUDGET / nEdges

Para cada iteração s:
  intercepto = Normal(interceptMu, interceptSigma)
  Para cada aresta i:
    opt = edge.options[seleção_PM[i]]
    dir = edge.direction  # 1 ou -1
    betaMu = opt.mu * perEdgeScale * dir
    betaSigma = opt.sigma * perEdgeScale
    coef[i] = Normal(betaMu, betaSigma)

  Para cada synth u:
    logit = intercepto + Σ(coef[i] * extractor[edge.userVar](u))
    P(adoção) = sigmoid(logit) = 1 / (1 + exp(-logit))
    adotou = random() < P(adoção)

  taxa_adoção[s] = count(adotou) / total_synths
```

**Análise de sensibilidade** (800 iterações por aresta):
```
Para cada aresta i:
  seleções_low = seleções_PM com aresta[i] = 0 (extremo forte)
  seleções_high = seleções_PM com aresta[i] = 4 (extremo fraco)
  média_low = mean(runSim(seleções_low, 800))
  média_high = mean(runSim(seleções_high, 800))
  impacto[i] = |média_high - média_low|
```

**Interpretações raw** (estatísticas, sem LLM):
- Distribuição: "Com 80% de confiança, a taxa de adoção fica entre {p10}% e {p90}%. A estimativa central é {mean}%." + classificação de incerteza baseada no desvio padrão (>3pp = alta, >1.5pp = moderada, <1.5pp = baixa).
- Segmentos: identifica melhor e pior segmento, calcula ratio, identifica fator mais discriminante (idade/renda/escolaridade).
- Sensibilidade: identifica premissa de maior impacto, segunda premissa se > 60% da primeira, e premissas de baixo impacto (< 20% da primeira).
