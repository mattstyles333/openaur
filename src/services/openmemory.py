"""OpenMemory integration with HMD2 architecture.

Tries to use openmemory-py SDK, falls back to SQLite if not available.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import hashlib

# Try to import OpenMemory SDK
try:
    from openmemory.client import Memory as OpenMemoryClient

    HAS_OPENMEMORY = True
except ImportError:
    HAS_OPENMEMORY = False
    print("⚠️  OpenMemory SDK not available, using SQLite fallback")

from sqlalchemy import Column, String, Float, DateTime, Integer, Text, JSON
from src.models.database import Base, get_db


# Memory model for SQLite fallback
class Memory(Base):
    """Memory model - stored in SQLite."""

    __tablename__ = "memories"

    id = Column(String, primary_key=True)
    content = Column(Text, nullable=False)
    memory_type = Column(String, default="episodic")
    importance = Column(Float, default=0.8)
    tags = Column(JSON, default=list)
    meta = Column(JSON, default=dict)  # Renamed from 'metadata' (reserved)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    access_count = Column(Integer, default=0)


class OpenMemoryService:
    """Service that uses OpenMemory SDK when available, SQLite as fallback."""

    def __init__(self):
        self.use_sdk = HAS_OPENMEMORY
        self.client = None

        if self.use_sdk:
            try:
                data_dir = "/home/aura/app/data"
                os.makedirs(data_dir, exist_ok=True)
                self.client = OpenMemoryClient(
                    storage_uri=f"sqlite:///{data_dir}/openmemory.db",
                )
            except Exception as e:
                print(f"⚠️  OpenMemory client init failed: {e}")
                self.use_sdk = False

        if not self.use_sdk:
            # Ensure SQLite table exists
            from src.models.database import engine

            Base.metadata.create_all(engine, tables=[Memory.__table__])

    async def store(
        self,
        content: str,
        memory_type: str = "episodic",
        importance: float = 0.8,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None,
        user_id: str = "default",
    ) -> Dict[str, Any]:
        """Store a memory."""
        if self.use_sdk and self.client:
            try:
                result = await self.client.add(
                    content=content,
                    user_id=user_id,
                    salience=importance,
                    metadata={
                        **(metadata or {}),
                        "memory_type": memory_type,
                        "tags": tags or [],
                    },
                )
                return {
                    "id": result.get("id"),
                    "sector": result.get("primary_sector", "episodic"),
                    "salience": importance,
                }
            except Exception as e:
                print(f"OpenMemory store failed: {e}, falling back to SQLite")

        # SQLite fallback
        memory_id = hashlib.sha256(content.encode()).hexdigest()[:16]

        memory = Memory(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            importance=importance,
            tags=tags or [],
            meta={**(metadata or {}), "user_id": user_id},
        )

        db = next(get_db())
        db.add(memory)
        db.commit()

        return {
            "id": memory_id,
            "sector": memory_type,
            "salience": importance,
        }

    async def retrieve(
        self,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 10,
        min_salience: float = 0.0,
        user_id: str = "default",
    ) -> List[Dict[str, Any]]:
        """Retrieve memories."""
        if self.use_sdk and self.client:
            try:
                results = await self.client.search(
                    query=query,
                    user_id=user_id,
                    limit=limit,
                    min_salience=min_salience,
                )

                matches = results.get("matches", [])

                # Reinforce top matches
                for m in matches[:3]:
                    if m.get("id"):
                        try:
                            await self.client.reinforce(m["id"], 0.05)
                        except:
                            pass

                return [
                    {
                        "id": m.get("id"),
                        "content": m.get("content"),
                        "memory_type": m.get("metadata", {}).get("memory_type", "episodic"),
                        "salience": m.get("salience", 0.5),
                        "score": m.get("score", 0.0),
                        "sector": m.get("primary_sector"),
                        "tags": m.get("metadata", {}).get("tags", []),
                    }
                    for m in matches
                ]
            except Exception as e:
                print(f"OpenMemory retrieve failed: {e}, falling back to SQLite")

        # SQLite fallback
        db = next(get_db())

        q = db.query(Memory).filter(Memory.importance >= min_salience)

        if memory_type:
            q = q.filter(Memory.memory_type == memory_type)

        if query == "*":
            results = q.order_by(Memory.last_accessed.desc()).limit(limit).all()
        else:
            query_lower = f"%{query.lower()}%"
            results = (
                q.filter(Memory.content.ilike(query_lower))
                .order_by(Memory.importance.desc())
                .limit(limit)
                .all()
            )

        # Update access metrics
        for memory in results:
            memory.last_accessed = datetime.utcnow()
            memory.access_count += 1

        db.commit()

        return [
            {
                "id": m.id,
                "content": m.content,
                "memory_type": m.memory_type,
                "salience": m.importance,
                "score": m.importance,
                "sector": m.memory_type,
                "tags": m.tags,
            }
            for m in results
        ]

    async def reinforce(self, memory_id: str, amount: float = 0.1) -> bool:
        """Reinforce a memory."""
        if self.use_sdk and self.client:
            try:
                await self.client.reinforce(memory_id, amount)
                return True
            except:
                pass
        return False

    async def stats(self, user_id: str = "default") -> Dict[str, Any]:
        """Get memory statistics."""
        if self.use_sdk and self.client:
            try:
                all_memories = await self.client.all(user_id=user_id, limit=1000)
                memories = all_memories.get("memories", [])

                by_sector = {}
                user_count = 0

                for m in memories:
                    sector = m.get("primary_sector", "unknown")
                    by_sector[sector] = by_sector.get(sector, 0) + 1

                    mem_type = m.get("metadata", {}).get("memory_type", "")
                    if mem_type != "system":
                        user_count += 1

                return {
                    "total_memories": user_count,
                    "by_sector": by_sector,
                    "by_type": {
                        "user_query": by_sector.get("episodic", 0),
                        "assistant_response": by_sector.get("episodic", 0),
                        "action_learning": by_sector.get("procedural", 0),
                    },
                    "max_capacity": 10000,
                    "utilization": min(user_count / 10000, 1.0),
                    "system_memories": by_sector.get("semantic", 0),
                    "backend": "openmemory",
                }
            except Exception as e:
                print(f"OpenMemory stats failed: {e}")

        # SQLite fallback
        db = next(get_db())
        all_memories = db.query(Memory).all()

        types = {}
        for m in all_memories:
            types[m.memory_type] = types.get(m.memory_type, 0) + 1

        user_count = sum(1 for m in all_memories if m.memory_type != "system")

        return {
            "total_memories": user_count,
            "by_type": {k: v for k, v in types.items() if k != "system"},
            "max_capacity": 10000,
            "utilization": min(user_count / 10000, 1.0),
            "system_memories": types.get("system", 0),
            "backend": "sqlite",
        }


# Singleton
_service_instance: Optional[OpenMemoryService] = None


def get_memory() -> OpenMemoryService:
    """Get singleton memory service."""
    global _service_instance
    if _service_instance is None:
        _service_instance = OpenMemoryService()
    return _service_instance


class SessionMemory:
    """Session-specific memory wrapper."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.memory = get_memory()
        self.conversation_history: List[Dict[str, Any]] = []

    async def add_message(self, role: str, content: str, metadata: Dict = None):
        """Add a message to session history and memory."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }
        self.conversation_history.append(message)

        if role in ["user", "assistant"] and len(content) > 20:
            mem_type = "user_query" if role == "user" else "assistant_response"
            await self.memory.store(
                content=content,
                memory_type=mem_type,
                user_id=self.session_id,
            )

    async def get_enhanced_context(self, query: str) -> Dict[str, Any]:
        """Get enhanced context."""
        relevant = await self.memory.retrieve(query, user_id=self.session_id, limit=5)

        return {
            "recent_history": self.conversation_history[-5:],
            "relevant_memories": relevant,
        }


_session_memories: Dict[str, SessionMemory] = {}


def get_session_memory(session_id: str) -> SessionMemory:
    """Get or create session memory."""
    if session_id not in _session_memories:
        _session_memories[session_id] = SessionMemory(session_id)
    return _session_memories[session_id]
