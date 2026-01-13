# Quickstart: Grupos de Synths Customizados

**Feature Branch**: `030-custom-synth-groups`
**Date**: 2026-01-12

## Visão Geral

Esta feature permite criar grupos de synths com distribuições demográficas customizadas para simular públicos específicos (aposentados, PcD, universitários, etc.).

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────────┐ │
│  │ CreateSynthGroup│  │DistributionSlider│  │ SynthGroupSelect        │ │
│  │ Modal.tsx       │  │ Group.tsx        │  │ .tsx                    │ │
│  └────────┬────────┘  └────────┬────────┘  └────────────┬─────────────┘ │
│           │                    │                        │               │
│  ┌────────▼────────────────────▼────────────────────────▼─────────────┐ │
│  │                    useSynthGroups.ts                                │ │
│  │           (useQuery, useMutation + queryKeys)                       │ │
│  └────────────────────────────────┬───────────────────────────────────┘ │
│                                   │                                     │
│  ┌────────────────────────────────▼───────────────────────────────────┐ │
│  │                    synth-groups-api.ts                              │ │
│  │                       (fetchAPI calls)                              │ │
│  └────────────────────────────────┬───────────────────────────────────┘ │
└───────────────────────────────────┼─────────────────────────────────────┘
                                    │ HTTP
┌───────────────────────────────────▼─────────────────────────────────────┐
│                              BACKEND                                      │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │               api/routers/synth_groups.py                           │ │
│  │   POST /synth-groups → create_with_config()                         │ │
│  │   GET  /synth-groups → list_groups()                                │ │
│  │   GET  /synth-groups/{id} → get_group_detail()                      │ │
│  └────────────────────────────────┬───────────────────────────────────┘ │
│                                   │                                     │
│  ┌────────────────────────────────▼───────────────────────────────────┐ │
│  │              services/synth_group_service.py                        │ │
│  │   - create_with_config() → validates + generates synths             │ │
│  │   - Uses gen_synth modules with custom distributions                │ │
│  └────────────────────────────────┬───────────────────────────────────┘ │
│                                   │                                     │
│  ┌────────────────────────────────▼───────────────────────────────────┐ │
│  │            repositories/synth_group_repository.py                   │ │
│  │   - create(group_with_config) → INSERT with JSONB                   │ │
│  │   - get_detail() → SELECT with config column                        │ │
│  └────────────────────────────────┬───────────────────────────────────┘ │
│                                   │                                     │
│  ┌────────────────────────────────▼───────────────────────────────────┐ │
│  │                         gen_synth/                                  │ │
│  │   demographics.py  - aceita custom_distributions                    │ │
│  │   disabilities.py  - aceita taxa + severidade config                │ │
│  │   simulation_attributes.py - aceita alpha/beta expertise            │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Fluxo Principal

### 1. PM abre modal de criação

```typescript
// Frontend: pages/SynthsPage.tsx
const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

<Button onClick={() => setIsCreateModalOpen(true)}>
  Criar Grupo
</Button>

<CreateSynthGroupModal
  open={isCreateModalOpen}
  onClose={() => setIsCreateModalOpen(false)}
  onSuccess={(group) => {
    toast.success(`Grupo "${group.name}" criado com ${group.synths_count} synths`);
    setIsCreateModalOpen(false);
  }}
/>
```

### 2. PM configura distribuições

```typescript
// Frontend: components/synths/CreateSynthGroupModal.tsx
const [config, dispatch] = useReducer(configReducer, DEFAULT_GROUP_CONFIG);

// Quando slider muda
const handleSliderChange = (section: string, key: string, value: number) => {
  dispatch({ type: 'SET_SLIDER', section, key, value });
};

// Redistribui outros sliders automaticamente
function configReducer(state: GroupConfig, action: Action): GroupConfig {
  if (action.type === 'SET_SLIDER') {
    const newDistribution = redistributeSliders(
      state.distributions[action.section],
      action.key,
      action.value
    );
    return {
      ...state,
      distributions: {
        ...state.distributions,
        [action.section]: newDistribution
      }
    };
  }
  // ...
}
```

