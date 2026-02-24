"""OpenMemory service - Cognitive layer for openaur.

Provides memory storage and retrieval with embeddings for contextual awareness.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import hashlib
from sqlalchemy.orm import Session

from src.models.database import get_db, ExecutionContext, Session as SessionModel


class Memory:
    """Individual memory unit."""

    def __init__(
        self,
        content: str,
        memory_type: str = "context",
        importance: float = 1.0,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None,
    ):
        self.id = hashlib.sha256(content.encode()).hexdigest()[:16]
        self.content = content
        self.memory_type = memory_type
        self.importance = importance
        self.tags = tags or []
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.last_accessed = datetime.utcnow()
        self.access_count = 0


class OpenMemory:
    """Cognitive memory layer for openaur.

    Manages short-term and long-term memory with retrieval capabilities.
    """

    def __init__(self):
        self.short_term: List[Memory] = []
        self.max_short_term = 30  # Working memory - active context
        self.decay_rate = 0.95  # Importance decay per hour

    def store(
        self,
        content: str,
        memory_type: str = "context",
        importance: float = 1.0,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None,
    ) -> Memory:
        """Store a new memory."""
        memory = Memory(
            content=content,
            memory_type=memory_type,
            importance=importance,
            tags=tags or [],
            metadata=metadata or {},
        )

        self.short_term.append(memory)

        # Prune short-term memory if too large
        if len(self.short_term) > self.max_short_term:
            self._prune_short_term()

        return memory

    def retrieve(
        self,
        query: str,
        memory_type: Optional[str] = None,
        limit: int = 10,
        min_importance: float = 0.0,
    ) -> List[Memory]:
        """Retrieve relevant memories."""
        # Handle wildcard - return all recent memories
        if query == "*":
            results = sorted(self.short_term, key=lambda m: m.last_accessed, reverse=True)[:limit]
            for memory in results:
                memory.last_accessed = datetime.utcnow()
                memory.access_count += 1
            return results

        # Simple keyword-based retrieval (can be enhanced with embeddings)
        query_terms = set(query.lower().split())

        scored_memories = []
        for memory in self.short_term:
            if memory_type and memory.memory_type != memory_type:
                continue

            if memory.importance < min_importance:
                continue

            # Calculate relevance score
            memory_terms = set(memory.content.lower().split())
            tag_terms = set(t.lower() for t in memory.tags)

            overlap = len(query_terms & memory_terms)
            tag_overlap = len(query_terms & tag_terms)

            score = overlap + (tag_overlap * 2)  # Tags weighted more
            score *= memory.importance
            score *= 0.5 + (memory.access_count / 10)  # Boost frequently accessed

            if score > 0:
                scored_memories.append((score, memory))

        # Sort by score descending
        scored_memories.sort(key=lambda x: x[0], reverse=True)

        # Update access metrics
        results = []
        for score, memory in scored_memories[:limit]:
            memory.last_accessed = datetime.utcnow()
            memory.access_count += 1
            results.append(memory)

        return results

    def get_context_window(self, current_query: str, window_size: int = 5) -> List[Memory]:
        """Get recent context for the current conversation."""
        # Get most recent memories plus relevant ones
        recent = sorted(self.short_term, key=lambda m: m.last_accessed, reverse=True)[:window_size]

        # Get relevant memories
        relevant = self.retrieve(current_query, limit=window_size)

        # Combine and deduplicate
        seen = set()
        combined = []

        for memory in recent + relevant:
            if memory.id not in seen:
                seen.add(memory.id)
                combined.append(memory)

        return combined[:window_size]

    def summarize_context(self, memories: List[Memory]) -> str:
        """Summarize memories into context string."""
        if not memories:
            return ""

        parts = []
        for mem in memories:
            prefix = f"[{mem.memory_type.upper()}] "
            parts.append(f"{prefix}{mem.content}")

        return "\n".join(parts)

    def _prune_short_term(self):
        """Remove least important memories from short-term storage."""
        # Sort by importance and recency
        now = datetime.utcnow()

        def score_memory(memory):
            age_hours = (now - memory.created_at).total_seconds() / 3600
            decayed_importance = memory.importance * (self.decay_rate**age_hours)
            return decayed_importance * (1 + memory.access_count * 0.1)

        self.short_term.sort(key=score_memory, reverse=True)
        self.short_term = self.short_term[: self.max_short_term]

    def decay_importance(self):
        """Decay importance of all memories over time."""
        now = datetime.utcnow()
        for memory in self.short_term:
            age_hours = (now - memory.created_at).total_seconds() / 3600
            memory.importance *= self.decay_rate**age_hours

    def clear(self, memory_type: Optional[str] = None):
        """Clear memories, optionally by type."""
        if memory_type:
            self.short_term = [m for m in self.short_term if m.memory_type != memory_type]
        else:
            self.short_term = []

    def stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        types = {}
        for memory in self.short_term:
            types[memory.memory_type] = types.get(memory.memory_type, 0) + 1

        # Count long-term memories from database
        long_term_count = 0
        try:
            db = next(get_db())
            long_term_count = db.query(ExecutionContext).count()
        except Exception:
            pass

        return {
            "total_memories": len(self.short_term) + long_term_count,
            "short_term": len(self.short_term),
            "short_term_max": self.max_short_term,
            "long_term": long_term_count,
            "by_type": types,
            "max_capacity": self.max_short_term,
            "utilization": len(self.short_term) / self.max_short_term,
        }


class SessionMemory:
    """Session-specific memory management."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.memory = OpenMemory()
        self.conversation_history: List[Dict[str, Any]] = []
        self.max_history = 100

    def add_message(self, role: str, content: str, metadata: Dict = None):
        """Add a message to conversation history."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }
        self.conversation_history.append(message)

        # Prune old messages
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history :]

        # Store important messages as memories
        if role == "user":
            self.memory.store(content=content, memory_type="user_query", tags=["conversation"])
        elif role == "assistant":
            self.memory.store(
                content=content, memory_type="assistant_response", tags=["conversation"]
            )

    def get_conversation_context(self, last_n: int = 10) -> str:
        """Get recent conversation as context."""
        recent = self.conversation_history[-last_n:]
        lines = []
        for msg in recent:
            role = msg["role"]
            content = msg["content"][:200]  # Truncate long messages
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def get_enhanced_context(self, current_query: str) -> Dict[str, Any]:
        """Get enhanced context for LLM calls."""
        # Get conversation history
        conversation = self.get_conversation_context()

        # Get relevant memories
        relevant_memories = self.memory.retrieve(current_query, limit=5)
        memory_context = self.memory.summarize_context(relevant_memories)

        return {
            "conversation_history": conversation,
            "relevant_memories": memory_context,
            "session_id": self.session_id,
        }


# Global memory instance
_global_memory = None


def get_memory() -> OpenMemory:
    """Get global memory instance."""
    global _global_memory
    if _global_memory is None:
        _global_memory = OpenMemory()
    return _global_memory


def get_session_memory(session_id: str) -> SessionMemory:
    """Get or create session memory."""
    # TODO: Cache session memories
    return SessionMemory(session_id)
