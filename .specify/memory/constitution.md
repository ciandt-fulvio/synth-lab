<!--
Sync Impact Report
==================
Version: 1.0.0 → 2.0.0 (MAJOR - Paradigm shift to notebook-first development)
Ratification Date: 2025-12-12
Last Amended: 2025-12-14

Modified Principles:
- V. Simplicity and Code Quality - Updated function line limit from <30 to ≤25 lines
- V. Simplicity and Code Quality - Removed class-based architecture expectations
- V. Simplicity and Code Quality - Added notebook-specific guidance

Added Sections:
- I. Notebook-First Development (new core principle)
- II. Python Environment Management (new core principle)
- III. Simple Script Architecture (new core principle)
- Notebook Best Practices section
- Python Script Guidelines section

Removed Sections:
- Development Workflow > Commit and Branch Strategy > Pull Request Process (reduced formality)
- Quality Gates > Test Coverage Requirements (formal testing no longer mandatory)
- Quality Gates > Validation Requirements (simplified for notebook context)

Templates Requiring Updates:
✅ plan-template.md - Reviewed, compatible with notebook workflows
✅ tasks-template.md - Reviewed, test tasks now truly optional per documentation
✅ spec-template.md - Reviewed, user scenarios align with notebook demonstrations
⚠️  No README.md found - will need creation when project structure established

Follow-up TODOs:
- Create virtual environment at project root using Python 3.13
- Create .gitignore for venv/ and .ipynb_checkpoints/
- Document notebook execution conventions in project README when created
-->

# Synth Lab Constitution

## Core Principles

### I. Notebook-First Development

Development MUST prioritize Jupyter notebooks (.ipynb) as the primary deliverable and
working environment for experimentation, analysis, and documentation.

**Rules:**
- Jupyter notebooks (.ipynb) MUST be the default format for all exploratory work
- Notebooks MUST combine code, visualizations, and narrative documentation
- Each notebook MUST have a clear purpose stated in the first markdown cell
- Notebooks MUST be organized with clear section headers using markdown cells
- Cell execution order MUST be linear (top to bottom) for reproducibility
- Output cells MUST be preserved in version control to show results
- Notebooks MUST include markdown cells explaining the "why" behind code decisions

**Rationale:** Notebooks provide an interactive environment that combines code, output,
and documentation in a single artifact. This is ideal for data exploration, algorithm
development, and sharing reproducible analyses. The visual nature helps communicate
findings effectively.

**Enforcement:** Code reviews verify notebook structure and documentation quality.
Notebooks with unclear purpose or missing explanations require revision before merge.

### II. Python Environment Management

A virtual environment MUST be maintained at the project root using Python 3.13 to
ensure dependency isolation and reproducibility.

**Rules:**
- Virtual environment MUST be created at project root (venv/)
- Python 3.13 MUST be the target version
- All dependencies MUST be managed through requirements.txt or pyproject.toml
- Virtual environment MUST NOT be committed to version control
- .gitignore MUST exclude venv/, .ipynb_checkpoints/, and __pycache__/
- New dependencies MUST be documented when added

**Enforcement:** Project setup documentation must include venv creation steps.
Code reviews verify .gitignore coverage.

### III. Simple Script Architecture

When Python scripts (.py files) are created, they MUST follow a simple, functional
architecture WITHOUT object-oriented patterns, frameworks, or heavy dependencies.

**Rules:**
- Scripts MUST use functions as the primary organizational unit (NO classes)
- Each function MUST have a single, well-defined purpose
- Functions MUST be ≤25 lines of code
- Scripts MUST NOT use object-oriented design (no classes except for data containers)
- Scripts MUST NOT use Pydantic or similar validation frameworks
- Scripts MUST be organized as simple .py files, not packages
- All functions MUST have type hints using Python's typing module
- Scripts should have a `if __name__ == "__main__":` block for direct execution

**Enforcement:** Code reviews reject classes (except dataclasses for simple data),
functions exceeding 25 lines, and unnecessary framework dependencies.

### IV. Frequent Version Control Commits

Commits MUST be made frequently to capture incremental progress and maintain clear
development history.

**Rules:**
- Commit MUST be made when any notebook reaches a meaningful checkpoint
- Commit MUST be made when a Python script is created or modified
- Commit messages MUST clearly describe what was accomplished
- Commits MUST be atomic (single logical change per commit)
- Each commit should represent working/demonstrable code when possible

**Enforcement:** Task completion requires corresponding commit. Code reviews verify
appropriate commit granularity.

### V. Simplicity and Code Quality

Code MUST prioritize simplicity, readability, and maintainability over cleverness or
premature optimization.

**Rules:**
- Functions MUST be focused and single-purpose (≤25 lines)
- Notebooks SHOULD be focused on a single topic or analysis
- Complex logic MUST be justified and documented
- Dependencies MUST be minimized and well-researched
- Code MUST follow Python PEP 8 style guidelines
- NO classes except for simple dataclasses or when absolutely necessary
- NO heavy frameworks (FastAPI, Django, etc.) unless explicitly requested

**Enforcement:** Code reviews reject unnecessary complexity. Functions exceeding
25 lines trigger refactoring requirements.

### VI. Language

**Rules:**
- Code (variables, functions, classes) MUST be written in English
- Documentation and markdown cells MUST be written in Portuguese
- Comments in code SHOULD be in Portuguese for clarity
- User-facing strings MUST support i18n, initially provided in English and Portuguese

**Enforcement:** Code reviews verify language adherence in code and documentation.

## Notebook Best Practices

### Structure and Organization

**Notebook Structure:**
1. **Title cell**: Clear notebook title and purpose (markdown)
2. **Setup cell**: Imports and configuration
3. **Content cells**: Analysis organized in logical sections with markdown headers
4. **Conclusion cell**: Summary of findings (markdown)

