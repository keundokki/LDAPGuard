import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.core.config import settings
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

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Multi-container Podman app for centralized LDAP backup/restore",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info(f"Shutting down {settings.APP_NAME}")
