# CLI Interface Contract: Topic Guides

**Feature**: `006-topic-guides`
**Date**: 2025-12-16
**Status**: Phase 1 Design

## Overview

This document defines the command-line interface for managing topic guides - collections of multi-modal contextual materials for synth interviews.

## Command Structure

All topic guide commands are accessed via the `topic-guide` subcommand group:

```bash
synthlab topic-guide <command> [options]
```

---

## Commands

### 1. Create Topic Guide

**Command**: `synthlab topic-guide create`

**Purpose**: Create a new topic guide directory with initialized summary.md file.

**Syntax**:
```bash
synthlab topic-guide create --name <topic-name>
```

**Parameters**:
- `--name` (required): Name of the topic guide to create
  - Type: string
  - Validation: Must be valid directory name (no special characters: `/\:*?"<>|`)
  - Example: `amazon-ecommerce`, `mobile-app-study`

**Behavior**:
1. Check if `data/topic_guides/<name>/` already exists
2. If exists, return error: "Topic guide '{name}' already exists"
3. If not exists:
   - Create directory `data/topic_guides/<name>/`
   - Create `summary.md` with initial content:
     ```markdown
     # contexto para o guide: <name>

     ## FILE DESCRIPTION
     ```
4. Log success message with path to created directory

**Exit Codes**:
- `0`: Success
- `1`: Topic guide already exists
- `2`: Invalid topic guide name
- `3`: File system error (permissions, disk full)

**Output Example**:
```
✓ Topic guide 'amazon-ecommerce' created successfully
  Path: /Users/user/synth-lab/data/topic_guides/amazon-ecommerce
  Add files to this directory and run 'synthlab topic-guide update --name amazon-ecommerce'
```

**Error Examples**:
```
✗ Error: Topic guide 'amazon-ecommerce' already exists
  Use 'synthlab topic-guide update --name amazon-ecommerce' to update it

✗ Error: Invalid topic guide name 'amazon/ecommerce'
  Name cannot contain special characters: / \ : * ? " < > |
```

---

### 2. Update Topic Guide

**Command**: `synthlab topic-guide update`

**Purpose**: Scan topic guide directory for new/modified files and generate AI descriptions.

**Syntax**:
```bash
synthlab topic-guide update --name <topic-name> [--force]
```

**Parameters**:
- `--name` (required): Name of the topic guide to update
  - Type: string
  - Validation: Topic guide must exist
- `--force` (optional): Re-process all files even if hashes match
  - Type: boolean flag
  - Default: false

**Behavior**:
1. Check if `data/topic_guides/<name>/` exists
2. If not exists, return error: "Topic guide '{name}' not found. Create it first with 'synthlab topic-guide create --name {name}'"
3. Load and parse `summary.md` (create `## FILE DESCRIPTION` section if missing)
4. Scan directory for all files (exclude `summary.md`)
5. For each file:
   - Check if supported type (PNG, JPEG, PDF, MD, TXT)
   - If unsupported: skip and log warning
   - Compute content hash (MD5)
   - If hash exists in summary.md and not `--force`: skip
   - If cannot read file: skip silently
   - If new/modified: send to LLM API for description
   - If LLM API fails: add placeholder entry and log warning
6. Update `summary.md` with new/updated descriptions
7. Display summary of operations

**Exit Codes**:
- `0`: Success (all files processed or skipped appropriately)
- `1`: Topic guide not found
- `2`: Network error (all LLM API calls failed)
- `3`: File system error

**Output Example**:
```
Updating topic guide 'amazon-ecommerce'...

Processing files:
  ✓ product-page.png - described successfully
  ✓ checkout-flow.pdf - described successfully
  ⊘ old-screenshot.png - unchanged (skipped)
  ⚠ logo.svg - unsupported file type (skipped)
  ⚠ corrupted.pdf - API failure (placeholder added)

Summary:
  - 2 files documented
  - 1 file unchanged
  - 1 file skipped (unsupported type)
  - 1 file failed (placeholder added)

Updated: /Users/user/synth-lab/data/topic_guides/amazon-ecommerce/summary.md
```

**Error Examples**:
```
✗ Error: Topic guide 'nonexistent' not found
  Create it first: synthlab topic-guide create --name nonexistent

⚠ Warning: Unsupported files skipped:
  - logo.svg
  - video.mp4
  Supported types: PNG, JPEG, PDF, MD, TXT
```

---

### 3. List Topic Guides

**Command**: `synthlab topic-guide list`

**Purpose**: List all topic guides in the data directory.

**Syntax**:
```bash
synthlab topic-guide list [--verbose]
```

**Parameters**:
- `--verbose` (optional): Show detailed information for each topic guide
  - Type: boolean flag
  - Default: false

**Behavior**:
1. Scan `data/topic_guides/` directory
2. For each subdirectory:
   - Verify `summary.md` exists
   - If `--verbose`: parse summary.md to count documented files
3. Display list sorted alphabetically

**Exit Codes**:
- `0`: Success (even if no topic guides exist)

**Output Example (default)**:
```
Topic Guides:
  - amazon-ecommerce
  - mobile-app-study
  - banking-ux-research

Total: 3 topic guides
```

**Output Example (--verbose)**:
```
Topic Guides:

amazon-ecommerce
  Path: data/topic_guides/amazon-ecommerce
  Files documented: 12
  Last updated: 2025-12-16 15:45

mobile-app-study
  Path: data/topic_guides/mobile-app-study
  Files documented: 7
  Last updated: 2025-12-15 10:30

banking-ux-research
  Path: data/topic_guides/banking-ux-research
  Files documented: 20
  Last updated: 2025-12-14 14:20

Total: 3 topic guides
```

**Empty State**:
```
No topic guides found.

Create your first topic guide:
  synthlab topic-guide create --name my-first-guide
```