**Cell Organization:**
- Use markdown cells to create narrative flow
- Keep code cells focused (one task per cell when possible)
- Use descriptive variable names that explain intent
- Clear old outputs before re-running when iteration changes approach

### Documentation Standards

**Every Notebook Must Include:**
- Purpose statement in first markdown cell
- Section headers explaining each analysis step
- Inline comments for complex operations
- Interpretation of outputs and visualizations
- Conclusions or next steps in final cell

**Markdown Cell Best Practices:**
- Use headers (##, ###) to organize sections
- Include context before code cells
- Explain why, not just what
- Document data sources and assumptions

### Reproducibility

**Execution Requirements:**
- Notebooks MUST run top-to-bottom without errors
- Dependencies MUST be imported in setup cells
- Random seeds MUST be set for reproducible results
- File paths MUST be relative or configurable
- Data sources MUST be documented

**Environment Documentation:**
- Document Python version (3.13) in notebook or README
- List required packages with versions
- Include sample data or data acquisition steps
- Note any external dependencies (APIs, databases)

## Python Script Guidelines

### When to Create Scripts

**Scripts should be created only when:**
- User explicitly requests a Python script
- Functionality needs to be reused across multiple notebooks
- Command-line execution is specifically needed
- Logic is stable and well-understood from notebook exploration

**Default to notebooks** for all exploratory and analytical work.

### Script Structure

**Simple Script Template:**

```python
"""
Brief description of script purpose.

Usage: python script_name.py
"""

from typing import List, Dict, Optional


def focused_function(param: str) -> Dict[str, any]:
    """
    Single-purpose function with clear intent.

    Args:
        param: Description of parameter

    Returns:
        Description of return value
    """
    # Implementation (≤25 lines)
    result = {"key": "value"}
    return result


def another_simple_function(data: List[str]) -> None:
    """Another focused function."""
    for item in data:
        print(item)


if __name__ == "__main__":
    # Example usage
    result = focused_function("example")
    print(result)
```

**Script Requirements:**
- All imports at top
- Type hints on all functions
- Docstrings in Portuguese explaining purpose
- Simple, linear logic flow
- Main block for direct execution demonstrations

### Prohibited Patterns

**Never Use:**
- Classes (except dataclasses for data containers)
- Inheritance or polymorphism
- Design patterns (Factory, Strategy, etc.)
- Pydantic models
- ORM frameworks
- Dependency injection
- Abstract base classes

**Keep It Simple:**
- Functions that do one thing
- Direct logic, not abstracted layers
- Minimal dependencies
- Straightforward error handling

## Development Workflow

### Commit and Branch Strategy

**Branch Naming:**
- Feature branches: `###-feature-name` (e.g., `001-audio-synthesis`)
- Branches created from main and merged via pull request

**Commit Process:**
1. Work in notebooks iteratively
2. Commit when reaching analysis checkpoints or milestones
3. Commit message format: "analysis: [description]" or "feat: [description]"
4. Push commits to feature branch regularly
5. Optional: Run any validation scripts if created

**Simple Merge Process:**
1. Ensure notebook runs top-to-bottom
2. Review outputs are meaningful
3. Create PR with summary of findings/changes
4. Merge when ready (no mandatory CI/CD gates)

### Documentation Requirements

**Every Feature Should Include:**
- Primary work in Jupyter notebook(s)
- README or markdown documentation if complexity warrants
- Requirements file or dependency list
- Sample data or data acquisition documentation if applicable

**Optional (only if requested):**
- Python scripts for reusable utilities
- Test files
- Formal specification documents

## Quality Gates

### Notebook Quality Requirements

**Before Commits:**
- Notebook runs top-to-bottom without errors
- Outputs are meaningful and demonstrate the work
- Markdown cells explain the analysis
- Code follows style guidelines (≤25 line functions)

**Before Merge:**
- Notebook has clear purpose and conclusions
- Dependencies are documented
- Any created scripts are simple and functional
- Documentation updated if needed

### Script Quality Requirements (if scripts created)

**Before Commits:**
- Functions are ≤25 lines
- Type hints present
- No classes (except dataclasses)
- Runs without errors

**Before Merge:**
- Clear docstrings in Portuguese
- Minimal dependencies
- Simple, focused logic
- Usage example in `if __name__ == "__main__":` block

## Governance

### Amendment Process

This constitution can be amended when necessary, but amendments require:
1. Clear documentation of the reason for amendment
2. Approval from project maintainers
3. Migration plan for existing code if amendment affects current practices
4. Version bump following semantic versioning rules:
   - **MAJOR**: Backward-incompatible governance changes, principle removals/redefinitions
   - **MINOR**: New principles added, materially expanded guidance
   - **PATCH**: Clarifications, wording improvements, non-semantic refinements

### Compliance and Reviews

**Constitution Compliance:**
- All PRs verify compliance with constitution principles
- Violations of non-negotiable principles require justification or rejection
- Complexity that violates simplicity principles MUST be justified

**Review Checkpoints:**
- Constitution reviewed during feature planning
- Notebook structure validated during code review
- Script simplicity verified (no classes, ≤25 lines functions)
- Constitution amendments tracked in this file's version history

### Runtime Development Guidance

For day-to-day development instructions and tooling setup, refer to:
- Project README.md for setup and running instructions (when created)
- Global CLAUDE.md for AI agent development standards
- Template files in `.specify/templates/` for feature development workflow
- This constitution for core principles and notebook/script standards

**Version**: 2.0.0 | **Ratified**: 2025-12-12 | **Last Amended**: 2025-12-14
