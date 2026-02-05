"""
Mechanisms API router for mechanism configuration and narrative generation.

REST endpoints for listing mechanisms, feature types, and generating LLM narratives.

References:
    - Spec: specs/039-narrative-mechanism-config/spec.md
    - Schemas: api/schemas/mechanisms.py
    - Service: services/narrative_service.py
"""

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.orm import Session

from synth_lab.api.schemas.mechanisms import (
    CreateMechanismRequest,
    CreateOptionRequest,
    FeatureTypeListResponse,
    FeatureTypeSchema,
    GenerateNarrativeRequest,
    GenerateNarrativeResponse,
    MechanismDefinitionSchema,
    MechanismListResponse,
    MechanismOptionSchema,
    SelectedMechanismSchema,
    UpdateMechanismRequest,
    UpdateOptionRequest,
)
from synth_lab.domain.entities.feature_type import FeatureType
from synth_lab.domain.entities.mechanism_definition import MechanismDefinition
from synth_lab.infrastructure.database_v2 import get_db_session
from synth_lab.repositories.mechanism_repository import MechanismRepository
from synth_lab.services.narrative_service import (
    NarrativeGenerationError,
    NarrativeService,
)

router = APIRouter(prefix="/mechanisms", tags=["mechanisms"])


# =============================================================================
# Helper functions
# =============================================================================


def _mechanism_to_schema(mech: MechanismDefinition) -> MechanismDefinitionSchema:
    """Convert MechanismDefinition entity to API schema."""
    return MechanismDefinitionSchema(
        id=mech.id,
        key=mech.key,
        label_pt=mech.label_pt,
        description=mech.description,
        options=[
            MechanismOptionSchema(
                id=opt.id,
                label=opt.label,
                value=opt.value,
                display_order=opt.display_order,
            )
            for opt in sorted(mech.options, key=lambda o: o.display_order)
        ],
    )


def _feature_type_to_schema(ft: FeatureType) -> FeatureTypeSchema:
    """Convert FeatureType entity to API schema."""
    return FeatureTypeSchema(
        id=ft.id,
        key=ft.key,
        label_pt=ft.label_pt,
        description=ft.description,
        amplifies_mechanisms=ft.amplifies_mechanisms or [],
    )


# =============================================================================
# T017: GET /mechanisms - List all mechanisms with options
# =============================================================================


@router.get(
    "",
    response_model=MechanismListResponse,
    summary="List all mechanisms",
    description="Retrieve all mechanism definitions with their options for dropdown rendering",
)
async def list_mechanisms(
    db: Session = Depends(get_db_session),
) -> MechanismListResponse:
    """
    List all mechanism definitions with their options.

    Used by frontend to populate dropdowns and by LLM prompt builder
    to know available mechanisms.

    Args:
        db: Database session

    Returns:
        MechanismListResponse with all mechanisms and options
    """
    repo = MechanismRepository(session=db)
    mechanisms = repo.list_all_with_options()

    logger.debug(f"Retrieved {len(mechanisms)} mechanisms")

    return MechanismListResponse(
        mechanisms=[_mechanism_to_schema(m) for m in mechanisms]
    )


# =============================================================================
# T018: GET /mechanisms/feature-types - List all feature types
# =============================================================================


@router.get(
    "/feature-types",
    response_model=FeatureTypeListResponse,
    summary="List all feature types",
    description="Retrieve all feature types with their amplified mechanisms",
)
async def list_feature_types(
    db: Session = Depends(get_db_session),
) -> FeatureTypeListResponse:
    """
    List all feature types.

    Used by LLM prompt builder to understand feature type definitions
    and which mechanisms they amplify.

    Args:
        db: Database session

    Returns:
        FeatureTypeListResponse with all feature types
    """
    repo = MechanismRepository(session=db)
    feature_types = repo.list_feature_types()

    logger.debug(f"Retrieved {len(feature_types)} feature types")

    return FeatureTypeListResponse(
        feature_types=[_feature_type_to_schema(ft) for ft in feature_types]
    )


# =============================================================================
# T019: POST /experiments/generate-narrative - Generate narrative with LLM
# Note: This endpoint is on /experiments prefix, but we handle it here
# and will register with a separate prefix in main.py
# =============================================================================

# Create a separate router for the generate-narrative endpoint
# since it needs to be under /experiments prefix
experiments_router = APIRouter(prefix="/experiments", tags=["mechanisms"])


