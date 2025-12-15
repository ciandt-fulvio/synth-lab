# Quickstart: SynthLab CLI

**Branch**: `002-synthlab-cli` | **Date**: 2025-12-15

## Installation

```bash
# Clone repository
git clone <repo-url>
cd synth-lab

# Install with uv (recommended)
uv pip install -e .

# Or with pip
pip install -e .
```

## Verify Installation

```bash
# Check version
synthlab --version
# Output: synthlab 1.0.0

# Check help
synthlab --help
```

## Quick Usage

### Generate a Single Synth

```bash
synthlab gensynth
```

Output:
```
=== Gerando 1 Synth(s) ===
  [1/1] Maria Silva (abc123)

1 synth(s) gerado(s) com sucesso!
```

### Generate Multiple Synths

```bash
synthlab gensynth -n 10
```

### Generate Quietly (for scripts)

```bash
synthlab gensynth -n 100 -q
# Output: 100 synth(s) gerado(s).
```

### Validate Generated Synths

```bash
# Validate all
synthlab gensynth --validate-all

# Validate specific file
synthlab gensynth --validate-file data/synths/abc123.json
```

### Analyze Distribution

```bash
# Compare with IBGE data
synthlab gensynth --analyze all
```

## Output Location

Generated synths are saved to `data/synths/` by default:

```
data/synths/
├── abc123.json
├── def456.json
└── ghi789.json
```

Each file contains a complete synthetic persona in JSON format.

## Custom Output Directory

```bash
synthlab gensynth -n 5 -o ./my-output/
```

## Performance Benchmark

```bash
synthlab gensynth -n 100 --benchmark
```

Output:
```
=== Benchmark ===
Tempo total: 4.23s
Taxa: 23.6 synths/segundo
```

## Alternative: Python Module

```bash
python -m synth_lab gensynth -n 5
```

## Programmatic Usage

```python
from synth_lab.gen_synth import assemble_synth, load_config_data

config = load_config_data()
synth = assemble_synth(config)
print(synth["nome"])  # Maria Silva
```

## Next Steps

- Read the full CLI documentation: `synthlab gensynth --help`
- Check the JSON schema: `data/schemas/synth-schema.json`
- Review IBGE distributions: `data/config/ibge_distributions.json`
