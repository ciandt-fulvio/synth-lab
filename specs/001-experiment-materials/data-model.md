# Data Model: Experiment Materials Upload

**Branch**: `001-experiment-materials`
**Date**: 2026-01-05

## Entities

### ExperimentMaterial (New)

Representa um arquivo anexado a um experimento (imagem, vídeo, documento).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `VARCHAR(50)` | PK | Identificador único (formato: `mat_{token_hex(6)}`) |
| `experiment_id` | `VARCHAR(50)` | FK, NOT NULL | Referência ao experimento pai |
| `file_type` | `VARCHAR(20)` | NOT NULL | Tipo: `image`, `video`, `document` |
| `file_url` | `TEXT` | NOT NULL | URL completa do arquivo no S3 |
| `thumbnail_url` | `TEXT` | NULLABLE | URL do thumbnail gerado |
| `file_name` | `VARCHAR(255)` | NOT NULL | Nome original do arquivo |
| `file_size` | `INTEGER` | NOT NULL | Tamanho em bytes |
| `mime_type` | `VARCHAR(100)` | NOT NULL | MIME type (e.g., `image/png`) |
| `material_type` | `VARCHAR(20)` | NOT NULL | Categoria: `design`, `prototype`, `competitor`, `spec`, `other` |
| `description` | `TEXT` | NULLABLE | Descrição gerada por IA (até 30 palavras) |
| `description_status` | `VARCHAR(20)` | NOT NULL, DEFAULT 'pending' | Status: `pending`, `generating`, `completed`, `failed` |
| `display_order` | `INTEGER` | NOT NULL | Ordem de exibição (0-indexed) |
| `created_at` | `TIMESTAMP` | NOT NULL, DEFAULT NOW() | Data de criação |

### Validation Rules

**file_type** - Enum:
- `image`: PNG, JPG, JPEG, WebP, GIF
- `video`: MP4, MOV, WebM
- `document`: PDF, TXT, MD

**material_type** - Enum:
- `design`: Wireframes, mockups, designs finais
- `prototype`: Protótipos interativos, demos
- `competitor`: Análise de concorrentes
- `spec`: Especificações, documentação
- `other`: Outros materiais

**description_status** - Enum:
- `pending`: Aguardando processamento
- `generating`: Em processamento pela IA
- `completed`: Descrição gerada com sucesso
- `failed`: Falha na geração

**Size Limits**:
- Images/Documents: max 25MB (26,214,400 bytes)
- Videos: max 100MB (104,857,600 bytes)
- Total per experiment: max 250MB
- Files per experiment: max 10

---

## Relationships

### Experiment ← ExperimentMaterial (1:N)

```
Experiment (1) ──────< (N) ExperimentMaterial
           │                    │
           │ experiments.id     │ experiment_materials.experiment_id
           └────────────────────┘
```

**Cascade Behavior**:
- `ON DELETE CASCADE`: Quando experimento é deletado, todos os materiais são removidos
- Arquivos no S3 devem ser deletados via job de cleanup

---

## SQLAlchemy ORM Model

```python
# models/orm/material.py
from sqlalchemy import ForeignKey, Index, String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from synth_lab.models.orm.base import Base

class ExperimentMaterial(Base):
    """
    Material file attached to an experiment.

    Stores images, videos, and documents uploaded by researchers
    for synth interview context.
    """
    __tablename__ = "experiment_materials"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    experiment_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    material_type: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships
    experiment: Mapped["Experiment"] = relationship(
        "Experiment",
        back_populates="materials",
    )

    __table_args__ = (
        Index("idx_experiment_materials_experiment", "experiment_id"),
        Index("idx_experiment_materials_type", "material_type"),
        Index("idx_experiment_materials_order", "experiment_id", "display_order"),
        Index("idx_experiment_materials_status", "description_status"),
    )
```

---

## Domain Entity (Pydantic)

```python
# domain/entities/experiment_material.py
from pydantic import BaseModel, Field, field_validator
import secrets
from datetime import datetime

def generate_material_id() -> str:
    return f"mat_{secrets.token_hex(6)}"

class ExperimentMaterial(BaseModel):
    """Domain entity for experiment material."""

    id: str = Field(default_factory=generate_material_id)
    experiment_id: str
    file_type: str = Field(pattern="^(image|video|document)$")
    file_url: str
    thumbnail_url: str | None = None
    file_name: str = Field(max_length=255)
    file_size: int = Field(gt=0)
    mime_type: str
    material_type: str = Field(pattern="^(design|prototype|competitor|spec|other)$")
    description: str | None = None
    description_status: str = Field(
        default="pending",
        pattern="^(pending|generating|completed|failed)$"
    )
    display_order: int = Field(ge=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("file_size")
    @classmethod
    def validate_file_size(cls, v: int, info) -> int:
        """Validate file size based on type."""
        # This is a basic check - actual limits enforced on upload
        max_size = 104_857_600  # 100MB
        if v > max_size:
            raise ValueError(f"File size {v} exceeds maximum {max_size}")
        return v
```

---

## API Schemas

