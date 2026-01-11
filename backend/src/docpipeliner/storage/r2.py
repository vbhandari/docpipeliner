"""Cloudflare R2 storage client."""

import logging
from io import BytesIO
from typing import BinaryIO, Optional
from uuid import UUID

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from docpipeliner.config import get_settings

logger = logging.getLogger(__name__)


class R2StorageError(Exception):
    """Exception raised by R2 storage operations."""

    pass


class R2StorageClient:
    """Client for Cloudflare R2 object storage.

    Uses boto3 with S3-compatible API to interact with R2.
    """

    def __init__(
        self,
        account_id: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        bucket_name: Optional[str] = None,
    ):
        """Initialize R2 storage client.

        Args:
            account_id: Cloudflare account ID (default: from settings)
            access_key_id: R2 access key ID (default: from settings)
            secret_access_key: R2 secret access key (default: from settings)
            bucket_name: R2 bucket name (default: from settings)
        """
        settings = get_settings()

        self._account_id = account_id or settings.r2_account_id
        self._access_key_id = access_key_id or settings.r2_access_key_id
        self._secret_access_key = secret_access_key or settings.r2_secret_access_key
        self._bucket_name = bucket_name or settings.r2_bucket_name
        self._endpoint_url = settings.r2_endpoint

        self._client = self._create_client()

    def _create_client(self):
        """Create boto3 S3 client configured for R2."""
        return boto3.client(
            "s3",
            endpoint_url=self._endpoint_url,
            aws_access_key_id=self._access_key_id,
            aws_secret_access_key=self._secret_access_key,
            config=Config(
                signature_version="s3v4",
                retries={"max_attempts": 3, "mode": "adaptive"},
            ),
        )

    def _get_document_key(self, document_id: UUID, filename: str) -> str:
        """Generate storage key for a document.

        Args:
            document_id: Document UUID
            filename: Original filename

        Returns:
            Storage key path
        """
        return f"documents/{document_id}/{filename}"

    def _get_page_key(self, document_id: UUID, page_number: int) -> str:
        """Generate storage key for a page image.

        Args:
            document_id: Document UUID
            page_number: Page number (1-indexed)

        Returns:
            Storage key path
        """
        return f"documents/{document_id}/pages/page_{page_number:04d}.png"

    async def upload_document(
        self,
        document_id: UUID,
        filename: str,
        file_data: BinaryIO,
        content_type: str = "application/pdf",
    ) -> str:
        """Upload a document to R2.

        Args:
            document_id: Document UUID
            filename: Original filename
            file_data: File data as binary stream
            content_type: MIME type of the file

        Returns:
            Storage path of the uploaded document

        Raises:
            R2StorageError: If upload fails
        """
        key = self._get_document_key(document_id, filename)

        try:
            self._client.upload_fileobj(
                file_data,
                self._bucket_name,
                key,
                ExtraArgs={"ContentType": content_type},
            )
            logger.info(f"Uploaded document to R2: {key}")
            return key

        except ClientError as e:
            logger.error(f"Failed to upload document to R2: {e}")
            raise R2StorageError(f"Failed to upload document: {e}") from e

    async def upload_page_image(
        self,
        document_id: UUID,
        page_number: int,
        image_data: bytes,
    ) -> str:
        """Upload a page image to R2.

        Args:
            document_id: Document UUID
            page_number: Page number (1-indexed)
            image_data: PNG image data as bytes

        Returns:
            Storage path of the uploaded image

        Raises:
            R2StorageError: If upload fails
        """
        key = self._get_page_key(document_id, page_number)

        try:
            self._client.upload_fileobj(
                BytesIO(image_data),
                self._bucket_name,
                key,
                ExtraArgs={"ContentType": "image/png"},
            )
            logger.info(f"Uploaded page image to R2: {key}")
            return key

        except ClientError as e:
            logger.error(f"Failed to upload page image to R2: {e}")
            raise R2StorageError(f"Failed to upload page image: {e}") from e

    async def download_document(self, storage_path: str) -> bytes:
        """Download a document from R2.

        Args:
            storage_path: Storage path of the document

        Returns:
            Document data as bytes

        Raises:
            R2StorageError: If download fails
        """
        try:
            response = self._client.get_object(
                Bucket=self._bucket_name,
                Key=storage_path,
            )
            return response["Body"].read()

        except ClientError as e:
            logger.error(f"Failed to download document from R2: {e}")
            raise R2StorageError(f"Failed to download document: {e}") from e

    async def download_page_image(
        self,
        document_id: UUID,
        page_number: int,
    ) -> bytes:
        """Download a page image from R2.

        Args:
            document_id: Document UUID
            page_number: Page number (1-indexed)

        Returns:
            Image data as bytes

        Raises:
            R2StorageError: If download fails
        """
        key = self._get_page_key(document_id, page_number)
        return await self.download_document(key)

    async def delete_document(self, document_id: UUID, filename: str) -> None:
        """Delete a document from R2.

        Args:
            document_id: Document UUID
            filename: Original filename

        Raises:
            R2StorageError: If deletion fails
        """
        key = self._get_document_key(document_id, filename)

        try:
            self._client.delete_object(
                Bucket=self._bucket_name,
                Key=key,
            )
            logger.info(f"Deleted document from R2: {key}")

        except ClientError as e:
            logger.error(f"Failed to delete document from R2: {e}")
            raise R2StorageError(f"Failed to delete document: {e}") from e

    async def delete_document_folder(self, document_id: UUID) -> None:
        """Delete all files for a document from R2.

        Args:
            document_id: Document UUID

        Raises:
            R2StorageError: If deletion fails
        """
        prefix = f"documents/{document_id}/"

        try:
            # List all objects with the prefix
            paginator = self._client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self._bucket_name, Prefix=prefix)

            objects_to_delete = []
            for page in pages:
                if "Contents" in page:
                    objects_to_delete.extend(
                        [{"Key": obj["Key"]} for obj in page["Contents"]]
                    )

            if objects_to_delete:
                self._client.delete_objects(
                    Bucket=self._bucket_name,
                    Delete={"Objects": objects_to_delete},
                )
                logger.info(f"Deleted {len(objects_to_delete)} objects for document {document_id}")

        except ClientError as e:
            logger.error(f"Failed to delete document folder from R2: {e}")
            raise R2StorageError(f"Failed to delete document folder: {e}") from e

    async def generate_presigned_url(
        self,
        storage_path: str,
        expiration: int = 3600,
    ) -> str:
        """Generate a presigned URL for downloading a file.

        Args:
            storage_path: Storage path of the file
            expiration: URL expiration time in seconds (default: 1 hour)

        Returns:
            Presigned URL

        Raises:
            R2StorageError: If URL generation fails
        """
        try:
            url = self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket_name, "Key": storage_path},
                ExpiresIn=expiration,
            )
            return url

        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise R2StorageError(f"Failed to generate presigned URL: {e}") from e

    async def health_check(self) -> bool:
        """Check if R2 storage is accessible.

        Returns:
            True if R2 is accessible, False otherwise
        """
        try:
            self._client.head_bucket(Bucket=self._bucket_name)
            return True
        except ClientError:
            return False
