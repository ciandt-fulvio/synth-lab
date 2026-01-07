"""
Materials context formatting for LLM prompts.

Provides shared utilities to format experiment materials as markdown sections
for different LLM contexts (interview, PR-FAQ, exploration).

References:
    - data-model.md: MaterialContext, MaterialReference definitions
    - contracts/materials_context.yaml: API contracts
    - research.md: Formatting decisions and patterns
"""

from typing import Literal
import re
from loguru import logger
from pydantic import BaseModel

try:
    import tiktoken
except ImportError:
    logger.warning("tiktoken not available - token budget validation will be approximate")
    tiktoken = None


# ============================================================================
# Data Models
# ============================================================================

class MaterialContext(BaseModel):
    """
    In-memory representation of material for LLM prompt formatting.

    This is a lightweight structure derived from ExperimentMaterial ORM
    for use in prompt building.
    """

    material_id: str  # mat_XXXXXX
    material_type: str  # design, prototype, competitor, spec, other
    file_name: str
    mime_type: str
    description: str | None
    file_size_mb: float  # Converted from bytes, rounded to 2 decimals

    @property
    def display_label(self) -> str:
        """
        Human-readable label for prompt.

        Returns:
            Formatted string like "[design] wireframe.png (image/png, 2.3 MB)"
        """
        return f"[{self.material_type}] {self.file_name} ({self.mime_type}, {self.file_size_mb} MB)"


class MaterialReference(BaseModel):
    """
    Citation of a material in generated content (PR-FAQs, summaries).

    Structured format for material references that appear in LLM outputs.
    """

    material_id: str  # mat_XXXXXX or filename
    reference_type: Literal["material_id", "filename_timestamp", "filename"]
    timestamp: str | None = None  # For videos: "00:12" or "1:23"
    context: str  # The insight or observation tied to this reference

    @classmethod
    def from_markdown_link(cls, link: str) -> "MaterialReference":
        """
        Parse material reference from markdown link.

        Formats supported:
        - [text](mat_abc123) → material_id type
        - [text](video.mp4@00:12) → filename_timestamp type
        - [text](image.png) → filename type

        Args:
            link: Markdown link string

        Returns:
            MaterialReference instance

        Raises:
            ValueError: If link format is invalid
        """
        pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        match = re.match(pattern, link)
        if not match:
            raise ValueError(f"Invalid reference format: {link}")

        context_text, ref = match.groups()

        # Video with timestamp: filename@HH:MM or filename@MM:SS
        if '@' in ref:
            filename, timestamp = ref.split('@', 1)
            return cls(
                material_id=filename,
                reference_type="filename_timestamp",
                timestamp=timestamp,
                context=context_text
            )
        # Material ID: mat_XXXXXX
        elif ref.startswith('mat_'):
            return cls(
                material_id=ref,
                reference_type="material_id",
                context=context_text
            )
        # Filename only
        else:
            return cls(
                material_id=ref,
                reference_type="filename",
                context=context_text
            )


# ============================================================================
# Transformation Functions
# ============================================================================

def to_material_context(material) -> MaterialContext:
    """
    Convert ORM ExperimentMaterial to MaterialContext.

    Args:
        material: SQLAlchemy ExperimentMaterial ORM instance

    Returns:
        MaterialContext instance
    """
    return MaterialContext(
        material_id=material.id,
        material_type=material.material_type,
        file_name=material.file_name,
        mime_type=material.mime_type,
        description=material.description,
        file_size_mb=round(material.file_size / 1_000_000, 2)
    )


# ============================================================================
# Formatting Functions
# ============================================================================

def format_materials_for_prompt(
    materials: list | None,
    context: Literal["interview", "prfaq", "exploration"],
    include_tool_instructions: bool = True
) -> str:
    """
    Format experiment materials as markdown section for LLM system prompts.

    Generates consistent materials context across interview, PR-FAQ, and
    exploration flows.

    Args:
        materials: List of ExperimentMaterial ORM instances (or None)
        context: Context type determines formatting style
            - interview: Includes tool usage instructions
            - prfaq: Includes reference format guidelines
            - exploration: Metadata only (no tool)
        include_tool_instructions: Whether to include ver_material() tool usage

    Returns:
        Markdown-formatted materials section (empty string if no materials)

    Raises:
        ValueError: If context not in allowed values
    """
    # Handle None or empty materials
    if not materials:
        return ""

    # Validate context
    if context not in ["interview", "prfaq", "exploration"]:
        raise ValueError(
            f"Invalid context: {context}. Must be 'interview', 'prfaq', or 'exploration'"
        )

    # Truncate if > 20 materials (token budget)
    if len(materials) > 20:
        logger.warning(
            f"Experiment has {len(materials)} materials, truncating to 20 for token budget"
        )
        materials = materials[:20]
        truncation_note = "\n\n⚠️ Nota: Apenas os primeiros 20 materiais são mostrados."
    else:
        truncation_note = ""

    # Transform to context objects
    contexts = [to_material_context(m) for m in materials]

    # Build markdown section based on context
    if context == "interview":
        return _format_for_interview(contexts, include_tool_instructions) + truncation_note
    elif context == "prfaq":
        return _format_for_prfaq(contexts) + truncation_note
    elif context == "exploration":
        return _format_for_exploration(contexts) + truncation_note


