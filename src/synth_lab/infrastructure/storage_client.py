"""
S3-compatible storage client for Railway Buckets.

Provides presigned URL generation for direct uploads and downloads,
as well as object management operations.

Railway Buckets are S3-compatible, so we use boto3 with Railway's endpoint.

Environment Variables (Railway provides these automatically):
    ENDPOINT: Railway endpoint (default: https://storage.railway.app)
    BUCKET: Target bucket name
    ACCESS_KEY_ID: Access key for S3 authentication
    SECRET_ACCESS_KEY: Secret key for S3 authentication
    REGION: Bucket region (default: auto)

    Fallback AWS-style names also supported:
    S3_ENDPOINT_URL, BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

References:
    - Railway Storage Buckets: https://docs.railway.com/guides/storage-buckets
    - boto3 S3 Client: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html

Sample usage:
    client = get_s3_client()
    url = generate_upload_url("materials/exp_123/mat_456.png", "image/png")
"""

import base64
from io import BytesIO
from typing import BinaryIO

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from loguru import logger

from synth_lab.infrastructure.config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    BUCKET_NAME,
    PRESIGNED_URL_EXPIRATION,
    S3_ENDPOINT_URL,
    S3_REGION,
)

# S3 client singleton
_s3_client = None


def get_s3_client():
    """
    Get configured S3 client for Railway Storage.

    Returns:
        boto3 S3 client configured for Railway or AWS S3
    """
    global _s3_client

    if _s3_client is None:
        config = Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
        )

        _s3_client = boto3.client(
            "s3",
            endpoint_url=S3_ENDPOINT_URL,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=S3_REGION,
            config=config,
        )
        logger.debug(f"S3 client initialized: {S3_ENDPOINT_URL}, bucket: {BUCKET_NAME}")

    return _s3_client


def generate_upload_url(
    object_key: str,
    content_type: str,
    expires_in: int = PRESIGNED_URL_EXPIRATION,
) -> str:
    """
    Generate presigned URL for direct upload to S3.

    Args:
        object_key: Full path in bucket (e.g., "experiments/exp_123/materials/mat_456.png")
        content_type: MIME type of the file (e.g., "image/png")
        expires_in: URL expiration time in seconds (default: 15 minutes)

    Returns:
        Presigned URL for PUT upload
    """
    s3 = get_s3_client()

    url = s3.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": BUCKET_NAME,
            "Key": object_key,
            "ContentType": content_type,
        },
        ExpiresIn=expires_in,
    )

    logger.debug(f"Generated upload URL for {object_key}, expires in {expires_in}s")
    return url


def generate_view_url(
    object_key: str,
    expires_in: int = 3600,
) -> str:
    """
    Generate presigned URL for viewing/downloading from S3.

    Args:
        object_key: Full path in bucket
        expires_in: URL expiration time in seconds (default: 1 hour, max: 7 days)

    Returns:
        Presigned URL for GET download
    """
    s3 = get_s3_client()

    url = s3.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": BUCKET_NAME,
            "Key": object_key,
        },
        ExpiresIn=expires_in,
    )

    logger.debug(f"Generated view URL for {object_key}, expires in {expires_in}s")
    return url


def check_object_exists(object_key: str) -> bool:
    """
    Check if an object exists in S3.

    Args:
        object_key: Full path in bucket

    Returns:
        True if object exists, False otherwise
    """
    s3 = get_s3_client()

    try:
        s3.head_object(Bucket=BUCKET_NAME, Key=object_key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        logger.error(f"Error checking object {object_key}: {e}")
        raise


def delete_object(object_key: str) -> bool:
    """
    Delete an object from S3.

    Args:
        object_key: Full path in bucket

    Returns:
        True if deleted successfully, False if not found
    """
    s3 = get_s3_client()

    try:
        s3.delete_object(Bucket=BUCKET_NAME, Key=object_key)
        logger.info(f"Deleted object {object_key}")
        return True
    except ClientError as e:
        logger.error(f"Error deleting object {object_key}: {e}")
        return False


def upload_object(
    object_key: str,
    data: BinaryIO | bytes,
    content_type: str,
) -> bool:
    """
    Upload an object directly to S3 (for server-side uploads like thumbnails).

    Args:
        object_key: Full path in bucket
        data: File-like object or bytes to upload
        content_type: MIME type of the file

    Returns:
        True if uploaded successfully
    """
    s3 = get_s3_client()

    try:
        if isinstance(data, bytes):
            data = BytesIO(data)

        s3.upload_fileobj(
            data,
            BUCKET_NAME,
            object_key,
            ExtraArgs={"ContentType": content_type},
        )
        logger.info(f"Uploaded object {object_key}")
        return True
    except ClientError as e:
        logger.error(f"Error uploading object {object_key}: {e}")
        return False


def get_object_as_base64(object_key: str) -> str | None:
    """
    Download an object from S3 and return as base64 string.

    Useful for passing images to LLM vision APIs.

    Args:
        object_key: Full path in bucket

    Returns:
        Base64-encoded string of object content, or None if not found
    """
    s3 = get_s3_client()

    try:
        response = s3.get_object(Bucket=BUCKET_NAME, Key=object_key)
        content = response["Body"].read()
        return base64.b64encode(content).decode("utf-8")
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            logger.warning(f"Object not found: {object_key}")
            return None
        logger.error(f"Error getting object {object_key}: {e}")
        raise


def get_object_bytes(object_key: str) -> bytes | None:
    """
    Download an object from S3 and return as bytes.

    Args:
        object_key: Full path in bucket

    Returns:
        Object content as bytes, or None if not found
    """
    s3 = get_s3_client()

    try:
        response = s3.get_object(Bucket=BUCKET_NAME, Key=object_key)
        return response["Body"].read()
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            logger.warning(f"Object not found: {object_key}")
            return None
        logger.error(f"Error getting object {object_key}: {e}")
        raise


if __name__ == "__main__":
    import sys

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Test 1: S3 client can be created (doesn't require credentials for creation)
    total_tests += 1
    try:
        client = get_s3_client()
        if client is None:
            all_validation_failures.append("get_s3_client() returned None")
    except Exception as e:
        all_validation_failures.append(f"get_s3_client() failed: {e}")

    # Test 2: generate_upload_url returns a string
    total_tests += 1
    try:
        url = generate_upload_url("test/test.png", "image/png", 60)
        if not isinstance(url, str) or not url.startswith("http"):
            all_validation_failures.append(f"generate_upload_url returned invalid URL: {url}")
    except Exception as e:
        all_validation_failures.append(f"generate_upload_url failed: {e}")

    # Test 3: generate_view_url returns a string
    total_tests += 1
    try:
        url = generate_view_url("test/test.png", 60)
        if not isinstance(url, str) or not url.startswith("http"):
            all_validation_failures.append(f"generate_view_url returned invalid URL: {url}")
    except Exception as e:
        all_validation_failures.append(f"generate_view_url failed: {e}")

    # Test 4: Configuration values are set
    total_tests += 1
    if not S3_ENDPOINT_URL:
        all_validation_failures.append("S3_ENDPOINT_URL is not set")
    if not BUCKET_NAME:
        all_validation_failures.append("BUCKET_NAME is not set")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        print(f"  S3_ENDPOINT_URL: {S3_ENDPOINT_URL}")
        print(f"  BUCKET_NAME: {BUCKET_NAME}")
        print(f"  AWS credentials: {'set' if AWS_ACCESS_KEY_ID else 'NOT SET (required for runtime)'}")
        sys.exit(0)
