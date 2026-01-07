# Research: Synth Material Integration

**Date**: 2026-01-06
**Feature**: 029-synth-material-integration

## Research Questions

### 1. How to pass materials to LLM in multimodal format?

**Decision**: Use OpenAI's multimodal message format with base64-encoded content

**Rationale**:
- OpenAI API supports images, PDFs, and videos in message content via `image_url` type
- Format: `{"type": "image_url", "image_url": {"url": "data:image/png;base64,{data}"}}`
- Already implemented in existing codebase (`tools.py::create_image_loader_tool`)
- Supports all required MIME types (PNG, JPEG, GIF, WebP, PDF, MP4, WebM)
- No additional dependencies needed

**Alternatives Considered**:
- **URL-based**: Pass S3 URLs directly → Rejected: Requires public URLs, security risk
- **File paths**: Pass local file paths → Rejected: Doesn't work with API, only local models
- **Embeddings**: Convert to embeddings first → Rejected: Loses visual detail, unnecessary complexity

**Implementation**:
```python
# Existing pattern from tools.py
def load_material(material_id: str) -> str:
    """Load material from S3 and encode as base64."""
    # 1. Fetch from S3 using material_service
    # 2. Encode as base64
    # 3. Return data URI: f"data:{mime_type};base64,{encoded}"
```

---

### 2. How to format materials metadata in prompts?

**Decision**: Use markdown sections with structured lists (not XML tags)

