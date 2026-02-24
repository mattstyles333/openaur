"""OpenMemory service - Cognitive layer for openaur.

Simplified SQLite-only storage for memories.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Integer, Text, JSON
from src.models.database import Base, get_db

# Singleton instance
_memory_instance = None


class Memory(Base):
    """Memory model - stored in SQLite."""

    __tablename__ = "memories"

    id = Column(String, primary_key=True)
    content = Column(Text, nullable=False)
    memory_type = Column(String, default="context")
    importance = Column(Float, default=1.0)
    tags = Column(JSON, default=list)
    meta = Column(JSON, default=dict)  # Renamed from 'metadata' (reserved)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)
    access_count = Column(Integer, default=0)


class OpenMemory:
    """Simplified cognitive memory layer - just SQLite."""

    def __init__(self):
        # Ensure table exists
        from src.models.database import engine

        Base.metadata.create_all(engine, tables=[Memory.__table__])

    def store(
        self,
        content: str,
        memory_type: str = "context",
        importance: float = 1.0,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None,
    ) -> Memory:
        """Store a new memory in SQLite."""
        import hashlib

        memory_id = hashlib.sha256(content.encode()).hexdigest()[:16]

        memory = Memory(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            importance=importance,
            tags=tags or [],
            meta=metadata or {},
        )

        db = next(get_db())
        db.add(memory)
        db.commit()

        return memory

    def retrieve(
        self,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 10,
        min_importance: float = 0.0,
    ) -> List[Memory]:
        """Retrieve relevant memories from SQLite."""
        db = next(get_db())

        # Base query
        q = db.query(Memory).filter(Memory.importance >= min_importance)

        # Filter by type if specified
        if memory_type:
            q = q.filter(Memory.memory_type == memory_type)

        # Handle wildcard - return most recent
        if query == "*":
            results = q.order_by(Memory.last_accessed.desc()).limit(limit).all()
        else:
            # Simple keyword search
            query_lower = f"%{query.lower()}%"
            results = (
                q.filter(
                    (Memory.content.ilike(query_lower))
                    | (Memory.tags.cast(String).ilike(query_lower))
                )
                .order_by(Memory.importance.desc())
                .limit(limit)
                .all()
            )

        # Update access metrics
        for memory in results:
            memory.last_accessed = datetime.utcnow()
            memory.access_count += 1

        db.commit()

        return results

    def stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        db = next(get_db())

        # Count by type
        all_memories = db.query(Memory).all()
        types = {}
        for m in all_memories:
            types[m.memory_type] = types.get(m.memory_type, 0) + 1

        # Hide system from main counts
        user_count = sum(1 for m in all_memories if m.memory_type != "system")

        return {
            "total_memories": user_count,
            "by_type": {k: v for k, v in types.items() if k != "system"},
            "max_capacity": 10000,  # SQLite can handle 10k+ easily
            "utilization": user_count / 10000 if user_count else 0,
            "system_memories": types.get("system", 0),
        }

    def clear(self, memory_type: Optional[str] = None):
        """Clear memories."""
        db = next(get_db())
        if memory_type:
            db.query(Memory).filter(Memory.memory_type == memory_type).delete()
        else:
            db.query(Memory).delete()
        db.commit()


# Backwards compatibility


def get_memory() -> OpenMemory:
    """Get singleton OpenMemory instance."""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = OpenMemory()
    return _memory_instance


class SessionMemory:
    """Session-specific memory management (simplified)."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.memory = get_memory()
        self.conversation_history: List[Dict[str, Any]] = []

    def add_message(self, role: str, content: str, metadata: Dict = None):
        """Add a message to conversation history."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }
        self.conversation_history.append(message)

    def get_enhanced_context(self, query: str) -> Dict[str, Any]:
        """Get enhanced context for a query."""
        relevant = self.memory.retrieve(query, limit=5)

        return {
            "recent_history": self.conversation_history[-5:],
            "relevant_memories": [
                {
                    "content": m.content,
                    "type": m.memory_type,
                    "importance": m.importance,
                }
                for m in relevant
            ],
        }


# Session memory cache
_session_memories: Dict[str, SessionMemory] = {}


def get_session_memory(session_id: str) -> SessionMemory:
    """Get or create session memory."""
    if session_id not in _session_memories:
        _session_memories[session_id] = SessionMemory(session_id)
    return _session_memories[session_id]
