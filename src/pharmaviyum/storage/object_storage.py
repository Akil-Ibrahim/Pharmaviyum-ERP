"""S3-compatible object storage for cross-container document ingestion."""

from __future__ import annotations

import asyncio
import io
from typing import BinaryIO

import boto3
from botocore.client import Config

from src.pharmaviyum.core.config import settings


class ObjectStorageError(RuntimeError):
    """Raised when object storage is unavailable or misconfigured."""


class ObjectStorage:
    """Small S3-compatible storage adapter used by ingestion workers."""

    def __init__(self) -> None:
        if not settings.OBJECT_STORAGE_BUCKET:
            raise ObjectStorageError("OBJECT_STORAGE_BUCKET is not configured")
        if not settings.OBJECT_STORAGE_ACCESS_KEY or not settings.OBJECT_STORAGE_SECRET_KEY:
            raise ObjectStorageError("Object storage credentials are not configured")

        kwargs: dict[str, object] = {
            "service_name": "s3",
            "aws_access_key_id": settings.OBJECT_STORAGE_ACCESS_KEY,
            "aws_secret_access_key": settings.OBJECT_STORAGE_SECRET_KEY,
            "region_name": settings.OBJECT_STORAGE_REGION,
            "config": Config(signature_version="s3v4"),
        }
        if settings.OBJECT_STORAGE_ENDPOINT:
            kwargs["endpoint_url"] = settings.OBJECT_STORAGE_ENDPOINT
        self._client = boto3.client(**kwargs)
        self._bucket = settings.OBJECT_STORAGE_BUCKET

    @staticmethod
    def tenant_key(pharmacy_id: int, job_id: str, suffix: str) -> str:
        """Build a tenant-scoped ingestion key from validated components."""
        if (
            not isinstance(pharmacy_id, int)
            or isinstance(pharmacy_id, bool)
            or pharmacy_id <= 0
            or not job_id
            or "/" in job_id
            or "\\" in job_id
        ):
            raise ValueError("Invalid object storage key components")
        clean_suffix = suffix.lstrip(".").lower()
        if clean_suffix not in {"pdf", "docx", "html", "htm"}:
            raise ValueError("Unsupported object suffix")
        return f"ingestion/{pharmacy_id}/{job_id}.{clean_suffix}"

    @staticmethod
    def validate_tenant_key(key: str, pharmacy_id: int) -> None:
        """Reject object keys that are outside the authorized tenant namespace."""
        expected_prefix = f"ingestion/{pharmacy_id}/"
        if (
            not isinstance(pharmacy_id, int)
            or isinstance(pharmacy_id, bool)
            or pharmacy_id <= 0
            or not isinstance(key, str)
            or not key.startswith(expected_prefix)
        ):
            raise ValueError("Object storage key is outside the tenant scope")

        relative_key = key[len(expected_prefix) :]
        if (
            not relative_key
            or "/" in relative_key
            or "\\" in relative_key
            or relative_key in {".", ".."}
            or ".." in relative_key
        ):
            raise ValueError("Object storage key is outside the tenant scope")
        suffix = relative_key.rsplit(".", 1)[-1].lower() if "." in relative_key else ""
        if suffix not in {"pdf", "docx", "html", "htm"}:
            raise ValueError("Unsupported object suffix")


    async def put_bytes(self, key: str, data: bytes, content_type: str) -> None:
        await asyncio.to_thread(
            self._client.put_object,
            Bucket=self._bucket,
            Key=key,
            Body=io.BytesIO(data),
            ContentType=content_type,
        )

    async def get_bytes(self, key: str) -> bytes:
        response = await asyncio.to_thread(
            self._client.get_object,
            Bucket=self._bucket,
            Key=key,
        )
        body: BinaryIO = response["Body"]
        try:
            return await asyncio.to_thread(body.read)
        finally:
            await asyncio.to_thread(body.close)

    async def delete(self, key: str) -> None:
        await asyncio.to_thread(self._client.delete_object, Bucket=self._bucket, Key=key)
