"""Simple file storage - uses Supabase Storage or local filesystem."""
import os
import uuid
from pathlib import Path
from typing import Optional

import httpx
import structlog

from app.config import get_settings

log = structlog.get_logger()
settings = get_settings()


class StorageClient:
    """Unified storage interface - Supabase Storage or local filesystem."""

    def __init__(self):
        self.supabase_url = settings.supabase_url
        self.supabase_anon_key = settings.supabase_anon_key
        self.bucket = "psquare-files"

    async def upload(
        self,
        file_data: bytes,
        filename: str,
        folder: str = "uploads",
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload a file and return the URL."""
        # Generate unique filename
        ext = Path(filename).suffix
        unique_name = f"{uuid.uuid4()}{ext}"
        path = f"{folder}/{unique_name}"

        # Try Supabase first, fall back to local
        if self.supabase_url and self.supabase_anon_key:
            return await self._upload_supabase(path, file_data, content_type)
        else:
            return self._upload_local(path, file_data)

    async def _upload_supabase(
        self, path: str, file_data: bytes, content_type: str
    ) -> str:
        """Upload to Supabase Storage."""
        if not self.supabase_url or not self.supabase_anon_key:
            raise ValueError("Supabase not configured")

        url = f"{self.supabase_url}/storage/v1/object/{self.bucket}/{path}"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.supabase_anon_key}",
                    "Content-Type": content_type,
                },
                content=file_data,
                timeout=60.0,
            )
            response.raise_for_status()

        # Return public URL
        return f"{self.supabase_url}/storage/v1/object/public/{self.bucket}/{path}"

    def _upload_local(self, path: str, file_data: bytes) -> str:
        """Upload to local filesystem (dev only)."""
        upload_dir = Path("uploads") / path
        upload_dir.parent.mkdir(parents=True, exist_ok=True)

        with open(upload_dir, "wb") as f:
            f.write(file_data)

        # Return local URL path
        return f"/uploads/{path}"

    async def delete(self, url: str) -> bool:
        """Delete a file by URL."""
        if not url:
            return False

        # Handle local files
        if url.startswith("/uploads/"):
            path = Path("." + url)
            if path.exists():
                path.unlink()
            return True

        # Handle Supabase URLs
        if "supabase" in url and "storage" in url:
            # Extract path from URL
            path = url.split("/object/public/")[-1] if "/object/public/" in url else None
            if not path:
                return False

            if not self.supabase_url or not self.supabase_anon_key:
                return False

            delete_url = f"{self.supabase_url}/storage/v1/object/{self.bucket}/{path}"

            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    delete_url,
                    headers={"Authorization": f"Bearer {self.supabase_anon_key}"},
                    timeout=30.0,
                )
                return response.status_code in (200, 404)

        return False


# Singleton
_storage_client: Optional[StorageClient] = None


def get_storage_client() -> StorageClient:
    """Get storage client singleton."""
    global _storage_client
    if _storage_client is None:
        _storage_client = StorageClient()
    return _storage_client