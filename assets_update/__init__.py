import json
import azure.functions as func

from shared.auth import require_api_key, AuthError
from shared.logging_utils import get_logger
from shared.cosmos_client import get_asset_doc, upsert_asset_doc
from shared.sql_client import execute


logger = get_logger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    # Handle CORS preflight (OPTIONS) requests - no authentication required
    if req.method == 'OPTIONS':
        return func.HttpResponse(
            '',
            status_code=204,
            headers={
                "Access-Control-Allow-Origin": "https://mystorage867.z33.web.core.windows.net",
                "Access-Control-Allow-Methods": "PUT, OPTIONS",
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

    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            'Invalid JSON',
            status_code=400,
            headers={
                "Access-Control-Allow-Origin": "https://mystorage867.z33.web.core.windows.net"
            }
        )

    update_fields = {}
    for k in ['fileName', 'fileType', 'fileSize', 'blobUrl']:
        if k in body:
            update_fields[k] = body[k]

    # Update Cosmos doc if exists
    doc = get_asset_doc(asset_id) or {"id": asset_id}
    doc.update(update_fields)
    upsert_asset_doc(doc)

    # Update SQL row
    fields_sql = []
    params = {"id": asset_id}
    mapping = {
        'fileName': 'file_name',
        'fileType': 'file_type',
        'fileSize': 'file_size',
        'blobUrl': 'blob_url',
    }
    for k, v in update_fields.items():
        fields_sql.append(f"{mapping[k]} = :{mapping[k]}")
        params[mapping[k]] = v
    status = body.get('status')
    if status:
        fields_sql.append("status = :status")
        params['status'] = status

    if fields_sql:
        sql = "UPDATE file_metadata SET " + ", ".join(fields_sql) + " WHERE id = :id"
        execute(sql, params)

    return func.HttpResponse(
        json.dumps({"id": asset_id, **doc}),
        mimetype='application/json',
        headers={
            "Access-Control-Allow-Origin": "https://mystorage867.z33.web.core.windows.net"
        }
    )



