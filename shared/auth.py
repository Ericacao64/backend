import os
from typing import Optional


class AuthError(Exception):
    pass


def require_api_key(provided_key: Optional[str]) -> None:
    """
    Validate API key from request headers.
    
    Args:
        provided_key: The API key from request headers (x-api-key)
        
    Raises:
        AuthError: If API key is missing or invalid
    """
    expected = os.getenv('API_KEY')
    
    # If API_KEY is not set in environment, skip validation (for development)
    if not expected:
        print("WARNING: API_KEY environment variable is not set. Skipping authentication.")
        return
    
    # Check if API key is provided
    if not provided_key:
        print(f"ERROR: API key is missing. Expected key is set: {bool(expected)}")
        raise AuthError('API key is required')
    
    # Strip whitespace from both keys for comparison
    provided_key = provided_key.strip()
    expected = expected.strip()
    
    # Check if API key matches
    if provided_key != expected:
        # Log detailed comparison (without exposing full keys)
        print(f"ERROR: Invalid API key provided.")
        print(f"  Provided key length: {len(provided_key)}, First 3 chars: {provided_key[:3] if len(provided_key) >= 3 else 'N/A'}")
        print(f"  Expected key length: {len(expected)}, First 3 chars: {expected[:3] if len(expected) >= 3 else 'N/A'}")
        print(f"  Keys match: {provided_key == expected}")
        raise AuthError('Invalid API key')
    
    print("INFO: API key validation successful")



