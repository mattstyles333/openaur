"""Agent routes - Sub-agent management API.

Provides endpoints for spawning, managing, and monitoring sub-agents.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from src.services.agents import (
    get_agent_registry,
    AgentRegistry,
    AgentDefinition,
    AgentState,
)

router = APIRouter()


class AgentCreateRequest(BaseModel):
    id: str
    name: str
    description: str
    system_prompt: str
    model: str = "openrouter/auto"
    tools: List[str] = []
    parent_id: Optional[str] = None


class AgentSpawnRequest(BaseModel):
    agent_id: str
    task_description: str
    task_context: Dict[str, Any] = {}


class AgentResponse(BaseModel):
    id: str
    name: str
    description: str
    model: str
    tools: List[str]
    state: Optional[str] = None


@router.post("/register")
async def register_agent(request: AgentCreateRequest):
    """Register a new agent definition."""
    registry = get_agent_registry()

    definition = registry.register_agent(
        id=request.id,
        name=request.name,
        description=request.description,
        system_prompt=request.system_prompt,
        model=request.model,
        tools=request.tools,
        parent_id=request.parent_id,
    )

    return {
        "id": definition.id,
        "name": definition.name,
        "description": definition.description,
        "model": definition.model,
        "tools": definition.tools,
    }


@router.get("/definitions")
async def list_agent_definitions():
    """List all registered agent definitions."""
    registry = get_agent_registry()
    definitions = registry.list_definitions()

    return {
        "count": len(definitions),
        "agents": [
            {
                "id": d.id,
                "name": d.name,
                "description": d.description,
                "model": d.model,
                "tools": d.tools,
            }
            for d in definitions
        ],
    }


@router.get("/definitions/{agent_id}")
async def get_agent_definition(agent_id: str):
    """Get a specific agent definition."""
    registry = get_agent_registry()
    definition = registry.get_definition(agent_id)

    if not definition:
        raise HTTPException(status_code=404, detail="Agent definition not found")

    return {
        "id": definition.id,
        "name": definition.name,
        "description": definition.description,
        "system_prompt": definition.system_prompt,
        "model": definition.model,
        "tools": definition.tools,
        "max_iterations": definition.max_iterations,
        "timeout_seconds": definition.timeout_seconds,
        "parent_id": definition.parent_id,
    }


@router.post("/spawn")
async def spawn_agent(request: AgentSpawnRequest, background_tasks: BackgroundTasks):
    """Spawn a new agent instance to execute a task.

    The agent runs in its own tmux session with isolated context.
    """
    registry = get_agent_registry()

    # Check if agent definition exists
    definition = registry.get_definition(request.agent_id)
    if not definition:
        raise HTTPException(
            status_code=404, detail=f"Agent definition not found: {request.agent_id}"
        )

    # Spawn agent (async)
    agent = await registry.spawn_agent(
        agent_id=request.agent_id,
        task_description=request.task_description,
        task_context=request.task_context,
    )

    return {
        "session_id": agent.session_id,
        "agent_id": request.agent_id,
        "task_id": agent.current_task.id if agent.current_task else None,
        "state": agent.state.value,
        "message": f"Agent {request.agent_id} spawned in tmux session: {agent.session_id}",
    }


@router.get("/running")
async def list_running_agents():
    """List all currently running agent instances."""
    registry = get_agent_registry()
    agents = registry.list_running_agents()

    return {"count": len(agents), "agents": agents}


@router.get("/running/{session_id}")
async def get_agent_status(session_id: str):
    """Get status of a running agent."""
    registry = get_agent_registry()
    agent = registry.get_running_agent(session_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return agent.get_status()


@router.post("/running/{session_id}/pause")
async def pause_agent(session_id: str):
    """Pause a running agent."""
    registry = get_agent_registry()
    agent = registry.get_running_agent(session_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent.pause()

    return {
        "session_id": session_id,
        "state": agent.state.value,
        "message": "Agent paused",
    }


@router.post("/running/{session_id}/resume")
async def resume_agent(session_id: str):
    """Resume a paused agent."""
    registry = get_agent_registry()
    agent = registry.get_running_agent(session_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent.resume()

    return {
        "session_id": session_id,
        "state": agent.state.value,
        "message": "Agent resumed",
    }


@router.post("/running/{session_id}/kill")
async def kill_agent(session_id: str):
    """Kill a running agent."""
    registry = get_agent_registry()

    registry.kill_agent(session_id)

    return {"session_id": session_id, "message": "Agent killed"}


@router.get("/templates")
async def list_agent_templates():
    """List built-in agent templates."""
    from src.services.agents import AGENT_TEMPLATES

    return {
        "templates": [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "model": t.model,
                "tools": t.tools,
            }
            for t in AGENT_TEMPLATES.values()
        ]
    }


@router.post("/templates/{template_id}/register")
async def register_from_template(template_id: str):
    """Register an agent from a built-in template."""
    from src.services.agents import AGENT_TEMPLATES

    if template_id not in AGENT_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")

    template = AGENT_TEMPLATES[template_id]
    registry = get_agent_registry()

    # Register if not already exists
    if template_id not in registry.definitions:
        registry.register_agent(
            id=template.id,
            name=template.name,
            description=template.description,
            system_prompt=template.system_prompt,
            model=template.model,
            tools=template.tools,
        )

    return {
        "template_id": template_id,
        "agent_id": template.id,
        "message": f"Agent {template.name} registered from template",
    }


@router.post("/cleanup")
async def cleanup_agents():
    """Clean up completed agent sessions."""
    registry = get_agent_registry()

    before_count = len(registry.running_agents)
    registry.cleanup_completed()
    after_count = len(registry.running_agents)

    return {
        "cleaned": before_count - after_count,
        "remaining": after_count,
        "message": f"Cleaned up {before_count - after_count} completed agents",
    }