**Rationale**:
- **Consistency**: All existing prompts use markdown headers (## Section) and bullet points
- **Readability**: More human-readable than XML, easier to debug
- **Token Efficiency**: Markdown is more concise than XML for lists
- **Proven Pattern**: Existing prompts successfully use markdown for structured data

**Alternatives Considered**:
- **XML tags** (`<attachments>...</attachments>`) → Rejected: Not consistent with codebase style, more verbose
- **JSON blocks** → Rejected: Less readable in system prompts, harder to scan
- **Plain text** → Rejected: Harder to parse, no structure

**Format**:
```markdown
## Materiais Anexados

Você tem acesso aos seguintes materiais do experimento. Use a função `ver_material(material_id)` para visualizar qualquer material.

- **mat_abc123** - [design] wireframe-checkout.png (image/png)
  Descrição: Wireframe do fluxo de checkout com 8 campos obrigatórios

- **mat_def456** - [prototype] demo-video.mp4 (video/mp4)
  Descrição: Vídeo demonstrando interação de agendamento (2min 30s)
```

---

### 3. How to implement materials retrieval tool for LLMs?

**Decision**: Use OpenAI Agents SDK `@function_tool` decorator pattern

**Rationale**:
- **Proven Pattern**: Already used in `tools.py::create_image_loader_tool()`
- **Auto-Generation**: SDK auto-generates JSON schema from function signature
- **Type Safety**: Python type hints → LLM tool schema
- **Integration**: Works seamlessly with existing Agent instances

**Alternatives Considered**:
- **Manual OpenAI function calling** → Rejected: More boilerplate, error-prone
- **Custom tool framework** → Rejected: Unnecessary complexity
- **MCP server** → Rejected: Overkill for simple S3 retrieval

**Implementation**:
```python
from agents import function_tool

@function_tool(
    name_override="ver_material",
    description_override="Visualiza um material anexado ao experimento. Use o material_id da lista de materiais disponíveis."
)
def view_material(material_id: str) -> str:
    """
    Load and return material content as base64 data URI.

    Args:
        material_id: ID do material (ex: mat_abc123)

    Returns:
        Data URI string: "data:image/png;base64,..."
    """
    # Implementation details in tool file
```

---

### 4. How to handle large video files within LLM constraints?

**Decision**: Multi-tier approach based on file size

**Rationale**:
- OpenAI API limits: ~50MB per request (total including all messages)
- Video files can exceed this limit
- Need graceful degradation strategy

**Strategy**:
1. **<10MB videos**: Send full video as base64 in message content
2. **10-50MB videos**: Extract keyframes (1 frame per 5 seconds) + metadata
3. **>50MB videos**: Metadata only + thumbnail + timestamp index

**Alternatives Considered**:
- **Always full video** → Rejected: API limits, slow processing
- **Always keyframes** → Rejected: Loses detail for small videos
- **External processing** → Rejected: Adds complexity, latency

**Implementation**:
```python
def prepare_video_for_llm(video_url: str, file_size: int) -> dict:
    """Prepare video based on size."""
    if file_size < 10_000_000:  # <10MB
        return {"type": "video", "url": encode_video_base64(video_url)}
    elif file_size < 50_000_000:  # <50MB
        return {"type": "keyframes", "frames": extract_keyframes(video_url)}
    else:  # >50MB
        return {"type": "metadata", "thumbnail": ..., "index": ...}
```

---

### 5. How to ensure Synth responses reference materials contextually?

**Decision**: Explicit instruction in system prompts + examples

**Rationale**:
- LLMs follow explicit instructions better than implicit expectations
- Few-shot examples demonstrate desired behavior
- Synth personality traits already influence tone via instructions

**Pattern**:
```markdown
## Como Referenciar Materiais

Quando discutir os materiais:
- Cite elementos específicos: "o botão verde no canto superior direito"
- Para vídeos, mencione timestamps: "aos 1:23 do vídeo, vi que..."
- Relacione com sua persona: [se baixa Tech Literacy] "achei confuso porque..."

Exemplo:
❌ "Gostei do design"
✅ "Achei o botão 'Finalizar Pedido' bem visível no wireframe, mas os 8 campos do formulário me intimidaram por serem muitos"
```

**Alternatives Considered**:
- **Automatic parsing** → Rejected: Unreliable, can't control quality
- **Post-processing** → Rejected: Can't fix vague responses after generation
- **No specific instructions** → Rejected: Tested in exploration, references were too generic

---

### 6. How to track material references in PR-FAQ generation?

**Decision**: LLM generates references inline using markdown link format

**Rationale**:
- Markdown links `[text](ref)` are human-readable and parseable
- Can be validated with regex: `\[.*?\]\((mat_\w+|.*?\.mp4@[\d:]+)\)`
- Frontend can render as clickable links

**Format**:
```markdown
## Insights da Pesquisa

### O que funcionou
- Calendário visual [ref: prototype-demo.mp4@00:12] teve boa recepção
- Botão "Finalizar" [ref: mat_abc123] ficou bem posicionado

### Pontos de Atenção
- Formulário extenso [ref: wireframe-checkout.png] causou fricção
```

**Alternatives Considered**:
- **Footnotes** → Rejected: Harder to parse, less visual connection
- **Separate references section** → Rejected: Disconnects insight from source
- **No structured format** → Rejected: Can't validate, hard to link in UI

---

### 7. Best practices for multimodal prompt design?

**Decision**: Combine best practices from OpenAI documentation and existing codebase

**Key Principles**:
1. **Materials before questions**: Present materials context early in system prompt
2. **Clear tool availability**: Explicitly state when `ver_material()` is available
3. **Metadata first**: List all materials upfront, load on-demand
4. **Token budget**: Reserve 2000 tokens max for materials metadata
5. **Graceful degradation**: Handle missing/corrupted materials without failing

**Pattern from OpenAI Best Practices**:
- System prompt: Context + tools + instructions
- User prompt: Specific question/task
- Materials: Metadata in system, content in tool responses

**Codebase Pattern**:
- Already follows this in `instructions.py` (system prompt) + dynamic user messages
- Tools registered at Agent creation: `Agent(tools=[view_material_tool])`

---

### 8. How to handle materials in different LLM contexts?

**Decision**: Context-specific formatting with shared core module

**Contexts**:

1. **Interview (Agents SDK)**:
   - Interviewer: Materials metadata in system prompt, tool available
   - Interviewee: Materials metadata + tool, persona-driven reactions

2. **PR-FAQ (Direct OpenAI API)**:
   - System prompt: Materials list + reference format instructions
   - Materials preloaded if <5 items, else tool-based

3. **Exploration (Direct OpenAI API)**:
   - Action proposal: Materials metadata, no tool (not interactive)
   - Summary: Preload all materials (typically <10 items)

**Shared Module** (`materials_context.py`):
```python
def format_materials_for_prompt(
    materials: list[ExperimentMaterial],
    context: Literal["interview", "prfaq", "exploration"],
    include_tool_instructions: bool = True
) -> str:
    """Generate materials section for any prompt context."""
```

---

## Technology Stack Confirmation

**No new dependencies required**:
- ✅ OpenAI SDK: Already installed
- ✅ OpenAI Agents SDK: Already used in `research_agentic/`
- ✅ boto3: Already used for S3
- ✅ SQLAlchemy: Already configured
- ✅ Phoenix tracing: Already integrated

**Existing Infrastructure to Reuse**:
- `ExperimentMaterialRepository`: Fetch materials by experiment_id
- `MaterialService.download_from_s3()`: Download file content
- `LLMClient`: Centralized LLM operations
- `get_tracer()`: Phoenix tracing for observability

---

## Performance Considerations

**Material Loading**:
- Use async/await for S3 downloads (avoid blocking)
- Cache materials in memory during interview session (avoid re-download)
- Timeout: 10s max for material retrieval tool

**Prompt Size**:
- Metadata: ~100 tokens per material
- Limit: 20 materials per experiment (2000 token budget)
- Validation: Warn if exceeded, truncate with message

**PR-FAQ Generation**:
- Baseline: ~30s without materials
- Target: <40s with materials (<30% increase per spec)
- Strategy: Parallel material loading, don't block on failures

---

## Security & Privacy

**Access Control**:
- Materials accessed via experiment_id → existing experiment permissions apply
- No new authorization logic needed
- Tool validates material belongs to current experiment

**Data Privacy**:
- Materials sent to OpenAI API (already true for text content)
- Same privacy implications as existing interview data
- No additional PII exposure (materials are design assets, not user data)

---

## Summary

All technical unknowns resolved. Implementation can proceed with:
- Markdown-based materials metadata in prompts
- OpenAI Agents SDK `@function_tool` for retrieval
- Shared `materials_context.py` module for formatting
- Context-specific integration in interview/PR-FAQ/exploration prompts
- No new dependencies or infrastructure changes required
