import tempfile

from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import get_settings

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx"}


def get_s3_client():
    settings = get_settings()
    return boto3.client("s3", region_name=settings.aws_region)


def list_supported_documents() -> list[dict]:
    settings = get_settings()
    client = get_s3_client()
    documents: list[dict] = []

    try:
        paginator = client.get_paginator("list_objects_v2")
        pages = paginator.paginate(
            Bucket=settings.aws_s3_bucket,
            Prefix=settings.aws_s3_prefix,
        )

        for page in pages:
            for item in page.get("Contents", []):
                key = item["Key"]
                if Path(key).suffix.lower() not in SUPPORTED_EXTENSIONS:
                    continue

                documents.append(
                    {
                        "key": key,
                        "filename": Path(key).name,
                        "size_bytes": item["Size"],
                        "etag": item["ETag"].strip('"'),
                        "last_modified": item["LastModified"].isoformat(),
                    }
                )
    except (ClientError, BotoCoreError) as exc:
        raise RuntimeError(
            f"Unable to list documents from AWS S3: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    return documents

def download_document(s3_key: str) -> Path:
    settings = get_settings()
    client = get_s3_client()

    filename = Path(s3_key).name
    temporary_directory = Path(tempfile.gettempdir()) / "knowledge-assistant"
    temporary_directory.mkdir(parents=True, exist_ok=True)

    destination = temporary_directory / filename

    try:
        client.download_file(
            settings.aws_s3_bucket,
            s3_key,
            str(destination),
        )
    except (ClientError, BotoCoreError) as exc:
        raise RuntimeError(
            f"Unable to download {s3_key}: {exc}"
        ) from exc

    return destination


def get_object_etag(s3_key: str) -> str:
    settings = get_settings()
    client = get_s3_client()

    try:
        response = client.head_object(Bucket=settings.aws_s3_bucket, Key=s3_key)
    except (ClientError, BotoCoreError) as exc:
        raise RuntimeError(f"Unable to read metadata for {s3_key}: {exc}") from exc

    return response["ETag"].strip('"')


def upload_document(filename: str, content: bytes, folder: str | None = None) -> tuple[str, str]:
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported document type: {extension}")

    settings = get_settings()
    client = get_s3_client()

    prefix = settings.aws_s3_prefix
    if folder:
        prefix = f"{prefix}{folder.strip('/')}/"

    s3_key = f"{prefix}{filename}"

    try:
        client.put_object(Bucket=settings.aws_s3_bucket, Key=s3_key, Body=content)
    except (ClientError, BotoCoreError) as exc:
        raise RuntimeError(f"Unable to upload {filename} to AWS S3: {exc}") from exc

    return s3_key, get_object_etag(s3_key)


def delete_s3_object(s3_key: str) -> None:
    settings = get_settings()
    client = get_s3_client()

    try:
        client.delete_object(Bucket=settings.aws_s3_bucket, Key=s3_key)
    except (ClientError, BotoCoreError) as exc:
        raise RuntimeError(f"Unable to delete {s3_key} from AWS S3: {exc}") from exc