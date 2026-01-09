import json
import azure.functions as func

from shared.auth import require_api_key, AuthError
from shared.logging_utils import get_logger
from shared.cosmos_client import delete_asset_doc
from shared.sql_client import execute
from shared.storage import get_blob_service_client, get_container_name





def main(req: func.HttpRequest) -> func.HttpResponse:
    # Handle CORS preflight (OPTIONS) requests - no authentication required
    if req.method == 'OPTIONS':
        return func.HttpResponse(
            '',
            status_code=204,
            headers={
                "Access-Control-Allow-Origin": "https://mystorage867.z33.web.core.windows.net",
                "Access-Control-Allow-Methods": "DELETE, OPTIONS",
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

    bsc = get_blob_service_client()
    container = bsc.get_container_client(get_container_name())
    to_delete = [b.name for b in container.list_blobs(name_starts_with=f"{asset_id}/")]
    for name in to_delete:
        container.delete_blob(name)

    execute("DELETE FROM file_metadata WHERE id = :id", {"id": asset_id})
    delete_asset_doc(asset_id)

    return func.HttpResponse(
        json.dumps({"deleted": True, "id": asset_id}),
        mimetype='application/json',
        headers={
            "Access-Control-Allow-Origin": "https://mystorage867.z33.web.core.windows.net"
        }
    )



