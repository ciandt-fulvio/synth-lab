# Quickstart: Observable vs. Latent Traits

**Feature**: 022-observable-latent-traits
**Date**: 2025-12-29

## Visão Geral

Esta feature separa as características de synths em dois grupos:

1. **Observáveis** (visíveis ao PM): Atributos que podem ser identificados em pessoas reais
2. **Latentes** (internas): Variáveis derivadas usadas apenas nas simulações

## Para Product Managers

### Visualizando Características de um Synth

1. Acesse a lista de synths
2. Clique em um synth para ver detalhes
3. Navegue até a aba **"Capacidades"**
4. Veja os 5 atributos observáveis:

| Atributo | O que significa | Uso para recrutamento |
|----------|----------------|----------------------|
| Literacia Digital | Familiaridade com tecnologia | "Procuro pessoa com [baixa/alta] experiência digital" |
| Exp. Ferramentas Similares | Uso prévio de ferramentas parecidas | "Já usou [Produto X]? Sim/Não" |
| Capacidade Motora | Habilidade física para interação | "Pessoa com/sem limitações motoras" |
| Disponibilidade de Tempo | Tempo típico disponível | "Tem [pouco/muito] tempo livre" |
| Conhecimento do Domínio | Expertise na área | "Trabalha na área de [domínio]" |

### Interpretando os Labels

| Label | Valor | Significado |
|-------|-------|-------------|
| Muito Baixo | 0.00 - 0.20 | Capacidade mínima ou ausente |
| Baixo | 0.20 - 0.40 | Abaixo da média |
| Médio | 0.40 - 0.60 | Na média da população |
| Alto | 0.60 - 0.80 | Acima da média |
| Muito Alto | 0.80 - 1.00 | Capacidade excepcional |

### Recrutando Pessoas Equivalentes

Para encontrar uma pessoa real equivalente a um synth:

1. Anote os observáveis do synth (aba Capacidades)
2. Use as descrições para criar critérios de recrutamento
3. Exemplo:
   ```
   Synth: Maria, 45 anos
   - Literacia Digital: Baixo (0.32)
   - Capacidade Motora: Muito Alto (0.95)
   - Disponibilidade de Tempo: Muito Baixo (0.15)

   Critérios de recrutamento:
   "Mulher 40-50 anos, pouca experiência com tecnologia,
    sem limitações motoras, agenda muito ocupada"
   ```

---

## Para Desenvolvedores

### Estrutura de Dados

```python
# SimulationAttributes (synth["simulation_attributes"])
{
    "observables": {
        "digital_literacy": 0.42,        # [0,1]
        "similar_tool_experience": 0.35, # [0,1]
        "motor_ability": 0.85,           # [0,1]
        "time_availability": 0.28,       # [0,1]
        "domain_expertise": 0.55         # [0,1]
    },
    "latent_traits": {
        "capability_mean": 0.45,          # Derivado
        "trust_mean": 0.38,               # Derivado
        "friction_tolerance_mean": 0.32,  # Derivado
        "exploration_prob": 0.41          # Derivado
    }
}
```

### Gerando Synths com Observáveis Correlacionados

```python
from synth_lab.gen_synth.simulation_attributes import generate_simulation_attributes

# Geração considera demografia para ajustar observáveis
simulation_attrs = generate_simulation_attributes(
    rng=random_generator,
    deficiencias=synth["deficiencias"],
    demografia=synth["demografia"]  # NOVO: usado para correlação
)

# Resultado: observáveis correlacionados com perfil demográfico
# Ex: Escolaridade alta → digital_literacy tende a ser maior
```

### Derivando Latentes

```python
from synth_lab.gen_synth.simulation_attributes import derive_latent_traits

# Latentes são SEMPRE derivadas de observáveis
latent = derive_latent_traits(observables)

# Fórmulas:
# capability_mean = 0.40*DL + 0.35*EXP + 0.15*MOT + 0.10*DOM
# trust_mean = 0.60*EXP + 0.40*DL
# friction_tolerance_mean = 0.40*TIME + 0.35*DL + 0.25*EXP
# exploration_prob = 0.50*DL + 0.30*(1-EXP) + 0.20*TIME
```

### Convertendo Valor para Label

```python
from synth_lab.services.observable_labels import value_to_label

label = value_to_label(0.42)  # Retorna "Médio"
label = value_to_label(0.15)  # Retorna "Muito Baixo"
label = value_to_label(0.85)  # Retorna "Muito Alto"
```

### Passando Contexto de Simulação para Entrevistas

```python
from synth_lab.services.research_agentic.context import SimulationContext

# Quando entrevista está conectada a uma simulação
context = SimulationContext(
    synth_id="abc123",
    analysis_id="analysis_456",
    attempt_rate=0.80,   # 80% tentou usar
    success_rate=0.60,   # 60% teve sucesso
    failure_rate=0.40,   # 40% falhou
    n_executions=1000
)

# Passado para format_interviewee_instructions()
# O synth "sabe" seu desempenho e responde coerentemente
```

### API Response (GET /synths/{id})

```json
{
  "id": "abc123",
  "nome": "Maria Silva",
  "simulation_attributes": {
    "observables_formatted": [
      {
        "key": "digital_literacy",
        "name": "Literacia Digital",
        "value": 0.42,
        "label": "Médio",
        "description": "Familiaridade com tecnologia e interfaces digitais"
      },
      // ... outros observáveis
    ],
    "raw": {
      "observables": { ... },
      "latent_traits": { ... }
    }
  }
}
```

---

## Testando

### Unit Tests

```bash
# Testar derivação de latentes
pytest tests/unit/test_simulation_attributes.py -v

# Testar labels
pytest tests/unit/test_observable_labels.py -v
```

### Integration Tests

```bash
# Testar correlação observáveis/demográficos
pytest tests/integration/test_synth_generation.py -v

# Testar contexto em entrevistas
pytest tests/integration/test_interview_context.py -v
```

---

## Troubleshooting

### Observáveis não aparecem no frontend
- Verifique se o backend retorna `simulation_attributes` no response
- Verifique se o tipo TypeScript `SynthDetail` inclui `simulation_attributes`

### Latentes visíveis onde não deveriam
- Frontend NUNCA deve exibir `latent_traits`
- Verifique se está usando `observables_formatted` (não `raw.latent_traits`)

### Entrevista incoerente com simulação
- Verifique se `SimulationContext` está sendo passado para o entrevistado
- Verifique se as taxas estão corretas (attempt + success + failure ≈ 1)
