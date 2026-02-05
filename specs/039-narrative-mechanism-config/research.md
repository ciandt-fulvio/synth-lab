# Research: Narrative Mechanism Configuration

**Feature**: 039-narrative-mechanism-config
**Date**: 2026-02-04

## Research Questions

### RQ-001: Como estruturar o prompt para LLM gerar narrativa com placeholders?

**Decision**: Prompt estruturado com mecanismos e tipos carregados do banco.

**Rationale**:
- Prompt deve incluir todas as definições de mecanismos e suas opções
- LLM retorna JSON estruturado com narrative_template e selected_mechanisms
- Usar OpenAI Structured Outputs (response_format) para garantir schema

**Prompt Structure**:
```
Você é um especialista em análise de features de produto.

## Tipos de Feature Disponíveis
{feature_types_from_db}

## Mecanismos e suas Opções
{mechanisms_with_options_from_db}

## Tarefa
Analise a feature descrita e:
1. Infira os tipos aplicáveis (1-3)
2. Selecione mecanismos relevantes (2-4) baseado nos tipos
3. Gere narrativa fluida em português com placeholders {mechanism_key}
4. Para cada mecanismo, escolha a opção default mais adequada

## Feature para Análise
Nome: {name}
Hipótese: {hypothesis}
Descrição: {description}

Retorne JSON no formato especificado.
```

**Alternatives Considered**:
- Few-shot examples: Descartado por aumentar tokens sem ganho significativo
- Chain-of-thought: Descartado por latência adicional desnecessária

---

### RQ-002: Qual modelo usar para geração de narrativa?

**Decision**: gpt-4o-mini

**Rationale**:
- Custo-benefício: ~10x mais barato que gpt-4o
- Latência: Média de 1-2s para prompts curtos
- Qualidade: Suficiente para inferência de tipos e geração de texto simples
- Structured outputs: Suportado nativamente

**Alternatives Considered**:
- gpt-4o: Melhor qualidade, mas custo/latência não justificam para este caso
- Claude: Não disponível na infraestrutura atual (OpenAI SDK)

---

### RQ-003: Como armazenar mecanismos e opções no banco?

**Decision**: Duas tabelas: mechanism_definitions e mechanism_options

**Rationale**:
- Tabelas separadas permitem N opções por mecanismo
- Facilita extensão sem código (adicionar opção = INSERT)
- Foreign key garante integridade referencial
- display_order permite ordenação personalizada

**Schema**:
```sql
mechanism_definitions (
  id UUID PRIMARY KEY,
  key VARCHAR(50) UNIQUE NOT NULL,
  label_pt VARCHAR(100) NOT NULL,
  description TEXT NOT NULL,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)

mechanism_options (
  id UUID PRIMARY KEY,
  mechanism_id UUID REFERENCES mechanism_definitions(id),
  label VARCHAR(100) NOT NULL,
  value NUMERIC(3,2) NOT NULL CHECK (value >= 0 AND value <= 1),
  display_order INTEGER NOT NULL,
  created_at TIMESTAMP
)
```

**Alternatives Considered**:
- JSONB em tabela única: Mais simples, mas dificulta queries por opção específica
- Enum no código: Inflexível, requer deploy para mudanças

---

### RQ-004: Como armazenar tipos de feature e seus mecanismos amplificados?

**Decision**: Tabela feature_types com JSONB para amplifies_mechanisms

**Rationale**:
- Lista de mecanismos amplificados é pequena e raramente consultada individualmente
- JSONB permite flexibilidade sem join tables
- Seed data inicial com 5 tipos predefinidos

**Schema**:
```sql
feature_types (
  id UUID PRIMARY KEY,
  key VARCHAR(50) UNIQUE NOT NULL,
  label_pt VARCHAR(100) NOT NULL,
  description TEXT,
  amplifies_mechanisms JSONB NOT NULL DEFAULT '[]',
  created_at TIMESTAMP
)
```

