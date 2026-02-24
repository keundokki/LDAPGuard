"""
S3-compatible cloud storage service for backup uploads/downloads.

Supports:
- AWS S3
- MinIO
- Backblaze B2
- Wasabi
- DigitalOcean Spaces
- Any S3-compatible storage
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Service for managing backup uploads/downloads to S3-compatible cloud storage."""

    def __init__(self):
        """Initialize storage service (S3 client created dynamically with latest settings)."""  # noqa: E501
        self.enabled = settings.S3_ENABLED
        self._s3_client = None
        self._config_cache = {}
        self._cache_time = None

        logger.info("S3 storage service initialized (dynamic configuration mode)")

    async def _get_db_settings(self, db: AsyncSession) -> Dict[str, str]:
        """Retrieve S3 settings from database."""
        from api.models.models import SystemSetting

        # Check cache (valid for 60 seconds)
        import time
        if self._cache_time and (time.time() - self._cache_time < 60):
            return self._config_cache

        result = await db.execute(
            select(SystemSetting).where(
                SystemSetting.key.in_([
                    's3_enabled',
                    's3_provider',
                    's3_region',
                    's3_bucket',
                    's3_access_key',
                    's3_secret_key',
                    's3_endpoint',
                    's3_storage_class'
                ])
            )
        )
        settings_list = result.scalars().all()

        config = {s.key: s.value for s in settings_list}

        # Update cache
        self._config_cache = config
        self._cache_time = time.time()

        return config

    async def _get_s3_client(self, db: AsyncSession):
        """Get or create S3 client with current database settings."""
        db_config = await self._get_db_settings(db)

        # Check if S3 is enabled in database
        s3_enabled = db_config.get('s3_enabled', '').lower() == 'true'
        if not s3_enabled and not settings.S3_ENABLED:
            raise RuntimeError("S3 storage is not enabled")

        # Get credentials from database or fall back to environment
        access_key = db_config.get('s3_access_key') or settings.S3_ACCESS_KEY_ID
        secret_key = db_config.get('s3_secret_key') or settings.S3_SECRET_ACCESS_KEY
        bucket_name = db_config.get('s3_bucket') or settings.S3_BUCKET_NAME
        region = db_config.get('s3_region') or settings.S3_REGION
        endpoint = db_config.get('s3_endpoint') or settings.S3_ENDPOINT_URL

        if not bucket_name:
            raise ValueError("S3 bucket name is required")

        if not access_key or not secret_key:
            raise ValueError("S3 access key and secret key are required")

        # Store for later use
        self.bucket_name = bucket_name
        self.storage_class = db_config.get(
            's3_storage_class') or settings.S3_STORAGE_CLASS
        self.provider = self._detect_provider(endpoint)

        # Configure boto3 client
        config = Config(
            region_name=region,
            signature_version='s3v4',
            retries={'max_attempts': 3, 'mode': 'adaptive'}
        )

        # Build client kwargs
        client_kwargs = {
            'service_name': 's3',
            'aws_access_key_id': access_key,
            'aws_secret_access_key': secret_key,
            'config': config
        }

        # Add endpoint URL for non-AWS providers
        if endpoint:
            client_kwargs['endpoint_url'] = endpoint

        return boto3.client(**client_kwargs)

    def _detect_provider(self, endpoint_url: Optional[str] = None) -> str:
        """Detect cloud storage provider from endpoint URL."""
        if not endpoint_url:
            return "aws"

        endpoint = endpoint_url.lower()

        if "minio" in endpoint:
            return "minio"
        elif "backblaze" in endpoint or "b2" in endpoint:
            return "backblaze"
        elif "wasabi" in endpoint:
            return "wasabi"
        elif "digitalocean" in endpoint:
            return "digitalocean"
        else:
            return "s3-compatible"

    async def upload_backup(
        self,
        file_path: str,
        object_key: str,
        metadata: Optional[Dict[str, str]] = None,
        storage_class: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Upload a backup file to S3-compatible storage.

        Args:
            file_path: Local path to backup file
            object_key: S3 object key (path in bucket)
            metadata: Optional metadata to attach to object
            storage_class: Storage class (overrides default)
            db: Database session for loading S3 settings

        Returns:
            Dictionary with upload details (url, etag, size, etc.)

        Raises:
            FileNotFoundError: If local file doesn't exist
            ClientError: If S3 upload fails
        """
        if not db:
            raise ValueError("Database session is required for S3 operations")

        s3_client = await self._get_s3_client(db)

        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise FileNotFoundError(f"Backup file not found: {file_path}")

        file_size = file_path_obj.stat().st_size
        storage_class = storage_class or self.storage_class

        logger.info(
            f"Uploading backup to S3: {object_key} ({file_size} bytes, class: {storage_class})")  # noqa: E501

        try:
            # Prepare upload parameters
            extra_args = {
                'StorageClass': storage_class,
            }

            # Add metadata if provided
            if metadata:
                extra_args['Metadata'] = metadata

            # Upload file
            s3_client.upload_file(
                str(file_path_obj),
                self.bucket_name,
                object_key,
                ExtraArgs=extra_args
            )

            # Get object metadata
            response = s3_client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )

            result = {
                'success': True,
                'bucket': self.bucket_name,
                'object_key': object_key,
                'size': file_size,
                'etag': response.get('ETag', '').strip('"'),
                'storage_class': storage_class,
                'provider': self.provider,
                'uploaded_at': datetime.utcnow().isoformat(),
                'metadata': metadata or {}
            }

            logger.info(f"Successfully uploaded backup to S3: {object_key}")
            return result

        except NoCredentialsError:
            logger.error("S3 credentials not available")
            raise
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"S3 upload failed ({error_code}): {e}")
            raise

    async def download_backup(
        self,
        object_key: str,
        destination_path: str,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Download a backup file from S3-compatible storage.

        Args:
            object_key: S3 object key to download
            destination_path: Local path to save file
            db: Database session for loading S3 settings

        Returns:
            Dictionary with download details

        Raises:
            ClientError: If S3 download fails
        """
        if not db:
            raise ValueError("Database session is required for S3 operations")

        s3_client = await self._get_s3_client(db)

        destination_path_obj = Path(destination_path)
        destination_path_obj.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Downloading backup from S3: {object_key}")

        try:
            # Download file
            s3_client.download_file(
                self.bucket_name,
                object_key,
                str(destination_path_obj)
            )

            file_size = destination_path_obj.stat().st_size

            result = {
                'success': True,
                'bucket': self.bucket_name,
                'object_key': object_key,
                'destination_path': str(destination_path_obj),
                'size': file_size,
                'downloaded_at': datetime.utcnow().isoformat()
            }

            logger.info(
                f"Successfully downloaded backup from S3: {object_key} ({file_size} bytes)")  # noqa: E501
            return result

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"S3 download failed ({error_code}): {e}")
            raise

    async def delete_backup(self, object_key: str, db: Optional[AsyncSession] = None) -> Dict[str, Any]:  # noqa: E501
        """
        Delete a backup file from S3-compatible storage.

        Args:
            object_key: S3 object key to delete
            db: Database session for loading S3 settings

        Returns:
            Dictionary with deletion details

        Raises:
            ClientError: If S3 deletion fails
        """
        if not db:
            raise ValueError("Database session is required for S3 operations")

        s3_client = await self._get_s3_client(db)

        logger.info(f"Deleting backup from S3: {object_key}")

        try:
            s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )

            result = {
                'success': True,
                'bucket': self.bucket_name,
                'object_key': object_key,
                'deleted_at': datetime.utcnow().isoformat()
            }

            logger.info(f"Successfully deleted backup from S3: {object_key}")
            return result

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"S3 deletion failed ({error_code}): {e}")
            raise

    async def list_backups(
        self,
        prefix: Optional[str] = None,
        max_keys: int = 1000,
        db: Optional[AsyncSession] = None
    ) -> List[Dict[str, Any]]:
        """
        List backup files in S3-compatible storage.

        Args:
            prefix: Optional prefix to filter objects
            max_keys: Maximum number of objects to return
            db: Database session for loading S3 settings

        Returns:
            List of object details

        Raises:
            ClientError: If S3 list fails
        """
        if not db:
            raise ValueError("Database session is required for S3 operations")

        s3_client = await self._get_s3_client(db)

        logger.info(f"Listing backups from S3 (prefix: {prefix or 'all'})")

        try:
            params = {
                'Bucket': self.bucket_name,
                'MaxKeys': max_keys
            }

            if prefix:
                params['Prefix'] = prefix

            response = s3_client.list_objects_v2(**params)

            objects = []
            for obj in response.get('Contents', []):
                objects.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'etag': obj.get('ETag', '').strip('"'),
                    'storage_class': obj.get('StorageClass', 'STANDARD')
                })

            logger.info(f"Found {len(objects)} backups in S3")
            return objects

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"S3 list failed ({error_code}): {e}")
            raise

    async def object_exists(self, object_key: str) -> bool:
        """
        Check if an object exists in S3.

        Args:
            object_key: S3 object key to check

        Returns:
            True if object exists, False otherwise
        """
        if not self.enabled:
            return False

        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            return True
        except ClientError as e:
            if e.response.get('Error', {}).get('Code') == '404':
                return False
            raise

    async def get_object_info(self, object_key: str, db: Optional[AsyncSession] = None) -> Dict[str, Any]:  # noqa: E501
        """
        Get metadata for an S3 object.

        Args:
            object_key: S3 object key
            db: Database session for loading S3 settings

        Returns:
            Dictionary with object metadata

        Raises:
            ClientError: If object doesn't exist or request fails
        """
        if not db:
            raise ValueError("Database session is required for S3 operations")

        s3_client = await self._get_s3_client(db)

        try:
            response = s3_client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )

            return {
                'key': object_key,
                'size': response['ContentLength'],
                'last_modified': response['LastModified'].isoformat(),
                'etag': response.get('ETag', '').strip('"'),
                'storage_class': response.get('StorageClass', 'STANDARD'),
                'metadata': response.get('Metadata', {})
            }

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"Failed to get object info ({error_code}): {e}")
            raise

    def generate_presigned_url(
        self,
        object_key: str,
        expiration: int = 3600,
        http_method: str = 'get_object'
    ) -> str:
        """
        Generate a presigned URL for temporary access to an S3 object.

        Args:
            object_key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)
            http_method: HTTP method (get_object, put_object)

        Returns:
            Presigned URL

        Raises:
            ClientError: If URL generation fails
        """
        if not self.enabled:
            raise RuntimeError("S3 storage is not enabled")

        try:
            url = self.s3_client.generate_presigned_url(
                http_method,
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_key
                },
                ExpiresIn=expiration
            )

            logger.info(
                f"Generated presigned URL for {object_key} (expires in {expiration}s)")
            return url

        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test S3 connection and credentials.

        Returns:
            Dictionary with connection test results
        """
        if not self.enabled:
            return {
                'success': False,
                'message': 'S3 storage is not enabled',
                'enabled': False
            }

        try:
            # Try to head the bucket
            self.s3_client.head_bucket(Bucket=self.bucket_name)

            return {
                'success': True,
                'message': 'Successfully connected to S3 storage',
                'enabled': True,
                'provider': self.provider,
                'bucket': self.bucket_name,
                'region': settings.S3_REGION
            }

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            return {
                'success': False,
                'message': f'S3 connection failed: {error_code}',
                'enabled': True,
                'error': str(e)
            }


# Singleton instance
storage_service = StorageService()
