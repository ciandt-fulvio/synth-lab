# Quickstart: Synth Material Integration

**Feature**: 029-synth-material-integration
**Date**: 2026-01-06

## Overview

This guide shows how to integrate experiment materials (images, PDFs, videos) into Synth interviews, PR-FAQ generation, and exploration workflows.

---

## Prerequisites

- Experiment with materials already uploaded (via feature 001-experiment-materials)
- Materials stored in S3 with metadata in `experiment_materials` table
- Python 3.13+ environment with synth-lab dependencies installed

---

## Quick Example: Interview with Materials

```python
from synth_lab.services.materials_context import format_materials_for_prompt
from synth_lab.services.research_agentic.tools import create_materials_tool
from synth_lab.repositories.experiment_material_repository import ExperimentMaterialRepository
from agents import Agent

# 1. Fetch materials for experiment
material_repo = ExperimentMaterialRepository(session)
materials = material_repo.get_by_experiment(experiment_id="exp_abc123")

# 2. Format materials for system prompt
materials_section = format_materials_for_prompt(
    materials=materials,
    context="interview",
    include_tool_instructions=True
)

# 3. Create materials retrieval tool
materials_tool = create_materials_tool(
    experiment_id="exp_abc123",
    material_repository=material_repo,
    s3_client=s3_client
)

# 4. Build interviewer instructions with materials
interviewer_instructions = f"""
{base_interviewer_instructions}

{materials_section}
"""

# 5. Create agent with tool
interviewer = Agent(
    name="Interviewer",
    instructions=interviewer_instructions,
    tools=[materials_tool],  # LLM can call ver_material()
    model="gpt-4"
)

# 6. Run interview
# Synth can now reference and load materials during conversation
```

---

## Usage by Context

### 1. Interview System

**File**: `services/research_agentic/instructions.py`

```python
def format_interviewer_instructions(
    topic_guide: str,
    materials: list[ExperimentMaterial],  # NEW parameter
    **kwargs
) -> str:
    """Format interviewer system prompt with materials."""

    # Format materials section
    materials_section = format_materials_for_prompt(
        materials=materials,
        context="interview",
        include_tool_instructions=True
    ) if materials else ""

    # Inject into template
    return INTERVIEWER_INSTRUCTIONS.format(
        topic_guide=topic_guide,
        materials_section=materials_section,  # NEW
        **kwargs
    )
```

**Tool Registration** (`services/research_agentic/agent_definitions.py`):

```python
def create_interviewee(
    experiment_id: str,
    materials: list[ExperimentMaterial],  # NEW parameter
    **kwargs
) -> Agent:
    """Create interviewee agent with materials tool."""

    # Format instructions with materials
    instructions = format_interviewee_instructions(
        materials=materials,
        **kwargs
    )

    # Create tools
    tools = []
    if materials:
        materials_tool = create_materials_tool(
            experiment_id=experiment_id,
            material_repository=material_repo,
            s3_client=s3_client
        )
        tools.append(materials_tool)

    return Agent(
        name="Interviewee",
        instructions=instructions,
        tools=tools,
        model=model
    )
```

---

### 2. PR-FAQ Generation

**File**: `services/research_prfaq/prompts.py`

```python
def get_system_prompt(
    materials: list[ExperimentMaterial] | None = None  # NEW parameter
) -> str:
    """Get PR-FAQ generation system prompt with materials."""

    base_prompt = """
    Você é um especialista em criar documentos PR-FAQ...
    """

    # Add materials section if available
    if materials:
        materials_section = format_materials_for_prompt(
            materials=materials,
            context="prfaq",
            include_tool_instructions=False  # No tool in PR-FAQ
        )
        base_prompt += f"\n\n{materials_section}"

    return base_prompt
```

**Usage** (`services/research_prfaq/generator.py`):

```python
def generate_prfaq(
    experiment_id: str,
    interview_data: str,
    **kwargs
) -> str:
    """Generate PR-FAQ with material references."""

    # Fetch materials
    materials = material_repo.get_by_experiment(experiment_id)

    # Build prompt with materials
    system_prompt = get_system_prompt(materials=materials)

    # Generate PR-FAQ
    with _tracer.start_as_current_span("Generate PR-FAQ with Materials"):
        response = llm_client.complete(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": interview_data}
            ],
            model="gpt-4"
        )

    return response.choices[0].message.content
```

