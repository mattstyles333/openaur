"""WebSocket manager for real-time dashboard updates.

Replaces polling with WebSocket push notifications for:
- Memory updates
- Heart status changes
- Agent status changes
- Session updates
"""

from datetime import datetime

from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections and broadcasts updates."""

    def __init__(self):
        # Active connections by type
        self.connections: dict[str, set[WebSocket]] = {
            "memory": set(),
            "heart": set(),
            "agents": set(),
            "sessions": set(),
            "all": set(),  # Subscribe to everything
        }

    async def connect(self, websocket: WebSocket, subscription: str = "all"):
        """Accept new WebSocket connection."""
        await websocket.accept()

        # Subscribe to requested channels
        if subscription in self.connections:
            self.connections[subscription].add(websocket)

        # Always add to 'all' for general messages
        self.connections["all"].add(websocket)

        # Send welcome message
        await websocket.send_json(
            {
                "type": "connected",
                "timestamp": datetime.utcnow().isoformat(),
                "subscription": subscription,
                "message": "WebSocket connected to OpenAur real-time updates",
            }
        )

    def disconnect(self, websocket: WebSocket):
        """Remove disconnected WebSocket."""
        for channel in self.connections.values():
            channel.discard(websocket)

    async def broadcast(self, channel: str, data: dict):
        """Broadcast message to all connections in a channel."""
        if channel not in self.connections:
            return

        message = {
            "type": "update",
            "channel": channel,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
        }

        # Get connections to broadcast to
        targets = self.connections[channel].copy()
        # Also send to 'all' subscribers
        targets.update(self.connections["all"])

        # Send to all targets
        disconnected = []
        for websocket in targets:
            try:
                await websocket.send_json(message)
            except Exception:
                # Mark for removal if send fails
                disconnected.append(websocket)

        # Clean up disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket)

    async def send_personal(self, websocket: WebSocket, data: dict):
        """Send message to specific client."""
        try:
            await websocket.send_json(
                {"type": "personal", "timestamp": datetime.utcnow().isoformat(), "data": data}
            )
        except Exception:
            self.disconnect(websocket)


# Global connection manager instance
manager = ConnectionManager()


# Helper functions for broadcasting updates from services


async def broadcast_memory_update(stats: dict, memories: list):
    """Broadcast memory update to all connected clients."""
    await manager.broadcast(
        "memory",
        {
            "stats": stats,
            "memories": memories[:5],  # Only send recent 5
            "action": "memory_updated",
        },
    )


async def broadcast_heart_update(status: dict):
    """Broadcast heart status update."""
    await manager.broadcast("heart", {"status": status, "action": "heart_updated"})


async def broadcast_agents_update(agents: list):
    """Broadcast agents update."""
    await manager.broadcast(
        "agents", {"agents": agents, "count": len(agents), "action": "agents_updated"}
    )


async def broadcast_sessions_update(sessions: list):
    """Broadcast sessions update."""
    await manager.broadcast(
        "sessions", {"sessions": sessions, "count": len(sessions), "action": "sessions_updated"}
    )


# Background task to periodically broadcast full state
# (useful for ensuring clients stay in sync)


async def broadcast_full_state():
    """Broadcast complete state to all clients."""
    from src.services.openmemory import get_memory

    try:
        # Get current state
        memory = get_memory()
        stats = await memory.stats()

        # Broadcast to all channels
        await manager.broadcast(
            "all",
            {
                "type": "full_state",
                "memory_stats": stats,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
    except Exception as e:
        print(f"Error broadcasting full state: {e}")
