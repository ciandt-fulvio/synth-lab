"""
Documents API router for synth-lab.

REST endpoints for experiment documents (summary, prfaq, executive_summary).

References:
    - Service: synth_lab.services.document_service
    - Service: synth_lab.services.executive_summary_service
    - Schemas: synth_lab.api.schemas.documents
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Response
from loguru import logger

from synth_lab.api.schemas.documents import (
    DocumentAvailabilityResponse,
    DocumentDetailResponse,
    DocumentStatusEnum,
    DocumentSummaryResponse,
    DocumentTypeEnum,
    GenerateDocumentRequest,
    GenerateDocumentResponse)
from synth_lab.domain.entities.experiment_document import DocumentStatus, DocumentType
from synth_lab.repositories.analysis_repository import AnalysisRepository
from synth_lab.repositories.experiment_document_repository import DocumentNotFoundError
from synth_lab.services.document_service import DocumentService
from synth_lab.services.executive_summary_service import ExecutiveSummaryService

router = APIRouter()


def _get_service() -> DocumentService:
    """Get document service instance."""
    return DocumentService()


def _map_type(api_type: DocumentTypeEnum) -> DocumentType:
    """Map API enum to domain enum."""
    return DocumentType(api_type.value)


def _map_status(domain_status: DocumentStatus) -> DocumentStatusEnum:
    """Map domain enum to API enum."""
    return DocumentStatusEnum(domain_status.value)


def _get_analysis_id(experiment_id: str) -> str | None:
    """Get the latest completed analysis_id for an experiment."""
    repo = AnalysisRepository()
    return repo.get_latest_completed_analysis_id(experiment_id)


def _generate_executive_summary_background(experiment_id: str, analysis_id: str) -> None:
    """Background task to generate executive summary."""
    try:
        service = ExecutiveSummaryService()
        service.generate_markdown_summary(experiment_id, analysis_id)
        logger.info(f"Executive summary generated for {experiment_id}")
    except Exception as e:
        logger.error(f"Failed to generate executive summary for {experiment_id}: {e}")


@router.get(
    "/{experiment_id}/documents",
    response_model=list[DocumentSummaryResponse],
    summary="List all documents for an experiment")
async def list_documents(experiment_id: str) -> list[DocumentSummaryResponse]:
    """
    List all documents for an experiment.

    Returns summary info for each document (without content).
    """
    service = _get_service()
    docs = service.list_documents(experiment_id)

    return [
        DocumentSummaryResponse(
            id=doc.id,
            document_type=DocumentTypeEnum(doc.document_type.value),
            status=DocumentStatusEnum(doc.status.value),
            generated_at=doc.generated_at,
            model=doc.model)
        for doc in docs
    ]


@router.get(
    "/{experiment_id}/documents/availability",
    response_model=DocumentAvailabilityResponse,
    summary="Check document availability for an experiment")
async def check_availability(experiment_id: str) -> DocumentAvailabilityResponse:
    """
    Check availability of all document types for an experiment.

    Returns status for each document type (summary, prfaq, executive_summary).
    """
    service = _get_service()
    avail = service.check_availability(experiment_id)

    return DocumentAvailabilityResponse(
        summary=avail[DocumentType.SUMMARY],
        prfaq=avail[DocumentType.PRFAQ],
        executive_summary=avail[DocumentType.EXECUTIVE_SUMMARY])


@router.get(
    "/{experiment_id}/documents/{document_type}",
    response_model=DocumentDetailResponse,
    summary="Get a specific document")
async def get_document(
    experiment_id: str,
    document_type: DocumentTypeEnum) -> DocumentDetailResponse:
    """
    Get full details of a specific document.

    Includes markdown content and metadata.
    """
    service = _get_service()
    domain_type = _map_type(document_type)

    try:
        doc = service.get_document(experiment_id, domain_type)
    except DocumentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    return DocumentDetailResponse(
        id=doc.id,
        experiment_id=doc.experiment_id,
        document_type=DocumentTypeEnum(doc.document_type.value),
        markdown_content=doc.markdown_content,
        metadata=doc.metadata,
        generated_at=doc.generated_at,
        model=doc.model,
        status=DocumentStatusEnum(doc.status.value),
        error_message=doc.error_message)


@router.get(
    "/{experiment_id}/documents/{document_type}/markdown",
    response_class=Response,
    summary="Get document markdown content")
async def get_document_markdown(
    experiment_id: str,
    document_type: DocumentTypeEnum) -> Response:
    """
    Get only the markdown content of a document.

    Returns plain text markdown.
    """
    service = _get_service()
    domain_type = _map_type(document_type)

    try:
        markdown = service.get_markdown(experiment_id, domain_type)
    except DocumentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    return Response(content=markdown, media_type="text/markdown")


@router.post(
    "/{experiment_id}/documents/{document_type}/generate",
    response_model=GenerateDocumentResponse,
    summary="Generate or regenerate a document")
async def generate_document(
    experiment_id: str,
    document_type: DocumentTypeEnum,
    background_tasks: BackgroundTasks,
    request: GenerateDocumentRequest | None = None) -> GenerateDocumentResponse:
    """
    Start generation of a document.

    This endpoint starts generation and returns immediately.
    The actual generation runs in a background task.

    For executive_summary: requires completed analysis with chart insights.
    """
    domain_type = _map_type(document_type)

    # Handle executive_summary specifically
    if domain_type == DocumentType.EXECUTIVE_SUMMARY:
        # Check for analysis_id
        analysis_id = _get_analysis_id(experiment_id)
        if not analysis_id:
            raise HTTPException(
                status_code=400,
                detail="No completed analysis found for this experiment. "
                "Run quantitative analysis first.")

        # Start background generation
        background_tasks.add_task(
            _generate_executive_summary_background,
            experiment_id,
            analysis_id)

        return GenerateDocumentResponse(
            document_id=None,
            status=DocumentStatusEnum.GENERATING,
            message="Started generation of executive_summary")

    # For other document types, just mark as generating (legacy behavior)
    service = _get_service()
    model = request.model if request else "gpt-4o-mini"

    pending = service.start_generation(experiment_id, domain_type, model)

    if pending is None:
        # Already generating
        return GenerateDocumentResponse(
            document_id=None,
            status=DocumentStatusEnum.GENERATING,
            message=f"Document {document_type.value} is already being generated")

    return GenerateDocumentResponse(
        document_id=pending.id,
        status=DocumentStatusEnum.GENERATING,
        message=f"Started generation of {document_type.value}")


@router.delete(
    "/{experiment_id}/documents/{document_type}",
    summary="Delete a document")
async def delete_document(
    experiment_id: str,
    document_type: DocumentTypeEnum) -> dict:
    """
    Delete a specific document.

    Returns success status.
    """
    service = _get_service()
    domain_type = _map_type(document_type)

    deleted = service.delete_document(experiment_id, domain_type)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Document {document_type.value} not found for experiment {experiment_id}")

    return {"deleted": True, "document_type": document_type.value}