---

### 3. Exploration System

**File**: `services/exploration/action_proposal_service.py`

```python
def _build_prompt(
    self,
    experiment: Experiment,
    materials: list[ExperimentMaterial],  # NEW parameter
    **kwargs
) -> str:
    """Build action proposal prompt with materials."""

    base_prompt = f"""
    ## Contexto do Experimento
    **Nome**: {experiment.name}
    **Hipótese**: {experiment.hypothesis}
    """

    # Add materials context
    if materials:
        materials_section = format_materials_for_prompt(
            materials=materials,
            context="exploration",
            include_tool_instructions=False  # No tool in exploration
        )
        base_prompt += f"\n\n{materials_section}"

    return base_prompt
```

---

## Common Patterns

### Pattern 1: Fetch Materials for Experiment

```python
from synth_lab.repositories.experiment_material_repository import ExperimentMaterialRepository

# Initialize repository
material_repo = ExperimentMaterialRepository(db_session)

# Fetch all materials for experiment
materials = material_repo.get_by_experiment(experiment_id="exp_123")

# Materials are ordered by display_order
# Returns: List[ExperimentMaterial]
```

---

### Pattern 2: Format Materials for Different Contexts

```python
from synth_lab.services.materials_context import format_materials_for_prompt

# For interviews (with tool instructions)
interview_section = format_materials_for_prompt(
    materials=materials,
    context="interview",
    include_tool_instructions=True
)

# For PR-FAQ (with reference format)
prfaq_section = format_materials_for_prompt(
    materials=materials,
    context="prfaq",
    include_tool_instructions=False
)

# For exploration (metadata only)
exploration_section = format_materials_for_prompt(
    materials=materials,
    context="exploration",
    include_tool_instructions=False
)
```

---

### Pattern 3: Create and Register Materials Tool

```python
from synth_lab.services.research_agentic.tools import create_materials_tool

# Create tool instance
materials_tool = create_materials_tool(
    experiment_id="exp_123",
    material_repository=material_repo,
    s3_client=s3_client
)

# Register with agent
agent = Agent(
    name="Synth",
    instructions=instructions,
    tools=[materials_tool],  # LLM can now call ver_material()
    model="gpt-4"
)
```

---

### Pattern 4: Handle Empty Materials

```python
# Always check for empty materials
if materials:
    materials_section = format_materials_for_prompt(materials, context="interview")
    instructions = f"{base_instructions}\n\n{materials_section}"
else:
    # No materials - use base instructions only
    instructions = base_instructions

# format_materials_for_prompt returns empty string if materials is empty/None
# Safe to always call:
materials_section = format_materials_for_prompt(
    materials=materials or [],  # Handle None
    context="interview"
)
```

---

## Testing Materials Integration

### Unit Test: Materials Formatting

```python
def test_format_materials_for_interview():
    """Test materials formatting for interview context."""

    # Create test materials
    materials = [
        ExperimentMaterial(
            id="mat_abc123",
            material_type="design",
            file_name="wireframe.png",
            mime_type="image/png",
            file_size=2_300_000,
            description="Wireframe do checkout"
        )
    ]

    # Format for interview
    result = format_materials_for_prompt(
        materials=materials,
        context="interview",
        include_tool_instructions=True
    )

    # Assertions
    assert "## Materiais Anexados" in result
    assert "mat_abc123" in result
    assert "wireframe.png" in result
    assert "ver_material" in result  # Tool instructions included
```

---

### Integration Test: Materials Tool

```python
import pytest
from unittest.mock import Mock

def test_materials_tool_loads_image(s3_mock):
    """Test materials tool successfully loads image."""

    # Setup
    material = ExperimentMaterial(
        id="mat_test123",
        experiment_id="exp_123",
        file_url="s3://bucket/mat_test123.png",
        mime_type="image/png",
        file_size=1000
    )

    # Mock S3 download
    s3_mock.download.return_value = b"fake_image_data"

    # Create tool
    tool = create_materials_tool(
        experiment_id="exp_123",
        material_repository=mock_repo,
        s3_client=s3_mock
    )

    # Call tool
    result = tool.function(material_id="mat_test123")

    # Verify
    assert result.startswith("data:image/png;base64,")
    assert "ZmFrZV9pbWFnZV9kYXRh" in result  # base64 of "fake_image_data"
```

