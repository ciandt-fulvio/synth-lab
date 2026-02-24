# Simulação Monte Carlo — Redesign v2

> Contexto: análise do run `sr_bed5cead`, synth `0wrccz` (Nicolas Teixeira, 97 anos),
> batch `sb_4fbf4b23`, modelo causal `cm_ebf96b3b` ("Delivery com entrega agendada 2").
> Resultado armazenado: `0.56`.

---

## Contexto: como o cálculo funciona hoje

### Camada 1 — Inputs (mantida, sem problemas)

Valores em [0,1] computados a partir do synth e do cenário de produto:

```
[sensitivity] Aversão a Risco          = 0.7759   ← alto: pessoa conservadora
[sensitivity] Confiança Instit.        = 0.2590   ← baixo: desconfiança
[sensitivity] Tolerância a Atrito      = 0.4349   ← moderado
[sensitivity] Planejamento Rotina      = 0.4140   ← moderado
[product]     Agendamento Claro        = 0.8      ← cenário "high"
[product]     Flexibilidade de Mudança = 0.2      ← cenário "low"
[product]     Precisão da Entrega      = 0.8      ← cenário "high"
[product]     Transparência do Status  = 0.2      ← cenário "low"
```

### Camada 2 — Nós de Interação (problemática no modelo atual)

Cada interaction node combina 1 pai de sensitivity + 1 pai de product via **média ponderada**
usando pesos gerados pelo LLM (`weight` em `causal_edges`):

```
interaction_val = Σ(effective_val_i × weight_i) / Σ(weight_i)
effective_val   = val se dir=+1, (1 - val) se dir=-1
```

Exemplo — Esforço p/ Ajustar Agenda:
```
Aversão a Risco:      val=0.7759, dir=+1 → eff=0.7759, weight=0.52 → contrib=0.4035
Flexibilidade:        val=0.2000, dir=-1 → eff=0.8000, weight=0.69 → contrib=0.5520
                                                                        ─────────────
resultado = 0.9555 / 1.21 = 0.7896
```

### Camada 3 — Outcome (Monte Carlo logístico)

```
coef_k ~ Normal(mu_k × scale × dir_outcome, sigma_k × scale)
logit  = intercept + Σ(coef_k × interaction_val_k)
prob   = sigmoid(logit)
```

`mu_k` e `sigma_k` vêm do **Likert selecionado pelo PM** para cada nó de interação.
`scale = BUDGET / sqrt(n_outcome_edges) = 3.0 / sqrt(4) = 1.5`

---

## Decisões de mudança

As três decisões abaixo foram tomadas para simplificar o modelo e dar mais controle ao PM.

---

### Decisão 1 — Remover os pesos LLM da camada 2

**Decisão:** A coluna `weight` em `causal_edges` deixa de ser usada no cálculo da camada 2.

**Motivação:** Os pesos eram gerados pelo LLM sem instrução de significado, produzindo valores
arbitrários que o PM não controlava e não conseguia interpretar. Removendo os pesos, a operação
de combinação não tem parâmetros livres — o único grau de liberdade do PM após os inputs da
camada 1 passa a ser o **Likert** (que já controla `mu_k` na camada 3).

**Impacto sobre os problemas do v1:**
- Problema 1 (pesos sem semântica) → eliminado
- Problema 4 (PM não controla camada 2) → eliminado

---

### Decisão 2 — Manter a semântica dual de `direction=-1` como design explícito

**Decisão:** `direction=-1` continua tendo comportamentos diferentes por camada, e isso é
intencional. Não haverá unificação de mecanismo — o que muda é que o comportamento passa a
ser **documentado explicitamente** em vez de ser uma inconsistência implícita.

| Camada | O que `dir=-1` faz | Semântica |
|---|---|---|
| Camada 2 | `eff = 1 - val` | "use a **ausência** do pai como contribuição" |
| Camada 3 | `coef = mu × scale × (-1)` | "o nó **penaliza** o outcome quando alto" |

**Motivação:** os dois mecanismos são matematicamente adequados para suas camadas. Na camada 2,
o que interessa é a direção da contribuição ao nó de interação (ex: baixa flexibilidade →
alta contribuição ao esforço). Na camada 3, o que interessa é se o nó aumenta ou diminui
a probabilidade de adoção. Unificar os mecanismos exigiria redesenho estrutural sem ganho real.

**Impacto sobre os problemas do v1:**
- Problema 2 (semântica inconsistente) → transformado em decisão documentada; o risco
  remanescente é de confusão por desenvolvedores/PMs (ver Problema A abaixo).

