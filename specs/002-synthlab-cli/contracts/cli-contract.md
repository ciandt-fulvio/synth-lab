# CLI Contract: SynthLab

**Branch**: `002-synthlab-cli` | **Date**: 2025-12-15

## Command Structure

```
synthlab [OPTIONS] COMMAND [ARGS]
```

## Global Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--help` | `-h` | flag | - | Show help message and exit |
| `--version` | `-V` | flag | - | Show version and exit |

## Commands

### gensynth

Generate synthetic Brazilian personas.

```
synthlab gensynth [OPTIONS]
```

#### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--quantidade` | `-n` | int | 1 | Number of synths to generate |
| `--output` | `-o` | path | data/synths/ | Output directory for generated synths |
| `--quiet` | `-q` | flag | false | Suppress verbose output |
| `--benchmark` | - | flag | false | Show performance statistics |
| `--validate-file` | - | path | - | Validate single synth file against schema |
| `--validate-all` | - | flag | false | Validate all synths in data/synths/ |
| `--validar` | - | flag | false | Run internal validation tests |
| `--analyze` | - | choice | - | Analyze distribution (region\|age\|all) |

---

## Usage Examples

### Generate Synths

```bash
# Generate 1 synth (default)
synthlab gensynth

# Generate 5 synths
synthlab gensynth -n 5

# Generate 100 synths quietly with benchmark
synthlab gensynth -n 100 -q --benchmark

# Generate to custom directory
synthlab gensynth -n 10 -o ./output/
```

### Validate Synths

```bash
# Validate single file
synthlab gensynth --validate-file data/synths/abc123.json

# Validate all synths
synthlab gensynth --validate-all

# Run internal validation tests
synthlab gensynth --validar
```

### Analyze Distribution

```bash
# Analyze regional distribution
synthlab gensynth --analyze region

# Analyze age distribution
synthlab gensynth --analyze age

# Analyze both
synthlab gensynth --analyze all
```

### Help

```bash
# Global help
synthlab --help

# Command help
synthlab gensynth --help

# Version
synthlab --version
```

---

## Output Formats

### Normal Mode (with progress)

```
=== Gerando 3 Synth(s) ===
  [1/3] Maria Silva (abc123)
  [2/3] João Santos (def456)
  [3/3] Ana Costa (ghi789)

3 synth(s) gerado(s) com sucesso!
```

### Quiet Mode

```
3 synth(s) gerado(s).
```

### With Benchmark

```
=== Gerando 100 Synth(s) ===
  [10/100] Gerados...
  [20/100] Gerados...
  ...
  [100/100] Gerados...

100 synth(s) gerado(s) com sucesso!

=== Benchmark ===
Tempo total: 4.23s
Taxa: 23.6 synths/segundo
```

### Validation Output

```
=== Validando todos os Synths em data/synths ===

✓ abc123.json
✓ def456.json
✗ ghi789.json
  - demografia -> idade: 150 is greater than maximum 120

============================================================
Total: 3 arquivo(s)
Válidos: 2
Inválidos: 1

1 arquivo(s) com erros de validação
```

### Analysis Output

```
=== Análise de Distribuição Demográfica ===

--- Distribuição Regional ---
Total de Synths: 100

Região          IBGE %     Real %     Count    Erro %
------------------------------------------------------------
Sudeste           42.13%    43.00%       43       0.87%
Nordeste          27.83%    26.00%       26       1.83%
Sul               14.75%    15.00%       15       0.25%
Norte              8.78%     9.00%        9       0.22%
Centro-Oeste       7.81%     7.00%        7       0.81%
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Validation error (invalid synths) |
| 2 | Command line error (invalid arguments) |

---

## Color Scheme

| Element | Color | ANSI Code |
|---------|-------|-----------|
| Success (✓) | Green | `\033[32m` |
| Error (✗) | Red | `\033[31m` |
| Warning | Yellow | `\033[33m` |
| Info | Blue | `\033[34m` |
| Headers | Bold | `\033[1m` |
| Reset | - | `\033[0m` |

**Note**: Colors are auto-detected. If terminal doesn't support colors, plain text is used.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SYNTHLAB_DATA_DIR` | `./data` | Base directory for data files |
| `NO_COLOR` | - | Disable colored output if set |
| `FORCE_COLOR` | - | Force colored output if set |