### 3. PM clica "Gerar Synths"

```typescript
// Frontend: hooks/useSynthGroups.ts
export function useCreateSynthGroup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateSynthGroupRequest) => createSynthGroup(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.synthGroups.all });
    },
  });
}

// Frontend: services/synth-groups-api.ts
export async function createSynthGroup(
  data: CreateSynthGroupRequest
): Promise<SynthGroupCreateResponse> {
  return fetchAPI<SynthGroupCreateResponse>('/synth-groups', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
```

### 4. Backend cria grupo e gera synths

```python
# Backend: api/routers/synth_groups.py
@router.post("", status_code=201)
async def create_synth_group(
    request: CreateSynthGroupRequest,
    service: SynthGroupService = Depends(get_synth_group_service)
) -> SynthGroupCreateResponse:
    return await service.create_with_config(
        name=request.name,
        description=request.description,
        config=request.config.model_dump()
    )
```

```python
# Backend: services/synth_group_service.py
async def create_with_config(
    self,
    name: str,
    description: str | None,
    config: dict
) -> SynthGroupCreateResponse:
    # 1. Validate config
    validated_config = self._validate_config(config)

    # 2. Create group entity
    group = SynthGroup(
        id=generate_group_id(),
        name=name,
        description=description,
        config=validated_config
    )

    # 3. Generate synths with custom distributions
    synths = self._generate_synths_with_config(validated_config)

    # 4. Persist group and synths (atomic transaction)
    await self.repository.create_with_synths(group, synths)

    return SynthGroupCreateResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        created_at=group.created_at,
        synths_count=len(synths)
    )
```

```python
# Backend: services/synth_group_service.py
def _generate_synths_with_config(self, config: dict) -> list[Synth]:
    """Generate synths using custom distributions."""
    synths = []
    distributions = config["distributions"]

    for _ in range(config["n_synths"]):
        # Generate demographics with custom distributions
        demographics = generate_demographics(
            self.ibge_config,
            custom_distributions={
                "idade": distributions["idade"],
                "escolaridade": self._expand_education(distributions["escolaridade"]),
                "composicao_familiar": distributions["composicao_familiar"]
            }
        )

        # Generate disabilities with custom rate/severity
        disabilities = generate_disabilities(
            taxa=distributions["deficiencias"]["taxa_com_deficiencia"],
            severidade_dist=distributions["deficiencias"]["distribuicao_severidade"]
        )

        # Generate observables with custom expertise params
        observables = generate_observables(
            demographics,
            disabilities,
            expertise_alpha=distributions["domain_expertise"]["alpha"],
            expertise_beta=distributions["domain_expertise"]["beta"]
        )

        synth = assemble_synth(demographics, disabilities, observables)
        synths.append(synth)

    return synths
```

---

## Estrutura de Arquivos

### Backend (src/synth_lab/)

```
api/
├── routers/
│   └── synth_groups.py     # Modificar: adicionar POST com config
├── schemas/
│   └── synth_group.py      # Criar: Pydantic schemas

services/
└── synth_group_service.py  # Modificar: create_with_config

repositories/
└── synth_group_repository.py  # Modificar: suportar config JSONB

domain/
├── entities/
│   └── synth_group.py      # Modificar: adicionar campo config
└── constants/
    └── group_defaults.py   # Criar: constantes IBGE

gen_synth/
├── demographics.py         # Modificar: aceitar custom_distributions
├── disabilities.py         # Modificar: aceitar taxa/severidade
└── simulation_attributes.py # Modificar: aceitar alpha/beta

alembic/versions/
└── xxx_add_config_column.py  # Criar: migration
```

### Frontend (frontend/src/)

