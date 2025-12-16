# Data Model: Avatar Generation

**Feature**: Synth Avatar Generation
**Date**: 2025-12-16
**Purpose**: Define data structures, entities, and their relationships for avatar generation

## Core Entities

### 1. Avatar Image File

**Description**: Individual PNG file representing a synth's visual avatar

**File Structure**:
```
Location: data/synths/avatar/{synth_id}.png
Format: PNG (lossless)
Dimensions: 341x341 pixels
Naming: {synth_id}.png (e.g., "a1b2c3.png")
```

**Attributes**:
- `synth_id` (string, 6 characters): Unique identifier linking avatar to synth
- `file_path` (string): Full path to PNG file
- `dimensions` (tuple): Always (341, 341)
- `format` (string): Always "PNG"
- `file_size` (int): Bytes on disk (typically 50-150KB)

**Validation Rules**:
- File MUST exist at `data/synths/avatar/{synth_id}.png`
- File MUST be readable PNG format
- Dimensions SHOULD be 341x341 (tolerance: ±5 pixels)
- File size SHOULD be under 500KB

**Relationships**:
- One-to-one with Synth entity (linked by `synth_id`)
- Part of Avatar Block (9 avatars per block)

### 2. Avatar Block

**Description**: Logical grouping of 9 avatars generated in a single API call

**Structure**:
```python
{
    "block_id": "uuid",  # Unique identifier for this block
    "grid_image_url": "https://...",  # OpenAI response URL
    "synth_ids": [  # 9 synth IDs in grid order (left-to-right, top-to-bottom)
        "abc123",  # Row 1, Col 1
        "def456",  # Row 1, Col 2
        "ghi789",  # Row 1, Col 3
        "jkl012",  # Row 2, Col 1
        "mno345",  # Row 2, Col 2
        "pqr678",  # Row 2, Col 3
        "stu901",  # Row 3, Col 1
        "vwx234",  # Row 3, Col 2
        "yza567"   # Row 3, Col 3
    ],
    "prompt": "Full prompt text sent to OpenAI",
    "created_at": "2025-12-16T19:30:00Z",
    "model": "gpt-image-1-mini-2",
    "status": "completed" | "processing" | "failed"
}
```

**Validation Rules**:
- `synth_ids` MUST contain exactly 9 unique IDs
- `prompt` MUST be non-empty string
- `model` MUST be "gpt-image-1-mini-2" or "gpt-image-1-mini-3"
- `status` MUST be one of: "completed", "processing", "failed"

**Relationships**:
- Contains 9 Avatar Images
- Created from 9 Synth entities

**State Transitions**:
```
processing → completed (success)
processing → failed (API error, network error, etc.)
```

### 3. Image Prompt

**Description**: Structured text sent to OpenAI API for avatar generation

**Structure**:
```python
{
    "grid_instructions": str,  # How to structure the 3x3 grid
    "avatar_descriptions": list[dict],  # 9 descriptions, one per grid cell
    "visual_directives": list[str],  # Filters, backgrounds, styling
    "full_prompt": str  # Complete assembled prompt
}
```

**Avatar Description Fields** (extracted from Synth):
```python
{
    "position": int,  # 1-9 (grid position)
    "idade": int,  # Age from synth.demografia.idade
    "genero": str,  # Gender from synth.demografia.genero_biologico
    "etnia": str,  # Ethnicity from synth.demografia.raca_etnia
    "ocupacao": str,  # Occupation from synth.demografia.ocupacao
    "filter": str  # Randomly chosen: none, B&W, sepia, warm, cold, 3D
}
```

**Validation Rules**:
- `avatar_descriptions` MUST have exactly 9 entries
- Each description MUST have all required fields (position, idade, genero, etnia, ocupacao)
- `filter` MUST be one of: "none", "black_white", "sepia", "warm", "cold", "3d_style"
- `full_prompt` length SHOULD be under 4000 characters (gpt-image-1-mini limit)

**Excluded Fields** (NOT included in prompts):
- `interesses` (interests)
- `traços de personalidade` (Big Five traits)
- `cidade específica` (specific city - use only region)
- `renda_mensal` (income)
- `escolaridade` (education level)
- `estado_civil` (marital status)
- Any psychographic or behavioral data

### 4. Synth Entity (Existing - Referenced)

**Relevant Fields for Avatar Generation**:
```python
{
    "id": str,  # 6-character unique ID
    "demografia": {
        "idade": int,  # Age (18-80+)
        "genero_biologico": str,  # "masculino" | "feminino"
        "identidade_genero": str,  # "homem cis" | "mulher cis" | others
        "raca_etnia": str,  # "branco" | "pardo" | "preto" | "amarelo" | "indígena"
        "ocupacao": str,  # Professional occupation
        "localizacao": {
            "regiao": str  # Brazilian region (used for context, not specific city)
        }
    }
}
```