def _format_for_interview(
    contexts: list[MaterialContext],
    include_tool: bool
) -> str:
    """Format materials for interview context."""
    lines = ["## Materiais Anexados", ""]

    if include_tool:
        lines.append(
            "Você tem acesso aos seguintes materiais do experimento. "
            "Use a função `ver_material(material_id)` para visualizar qualquer "
            "material quando precisar analisá-lo em detalhes."
        )
    else:
        lines.append("Você tem acesso aos seguintes materiais do experimento:")

    lines.append("")

    # List materials
    for ctx in contexts:
        lines.append(f"- **{ctx.material_id}** - {ctx.display_label}")
        if ctx.description:
            lines.append(f"  Descrição: {ctx.description}")
        lines.append("")

    # Add tool usage instructions if requested
    if include_tool:
        lines.extend([
            "### Como Referenciar Materiais",
            "",
            "Quando discutir os materiais:",
            "- Cite elementos específicos: \"o botão verde no canto superior\"",
            "- Para vídeos, mencione timestamps: \"aos 1:23 do vídeo...\"",
            "- Relacione com sua persona: explique como os elementos afetam sua experiência",
            "",
            "Exemplo:",
            "❌ \"Gostei do design\"",
            "✅ \"Achei o botão 'Finalizar Pedido' bem visível no wireframe, mas "
            "os 8 campos do formulário me intimidaram por serem muitos\"",
            ""
        ])

    return "\n".join(lines)


def _format_for_prfaq(contexts: list[MaterialContext]) -> str:
    """Format materials for PR-FAQ context."""
    lines = ["## Materiais de Referência", ""]
    lines.append("Os seguintes materiais foram usados durante a pesquisa:")
    lines.append("")

    # List materials
    for ctx in contexts:
        lines.append(f"- **{ctx.material_id}** - {ctx.display_label}")
        if ctx.description:
            lines.append(f"  Descrição: {ctx.description}")
        lines.append("")

    # Add reference format guidelines
    lines.extend([
        "### Formato de Referências",
        "",
        "Ao citar materiais nos insights:",
        "- Use: [observação](mat_XXXXXX) para imagens/documentos",
        "- Use: [observação](filename.mp4@MM:SS) para vídeos com timestamp",
        "",
        "Exemplo: \"Calendário visual [ref: demo-video.mp4@01:23] teve boa recepção\"",
        ""
    ])

    return "\n".join(lines)


def _format_for_exploration(contexts: list[MaterialContext]) -> str:
    """Format materials for exploration context (metadata only)."""
    lines = ["## Materiais do Experimento", ""]
    lines.append("Os seguintes materiais estão anexados ao experimento:")
    lines.append("")

    # List materials (metadata only, no tool)
    for ctx in contexts:
        lines.append(f"- **{ctx.material_id}** - {ctx.display_label}")
        if ctx.description:
            lines.append(f"  Descrição: {ctx.description}")
        lines.append("")

    return "\n".join(lines)


# ============================================================================
# Validation Functions
# ============================================================================

def validate_token_budget(formatted_section: str) -> dict:
    """
    Check if materials section exceeds token budget.

    Args:
        formatted_section: Output from format_materials_for_prompt()

    Returns:
        Dictionary with:
            - is_valid: bool (True if within budget)
            - estimated_tokens: int
            - budget: int (always 2000)
            - exceeded_by: int | None (tokens over budget, or None if valid)
    """
    budget = 2000

    # Use tiktoken for accurate counting if available
    if tiktoken:
        try:
            encoding = tiktoken.encoding_for_model("gpt-4")
            estimated_tokens = len(encoding.encode(formatted_section))
        except Exception as e:
            logger.warning(f"tiktoken encoding failed: {e}, using approximation")
            # Fallback: approximate as 4 chars per token
            estimated_tokens = len(formatted_section) // 4
    else:
        # Approximate: 4 characters per token
        estimated_tokens = len(formatted_section) // 4

    is_valid = estimated_tokens <= budget
    exceeded_by = estimated_tokens - budget if not is_valid else None

    return {
        "is_valid": is_valid,
        "estimated_tokens": estimated_tokens,
        "budget": budget,
        "exceeded_by": exceeded_by
    }


# ============================================================================
# Validation
# ============================================================================

if __name__ == "__main__":
    import sys

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Test 1: MaterialContext model instantiation
    total_tests += 1
    try:
        ctx = MaterialContext(
            material_id="mat_test123",
            material_type="design",
            file_name="test.png",
            mime_type="image/png",
            description="Test material",
            file_size_mb=1.23
        )
        assert ctx.material_id == "mat_test123"
        assert ctx.display_label == "[design] test.png (image/png, 1.23 MB)"
    except Exception as e:
        all_validation_failures.append(f"MaterialContext instantiation failed: {e}")

    # Test 2: MaterialReference from_markdown_link
    total_tests += 1
    try:
        ref = MaterialReference.from_markdown_link("[text](mat_abc123)")
        assert ref.material_id == "mat_abc123"
        assert ref.reference_type == "material_id"
    except Exception as e:
        all_validation_failures.append(f"MaterialReference parsing failed: {e}")

    # Test 3: format_materials_for_prompt with empty list
    total_tests += 1
    try:
        result = format_materials_for_prompt([], context="interview")
        assert result == "", f"Expected empty string, got: {result}"
    except Exception as e:
        all_validation_failures.append(f"Empty materials formatting failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(
            f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Module is validated and ready for use")
        sys.exit(0)
