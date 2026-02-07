# Quickstart: Mechanism & Sensitivity Update

**Feature**: 040-mechanism-sensitivity-update
**Date**: 2026-02-06

## Pré-requisitos

```bash
# Garantir que está na branch correta
git checkout 040-mechanism-sensitivity-update

# Garantir ambiente ativo
source .venv/bin/activate  # ou equivalente

# Instalar dependências
uv pip install --system -e .
```

## Fluxo de Desenvolvimento

### Fase 1: Sensibilidades

```bash
# 1. Criar YAML rules
# → src/synth_lab/config/sensitivity_rules.yaml

# 2. Criar deriver
# → src/synth_lab/services/sensitivity_deriver.py

# 3. Validar deriver
python src/synth_lab/services/sensitivity_deriver.py

# 4. Rodar testes
pytest tests/unit/services/test_sensitivity_deriver.py -v

# 5. Integrar no synth_builder
# → src/synth_lab/gen_synth/synth_builder.py (adicionar derive_sensitivities)

# 6. Validar integração
pytest tests/integration/test_synth_sensitivity_integration.py -v
```

### Fase 2: Novos Mecanismos

```bash
# 1. Atualizar entidade
# → src/synth_lab/domain/entities/feature_mechanisms.py (adicionar 3 campos)

# 2. Atualizar seed script
# → scripts/seed_mechanisms.py (adicionar 3 definições)

# 3. Rodar seed no banco local
DATABASE_URL="postgresql://synthlab:synthlab@localhost:5432/synthlab" python scripts/seed_mechanisms.py

# 4. Validar
pytest tests/unit/domain/test_feature_mechanisms.py -v
```

### Fase 3: Emergent States + Monte Carlo

```bash
# 1. Reescrever EmergentState entity
# → src/synth_lab/domain/entities/emergent_state.py (9 estados)

# 2. Reescrever UserSensitivities entity
# → src/synth_lab/domain/entities/user_sensitivities.py (7 campos)

# 3. Criar novo calculador emergente
# → src/synth_lab/services/simulation/emergent_calculator.py

# 4. Criar novo motor Monte Carlo
# → src/synth_lab/services/simulation/feature_monte_carlo.py

# 5. Rodar testes completos
pytest tests/ -v --tb=short
```

## Verificação Rápida

```bash
# Rodar todos os testes da feature
pytest tests/unit/services/test_sensitivity_deriver.py \
       tests/unit/services/simulation/test_emergent_calculator.py \
       tests/unit/services/simulation/test_feature_monte_carlo.py \
       tests/integration/test_synth_sensitivity_integration.py \
       -v

# Validar linting
ruff check src/synth_lab/services/sensitivity_deriver.py \
           src/synth_lab/services/simulation/emergent_calculator.py \
           src/synth_lab/services/simulation/feature_monte_carlo.py \
           src/synth_lab/domain/entities/user_sensitivities.py \
           src/synth_lab/domain/entities/feature_mechanisms.py \
           src/synth_lab/domain/entities/emergent_state.py
```

## Arquivos Chave

| Arquivo | Ação | Descrição |
|---------|------|-----------|
| `src/synth_lab/config/sensitivity_rules.yaml` | NOVO | YAML rules para derivação |
| `src/synth_lab/services/sensitivity_deriver.py` | NOVO | Motor de derivação |
| `src/synth_lab/domain/entities/user_sensitivities.py` | REESCRITA | 7 sensibilidades |
| `src/synth_lab/domain/entities/feature_mechanisms.py` | ESTENDIDA | +3 mecanismos |
| `src/synth_lab/domain/entities/emergent_state.py` | REESCRITA | 9 estados emergentes |
| `src/synth_lab/services/simulation/emergent_calculator.py` | NOVO | Calculador emergente |
| `src/synth_lab/services/simulation/feature_monte_carlo.py` | NOVO | Novo motor Monte Carlo |
| `src/synth_lab/gen_synth/synth_builder.py` | MODIFICADA | Integrar sensibilidades |
| `scripts/seed_mechanisms.py` | MODIFICADA | +3 mecanismos no seed |
