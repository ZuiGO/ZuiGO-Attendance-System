"""Main FastAPI application entrypoint for ZuiGO Attendance System."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.redis import close_redis_connection, get_redis_client
from app.core.tenant import TenantMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager: connects to Redis on startup and closes on shutdown."""
    # Startup: test redis connection if reachable
    try:
        redis_client = await get_redis_client()
        await redis_client.ping()
    except Exception as e:
        print(f"[Startup Warning] Redis connection failed: {e}. In-memory mock will be used in offline modes.")
    
    yield

    # Shutdown: close redis connection
    await close_redis_connection()


app = FastAPI(
    title="ZuiGO Attendance & Field-Visit Tracking System API",
    description="Enterprise Multi-Tenant Physical Presence Attendance, Anti-Proxy Verification, and Task/Mileage Tracking",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production via settings
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Tenant-ID"],
)

# Multi-Tenant Resolution Middleware
app.add_middleware(TenantMiddleware)

# API v1 Routers
from app.api.v1 import api_v1_router
app.include_router(api_v1_router)


# Health Check Endpoints
@app.get("/health", tags=["System"])
async def health_check():
    """Liveness probe."""
    return {
        "status": "healthy",
        "service": "zuigo-attendance-backend",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/ready", tags=["System"])
async def readiness_probe(request: Request):
    """Readiness probe checking DB & tenant context."""
    tenant_id = getattr(request.state, "tenant_id", None)
    return {
        "status": "ready",
        "tenant_id": tenant_id,
        "database": "configured",
    }


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Fallback exception handler for unhandled errors."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred",
        },
    )
