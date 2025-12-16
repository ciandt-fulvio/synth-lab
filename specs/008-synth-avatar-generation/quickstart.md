# Quickstart: Avatar Generation

**Feature**: Synth Avatar Generation
**Date**: 2025-12-16
**Audience**: Users who want to generate visual avatars for their synthetic personas

## Prerequisites

1. **OpenAI API Key**: You need an active OpenAI API key with image generation access
2. **Python 3.13+**: Ensure you have the correct Python version
3. **Synth Lab Installed**: Follow main README for installation

## Setup

### 1. Configure API Key

Set your OpenAI API key as an environment variable:

```bash
# macOS/Linux
export OPENAI_API_KEY="sk-your-api-key-here"

# Or add to your shell profile (~/.zshrc or ~/.bashrc)
echo 'export OPENAI_API_KEY="sk-your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

**Security Note**: Never commit API keys to version control. Use environment variables or `.env` files (add `.env` to `.gitignore`).

### 2. Verify Installation

Check that avatar generation dependencies are installed:

```bash
# Install/update dependencies
uv sync

# Verify Pillow is available
python -c "from PIL import Image; print('Pillow OK')"

# Verify OpenAI SDK
python -c "import openai; print('OpenAI SDK OK')"
```

## Basic Usage

### Generate Synths with Avatars

The simplest way to create synths with avatars:

```bash
# Generate 9 synths with avatars (1 block)
synthlab gensynth -n 9 --avatar

# Generate 18 synths with avatars (2 blocks)
synthlab gensynth -n 18 --avatar
```

**What happens**:
1. System generates synth data (demographics, psychographics, etc.)
2. Groups synths into blocks of 9
3. Calls OpenAI API to generate 1024x1024 grid image for each block
4. Splits each grid into 9 individual 341x341 avatar images
5. Saves avatars to `data/synths/avatar/{synth-id}.png`

**Cost**: ~$0.02 per block (9 avatars) using gpt-image-1-mini 2

### Specify Number of Blocks

Control exactly how many blocks (and therefore avatars) to generate:

```bash
# Generate 3 blocks = 27 avatars
synthlab gensynth --avatar -b 3

# Generate 1 block = 9 avatars (default)
synthlab gensynth --avatar -b 1
```

**Note**: When both `-n` and `-b` are specified, synth count takes precedence and blocks are calculated automatically.

## Output

### File Structure

After generating avatars, your directory structure will look like:

```
data/synths/
├── avatar/
│   ├── a1b2c3.png    # 341x341 PNG avatar for synth a1b2c3
│   ├── d4e5f6.png    # 341x341 PNG avatar for synth d4e5f6
│   └── ...
└── synths.json       # Synth data (unchanged)
```

### Avatar Properties

- **Format**: PNG (lossless)
- **Size**: 341x341 pixels
- **File Size**: Typically 50-150 KB per avatar
- **Naming**: `{synth_id}.png` (e.g., `a1b2c3.png`)

### Viewing Avatars

Open avatars directly:

```bash
# macOS
open data/synths/avatar/a1b2c3.png

# Linux
xdg-open data/synths/avatar/a1b2c3.png
```

Or use any image viewer to browse the `data/synths/avatar/` directory.

## Common Workflows

### 1. Create Complete Synth Database with Avatars

Generate a batch of synths with all attributes and avatars:

```bash
# Create 50 synths with avatars (6 blocks total)
synthlab gensynth -n 50 --avatar

# Check results
ls data/synths/avatar/ | wc -l  # Should show 50
```

### 2. Generate More Avatars for Existing Synths

If you already have synths without avatars, generate new synths with avatars:

```bash
# Generate 9 new synths with avatars
synthlab gensynth -n 9 --avatar
```

**Note**: Future versions will support generating avatars for existing synth IDs.

### 3. Quiet Mode (Minimal Output)

Suppress verbose output during generation:

```bash
synthlab gensynth -n 18 --avatar -q
```

### 4. Benchmark Performance

See how long avatar generation takes:

```bash
synthlab gensynth -n 27 --avatar --benchmark
```

**Expected Output**:
```
=== Gerando 27 Synth(s) ===
  [1/27] João Silva (a1b2c3)
  ...
  [27/27] Maria Santos (xyz789)

27 synth(s) gerado(s) com sucesso!

