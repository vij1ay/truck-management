from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.logger import get_logger, reset_trace_id, set_trace_id

TRACE_ID_HEADER = "X-Request-ID"
CORRELATION_HEADER = "X-Correlation-ID"

logger = get_logger(__name__)


class TraceIdMiddleware(BaseHTTPMiddleware):
    """Attach a per-request trace ID and propagate it via contextvars and headers."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        incoming_trace_id = (
            request.headers.get(TRACE_ID_HEADER)
            or request.headers.get(CORRELATION_HEADER)
        )
        trace_id = incoming_trace_id or uuid4().hex

        token = set_trace_id(trace_id)
        request.state.trace_id = trace_id

        response = None
        try:
            response = await call_next(request)
            return response
        finally:
            if response is not None:
                response.headers.setdefault(TRACE_ID_HEADER, trace_id)
            reset_trace_id(token)