---

### 4. Show Topic Guide

**Command**: `synthlab topic-guide show`

**Purpose**: Display detailed information about a specific topic guide.

**Syntax**:
```bash
synthlab topic-guide show --name <topic-name>
```

**Parameters**:
- `--name` (required): Name of the topic guide to display
  - Type: string
  - Validation: Topic guide must exist

**Behavior**:
1. Check if topic guide exists
2. Load and parse `summary.md`
3. List all context files with their status
4. Display file descriptions from summary.md

**Exit Codes**:
- `0`: Success
- `1`: Topic guide not found

**Output Example**:
```
Topic Guide: amazon-ecommerce
Path: data/topic_guides/amazon-ecommerce

Context Description:
  Este guia contém materiais sobre a experiência de compra na Amazon.

Files (5):
  ✓ product-page.png (documented)
  ✓ checkout-flow.pdf (documented)
  ✓ payment-screen.png (documented)
  ⊘ notes.md (not documented)
  ⚠ logo.svg (unsupported type)

File Descriptions:

product-page.png (hash: a3b5c7...):
  Screenshot da página de produto da Amazon mostrando detalhes do item,
  preço, avaliações de clientes e botão de adicionar ao carrinho.
  Interface desktop com navegação superior visível.

checkout-flow.pdf (hash: d4e6f8...):
  Documento descrevendo o fluxo de checkout da Amazon com diagramas de
  cada etapa do processo de finalização de compra.

payment-screen.png (hash: b1c3e5...):
  Tela de pagamento exibindo opções de cartão de crédito, endereço de
  cobrança e resumo do pedido com valor total.
```

---

## Global Options

All commands support standard global options:

- `--help`: Display help for the command
- `--version`: Display version information
- `--verbose`: Enable verbose logging
- `--quiet`: Suppress non-error output

---

## Environment Variables

**OPENAI_API_KEY** (required for `update` command):
- Description: OpenAI API key for generating file descriptions
- Validation: Must be valid API key format
- Error if missing: "OpenAI API key not found. Set OPENAI_API_KEY environment variable."

**TOPIC_GUIDES_DIR** (optional):
- Description: Override default topic guides directory
- Default: `data/topic_guides/`
- Example: `TOPIC_GUIDES_DIR=/custom/path synthlab topic-guide list`

---

## Integration with Existing Commands

### Research Interview Integration (Future - P3)

**Modified Command**: `synthlab research interview`

**New Parameter**:
```bash
synthlab research interview \
  --synth-id <id> \
  --topic <topic> \
  --topic-guide <guide-name>  # NEW
```

**Behavior**:
- If `--topic-guide` specified:
  - Load topic guide summary.md
  - Include file descriptions in interview context
  - Synth can reference materials in responses

---

## Output Format Standards

### Success Messages
- Prefix: `✓` (green checkmark)
- Format: `✓ <Action> '<resource>' <result>`
- Example: `✓ Topic guide 'amazon' created successfully`

### Warning Messages
- Prefix: `⚠` (yellow warning symbol)
- Format: `⚠ Warning: <message>`
- Example: `⚠ Warning: Unsupported files skipped: logo.svg`

### Error Messages
- Prefix: `✗` (red X)
- Format: `✗ Error: <message>`
- Example: `✗ Error: Topic guide 'test' not found`

### Progress Indicators
- For long operations (updating many files):
  ```
  Processing files: [2/5] checkout-flow.pdf...
  ```

### Color Coding
- Success: Green
- Warning: Yellow
- Error: Red
- Info: Blue
- Neutral: Default terminal color

---

## Testing Contract

### Unit Tests
- Argument parsing and validation
- Help text generation
- Error message formatting

### Integration Tests
- End-to-end command execution
- File system operations
- Output format validation

### Contract Tests
- Command structure stability (backward compatibility)
- Parameter names and types
- Exit code consistency
- Output format structure

---

## Backward Compatibility

**Version 1.0.0** (initial release):
- All commands and parameters defined above are part of the stable API
- Breaking changes require major version bump
- Deprecations must include migration guide

**Future Additions** (non-breaking):
- New optional parameters (with defaults)
- New commands in topic-guide group
- Additional output formats (e.g., `--format json`)

---

## Examples

### Complete Workflow

```bash
# 1. Create topic guide
synthlab topic-guide create --name amazon-study

# 2. Add files to directory
cp screenshots/*.png data/topic_guides/amazon-study/
cp documents/*.pdf data/topic_guides/amazon-study/

# 3. Generate descriptions
synthlab topic-guide update --name amazon-study

# 4. View results
synthlab topic-guide show --name amazon-study

# 5. Use in interview
synthlab research interview \
  --synth-id S001 \
  --topic "Amazon shopping experience" \
  --topic-guide amazon-study
```

### Error Handling

```bash
# Try to create duplicate
$ synthlab topic-guide create --name existing
✗ Error: Topic guide 'existing' already exists
  Use 'synthlab topic-guide update --name existing' to update it

# Try to update non-existent
$ synthlab topic-guide update --name nonexistent
✗ Error: Topic guide 'nonexistent' not found
  Create it first: synthlab topic-guide create --name nonexistent

# Invalid name
$ synthlab topic-guide create --name "invalid/name"
✗ Error: Invalid topic guide name 'invalid/name'
  Name cannot contain special characters: / \ : * ? " < > |
```

---

## Summary

This CLI interface provides:
- **Intuitive commands** following Unix conventions
- **Clear error messages** with actionable guidance
- **Robust validation** at every input point
- **Consistent output formatting** for programmatic parsing
- **Backward compatibility** guarantees for stable automation

All contracts follow the project's simplicity principle while maintaining professional CLI standards.
