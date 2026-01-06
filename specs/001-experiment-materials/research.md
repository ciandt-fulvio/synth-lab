# Research: Experiment Materials Upload

**Branch**: `001-experiment-materials`
**Date**: 2026-01-05

## 1. Storage Backend: Railway Buckets

### Decision
Utilizar Railway Buckets (S3-compatible) com boto3 para armazenamento de arquivos.

### Rationale
- Railway Buckets são buckets de object storage S3-compatíveis nativos do Railway
- Suportam virtual-hosted–style URLs (bucket como subdomínio)
- Presigned URLs podem durar até 90 dias
- Egress de buckets é grátis (diferente de egress de serviços)
- Possui presets para FastAPI que configuram variáveis de ambiente automaticamente
- Já existe infraestrutura Railway no projeto

### Alternatives Considered
1. **AWS S3 Direto**: Mais complexo para configurar, custos de egress
2. **MinIO Self-hosted**: Overhead de manutenção, volume persistente necessário
3. **Cloudflare R2**: Mais barato, mas adiciona complexidade de vendor

### Implementation Details
```python
# Variáveis de ambiente Railway (via preset FastAPI)
BUCKET_NAME=attachments          # Produção
BUCKET_NAME=attachments-stg      # Staging

# Conexão boto3

### Sources
- [Railway Storage Buckets Docs](https://docs.railway.com/guides/storage-buckets)

---

## 2. Upload Architecture: Presigned URLs

### Decision
Upload direto do frontend para S3 via presigned URLs geradas pelo backend.

### Rationale
- Não roteia arquivos pelo backend (reduz carga do servidor)
- Melhora escalabilidade (50 uploads concorrentes como requisito)
- Maior segurança (credenciais nunca expostas ao frontend)
- Adequado para arquivos grandes (até 100MB para vídeos)
- Egress de presigned URLs é grátis no Railway

### Alternatives Considered
1. **Upload via Backend**: Sobrecarrega servidor, latência maior
2. **Multipart Upload via Backend**: Complexidade desnecessária para tamanhos < 100MB
3. **Upload direto sem presigned**: Exposição de credenciais

### Flow
```
1. Frontend solicita presigned URL: POST /experiments/{id}/materials/upload-url
2. Backend gera URL com generate_presigned_url()
3. Backend retorna URL + object key
4. Frontend faz PUT diretamente para S3 com a URL
5. Frontend confirma upload: POST /experiments/{id}/materials/confirm
6. Backend valida arquivo existe e persiste metadata
```

---

## 3. Async Content Description with GPT-4o-mini

### Decision
Após confirmação de upload, disparar processo async para gerar descrição de até 30 palavras usando `gpt-4o-mini`.

### Rationale
- GPT-4o-mini suporta visão (aceita imagens) e é rápido/barato
- Descrição disponibilizada para agentes entrevistador/entrevistado via tool
- Processo async não bloqueia confirmação de upload (UX melhor)
- Descrição de 30 palavras suficiente para contexto LLM

### Model Selection
```python
# gpt-4o-mini - melhor custo-benefício para tarefas focadas com visão
model = "gpt-4o-mini"
# detail="low" para reduzir tokens de imagem
```

### Implementation Pattern
```python
async def generate_material_description(material_id: str, file_url: str) -> str:
    """Gera descrição de material usando GPT-4o-mini com visão."""
    prompt = (
        "Descreva o conteúdo desta imagem/documento em até 30 palavras. "
        "Seja objetivo e focado no que é visualmente relevante."
    )
    # Usar AsyncOpenAI para não bloquear
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": file_url, "detail": "low"}}
                ]
            }
        ],
        max_tokens=100
    )
    return response.choices[0].message.content
```

### Handling Different File Types
- **Imagens (PNG, JPG, WebP, GIF)**: Enviar diretamente como image_url
- **Vídeos (MP4, MOV, WebM)**: Extrair primeiro frame com ffmpeg/moviepy, enviar como imagem
- **PDFs**: Extrair primeira página como imagem com pdf2image, enviar como imagem
- **TXT/MD**: Ler conteúdo textual diretamente (não precisa visão)

### Sources
- [OpenAI Vision API Guide](https://platform.openai.com/docs/guides/images-vision)
- [GPT-4o mini Model](https://platform.openai.com/docs/models/gpt-4o-mini)

---

## 4. Tool para Visualização durante Entrevista

### Decision
Criar função tool `ver_material` disponível para agentes interviewer e interviewee, seguindo padrão existente de `ver_imagem`.

### Rationale
- Padrão já existe no projeto para imagens de topic guide (`tools.py`)
- Tool permite que LLM solicite visualização de material específico
- Retorno inclui descrição gerada + imagem base64 para visão
- Ambos os agentes podem solicitar para manter coerência de conversa

### Existing Pattern to Follow
```python
# services/research_agentic/tools.py - padrão existente
@function_tool(
    name_override="ver_imagem",
    description_override=f"Carrega uma imagem do guia de tópicos..."
)
def load_image(filename: str) -> str:
    ...
