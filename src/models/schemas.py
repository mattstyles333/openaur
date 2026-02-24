from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    context_depth: int = 2


class ChatResponse(BaseModel):
    response: str
    session_id: str
    tools_used: list[str] = []
    emotional_adaptation: str | None = None
    preview_used: bool = False  # True if Instant Preview (dual response) was used


class PackageSearchResult(BaseModel):
    name: str
    version: str
    source: str
    description: str


class PackageInstallRequest(BaseModel):
    package: str
    auto: bool = False
    context: str | None = None


class SessionCreateRequest(BaseModel):
    action_id: str
    command: str
    async_exec: bool = True


class SessionResponse(BaseModel):
    id: str
    tmux_session: str
    status: str
    command: str
    started_at: datetime
    completed_at: datetime | None = None
    exit_code: int | None = None


class ActionCreateRequest(BaseModel):
    binary: str
    safety: int = 2
    auto_index: bool = True


class ActionTreeNode(BaseModel):
    command: str
    description: str
    safety: int
    subcommands: dict[str, Any] | None = None
