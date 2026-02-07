# Implementation Plan: Mechanism & Sensitivity Update

**Branch**: `040-mechanism-sensitivity-update` | **Date**: 2026-02-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/040-mechanism-sensitivity-update/spec.md`

## Summary

Substituir o motor de simulação baseado em scorecard por um sistema baseado em **9 mecanismos** (com distribuições Beta) × **7 sensibilidades** (derivadas de YAML rules) → **9 estados emergentes** (7 barreiras + 2 appeals) que ajustam a probabilidade de adoção. Remove scorecard dimensions, observáveis e latent traits do pipeline de simulação.

## Technical Context

**Language/Version**: Python 3.13+ (backend) + TypeScript (frontend mínimo: types + MechanismEditor)
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0+, Pydantic, NumPy, PyYAML
**Storage**: PostgreSQL 14+ (JSONB fields — sem migração de schema)
**Testing**: pytest (unit + integration, mocked — sem chamadas LLM)
**Target Platform**: Linux server (Railway), macOS dev
**Project Type**: Web application (backend + frontend mínimo para novos mecanismos)
**Performance Goals**: 100 synths × 100 executions < 1 segundo
**Constraints**: Backward compatibility com experimentos usando 6 mecanismos
**Scale/Scope**: ~17 arquivos modificados/criados, 0 endpoints novos

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Status | Notas |
|-----------|--------|-------|
| I. Test-First (TDD) | ✅ PASS | Testes escritos antes de cada módulo |
| II. Fast Tests < 5s | ✅ PASS | Unit tests são pure-Python, sem I/O |
| III. Complete Tests antes de PR | ✅ PASS | Unit + integration antes de merge |
| IV. Commits atômicos | ✅ PASS | 1 commit por fase lógica |
| V. Simplicidade | ✅ PASS | Arquivos < 500 linhas, funções < 30 linhas |
| VI. Language | ✅ PASS | Código em inglês, docs em português, YAML em português |
| VII. Architecture | ✅ PASS | Service layer para lógica, domain para entidades |

### Post-Design Re-Check

| Princípio | Status | Notas |
|-----------|--------|-------|
| I. TDD | ✅ PASS | Validation blocks + pytest para cada módulo |
| V. Simplicidade | ✅ PASS | Nenhum arquivo excede 500 linhas |
| VII. Architecture | ✅ PASS | Segue padrão: domain → services → gen_synth |

## Project Structure

### Documentation (this feature)

```text
specs/040-mechanism-sensitivity-update/
├── spec.md              # Especificação funcional
├── plan.md              # Este arquivo
├── research.md          # Decisões técnicas
├── data-model.md        # Modelo de dados
├── quickstart.md        # Guia de início rápido
├── contracts/           # Contratos de API internos
│   └── simulation-api.md
└── checklists/
    └── requirements.md  # Checklist de qualidade
```

### Source Code (repository root)

```text
src/synth_lab/
├── config/
│   └── sensitivity_rules.yaml          # NOVO: YAML rules para derivação
├── domain/entities/
│   ├── user_sensitivities.py           # REESCRITA: 6 → 7 campos
│   ├── feature_mechanisms.py           # ESTENDIDA: 6 → 9 campos
│   └── emergent_state.py              # REESCRITA: 4 deltas → 9 estados
├── services/
│   ├── sensitivity_deriver.py          # NOVO: motor de derivação YAML
│   └── simulation/
│       ├── emergent_calculator.py      # NOVO: calculador 9 estados emergentes
│       ├── feature_monte_carlo.py      # NOVO: motor MC baseado em mecanismos+Beta
│       ├── engine.py                   # DEPRECATED (mantido para referência)
│       ├── probability.py              # DEPRECATED (mantido para referência)
│       ├── sample_state.py             # DEPRECATED (mantido para referência)
│       └── mechanism_interaction.py    # DEPRECATED (substituído por emergent_calculator)
├── gen_synth/
│   ├── synth_builder.py               # MODIFICADA: integrar derive_sensitivities
│   └── simulation_attributes.py       # DEPRECATED (observáveis não mais gerados)
└── scorecard_estimator.py              # NÃO MODIFICADA (LLM scorer ainda existe para outro uso)

scripts/
└── seed_mechanisms.py                  # MODIFICADA: +3 mecanismos e opções

tests/
├── unit/
│   ├── services/
│   │   ├── test_sensitivity_deriver.py     # NOVO
│   │   └── simulation/
│   │       ├── test_emergent_calculator.py  # NOVO
│   │       └── test_feature_monte_carlo.py  # NOVO
│   └── domain/
│       └── test_user_sensitivities.py       # REESCRITA
└── integration/
    └── test_synth_sensitivity_integration.py # NOVO
