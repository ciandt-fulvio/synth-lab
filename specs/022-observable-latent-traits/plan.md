# Implementation Plan: Observable vs. Latent Traits Model

**Branch**: `022-observable-latent-traits` | **Date**: 2025-12-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/022-observable-latent-traits/spec.md`

## Summary

Refatorar o modelo de synths para separar claramente características **observáveis** (visíveis ao PM para recrutamento) de **latentes** (usadas internamente nas simulações). A implementação envolve:

1. **Backend**: Ajustar geração de observáveis baseada em demográficos, manter derivação de latentes
2. **Frontend**: Exibir apenas observáveis com labels textuais, ocultar latentes
3. **Entrevistas**: Passar contexto de simulação (taxas sucesso/falha) e observáveis para o prompt do entrevistado

## Technical Context

**Language/Version**: Python 3.13+ (backend), TypeScript 5.5+ (frontend)
**Primary Dependencies**: FastAPI 0.109+, Pydantic 2.5+, React 18, TanStack Query, shadcn/ui
**Storage**: SQLite 3 with JSON1 extension (output/synthlab.db)
**Testing**: pytest 8.0+, pytest-asyncio
**Target Platform**: Linux/macOS server, Web browser
**Project Type**: Web application (backend + frontend)
**Performance Goals**: N/A (feature não adiciona endpoints críticos)
**Constraints**: Backward compatibility total com simulações existentes
**Scale/Scope**: ~15 arquivos modificados, 0 novos endpoints

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. TDD/BDD | ✅ PASS | Tests primeiro para novas funções de derivação e geração |
| II. Fast Tests (<5s) | ✅ PASS | Unit tests para funções puras de derivação/labeling |
| III. Complete Tests Before PR | ✅ PASS | Integration tests para fluxo synth→simulação→entrevista |
| IV. Frequent Commits | ✅ PASS | Commits por camada: domain → gen_synth → services → api → frontend |
| V. Simplicity | ✅ PASS | Reutiliza estruturas existentes, mínimas adições |
| VI. Language | ✅ PASS | Código em inglês, labels em português |
| VII. Architecture | ✅ PASS | Segue padrões existentes: router→service→repository |
| VIII. Other | ✅ PASS | DRY: reutiliza SimulationObservables/LatentTraits existentes |

**Gate Result**: ✅ PASS - Nenhuma violação identificada

## Project Structure

### Documentation (this feature)

```text
specs/022-observable-latent-traits/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (API schemas)
│   └── synth-api.yaml   # Updated synth response schema
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
# Backend (Python)
src/synth_lab/
├── domain/entities/
│   └── simulation_attributes.py    # SimulationObservables, SimulationLatentTraits (EXISTS)
├── gen_synth/
│   └── simulation_attributes.py    # generate_observables(), derive_latent_traits() (MODIFY)
├── services/
│   ├── simulation/
│   │   └── engine.py               # MonteCarloEngine (NO CHANGE - uses latent_traits)
│   └── research_agentic/
│       ├── instructions.py         # format_interviewee_instructions() (MODIFY)
│       └── runner.py               # generate_initial_context() (MODIFY)
├── api/
│   ├── routers/
│   │   └── synths.py               # GET /synths/{id} (MODIFY response)
│   └── schemas/
│       └── synth_schemas.py        # SimulationAttributesResponse (NEW)
└── models/
    └── synth.py                    # SynthDetail (MODIFY)

# Frontend (TypeScript/React)
frontend/src/
├── types/
│   └── synth.ts                    # SimulationAttributes interface (MODIFY)
├── components/
│   └── synths/
│       ├── SynthDetailDialog.tsx   # Add observables tab (MODIFY)
│       └── ObservablesDisplay.tsx  # New component for observables (NEW)
├── lib/
│   └── observable-labels.ts        # Label mapping utilities (NEW)
└── hooks/
    └── use-synths.ts               # No change (already fetches SynthDetail)

# Tests
tests/
├── unit/
│   ├── test_simulation_attributes.py     # Test derivation formulas (MODIFY)
│   └── test_observable_labels.py         # Test label mapping (NEW)
└── integration/
    └── test_interview_context.py         # Test simulation context in interviews (NEW)
