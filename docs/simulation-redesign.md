# Simulação Monte Carlo — Análise de Problemas e Caminhos

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

### Camada 2 — Nós de Interação (problemática)

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

## Problemas identificados

---

### Problema 1 — Os pesos da camada 2 não têm semântica definida

**O que são:** a coluna `weight` em `causal_edges` (ex: `0.52`, `0.69`, `0.62`...).

**De onde vêm:** gerados pelo LLM no Pass 1 da topologia. O prompt só mostra
`"weight": 0.6` no exemplo JSON, sem nenhuma instrução de significado.

**Impacto:** o LLM produz valores arbitrários. A razão entre `weight=0.52`
(Aversão a Risco) e `weight=0.69` (Flexibilidade) implica que Flexibilidade
pesa 33% mais que Aversão — sem nenhuma justificativa ou controle do PM.

**Exemplo numérico:**
```
Com weight=0.52 e weight=0.69:
  Esforço = (0.7759×0.52 + 0.8×0.69) / 1.21 = 0.7896

Se LLM tivesse gerado weight=0.69 e weight=0.52 (invertido):
  Esforço = (0.7759×0.69 + 0.8×0.52) / 1.21 = 0.7870   ← quase igual neste caso

Com extremos: weight=0.9 e weight=0.1:
  Esforço = (0.7759×0.9 + 0.8×0.1) / 1.0 = 0.7583       ← diferença relevante
```

**Solução proposta:** remover os pesos da camada 2. O único "peso" que o PM
controla é o Likert do nó (que já existe). A combinação dos pais deve usar
uma operação sem parâmetros livres (ver Problema 3).

---

### Problema 2 — `direction=-1` significa coisas diferentes dependendo da camada

O LLM recebe uma instrução uniforme: `direction=-1` significa "quanto maior
o pai, menor o filho". Mas o código implementa essa instrução de duas formas
distintas conforme a camada.

---

**Camada 2 (interaction nodes) — mecanismo: inversão do valor**

```python
effective_val = val if direction == 1 else (1 - val)
interaction_val = weighted_avg(effective_vals)
```

O que acontece: o valor do pai é **substituído pelo seu complemento** antes
de entrar na média. O sinal que entra na combinação não é "quanto flexibilidade
existe", mas "quanto flexibilidade está ausente".

Exemplo — e6: Flexibilidade=0.2, dir=-1:
```
eff = 1 - 0.2 = 0.8   ← "ausência de flexibilidade" = 0.8
```

Exemplo — e6: Flexibilidade=0.8, dir=-1:
```
eff = 1 - 0.8 = 0.2   ← "ausência de flexibilidade" = 0.2
```

Funciona corretamente: menos flexibilidade → maior contribuição ao Esforço.

---

**Camada 3 (outcome, Monte Carlo) — mecanismo: inversão do coeficiente**

```python
beta_mu = mu × scale × direction   # direction=-1 → coeficiente negativo
contribution = coef × interaction_val
```

O que acontece: o valor do nó de interação entra **intacto**, mas o
coeficiente que o multiplica é negativo. O sinal que entra no logit é
"quanto Esforço existe", e o coeficiente negativo transforma isso em
"punição à adoção".

Exemplo — e11: Esforço=0.79, dir=-1, coef≈-1.2:
```
contribution = -1.2 × 0.79 = -0.95   ← penaliza o logit
```

Funciona corretamente: mais Esforço → logit cai → probabilidade cai.

---

**Por que as duas formas dão resultados equivalentes neste caso**

Para e6 + e11 encadeados, o PM quer: baixa flexibilidade → baixa adoção.

Com o design atual:
```
Flexibilidade=0.2
→ eff = 1-0.2 = 0.8          (camada 2, inversão do valor)
→ Esforço ≈ 0.79             (contribuição alta)
→ contribution = -1.2 × 0.79 = -0.95   (camada 3, coef negativo)
→ logit cai → adoção baixa ✓
```

Se flexibilidade fosse alta (0.8):
```
Flexibilidade=0.8
→ eff = 1-0.8 = 0.2          (camada 2)
→ Esforço ≈ contribuição baixa
→ contribution = -1.2 × (algo pequeno) = pequena penalização
→ logit quase não cai → adoção maior ✓
```

Funciona. O problema não é que os resultados estejam errados hoje.

---

**Onde a inconsistência causa problema: extensão e manutenção**

O rótulo `direction=-1` significa coisas diferentes:

| Camada | O que `-1` faz | Interpretação |
|---|---|---|
| Camada 2 | `eff = 1 - val` | "use a **ausência** do pai" |
| Camada 3 | `coef = -coef` | "a **presença** do nó **penaliza** o outcome" |

São semânticas opostas. Na camada 2, é o valor BAIXO do pai que produz
o efeito forte. Na camada 3, é o valor ALTO do nó que produz o efeito forte.

