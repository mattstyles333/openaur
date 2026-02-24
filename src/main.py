from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.routes import (
    chat,
    packages,
    sessions,
    actions,
    heart,
    ingest,
    openai,
    memory,
    memory_ui,
    emails,
    dashboard,
    agents,
)
from src.models.database import init_db
from src.services.gateway import OpenRouterGateway
from src.services.package_manager import PackageManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    await init_db()
    app.state.gateway = OpenRouterGateway()
    app.state.package_manager = PackageManager()
    print("🚀 openaur initialized")
    yield
    # Shutdown
    print("👋 openaur shutting down")


app = FastAPI(
    title="openaur",
    description="Personal AI Assistant with Arch Linux Action Registry",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(packages.router, prefix="/packages", tags=["packages"])
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
app.include_router(actions.router, prefix="/actions", tags=["actions"])
app.include_router(memory.router, prefix="/memory", tags=["memory"])
app.include_router(memory_ui.router, prefix="/memory", tags=["memory"])
app.include_router(emails.router, prefix="/emails", tags=["emails"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(agents.router, prefix="/agents", tags=["agents"])
app.include_router(heart.router, prefix="/heart", tags=["heart"])
app.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
app.include_router(openai.router, prefix="/v1", tags=["openai"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "openaura",
        "message": "Use /heart for combined health + empathy",
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to openaur",
        "version": "1.0.0",
        "endpoints": [
            "/v1/chat/completions - OpenAI-compatible API",
            "/v1/models - OpenAI-compatible models",
            "/heart - The Heart (health + empathy)",
            "/chat - Chat interface",
            "/ingest - Ingest data (actions, memories)",
            "/packages - Package management",
            "/sessions - Tmux session management",
            "/actions - Action registry",
            "/memory - OpenMemory API",
            "/memory/ui - OpenMemory Browser UI",
            "/emails - Email ingestion and search",
            "/dashboard - System overview",
            "/agents - Sub-agent management",
            "/health - Health check",
        ],
        "ui": "Open WebUI available at http://localhost:3000",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