```

**Structure Decision**: Web application pattern (backend + frontend). Reutiliza estrutura existente com mínimas adições.

## Complexity Tracking

> Nenhuma violação de constitution identificada - seção não aplicável.

## Phase 0: Research Summary

### Design Decisions

1. **Geração de Observáveis baseada em Demográficos**
   - Decision: Ajustar parâmetros Beta usando escolaridade, deficiência, composição familiar
   - Rationale: Mantém correlação estatística realista entre perfil demográfico e capacidades
   - Alternatives: Geração independente (rejeitado: perde coerência)

2. **Labels Textuais para Observáveis**
   - Decision: 5 níveis (Muito Baixo, Baixo, Médio, Alto, Muito Alto) com ranges [0-0.2, 0.2-0.4, 0.4-0.6, 0.6-0.8, 0.8-1.0] (exceto para escolaridade que devemos mapear diretamente para níveis formais)
   - Rationale: Padrão UX comum, fácil compreensão pelo PM
   - Alternatives: 3 níveis (rejeitado: menos granularidade), percentuais (rejeitado: menos intuitivo)

3. **Contexto de Simulação em Entrevistas**
   - Decision: Passar taxas de tentativa/sucesso/falha via system prompt
   - Rationale: Synth precisa "saber" seu comportamento para responder coerentemente
   - Alternatives: Inferir do perfil (rejeitado: perde especificidade da simulação)

4. **Backward Compatibility**
   - Decision: Manter todas as variáveis existentes, apenas adicionar labels e ajustar geração
   - Rationale: Simulações existentes não podem quebrar
   - Alternatives: Refatoração completa (rejeitado: risco alto)

## Phase 1: Implementation Approach

### Layer 1: Domain/Entities (No Changes)
- `SimulationObservables` e `SimulationLatentTraits` já existem e estão corretos
- Nenhuma mudança estrutural necessária

### Layer 2: Generation (gen_synth)
- **Modify** `generate_observables()` para aceitar `demografia` além de `deficiencias`
- **Implement** ajuste de parâmetros Beta baseado em escolaridade, idade, composição familiar
- **Keep** `derive_latent_traits()` sem alterações (fórmulas já corretas)

### Layer 3: Services
- **Modify** `format_interviewee_instructions()` para incluir observáveis formatados
- **Modify** `generate_initial_context()` para aceitar contexto de simulação (taxas)
- **Add** função para formatar observáveis com labels em português

### Layer 4: API/Schemas
- **Add** `SimulationAttributesResponse` schema com observáveis e labels
- **Modify** `SynthDetail` response para incluir simulation_attributes formatados
- **No new endpoints** - apenas modificação de response

### Layer 5: Frontend Types
- **Add** `SimulationObservables`, `SimulationLatentTraits`, `SimulationAttributes` interfaces
- **Add** `ObservableLabel` type com níveis e descrições

### Layer 6: Frontend Components
- **Add** `ObservablesDisplay.tsx` - componente para exibir observáveis com labels
- **Modify** `SynthDetailDialog.tsx` - adicionar tab/seção de capacidades
- **Add** `observable-labels.ts` - mapeamento de valores para labels

### Layer 7: Integration
- **Modify** fluxo de entrevista para passar contexto de simulação quando disponível
- **Add** testes de integração para verificar coerência

## Test Strategy

### Unit Tests (Fast Battery < 5s)
- `test_derive_latent_traits()` - Verificar fórmulas de derivação
- `test_generate_observables_with_demographics()` - Verificar correlações
- `test_observable_to_label()` - Verificar mapeamento de labels
- `test_format_simulation_context()` - Verificar formatação para prompt

### Integration Tests
- `test_synth_generation_observables_correlation()` - Gerar 100 synths, verificar correlações
- `test_interview_with_simulation_context()` - Verificar prompt inclui taxas
- `test_api_synth_detail_includes_observables()` - Verificar response schema

### Contract Tests
- `test_synth_detail_schema()` - Validar schema de resposta atualizado

## Dependencies & Risks

### Dependencies
- Nenhuma nova dependência de pacotes
- Depende de estrutura existente de synths e simulações

### Risks
| Risk | Mitigation |
|------|------------|
| Quebrar simulações existentes | Manter todas variáveis, apenas adicionar |
| Performance de geração | Funções Beta são O(1), sem impacto |
| Complexidade de prompt | Limitar contexto a informações essenciais |

## Next Steps

1. Execute `/speckit.tasks` para gerar tasks.md com tarefas detalhadas
2. Implementar em ordem: domain → gen_synth → services → api → frontend
3. Commits frequentes por camada
4. PR quando todos os testes passarem