```

frontend/src/
├── types/
│   └── simulation.ts                    # MODIFICADA: +3 campos em FeatureMechanisms
└── components/experiments/
    ├── MechanismEditor.tsx              # MODIFICADA: +3 sliders (MECHANISM_CONFIGS + DEFAULT_MECHANISMS)
    └── NarrativeMechanismEditor.tsx     # NÃO MODIFICADA (dinâmico, carrega do banco)
```

**Structure Decision**: Backend + frontend mínimo. Segue estrutura existente: `domain/entities/` para modelos, `services/` para lógica, `gen_synth/` para geração, `config/` para YAML. Frontend: apenas MechanismEditor (hardcoded) precisa de update — o sistema de narrativa é dinâmico. Sem novos endpoints API.

## Design Decisions

### D-001: Beta Distribution para Mecanismos

Cada mecanismo é amostrado de `Beta(mean × 15, (1-mean) × 15)` em cada execução MC, em vez de usar valor fixo. Isso introduz variação natural que produz distribuições de outcomes mais realistas.

**Exceções**: mean=0.0 → não amostra (fica 0.0). mean=1.0 → não amostra (fica 1.0). Evita distribuições Beta degeneradas (`Beta(0, 15)` e `Beta(15, 0)`).

Ver [research.md#RQ-002](./research.md) para detalhes.

### D-002: YAML Rules Determinísticas

Sensibilidades são derivadas de forma determinística via YAML. Mesmos dados demográficos → mesmas sensibilidades → reprodutibilidade garantida. Versão do config rastreada em metadados.

Ver [research.md#RQ-003](./research.md) para detalhes.

### D-003: Base Probability = 0.5

O novo motor usa probabilidade base neutra (0.5), ajustada por barreiras (-) e appeals (+):

```
prob = 0.5 − sum(7 barriers) × 0.15 + sum(2 appeals) × 0.20
prob = clamp(prob, 0.0, 1.0)
adopted = Bernoulli(prob)
```

Pesos de calibração (0.15, 0.20) são valores iniciais. Tuning é out of scope.

### D-004: Outcome Simplificado

O motor antigo tinha 3 outcomes (did_not_try, failed, success). O novo motor tem 2 outcomes (adopted, not_adopted), alinhado com o modelo de barreiras/appeals que determina probabilidade de adoção binária.

### D-005: Deprecação Sem Remoção

Arquivos antigos (`engine.py`, `probability.py`, `sample_state.py`, `mechanism_interaction.py`, `simulation_attributes.py`) serão marcados como deprecated com docstring update, mas **não removidos**. Isso permite:
- Referência para debugging
- Rollback se necessário
- Testes antigos continuam compilando

### D-006: Sensibilidades em Synths Existentes

Synths gerados antes desta feature não terão `sensitivities` no seu data dict. O motor de simulação verifica:
1. Se `synth.data.sensitivities` existe → usa
2. Se não existe → deriva on-demand via `derive_sensitivities(synth.data)`
3. Se não há dados demográficos → defaults (0.5 para todas)

## Implementation Phases

### Fase 1: Foundation (Sensibilidades) — P1

**Entrega**: Sistema de derivação de sensibilidades + integração no synth builder.

1. Criar `src/synth_lab/config/sensitivity_rules.yaml` com 7 sensibilidades
2. Criar `src/synth_lab/services/sensitivity_deriver.py` com funções:
   - `load_sensitivity_rules()`, `get_nested_value()`, `evaluate_condition()`, `derive_sensitivities()`
3. Reescrever `src/synth_lab/domain/entities/user_sensitivities.py` com 7 campos
4. Testes unit para deriver (30+ test cases)
5. Integrar `derive_sensitivities()` em `synth_builder.py`
6. Teste de integração: synth gerado tem 7 sensibilidades

### Fase 2: Novos Mecanismos — P2

**Entrega**: 9 mecanismos disponíveis no sistema.

1. Estender `FeatureMechanisms` com 3 novos campos
2. Atualizar `has_any_mechanism()` para incluir novos campos
3. Adicionar 3 mecanismos + 15 opções ao seed script
4. Testes unit para backward compatibility (6 mechs → 9 mechs)

### Fase 3: Emergent States + Monte Carlo — P3

**Entrega**: Motor de simulação completo com estados emergentes.

1. Reescrever `EmergentState` entity com 9 estados
2. Criar `emergent_calculator.py` com novo `calculate_emergent_state()`
3. Criar `feature_monte_carlo.py` com novo motor (Beta sampling + emergent states)
4. Testes unit para calculador emergente (fórmulas, edge cases)
5. Testes unit para motor MC (variance, reproduction, performance)
6. Teste de integração: populações diferentes produzem resultados diferentes

## Complexity Tracking

> Nenhuma violação de constituição detectada. Seção vazia.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
