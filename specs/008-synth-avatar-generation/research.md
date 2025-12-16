# Research Findings: Avatar Generation

**Feature**: Synth Avatar Generation
**Date**: 2025-12-16
**Purpose**: Document technical decisions and best practices for implementing avatar generation

## 1. OpenAI Image Generation API

### Decision: Use gpt-image-1-mini 3 model (gpt-image-1-mini-3)

**Rationale**:
- The user specified "gpt-image-1-mini" but this model doesn't exist in OpenAI's current API
- Correct model options are: `gpt-image-1-mini-2` and `gpt-image-1-mini-3`
- gpt-image-1-mini 3 provides better quality and more accurate prompt following
- For cost-conscious implementations, `gpt-image-1-mini-2` is more economical

**Cost Comparison**:
- gpt-image-1-mini 3: ~$0.040 per 1024x1024 standard quality image
- gpt-image-1-mini 2: ~$0.020 per 1024x1024 image
- Recommendation: Use `gpt-image-1-mini-2` for this feature (better cost-to-value ratio)

**API Usage Pattern**:
```python
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

response = client.images.generate(
    model="gpt-image-1-mini-2",  # or "gpt-image-1-mini-3"
    prompt="[detailed prompt here]",
    n=1,  # Number of images (gpt-image-1-mini 3 only supports n=1)
    size="1024x1024",  # Options: 256x256, 512x512, 1024x1024
    quality="standard",  # "standard" or "hd" (gpt-image-1-mini 3 only)
    response_format="url"  # "url" or "b64_json"
)

image_url = response.data[0].url
```

**Error Handling Best Practices**:
```python
from openai import OpenAI, APIError, APIConnectionError, RateLimitError

try:
    response = client.images.generate(...)
except RateLimitError as e:
    # Handle rate limit (wait and retry)
    logger.error(f"Rate limit exceeded: {e}")
    raise
except APIConnectionError as e:
    # Handle connection errors
    logger.error(f"API connection failed: {e}")
    raise
except APIError as e:
    # Handle API errors
    logger.error(f"OpenAI API error: {e}")
    raise
```

**Rate Limiting**:
- gpt-image-1-mini has rate limits (varies by tier)
- Implement exponential backoff for retries
- Add delays between batch requests (e.g., 1-2 seconds)
- Monitor quota usage

**Prompt Best Practices for Grid Layouts**:
```python
prompt = """Create a single image divided into a precise 3x3 grid (3 rows, 3 columns) containing 9 distinct portrait photographs. Each portrait should be centered in its grid cell.

Grid Layout Instructions:
- Divide the image into exactly 9 equal squares
- Each square contains one portrait photograph
- Portraits should be head-and-shoulders shots
- Each portrait should be clearly separated from others

Portrait Descriptions:
1. [Position 1,1 - Top Left]: {description_1}
2. [Position 1,2 - Top Center]: {description_2}
3. [Position 1,3 - Top Right]: {description_3}
4. [Position 2,1 - Middle Left]: {description_4}
5. [Position 2,2 - Middle Center]: {description_5}
6. [Position 2,3 - Middle Right]: {description_6}
7. [Position 3,1 - Bottom Left]: {description_7}
8. [Position 3,2 - Bottom Center]: {description_8}
9. [Position 3,3 - Bottom Right]: {description_9}

Visual Requirements:
- Apply diverse visual filters randomly across portraits: no filter, black & white, sepia, warm tone, cool tone, or 3D movie character style
- Backgrounds should relate to the person's profession, preferably with bokeh/defocused effect
- Vary clothing colors, patterns, and accessories (glasses, earrings, hair accessories)
- Occasionally include profession-related items
- Ensure Brazilian demographics representation
"""
```

**Alternatives Considered**:
- Stability AI (Stable Diffusion): More complex setup, requires hosting
- Midjourney: No official API, Discord-based only
- Local models: Requires GPU infrastructure

**Why OpenAI chosen**: Official API, simple integration, reliable uptime, good prompt following

## 2. Image Processing with Pillow

### Decision: Use Pillow (PIL) for image splitting

**Rationale**:
- Standard Python library for image processing
- Simple, well-documented API
- Handles PNG format perfectly
- No additional dependencies needed (already available in most Python environments)

**Image Splitting Pattern**:
```python
from PIL import Image
from pathlib import Path

def split_grid_image(image_path: str, output_dir: str, synth_ids: list[str]) -> list[str]:
    """
    Split a 1024x1024 grid image into 9 individual avatar images.

    Args:
        image_path: Path to the source 1024x1024 image
        output_dir: Directory to save individual avatars
        synth_ids: List of 9 synth IDs (one per grid position)

    Returns:
        List of paths to saved avatar images
    """
    # Open the image
    img = Image.open(image_path)

    # Calculate cell size (1024 / 3 = 341.33, rounded to 341)
    cell_width = img.width // 3  # 341 pixels
    cell_height = img.height // 3  # 341 pixels

    saved_paths = []

    # Extract each of the 9 cells
    for row in range(3):
        for col in range(3):
            # Calculate crop box (left, upper, right, lower)
            left = col * cell_width
            upper = row * cell_height
            right = left + cell_width
            lower = upper + cell_height

            # Crop the cell
            cell = img.crop((left, upper, right, lower))

            # Get corresponding synth ID
            idx = row * 3 + col
            synth_id = synth_ids[idx]

            # Save as PNG
            output_path = Path(output_dir) / f"{synth_id}.png"
            cell.save(output_path, format='PNG', optimize=True)
            saved_paths.append(str(output_path))

    return saved_paths
```