```python
# api/schemas/materials.py
from pydantic import BaseModel, Field
from datetime import datetime

class MaterialUploadRequest(BaseModel):
    """Request for presigned upload URL."""
    file_name: str = Field(max_length=255)
    file_size: int = Field(gt=0, le=104_857_600)
    mime_type: str
    material_type: str = Field(pattern="^(design|prototype|competitor|spec|other)$")

class MaterialUploadResponse(BaseModel):
    """Response with presigned URL for upload."""
    material_id: str
    upload_url: str
    object_key: str
    expires_in: int  # seconds

class MaterialConfirmRequest(BaseModel):
    """Confirm upload completion."""
    material_id: str
    object_key: str

class MaterialResponse(BaseModel):
    """Material data for API responses."""
    id: str
    experiment_id: str
    file_type: str
    file_url: str
    thumbnail_url: str | None
    file_name: str
    file_size: int
    mime_type: str
    material_type: str
    description: str | None
    description_status: str
    display_order: int
    created_at: datetime

class MaterialReorderRequest(BaseModel):
    """Request to reorder materials."""
    material_ids: list[str]  # IDs na nova ordem
```

---

## Alembic Migration

```python
# alembic/versions/xxx_add_experiment_materials.py
"""Add experiment_materials table.

Revision ID: xxx
Create Date: 2026-01-05
"""
from alembic import op
import sqlalchemy as sa

revision = 'xxx'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'experiment_materials',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('experiment_id', sa.String(50), sa.ForeignKey('experiments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('file_type', sa.String(20), nullable=False),
        sa.Column('file_url', sa.Text(), nullable=False),
        sa.Column('thumbnail_url', sa.Text(), nullable=True),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('material_type', sa.String(20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('description_status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('display_order', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.String(50), nullable=False),
    )

    op.create_index('idx_experiment_materials_experiment', 'experiment_materials', ['experiment_id'])
    op.create_index('idx_experiment_materials_type', 'experiment_materials', ['material_type'])
    op.create_index('idx_experiment_materials_order', 'experiment_materials', ['experiment_id', 'display_order'])
    op.create_index('idx_experiment_materials_status', 'experiment_materials', ['description_status'])

def downgrade() -> None:
    op.drop_index('idx_experiment_materials_status', 'experiment_materials')
    op.drop_index('idx_experiment_materials_order', 'experiment_materials')
    op.drop_index('idx_experiment_materials_type', 'experiment_materials')
    op.drop_index('idx_experiment_materials_experiment', 'experiment_materials')
    op.drop_table('experiment_materials')
```

---

## State Transitions

### Description Status Machine

```
                    upload confirmed
                          │
                          ▼
                    ┌─────────┐
                    │ pending │
                    └────┬────┘
                         │ background job starts
                         ▼
                  ┌──────────────┐
                  │  generating  │
                  └──────┬───────┘
                         │
           ┌─────────────┴─────────────┐
           │                           │
           ▼                           ▼
    ┌────────────┐              ┌──────────┐
    │ completed  │              │  failed  │
    └────────────┘              └────┬─────┘
                                     │ retry
                                     ▼
                              ┌──────────────┐
                              │  generating  │
                              └──────────────┘
```

### Upload Flow

```
1. Client requests presigned URL
   → Backend creates material record (status: pending, file_url: empty)
   → Returns presigned URL + material_id

2. Client uploads to S3 directly
   → S3 stores file

3. Client confirms upload
   → Backend verifies file exists in S3
   → Backend updates file_url
   → Backend queues description generation
   → Returns material with status: pending

4. Background job generates description
   → Updates status: generating → completed/failed
```

---

## Repository Pattern

```python
# repositories/experiment_material_repository.py
class ExperimentMaterialRepository(BaseRepository):
    """Repository for experiment material operations."""

    def create(self, material: ExperimentMaterial) -> ExperimentMaterial:
        """Create new material record."""
        ...

    def get_by_id(self, material_id: str) -> ExperimentMaterial | None:
        """Get material by ID."""
        ...

    def list_by_experiment(
        self,
        experiment_id: str,
        order_by: str = "display_order"
    ) -> list[ExperimentMaterial]:
        """List all materials for an experiment."""
        ...

    def update_description(
        self,
        material_id: str,
        description: str | None,
        status: str
    ) -> None:
        """Update material description and status."""
        ...

    def reorder(
        self,
        experiment_id: str,
        material_ids: list[str]
    ) -> None:
        """Reorder materials by updating display_order."""
        ...

    def delete(self, material_id: str) -> None:
        """Delete material record."""
        ...

    def count_by_experiment(self, experiment_id: str) -> int:
        """Count materials for an experiment."""
        ...

    def get_total_size_by_experiment(self, experiment_id: str) -> int:
        """Get total file size for an experiment."""
        ...

    def get_pending_descriptions(self, limit: int = 100) -> list[ExperimentMaterial]:
        """Get materials pending description generation."""
        ...
```

---

## Integration with Existing Entities

### Experiment (existing)

Adicionar relationship para materials:

```python
# models/orm/experiment.py - adicionar
materials: Mapped[list["ExperimentMaterial"]] = relationship(
    "ExperimentMaterial",
    back_populates="experiment",
    order_by="ExperimentMaterial.display_order",
    cascade="all, delete-orphan",
)
```

### PR-FAQ Generator (existing)

Integrar referências de materiais:

```python
# services/research_prfaq/generator.py - modificar
def generate_prfaq(experiment_id: str) -> str:
    # ... existing code ...

    # Adicionar seção de materiais referenciados
    materials = material_repository.list_by_experiment(experiment_id)
    if materials:
        materials_section = format_materials_section(materials)
        prfaq_content += materials_section
```
