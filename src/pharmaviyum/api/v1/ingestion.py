"""
Ingestion API Endpoints — Document Upload and Job Tracking.

All ingestion operations require an authenticated administrator. URL/path
ingestion is especially privileged because the worker may access resources
outside the request process.
"""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import (APIRouter, Depends, File, Form, HTTPException, UploadFile,
                     status)
from pydantic import BaseModel, Field
from redis.asyncio import Redis

from src.pharmaviyum.ai.dependencies import get_redis_client
from src.pharmaviyum.ai.rag.ingestion import ingest_document
from src.pharmaviyum.modules.auth.deps import CurrentSuperuser
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
)
async def upload_and_ingest_document(
    file: UploadFile = File(..., description="PDF, DOCX, or HTML file"),
    country: str = Form(default="VN"),
    language: str = Form(default="vi"),
    extract_tables: bool = Form(default=True),
    ocr_enabled: bool = Form(default=True),
    redis: Redis = Depends(get_redis_client),
    _current_user: CurrentSuperuser = None,
):
    """Upload a document and trigger asynchronous ingestion."""
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

    from src.pharmaviyum.ai.rag.ingestion import IngestionProgressTracker

    tracker = IngestionProgressTracker(redis)
    await tracker.create_job(job_id, temp_path, total_documents=1, metadata=config)

    task = ingest_document.delay(
        source=temp_path,
        source_type=source_type,
        job_id=job_id,
        config=config,
    )
    logger.info(
        "Dispatched ingestion task %s for uploaded file %s (job %s)",
        task.id,
        file.filename,
        job_id,
    )

    return {
        "job_id": job_id,
        "status": "queued",
        "message": "File uploaded successfully. Ingestion started.",
        "check_status_url": f"/api/v1/ingest/jobs/{job_id}",
    }


@router.post("/documents/url", response_model=dict)
async def ingest_from_url(
    request: IngestURLRequest,
    redis: Redis = Depends(get_redis_client),
    _current_user: CurrentSuperuser = None,
):
    """Trigger ingestion from a URL or local path for administrators only.

    The worker-side source must still enforce an outbound network policy and
    reject private/link-local destinations before fetching arbitrary URLs.
    """
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
async def get_job_status(
    job_id: str,
    redis: Redis = Depends(get_redis_client),
    _current_user: CurrentSuperuser = None,
):
    """Get ingestion status for an administrator."""
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
    _current_user: CurrentSuperuser = None,
):
    """List ingestion jobs for an administrator."""
    from src.pharmaviyum.ai.rag.ingestion import IngestionProgressTracker

    limit = min(max(limit, 1), 100)
    tracker = IngestionProgressTracker(redis)
    jobs = await tracker.list_jobs(status=status_filter, limit=limit)
    return {"jobs": jobs, "count": len(jobs)}
