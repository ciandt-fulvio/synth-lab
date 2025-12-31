"""
ActionCatalog service for LLM-assisted scenario exploration.

Provides access to the action catalog, which contains categories of improvement
actions with examples and typical impacts. Used to anchor LLM proposals.

References:
    - Spec: specs/024-llm-scenario-exploration/spec.md
    - Data model: specs/024-llm-scenario-exploration/data-model.md
"""

import json
from pathlib import Path

from loguru import logger
from pydantic import BaseModel, Field

# Default catalog path
DEFAULT_CATALOG_PATH = Path(__file__).parent.parent.parent.parent.parent / "data" / "action_catalog.json"


class ImpactRange(BaseModel):
    """Range for a typical impact value."""

    min: float = Field(description="Minimum typical impact.")
    max: float = Field(description="Maximum typical impact.")


class ActionExample(BaseModel):
    """An example action with typical impacts."""

    action: str = Field(description="Description of the action.")
    typical_impacts: dict[str, ImpactRange] = Field(
        description="Typical impact ranges by parameter."
    )


class ActionCategory(BaseModel):
    """A category of improvement actions."""

    id: str = Field(description="Category identifier.")
    name: str = Field(description="Display name of the category.")
    description: str = Field(description="Description of the category.")
    examples: list[ActionExample] = Field(
        default_factory=list,
        description="Example actions in this category.",
    )


class ActionCatalogData(BaseModel):
    """Complete action catalog data."""

    version: str = Field(description="Catalog version.")
    categories: list[ActionCategory] = Field(
        description="List of action categories."
    )


class ActionCatalogService:
    """
    Service for accessing the action catalog.

    The catalog is loaded from a JSON file and cached in memory.
    Provides methods for validation and prompt context generation.
    """

    def __init__(self, catalog_path: Path | None = None):
        """
        Initialize the action catalog service.

        Args:
            catalog_path: Path to the catalog JSON file. Defaults to data/action_catalog.json.
        """
        self.catalog_path = catalog_path or DEFAULT_CATALOG_PATH
        self._catalog: ActionCatalogData | None = None
        self._category_ids: set[str] = set()
        self.logger = logger.bind(component="action_catalog")

    def _load_catalog(self) -> None:
        """Load the catalog from JSON file."""
        if self._catalog is not None:
            return

        if not self.catalog_path.exists():
            self.logger.warning(f"Catalog file not found: {self.catalog_path}")
            # Create empty catalog
            self._catalog = ActionCatalogData(version="0.0.0", categories=[])
            self._category_ids = set()
            return

        with open(self.catalog_path, encoding="utf-8") as f:
            data = json.load(f)

        self._catalog = ActionCatalogData(**data)
        self._category_ids = {cat.id for cat in self._catalog.categories}
        self.logger.info(
            f"Loaded action catalog v{self._catalog.version} with {len(self._catalog.categories)} categories"
        )

    def get_catalog(self) -> ActionCatalogData:
        """
        Get the complete action catalog.

        Returns:
            ActionCatalogData with all categories and examples.
        """
        self._load_catalog()
        return self._catalog

    def get_categories(self) -> list[ActionCategory]:
        """
        Get all action categories.

        Returns:
            List of ActionCategory objects.
        """
        self._load_catalog()
        return self._catalog.categories

    def get_category_by_id(self, category_id: str) -> ActionCategory | None:
        """
        Get a specific category by ID.

        Args:
            category_id: The category ID to look up.

        Returns:
            ActionCategory if found, None otherwise.
        """
        self._load_catalog()
        for cat in self._catalog.categories:
            if cat.id == category_id:
                return cat
        return None

    def validate_category(self, category_id: str) -> bool:
        """
        Check if a category ID is valid.

        Args:
            category_id: The category ID to validate.

        Returns:
            True if valid, False otherwise.
        """
        self._load_catalog()
        return category_id in self._category_ids

    def get_valid_category_ids(self) -> set[str]:
        """
        Get all valid category IDs.

        Returns:
            Set of valid category IDs.
        """
        self._load_catalog()
        return self._category_ids.copy()

    def get_prompt_context(self) -> str:
        """
        Generate a context string for LLM prompts.

        Returns:
            Formatted string describing all categories and examples.
        """
        self._load_catalog()

        lines = ["## Catalogo de Acoes Disponiveis", ""]

        for cat in self._catalog.categories:
            lines.append(f"### {cat.name} ({cat.id})")
            lines.append(cat.description)
            lines.append("")

            if cat.examples:
                lines.append("Exemplos:")
                for example in cat.examples[:3]:  # Limit to 3 examples per category
                    impacts_str = ", ".join(
                        f"{k}: [{v.min:.2f}, {v.max:.2f}]"
                        for k, v in example.typical_impacts.items()
                    )
                    lines.append(f"  - {example.action}")
                    lines.append(f"    Impactos tipicos: {impacts_str}")
                lines.append("")

        return "\n".join(lines)

    def get_catalog_json(self) -> str:
        """
        Get the catalog as a JSON string for API responses.

        Returns:
            JSON string representation of the catalog.
        """
        self._load_catalog()
        return self._catalog.model_dump_json(indent=2)


