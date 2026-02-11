from __future__ import annotations

import logging
from typing import Optional

from fastapi import Request
from api.core.database import AsyncSessionLocal
from api.core.security import decode_access_token
from api.models.models import AuditLog

logger = logging.getLogger(__name__)

AUDIT_SKIP_PATHS = {"/health", "/metrics", "/version"}
AUDIT_SKIP_PREFIXES = ("/docs", "/openapi.json", "/redoc", "/static")


def _resolve_action(method: str, path: str) -> Optional[str]:
    if path.startswith("/auth/login"):
        return "login"
    if method == "POST" and "delete" in path:
        return "delete"
    return {
        "POST": "create",
        "PUT": "update",
        "PATCH": "update",
        "DELETE": "delete",
    }.get(method)


def _resolve_resource(path: str) -> Optional[str]:
    parts = [part for part in path.strip("/").split("/") if part]
    return parts[0] if parts else None


def _resolve_resource_id(path: str) -> Optional[int]:
    parts = [part for part in path.strip("/").split("/") if part]
    if not parts:
        return None
    last = parts[-1]
    return int(last) if last.isdigit() else None


async def audit_middleware(request: Request, call_next):
    response = await call_next(request)

    path = request.url.path
    if (
        request.method in ("GET", "HEAD", "OPTIONS")
        or response.status_code >= 400
        or path in AUDIT_SKIP_PATHS
        or path.startswith(AUDIT_SKIP_PREFIXES)
        or path.startswith("/audit-logs")
    ):
        return response

    action = _resolve_action(request.method, path)
    if not action:
        return response

    auth_header = request.headers.get("authorization", "")
    if not auth_header.lower().startswith("bearer "):
        return response

    token = auth_header.split(" ", 1)[1].strip()
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return response

    username = payload.get("sub")
    role = payload.get("role")

    try:
        async with AsyncSessionLocal() as db:
            log = AuditLog(
                user_id=None,
                action=action,
                resource_type=_resolve_resource(path),
                resource_id=_resolve_resource_id(path),
                details=f"{request.method} {path} by {username} ({role})",
                ip_address=request.client.host if request.client else None,
            )
            db.add(log)
            await db.commit()
    except Exception as exc:
        logger.warning("Audit log write failed: %s", exc)

    return response
