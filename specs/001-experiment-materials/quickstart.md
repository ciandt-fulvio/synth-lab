# Quickstart: Experiment Materials Upload

**Branch**: `001-experiment-materials`
**Date**: 2026-01-05

## Setup

### 1. Variáveis de Ambiente

Adicionar ao `.env`:

```bash
# Railway Storage Buckets (S3-compatible)
# Railway provides these automatically when you link a bucket:
ENDPOINT=https://storage.railway.app
BUCKET=attachments                # Production bucket name
# BUCKET=attachments-stg          # Staging bucket name
ACCESS_KEY_ID=<railway-access-key>
SECRET_ACCESS_KEY=<railway-secret-key>
REGION=auto

# Para processamento de vídeos/PDFs (opcional)
FFMPEG_PATH=/usr/bin/ffmpeg
```

### 2. Dependências Python

Adicionar ao `pyproject.toml`:

```toml
[project]
dependencies = [
    # ... existing deps ...
    "boto3>=1.34.0",
    "pdf2image>=1.17.0",
    "Pillow>=10.0.0",
    "moviepy>=1.0.3",  # Para extração de frames de vídeo
]
```

Instalar:
```bash
uv sync
```

### 3. Dependências Sistema (para thumbnails)

```bash
# macOS
brew install poppler  # Para pdf2image

# Ubuntu/Debian
apt-get install poppler-utils
```

### 4. Migração de Banco

```bash
# Criar migração
make alembic-revision MSG="add experiment_materials table"

# Aplicar migração
make alembic-upgrade
```

---

## Fluxo de Upload

### 1. Solicitar URL de Upload (Frontend → Backend)

```typescript
// frontend/src/services/materials-api.ts
export async function requestUploadUrl(
  experimentId: string,
  file: File,
  materialType: string
): Promise<UploadUrlResponse> {
  return fetchAPI(`/experiments/${experimentId}/materials/upload-url`, {
    method: 'POST',
    body: JSON.stringify({
      file_name: file.name,
      file_size: file.size,
      mime_type: file.type,
      material_type: materialType,
    }),
  });
}
```

### 2. Upload Direto para S3 (Frontend → S3)

```typescript
// Upload direto usando presigned URL
export async function uploadToS3(
  uploadUrl: string,
  file: File
): Promise<void> {
  const response = await fetch(uploadUrl, {
    method: 'PUT',
    body: file,
    headers: {
      'Content-Type': file.type,
    },
  });

  if (!response.ok) {
    throw new Error('Upload failed');
  }
}
```

### 3. Confirmar Upload (Frontend → Backend)

```typescript
export async function confirmUpload(
  experimentId: string,
  materialId: string,
  objectKey: string
): Promise<Material> {
  return fetchAPI(`/experiments/${experimentId}/materials/confirm`, {
    method: 'POST',
    body: JSON.stringify({
      material_id: materialId,
      object_key: objectKey,
    }),
  });
}
```

### 4. Fluxo Completo

```typescript
// hooks/use-upload-material.ts
export function useUploadMaterial() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      experimentId,
      file,
      materialType,
    }: UploadParams) => {
      // 1. Get presigned URL
      const { material_id, upload_url, object_key } =
        await requestUploadUrl(experimentId, file, materialType);

      // 2. Upload to S3
      await uploadToS3(upload_url, file);

      // 3. Confirm upload
      return confirmUpload(experimentId, material_id, object_key);
    },
    onSuccess: (_, { experimentId }) => {
      queryClient.invalidateQueries({
        queryKey: ['experiments', experimentId, 'materials'],
      });
    },
  });
}
```

---

## Backend Implementation

### 1. Storage Client

```python
# infrastructure/storage_client.py
import boto3
from synth_lab.infrastructure.config import (
    S3_ENDPOINT_URL,
    BUCKET_NAME,
)

def generate_upload_url(
    object_key: str,
    content_type: str,
    expires_in: int = 900
) -> str:
    """Generate presigned URL for upload."""
```

### 2. Material Service

