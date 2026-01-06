"""
Materials API router for synth-lab.

REST endpoints for experiment materials (images, videos, documents).

References:
    - Service: synth_lab.services.material_service
    - Schemas: synth_lab.api.schemas.materials
    - Spec: specs/001-experiment-materials/contracts/materials-api.yaml
"""

from fastapi import APIRouter, HTTPException

from synth_lab.api.schemas.materials import (
    DescriptionStatusEnum,
    FileTypeEnum,
    MaterialConfirmRequest,
    MaterialLimitsResponse,
    MaterialListResponse,
    MaterialReorderRequest,
    MaterialResponse,
    MaterialSummaryResponse,
    MaterialTypeEnum,
    MaterialUploadRequest,
    MaterialUploadResponse,
    MaterialViewUrlResponse,
    RetryDescriptionResponse,
)
from synth_lab.domain.entities.experiment_material import (
    DescriptionStatus,
    ExperimentMaterial,
    ExperimentMaterialSummary,
    MaterialType,
)
from synth_lab.repositories.experiment_material_repository import (
    MaterialLimitExceededError,
    MaterialNotFoundError,
)
from synth_lab.services.material_service import (
    FileSizeLimitError,
    MaterialService,
    UnsupportedFileTypeError,
)

router = APIRouter()


def _get_service() -> MaterialService:
    """Get material service instance."""
    return MaterialService()


def _map_material_type(api_type: MaterialTypeEnum) -> MaterialType:
    """Map API enum to domain enum."""
    return MaterialType(api_type.value)


def _summary_to_response(summary: ExperimentMaterialSummary) -> MaterialSummaryResponse:
    """Convert domain summary to API response with presigned thumbnail URL."""
    from synth_lab.infrastructure.storage_client import generate_view_url

    # Generate presigned URL for thumbnail if it exists
    thumbnail_view_url = None
    if summary.thumbnail_url:
        try:
            # Extract object key from thumbnail URL
            url_parts = summary.thumbnail_url.split("/")
            object_key = "/".join(url_parts[4:])  # Skip https:, empty, endpoint, bucket
            thumbnail_view_url = generate_view_url(object_key, expires_in=3600)
        except Exception:
            # If presigned URL generation fails, use None (placeholder icon will show)
            thumbnail_view_url = None

    return MaterialSummaryResponse(
        id=summary.id,
        file_type=FileTypeEnum(summary.file_type.value),
        file_name=summary.file_name,
        file_size=summary.file_size,
        thumbnail_url=thumbnail_view_url,
        material_type=MaterialTypeEnum(summary.material_type.value),
        description=summary.description,
        description_status=DescriptionStatusEnum(summary.description_status.value),
        display_order=summary.display_order,
    )


def _material_to_response(material: ExperimentMaterial) -> MaterialResponse:
    """Convert domain entity to API response with presigned thumbnail URL."""
    from synth_lab.infrastructure.storage_client import generate_view_url

    # Generate presigned URL for thumbnail if it exists
    thumbnail_view_url = None
    if material.thumbnail_url:
        try:
            url_parts = material.thumbnail_url.split("/")
            object_key = "/".join(url_parts[4:])
            thumbnail_view_url = generate_view_url(object_key, expires_in=3600)
        except Exception:
            thumbnail_view_url = None

    return MaterialResponse(
        id=material.id,
        experiment_id=material.experiment_id,
        file_type=FileTypeEnum(material.file_type.value),
        file_url=material.file_url,
        thumbnail_url=thumbnail_view_url,
        file_name=material.file_name,
        file_size=material.file_size,
        mime_type=material.mime_type,
        material_type=MaterialTypeEnum(material.material_type.value),
        description=material.description,
        description_status=DescriptionStatusEnum(material.description_status.value),
        display_order=material.display_order,
        created_at=material.created_at,
    )


@router.get(
    "/{experiment_id}/materials",
    response_model=MaterialListResponse,
    summary="List materials for an experiment",
)
async def list_materials(experiment_id: str) -> MaterialListResponse:
    """
    List all materials for an experiment.

    Returns material summaries ordered by display_order.
    """
    service = _get_service()
    summaries = service.list_materials(experiment_id)
    limits = service.get_limits(experiment_id)

    return MaterialListResponse(
        materials=[_summary_to_response(s) for s in summaries],
        total=limits["current_count"],
        total_size=limits["current_size"],
    )


@router.get(
    "/{experiment_id}/materials/limits",
    response_model=MaterialLimitsResponse,
    summary="Get material limits for an experiment",
)
async def get_limits(experiment_id: str) -> MaterialLimitsResponse:
    """
    Get current usage and limits for experiment materials.

    Returns count and size limits with current values.
    """
    service = _get_service()
    limits = service.get_limits(experiment_id)

    return MaterialLimitsResponse(
        current_count=limits["current_count"],
        max_count=limits["max_count"],
        current_size=limits["current_size"],
        max_size=limits["max_size"],
        can_upload=limits["can_upload"],
    )


