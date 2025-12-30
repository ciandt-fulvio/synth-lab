# Research: Observable vs. Latent Traits Model

**Feature**: 022-observable-latent-traits
**Date**: 2025-12-29

## Research Questions Resolved

### 1. Como ajustar parâmetros Beta baseado em demográficos?

**Decision**: Usar multiplicadores baseados em fatores demográficos normalizados [0,1]

**Rationale**:
- Escolaridade, idade e deficiências têm correlações conhecidas com literacia digital e outras capacidades
- Distribuições Beta permitem ajuste fino via parâmetros α e β
- Fórmula: `Beta(α_base + δ_α * factor, β_base + δ_β * (1 - factor))`

**Implementation**:
```python
# Exemplo para digital_literacy
education_factor = normalize_education(escolaridade)  # [0,1]
age_factor = 1 - normalize_age_penalty(idade)         # Jovens = 1, Idosos = 0.5
alpha = 2 + 3 * education_factor * age_factor
beta = 4 + 2 * (1 - education_factor)
digital_literacy = rng.beta(alpha, beta)
```

**Alternatives Considered**:
- Lookup tables por categoria (rejeitado: menos flexível)
- ML model (rejeitado: overengineering para o caso)
- Valores fixos por perfil (rejeitado: perde variabilidade)

---

### 2. Quais faixas usar para labels textuais?

**Decision**: 5 níveis equidistantes

| Range | Label | Descrição |
|-------|-------|-----------|
| 0.00 - 0.20 | Muito Baixo | Capacidade mínima ou ausente |
| 0.20 - 0.40 | Baixo | Abaixo da média |
| 0.40 - 0.60 | Médio | Na média da população |
| 0.60 - 0.80 | Alto | Acima da média |
| 0.80 - 1.00 | Muito Alto | Capacidade excepcional |

**Rationale**:
- Faixas equidistantes são intuitivas
- 5 níveis oferecem granularidade suficiente sem confusão
- Padrão comum em pesquisa UX (escala Likert adaptada)

**Alternatives Considered**:
- 3 níveis (rejeitado: granularidade insuficiente)
- 7 níveis (rejeitado: complexidade desnecessária)
- Percentis (rejeitado: menos intuitivo para PMs)

---

### 3. Como passar contexto de simulação para entrevistas?

**Decision**: Adicionar seção estruturada no system prompt do entrevistado

**Format**:
```text
## SEU DESEMPENHO NA SIMULAÇÃO

Você participou de uma simulação de uso do produto com os seguintes resultados:
- Taxa de tentativa: {attempt_rate}% (você tentou usar a feature em {attempt_rate}% das vezes)
- Taxa de sucesso: {success_rate}% (quando tentou, conseguiu em {success_rate}% das vezes)
- Taxa de falha: {failure_rate}% (quando tentou, falhou em {failure_rate}% das vezes)

IMPORTANTE: Suas respostas devem refletir essa experiência. Se você teve alta taxa de falha,
demonstre frustração ou dificuldade. Se teve alta taxa de não-tentativa, demonstre hesitação
ou desinteresse em usar a feature.
```

**Rationale**:
- Informação explícita permite comportamento consistente
- Instruções claras evitam contradições nas respostas
- Taxas numéricas são precisas e não ambíguas

**Alternatives Considered**:
- Inferir comportamento das observáveis (rejeitado: perde especificidade da simulação)
- Apenas sentimento geral (rejeitado: pouco granular)
- Nenhum contexto (rejeitado: respostas incoerentes)

---

### 4. Como garantir backward compatibility?

**Decision**: Manter todas as variáveis existentes, apenas adicionar

**Checklist de Compatibilidade**:
- [ ] `SimulationObservables` mantém mesmos 5 campos
- [ ] `SimulationLatentTraits` mantém mesmos 4 campos
- [ ] Fórmulas de derivação inalteradas
- [ ] `MonteCarloEngine` usa `latent_traits` sem mudanças
- [ ] Synths existentes no DB continuam funcionando

**Implementation**:
```python
# generate_observables() - ANTES
def generate_observables(rng, deficiencias) -> SimulationObservables:
    ...

# generate_observables() - DEPOIS (adiciona parâmetro opcional)
def generate_observables(
    rng,
    deficiencias,
    demografia: dict | None = None  # NOVO - opcional
) -> SimulationObservables:
    ...
```

**Rationale**:
- Parâmetro opcional não quebra chamadas existentes
- Synths antigos já têm simulation_attributes populados
- Simulações usam latent_traits que derivam de observables (cadeia intacta)

---

### 5. Como exibir observáveis no frontend?

**Decision**: Nova tab "Capacidades" no SynthDetailDialog com cards para cada observável

**UI Design**:
```
┌─────────────────────────────────────────────────────┐
│ [Perfil] [Psicografia] [Capacidades] [Deficiências] │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Literacia Digital                                   │
│  ████████░░░░░░░░░░░░ 0.42 - Médio                  │
│  Familiaridade com tecnologia e interfaces digitais  │
│                                                      │
│  Experiência com Ferramentas Similares               │
│  ██████░░░░░░░░░░░░░░ 0.35 - Baixo                  │
│  Uso prévio de ferramentas semelhantes              │
│                                                      │
│  ...                                                 │
└─────────────────────────────────────────────────────┘
```

**Rationale**:
- Tab separada mantém organização existente
- Progress bars são visualmente claras
- Labels + descrições tornam dados acionáveis para recrutamento

**Alternatives Considered**:
- Expandir tab "Tecnologia" existente (rejeitado: mistura conceitos)
- Modal separado (rejeitado: fragmenta experiência)
- Apenas texto (rejeitado: menos visual)

---

## Mapeamento de Escolaridade para Factor

| Escolaridade | Factor |
|--------------|--------|
| Sem instrução | 0.0 |
| Fundamental incompleto | 0.15 |
| Fundamental completo | 0.25 |
| Médio incompleto | 0.35 |
| Médio completo | 0.45 |
| Superior incompleto | 0.60 |
| Superior completo | 0.75 |
| Pós-graduação | 0.90 |
| Mestrado/Doutorado | 1.0 |

---

## Mapeamento de Deficiência Motora para motor_ability

| Tipo | Factor | Resultado Beta |
|------|--------|----------------|
| Nenhuma | 0.0 | Beta(5.0, 1.5) → média ~0.77 |
| Leve | 0.25 | Beta(3.75, 2.5) → média ~0.60 |
| Moderada | 0.5 | Beta(2.5, 3.5) → média ~0.42 |
| Severa | 1.0 | Beta(0.0, 5.5) → média ~0.08 |

---

## Mapeamento de Composição Familiar para time_availability

| Tipo | Pressure Factor | Efeito |
|------|-----------------|--------|
| Sozinho | 0.1 | Mais tempo disponível |
| Casal sem filhos | 0.25 | Tempo moderado |
| Casal com 1 filho | 0.5 | Menos tempo |
| Casal com 2+ filhos | 0.75 | Muito menos tempo |
| Monoparental | 0.9 | Tempo muito limitado |

---

## Conclusão

Todas as questões de pesquisa foram resolvidas. Decisões priorizaram:
1. **Simplicidade**: Fórmulas claras e determinísticas
2. **Compatibilidade**: Nenhuma quebra de funcionalidade existente
3. **Usabilidade**: Labels e UI intuitivos para PMs
4. **Coerência**: Contexto de simulação garante respostas consistentes em entrevistas
