# Quickstart Guide: Narrative Mechanism Configuration

**Feature**: 039-narrative-mechanism-config
**Audience**: Developers integrating with the mechanism configuration and narrative generation APIs
**Last Updated**: 2026-02-04

## Overview

Feature 039 replaces the experiment wizard Step 2 sliders with a narrative-based interface. Mechanisms and their options are stored in the database, the LLM generates a narrative text with inline dropdowns for relevant mechanisms, and users adjust intensities by selecting options from dropdowns embedded in the text.

## Prerequisites

- Database migrated with mechanism_definitions, mechanism_options, and feature_types tables
- Seed data loaded (6 mechanisms, 30 options, 5 feature types)
- Experiment exists with name and hypothesis defined

## Step 1: List Available Mechanisms

**Endpoint**: `GET /api/v1/mechanisms`

```bash
curl -X GET http://localhost:8000/api/v1/mechanisms
```

**Response** (200 OK):
```json
{
  "mechanisms": [
    {
      "id": "uuid-irreversibility",
      "key": "irreversibility",
      "label_pt": "Irreversibilidade",
      "description": "Grau em que a ação não pode ser desfeita",
      "options": [
        { "id": "uuid-opt-1", "label": "totalmente reversível", "value": 0.0, "display_order": 1 },
        { "id": "uuid-opt-2", "label": "reversível com algum esforço", "value": 0.25, "display_order": 2 },
        { "id": "uuid-opt-3", "label": "parcialmente reversível", "value": 0.5, "display_order": 3 },
        { "id": "uuid-opt-4", "label": "difícil de reverter", "value": 0.75, "display_order": 4 },
        { "id": "uuid-opt-5", "label": "irreversível", "value": 1.0, "display_order": 5 }
      ]
    },
    {
      "id": "uuid-network-effect",
      "key": "network_effect",
      "label_pt": "Efeito de Rede",
      "description": "Grau em que o valor depende de outros usarem",
      "options": [...]
    }
  ]
}
```

**What This Returns**:
- All 6 mechanism definitions with their 5 text options each
- Options are ordered by `display_order` (ascending)
- Values range from 0.0 (minimal intensity) to 1.0 (maximum intensity)

## Step 2: Generate Narrative with Placeholders

**Endpoint**: `POST /api/v1/experiments/generate-narrative`

```bash
curl -X POST http://localhost:8000/api/v1/experiments/generate-narrative \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Pix via WhatsApp",
    "hypothesis": "Usuários preferem pagar pelo app de mensagens",
    "description": "Permite enviar dinheiro para contatos do WhatsApp sem sair do app"
  }'
```

**Response** (200 OK):
```json
{
  "inferred_types": ["financial", "social"],
  "narrative_template": "O Pix via WhatsApp permite transferências instantâneas diretamente no chat. A transação é {irreversibility} após confirmada. O usuário precisa {institutional_trust} no banco para autorizar. O valor cresce quando {network_effect} do seu círculo usa.",
  "selected_mechanisms": [
    { "key": "irreversibility", "default_option_id": "uuid-opt-5" },
    { "key": "institutional_trust", "default_option_id": "uuid-opt-3" },
    { "key": "network_effect", "default_option_id": "uuid-opt-2" }
  ],
  "excluded_mechanisms": ["learning_curve", "habit_displacement", "social_visibility"]
}
```

**What Happens**:
1. LLM analyzes the feature description and infers types (financial, social, etc.)
2. Based on types, LLM selects 2-4 relevant mechanisms
3. LLM generates narrative text in Portuguese with `{mechanism_key}` placeholders
4. LLM chooses the most appropriate default option for each mechanism
5. Response includes excluded mechanisms (not relevant for this feature)

## Step 3: Render Narrative with Dropdowns

Frontend parses the template and renders dropdowns:

