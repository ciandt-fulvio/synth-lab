# Análise: SynthLab como Plataforma Genérica de Decisão

## Context

O SynthLab hoje é especializado em **"probabilidade de adoção de feature digital em instituição financeira brasileira"**. A pergunta é: poderia ser generalizado para qualquer decisão de produto — "chocolate vs morango", "modelo de precificação A vs B", "embalagem vermelha vs azul"?

Esta análise mapeia o que já é genérico, o que está hardcoded, e o que teria que mudar.

---

## Diagnóstico por Camada

### 1. Geração de Personas (Synths) — ✅ JÁ É GENÉRICO

**Arquivos**: `src/synth_lab/gen_synth/`

Personas são perfis demográficos/psicográficos genéricos:
- Demografia: idade, renda, escolaridade, composição familiar, ocupação, localização
- Psicografia: Big Five, interesses, contratos cognitivos
- Avatar visual

**Nada** aqui assume "produto digital" ou "adoção". Personas podem representar consumidores de sorvete, eleitores, pacientes — qualquer população.

**Veredicto**: Zero mudanças necessárias.

---

### 2. Pesquisa Qualitativa (Entrevistas) — ✅ JÁ É GENÉRICO

**Arquivos**: `src/synth_lab/services/research_agentic/instructions.py`, `interview_guide_generator_service.py`

- Entrevistador: "Explicar fenômenos conectando fatos observáveis com experiência vivida" — domain-agnostic
- Entrevistado: Recebe nome, idade, ocupação, perfil do synth — sem referência a "adoção"
- Orquestrador: Puramente estrutural (quem fala agora?)
- Guia de entrevista: Gerado a partir do nome/hipótese do experimento — adapta-se ao contexto

**Veredicto**: Funciona out-of-the-box para qualquer tema.

---

### 3. Motor Quantitativo (DAG + Monte Carlo) — 🔴 HARDCODED PARA ADOÇÃO DIGITAL

Este é o núcleo do problema. Três sub-problemas:

#### 3a. Variáveis de Usuário Fixas

**Arquivo**: `src/synth_lab/domain/entities/causal_model.py` (VALID_USER_VARS)

```python
VALID_USER_VARS = frozenset({
    "ageNorm", "incomeNorm", "eduNorm", "familySizeNorm",
    "hasVisualDisab", "hasMotorDisab",
    "digitalCapability",        # ← específico digital
    "riskAversion",
    "institutionalTrust",       # ← específico financeiro
    "frictionTolerance",
})
```

Para sorvete precisaríamos: `sweetnessTolerance`, `healthConsciousness`, `brandLoyalty`...
Para eleições: `politicalAlignment`, `mediaExposure`...

**Cada domínio tem suas variáveis relevantes.** O frozenset de 10 não serve.

#### 3b. Prompt da DAG

**Arquivo**: `src/synth_lab/services/quantitative_analysis_service.py` (DAG_SYSTEM_PROMPT)

Hardcoded:
- "expert in... behavioral modeling for a **Brazilian financial institution**"
- "Last node = outcome (**adoption/conversion/engagement**)"
- "DEMOGRAPHIC ROOTS: **Idade, Renda, Escolaridade** as root nodes"
- 3-layer structure fixo (demográfico → mediador → outcome)
- userVars fixos no prompt

#### 3c. Segmentação Fixa

**Arquivo**: `src/synth_lab/services/simulation_engine.py` (compute_segments)

Apenas 3 dimensões com buckets hardcoded:
- Idade: 18-29, 30-49, 50+
- Renda: <3000, 3000-10000, >10000 (BRL)
- Educação: fundamental, médio, superior

Para sorvete: segmentar por preferência alimentar, faixa etária diferente (crianças!), região.

#### 3d. Linguagem de Interpretação

**Arquivo**: `src/synth_lab/services/simulation_engine.py` (compute_raw_interpretations)

"taxa de **adoção**" hardcoded em todo o texto de interpretação.

---

### 4. Frontend — 🟡 MAYORMENTE OK

**Arquivos**: `frontend/src/components/quantitative/`

- Componentes de UI (cards, charts, badges) são genéricos
- Labels de segmento ("Idade", "Renda", "Escolaridade") vêm do backend — mudariam automaticamente
- Linguagem de interpretação vem do backend
- **Único hardcoding frontend**: labels em BUCKET_LABELS no `SegmentCards.tsx`

---

## Modelo Mental: O que É o SynthLab?

Hoje o SynthLab faz 3 coisas:

