from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.exceptions import AppException
from app.core.logger import get_logger

logger = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware."""
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ):
        try:
            response = await call_next(request)
            return response
        except AppException as e:
            logger.warning(
                "Handled application exception",
                extra={"path": request.url.path, "status_code": e.status_code},
            )
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error_code": e.error_code,
                    "message": e.message,
                    "details": e.details
                }
            )
        except Exception as e:
            logger.exception(
                "Unhandled exception during request",
                extra={"path": request.url.path},
            )
            return JSONResponse(
                status_code=500,
                content={
                    "error_code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {}
                }
            )