@experiments_router.post(
    "/generate-narrative",
    response_model=GenerateNarrativeResponse,
    summary="Generate narrative with mechanism placeholders",
    description="Use LLM to analyze feature and generate narrative text with dropdowns",
)
async def generate_narrative(
    request: GenerateNarrativeRequest,
    db: Session = Depends(get_db_session),
) -> GenerateNarrativeResponse:
    """
    Generate a narrative template with mechanism placeholders.

    The LLM analyzes the feature name, hypothesis, and optional description
    to infer feature types, select relevant mechanisms (2-4), and generate
    a fluent Portuguese narrative with {mechanism_key} placeholders.

    Args:
        request: Feature details (name, hypothesis, description)
        db: Database session

    Returns:
        GenerateNarrativeResponse with template, selected mechanisms, and inferred types

    Raises:
        HTTPException 500: If LLM call fails
    """
    logger.info(f"Generating narrative for feature: {request.name}")

    service = NarrativeService(session=db)

    try:
        response = service.generate_narrative(
            name=request.name,
            hypothesis=request.hypothesis,
            description=request.description,
        )
    except NarrativeGenerationError as e:
        logger.error(f"Narrative generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

    return GenerateNarrativeResponse(
        inferred_types=response.inferred_types,
        narrative_template=response.narrative_template,
        selected_mechanisms=[
            SelectedMechanismSchema(
                key=sm.key,
                default_option_id=sm.default_option_id,
            )
            for sm in response.selected_mechanisms
        ],
        excluded_mechanisms=response.excluded_mechanisms,
    )


# =============================================================================
# US4: Admin CRUD endpoints (T035-T038)
# =============================================================================


@router.post(
    "",
    response_model=MechanismDefinitionSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new mechanism",
    description="Create a new mechanism definition (admin only)",
)
async def create_mechanism(
    request: CreateMechanismRequest,
    db: Session = Depends(get_db_session),
) -> MechanismDefinitionSchema:
    """
    Create a new mechanism definition.

    Args:
        request: Mechanism details (key, label_pt, description)
        db: Database session

    Returns:
        Created mechanism

    Raises:
        HTTPException 409: If mechanism key already exists
    """
    repo = MechanismRepository(session=db)

    # Check if key already exists
    existing = repo.get_by_key(request.key)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Mechanism with key '{request.key}' already exists",
        )

    mechanism = repo.create_mechanism(
        key=request.key,
        label_pt=request.label_pt,
        description=request.description,
    )

    logger.info(f"Created mechanism: {mechanism.key}")

    return _mechanism_to_schema(mechanism)


@router.put(
    "/{key}",
    response_model=MechanismDefinitionSchema,
    summary="Update a mechanism",
    description="Update mechanism label or description (admin only)",
)
async def update_mechanism(
    key: str,
    request: UpdateMechanismRequest,
    db: Session = Depends(get_db_session),
) -> MechanismDefinitionSchema:
    """
    Update an existing mechanism.

    Args:
        key: Mechanism key
        request: Fields to update
        db: Database session

    Returns:
        Updated mechanism

    Raises:
        HTTPException 404: If mechanism not found
    """
    repo = MechanismRepository(session=db)

    mechanism = repo.get_by_key(key)
    if not mechanism:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mechanism '{key}' not found",
        )

    updated = repo.update_mechanism(
        key=key,
        label_pt=request.label_pt,
        description=request.description,
    )

    logger.info(f"Updated mechanism: {key}")

    return _mechanism_to_schema(updated)


@router.post(
    "/{key}/options",
    response_model=MechanismOptionSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Add option to mechanism",
    description="Add a new option to an existing mechanism (admin only)",
)
async def add_option(
    key: str,
    request: CreateOptionRequest,
    db: Session = Depends(get_db_session),
) -> MechanismOptionSchema:
    """
    Add a new option to an existing mechanism.

    Args:
        key: Mechanism key
        request: Option details (label, value, display_order)
        db: Database session

    Returns:
        Created option

    Raises:
        HTTPException 404: If mechanism not found
    """
    repo = MechanismRepository(session=db)

    mechanism = repo.get_by_key(key)
    if not mechanism:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mechanism '{key}' not found",
        )

    option = repo.add_option(
        mechanism_key=key,
        label=request.label,
        value=request.value,
        display_order=request.display_order,
    )

    logger.info(f"Added option '{option.label}' to mechanism '{key}'")

    return MechanismOptionSchema(
        id=option.id,
        label=option.label,
        value=option.value,
        display_order=option.display_order,
    )


@router.put(
    "/{key}/options/{option_id}",
    response_model=MechanismOptionSchema,
    summary="Update mechanism option",
    description="Update an existing option (admin only)",
)
async def update_option(
    key: str,
    option_id: str,
    request: UpdateOptionRequest,
    db: Session = Depends(get_db_session),
) -> MechanismOptionSchema:
    """
    Update an existing mechanism option.

    Args:
        key: Mechanism key
        option_id: Option UUID
        request: Fields to update
        db: Database session

    Returns:
        Updated option

    Raises:
        HTTPException 404: If mechanism or option not found
    """
    repo = MechanismRepository(session=db)

    mechanism = repo.get_by_key(key)
    if not mechanism:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mechanism '{key}' not found",
        )

    # Verify option belongs to this mechanism
    option_exists = any(opt.id == option_id for opt in mechanism.options)
    if not option_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Option '{option_id}' not found in mechanism '{key}'",
        )

    option = repo.update_option(
        option_id=option_id,
        label=request.label,
        value=request.value,
        display_order=request.display_order,
    )

    logger.info(f"Updated option '{option_id}' in mechanism '{key}'")

    return MechanismOptionSchema(
        id=option.id,
        label=option.label,
        value=option.value,
        display_order=option.display_order,
    )
