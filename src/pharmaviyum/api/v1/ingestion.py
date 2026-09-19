"""
Ingestion API endpoints — document upload and job tracking.

Ingestion is administrator-only and every job is bound to an authenticated
pharmacy membership before the tenant id reaches the worker.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field
from redis.asyncio import Redis

from src.pharmaviyum.ai.dependencies import get_redis_client
from src.pharmaviyum.ai.mortarium_rag.ingestion import ingest_document
from src.pharmaviyum.core.logging import logger
from src.pharmaviyum.storage.object_storage import ObjectStorage, ObjectStorageError
from src.pharmaviyum.modules.auth.deps import CurrentSuperuser, CurrentUser, SessionDep
from src.pharmaviyum.modules.auth.tenant import require_pharmacy_tenant

router = APIRouter(prefix="/api/v1/ingest", tags=["Ingestion"])


class IngestURLRequest(BaseModel):
    source: str = Field(..., description="File path or URL")
    source_type: str = Field(..., description="pdf, html, or docx")
    pharmacy_id: int = Field(..., gt=0)
    country: str = Field(default="VN")
    language: str = Field(default="vi")


async def _authorize_ingestion_tenant(
    pharmacy_id: int,
    current_user: CurrentUser,
    session: SessionDep,
) -> int:
    """Return a pharmacy id only after membership authorization."""
    tenant = await require_pharmacy_tenant(pharmacy_id, current_user, session)
    return tenant.pharmacy_id


@router.post("/documents/upload", response_model=dict)
async def upload_and_ingest_document(
    _current_superuser: CurrentSuperuser,
    current_user: CurrentUser,
    session: SessionDep,
    pharmacy_id: int = Form(..., gt=0),
    file: UploadFile = File(..., description="PDF, DOCX, or HTML file"),
    country: str = Form(default="VN"),
    language: str = Form(default="vi"),
    extract_tables: bool = Form(default=True),
    ocr_enabled: bool = Form(default=True),
    redis: Redis = Depends(get_redis_client),
):
    """Upload a document after proving the admin belongs to its pharmacy."""
    authorized_pharmacy_id = await _authorize_ingestion_tenant(
        pharmacy_id, current_user, session
    )
    allowed_extensions = {".pdf", ".docx", ".html", ".htm"}
    file_ext = Path(file.filename).suffix.lower() if file.filename else ""
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(sorted(allowed_extensions))}",
        )

    max_size = 50 * 1024 * 1024
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum size is 50MB.",
        )

    job_id = str(uuid.uuid4())
    object_key = ObjectStorage.tenant_key(authorized_pharmacy_id, job_id, file_ext)
    try:
        storage = ObjectStorage()
        await storage.put_bytes(
            object_key,
            contents,
            file.content_type or "application/octet-stream",
        )
    except ObjectStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document storage is not configured",
        ) from exc

    source_type = (
        "pdf" if file_ext == ".pdf" else "docx" if file_ext == ".docx" else "html"
    )
    config = {
        "pharmacy_id": authorized_pharmacy_id,
        "country": country,
        "language": language,
        "extract_tables": extract_tables,
        "ocr_enabled": ocr_enabled,
        "original_filename": file.filename,
    }

    from src.pharmaviyum.ai.mortarium_rag.ingestion import IngestionProgressTracker

    tracker = IngestionProgressTracker(redis)
    await tracker.create_job(job_id, object_key, total_documents=1, metadata=config)
    try:
      task = ingest_document.delay(
          source=object_key,
          source_type=source_type,
          job_id=job_id,
          config={**config, "source_storage": "object"},
      )
    except Exception:
        try:
            await storage.delete(object_key)
        except Exception:
            logger.exception("Failed to clean up orphaned ingestion object %s", object_key)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ingestion queue is unavailable",
        )
    logger.info("Dispatched ingestion task %s for job %s", task.id, job_id)
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "File uploaded successfully. Ingestion started.",
        "check_status_url": f"/api/v1/ingest/jobs/{job_id}",
    }


@router.post("/documents/url", response_model=dict)
async def ingest_from_url(
    request: IngestURLRequest,
    _current_superuser: CurrentSuperuser,
    current_user: CurrentUser,
    session: SessionDep,
    redis: Redis = Depends(get_redis_client),
):
    """Trigger URL/path ingestion after pharmacy membership authorization."""
    authorized_pharmacy_id = await _authorize_ingestion_tenant(
        request.pharmacy_id, current_user, session
    )
    if request.source_type not in {"pdf", "html", "docx"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported source type",
        )
    parsed = urlparse(request.source)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL ingestion requires an absolute http(s) URL",
        )
    job_id = str(uuid.uuid4())
    config = {
        "pharmacy_id": authorized_pharmacy_id,
        "country": request.country,
        "language": request.language,
    }

    from src.pharmaviyum.ai.mortarium_rag.ingestion import IngestionProgressTracker

    tracker = IngestionProgressTracker(redis)
    await tracker.create_job(job_id, request.source, total_documents=1, metadata=config)
    task = ingest_document.delay(
        source=request.source,
        source_type=request.source_type,
        job_id=job_id,
        config=config,
    )
    return {"job_id": job_id, "status": "queued", "task_id": task.id}


@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    _current_user: CurrentSuperuser,
    redis: Redis = Depends(get_redis_client),
):
    """Get ingestion status for an administrator."""
    from src.pharmaviyum.ai.mortarium_rag.ingestion import IngestionProgressTracker

    tracker = IngestionProgressTracker(redis)
    job_data = await tracker.get_job(job_id)
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found or expired")
    return job_data


@router.get("/jobs")
async def list_jobs(
    _current_user: CurrentSuperuser,
    status_filter: str | None = None,
    limit: int = 20,
    redis: Redis = Depends(get_redis_client),
):
    """List ingestion jobs for an administrator."""
    from src.pharmaviyum.ai.mortarium_rag.ingestion import IngestionProgressTracker

    limit = min(max(limit, 1), 100)
    tracker = IngestionProgressTracker(redis)
    jobs = await tracker.list_jobs(status=status_filter, limit=limit)
    return {"jobs": jobs, "count": len(jobs)}
