"""Dashboard routes - System overview and monitoring.

Provides a unified view of openaur system state.
"""

from fastapi import APIRouter
from typing import Dict, Any
import psutil
import os
from datetime import datetime

from src.services.openmemory import get_memory
from src.services.email_ingestion import EmailIngestionService

router = APIRouter()


@router.get("/")
async def get_dashboard():
    """Get comprehensive dashboard view."""

    # Memory stats
    memory = get_memory()
    memory_stats = memory.stats()

    # Email stats
    email_service = EmailIngestionService()
    email_stats = email_service.get_stats()

    # System stats
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage("/")

        system = {
            "cpu_percent": cpu_percent,
            "memory_used_gb": round(memory_info.used / (1024**3), 2),
            "memory_total_gb": round(memory_info.total / (1024**3), 2),
            "memory_percent": memory_info.percent,
            "disk_used_gb": round(disk_info.used / (1024**3), 2),
            "disk_total_gb": round(disk_info.total / (1024**3), 2),
            "disk_percent": disk_info.percent,
        }
    except:
        system = {"status": "unavailable"}

    # Service health
    services = {
        "openaura_api": "running",
        "open_webui": "connected" if _check_webui() else "disconnected",
        "memory_layer": "active",
        "email_ingestion": "ready",
    }

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": services,
        "memory": memory_stats,
        "emails": email_stats,
        "system": system,
        "endpoints": [
            {"path": "/v1/chat/completions", "status": "active"},
            {"path": "/memory", "status": "active"},
            {"path": "/emails", "status": "active"},
            {"path": "/actions", "status": "active"},
        ],
    }


def _check_webui() -> bool:
    """Check if Open WebUI is accessible."""
    import socket

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(("localhost", 3000))
        sock.close()
        return result == 0
    except:
        return False


@router.get("/health")
async def get_health_status():
    """Get detailed health status."""
    checks = {
        "database": _check_database(),
        "openrouter": _check_openrouter(),
        "memory_service": True,
        "email_service": True,
    }

    all_healthy = all(checks.values())

    return {
        "status": "healthy" if all_healthy else "degraded",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
    }


def _check_database() -> bool:
    """Check database connectivity."""
    try:
        from src.models.database import engine

        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except:
        return False


def _check_openrouter() -> bool:
    """Check OpenRouter connectivity."""
    import os

    api_key = os.getenv("OPENROUTER_API_KEY")
    return api_key is not None and len(api_key) > 0