```typescript
// Parse template into parts
const parts = narrative_template.split(/(\{[a-z_]+\})/g);

// Render each part
parts.map((part, i) => {
  const match = part.match(/\{([a-z_]+)\}/);
  if (match) {
    const key = match[1];
    const mechanism = mechanisms.find(m => m.key === key);
    const selectedMech = selected_mechanisms.find(sm => sm.key === key);
    return (
      <MechanismDropdown
        key={i}
        mechanism={mechanism}
        defaultOptionId={selectedMech.default_option_id}
        onChange={(optionId) => handleChange(key, optionId)}
      />
    );
  }
  return <span key={i}>{part}</span>;
});
```

**Result**: Text like "A transação é [dropdown: irreversível ▼] após confirmada."

## Step 4: Extract Values for Experiment

When user clicks "Continue", extract numeric values:

```typescript
function getMechanismValues(): Record<string, number> {
  const values: Record<string, number> = {};

  for (const [key, optionId] of Object.entries(selectedOptions)) {
    const mechanism = mechanisms.find(m => m.key === key);
    const option = mechanism.options.find(o => o.id === optionId);
    values[key] = option.value;
  }

  return values;
}

// Example output:
// {
//   "irreversibility": 1.0,
//   "institutional_trust": 0.5,
//   "network_effect": 0.25
// }
```

These values are saved to the experiment's mechanism configuration.

## Feature Types Reference

**Endpoint**: `GET /api/v1/mechanisms/feature-types`

```bash
curl -X GET http://localhost:8000/api/v1/mechanisms/feature-types
```

**Response** (200 OK):
```json
{
  "feature_types": [
    {
      "id": "uuid-financial",
      "key": "financial",
      "label_pt": "Financeira",
      "description": "Features que envolvem transações financeiras",
      "amplifies_mechanisms": ["irreversibility", "institutional_trust"]
    },
    {
      "id": "uuid-social",
      "key": "social",
      "label_pt": "Social",
      "description": "Features com componente social ou de rede",
      "amplifies_mechanisms": ["network_effect", "social_visibility"]
    }
  ]
}
```

**Note**: Feature types are inferred by the LLM, not selected by users. This endpoint is for admin/debug purposes.

## Frontend Integration

```typescript
// Hook for fetching mechanisms
const { data: mechanisms } = useMechanisms();

// Mutation for generating narrative
const generateNarrative = useGenerateNarrative();

// Generate on mount or when regenerate is clicked
const handleGenerate = async () => {
  const result = await generateNarrative.mutateAsync({
    name: experiment.name,
    hypothesis: experiment.hypothesis,
    description: experiment.description
  });
  setNarrativeData(result);
};

// Component structure
<NarrativeMechanismEditor
  template={narrativeData.narrative_template}
  mechanisms={mechanisms}
  selectedMechanisms={narrativeData.selected_mechanisms}
  onValuesChange={setMechanismValues}
/>
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `422` Name too short | name < 3 chars | Provide descriptive feature name |
| `422` Hypothesis too short | hypothesis < 10 chars | Provide complete hypothesis |
| `500` LLM generation failed | gpt-4o-mini timeout or error | Retry with "Regenerar" button |
| `500` No mechanisms in DB | Seed data not loaded | Run `scripts/seed_mechanisms.py` |

## Regeneration

Users can click "Regenerar" to get a fresh narrative:

```typescript
const handleRegenerate = () => {
  generateNarrative.mutate({
    name: experiment.name,
    hypothesis: experiment.hypothesis,
    description: experiment.description
  });
};
```

Each regeneration may:
- Infer different feature types
- Select different mechanisms (within the relevant set)
- Generate different narrative text
- Choose different default options

## Mechanism Tooltips

Hovering over a dropdown shows the mechanism description:

```typescript
<TooltipProvider>
  <Tooltip>
    <TooltipTrigger asChild>
      <Select value={selectedOptionId} onValueChange={onChange}>
        {/* options */}
      </Select>
    </TooltipTrigger>
    <TooltipContent>
      <p className="font-medium">{mechanism.label_pt}</p>
      <p className="text-sm text-muted-foreground">{mechanism.description}</p>
    </TooltipContent>
  </Tooltip>
</TooltipProvider>
```

## API Reference

Full OpenAPI specification: [contracts/api.yaml](contracts/api.yaml)