```

### New Tool Design
```python
@function_tool(
    name_override="ver_material",
    description_override=(
        "Mostra um material anexado ao experimento. "
        f"Materiais disponíveis: {materials_list}"
    )
)
def view_material(material_id: str) -> str:
    """
    Retorna material para visualização durante entrevista.

    Returns:
        JSON com {description, type, data_url}
    """
```

### Integration Points
- `agent_definitions.py`: Passar tool para `create_interviewer()` e `create_interviewee()`
- `runner.py`: Criar lista de materiais disponíveis do experimento
- Tool retorna descrição + base64 da imagem/thumbnail

---

## 5. Database Schema: ExperimentMaterial

### Decision
Criar nova tabela `experiment_materials` com FK para `experiments`.

### Rationale
- Separação clara de responsabilidades (materials vs documents)
- Tabela `experiment_documents` já existe para documentos gerados (PR-FAQ, summaries)
- Materials são arquivos do usuário, documents são gerados pelo sistema

### Schema Design
```sql
CREATE TABLE experiment_materials (
    id VARCHAR(50) PRIMARY KEY,
    experiment_id VARCHAR(50) NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    file_type VARCHAR(20) NOT NULL,  -- image, video, document
    file_url TEXT NOT NULL,          -- S3 URL
    file_name VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    material_type VARCHAR(20) NOT NULL,  -- design, prototype, competitor, spec, other
    description TEXT,                -- AI-generated description (30 words)
    description_status VARCHAR(20) DEFAULT 'pending',  -- pending, generating, completed, failed
    display_order INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Indexes
    INDEX idx_experiment_materials_experiment (experiment_id),
    INDEX idx_experiment_materials_type (material_type),
    INDEX idx_experiment_materials_order (experiment_id, display_order)
);
```

### Relationship
- Experiment 1:N ExperimentMaterial
- CASCADE delete quando experiment é removido

---

## 6. Frontend Upload Component

### Decision
Usar react-dropzone para drag-and-drop com preview imediato e upload em paralelo.

### Rationale
- Biblioteca madura e bem documentada
- Suporta drag-and-drop e file picker
- Permite limitar tipos e tamanhos de arquivo
- Compatível com upload direto para S3

### Component Design
```tsx
// components/experiments/MaterialUpload.tsx
interface MaterialUploadProps {
  experimentId: string;
  onUploadComplete: (materials: Material[]) => void;
  maxFiles?: number;  // default 10
}

// Fluxo:
// 1. Drop/Select files
// 2. Validação local (tipo, tamanho)
// 3. Preview imediato (staged files)
// 4. Request presigned URLs (batch)
// 5. Upload paralelo para S3
// 6. Confirmar uploads no backend
// 7. Polling para status da descrição
```

### Validation Rules (Client-side)
- Tipos aceitos: PNG, JPG, JPEG, WebP, GIF, MP4, MOV, WebM, PDF, TXT, MD
- Limite por arquivo: 25MB (imagens/docs), 100MB (vídeos)
- Máximo de arquivos: 10
- Tamanho total máximo: 250MB

---

## 7. Thumbnail Generation

### Decision
Thumbnails gerados no backend após upload confirmado.

### Rationale
- Reduz processamento no frontend
- Permite cache e CDN de thumbnails
- Consistência de formato e qualidade

### Implementation
- **Imagens**: Resize com Pillow para 200x200 max
- **Vídeos**: Extrair frame 0 com moviepy/opencv
- **PDFs**: Render primeira página com pdf2image

### Storage
- Thumbnails salvos no mesmo bucket com prefix: `thumbnails/`
- Formato: `thumbnails/{material_id}_thumb.jpg`

---

## 8. Error Handling and Resilience

### Decision
Implementar retries e fallbacks para operações assíncronas.

### Strategies
1. **Upload falhou**: Frontend pode retentar com mesma presigned URL (válida por 15min)
2. **Descrição falhou**: Status `failed`, pode ser reprocessada manualmente
3. **S3 indisponível durante entrevista**: Log erro, continuar sem material visual
4. **Thumbnail falhou**: Usar placeholder genérico por tipo

### Status Machine (Material)
```
pending → uploading → uploaded → processing → ready
                   ↘         ↗
                     failed
```

---

## Summary

| Decisão | Escolha | Alternativa Rejeitada |
|---------|---------|----------------------|
| Storage | Railway Buckets | AWS S3, MinIO |
| Upload | Presigned URLs | Backend passthrough |
| Descrição | gpt-4o-mini async | Síncrono, modelo maior |
| Tool | `ver_material` via function_tool | MCP, novo agente |
| DB | Nova tabela `experiment_materials` | Estender `experiment_documents` |
| Frontend | react-dropzone | Filepond, upload nativo |
| Thumbnails | Backend com Pillow/pdf2image | Frontend, sem thumbnail |
