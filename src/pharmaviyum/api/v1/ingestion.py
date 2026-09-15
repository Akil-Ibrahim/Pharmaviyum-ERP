"""
Ingestion API Endpoints — Document Upload and Job Tracking.
"""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

from fastapi import (APIRouter, Depends, File, Form, HTTPException, UploadFile,
                     status)
from pydantic import BaseModel, Field
from redis.asyncio import Redis

from src.pharmaviyum.ai.dependencies import get_redis_client
from src.pharmaviyum.ai.rag.ingestion import ingest_document
from src.pharmaviyum.api.dependencies import require_role
from src.pharmaviyum.core.logging import logger

router = APIRouter(prefix="/api/v1/ingest", tags=["Ingestion"])


class IngestURLRequest(BaseModel):
    source: str = Field(..., description="File path or URL")
    source_type: str = Field(..., description="pdf, html, or docx")
    country: str = Field(default="VN")
    language: str = Field(default="vi")


@router.post(
    "/documents/upload",
    response_model=dict,
    dependencies=[Depends(require_role(["pharmacist", "admin", "system"]))],
)
async def upload_and_ingest_document(
    file: UploadFile = File(..., description="PDF, DOCX, or HTML file"),
    country: str = Form(default="VN"),
    language: str = Form(default="vi"),
    extract_tables: bool = Form(default=True),
    ocr_enabled: bool = Form(default=True),
    redis: Redis = Depends(get_redis_client),
):
    """
    Upload a file and trigger asynchronous ingestion via Celery.
    """
    # 1. Validate file type
    allowed_extensions = {".pdf", ".docx", ".html", ".htm"}
    file_ext = Path(file.filename).suffix.lower() if file.filename else ""

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}",
        )

    # 2. Validate file size (e.g., max 50MB)
    MAX_SIZE = 50 * 1024 * 1024
    contents = await file.read()
    if len(contents) > MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum size is 50MB.",
        )

    # 3. Save to temporary file
    job_id = str(uuid.uuid4())
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
        tmp_file.write(contents)
        temp_path = tmp_file.name

    source_type = (
        "pdf" if file_ext == ".pdf" else "docx" if file_ext == ".docx" else "html"
    )

    config = {
        "country": country,
        "language": language,
        "extract_tables": extract_tables,
        "ocr_enabled": ocr_enabled,
        "original_filename": file.filename,
    }

    # 4. Initialize progress tracker
    from src.pharmaviyum.ai.rag.ingestion import IngestionProgressTracker

    tracker = IngestionProgressTracker(redis)
    await tracker.create_job(job_id, temp_path, total_documents=1, metadata=config)

    # 5. Dispatch Celery task
    task = ingest_document.delay(
        source=temp_path,
        source_type=source_type,
        job_id=job_id,
        config=config,
    )

    logger.info(
        f"Dispatched ingestion task {task.id} for uploaded file {file.filename} (job {job_id})"
    )

    return {
        "job_id": job_id,
        "status": "queued",
        "message": f"File '{file.filename}' uploaded successfully. Ingestion started.",
        "check_status_url": f"/api/v1/ingest/jobs/{job_id}",
    }


@router.post("/documents/url", response_model=dict)
async def ingest_from_url(
    request: IngestURLRequest,
    redis: Redis = Depends(get_redis_client),
):
    """Trigger ingestion from a URL or local path."""
    job_id = str(uuid.uuid4())
    config = {"country": request.country, "language": request.language}

    from src.pharmaviyum.ai.rag.ingestion import IngestionProgressTracker

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
async def get_job_status(job_id: str, redis: Redis = Depends(get_redis_client)):
    from src.pharmaviyum.ai.rag.ingestion import IngestionProgressTracker

    tracker = IngestionProgressTracker(redis)
    job_data = await tracker.get_job(job_id)
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found or expired")
    return job_data


@router.get("/jobs")
async def list_jobs(
    status_filter: str | None = None,
    limit: int = 20,
    redis: Redis = Depends(get_redis_client),
):
    from src.pharmaviyum.ai.rag.ingestion import IngestionProgressTracker

    tracker = IngestionProgressTracker(redis)
    jobs = await tracker.list_jobs(status=status_filter, limit=limit)
    return {"jobs": jobs, "count": len(jobs)}
