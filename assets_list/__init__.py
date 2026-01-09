import json
import os
import azure.functions as func

from shared.auth import require_api_key, AuthError
from shared.logging_utils import get_logger
from shared.sql_client import query_all


logger = get_logger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    # Debug: Log request details
    print(f"=== assets_list function called ===")
    print(f"Method: {req.method}")
    print(f"URL: {req.url}")
    print(f"Route params: {req.route_params}")
    print(f"Headers: {dict(req.headers)}")
    
    # Handle CORS preflight (OPTIONS) requests - no authentication required
    if req.method == 'OPTIONS':
        
            '',
            status_code=204,
            headers={
                "Access-Control-Allow-Origin": "https://mystorage867.z33.web.core.windows.net",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, x-api-key",
                
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
        print("Attempting to query database...")
        print(f"SQL_SERVER env: {os.getenv('SQL_SERVER', 'NOT SET')}")
        print(f"SQL_DATABASE env: {os.getenv('SQL_DATABASE', 'NOT SET')}")
        print(f"SQL_USERNAME env: {os.getenv('SQL_USERNAME', 'NOT SET')}")
        
        rows = query_all(
            """
            SELECT id, file_name AS fileName, file_type AS fileType, file_size AS fileSize,
                   blob_url AS blobUrl, status, created_at AS uploadDate
            FROM file_metadata
            ORDER BY created_at DESC
            """
        )
        
        print(f"Query returned {len(rows)} rows")
        
        return func.HttpResponse(
            json.dumps(rows),
            mimetype='application/json',
            headers={
                "Access-Control-Allow-Origin": "https://mystorage867.z33.web.core.windows.net"
            }
        )
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Error in assets_list: {str(e)}", exc_info=True)
        print(f"ERROR in assets_list: {str(e)}")
        print(f"Traceback: {error_trace}")
        return func.HttpResponse(
            json.dumps({
                'error': 'Internal Server Error', 
                'message': str(e),
                'type': type(e).__name__
            }),
            status_code=500,
            mimetype='application/json',
            headers={
                "Access-Control-Allow-Origin": "https://mystorage867.z33.web.core.windows.net"
            }
        )