```python
# services/material_service.py
class MaterialService:
    def __init__(
        self,
        repository: ExperimentMaterialRepository | None = None,
        storage: StorageClient | None = None,
    ):
        self.repository = repository or ExperimentMaterialRepository()
        self.storage = storage or get_storage_client()

    def request_upload_url(
        self,
        experiment_id: str,
        file_name: str,
        file_size: int,
        mime_type: str,
        material_type: str,
    ) -> dict:
        """Generate presigned URL for upload."""
        # Validations
        self._validate_limits(experiment_id, file_size)
        self._validate_file_type(mime_type)

        # Create material record
        material = ExperimentMaterial(
            experiment_id=experiment_id,
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type,
            material_type=material_type,
            file_type=self._get_file_type(mime_type),
            display_order=self._get_next_order(experiment_id),
        )
        self.repository.create(material)

        # Generate presigned URL
        object_key = f"experiments/{experiment_id}/materials/{material.id}{self._get_extension(file_name)}"
        upload_url = self.storage.generate_upload_url(object_key, mime_type)

        return {
            "material_id": material.id,
            "upload_url": upload_url,
            "object_key": object_key,
            "expires_in": 900,
        }
```

### 3. Description Generator

```python
# services/material_description_service.py
class MaterialDescriptionService:
    """Generates AI descriptions for materials."""

    def __init__(self, llm_client: LLMClient | None = None):
        self.llm = llm_client or get_llm_client()
        self.logger = logger.bind(component="material_description")

    async def generate_description(
        self,
        material_id: str,
        file_url: str,
        file_type: str,
    ) -> str:
        """Generate description for material using gpt-4o-mini."""
        with _tracer.start_as_current_span(
            "MaterialDescription: generate",
            attributes={"material_id": material_id, "file_type": file_type},
        ):
            prompt = (
                "Descreva o conteúdo desta imagem em até 30 palavras. "
                "Seja objetivo e focado no que é visualmente relevante."
            )

            # Handle different file types
            if file_type == "document":
                # Extract text or first page image
                content = await self._extract_document_content(file_url)
            elif file_type == "video":
                # Extract first frame
                content = await self._extract_video_frame(file_url)
            else:
                # Image - use directly
                content = file_url

            response = await self.llm.complete_vision(
                prompt=prompt,
                image_url=content,
                model="gpt-4o-mini",
                detail="low",
            )

            return response.strip()
```

---

## Tool para Entrevistas

### Tool Definition

```python
# services/research_agentic/tools.py (adicionar)
def create_material_viewer_tool(
    experiment_id: str,
    available_materials: list[dict],
) -> FunctionTool:
    """
    Create tool for viewing experiment materials during interviews.

    Args:
        experiment_id: Experiment ID
        available_materials: List of {id, name, description, type}
    """
    materials_list = ", ".join(
        f"{m['name']} ({m['type']})" for m in available_materials
    )

    @function_tool(
        name_override="ver_material",
        description_override=(
            "Mostra um material anexado ao experimento para visualização. "
            f"Materiais disponíveis: {materials_list}"
        )
    )
    def view_material(material_name: str) -> str:
        """
        View an experiment material.

        Args:
            material_name: Name of the material to view

        Returns:
            JSON with description and base64 image data
        """
        # Find material by name
        material = next(
            (m for m in available_materials if m['name'] == material_name),
            None
        )
        if not material:
            return json.dumps({"error": f"Material '{material_name}' não encontrado"})

        # Get material data
        image_data = get_material_base64(material['id'])

        return json.dumps({
            "name": material['name'],
            "type": material['type'],
            "description": material.get('description', 'Sem descrição'),
            "image": f"data:image/png;base64,{image_data}",
        })

    return view_material
```

### Integration with Runner

```python
# services/research_agentic/runner.py (modificar)
async def run_interview(
    synth_id: str,
    experiment_id: str,  # Novo parâmetro
    # ... outros params
):
    # Load experiment materials
    material_repo = ExperimentMaterialRepository()
    materials = material_repo.list_by_experiment(experiment_id)

    # Create material viewer tool
    material_tool = create_material_viewer_tool(
        experiment_id=experiment_id,
        available_materials=[
            {
                "id": m.id,
                "name": m.file_name,
                "description": m.description,
                "type": m.material_type,
            }
            for m in materials
        ],
    )

    # Pass tool to both agents
    interviewer = create_interviewer(
        # ... existing params
        tools=[material_tool],
    )

    interviewee = create_interviewee(
        synth=synth,
        # ... existing params
        tools=[material_tool],
    )
```

