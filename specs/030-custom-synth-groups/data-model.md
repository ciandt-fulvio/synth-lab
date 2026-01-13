# Data Model: Grupos de Synths Customizados

**Feature Branch**: `030-custom-synth-groups`
**Date**: 2026-01-12

## Entity Overview

```
┌─────────────────────┐       1:N       ┌─────────────────┐
│    SynthGroup       │────────────────▶│     Synth       │
│  (with config)      │                 │                 │
└─────────────────────┘                 └─────────────────┘
```

---

## 1. SynthGroup Entity (Modified)

### Schema

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | String(50) | PK, format: `grp_[a-f0-9]{8}` | Unique identifier |
| `name` | String(100) | NOT NULL | Group name |
| `description` | Text | NULLABLE, max 50 chars | Optional description |
| `created_at` | String(50) | NOT NULL, ISO 8601 | Creation timestamp |
| `config` | JSONB | NULLABLE | **NEW** Distribution configuration |

### Config JSONB Structure

```json
{
  "n_synths": 500,
  "distributions": {
    "idade": {
      "15-29": 0.26,
      "30-44": 0.27,
      "45-59": 0.24,
      "60+": 0.23
    },
    "escolaridade": {
      "sem_instrucao": 0.068,
      "fundamental": 0.329,
      "medio": 0.314,
      "superior": 0.289
    },
    "deficiencias": {
      "taxa_com_deficiencia": 0.084,
      "distribuicao_severidade": {
        "nenhuma": 0.20,
        "leve": 0.20,
        "moderada": 0.20,
        "severa": 0.20,
        "total": 0.20
      }
    },
    "composicao_familiar": {
      "unipessoal": 0.15,
      "casal_sem_filhos": 0.20,
      "casal_com_filhos": 0.35,
      "monoparental": 0.18,
      "multigeracional": 0.12
    },
    "domain_expertise": {
      "alpha": 3,
      "beta": 3
    }
  }
}
```

### Indexes

| Index Name | Columns | Type |
|------------|---------|------|
| `idx_synth_groups_created` | `created_at` | DESC |
| `idx_synth_groups_name` | `name` | BTREE |

---

## 2. Synth Entity (Unchanged)

The existing `Synth` entity remains unchanged. Synths are generated based on the `SynthGroup.config` and linked via `synth_group_id` FK.

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | String(50) | PK |
| `synth_group_id` | String(50) | FK → synth_groups.id, NULLABLE |
| `nome` | String(200) | NOT NULL |
| `descricao` | Text | NULLABLE |
| `link_photo` | Text | NULLABLE |
| `avatar_path` | Text | NULLABLE |
| `created_at` | String(50) | NOT NULL |
| `version` | String(20) | DEFAULT "2.0.0" |
| `data` | JSON | NULLABLE (demographics, disabilities, observables) |

---

## 3. Value Objects

### IdadeDistribution

```python
class IdadeDistribution(TypedDict):
    """Age distribution weights (must sum to 1.0)"""
    faixa_15_29: float  # "15-29"
    faixa_30_44: float  # "30-44"
    faixa_45_59: float  # "45-59"
    faixa_60_plus: float  # "60+"
```

### EscolaridadeDistribution

```python
class EscolaridadeDistribution(TypedDict):
    """Education distribution weights (must sum to 1.0)"""
    sem_instrucao: float
    fundamental: float  # Expands to incompleto/completo
    medio: float  # Expands to incompleto/completo
    superior: float  # Expands to incompleto/completo/pos
```

### DeficienciasConfig

```python
class SeveridadeDistribution(TypedDict):
    """Severity distribution weights (must sum to 1.0)"""
    nenhuma: float
    leve: float
    moderada: float
    severa: float
    total: float

class DeficienciasConfig(TypedDict):
    """Disability configuration"""
    taxa_com_deficiencia: float  # 0.0 to 1.0
    distribuicao_severidade: SeveridadeDistribution
```

### ComposicaoFamiliarDistribution

```python
class ComposicaoFamiliarDistribution(TypedDict):
    """Family composition weights (must sum to 1.0)"""
    unipessoal: float
    casal_sem_filhos: float
    casal_com_filhos: float
    monoparental: float
    multigeracional: float
```

### DomainExpertiseConfig

```python
class DomainExpertiseConfig(TypedDict):
    """Beta distribution parameters for domain expertise"""
    alpha: float  # Shape parameter (> 0)
    beta: float  # Shape parameter (> 0)
```

### GroupConfig (Complete)

```python
class GroupDistributions(TypedDict):
    """All distribution configurations"""
    idade: IdadeDistribution
    escolaridade: EscolaridadeDistribution
    deficiencias: DeficienciasConfig
    composicao_familiar: ComposicaoFamiliarDistribution
    domain_expertise: DomainExpertiseConfig

class GroupConfig(TypedDict):
    """Complete group configuration"""
    n_synths: int
    distributions: GroupDistributions
```

---

## 4. Validation Rules

### Distribution Weights

| Distribution | Validation | Tolerance |
|--------------|------------|-----------|
| `idade` | Sum of weights = 1.0 | ±0.01 |
| `escolaridade` | Sum of weights = 1.0 | ±0.01 |
| `composicao_familiar` | Sum of weights = 1.0 | ±0.01 |
| `distribuicao_severidade` | Sum of weights = 1.0 | ±0.01 |

### Value Ranges

| Field | Min | Max | Validation |
|-------|-----|-----|------------|
| `taxa_com_deficiencia` | 0.0 | 1.0 | Float in range |
| `alpha` | 0.1 | 10.0 | Positive float |
| `beta` | 0.1 | 10.0 | Positive float |
| `n_synths` | 1 | 1000 | Positive integer (fixed at 500 for MVP) |