Gerando avatares (bloco 1 de 3)...
Gerando avatares (bloco 2 de 3)...
Gerando avatares (bloco 3 de 3)...

27 avatares salvos em data/synths/avatar/

=== Benchmark ===
Tempo total: 75.32s
Taxa: 0.4 synths/segundo
```

## Examples

### Example 1: Quick Test (9 Synths)

```bash
# Generate 9 synths with avatars for testing
synthlab gensynth -n 9 --avatar

# View first avatar
open data/synths/avatar/$(ls data/synths/avatar/ | head -1)
```

### Example 2: Production Batch (100 Synths)

```bash
# Generate large batch for research
synthlab gensynth -n 100 --avatar

# Estimated cost: ~$0.22 (11 blocks * $0.02)
# Estimated time: ~3-5 minutes (depends on API speed)
```

### Example 3: Combine with Query

Generate synths, then query and view avatars:

```bash
# Generate synths with avatars
synthlab gensynth -n 27 --avatar

# Query for specific demographics
synthlab listsynth --where "demografia.idade > 50 AND demografia.genero_biologico = 'feminino'"

# Manually view avatar for a specific synth ID
open data/synths/avatar/abc123.png
```

## Troubleshooting

### "OPENAI_API_KEY not found"

**Cause**: Environment variable not set

**Solution**:
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

### "Rate limit exceeded"

**Cause**: Too many API requests in short time

**Solution**: Wait 1-2 minutes and try again, or reduce batch size:
```bash
# Generate fewer blocks at a time
synthlab gensynth -n 9 --avatar  # Start with 1 block
```

### "Connection error" or "Timeout"

**Cause**: Network issues or OpenAI service down

**Solution**:
1. Check internet connection
2. Retry after a few seconds
3. Check OpenAI status: https://status.openai.com

### Avatars Look Wrong

**Cause**: OpenAI may interpret prompts differently

**Solution**: This is expected variability in AI-generated images. Avatars are meant to be diverse and approximate representations. If specific avatar is problematic, regenerate that synth:
```bash
# Delete problematic avatar
rm data/synths/avatar/abc123.png

# Regenerate (future feature: regenerate specific IDs)
# For now: generate new synth
synthlab gensynth -n 1 --avatar
```

### Directory Permission Error

**Cause**: No write permissions for `data/synths/avatar/`

**Solution**:
```bash
# Create directory with correct permissions
mkdir -p data/synths/avatar
chmod 755 data/synths/avatar
```

## Cost Estimation

### gpt-image-1-mini 2 Pricing (Current)
- **Per Block (9 avatars)**: $0.020
- **Per Avatar**: ~$0.0022

### Estimated Costs by Batch Size

| Synths | Blocks | Estimated Cost |
|--------|--------|----------------|
| 9 | 1 | $0.02 |
| 18 | 2 | $0.04 |
| 27 | 3 | $0.06 |
| 50 | 6 | $0.12 |
| 100 | 12 | $0.24 |
| 500 | 56 | $1.12 |
| 1000 | 112 | $2.24 |

**Note**: Actual costs may vary. Check current OpenAI pricing: https://openai.com/pricing

## Performance Expectations

### Timing

- **API Call**: ~3-5 seconds per block (network-dependent)
- **Image Processing**: <1 second per block (local)
- **Total per Block**: ~5-10 seconds

**For 100 synths** (12 blocks):
- Fast case: ~60 seconds (1 minute)
- Typical case: ~120 seconds (2 minutes)
- Slow case: ~180 seconds (3 minutes with retries)

### Limits

- **Recommended batch size**: 1-100 synths per command
- **Maximum tested**: 100 synths (works well)
- **Beyond 100**: May require rate limit handling

## Next Steps

1. **Generate Research Dataset**: Create 50-100 synths with avatars for your research
2. **Integrate with Research Tool**: Use avatars in UX research interviews (see `synthlab research` command)
3. **Export for Prototypes**: Copy avatars to your design tool or application

## Related Commands

- `synthlab gensynth -h`: Full gensynth help
- `synthlab listsynth --help`: Query synth data
- `synthlab research --help`: Conduct UX interviews with synths

## Support

For issues or questions:
1. Check [GitHub Issues](https://github.com/your-repo/synth-lab/issues)
2. Review main [README.md](../../README.md)
3. Check OpenAI API status: https://status.openai.com
