# Data Model: Narrative Mechanism Configuration

**Feature**: 039-narrative-mechanism-config
**Date**: 2026-02-04

## Entity Relationship Diagram

```
┌─────────────────────────┐
│   mechanism_definitions │
├─────────────────────────┤
│ id: UUID (PK)           │
│ key: VARCHAR(50) UNIQUE │
│ label_pt: VARCHAR(100)  │
│ description: TEXT       │
│ created_at: TIMESTAMP   │
│ updated_at: TIMESTAMP   │
└───────────┬─────────────┘
            │ 1
            │
            │ N
┌───────────▼─────────────┐
│    mechanism_options    │
├─────────────────────────┤
│ id: UUID (PK)           │
│ mechanism_id: UUID (FK) │
│ label: VARCHAR(100)     │
│ value: NUMERIC(3,2)     │
│ display_order: INTEGER  │
│ created_at: TIMESTAMP   │
└─────────────────────────┘

┌─────────────────────────────┐
│       feature_types         │
├─────────────────────────────┤
│ id: UUID (PK)               │
│ key: VARCHAR(50) UNIQUE     │
│ label_pt: VARCHAR(100)      │
│ description: TEXT           │
│ amplifies_mechanisms: JSONB │
│ created_at: TIMESTAMP       │
└─────────────────────────────┘
```

## Entities

### MechanismDefinition

Define um mecanismo de feature que pode ser configurado pelo usuário.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-generated | Identificador único |
| key | VARCHAR(50) | UNIQUE, NOT NULL | Chave programática (ex: "irreversibility") |
| label_pt | VARCHAR(100) | NOT NULL | Label para exibição em português |
| description | TEXT | NOT NULL | Descrição explicativa do mecanismo |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Data de criação |
| updated_at | TIMESTAMP | NULL | Data da última atualização |

**Validation Rules**:
- `key` deve conter apenas letras minúsculas e underscores
- `key` deve ser único no sistema
- `label_pt` não pode ser vazio

**State Transitions**: N/A (entidade estática, apenas CRUD)

---

### MechanismOption

Uma opção textual para um mecanismo, com valor numérico associado.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-generated | Identificador único |
| mechanism_id | UUID | FK → mechanism_definitions(id), NOT NULL | Mecanismo pai |
| label | VARCHAR(100) | NOT NULL | Texto da opção (ex: "irreversível") |
| value | NUMERIC(3,2) | NOT NULL, CHECK (0 ≤ value ≤ 1) | Valor numérico [0.0, 1.0] |
| display_order | INTEGER | NOT NULL | Ordem de exibição no dropdown |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Data de criação |

**Validation Rules**:
- `value` deve estar no intervalo [0.0, 1.0]
- `display_order` deve ser único por mechanism_id
- `label` não pode ser vazio

**Relationships**:
- BELONGS_TO MechanismDefinition (many-to-one)

**State Transitions**: N/A (entidade estática, apenas CRUD)

---

### FeatureType

Categoria de feature que amplifica certos mecanismos.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-generated | Identificador único |
| key | VARCHAR(50) | UNIQUE, NOT NULL | Chave programática (ex: "financial") |
| label_pt | VARCHAR(100) | NOT NULL | Label para exibição em português |
| description | TEXT | NULL | Descrição do tipo de feature |
| amplifies_mechanisms | JSONB | NOT NULL, DEFAULT '[]' | Lista de mechanism keys amplificados |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Data de criação |

**Validation Rules**:
- `key` deve conter apenas letras minúsculas e underscores
- `key` deve ser único no sistema
- `amplifies_mechanisms` deve ser array de strings válidas

**Example**:
```json
{
  "key": "financial",
  "label_pt": "Financeira",
  "description": "Features que envolvem transações financeiras",
  "amplifies_mechanisms": ["irreversibility", "institutional_trust"]
}
```

---

### NarrativeResponse (Transient - não persistido)

Resposta da LLM para geração de narrativa. Usado apenas em memória.

| Field | Type | Description |
|-------|------|-------------|
| inferred_types | string[] | Tipos de feature inferidos pela LLM |
| narrative_template | string | Texto narrativo com placeholders {key} |
| selected_mechanisms | SelectedMechanism[] | Mecanismos selecionados com default |
| excluded_mechanisms | string[] | Keys dos mecanismos não relevantes |

**SelectedMechanism**:
```typescript
{
  key: string;           // mechanism key
  default_option_id: string;  // UUID da opção default escolhida
}
```

---

## Indexes

```sql
-- mechanism_definitions
CREATE UNIQUE INDEX idx_mechanism_definitions_key ON mechanism_definitions(key);

-- mechanism_options
CREATE INDEX idx_mechanism_options_mechanism_id ON mechanism_options(mechanism_id);
CREATE UNIQUE INDEX idx_mechanism_options_order ON mechanism_options(mechanism_id, display_order);

-- feature_types
CREATE UNIQUE INDEX idx_feature_types_key ON feature_types(key);
```

---

## Migration Script Outline

```python
# alembic/versions/xxx_add_mechanism_tables.py

def upgrade():
    # 1. Create mechanism_definitions table
    op.create_table(
        'mechanism_definitions',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('key', sa.String(50), unique=True, nullable=False),
        sa.Column('label_pt', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )

    # 2. Create mechanism_options table
    op.create_table(
        'mechanism_options',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('mechanism_id', sa.UUID(), sa.ForeignKey('mechanism_definitions.id'), nullable=False),
        sa.Column('label', sa.String(100), nullable=False),
        sa.Column('value', sa.Numeric(3, 2), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('value >= 0 AND value <= 1', name='check_value_range'),
    )

    # 3. Create feature_types table
    op.create_table(
        'feature_types',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('key', sa.String(50), unique=True, nullable=False),
        sa.Column('label_pt', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('amplifies_mechanisms', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # 4. Create indexes
    op.create_index('idx_mechanism_options_mechanism_id', 'mechanism_options', ['mechanism_id'])
    op.create_unique_index('idx_mechanism_options_order', 'mechanism_options', ['mechanism_id', 'display_order'])

def downgrade():
    op.drop_table('feature_types')
    op.drop_table('mechanism_options')
    op.drop_table('mechanism_definitions')
```

---

## Seed Data

Será executado via `scripts/seed_mechanisms.py` após migration:

- 6 mechanism_definitions
- 30 mechanism_options (5 per mechanism)
- 5 feature_types

Detalhes em [research.md](./research.md#seed-data).
