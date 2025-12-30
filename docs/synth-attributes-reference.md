# Referência de Atributos do Synth

Todos os atributos de um synth, com tipo de dado, fórmula de geração e persistência.

**Versão do Schema**: 2.3.0

---

## Identificação

| Atributo | Tipo | Geração | Persistência |
|----------|------|---------|--------------|
| **id** | `string (6 chars)` | UUID truncado para 6 caracteres | `synths.id` (PRIMARY KEY) |
| **nome** | `string` | Gerado via Faker (nome brasileiro) | `synths.nome` |
| **descricao** | `string \| null` | Gerado via LLM baseado no perfil | `synths.descricao` |
| **link_photo** | `string \| null` | URL externa (thispersondoesnotexist) | `synths.link_photo` |
| **avatar_path** | `string \| null` | Path local do avatar gerado | `synths.avatar_path` |
| **created_at** | `datetime` | `datetime.now()` no momento da criação | `synths.created_at` |
| **version** | `string` | Fixo: `"2.3.0"` | `synths.version` |
| **synth_group_id** | `string \| null` | ID do grupo ao qual pertence | `synths.synth_group_id` (FK) |

---

## Demografia (`synths.data -> "demografia"`)

| Atributo | Tipo | Geração | Persistência |
|----------|------|---------|--------------|
| **idade** | `int (0-120)` | Faker com distribuição realística brasileira | JSON em `synths.data` |
| **genero_biologico** | `string` | Distribuição IBGE: ~51% feminino, ~49% masculino | JSON em `synths.data` |
| **raca_etnia** | `string` | Distribuição IBGE Censo 2022: branco/pardo/preto/amarelo/indígena | JSON em `synths.data` |
| **escolaridade** | `string` | Distribuição PNAD 2023 por região | JSON em `synths.data` |
| **renda_mensal** | `float (BRL)` | Log-normal baseada em escolaridade e região | JSON em `synths.data` |
| **ocupacao** | `string` | CBO correlacionado com escolaridade | JSON em `synths.data` |
| **estado_civil** | `string` | Correlacionado com idade | JSON em `synths.data` |
| **localizacao.pais** | `string` | Fixo: `"Brasil"` | JSON em `synths.data` |
| **localizacao.regiao** | `string` | Norte/Nordeste/Centro-Oeste/Sudeste/Sul (distribuição IBGE) | JSON em `synths.data` |
| **localizacao.estado** | `string` | UF correlacionado com região | JSON em `synths.data` |
| **localizacao.cidade** | `string` | Faker cidade brasileira | JSON em `synths.data` |
| **composicao_familiar.tipo** | `string` | unipessoal/casal sem filhos/casal com filhos/monoparental/multigeracional | JSON em `synths.data` |
| **composicao_familiar.numero_pessoas** | `int (1-15)` | Correlacionado com tipo | JSON em `synths.data` |

---

## Psicografia (`synths.data -> "psicografia"`)

| Atributo | Tipo | Geração | Persistência |
|----------|------|---------|--------------|
| **interesses** | `list[string]` | 1-4 itens selecionados aleatoriamente de pool | JSON em `synths.data` |
| **contrato_cognitivo.tipo** | `string` | factual/narrador/desconfiado/racionalizador/impaciente/esforçado_confuso | JSON em `synths.data` |
| **contrato_cognitivo.perfil_cognitivo** | `string` | Descrição textual do perfil | JSON em `synths.data` |
| **contrato_cognitivo.regras** | `list[string]` | Regras de comportamento para LLM | JSON em `synths.data` |
| **contrato_cognitivo.efeito_esperado** | `string` | Descrição do efeito nas respostas | JSON em `synths.data` |

---

## Deficiências (`synths.data -> "deficiencias"`)

| Atributo | Tipo | Geração | Persistência |
|----------|------|---------|--------------|
| **visual.tipo** | `string` | nenhuma/leve/moderada/severa/cegueira (PNS 2019: 3.4% alguma) | JSON em `synths.data` |
| **auditiva.tipo** | `string` | nenhuma/leve/moderada/severa/surdez (PNS 2019: 1.1% alguma) | JSON em `synths.data` |
| **motora.tipo** | `string` | nenhuma/leve/moderada/severa (PNS 2019: 3.8% alguma) | JSON em `synths.data` |
| **cognitiva.tipo** | `string` | nenhuma/leve/moderada/severa (PNS 2019: 1.2% alguma) | JSON em `synths.data` |

---

## Atributos Observáveis (`synths.data -> "observables"`)

Gerados durante criação do synth. **Visíveis ao PM** imediatamente após geração.

| Atributo | Tipo | Fórmula de Geração | Persistência |
|----------|------|---------------------|--------------|
| **digital_literacy** | `float [0,1]` | `Beta(α=2, β=4)` → tendência baixo-médio. Com correlação: `α = 2 + edu_factor×3`, `β = 4 - edu_factor×2` | JSON em `synths.data["observables"]` |
| **similar_tool_experience** | `float [0,1]` | `Beta(α=3, β=3)` → simétrico. Com correlação: `α = 2 + edu_factor×2`, `β = 3` | JSON em `synths.data["observables"]` |
| **motor_ability** | `float [0,1]` | `max(0.1, (1.0 - disability_severity) - (0.2 × age_motor_factor))` | JSON em `synths.data["observables"]` |
| **time_availability** | `float [0,1]` | `Beta(α=2, β=3)` → tendência baixo. Com correlação: `α = 2 + (1-family_pressure)×2 + age_factor`, `β = 3 + family_pressure×2` | JSON em `synths.data["observables"]` |
| **domain_expertise** | `float [0,1]` | `Beta(α=3, β=3)` → simétrico (não correlacionado) | JSON em `synths.data["observables"]` |

