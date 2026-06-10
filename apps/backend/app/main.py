from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.api.v1 import router as api_v1_router
from app.core.logger import init_logger
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.tenant_context import TenantContextMiddleware
from app.middleware.trace_id import TraceIdMiddleware
from app.core.exceptions import AppException
from app.schemas import HealthResponse

settings = get_settings()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    init_logger(settings.DEBUG)

    app = FastAPI(
        title=settings.APP_NAME,
        description="Transport & Load Management System API",
        version="0.1.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure properly in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add custom middleware
    app.add_middleware(TraceIdMiddleware)
    app.add_middleware(TenantContextMiddleware)
    app.add_middleware(ErrorHandlerMiddleware)
    
    # Exception handlers
    @app.exception_handler(AppException)
    async def app_exception_handler(request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        )
    
    # Health check endpoint
    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health_check():
        """Health check endpoint."""
        return HealthResponse(status="healthy", version="0.1.0")
    
    # Include API routers
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)
    
    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