---

## Frontend Components

### Upload Component

```tsx
// components/experiments/MaterialUpload.tsx
import { useDropzone } from 'react-dropzone';

interface MaterialUploadProps {
  experimentId: string;
  onUploadComplete: (materials: Material[]) => void;
}

export function MaterialUpload({
  experimentId,
  onUploadComplete,
}: MaterialUploadProps) {
  const [stagedFiles, setStagedFiles] = useState<StagedFile[]>([]);
  const uploadMutation = useUploadMaterial();

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg', '.webp', '.gif'],
      'video/*': ['.mp4', '.mov', '.webm'],
      'application/pdf': ['.pdf'],
      'text/*': ['.txt', '.md'],
    },
    maxSize: 104857600, // 100MB
    maxFiles: 10,
    onDrop: (files) => {
      // Add to staged files with preview
      const staged = files.map((file) => ({
        file,
        preview: URL.createObjectURL(file),
        status: 'pending' as const,
      }));
      setStagedFiles((prev) => [...prev, ...staged]);
    },
  });

  const handleUploadAll = async () => {
    // Upload in parallel
    const results = await Promise.all(
      stagedFiles.map((staged) =>
        uploadMutation.mutateAsync({
          experimentId,
          file: staged.file,
          materialType: 'design', // TODO: let user select
        })
      )
    );
    onUploadComplete(results);
  };

  return (
    <div>
      <div
        {...getRootProps()}
        className={cn(
          "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer",
          isDragActive && "border-primary bg-primary/5"
        )}
      >
        <input {...getInputProps()} />
        <p>Arraste arquivos ou clique para selecionar</p>
      </div>

      {stagedFiles.length > 0 && (
        <div className="mt-4 grid grid-cols-4 gap-4">
          {stagedFiles.map((staged, idx) => (
            <MaterialPreview
              key={idx}
              file={staged.file}
              preview={staged.preview}
              status={staged.status}
            />
          ))}
        </div>
      )}

      <Button onClick={handleUploadAll} disabled={stagedFiles.length === 0}>
        Fazer upload de {stagedFiles.length} arquivo(s)
      </Button>
    </div>
  );
}
```

---

## Testes

### Backend Tests

```python
# tests/services/test_material_service.py


### Frontend Tests

```typescript
// frontend/src/__tests__/MaterialUpload.test.tsx
describe('MaterialUpload', () => {
  it('should show file previews after drop', async () => {
    render(<MaterialUpload experimentId="exp_123" />);

    const file = new File(['test'], 'test.png', { type: 'image/png' });
    const dropzone = screen.getByText(/Arraste arquivos/);

    fireEvent.drop(dropzone, { dataTransfer: { files: [file] } });

    expect(await screen.findByText('test.png')).toBeInTheDocument();
  });

  it('should reject files exceeding size limit', async () => {
    // ...
  });
});
```

---

## Checklist de Implementação

- [ ] Criar `infrastructure/storage_client.py`
- [ ] Criar `models/orm/material.py`
- [ ] Criar `domain/entities/experiment_material.py`
- [ ] Criar `repositories/experiment_material_repository.py`
- [ ] Criar `services/material_service.py`
- [ ] Criar `services/material_description_service.py`
- [ ] Criar `api/routers/materials.py`
- [ ] Criar `api/schemas/materials.py`
- [ ] Atualizar `api/main.py` para incluir router
- [ ] Criar migração Alembic
- [ ] Atualizar `services/research_agentic/tools.py` com `ver_material`
- [ ] Atualizar `services/research_agentic/runner.py`
- [ ] Criar `frontend/src/services/materials-api.ts`
- [ ] Criar `frontend/src/hooks/use-materials.ts`
- [ ] Criar `frontend/src/components/experiments/MaterialUpload.tsx`
- [ ] Criar `frontend/src/components/experiments/MaterialGallery.tsx`
- [ ] Atualizar `frontend/src/types/material.ts`
- [ ] Escrever testes unitários backend
- [ ] Escrever testes integração backend
- [ ] Escrever testes frontend
