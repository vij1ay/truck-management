from uuid import UUID

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.security import decode_token


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract tenant context from JWT token.
    
    Stores tenant_id and user_id in request.state for downstream access.
    """
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ):
        # Initialize state
        request.state.user_id = None
        request.state.tenant_id = None
        request.state.role = None
        
        # Try to extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            try:
                # Verified decode: forged or expired tokens leave the context empty
                payload = decode_token(token)
                
                if payload.get("sub"):
                    request.state.user_id = UUID(payload["sub"])
                
                if payload.get("tenant_id"):
                    request.state.tenant_id = UUID(payload["tenant_id"])
                
                request.state.role = payload.get("role")
            except Exception:
                # Silently fail - authentication will be handled by dependencies
                pass
        
        response = await call_next(request)
        return response


def get_request_context(request: Request) -> dict:
    """Get the current request context from state."""
    return {
        "user_id": getattr(request.state, "user_id", None),
        "tenant_id": getattr(request.state, "tenant_id", None),
        "role": getattr(request.state, "role", None),
        "ip_address": get_client_ip(request),
        "user_agent": request.headers.get("User-Agent"),
    }


def get_client_ip(request: Request) -> str | None:
    """Extract the client IP address from the request."""
    # Check for forwarded headers (behind proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to direct client
    if request.client:
        return request.client.host
    
    return None
