import json
import uuid
from datetime import datetime, timezone

import azure.functions as func

from shared.auth import require_api_key, AuthError
from shared.logging_utils import get_logger
from shared.storage import generate_blob_write_sas, get_container_name, get_blob_url
from shared.cosmos_client import upsert_asset_doc
from shared.sql_client import execute


logger = get_logger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    # Debug: Log request details
    print(f"=== assets_create function called ===")
    print(f"Method: {req.method}")
    print(f"URL: {req.url}")
    
    # Handle CORS preflight (OPTIONS) requests - no authentication required
    if req.method == 'OPTIONS':
        return func.HttpResponse(
            '',
            status_code=204,
            headers={
                "Access-Control-Allow-Origin": "https://mystorage867.z33.web.core.windows.net",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, x-api-key",
                "Access-Control-Max-Age": "3600"
            }
        )
    
    # Get API key from headers (support both lowercase and uppercase)
    api_key = req.headers.get('x-api-key') or req.headers.get('X-Api-Key') or req.headers.get('X-API-Key')
    print(f"Request method: {req.method}, API Key present: {bool(api_key)}, API Key value: {api_key if api_key else 'None'}")
    
    # Validate API key
    try:
        require_api_key(api_key)
    except AuthError as e:
        logger.warning(f"Authentication failed: {str(e)}")
        return func.HttpResponse(
            json.dumps({'error': 'Unauthorized', 'message': str(e)}),
            status_code=401,
            mimetype='application/json',
            headers={
                "Access-Control-Allow-Origin": "https://mystorage867.z33.web.core.windows.net"
            }
        )

    try:
        body = req.get_json()
        print(f"Request body: {body}")
    except ValueError as e:
        print(f"Error parsing JSON: {str(e)}")
        return func.HttpResponse(
            json.dumps({'error': 'Invalid JSON', 'message': str(e)}),
            status_code=400,
            mimetype='application/json',
            headers={
                "Access-Control-Allow-Origin": "https://mystorage867.z33.web.core.windows.net"
            }
        )

    file_name = body.get('fileName')
    file_type = body.get('fileType')
    file_size = int(body.get('fileSize') or 0)
    if not file_name or not file_type or not file_size:
        return func.HttpResponse(
            json.dumps({'error': 'Bad Request', 'message': 'fileName, fileType, fileSize are required'}),
            status_code=400,
            mimetype='application/json',
            headers={
                "Access-Control-Allow-Origin": "https://mystorage867.z33.web.core.windows.net"
            }
        )

    try:
        asset_id = str(uuid.uuid4())
        print(f"Generated asset_id: {asset_id}")
        
        container = get_container_name()
        print(f"Container name: {container}")
        
        blob_name = f"{asset_id}/{file_name}"
        print(f"Blob name: {blob_name}")
        
        sas = generate_blob_write_sas(container, blob_name)
        print(f"SAS generated: {bool(sas)}")
        
        blob_url = get_blob_url(container, blob_name)
        print(f"Blob URL: {blob_url}")

        now_iso = datetime.now(timezone.utc).isoformat()

        # Cosmos: initial metadata document
        print("Attempting to upsert Cosmos document...")
        doc = {
            'id': asset_id,
            'fileName': file_name,
            'fileType': file_type,
            'uploadDate': now_iso,
            'fileSize': file_size,
            'blobUrl': blob_url,
        }
        upsert_asset_doc(doc)
        print("Cosmos document upserted successfully")

        # SQL: create metadata row (status pending)
        print("Attempting to insert SQL row...")
        execute(
            """
            INSERT INTO file_metadata (id, user_id, file_name, file_type, file_size, blob_url, status, created_at)
            VALUES (:id, NULL, :file_name, :file_type, :file_size, :blob_url, 'pending', SYSUTCDATETIME())
            """,
            {
                'id': asset_id,
                'file_name': file_name,
                'file_type': file_type,
                'file_size': file_size,
                'blob_url': blob_url,
            },
        )
        print("SQL row inserted successfully")

        response = {
            'id': asset_id,
            'blobUrl': blob_url,
            'uploadUrl': f"{blob_url}?{sas}",
        }
        logger.info("Created asset %s", asset_id)
        return func.HttpResponse(
            json.dumps(response),
            status_code=201,
            mimetype='application/json',
            headers={
                "Access-Control-Allow-Origin": "https://mystorage867.z33.web.core.windows.net"
            }
        )
    except Exception as e:
        logger.error(f"Error in assets_create: {str(e)}", exc_info=True)
        print(f"ERROR in assets_create: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return func.HttpResponse(
            json.dumps({'error': 'Internal Server Error', 'message': str(e)}),
            status_code=500,
            mimetype='application/json',
            headers={
                "Access-Control-Allow-Origin": "https://mystorage867.z33.web.core.windows.net"
            }
        )



