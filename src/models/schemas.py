from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context_depth: int = 2


class ChatResponse(BaseModel):
    response: str
    session_id: str
    tools_used: List[str] = []
    emotional_adaptation: Optional[str] = None


class PackageSearchResult(BaseModel):
    name: str
    version: str
    source: str
    description: str


class PackageInstallRequest(BaseModel):
    package: str
    auto: bool = False
    context: Optional[str] = None


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
    completed_at: Optional[datetime] = None
    exit_code: Optional[int] = None


class ActionCreateRequest(BaseModel):
    binary: str
    safety: int = 2
    auto_index: bool = True


class ActionTreeNode(BaseModel):
    command: str
    description: str
    safety: int
    subcommands: Optional[Dict[str, Any]] = None