**Quality Considerations**:
- PNG format preserves quality (lossless)
- Use `optimize=True` to reduce file size without quality loss
- Each 341x341 avatar is suitable for web/mobile display
- No resampling needed (direct crop from 1024x1024)

**Format Choice: PNG vs JPEG**:
- **PNG** (chosen): Lossless, supports transparency, better for portraits
- JPEG: Lossy compression, smaller file size, but quality degradation
- Decision: Use PNG for avatars (quality over size)

**Alternatives Considered**:
- OpenCV: Overkill for simple cropping, additional dependency
- Wand (ImageMagick): More complex, less Python-friendly
- NumPy slicing: Requires format conversion, less straightforward

**Why Pillow chosen**: Simple, standard, perfect for this use case

## 3. CLI Integration Patterns

### Decision: Extend existing argparse structure in gen_synth.py

**Rationale**:
- Consistent with existing gensynth command structure
- Users already familiar with gensynth parameters
- Minimal changes to existing CLI code

**Integration Pattern**:
```python
# In src/synth_lab/__main__.py (existing file)
gensynth_parser.add_argument(
    "--avatar",
    action="store_true",
    help="Gerar avatares para os synths (requer API OpenAI)"
)
gensynth_parser.add_argument(
    "-b", "--blocks",
    type=int,
    default=None,
    metavar="N",
    help="Número de blocos de avatares a gerar (1 bloco = 9 avatares)"
)

# In src/synth_lab/gen_synth/gen_synth.py (existing file)
def cli_main():
    parser = argparse.ArgumentParser(...)
    parser.add_argument("--avatar", action="store_true", ...)
    parser.add_argument("-b", "--blocks", type=int, default=None, ...)

    args = parser.parse_args()

    # Generate synths as usual
    synths = main(args.quantidade, ...)

    # Generate avatars if requested
    if args.avatar:
        from synth_lab.gen_synth.avatar_generator import generate_avatars
        generate_avatars(synths, blocks=args.blocks)
```

**Environment Variable Management**:
```python
import os
from pathlib import Path

# Load API key from environment
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY not found in environment. "
        "Set it with: export OPENAI_API_KEY='your-key-here'"
    )

# Alternative: Load from .env file (using python-dotenv)
from dotenv import load_dotenv
load_dotenv()  # Load from .env file in project root
```

**Progress Indication**:
```python
from rich.progress import Progress, SpinnerColumn, TextColumn

with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    console=console
) as progress:
    task = progress.add_task(
        f"Gerando avatares (bloco 1 de {total_blocks})...",
        total=None
    )

    # Make API call
    response = client.images.generate(...)

    progress.update(task, description="Processando imagem...")

    # Split and save
    split_grid_image(...)

    progress.update(task, completed=True)
```

**Alternatives Considered**:
- Separate `avatargen` command: Adds complexity, less discoverable
- Config file for API key: Environment variables are more standard
- Async/concurrent API calls: Unnecessary for typical batch sizes, adds complexity

**Why chosen approach**: Minimal changes, consistent UX, simple implementation

## 4. Additional Considerations

### Download Strategy for API Response

**Decision**: Download image from URL to temporary file, then process

```python
import requests
from pathlib import Path
import tempfile

def download_image(url: str, temp_dir: str = None) -> str:
    """Download image from OpenAI response URL to temporary file."""
    response = requests.get(url, stream=True)
    response.raise_for_status()

    # Create temp file
    temp_dir = temp_dir or tempfile.gettempdir()
    temp_path = Path(temp_dir) / f"avatar_grid_{uuid.uuid4()}.png"

    # Write image data
    with open(temp_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return str(temp_path)
```

**Rationale**:
- OpenAI returns URL by default (simpler than base64)
- Download once, process locally
- Clean up temp file after processing

### Validation Strategy

**Decision**: Validate synth data before making API calls

```python
def validate_synth_for_avatar(synth: dict) -> bool:
    """Check if synth has required fields for avatar generation."""
    required_fields = [
        "id",
        "demografia.idade",
        "demografia.genero_biologico",
        "demografia.raca_etnia",
        "demografia.ocupacao"
    ]

    for field in required_fields:
        if not get_nested_field(synth, field):
            return False

    return True
```

**Rationale**: Fail fast, clear error messages, avoid wasted API calls

## Summary of Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Image API | OpenAI gpt-image-1-mini 2 | Cost-effective, reliable, simple integration |
| Image Processing | Pillow (PIL) | Standard, simple, perfect for cropping |
| Image Format | PNG | Lossless quality for portraits |
| CLI Integration | Extend gensynth | Consistent UX, minimal changes |
| API Key Storage | Environment Variable | Standard practice, secure |
| Progress UI | Rich library | Already used in project |
| Download Method | URL to temp file | Simpler than base64 handling |

## Next Steps

1. Create data-model.md with avatar entities and structures
2. Create contracts/openai-image-api.md with API contract details
3. Create quickstart.md with usage examples
4. Generate tasks.md with test-first implementation plan