**Cenário concreto onde isso confunde:**

Suponha que o PM, ao revisar o modelo, veja a edge e11 (Esforço → Outcome, dir=-1)
e queira entender: "quando Esforço=0.8, qual é a contribuição?"

- Se raciocinar como camada 2: "dir=-1, então o que entra é 1-0.8=0.2 — contribuição pequena"
- O que realmente acontece (camada 3): "dir=-1 → coef negativo, 0.8 entra intacto → -1.2×0.8=-0.96 — penalização grande"

O mesmo rótulo `direction=-1` leva a previsões opostas dependendo da camada.
Um PM ou desenvolvedor que não conhece os dois mecanismos fará a análise errada.

**Segundo cenário — nó de interação alimentando outro nó de interação:**

O modelo atual não tem isso, mas a arquitetura permite. Se futuramente
um nó de interação X alimentar outro nó de interação Y com dir=-1:

- O código usa a camada 2 (é um nó intermediário): `eff = 1 - X`
- O PM pensa "alto X → baixo Y" — entende o efeito como penalização
- O que acontece: o **complemento de X** entra na média de Y
- Se X=0.7: eff=0.3 entra na média — Y fica baixo ✓
- Se X=0.3: eff=0.7 entra na média — Y fica alto ✓
- Resultado qualitativo correto, mas o desenvolvedor que olha Y=0.7
  não consegue dizer "qual pai contribuiu quanto" — a origem do 0.7
  mistura valores reais e complementos sem distinção visível.

---

**Solução proposta**

Não é necessário unificar os mecanismos — eles são matematicamente
adequados para suas camadas. O que precisa mudar é a **documentação e
o prompt ao LLM**:

1. Deixar explícito que `direction` tem dois efeitos distintos conforme
   o tipo de aresta (→ interaction vs. → outcome).

2. No prompt ao LLM, separar os dois conceitos:
   - Para arestas → interaction node: "direction=-1 significa que a **ausência** do pai contribui para o filho. Use quando o pai é uma barreira ou custo."
   - Para arestas → outcome: "direction=-1 significa que o nó de interação **penaliza** a adoção quando alto. Use quando o nó representa fricção ou risco."

3. Considerar renomear o campo: `input_direction` para arestas de camada 2,
   `outcome_direction` para arestas de camada 3.

- Intenção: "mais flexibilidade → menos esforço percebido"
- Camada 2 usa: `eff = 1 - 0.2 = 0.8` (baixa flexibilidade → alta contribuição ao esforço) ✓
- Camada 3 usaria: `beta_mu = mu × scale × (-1)` (coeficiente negativo) — mecanismo diferente

**Solução proposta:** unificar a semântica. Na camada 2, a direction deve ser
aplicada antes da operação de combinação (inversão do input), e na camada 3,
via sinal do coeficiente. Documentar explicitamente que são camadas distintas
com mecanismos distintos, ou redesenhar para usar o mesmo mecanismo em ambas.

---

### Problema 3 — A operação de combinação dos pais não captura interação real

**Operação atual:** média ponderada
```
interaction_val = Σ(effective_val_i × weight_i) / Σ(weight_i)
```

**Problema semântico:** a média ponderada trata os pais como substitutos parciais
um do outro. Um pai forte compensa um pai fraco.

**Exemplo — Sensação de Controle:**
```
Tolerância a Atrito = 0.4349  (moderada)
Agendamento Claro   = 0.8000  (alto)

Média ponderada: (0.4349×0.62 + 0.8×0.78) / 1.40 = 0.6383
```
Resultado: 0.64 — parece razoável, mas não captura que o produto
compensa a tolerância baixa.

**Problema numérico — caso extremo:**
```
Tolerância a Atrito = 0.05  (muito baixa)
Agendamento Claro   = 0.95  (muito alto)

Média ponderada: (0.05×0.62 + 0.95×0.78) / 1.40 = 0.551
```
A Sensação de Controle ainda seria 0.55 mesmo para alguém com tolerância
quase zero. Semanticamente questionável.

**Alternativas e suas semânticas:**

| Operação | Fórmula | Semântica |
|---|---|---|
| Produto | `s × p` | Ambos precisam ser altos. Um fraco cancela o outro. |
| Geométrica | `√(s × p)` | Idem, mas mais suave. |
| Mínimo | `min(s, p)` | O gargalo domina. O elo mais fraco limita o todo. |
| Média aritmética | `(s + p) / 2` | Um forte compensa o fraco. Contribuições se somam. |
| Média harmônica | `2sp/(s+p)` | Similar ao mínimo, mas contínua. |

