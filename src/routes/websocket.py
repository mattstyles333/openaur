"""WebSocket routes for real-time dashboard updates.

Provides WebSocket endpoints for live data streaming to dashboard.
"""


from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.services.websocket_manager import manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, subscription: str | None = "all"):
    """WebSocket endpoint for real-time dashboard updates.

    Query Parameters:
    - subscription: Channel to subscribe to (memory, heart, agents, sessions, all)

    Messages received from client:
    - {"action": "ping"} -> Pong response
    - {"action": "subscribe", "channel": "memory"} -> Subscribe to channel
    - {"action": "unsubscribe", "channel": "memory"} -> Unsubscribe from channel

    Messages sent to client:
    - {"type": "connected", ...} -> Connection established
    - {"type": "update", "channel": "memory", "data": {...}} -> Data update
    - {"type": "personal", ...} -> Direct response to client action
    """
    await manager.connect(websocket, subscription or "all")

    try:
        while True:
            # Receive and handle client messages
            data = await websocket.receive_json()

            action = data.get("action")

            if action == "ping":
                await manager.send_personal(websocket, {"action": "pong"})

            elif action == "subscribe":
                channel = data.get("channel", "all")
                if channel in manager.connections:
                    manager.connections[channel].add(websocket)
                await manager.send_personal(websocket, {"action": "subscribed", "channel": channel})

            elif action == "unsubscribe":
                channel = data.get("channel", "all")
                if channel in manager.connections:
                    manager.connections[channel].discard(websocket)
                await manager.send_personal(
                    websocket, {"action": "unsubscribed", "channel": channel}
                )

            elif action == "get_state":
                # Send current full state
                from src.services.openmemory import get_memory

                memory = get_memory()
                stats = await memory.stats()

                await manager.send_personal(
                    websocket,
                    {
                        "action": "state",
                        "data": {
                            "memory_stats": stats,
                        },
                    },
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)