# Global singleton instance
_catalog_service: ActionCatalogService | None = None


def get_action_catalog_service(catalog_path: Path | None = None) -> ActionCatalogService:
    """
    Get or create the global action catalog service.

    Args:
        catalog_path: Optional path override. Only used on first call.

    Returns:
        ActionCatalogService: Global catalog service instance.
    """
    global _catalog_service
    if _catalog_service is None:
        _catalog_service = ActionCatalogService(catalog_path)
    return _catalog_service


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Load catalog
    total_tests += 1
    try:
        service = ActionCatalogService()
        catalog = service.get_catalog()
        if catalog.version != "1.0.0":
            all_validation_failures.append(f"Expected version 1.0.0, got {catalog.version}")
    except Exception as e:
        all_validation_failures.append(f"Load catalog failed: {e}")

    # Test 2: Get categories
    total_tests += 1
    try:
        categories = service.get_categories()
        if len(categories) != 5:
            all_validation_failures.append(f"Expected 5 categories, got {len(categories)}")
        category_ids = {cat.id for cat in categories}
        expected_ids = {"ux_interface", "onboarding", "flow", "communication", "operational"}
        if category_ids != expected_ids:
            all_validation_failures.append(f"Category IDs mismatch: {category_ids}")
    except Exception as e:
        all_validation_failures.append(f"Get categories failed: {e}")

    # Test 3: Get category by ID
    total_tests += 1
    try:
        cat = service.get_category_by_id("ux_interface")
        if cat is None:
            all_validation_failures.append("ux_interface category not found")
        elif cat.name != "UX / Interface":
            all_validation_failures.append(f"Category name mismatch: {cat.name}")
    except Exception as e:
        all_validation_failures.append(f"Get category by ID failed: {e}")

    # Test 4: Get non-existent category
    total_tests += 1
    try:
        cat = service.get_category_by_id("invalid_category")
        if cat is not None:
            all_validation_failures.append("Should return None for invalid category")
    except Exception as e:
        all_validation_failures.append(f"Get invalid category failed: {e}")

    # Test 5: Validate category
    total_tests += 1
    try:
        if not service.validate_category("flow"):
            all_validation_failures.append("flow should be valid")
        if service.validate_category("invalid"):
            all_validation_failures.append("invalid should not be valid")
    except Exception as e:
        all_validation_failures.append(f"Validate category failed: {e}")

    # Test 6: Get valid category IDs
    total_tests += 1
    try:
        ids = service.get_valid_category_ids()
        if len(ids) != 5:
            all_validation_failures.append(f"Expected 5 IDs, got {len(ids)}")
        if "communication" not in ids:
            all_validation_failures.append("communication should be in valid IDs")
    except Exception as e:
        all_validation_failures.append(f"Get valid category IDs failed: {e}")

    # Test 7: Get prompt context
    total_tests += 1
    try:
        context = service.get_prompt_context()
        if "## Catalogo de Acoes Disponiveis" not in context:
            all_validation_failures.append("Prompt context missing header")
        if "UX / Interface" not in context:
            all_validation_failures.append("Prompt context missing UX/Interface")
        if "Exemplos:" not in context:
            all_validation_failures.append("Prompt context missing examples")
    except Exception as e:
        all_validation_failures.append(f"Get prompt context failed: {e}")

    # Test 8: Category has examples
    total_tests += 1
    try:
        cat = service.get_category_by_id("flow")
        if not cat.examples:
            all_validation_failures.append("flow category should have examples")
        elif len(cat.examples) < 3:
            all_validation_failures.append(f"flow should have at least 3 examples: {len(cat.examples)}")
    except Exception as e:
        all_validation_failures.append(f"Category examples check failed: {e}")

    # Test 9: Example has typical impacts
    total_tests += 1
    try:
        cat = service.get_category_by_id("ux_interface")
        example = cat.examples[0]
        if not example.typical_impacts:
            all_validation_failures.append("Example should have typical_impacts")
        if "complexity" not in example.typical_impacts:
            all_validation_failures.append("Example should have complexity impact")
    except Exception as e:
        all_validation_failures.append(f"Example impacts check failed: {e}")

    # Test 10: Global singleton
    total_tests += 1
    try:
        service1 = get_action_catalog_service()
        service2 = get_action_catalog_service()
        if service1 is not service2:
            all_validation_failures.append("Should return same singleton instance")
    except Exception as e:
        all_validation_failures.append(f"Global singleton failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
