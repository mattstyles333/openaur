"""OpenMemory routes - Cognitive layer API.

Provides endpoints for memory storage, retrieval, and management.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from src.services.openmemory import (
    get_memory,
    get_session_memory,
    OpenMemory,
    SessionMemory,
)

router = APIRouter()


class MemoryCreateRequest(BaseModel):
    content: str
    memory_type: str = "context"
    importance: float = 1.0
    tags: List[str] = []
    metadata: Dict[str, Any] = {}


class MemoryResponse(BaseModel):
    id: str
    content: str
    memory_type: str
    importance: float
    tags: List[str]
    created_at: str


class MemoryQueryRequest(BaseModel):
    query: str
    memory_type: Optional[str] = None
    limit: int = 10
    min_importance: float = 0.0


class ContextWindowRequest(BaseModel):
    session_id: str
    query: str
    window_size: int = 5


@router.post("/store")
async def store_memory(request: MemoryCreateRequest):
    """Store a new memory."""
    memory = get_memory().store(
        content=request.content,
        memory_type=request.memory_type,
        importance=request.importance,
        tags=request.tags,
        metadata=request.metadata,
    )

    return {
        "id": memory.id,
        "content": memory.content,
        "memory_type": memory.memory_type,
        "importance": memory.importance,
        "tags": memory.tags,
        "created_at": memory.created_at.isoformat(),
    }


@router.post("/retrieve")
async def retrieve_memories(request: MemoryQueryRequest):
    """Retrieve memories based on query."""
    memories = get_memory().retrieve(
        query=request.query,
        memory_type=request.memory_type,
        limit=request.limit,
        min_importance=request.min_importance,
    )

    # Filter out system memories (pre-loaded context) unless explicitly requested
    if request.memory_type != "system":
        memories = [m for m in memories if m.memory_type != "system"]

    return {
        "count": len(memories),
        "memories": [
            {
                "id": m.id,
                "content": m.content,
                "memory_type": m.memory_type,
                "importance": m.importance,
                "tags": m.tags,
                "created_at": m.created_at.isoformat(),
                "last_accessed": m.last_accessed.isoformat(),
                "access_count": m.access_count,
            }
            for m in memories
        ],
    }


@router.post("/context")
async def get_context_window(request: ContextWindowRequest):
    """Get context window for a session."""
    session_memory = get_session_memory(request.session_id)

    # Get enhanced context
    context = session_memory.get_enhanced_context(request.query)

    # Get relevant memories from global memory
    global_memories = get_memory().retrieve(request.query, limit=5)

    return {
        "session_id": request.session_id,
        "conversation_history": context["conversation_history"],
        "relevant_memories": context["relevant_memories"],
        "global_memories": [{"content": m.content, "type": m.memory_type} for m in global_memories],
    }


@router.post("/session/{session_id}/message")
async def add_session_message(
    session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None
):
    """Add a message to session memory."""
    session_memory = get_session_memory(session_id)
    session_memory.add_message(role, content, metadata)

    return {
        "session_id": session_id,
        "role": role,
        "stored": True,
        "conversation_length": len(session_memory.conversation_history),
    }


@router.get("/session/{session_id}/history")
async def get_session_history(session_id: str, last_n: int = 20):
    """Get conversation history for a session."""
    session_memory = get_session_memory(session_id)

    history = session_memory.conversation_history[-last_n:]

    return {
        "session_id": session_id,
        "message_count": len(session_memory.conversation_history),
        "history": history,
    }


@router.get("/stats")
async def get_memory_stats():
    """Get memory statistics."""
    stats = get_memory().stats()
    return stats


@router.post("/clear")
async def clear_memories(memory_type: Optional[str] = None):
    """Clear memories, optionally by type."""
    get_memory().clear(memory_type)

    return {"cleared": True, "memory_type": memory_type or "all"}


@router.post("/decay")
async def decay_memories():
    """Trigger importance decay for all memories."""
    get_memory().decay_importance()

    return {"decayed": True, "message": "Memory importance values decayed"}
