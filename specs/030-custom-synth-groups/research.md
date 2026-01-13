# Research Report: Grupos de Synths Customizados

**Feature Branch**: `030-custom-synth-groups`
**Date**: 2026-01-12

## Executive Summary

This feature extends the existing synth generation system to support custom demographic distributions. The current system uses fixed IBGE distributions; this feature allows PMs to create groups with customized distributions for specific target audiences.

---

## 1. Existing Synth Generation System Analysis

### Current Architecture

**Generation Flow** (`src/synth_lab/gen_synth/`):
1. `synth_builder.py` - Orchestrator that assembles synths
2. `demographics.py` - Age, gender, education, location, family composition
3. `disabilities.py` - Visual, auditory, motor, cognitive disabilities
4. `psychographics.py` - Interests, cognitive contracts
5. `simulation_attributes.py` - Observable attributes (digital_literacy, domain_expertise, etc.)

**Key Finding**: The generation modules currently use hardcoded IBGE distributions loaded from `data/config/ibge_distributions.json`. They need to be modified to accept custom distributions as parameters.

### Current Distribution Sources

| Factor | Current Source | Default Values |
|--------|----------------|----------------|
| Age (faixas_etarias) | IBGE config | 15-29: 26%, 30-44: 27%, 45-59: 24%, 60+: 23% |
| Education (escolaridade) | IBGE config | sem_instrucao: 6.8%, fundamental: 32.9%, medio: 31.4%, superior: 28.9% |
| Disabilities | IBGE PNS 2019 | ~8.4% prevalence, uniform severity |
| Family Composition | IBGE config | unipessoal: 15%, casal_sem_filhos: 20%, casal_com_filhos: 35%, monoparental: 18%, multigeracional: 12% |
| Domain Expertise | Beta(3,3) | Mean ~0.50 (symmetric) |

---

## 2. Database Schema Analysis

### Current SynthGroup Table

```sql
synth_groups (
  id: String(50) PK - format: grp_[a-f0-9]{8}
  name: String(100) NOT NULL
  description: Text NULLABLE
  created_at: String(50) ISO timestamp
)
```

**Decision**: Add `config` JSONB column to store distribution parameters.

**Rationale**:
- JSONB allows flexible schema for distribution configurations
- No need to alter existing synth generation for backwards compatibility
- Group config can be used to regenerate synths with same distributions

### Proposed Migration

```sql
ALTER TABLE synth_groups
ADD COLUMN config JSONB DEFAULT NULL;
```

---

## 3. API Design Decisions

### Endpoint Structure

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/synth-groups` | GET | List all groups (existing) |
| `/api/synth-groups/{id}` | GET | Get group details with config (existing, extend response) |
| `/api/synth-groups` | POST | Create new group with custom config (new) |

**Decision**: Extend existing endpoints rather than create new ones.

**Rationale**:
- `synth_groups.py` router already exists
- Adding config to create endpoint is backwards-compatible
- GET detail already returns synth_count, adding config is natural extension

### Request/Response Schemas

**Create Request** (new):
```json
{
  "name": "Aposentados 60+",
  "description": "Grupo para simular previdência",
  "config": {
    "n_synths": 500,
    "distributions": {
      "idade": {"15-29": 0.05, "30-44": 0.05, "45-59": 0.10, "60+": 0.80},
      "escolaridade": {"sem_instrucao": 0.10, "fundamental": 0.40, "medio": 0.30, "superior": 0.20},
      "deficiencias": {
        "taxa_com_deficiencia": 0.25,
        "distribuicao_severidade": {"nenhuma": 0.00, "leve": 0.10, "moderada": 0.25, "severa": 0.30, "total": 0.35}
      },
      "composicao_familiar": {"unipessoal": 0.30, "casal_sem_filhos": 0.40, "casal_com_filhos": 0.10, "monoparental": 0.10, "multigeracional": 0.10},
      "domain_expertise": {"alpha": 2, "beta": 5}
    }
  }
}
```

**Create Response**:
```json
{
  "id": "grp_abc12345",
  "name": "Aposentados 60+",
  "description": "Grupo para simular previdência",
  "created_at": "2026-01-12T10:30:00Z",
  "synths_count": 500
}
```

---

## 4. Generation Logic Modifications

### Demographics Module Changes

**Current**: `generate_demographics(config: dict)` uses `config["ibge"]["faixas_etarias"]`

**Change**: Accept optional `custom_distributions` parameter that overrides IBGE defaults

```python
def generate_demographics(
    config: dict,
    custom_distributions: dict | None = None
) -> dict:
    # If custom_distributions provided, merge with config
    # Otherwise, use default IBGE distributions
```

### Disabilities Module Changes

**Current**: Fixed 8.4% disability rate with uniform severity distribution

**Change**: Accept `taxa_com_deficiencia` and `distribuicao_severidade` parameters

```python
def generate_disabilities(
    taxa_com_deficiencia: float = 0.084,
    distribuicao_severidade: dict | None = None
) -> dict:
    # Use provided rate instead of hardcoded
    # Apply provided severity distribution
```

### Domain Expertise Changes

**Current**: `Beta(3, 3)` fixed distribution for domain_expertise

**Change**: Accept `alpha` and `beta` parameters

```python
def generate_domain_expertise(
    alpha: float = 3.0,
    beta: float = 3.0
) -> float:
    # Use provided parameters for Beta distribution