---

### End-to-End Test: Interview with Materials

```python
@pytest.mark.integration
def test_interview_with_materials(db_session, s3_client):
    """Test complete interview flow with materials."""

    # Setup experiment with materials
    experiment = create_test_experiment()
    materials = create_test_materials(experiment.id)

    # Create interviewer with materials
    interviewer = create_interviewer(
        experiment_id=experiment.id,
        materials=materials
    )

    # Create interviewee with materials
    interviewee = create_interviewee(
        experiment_id=experiment.id,
        materials=materials,
        synth_profile=test_profile
    )

    # Run interview
    conversation = run_interview(
        interviewer=interviewer,
        interviewee=interviewee,
        max_turns=5
    )

    # Verify materials were referenced
    responses = [turn["message"] for turn in conversation if turn["agent"] == "interviewee"]
    material_references = sum(1 for r in responses if "mat_" in r or "wireframe" in r)

    assert material_references > 0, "Synth should reference materials in responses"
```

---

## Validation Checklist

Before deploying materials integration:

- [ ] Materials fetch correctly from database
- [ ] Materials format correctly for each context (interview, prfaq, exploration)
- [ ] Materials tool registers with agents
- [ ] LLM can call `ver_material()` successfully
- [ ] Materials appear in interview responses
- [ ] PR-FAQs include material references
- [ ] Token budget validation passes (<2000 tokens)
- [ ] Error handling works (missing files, corrupted data)
- [ ] Phoenix tracing captures material operations

---

## Troubleshooting

### Issue: Materials not appearing in prompts

**Solution**: Check if materials list is empty
```python
materials = material_repo.get_by_experiment(experiment_id)
print(f"Found {len(materials)} materials")  # Should be > 0

# Verify format_materials_for_prompt returns non-empty
section = format_materials_for_prompt(materials, context="interview")
print(len(section))  # Should be > 0
```

---

### Issue: LLM not calling ver_material tool

**Possible causes**:
1. Tool not registered with agent
   ```python
   # Verify tools list
   print(agent.tools)  # Should include materials tool
   ```

2. System prompt doesn't mention tool
   ```python
   # Verify materials section in instructions
   print("ver_material" in agent.instructions)  # Should be True
   ```

3. Materials metadata not clear enough
   ```python
   # Check material descriptions
   for m in materials:
       print(f"{m.id}: {m.description}")
   # Descriptions should be meaningful
   ```

---

### Issue: Material download fails

**Solution**: Check S3 permissions and file existence
```python
# Test S3 access
try:
    content = s3_client.download_from_s3(material.file_url)
    print("S3 download successful")
except Exception as e:
    print(f"S3 error: {e}")
    # Check: AWS credentials, bucket permissions, file exists
```

---

### Issue: Token budget exceeded

**Solution**: Limit number of materials
```python
# Get token count
from synth_lab.services.materials_context import validate_token_budget

section = format_materials_for_prompt(materials, context="interview")
budget_check = validate_token_budget(section)

if not budget_check["is_valid"]:
    print(f"Exceeded by {budget_check['exceeded_by']} tokens")
    # Reduce materials or descriptions
    materials = materials[:15]  # Limit to 15 materials
```

---

## Performance Tips

1. **Cache materials during interview session**
   - Fetch once at session start
   - Reuse for all turns

2. **Async download for multiple materials**
   ```python
   import asyncio

   async def download_all_materials(materials):
       tasks = [download_material_async(m) for m in materials]
       return await asyncio.gather(*tasks)
   ```

3. **Preload small materials (<5 items)**
   - For PR-FAQ/exploration, preload all materials
   - Faster than on-demand tool calls

4. **Monitor Phoenix traces**
   - Check material loading times
   - Optimize slow S3 downloads

---

## Next Steps

After materials integration is working:

1. **Monitor usage**: Track material reference rates in Phoenix
2. **Gather feedback**: Do Synths reference materials effectively?
3. **Optimize**: Identify bottlenecks (S3 downloads, token usage)
4. **Extend**: Consider video keyframe extraction for large files

---

## References

- [Spec](./spec.md) - Feature requirements
- [Research](./research.md) - Technical decisions
- [Data Model](./data-model.md) - Data structures
- [Contracts](./contracts/) - API contracts
- [Plan](./plan.md) - Implementation plan