### Name Constraints

| Field | Min Length | Max Length | Pattern |
|-------|------------|------------|---------|
| `name` | 1 | 100 | Non-empty string |
| `description` | 0 | 50 | Optional string |

---

## 5. Default Values (IBGE)

```python
DEFAULT_GROUP_CONFIG = {
    "n_synths": 500,
    "distributions": {
        "idade": {
            "15-29": 0.26,
            "30-44": 0.27,
            "45-59": 0.24,
            "60+": 0.23
        },
        "escolaridade": {
            "sem_instrucao": 0.068,
            "fundamental": 0.329,
            "medio": 0.314,
            "superior": 0.289
        },
        "deficiencias": {
            "taxa_com_deficiencia": 0.084,
            "distribuicao_severidade": {
                "nenhuma": 0.20,
                "leve": 0.20,
                "moderada": 0.20,
                "severa": 0.20,
                "total": 0.20
            }
        },
        "composicao_familiar": {
            "unipessoal": 0.15,
            "casal_sem_filhos": 0.20,
            "casal_com_filhos": 0.35,
            "monoparental": 0.18,
            "multigeracional": 0.12
        },
        "domain_expertise": {
            "alpha": 3,
            "beta": 3
        }
    }
}
```

---

## 6. Education Internal Expansion

The 4-level UI escolaridade expands internally to 8 levels:

| UI Level | Internal Expansion |
|----------|-------------------|
| `sem_instrucao` | `sem_instrucao` (100%) |
| `fundamental` | `fundamental_incompleto` (76.3%) + `fundamental_completo` (23.7%) |
| `medio` | `medio_incompleto` (13.4%) + `medio_completo` (86.6%) |
| `superior` | `superior_incompleto` (18.3%) + `superior_completo` (60.6%) + `pos_graduacao` (21.1%) |

### Expansion Constants

```python
ESCOLARIDADE_INTERNAL_RATIOS = {
    "fundamental": {
        "fundamental_incompleto": 0.763,
        "fundamental_completo": 0.237
    },
    "medio": {
        "medio_incompleto": 0.134,
        "medio_completo": 0.866
    },
    "superior": {
        "superior_incompleto": 0.183,
        "superior_completo": 0.606,
        "pos_graduacao": 0.211
    }
}
```

---

## 7. State Transitions

### SynthGroup Lifecycle

```
┌──────────┐     create()      ┌──────────┐
│  (none)  │ ─────────────────▶│ Created  │
└──────────┘                   └──────────┘
                                    │
                                    │ (immutable)
                                    │
                               No transitions
                               (groups are immutable)
```

### Synth Generation Flow

```
┌─────────────┐     validate_config()     ┌─────────────┐
│ Config JSON │ ─────────────────────────▶│ Valid Config│
└─────────────┘                           └─────────────┘
                                               │
                                               │ expand_education()
                                               ▼
                                          ┌─────────────┐
                                          │ Full Config │
                                          └─────────────┘
                                               │
                                               │ generate_synths(n=500)
                                               ▼
                                          ┌─────────────┐
                                          │ 500 Synths  │
                                          └─────────────┘
                                               │
                                               │ persist_group()
                                               ▼
                                          ┌─────────────┐
                                          │ SynthGroup  │
                                          │ + Synths    │
                                          └─────────────┘
```

---

## 8. Migration SQL

```sql
-- Migration: Add config column to synth_groups
ALTER TABLE synth_groups
ADD COLUMN config JSONB DEFAULT NULL;

-- Index for config queries (optional, for future filtering)
CREATE INDEX idx_synth_groups_config ON synth_groups USING GIN (config);

-- Seed Default group with IBGE config
UPDATE synth_groups
SET config = '{
    "n_synths": 500,
    "distributions": {
        "idade": {"15-29": 0.26, "30-44": 0.27, "45-59": 0.24, "60+": 0.23},
        "escolaridade": {"sem_instrucao": 0.068, "fundamental": 0.329, "medio": 0.314, "superior": 0.289},
        "deficiencias": {
            "taxa_com_deficiencia": 0.084,
            "distribuicao_severidade": {"nenhuma": 0.20, "leve": 0.20, "moderada": 0.20, "severa": 0.20, "total": 0.20}
        },
        "composicao_familiar": {"unipessoal": 0.15, "casal_sem_filhos": 0.20, "casal_com_filhos": 0.35, "monoparental": 0.18, "multigeracional": 0.12},
        "domain_expertise": {"alpha": 3, "beta": 3}
    }
}'::jsonb
WHERE name = 'Default';
```

---

## 9. Relationships

| Parent | Child | Cardinality | FK Behavior |
|--------|-------|-------------|-------------|
| SynthGroup | Synth | 1:N | SET NULL on delete |

- When a SynthGroup is deleted, its synths remain but with `synth_group_id = NULL`
- Synths can exist without a group (orphaned synths)
- A synth belongs to at most one group

---

## 10. Query Patterns

### List Groups with Synth Count
```sql
SELECT sg.id, sg.name, sg.description, sg.created_at, sg.config,
       COUNT(s.id) as synths_count
FROM synth_groups sg
LEFT JOIN synths s ON sg.id = s.synth_group_id
GROUP BY sg.id
ORDER BY sg.created_at DESC;
```

### Get Group Detail with Config
```sql
SELECT id, name, description, created_at, config
FROM synth_groups
WHERE id = ?;
```

### Create Group with Config
```sql
INSERT INTO synth_groups (id, name, description, created_at, config)
VALUES (?, ?, ?, ?, ?::jsonb);
```
