"""
Storage Service
Handles all interactions with Google Cloud Storage.
"""

from google.cloud import storage
from google.cloud.storage import Blob
from typing import Optional, Tuple, BinaryIO
import asyncio
from functools import lru_cache
from datetime import timedelta
import mimetypes
import os

from config.settings import get_settings


class StorageService:
    """Service for interacting with Google Cloud Storage."""
    
    def __init__(self):
        """Initialize the Storage service."""
        self.settings = get_settings()
        self._client = None
        self._bucket = None
    
    @property
    def client(self) -> storage.Client:
        """Get or create the Storage client."""
        if self._client is None:
            self._client = storage.Client(
                project=self.settings.google_cloud_project
            )
        return self._client
    
    @property
    def bucket(self) -> storage.Bucket:
        """Get the configured bucket."""
        if self._bucket is None:
            self._bucket = self.client.bucket(self.settings.gcs_bucket_name)
        return self._bucket
    
    def _get_blob_path(self, folder: str, filename: str) -> str:
        """Construct the full blob path.
        
        Args:
            folder: Folder within the bucket
            filename: File name
            
        Returns:
            Full blob path
        """
        return f"{folder}/{filename}"
    
    async def upload_file(
        self,
        file_data: BinaryIO,
        filename: str,
        folder: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> str:
        """Upload a file to Cloud Storage.
        
        Args:
            file_data: File data as binary stream
            filename: Name for the file
            folder: Optional folder (defaults to contracts folder)
            content_type: Optional MIME type
            
        Returns:
            Public URL or signed URL for the file
        """
        folder = folder or self.settings.gcs_contracts_folder
        blob_path = self._get_blob_path(folder, filename)
        
        blob = self.bucket.blob(blob_path)
        
        # Detect content type if not provided
        if content_type is None:
            content_type, _ = mimetypes.guess_type(filename)
            content_type = content_type or "application/octet-stream"
        
        # Upload the file
        await asyncio.to_thread(
            blob.upload_from_file,
            file_data,
            content_type=content_type
        )
        
        # Return the GCS URI
        return f"gs://{self.settings.gcs_bucket_name}/{blob_path}"
    
    async def upload_bytes(
        self,
        data: bytes,
        filename: str,
        folder: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> str:
        """Upload bytes data to Cloud Storage.
        
        Args:
            data: Raw bytes data
            filename: Name for the file
            folder: Optional folder
            content_type: Optional MIME type
            
        Returns:
            GCS URI for the file
        """
        folder = folder or self.settings.gcs_contracts_folder
        blob_path = self._get_blob_path(folder, filename)
        
        blob = self.bucket.blob(blob_path)
        
        if content_type is None:
            content_type, _ = mimetypes.guess_type(filename)
            content_type = content_type or "application/octet-stream"
        
        await asyncio.to_thread(
            blob.upload_from_string,
            data,
            content_type=content_type
        )
        
        return f"gs://{self.settings.gcs_bucket_name}/{blob_path}"
    
    async def upload_contract_pdf(
        self,
        file_data: BinaryIO,
        contract_id: str,
        original_filename: str,
    ) -> str:
        """Upload a contract PDF.
        
        Args:
            file_data: PDF file data
            contract_id: Contract ID for naming
            original_filename: Original file name
            
        Returns:
            GCS URI for the uploaded file
        """
        # Create unique filename
        ext = os.path.splitext(original_filename)[1] or ".pdf"
        filename = f"{contract_id}{ext}"
        
        return await self.upload_file(
            file_data,
            filename,
            folder=self.settings.gcs_contracts_folder,
            content_type="application/pdf"
        )
    
    async def upload_generated_document(
        self,
        file_data: BinaryIO,
        document_id: str,
        document_type: str,
        extension: str = ".docx",
    ) -> str:
        """Upload a generated document.
        
        Args:
            file_data: Document data
            document_id: Document ID for naming
            document_type: Type of document (memo, summary, etc.)
            extension: File extension
            
        Returns:
            GCS URI for the uploaded file
        """
        filename = f"{document_type}_{document_id}{extension}"
        
        # Determine content type
        content_types = {
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".pdf": "application/pdf",
            ".txt": "text/plain",
            ".md": "text/markdown",
        }
        content_type = content_types.get(extension, "application/octet-stream")
        
        return await self.upload_file(
            file_data,
            filename,
            folder=self.settings.gcs_documents_folder,
            content_type=content_type
        )
    
    async def download_file(
        self,
        blob_path: str,
    ) -> bytes:
        """Download a file from Cloud Storage.
        
        Args:
            blob_path: Path to the blob (without gs:// prefix)
            
        Returns:
            File contents as bytes
        """
        # Handle both full URI and path
        if blob_path.startswith("gs://"):
            # Parse gs:// URI
            parts = blob_path[5:].split("/", 1)
            if len(parts) == 2:
                blob_path = parts[1]
        
        blob = self.bucket.blob(blob_path)
        return await asyncio.to_thread(blob.download_as_bytes)
    
    async def download_contract(self, contract_id: str) -> Optional[bytes]:
        """Download a contract PDF by ID.
        
        Args:
            contract_id: Contract ID
            
        Returns:
            PDF bytes or None if not found
        """
        # Try common extensions
        for ext in [".pdf", ".PDF"]:
            blob_path = self._get_blob_path(
                self.settings.gcs_contracts_folder,
                f"{contract_id}{ext}"
            )
            blob = self.bucket.blob(blob_path)
            
            if await asyncio.to_thread(blob.exists):
                return await asyncio.to_thread(blob.download_as_bytes)
        
        return None
    
    async def get_signed_url(
        self,
        blob_path: str,
        expiration_minutes: int = 60,
    ) -> str:
        """Generate a signed URL for temporary access.
        
        Args:
            blob_path: Path to the blob
            expiration_minutes: URL expiration time in minutes
            
        Returns:
            Signed URL
        """
        # Handle gs:// URI
        if blob_path.startswith("gs://"):
            parts = blob_path[5:].split("/", 1)
            if len(parts) == 2:
                blob_path = parts[1]
        
        blob = self.bucket.blob(blob_path)
        
        url = await asyncio.to_thread(
            blob.generate_signed_url,
            expiration=timedelta(minutes=expiration_minutes),
            method="GET"
        )
        
        return url
    
    async def delete_file(self, blob_path: str) -> bool:
        """Delete a file from Cloud Storage.
        
        Args:
            blob_path: Path to the blob
            
        Returns:
            True if deleted, False if not found
        """
        # Handle gs:// URI
        if blob_path.startswith("gs://"):
            parts = blob_path[5:].split("/", 1)
            if len(parts) == 2:
                blob_path = parts[1]
        
        blob = self.bucket.blob(blob_path)
        
        if await asyncio.to_thread(blob.exists):
            await asyncio.to_thread(blob.delete)
            return True
        
        return False
    
    async def list_files(
        self,
        folder: Optional[str] = None,
        prefix: Optional[str] = None,
        limit: int = 100,
    ) -> list:
        """List files in a folder.
        
        Args:
            folder: Folder to list (defaults to contracts folder)
            prefix: Additional prefix filter
            limit: Maximum number of results
            
        Returns:
            List of blob information dicts
        """
        folder = folder or self.settings.gcs_contracts_folder
        full_prefix = f"{folder}/"
        
        if prefix:
            full_prefix = f"{full_prefix}{prefix}"
        
        blobs = self.client.list_blobs(
            self.settings.gcs_bucket_name,
            prefix=full_prefix,
            max_results=limit
        )
        
        results = []
        for blob in blobs:
            results.append({
                "name": blob.name,
                "size": blob.size,
                "content_type": blob.content_type,
                "created": blob.time_created.isoformat() if blob.time_created else None,
                "updated": blob.updated.isoformat() if blob.updated else None,
                "uri": f"gs://{self.settings.gcs_bucket_name}/{blob.name}",
            })
        
        return results
    
    async def file_exists(self, blob_path: str) -> bool:
        """Check if a file exists.
        
        Args:
            blob_path: Path to the blob
            
        Returns:
            True if file exists
        """
        # Handle gs:// URI
        if blob_path.startswith("gs://"):
            parts = blob_path[5:].split("/", 1)
            if len(parts) == 2:
                blob_path = parts[1]
        
        blob = self.bucket.blob(blob_path)
        return await asyncio.to_thread(blob.exists)
    
    async def get_file_metadata(self, blob_path: str) -> Optional[dict]:
        """Get metadata for a file.
        
        Args:
            blob_path: Path to the blob
            
        Returns:
            Metadata dict or None if not found
        """
        # Handle gs:// URI
        if blob_path.startswith("gs://"):
            parts = blob_path[5:].split("/", 1)
            if len(parts) == 2:
                blob_path = parts[1]
        
        blob = self.bucket.blob(blob_path)
        
        # Reload to get metadata
        try:
            await asyncio.to_thread(blob.reload)
            return {
                "name": blob.name,
                "size": blob.size,
                "content_type": blob.content_type,
                "created": blob.time_created.isoformat() if blob.time_created else None,
                "updated": blob.updated.isoformat() if blob.updated else None,
                "md5_hash": blob.md5_hash,
                "uri": f"gs://{self.settings.gcs_bucket_name}/{blob.name}",
            }
        except Exception:
            return None


# Create singleton instance
@lru_cache()
def get_storage_service() -> StorageService:
    """Get the singleton Storage service instance."""
    return StorageService()