@router.post(
    "/{experiment_id}/materials/upload-url",
    response_model=MaterialUploadResponse,
    summary="Request presigned upload URL",
)
async def request_upload_url(
    experiment_id: str,
    request: MaterialUploadRequest,
) -> MaterialUploadResponse:
    """
    Request a presigned URL for uploading a material file.

    Creates a pending material record and returns URL for direct S3 upload.
    The client should upload the file to the returned URL using PUT.
    """
    service = _get_service()

    try:
        result = service.request_upload_url(
            experiment_id=experiment_id,
            file_name=request.file_name,
            file_size=request.file_size,
            mime_type=request.mime_type,
            material_type=_map_material_type(request.material_type),
        )
    except UnsupportedFileTypeError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {e.mime_type}",
        )
    except FileSizeLimitError as e:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {e.file_size} bytes exceeds {e.max_size} bytes limit",
        )
    except MaterialLimitExceededError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    return MaterialUploadResponse(
        material_id=result["material_id"],
        upload_url=result["upload_url"],
        object_key=result["object_key"],
        expires_in=result["expires_in"],
    )


@router.post(
    "/{experiment_id}/materials/confirm",
    response_model=MaterialResponse,
    summary="Confirm upload completion",
)
async def confirm_upload(
    experiment_id: str,
    request: MaterialConfirmRequest,
) -> MaterialResponse:
    """
    Confirm that a material upload has completed.

    Verifies file exists in S3 and updates material record.
    Returns the full material with file URL.
    """
    service = _get_service()

    try:
        material = service.confirm_upload(
            experiment_id=experiment_id,
            material_id=request.material_id,
            object_key=request.object_key,
        )
    except MaterialNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Material not found: {e.material_id}",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    return _material_to_response(material)


@router.get(
    "/{experiment_id}/materials/{material_id}",
    response_model=MaterialResponse,
    summary="Get a material",
)
async def get_material(
    experiment_id: str,
    material_id: str,
) -> MaterialResponse:
    """
    Get details of a specific material.

    Returns full material data including file URL.
    """
    service = _get_service()

    try:
        material = service.get_material(material_id)
    except MaterialNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Material not found: {e.material_id}",
        )

    if material.experiment_id != experiment_id:
        raise HTTPException(
            status_code=404,
            detail=f"Material {material_id} not found in experiment {experiment_id}",
        )

    return _material_to_response(material)


@router.get(
    "/{experiment_id}/materials/{material_id}/view-url",
    response_model=MaterialViewUrlResponse,
    summary="Get presigned view URL",
)
async def get_view_url(
    experiment_id: str,
    material_id: str,
) -> MaterialViewUrlResponse:
    """
    Get a presigned URL for viewing a material.

    Returns URL valid for 1 hour by default.
    """
    service = _get_service()

    try:
        result = service.get_view_url(material_id)
    except MaterialNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Material not found: {e.material_id}",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    return MaterialViewUrlResponse(
        material_id=result["material_id"],
        view_url=result["view_url"],
        thumbnail_url=result["thumbnail_url"],
        expires_in=result["expires_in"],
    )


@router.put(
    "/{experiment_id}/materials/reorder",
    response_model=MaterialListResponse,
    summary="Reorder materials",
)
async def reorder_materials(
    experiment_id: str,
    request: MaterialReorderRequest,
) -> MaterialListResponse:
    """
    Reorder materials for an experiment.

    Updates display_order based on the provided order of material IDs.
    """
    service = _get_service()

    try:
        summaries = service.reorder_materials(
            experiment_id=experiment_id,
            material_ids=request.material_ids,
        )
    except MaterialNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Material not found: {e.material_id}",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    limits = service.get_limits(experiment_id)

    return MaterialListResponse(
        materials=[_summary_to_response(s) for s in summaries],
        total=limits["current_count"],
        total_size=limits["current_size"],
    )


@router.delete(
    "/{experiment_id}/materials/{material_id}",
    status_code=204,
    summary="Delete a material",
)
async def delete_material(
    experiment_id: str,
    material_id: str,
) -> None:
    """
    Delete a material from an experiment.

    Removes the material record and deletes the file from S3.
    """
    service = _get_service()

    try:
        service.delete_material(
            experiment_id=experiment_id,
            material_id=material_id,
        )
    except MaterialNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Material not found: {e.material_id}",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.post(
    "/{experiment_id}/materials/{material_id}/retry-description",
    response_model=RetryDescriptionResponse,
    summary="Retry description generation",
)
async def retry_description(
    experiment_id: str,
    material_id: str,
) -> RetryDescriptionResponse:
    """
    Retry AI description generation for a material.

    Only works for materials with 'failed' description status.
    Queues a new description generation task.
    """
    service = _get_service()

    try:
        material = service.get_material(material_id)
    except MaterialNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Material not found: {e.material_id}",
        )

    if material.experiment_id != experiment_id:
        raise HTTPException(
            status_code=404,
            detail=f"Material {material_id} not found in experiment {experiment_id}",
        )

    if material.description_status != DescriptionStatus.FAILED:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot retry: current status is {material.description_status.value}",
        )

    # TODO: Queue description generation (Phase 5)
    # For now, just update status to pending
    service.repository.update_description(
        material_id=material_id,
        description=None,
        status=DescriptionStatus.PENDING,
    )

    return RetryDescriptionResponse(
        material_id=material_id,
        status=DescriptionStatusEnum.PENDING,
        message="Description generation queued",
    )
