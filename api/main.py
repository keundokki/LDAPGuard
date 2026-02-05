import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from api.core.config import settings
from api.core.redis import close_redis_client, get_redis_client
from api.routes import (
    api_keys,
    audit_logs,
    auth,
    backups,
    config,
    ldap_servers,
    restores,
    scheduled_backups,
    settings as settings_routes,
)
from api.services.metrics_service import MetricsService

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Create rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Multi-container Podman app for centralized LDAP backup/restore",
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.on_event("startup")
async def validate_configuration():
    """Validate critical configuration on startup."""
    errors = []

    # Check for default/insecure secrets
    if settings.SECRET_KEY == "your-secret-key-change-in-production":
        errors.append(
            "SECRET_KEY is using default value - must be changed in production"
        )

    if len(settings.SECRET_KEY) < 32:
        errors.append("SECRET_KEY must be at least 32 characters long")

    if settings.ENCRYPTION_KEY == "your-encryption-key-32-bytes-min":
        errors.append(
            "ENCRYPTION_KEY is using default value - must be changed in production"
        )

    if len(settings.ENCRYPTION_KEY) < 32:
        errors.append("ENCRYPTION_KEY must be at least 32 bytes long")

    if errors:
        logger.error("Configuration validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        if not settings.DEBUG:
            logger.error("Shutting down due to configuration errors")
            sys.exit(1)
        else:
            logger.warning("Running in DEBUG mode with insecure configuration")


# CORS middleware
if settings.CORS_ALLOWED_ORIGINS:
    # Use configured origins if provided
    allowed_origins = settings.CORS_ALLOWED_ORIGINS.split(",")
elif settings.DEBUG:
    # Allow all in debug mode
    allowed_origins = ["*"]
else:
    # Default production origins (localhost for testing)
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Content-Type", "Authorization"],
)

# Include routers
app.include_router(auth.router)
app.include_router(ldap_servers.router)
app.include_router(backups.router)
app.include_router(restores.router)
app.include_router(scheduled_backups.router)
app.include_router(audit_logs.router)
app.include_router(api_keys.router)
app.include_router(settings_routes.router)
app.include_router(config.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    if settings.PROMETHEUS_ENABLED:
        return MetricsService.get_metrics()
    return {"error": "Metrics disabled"}


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # Initialize Redis connection
    try:
        await get_redis_client()
        logger.info("Redis client initialized")
    except Exception as e:
        logger.warning(f"Redis client initialization failed: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info(f"Shutting down {settings.APP_NAME}")

    # Close Redis connection
    await close_redis_client()