```
components/synths/
├── CreateSynthGroupModal.tsx     # Criar: modal principal
├── DistributionSlider.tsx        # Criar: slider-histograma
├── DistributionSliderGroup.tsx   # Criar: grupo de sliders
└── SynthGroupSelect.tsx          # Criar: select "Baseado em"

hooks/
└── use-synth-groups.ts           # Criar: hooks React Query

services/
└── synth-groups-api.ts           # Modificar: adicionar create

lib/
└── query-keys.ts                 # Modificar: adicionar keys

types/
└── synthGroup.ts                 # Modificar: adicionar GroupConfig
```

---

## Comandos de Desenvolvimento

### Backend

```bash
# Rodar servidor
cd /Users/fulvio/Projects/synth-lab
uv run uvicorn synth_lab.api.main:app --reload

# Rodar testes
pytest tests/

# Criar migration
uv run alembic revision --autogenerate -m "add_config_column_synth_groups"

# Aplicar migration
uv run alembic upgrade head

# Lint
ruff check . && ruff format .
```

### Frontend

```bash
# Rodar dev server
cd frontend && npm run dev

# Lint
npm run lint

# Type check
npm run typecheck
```

---

## Valores Default (IBGE)

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

## Testes Esperados

### Backend

```python
# tests/services/test_synth_group_service.py

def test_create_with_config_generates_500_synths():
    """FR-002: Sistema DEVE gerar 500 synths ao criar grupo."""
    config = DEFAULT_GROUP_CONFIG.copy()
    result = service.create_with_config("Test", None, config)
    assert result.synths_count == 500

def test_create_with_custom_age_distribution():
    """FR-007: Sistema DEVE permitir configurar distribuição de Idade."""
    config = DEFAULT_GROUP_CONFIG.copy()
    config["distributions"]["idade"] = {
        "15-29": 0.05, "30-44": 0.05, "45-59": 0.10, "60+": 0.80
    }
    result = service.create_with_config("Aposentados", None, config)
    # Verificar distribuição dos synths gerados
    synths = repository.get_synths_by_group(result.id)
    age_60_plus = sum(1 for s in synths if s.data["demografia"]["idade"] >= 60)
    assert 0.75 <= age_60_plus / 500 <= 0.85  # ±5% tolerância

def test_config_validation_rejects_invalid_sum():
    """Distribuições devem somar 1.0."""
    config = DEFAULT_GROUP_CONFIG.copy()
    config["distributions"]["idade"] = {
        "15-29": 0.50, "30-44": 0.50, "45-59": 0.50, "60+": 0.50
    }
    with pytest.raises(ValidationError):
        service.create_with_config("Invalid", None, config)
```

### Frontend

```typescript
// tests/components/DistributionSliderGroup.test.tsx

test('redistributes other sliders when one changes', () => {
  const initial = [
    { key: '15-29', value: 0.26 },
    { key: '30-44', value: 0.27 },
    { key: '45-59', value: 0.24 },
    { key: '60+', value: 0.23 }
  ];

  const result = redistributeSliders(initial, '60+', 0.80);

  expect(result.find(s => s.key === '60+')?.value).toBe(0.80);
  expect(result.reduce((sum, s) => sum + s.value, 0)).toBeCloseTo(1.0);
});

test('shows loading state during synth generation', async () => {
  render(<CreateSynthGroupModal open={true} />);

  await userEvent.type(screen.getByLabelText('Nome'), 'Teste');
  await userEvent.click(screen.getByText('Gerar Synths'));

  expect(screen.getByText('Gerando synths...')).toBeInTheDocument();
});
```

---

## Próximos Passos

1. **Migration**: Criar migration Alembic para adicionar coluna `config`
2. **Backend**: Modificar gen_synth modules para aceitar parâmetros
3. **API**: Atualizar schemas e router
4. **Frontend**: Criar componentes de UI (sliders, modal)
5. **Integração**: Conectar frontend ao backend
6. **Testes**: Escrever testes unitários e de integração
