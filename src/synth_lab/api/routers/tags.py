"""
Tags API router for synth-lab.

REST endpoints for tag management and experiment tagging.

References:
    - Domain entities: synth_lab.domain.entities.tag
    - Repository: synth_lab.repositories.tag_repository
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from synth_lab.domain.entities.tag import Tag
from synth_lab.infrastructure.database_v2 import get_session
from synth_lab.repositories.tag_repository import TagRepository

router = APIRouter()


# =============================================================================
# Request/Response Schemas
# =============================================================================


class TagResponse(BaseModel):
    """Response schema for tag data."""

    id: str = Field(description="Tag ID.")
    name: str = Field(description="Tag name.")


class TagCreateRequest(BaseModel):
    """Request schema for creating a new tag."""

    name: str = Field(max_length=50, description="Tag name (max 50 chars).")


class AddTagRequest(BaseModel):
    """Request schema for adding a tag to an experiment."""

    tag_name: str = Field(description="Name of the tag to add.")


# =============================================================================
# Tag Endpoints
# =============================================================================


@router.get("", response_model=list[TagResponse])
async def list_tags() -> list[TagResponse]:
    """
    List all available tags.

    Returns a list of all tags in the system, ordered by name.
    """
    with get_session() as session:
        repo = TagRepository(session=session)
        tags = repo.list_tags()
        return [TagResponse(id=tag.id, name=tag.name) for tag in tags]


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(data: TagCreateRequest) -> TagResponse:
    """
    Create a new tag.

    Creates a new tag if it doesn't already exist. If a tag with the same name
    exists, returns that existing tag instead of creating a duplicate.

    Args:
        data: Tag creation request with name.

    Returns:
        Created or existing tag.
    """
    with get_session() as session:
        repo = TagRepository(session=session)

        # Check if tag already exists
        existing_tag = repo.get_by_name(data.name)
        if existing_tag:
            return TagResponse(id=existing_tag.id, name=existing_tag.name)

        # Create new tag
        new_tag = Tag(name=data.name)
        created_tag = repo.create(new_tag)
        return TagResponse(id=created_tag.id, name=created_tag.name)


@router.post("/experiments/{experiment_id}/tags", status_code=status.HTTP_204_NO_CONTENT)
async def add_tag_to_experiment(experiment_id: str, data: AddTagRequest) -> None:
    """
    Add a tag to an experiment.

    Creates the tag if it doesn't exist, then associates it with the experiment.
    If the experiment already has this tag, does nothing (idempotent).

    Args:
        experiment_id: ID of the experiment.
        data: Request with tag name to add.

    Raises:
        404: Experiment not found.
    """
    with get_session() as session:
        # Verify experiment exists
        from synth_lab.repositories.experiment_repository import ExperimentRepository

        exp_repo = ExperimentRepository(session=session)
        experiment = exp_repo.get_by_id(experiment_id)
        if experiment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment {experiment_id} not found",
            )

        # Get or create tag
        tag_repo = TagRepository(session=session)
        tag = tag_repo.get_by_name(data.tag_name)
        if tag is None:
            tag = Tag(name=data.tag_name)
            tag = tag_repo.create(tag)

        # Add tag to experiment (idempotent)
        tag_repo.add_tag_to_experiment(experiment_id, tag.id)


@router.delete("/experiments/{experiment_id}/tags/{tag_name}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_tag_from_experiment(experiment_id: str, tag_name: str) -> None:
    """
    Remove a tag from an experiment.

    Removes the association between the tag and the experiment.
    The tag itself is not deleted from the system.

    Args:
        experiment_id: ID of the experiment.
        tag_name: Name of the tag to remove.

    Raises:
        404: Experiment or tag not found, or tag not associated with experiment.
    """
    with get_session() as session:
        # Verify experiment exists
        from synth_lab.repositories.experiment_repository import ExperimentRepository

        exp_repo = ExperimentRepository(session=session)
        experiment = exp_repo.get_by_id(experiment_id)
        if experiment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experiment {experiment_id} not found",
            )

        # Get tag
        tag_repo = TagRepository(session=session)
        tag = tag_repo.get_by_name(tag_name)
        if tag is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag '{tag_name}' not found",
            )

        # Remove tag from experiment
        removed = tag_repo.remove_tag_from_experiment(experiment_id, tag.id)
        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag '{tag_name}' not associated with experiment {experiment_id}",
            )