### Fatores de Correlação

- **edu_factor**: `EDUCATION_FACTOR_MAP[escolaridade]` → 0.0 (sem escolaridade) a 1.0 (doutorado)
- **disability_severity**: Retorna **0.8** se QUALQUER deficiência for 'severa', 'cegueira', ou 'surdez'. Caso contrário, usa `max(DISABILITY_SEVERITY_MAP[tipo])` → 0.0 (nenhuma) a 0.6 (moderada)
- **family_pressure**: `FAMILY_PRESSURE_MAP[composicao_familiar]` → 0.1 (sozinho) a 0.9 (mãe solo)
- **age_factor**: `<30: 0.4, 30-60: 0.5, >60: 0.7` (mais tempo disponível com idade)
- **age_motor_factor**: `<30: 0.0, 30-60: 0.3, >60: 0.6` (redução de habilidade motora com idade)

---

## Traços Latentes (`synth_outcomes.synth_attributes -> "latent_traits"`)

Derivados dos observáveis **durante simulação**. **NÃO visíveis ao PM** - usados internamente na simulação.

| Atributo | Tipo | Fórmula de Derivação | Persistência |
|----------|------|----------------------|--------------|
| **capability_mean** | `float [0,1]` | `0.40×digital_literacy + 0.35×similar_tool_experience + 0.15×motor_ability + 0.10×domain_expertise` | JSON em `synth_outcomes.synth_attributes` |
| **trust_mean** | `float [0,1]` | `0.60×similar_tool_experience + 0.40×digital_literacy` | JSON em `synth_outcomes.synth_attributes` |
| **friction_tolerance_mean** | `float [0,1]` | `0.40×time_availability + 0.35×digital_literacy + 0.25×similar_tool_experience` | JSON em `synth_outcomes.synth_attributes` |
| **exploration_prob** | `float [0,1]` | `0.50×digital_literacy + 0.30×(1 - similar_tool_experience) + 0.20×time_availability` | JSON em `synth_outcomes.synth_attributes` |

### Significado dos Traços

- **capability_mean**: Capacidade do usuário de completar tarefas digitais
- **trust_mean**: Confiança do usuário em sistemas digitais
- **friction_tolerance_mean**: Paciência com obstáculos e erros
- **exploration_prob**: Probabilidade de explorar funcionalidades novas

---

## Resultados de Simulação (`synth_outcomes`)

Calculados durante a simulação Monte Carlo. Persistidos por execução.

| Atributo | Tipo | Cálculo | Persistência |
|----------|------|---------|--------------|
| **id** | `string` | UUID gerado | `synth_outcomes.id` (PRIMARY KEY) |
| **analysis_id** | `string` | ID da análise executada | `synth_outcomes.analysis_id` (FK) |
| **synth_id** | `string` | ID do synth | `synth_outcomes.synth_id` |
| **did_not_try_rate** | `float [0,1]` | `count(outcome == "did_not_try") / n_executions` | `synth_outcomes.did_not_try_rate` |
| **failed_rate** | `float [0,1]` | `count(outcome == "failed") / n_executions` | `synth_outcomes.failed_rate` |
| **success_rate** | `float [0,1]` | `count(outcome == "success") / n_executions` | `synth_outcomes.success_rate` |

---

## Labels de Display (Calculados Dinamicamente)

Mapeamento de valores [0,1] para labels textuais. **Não persistidos** - calculados no momento da exibição.

| Range | Label | Cor |
|-------|-------|-----|
| [0.0, 0.2) | Muito Baixo | `red-500` |
| [0.2, 0.4) | Baixo | `orange-500` |
| [0.4, 0.6) | Médio | `yellow-500` |
| [0.6, 0.8) | Alto | `lime-500` |
| [0.8, 1.0] | Muito Alto | `green-500` |

---

## Resumo de Persistência

| Tabela | Campos Diretos | Campos JSON |
|--------|----------------|-------------|
| `synths` | id, synth_group_id, nome, descricao, link_photo, avatar_path, created_at, version | `data` (demografia, psicografia, deficiencias, **observables**) |
| `synth_outcomes` | id, analysis_id, synth_id, did_not_try_rate, failed_rate, success_rate | `synth_attributes` (observables, latent_traits) |
| `synth_groups` | id, name, description, created_at | — |

---

## Changelog

### v2.3.0 (Atual)
- **Removidos**: `identidade_genero`, `personalidade_big_five` (5 traços), `motora.usa_cadeira_rodas`, `alfabetizacao_digital`
- **Motor Ability**: Agora inclui age_motor_factor na fórmula
- **Disability Severity**: Retorna 0.8 se qualquer deficiência for 'severa', 'cegueira', ou 'surdez'
- **Observables**: Agora persistidos em `synths.data["observables"]` (visíveis ao PM logo após geração)
- **Latent Traits**: Calculados apenas durante simulação, persistidos em `synth_outcomes.synth_attributes`

### v2.0.0 (Anterior)
- Schema inicial com todos os atributos