**Validation for Avatar Generation**:
- `id` MUST exist and be 6 characters
- `demografia.idade` MUST be integer >= 18
- `demografia.genero_biologico` MUST be non-empty
- `demografia.raca_etnia` MUST be non-empty
- `demografia.ocupacao` MUST be non-empty

## File System Structure

```
data/
└── synths/
    ├── avatar/                    # Avatar storage directory
    │   ├── {synth_id_1}.png      # 341x341 avatar image
    │   ├── {synth_id_2}.png
    │   ├── ...
    │   └── {synth_id_n}.png
    └── synths.json               # Existing synth data (not modified)
```

**Directory Requirements**:
- `data/synths/avatar/` MUST be created if it doesn't exist
- Directory MUST have write permissions
- PNG files MUST use synth ID as filename (no extensions in ID)

## Naming Conventions

### Files
- Avatar images: `{synth_id}.png` (lowercase, 6 chars + .png extension)
- Temporary grid images: `avatar_grid_{uuid}.png` (in temp directory)

### Variables (Python Code)
- `synth_id`: 6-character synth identifier
- `block_id`: UUID for avatar block
- `grid_image`: 1024x1024 source image
- `avatar_image`: Individual 341x341 cropped image
- `prompt`: Text sent to OpenAI
- `avatar_dir`: Path to `data/synths/avatar/`

### Functions (Python Code)
- `build_prompt()`: Construct OpenAI prompt from synth data
- `generate_block()`: Create one avatar block (9 avatars)
- `split_grid_image()`: Split 1024x1024 into 9 parts
- `save_avatar()`: Save individual avatar PNG
- `validate_synth_for_avatar()`: Check synth has required fields

## Data Flow

```
1. Input: List of Synth entities
   ↓
2. Validation: Check each synth has required fields
   ↓
3. Grouping: Organize synths into blocks of 9
   ↓
4. Prompt Construction: Build prompt for each block
   ↓
5. API Call: Send prompt to OpenAI, receive grid image URL
   ↓
6. Download: Fetch 1024x1024 image to temp file
   ↓
7. Splitting: Crop grid into 9 individual 341x341 images
   ↓
8. Saving: Write each avatar to data/synths/avatar/{synth_id}.png
   ↓
9. Cleanup: Delete temporary grid image
   ↓
10. Output: List of saved avatar file paths
```

## Error Handling Data

### Error Types
```python
class AvatarGenerationError(Exception):
    """Base exception for avatar generation errors."""
    pass

class InvalidSynthDataError(AvatarGenerationError):
    """Synth missing required fields for avatar generation."""
    def __init__(self, synth_id: str, missing_fields: list[str]):
        self.synth_id = synth_id
        self.missing_fields = missing_fields

class OpenAIAPIError(AvatarGenerationError):
    """Error calling OpenAI API."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message

class ImageSplitError(AvatarGenerationError):
    """Error splitting grid image into individual avatars."""
    def __init__(self, grid_path: str, reason: str):
        self.grid_path = grid_path
        self.reason = reason
```

### Error Response Format
```python
{
    "error_type": str,  # Class name (e.g., "InvalidSynthDataError")
    "synth_id": str | None,  # Affected synth ID if applicable
    "message": str,  # Human-readable error description
    "details": dict | None,  # Additional context
    "timestamp": str  # ISO 8601 timestamp
}
```

## Performance Considerations

### Memory Usage
- Grid image: ~3-5 MB in memory (1024x1024 PNG)
- Individual avatar: ~100-200 KB in memory (341x341 PNG)
- Peak memory per block: ~7 MB (1 grid + 9 avatars in memory simultaneously)
- Recommendation: Process blocks sequentially to keep memory under 10 MB

### Disk Space
- Per avatar: 50-150 KB on disk (PNG, optimized)
- Per block: 450-1350 KB total (9 avatars)
- For 100 synths: ~5-15 MB total disk space

### API Quota
- Cost per block: ~$0.020 (gpt-image-1-mini 2, 1024x1024)
- For 100 synths: ~$0.22 (12 blocks rounded up)
- Rate limit: ~50 requests/minute (varies by tier)
- Recommendation: Add 1-2 second delay between blocks

## Constraints and Limits

| Constraint | Limit | Reason |
|------------|-------|--------|
| Avatars per block | 9 (fixed) | 3x3 grid layout |
| Grid image size | 1024x1024 | OpenAI standard size |
| Avatar image size | 341x341 | 1024 ÷ 3 = 341.33 rounded |
| Prompt length | < 4000 chars | OpenAI API limit |
| Synth ID length | 6 characters | Existing synth system |
| File format | PNG only | Quality preservation |
| Min synth age | 18+ | Existing synth generation rule |
| Max batch size | 100 synths/command | Practical limit, can be increased |