**Exemplo comparativo para Sensação de Controle (s=0.43, p=0.80):**
```
Produto:          0.43 × 0.80 = 0.344   ← muito baixo
Geométrica:   √(0.43 × 0.80) = 0.587
Mínimo:        min(0.43,0.80) = 0.430
Média aritmét:  (0.43+0.80)/2 = 0.615
Média harmôn:  2×0.43×0.80/(0.43+0.80) = 0.559
```

**Exemplo comparativo para Esforço p/ Ajustar Agenda (s=0.78, p=0.80):**
```
Produto:          0.78 × 0.80 = 0.622
Geométrica:   √(0.78 × 0.80) = 0.789
Mínimo:        min(0.78,0.80) = 0.780
Média aritmét:  (0.78+0.80)/2 = 0.790
Média harmôn:  2×0.78×0.80/(0.78+0.80) = 0.789
```

Quando os dois pais são altos, as operações convergem. A diferença é maior
quando os pais são assimétricos.

**Observação:** a operação ideal pode variar por nó. "Esforço" faz mais
sentido com produto ou mínimo (requer os dois). "Sensação de Controle"
faz mais sentido com média (um bom produto compensa tolerância moderada).
Isso exigiria configuração por nó — adiciona complexidade.

---

### Problema 4 — O Likert do PM é usado só no outcome, não na camada 2

**Situação atual:**
- Camada 2 (interaction): usa pesos do LLM (`0.52`, `0.69`)
- Camada 3 (outcome): usa Likert do PM (`mu=0.80` para "decisivo")

**O PM não controla nada da camada 2.** A única entrada do usuário no
cálculo (o Likert) só aparece na etapa final.

**Implicação:** dois modelos com topologia diferente mas mesmos Likerts
produzem resultados distintos apenas por causa dos pesos LLM, sem que
o PM saiba ou controle.

**Solução proposta:** remover os pesos LLM da camada 2 e usar uma
operação sem parâmetros livres (produto, mínimo, geométrica). O Likert
do PM passa a ser o único grau de liberdade do modelo após os inputs
da camada 1.

---

### Problema 5 — Ordens de grandeza e calibração do BUDGET

**Situação atual:**
- `BUDGET = 3.0`, `scale = 3.0 / sqrt(4) = 1.5`
- `beta_mu` varia de `0.15×1.5=0.225` (opção 4) a `0.80×1.5=1.2` (opção 0)
- Os `interaction_vals` ficam em ~[0.2, 0.8] com a média ponderada atual

**Com produto como operação:**
- `signal = s × p` fica em [0, 1] mas na prática em [0.01, 0.64] para inputs reais
- A contribuição ao logit: `beta_mu × signal` fica em ~[0.01, 0.77] por nó
- Com 4 nós: range total ~[0.04, 3.1] → dentro do BUDGET ✓

**Com média aritmética:**
- `signal = (s+p)/2` fica em [0.1, 0.9] para inputs reais
- Contribuição por nó: ~[0.02, 1.08]
- Com 4 nós: range total ~[0.09, 4.3] → ultrapassa BUDGET

**Implicação:** mudar a operação de combinação exige recalibrar o BUDGET
ou o intercept. O BUDGET de 3.0 foi definido para a média ponderada.
Com produto (valores menores), o BUDGET efetivo cai; com média (valores
maiores), estoura.

**Solução proposta:** após definir a operação, recalibrar empiricamente
o BUDGET verificando a distribuição de logits para um conjunto de synths
representativos. O objetivo é que o range de probabilidades cubra
razoavelmente [0.1, 0.9] para os inputs esperados.

---

## Resumo: o que manter, o que mudar

| Componente | Status | Decisão |
|---|---|---|
| Camada 1 (sensitivity + product) | ✅ Correto | Manter |
| Direção das arestas | ⚠️ Semântica OK, implementação inconsistente entre camadas | Documentar / unificar |
| Pesos LLM (`causal_edges.weight`) | ❌ Sem semântica, não controlados pelo PM | Remover |
| Operação de combinação (média ponderada) | ❌ Não captura interação real | Substituir |
| Likert do PM como coeficiente | ✅ Correto conceitualmente | Manter, expandir uso |
| Multiplicador 2x para "mais importante" | ❓ Não discutido em detalhe | Decidir |
| BUDGET / scale | ⚠️ Depende da operação escolhida | Recalibrar após decisão |
| Monte Carlo logístico (sigmoid) | ✅ Correto | Manter |

---

## Próximas decisões

1. **Qual operação de combinação para camada 2?**
   - Uniforme (mesma para todos os nós) ou configurável por nó?
   - Candidatas: geométrica `√(s×p)` como padrão razoável

2. **O multiplicador 2x ("mais importante") permanece?**
   - Atualmente: o PM seleciona qual interaction node é "o mais importante"
     e ela recebe `2×norm_factor` como multiplicador no `beta_mu`

3. **Recalibrar BUDGET após decidir a operação**
