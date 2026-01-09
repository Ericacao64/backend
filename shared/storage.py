import os
from datetime import datetime, timedelta
from typing import Tuple

from azure.storage.blob import (
    BlobServiceClient,
    BlobSasPermissions,
    generate_blob_sas,
)


def get_blob_service_client() -> BlobServiceClient:
    conn_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    return BlobServiceClient.from_connection_string(conn_str)


def get_container_name() -> str:
    return os.getenv('AZURE_STORAGE_CONTAINER', 'assets')


def generate_blob_write_sas(container: str, blob_name: str, hours: int = 2) -> str:
    account_name = os.getenv('AZURE_STORAGE_ACCOUNT')
    account_key = _extract_account_key_from_connection_string(os.getenv('AZURE_STORAGE_CONNECTION_STRING', ''))
    sas = generate_blob_sas(
        account_name=account_name,
        container_name=container,
        blob_name=blob_name,
        account_key=account_key,
        permission=BlobSasPermissions(create=True, write=True, add=True),
        expiry=datetime.utcnow() + timedelta(hours=hours),
        content_disposition=f'inline; filename="{blob_name}"',
    )
    return sas


def get_blob_url(container: str, blob_name: str) -> str:
    account = os.getenv('AZURE_STORAGE_ACCOUNT')
    return f"https://{account}.blob.core.windows.net/{container}/{blob_name}"


def _extract_account_key_from_connection_string(conn_str: str) -> str:
    parts = {kv.split('=', 1)[0]: kv.split('=', 1)[1] for kv in conn_str.split(';') if '=' in kv}
    return parts.get('AccountKey', '')