---

### Decisão 3 — Usar média geométrica na camada 2

**Decisão:** A operação de combinação dos pais na camada 2 passa de média ponderada para
**média geométrica**:

```
interaction_val = √(eff_sensitivity × eff_product)
effective_val   = val se dir=+1, (1 - val) se dir=-1
```

**Motivação:** a média ponderada tratava os pais como substitutos parciais (um valor alto
compensa um baixo). A média geométrica captura que **ambos precisam estar presentes** — se
qualquer um tender a zero, o resultado tende a zero, independentemente do outro. Essa semântica
é mais adequada para interaction nodes que representam fricção, esforço ou percepção composta.

**Exemplo comparativo — Esforço p/ Ajustar Agenda (Aversão=0.7759, Flexibilidade=0.2→eff=0.8):**
```
Média ponderada (v1):  (0.7759×0.52 + 0.8×0.69) / 1.21 = 0.7896
Média geométrica (v2):  √(0.7759 × 0.8000)              = √0.6207 = 0.7879
```
Valores próximos neste caso (pais simétricos). A diferença aparece quando os pais são assimétricos.

**Exemplo — Sensação de Controle (Tolerância=0.4349, Agendamento=0.8000):**
```
Média ponderada (v1):  (0.4349×0.62 + 0.8×0.78) / 1.40 = 0.6383
Média geométrica (v2):  √(0.4349 × 0.8000)              = √0.3479 = 0.5898
```
A média geométrica dá 0.59 vs 0.64 da média ponderada. Uma pessoa com tolerância a atrito
moderada (0.43) não chega a ter alta sensação de controle mesmo com agendamento claro —
semanticamente mais conservador e defensável.

**Impacto sobre os problemas do v1:**
- Problema 3 (operação não captura interação real) → resolvido
- Problema 5 (calibração do BUDGET) → **requer recalibração** (ver Problema B abaixo)

---

## Problemas remanescentes

Com as três decisões tomadas, os problemas 1, 3 e 4 do v1 estão eliminados.
Restam dois problemas que precisam de ação antes da implementação.

---

### Problema A — Semântica dual de `direction=-1` exige documentação ativa

**Status:** decisão tomada (Decisão 2), mas risco de confusão permanece.

**O que pode dar errado:** um PM ou desenvolvedor que encontre a edge `e11`
(Esforço → Outcome, `dir=-1`) e raciocine como camada 2 vai chegar à previsão errada:

- Raciocínio incorreto (usando lógica da camada 2):
  ```
  Esforço=0.8, dir=-1 → "o que entra é 1-0.8=0.2 — contribuição pequena"
  ```
- O que realmente acontece (camada 3):
  ```
  Esforço=0.8, dir=-1 → coef negativo → -1.2 × 0.8 = -0.96 — penalização grande
  ```

O mesmo rótulo `dir=-1` leva a previsões opostas conforme a camada.

**Cenário de extensão — nó de interação alimentando outro nó de interação:**

O modelo atual não tem isso, mas a arquitetura permite. Se futuramente um nó de interação X
alimentar outro nó Y com `dir=-1`:
```
X=0.7 → eff = 1-0.7 = 0.3 → entra na média geométrica de Y como 0.3
X=0.3 → eff = 1-0.3 = 0.7 → entra como 0.7
```
O comportamento qualitativo está correto, mas o desenvolvedor que inspeciona
`Y=0.5` não consegue reconstituir a origem sem saber que `1-X` foi usado.

**Solução proposta:**

1. Criar constante nomeada no código:
   ```python
   LAYER2_DIR_POSITIVE = 1    # usa val diretamente
   LAYER2_DIR_NEGATIVE = -1   # usa (1 - val): "ausência contribui"

   LAYER3_DIR_POSITIVE = 1    # coef positivo: nó facilita adoção
   LAYER3_DIR_NEGATIVE = -1   # coef negativo: nó penaliza adoção
   ```

2. No prompt ao LLM, separar os dois conceitos:
   - Para arestas `→ interaction node`: "direction=-1 significa que a **ausência** do pai
     contribui para o filho. Use quando o pai é uma barreira ou custo (ex: Flexibilidade
     alta → menos Esforço → direction=-1 para Flexibilidade→Esforço)."
   - Para arestas `→ outcome`: "direction=-1 significa que o nó de interação **penaliza**
     a adoção quando alto. Use quando o nó representa fricção ou risco."

