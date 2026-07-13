"""Security and authentication middleware for the API."""
import os
from fastapi import Security, HTTPException, Request
from fastapi.security import APIKeyHeader

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def get_api_key(
    api_key_header_val: str = Security(api_key_header),
    request: Request = None
) -> str:
    """
    Validates API key from either X-API-Key header or '?key=' query parameter.
    """
    expected_api_key = os.getenv("AGRICARE_API_KEY", "agricare_test_key_123")
    
    query_key = request.query_params.get("key") if request else None
    if query_key == expected_api_key:
        return query_key
    if api_key_header_val == expected_api_key:
        return api_key_header_val
        
    raise HTTPException(
        status_code=403,
        detail="Could not validate credentials. Please provide a valid API key via 'X-API-Key' header or '?key=' query parameter."
    )
