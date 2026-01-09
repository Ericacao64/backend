import json
import azure.functions as func

from shared.auth import require_api_key, AuthError
from shared.logging_utils import get_logger
from shared.cosmos_client import get_asset_doc
from shared.sql_client import query_all


logger = get_logger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    # Handle CORS preflight (OPTIONS) requests - no authentication required
    if req.method == 'OPTIONS':
        return func.HttpResponse(
            '',
            status_code=204,
            headers={
                "Access-Control-Allow-Origin": "https://mystorage867.z33.web.core.windows.net",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
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

    asset_id = req.route_params.get('id')
    if not asset_id:
        return func.HttpResponse(
            'id is required',
            status_code=400,
            headers={
                "Access-Control-Allow-Origin": "https://mystorage867.z33.web.core.windows.net"
            }
        )

    doc = get_asset_doc(asset_id)
    row = None
    rows = query_all(
        "SELECT id, file_name AS fileName, file_type AS fileType, file_size AS fileSize, blob_url AS blobUrl, status, created_at AS uploadDate FROM file_metadata WHERE id = :id",
        {"id": asset_id},
    )
    if rows:
        row = rows[0]

    if not doc and not row:
        return func.HttpResponse(
            'Not Found',
            status_code=404,
            headers={
                "Access-Control-Allow-Origin": "https://mystorage867.z33.web.core.windows.net"
            }
        )

    result = doc or {}
    if row:
        result.update(row)
    return func.HttpResponse(
        json.dumps(result),
        mimetype='application/json',
        headers={
            "Access-Control-Allow-Origin": "https://mystorage867.z33.web.core.windows.net"
        }
    )