3. Adicionar campo `edge_layer` ou `target_type` ao schema de edges para deixar explícito
   no banco qual mecanismo se aplica.

---

### Problema B — Recalibração do BUDGET necessária após mudança para média geométrica

**Status:** aberto, requer validação empírica.

**O problema:** o BUDGET de `3.0` foi calibrado empiricamente para a média ponderada, onde
os valores de camada 2 ficavam tipicamente em `[0.35, 0.85]`. Com a média geométrica, os
valores são sistematicamente menores para inputs assimétricos:

```
Média ponderada — range esperado dos interaction_vals: [0.35, 0.85]
Média geométrica — range esperado dos interaction_vals: [0.15, 0.80]
```

**Exemplo numérico — caso extremo assimétrico (s=0.05, p=0.80):**
```
Média ponderada (pesos iguais):  (0.05 + 0.80) / 2 = 0.425
Média geométrica:                √(0.05 × 0.80)    = √0.040 = 0.200
```
A média geométrica produz 0.20 vs 0.43 da ponderada — diferença de 53%.

**Impacto no logit:**
```
scale = BUDGET / sqrt(n) = 3.0 / sqrt(4) = 1.5
beta_mu_max = 0.80 × 1.5 = 1.20   (Likert "decisivo")

Com geométrica — contribution_max ≈ 1.20 × 0.80 = 0.96 por nó
Com geométrica — contribution_min ≈ 0.225 × 0.15 = 0.034 por nó
4 nós, range total: [0.14, 3.84]
```

O range ainda está dentro do BUDGET `3.0`, mas a cauda inferior comprime bastante:
para inputs muito assimétricos, o logit mal sai do intercept mesmo com Likert alto.

**Comparação com média ponderada:**
```
Com ponderada — contribution_max ≈ 1.20 × 0.85 = 1.02 por nó
Com ponderada — 4 nós: range total [0.30, 4.08]
```

**Efeito na distribuição de probabilidades:**

Com a geométrica, synths com features assimétricas (ex: alta aversão a risco mas produto
pouco flexível) terão `interaction_vals` menores, resultando em logits mais próximos do
intercept e probabilidades mais próximas de `0.5`. Isso é semanticamente correto — a incerteza
é maior quando os fatores não se alinham — mas pode comprimir excessivamente o range de saída.

**Solução proposta:**

1. **Recalibrar empiricamente:** calcular a distribuição de `interaction_vals` para os synths
   existentes (amostra representativa de ~50 synths × todos os cenários de produto) usando a
   nova fórmula.

2. **Ajustar BUDGET ou intercept** para que a distribuição de probabilidades finais cubra
   razoavelmente `[0.10, 0.90]` para os inputs observados.

3. **Critério de aceitação:** para o run de referência (`sr_bed5cead`, resultado=`0.56`),
   verificar que o novo modelo produz resultado na mesma região após recalibração.

4. **Possível ajuste simples:** aumentar BUDGET de `3.0` para `4.0` ou `4.5` para compensar
   os valores menores da geométrica, sem alterar a estrutura do modelo.

---

## Resumo: status dos problemas v1 → v2

| Problema (v1) | Status no v2 | Ação necessária |
|---|---|---|
| P1 — Pesos LLM sem semântica | ✅ Eliminado (Decisão 1) | — |
| P2 — `dir=-1` com semântica dual | ✅ Mantido como design explícito (Decisão 2) | Documentar + atualizar prompts |
| P3 — Média ponderada não captura interação | ✅ Resolvido (Decisão 3) | — |
| P4 — PM não controla camada 2 | ✅ Eliminado (Decisão 1) | — |
| P5 — Calibração do BUDGET | ⚠️ Aberto, mais urgente agora | Recalibrar empiricamente |
| **A — Documentação da semântica dual** | ⚠️ Novo problema explicitado | Constantes, prompts, schema |
| **B — Recalibração para geométrica** | ⚠️ Novo problema explicitado | Validação empírica + ajuste |

---

## Próximos passos

1. **Implementar Decisão 1 + 3** no código de simulação (remover pesos, trocar operação)
2. **Recalibrar BUDGET** (Problema B) — rodar distribuição empírica antes de ir para produção
3. **Atualizar prompts ao LLM** (Problema A) — separar semântica de `dir` por tipo de aresta
4. **Validar contra run de referência** — o resultado `0.56` do run `sr_bed5cead` deve
   manter-se na mesma região após recalibração
