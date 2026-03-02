from __future__ import annotations

import asyncio
from io import BytesIO

from minio import Minio
from minio.error import S3Error

from bot.config import get_settings


class MinioClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.bucket = settings.minio_bucket_photos
        self.client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )

    async def ensure_bucket(self) -> None:
        def _ensure() -> None:
            found = self.client.bucket_exists(self.bucket)
            if not found:
                self.client.make_bucket(self.bucket)

        await asyncio.to_thread(_ensure)

    async def put_bytes(self, key: str, content: bytes, content_type: str = "image/jpeg") -> None:
        await self.ensure_bucket()

        def _put() -> None:
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=key,
                data=BytesIO(content),
                length=len(content),
                content_type=content_type,
            )

        await asyncio.to_thread(_put)

    async def presigned_get_url(self, key: str, expires: int = 86400) -> str:
        def _url() -> str:
            return self.client.presigned_get_object(self.bucket, key, expires=expires)

        try:
            return await asyncio.to_thread(_url)
        except S3Error:
            return ""
