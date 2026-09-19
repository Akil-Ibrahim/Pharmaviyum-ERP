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
        return await asyncio.to_thread(body.read)

    async def delete(self, key: str) -> None:
        await asyncio.to_thread(self._client.delete_object, Bucket=self._bucket, Key=key)