```

---

## 5. Education Internal Mapping

### Decision: Internal Expansion Happens in Backend

When user selects "Fundamental = 40%", backend expands to:
- `fundamental_incompleto`: 40% × 0.763 = 30.5%
- `fundamental_completo`: 40% × 0.237 = 9.5%

**Rationale**:
- User shouldn't need to configure 8+ education levels
- Internal ratios are IBGE-based and stable
- Simplifies frontend UI significantly

### Expansion Ratios (IBGE)

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

## 6. Disability Severity Logic

### Decision: Dynamic Distribution Based on Rate

| Condition | "nenhuma" in pool | Distribution |
|-----------|-------------------|--------------|
| rate <= 8% (IBGE) | Yes | Uniform (20% each) |
| rate > 8% | No | Weighted to severe (leve: 10%, moderada: 25%, severa: 30%, total: 35%) |

**Rationale**:
- At IBGE rate, disabilities are realistically distributed
- Higher rates suggest intentional targeting of PcD population
- "nenhuma" in pool ensures some synths have disabilities without impairment in that category

### Total Mapping

| Category | "total" maps to |
|----------|-----------------|
| Visual | "cegueira" |
| Auditory | "surdez" |
| Motor | "severa" (no "total" exists) |
| Cognitive | "severa" (no "total" exists) |

---

## 7. Frontend Implementation

### Slider-Histograma Component

**Decision**: Create reusable `DistributionSlider` component

**Behavior**:
1. Visual bar shows percentage filled
2. Dragging adjusts percentage
3. Other sliders in group auto-redistribute to maintain 100%
4. Real-time update on drag

### Redistribution Algorithm

```typescript
function redistributeSliders(
  sliders: { key: string; value: number }[],
  changedKey: string,
  newValue: number
): { key: string; value: number }[] {
  const others = sliders.filter(s => s.key !== changedKey);
  const currentTotal = others.reduce((sum, s) => sum + s.value, 0);
  const targetTotal = 100 - newValue;

  // Proportionally scale other sliders
  const ratio = currentTotal > 0 ? targetTotal / currentTotal : 0;
  return sliders.map(s =>
    s.key === changedKey
      ? { ...s, value: newValue }
      : { ...s, value: Math.round(s.value * ratio * 100) / 100 }
  );
}
```

### State Management

**Decision**: Local React state with useReducer for complex distribution state

**Rationale**:
- Distribution state is form-local, not shared
- useReducer handles complex interdependent updates
- Only POST to server on "Gerar Synths" click

---

## 8. Default Group Seeding

### Decision: Seed Default Group with Explicit Config

The "Default" group (id: `grp_00000001` or `default`) must have config populated with IBGE values.

**Migration Approach**:
1. Add `config` column to `synth_groups` table
2. Run data migration to set Default group config
3. Frontend uses Default config as base for "Baseado em" dropdown

---

## 9. Files to Create/Modify

### Backend (src/synth_lab/)

| File | Action | Description |
|------|--------|-------------|
| `api/routers/synth_groups.py` | Modify | Add POST with config, extend GET detail |
| `api/schemas/synth_group.py` | Create | Pydantic schemas for request/response |
| `services/synth_group_service.py` | Modify | Add create_with_config method |
| `repositories/synth_group_repository.py` | Modify | Support config JSONB column |
| `domain/entities/synth_group.py` | Modify | Add config field to entity |
| `gen_synth/demographics.py` | Modify | Accept custom_distributions |
| `gen_synth/disabilities.py` | Modify | Accept rate and severity config |
| `gen_synth/simulation_attributes.py` | Modify | Accept alpha/beta for expertise |
| `gen_synth/synth_builder.py` | Modify | Pass custom config to generators |
| `alembic/versions/xxx_add_config_column.py` | Create | Migration for config column |

### Frontend (frontend/src/)

| File | Action | Description |
|------|--------|-------------|
| `services/synth-groups-api.ts` | Modify | Add create with config |
| `hooks/use-synth-groups.ts` | Create | useQuery/useMutation hooks |
| `lib/query-keys.ts` | Modify | Add synth-groups keys |
| `components/synths/CreateSynthGroupModal.tsx` | Create | Main modal component |
| `components/synths/DistributionSlider.tsx` | Create | Slider-histogram component |
| `components/synths/DistributionSliderGroup.tsx` | Create | Group with reset button |
| `components/synths/SynthGroupSelect.tsx` | Create | Dropdown for "Baseado em" |
| `pages/SynthsPage.tsx` | Modify | Add group selection UI |
| `types/synthGroup.ts` | Modify | Add config types |

---

## 10. Alternatives Considered

### Distribution Storage

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| JSONB column | Flexible, queryable | Schema evolution harder | **Selected** |
| Separate table | Normalized, typed | Over-engineering | Rejected |
| Config file reference | Simple | Can't customize per-group | Rejected |

### Synth Generation Timing

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| Generate on group create | Simple UX, immediate | Blocking request | **Selected** |
| Background job | Non-blocking | Complex, requires job queue | Rejected |
| Lazy generation | On-demand | Unpredictable latency | Rejected |

### Slider Behavior

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| Auto-redistribute | Intuitive | Complex implementation | **Selected** |
| Lock total at 100 | Simple | Confusing UX | Rejected |
| Allow >100, normalize | Flexible | Error-prone | Rejected |

---

## 11. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Synth generation slow | Medium | Medium | Show loading state, consider pagination |
| Distribution validation errors | Low | Low | Validate sum = 100% before submit |
| Default group missing config | Low | High | Migration must seed config |
| Slider UX confusion | Medium | Low | Clear labels, "Reset to IBGE" button |

---

## Summary of Key Decisions

1. **Storage**: JSONB column `config` in `synth_groups` table
2. **API**: Extend existing endpoints, POST creates group + generates synths
3. **Generation**: Synchronous (blocking request), show loading state
4. **Education**: 4-level UI, 8-level internal expansion in backend
5. **Disabilities**: Dynamic severity distribution based on rate threshold
6. **Frontend**: useReducer for complex slider state, auto-redistribution
7. **Default Group**: Seed with explicit IBGE config via migration
