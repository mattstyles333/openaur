"""OpenMemory routes - Cognitive layer API using HMD2.

Provides endpoints for memory storage, retrieval, and management
using OpenMemory's Hierarchical Memory Decomposition architecture.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from src.services.openmemory import get_memory, OpenMemoryService

router = APIRouter()
memory_service: OpenMemoryService = get_memory()


class MemoryCreateRequest(BaseModel):
    content: str
    memory_type: str = "episodic"
    importance: float = 0.8
    tags: List[str] = []
    metadata: Dict[str, Any] = {}
    user_id: str = "default"


class MemoryQueryRequest(BaseModel):
    query: str
    memory_type: Optional[str] = None
    limit: int = 10
    min_importance: float = 0.0
    user_id: str = "default"


class ReinforceRequest(BaseModel):
    memory_id: str
    amount: float = 0.1


@router.post("/store")
async def store_memory(request: MemoryCreateRequest):
    """Store a new memory with automatic sector classification and chunking."""
    try:
        result = await memory_service.store(
            content=request.content,
            memory_type=request.memory_type,
            importance=request.importance,
            tags=request.tags,
            metadata=request.metadata,
            user_id=request.user_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retrieve")
async def retrieve_memories(request: MemoryQueryRequest):
    """Retrieve memories using composite scoring (similarity + salience + recency)."""
    try:
        memories = await memory_service.retrieve(
            query=request.query,
            memory_type=request.memory_type,
            limit=request.limit,
            min_salience=request.min_importance,
            user_id=request.user_id,
        )

        # Reinforce retrieved memories (boost salience on recall)
        for mem in memories[:3]:  # Top 3 matches
            if mem.get("id"):
                await memory_service.reinforce(mem["id"], 0.05)

        return {
            "count": len(memories),
            "memories": memories,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reinforce")
async def reinforce_memory(request: ReinforceRequest):
    """Reinforce a memory to boost its salience."""
    try:
        success = await memory_service.reinforce(request.memory_id, request.amount)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_memory_stats(user_id: str = "default"):
    """Get memory statistics by sector."""
    try:
        stats = await memory_service.stats(user_id=user_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sectors")
async def get_sectors():
    """List available memory sectors in HMD2."""
    return {
        "sectors": [
            {
                "name": "episodic",
                "description": "Events, conversations, interactions",
                "examples": ["User asked about weather", "Discussed project deadline"],
            },
            {
                "name": "semantic",
                "description": "Facts, knowledge, preferences",
                "examples": ["User prefers dark mode", "Python version 3.11"],
            },
            {
                "name": "procedural",
                "description": "How-to, actions, steps",
                "examples": ["Install package with yay", "Git commit workflow"],
            },
            {
                "name": "emotional",
                "description": "Feelings, sentiment, mood",
                "examples": ["User was frustrated", "Celebrated success"],
            },
            {
                "name": "reflective",
                "description": "Insights, summaries, learnings",
                "examples": ["Learned that user likes concise answers"],
            },
        ]
    }
