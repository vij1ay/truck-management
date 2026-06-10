from fastapi import Request

from app.core.logger import get_logger
from app.middleware.tenant_context import get_client_ip

logger = get_logger("app.api")


async def log_request(request: Request) -> None:
    """Log every API request with request context."""
    user_id = getattr(request.state, "user_id", None)
    tenant_id = getattr(request.state, "tenant_id", None)
    logger.info(
        f"{request.method} {request.url.path} | user_id={user_id} | tenant_id={tenant_id} | ip={get_client_ip(request)}"
    )