**Alternatives Considered**:
- Join table feature_types_mechanisms: Overengineering para lista pequena e estável

---

### RQ-005: Como renderizar dropdowns inline no texto narrativo?

**Decision**: Parse de template com regex para {mechanism_key} e renderização React

**Rationale**:
- Template usa placeholders no formato {key}
- Frontend faz split do texto por regex
- Cada placeholder é substituído por componente Select/Dropdown
- Estado local mantém seleções do usuário

**Implementation Pattern**:
```tsx
function NarrativeMechanismEditor({ template, mechanisms }) {
  const parts = template.split(/(\{[a-z_]+\})/g);

  return parts.map((part, i) => {
    const match = part.match(/\{([a-z_]+)\}/);
    if (match) {
      const key = match[1];
      const mechanism = mechanisms.find(m => m.key === key);
      return <MechanismDropdown key={i} mechanism={mechanism} />;
    }
    return <span key={i}>{part}</span>;
  });
}
```

**Alternatives Considered**:
- Markdown com custom renderer: Complexidade desnecessária
- Rich text editor: Overengineering para caso simples

---

### RQ-006: Como garantir que mecanismos do banco são usados no prompt?

**Decision**: Carregar mecanismos do banco antes de cada chamada LLM

**Rationale**:
- Garante que mudanças no banco são refletidas imediatamente
- Prompt é construído dinamicamente com dados atuais
- Cache opcional (5 min) para reduzir queries em alta carga

**Implementation**:
```python
async def generate_narrative(name, hypothesis, description):
    # 1. Load from DB
    mechanisms = await mechanism_repo.list_all_with_options()
    feature_types = await mechanism_repo.list_feature_types()

    # 2. Build prompt
    prompt = build_prompt(mechanisms, feature_types, name, hypothesis, description)

    # 3. Call LLM with structured output
    response = await llm_client.generate(prompt, response_format=NarrativeResponse)

    return response
```

**Alternatives Considered**:
- Hardcode no prompt: Inflexível, requer deploy para mudanças
- Cache longo: Risco de dados stale após UPDATE

---

## Seed Data

### Mechanism Definitions (6)

| Key | Label PT | Description |
|-----|----------|-------------|
| irreversibility | Irreversibilidade | Grau em que a ação não pode ser desfeita |
| network_effect | Efeito de Rede | Grau em que o valor depende de outros usarem |
| institutional_trust | Confiança Institucional | Grau em que requer confiar na instituição |
| habit_displacement | Substituição de Hábito | Grau em que substitui hábitos existentes |
| learning_curve | Curva de Aprendizado | Grau em que requer aprender algo novo |
| social_visibility | Visibilidade Social | Grau em que o uso é visível para outros |

### Mechanism Options (5 per mechanism)

| Order | Value | Example Labels (irreversibility) |
|-------|-------|----------------------------------|
| 1 | 0.00 | totalmente reversível |
| 2 | 0.25 | reversível com algum esforço |
| 3 | 0.50 | parcialmente reversível |
| 4 | 0.75 | difícil de reverter |
| 5 | 1.00 | irreversível |

### Feature Types (5)

| Key | Label PT | Amplifies |
|-----|----------|-----------|
| financial | Financeira | irreversibility, institutional_trust |
| social | Social | network_effect, social_visibility |
| aesthetic | Estética | (nenhum forte) |
| flow | Fluxo | learning_curve, habit_displacement |
| infra | Infraestrutura | institutional_trust |

---

## Technical Decisions Summary

| Topic | Decision | Reference |
|-------|----------|-----------|
| LLM Model | gpt-4o-mini | RQ-002 |
| DB Schema | 3 tables (definitions, options, types) | RQ-003, RQ-004 |
| Prompt Construction | Dynamic from DB | RQ-001, RQ-006 |
| Frontend Rendering | Regex split + React components | RQ-005 |
| Output Format | OpenAI Structured Outputs | RQ-001 |