| Capacidade | Genérico? | Descrição |
|-----------|-----------|-----------|
| **Gerar personas sintéticas** | ✅ Sim | População representativa para qualquer pesquisa |
| **Entrevistar personas** | ✅ Sim | Pesquisa qualitativa sobre qualquer tema |
| **Simular probabilidade via DAG causal** | 🔴 Não | Hardcoded para adoção de produto digital financeiro |

A boa notícia: **2 de 3 pilares já são genéricos**. O problema é concentrado no motor quantitativo.

---

## O Que Teria Que Mudar (Se Quiséssemos Generalizar)

### Mudança 1: UserVars Dinâmicas (IMPACTO ALTO)

**De**: frozenset de 10 variáveis fixas
**Para**: variáveis definidas por experimento, com extractors registráveis

Isso envolve:
- Remover `VALID_USER_VARS` como constante global
- Criar um sistema onde o LLM gera as variáveis relevantes para o domínio
- Extractors precisariam ser dinâmicos (ou mapeados via config do experimento)
- Synths precisariam ter atributos que o motor consiga extrair → **conexão entre geração de synths e variáveis da DAG**

**Problema profundo**: Hoje synths são gerados ANTES da DAG. Se as variáveis são dinâmicas, os synths precisam ter os atributos que a DAG vai usar. Isso cria uma dependência circular ou exige re-geração.

### Mudança 2: Prompt DAG Parametrizável (IMPACTO MÉDIO)

**De**: prompt hardcoded com "Brazilian financial institution"
**Para**: template com placeholders para domínio, outcome, e variáveis disponíveis

Relativamente simples — é "apenas" refatorar o prompt para aceitar contexto do experimento.

### Mudança 3: Segmentação Dinâmica (IMPACTO MÉDIO)

**De**: 3 dimensões fixas (idade/renda/educação) com buckets hardcoded
**Para**: dimensões definidas pelo LLM na geração da DAG, com buckets configuráveis

Precisaria que a DAG retornasse não apenas edges mas também a definição de segmentos relevantes.

### Mudança 4: Outcome Multi-Way (IMPACTO ALTO)

**De**: binário (adotou / não adotou → taxa %)
**Para**: multi-opção (chocolate 40%, morango 35%, outro 25%)

Isso muda fundamentalmente o motor de simulação:
- Monte Carlo hoje gera bernoulli(p) por synth → precisaria de multinomial
- Sensibilidade hoje compara mean_option0 vs mean_option4 → precisaria de comparação por outcome
- Toda a estrutura de `stats` (mean, p10, p90) muda

### Mudança 5: Linguagem Dinâmica (IMPACTO BAIXO)

Substituir "taxa de adoção" por termo configurável. Trivial.

---

## Conclusão Pragmática

### O SynthLab JÁ serve para:

1. **Qualquer pesquisa qualitativa**: Criar personas, entrevistar sobre qualquer tema. Funciona hoje.
2. **Qualquer decisão binária em contexto demográfico brasileiro**: Se a pergunta é "vai aderir ou não?" e a população pode ser descrita por idade/renda/educação/digital, o motor quantitativo funciona.

### O SynthLab NÃO serve (sem mudanças) para:

1. **Domínios com variáveis diferentes**: Sorvete, política, saúde — onde digitalCapability/institutionalTrust são irrelevantes
2. **Decisões multi-opção**: "A vs B vs C" (não binário)
3. **Populações não-brasileiras**: Segmentação assume contexto BR (renda em BRL, escolaridade BR)

### Esforço estimado para generalizar:

| Mudança | Esforço | Risco |
|---------|---------|-------|
| Linguagem dinâmica ("adoção" → configurável) | 1-2 dias | Baixo |
| Prompt DAG parametrizável | 2-3 dias | Médio |
| Segmentação dinâmica | 3-5 dias | Médio |
| UserVars dinâmicas + extractors | 5-8 dias | Alto (dependência circular synth↔DAG) |
| Outcome multi-way | 8-12 dias | Alto (refatora todo o motor MC) |
| **Total** | **~3-4 semanas** | |

### Recomendação

Não generalizar "tudo de uma vez". A abordagem incremental mais valiosa seria:

1. **Fase 1**: Parametrizar linguagem + prompt DAG (3-4 dias) → permite testar produtos não-financeiros, mas ainda com outcome binário e segmentação demográfica
2. **Fase 2**: Segmentação dinâmica (3-5 dias) → permite segmentos além de idade/renda/educação
3. **Fase 3**: UserVars dinâmicas (5-8 dias) → permite variáveis causais de qualquer domínio
4. **Fase 4**: Multi-way outcome (8-12 dias) → permite "A vs B vs C"

Cada fase agrega valor independente. Fase 1 sozinha já abre o SynthLab para ~80% dos casos de uso de produto (a maioria é binário: "vai usar ou não?").
