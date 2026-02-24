"""Sub-agent service for OpenAura.

Manages specialized AI agents that run in isolated tmux sessions.
Each sub-agent has its own context, memory, and tool access.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import asyncio
from pathlib import Path

from src.services.tmux_executor import TmuxExecutor
from src.services.openmemory import get_memory, SessionMemory


class AgentState(Enum):
    """Agent lifecycle states."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class AgentDefinition:
    """Definition of a sub-agent."""

    id: str
    name: str
    description: str
    system_prompt: str
    model: str = "openrouter/auto"
    tools: List[str] = field(default_factory=list)
    max_iterations: int = 50
    timeout_seconds: int = 300
    parent_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AgentTask:
    """Task assigned to an agent."""

    id: str
    agent_id: str
    description: str
    context: Dict[str, Any]
    state: AgentState = AgentState.IDLE
    result: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class SubAgent:
    """Running instance of a sub-agent."""

    def __init__(
        self, definition: AgentDefinition, session_id: str, tmux_executor: TmuxExecutor
    ):
        self.definition = definition
        self.session_id = session_id
        self.tmux = tmux_executor
        self.memory = SessionMemory(session_id)
        self.state = AgentState.IDLE
        self.current_task: Optional[AgentTask] = None
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.iteration_count = 0

    async def execute_task(self, task: AgentTask) -> AgentTask:
        """Execute a task in this agent's context."""
        self.current_task = task
        task.state = AgentState.RUNNING
        task.started_at = datetime.utcnow()
        self.state = AgentState.RUNNING

        # Initialize context
        self.memory.add_message(role="system", content=self.definition.system_prompt)

        self.memory.add_message(
            role="user",
            content=f"Task: {task.description}\n\nContext: {json.dumps(task.context, indent=2)}",
        )

        try:
            # Execute in tmux session
            cmd = self._build_execution_command(task)

            result = await self.tmux.execute_async(
                session_name=self.session_id, command=cmd, cwd="/home/aura/app"
            )

            task.result = result.get("output", "")
            task.state = AgentState.COMPLETED
            self.state = AgentState.COMPLETED

        except Exception as e:
            task.error = str(e)
            task.state = AgentState.ERROR
            self.state = AgentState.ERROR

        task.completed_at = datetime.utcnow()
        self.iteration_count += 1

        return task

    def _build_execution_command(self, task: AgentTask) -> str:
        """Build the execution command for a task."""
        # Create a Python script to run in the tmux session
        script = f'''
import asyncio
import json
from src.services.gateway import OpenRouterGateway
from src.services.openmemory import get_session_memory

async def run_task():
    gateway = OpenRouterGateway()
    memory = get_session_memory("{self.session_id}")
    
    # Get conversation context
    context = memory.get_enhanced_context("{task.description}")
    
    # Build messages
    messages = [
        {{"role": "system", "content": """{self.definition.system_prompt}"""}},
        {{"role": "user", "content": """Task: {task.description}

Context: {json.dumps(task.context)}

Previous conversation:
{{context['conversation_history']}}

Relevant memories:
{{context['relevant_memories']}}"""}}
    ]
    
    # Call LLM
    response = await gateway.chat_completion(
        messages=messages,
        model="{self.definition.model}"
    )
    
    # Store response
    memory.add_message(role="assistant", content=response)
    
    print(response)
    return response

result = asyncio.run(run_task())
print("___AGENT_COMPLETE___")
print(json.dumps({{"result": result}}))
'''

        # Write script to temp file
        script_path = f"/tmp/agent_{self.session_id}_{task.id}.py"
        Path(script_path).write_text(script)

        return f"cd /home/aura/app && python {script_path}"

    def pause(self):
        """Pause agent execution."""
        self.state = AgentState.PAUSED
        self.tmux.send_keys(self.session_id, "C-c")

    def resume(self):
        """Resume agent execution."""
        self.state = AgentState.RUNNING

    def kill(self):
        """Kill agent session."""
        self.tmux.kill_session(self.session_id)
        self.state = AgentState.COMPLETED

    def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            "agent_id": self.definition.id,
            "session_id": self.session_id,
            "state": self.state.value,
            "current_task": self.current_task.id if self.current_task else None,
            "iteration_count": self.iteration_count,
            "memory_stats": self.memory.memory.stats(),
        }


class AgentRegistry:
    """Registry of agent definitions and running instances."""

    def __init__(self, storage_path: str = "/home/aura/app/data/agents"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.definitions: Dict[str, AgentDefinition] = {}
        self.running_agents: Dict[str, SubAgent] = {}
        self.tmux = TmuxExecutor()
        self._load_definitions()

    def _load_definitions(self):
        """Load agent definitions from storage."""
        for def_file in self.storage_path.glob("*.json"):
            try:
                data = json.loads(def_file.read_text())
                definition = AgentDefinition(
                    id=data["id"],
                    name=data["name"],
                    description=data["description"],
                    system_prompt=data["system_prompt"],
                    model=data.get("model", "openrouter/auto"),
                    tools=data.get("tools", []),
                    max_iterations=data.get("max_iterations", 50),
                    timeout_seconds=data.get("timeout_seconds", 300),
                    parent_id=data.get("parent_id"),
                )
                self.definitions[definition.id] = definition
            except Exception as e:
                print(f"Error loading agent definition {def_file}: {e}")

    def _save_definition(self, definition: AgentDefinition):
        """Save agent definition to storage."""
        def_file = self.storage_path / f"{definition.id}.json"
        data = {
            "id": definition.id,
            "name": definition.name,
            "description": definition.description,
            "system_prompt": definition.system_prompt,
            "model": definition.model,
            "tools": definition.tools,
            "max_iterations": definition.max_iterations,
            "timeout_seconds": definition.timeout_seconds,
            "parent_id": definition.parent_id,
            "created_at": definition.created_at.isoformat(),
        }
        def_file.write_text(json.dumps(data, indent=2))

    def register_agent(
        self,
        id: str,
        name: str,
        description: str,
        system_prompt: str,
        model: str = "openrouter/auto",
        tools: List[str] = None,
        parent_id: Optional[str] = None,
    ) -> AgentDefinition:
        """Register a new agent definition."""
        definition = AgentDefinition(
            id=id,
            name=name,
            description=description,
            system_prompt=system_prompt,
            model=model,
            tools=tools or [],
            parent_id=parent_id,
        )

        self.definitions[id] = definition
        self._save_definition(definition)

        return definition

    def get_definition(self, agent_id: str) -> Optional[AgentDefinition]:
        """Get agent definition by ID."""
        return self.definitions.get(agent_id)

    def list_definitions(self) -> List[AgentDefinition]:
        """List all agent definitions."""
        return list(self.definitions.values())

    async def spawn_agent(
        self, agent_id: str, task_description: str, task_context: Dict[str, Any] = None
    ) -> SubAgent:
        """Spawn a new agent instance to execute a task."""
        definition = self.get_definition(agent_id)
        if not definition:
            raise ValueError(f"Agent definition not found: {agent_id}")

        # Create unique session ID
        session_id = f"agent_{agent_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{id(task_description) % 10000}"

        # Create agent instance
        agent = SubAgent(definition, session_id, self.tmux)

        # Create task
        task = AgentTask(
            id=f"task_{session_id}",
            agent_id=agent_id,
            description=task_description,
            context=task_context or {},
        )

        # Store running agent
        self.running_agents[session_id] = agent

        # Execute task
        await agent.execute_task(task)

        return agent

    def get_running_agent(self, session_id: str) -> Optional[SubAgent]:
        """Get a running agent by session ID."""
        return self.running_agents.get(session_id)

    def list_running_agents(self) -> List[Dict[str, Any]]:
        """List all running agents."""
        return [agent.get_status() for agent in self.running_agents.values()]

    def kill_agent(self, session_id: str):
        """Kill a running agent."""
        agent = self.running_agents.get(session_id)
        if agent:
            agent.kill()
            del self.running_agents[session_id]

    def cleanup_completed(self):
        """Remove completed agents from running list."""
        completed = [
            sid
            for sid, agent in self.running_agents.items()
            if agent.state in (AgentState.COMPLETED, AgentState.ERROR)
        ]
        for sid in completed:
            del self.running_agents[sid]


# Predefined agent templates (similar to OpenCode's subagents)
AGENT_TEMPLATES = {
    "deep": AgentDefinition(
        id="deep",
        name="Deep Research Agent",
        description="Agent for deep analysis and research tasks",
        system_prompt="""You are a deep research agent. Your role is to:
1. Analyze problems thoroughly
2. Break down complex tasks
3. Research using available tools
4. Provide detailed, well-researched answers

When given a task:
- First understand the full scope
- Research any unknowns using the action registry
- Think step-by-step
- Provide comprehensive answers

Use the action registry to execute commands when needed.
Always explain your reasoning.""",
        model="openrouter/auto",
        tools=["search", "execute", "read_file"],
        max_iterations=100,
        timeout_seconds=600,
    ),
    "quick": AgentDefinition(
        id="quick",
        name="Quick Action Agent",
        description="Agent for fast, simple tasks",
        system_prompt="""You are a quick action agent. Your role is to:
1. Execute simple tasks rapidly
2. Use the simplest solution that works
3. Return results quickly

When given a task:
- Identify the fastest path to completion
- Use available tools efficiently
- Provide concise answers

Speed over perfection for simple tasks.""",
        model="openrouter/auto",
        tools=["execute", "read_file"],
        max_iterations=20,
        timeout_seconds=120,
    ),
    "code-reviewer": AgentDefinition(
        id="code-reviewer",
        name="Code Review Agent",
        description="Agent for reviewing code changes",
        system_prompt="""You are a code review agent. Your role is to:
1. Review code for quality issues
2. Check for security problems
3. Verify best practices
4. Suggest improvements

When reviewing code:
- Check for common anti-patterns
- Verify error handling
- Look for security issues
- Suggest simplifications

Be constructive but thorough.""",
        model="openrouter/auto",
        tools=["read_file", "execute", "git_diff"],
        max_iterations=30,
        timeout_seconds=180,
    ),
    "test-runner": AgentDefinition(
        id="test-runner",
        name="Test Runner Agent",
        description="Agent for running tests and analyzing results",
        system_prompt="""You are a test runner agent. Your role is to:
1. Execute test suites
2. Analyze test failures
3. Debug failing tests
4. Report results clearly

When running tests:
- Run the appropriate test command
- Capture full output
- Analyze failures
- Suggest fixes

Be thorough in debugging.""",
        model="openrouter/auto",
        tools=["execute", "read_file"],
        max_iterations=50,
        timeout_seconds=300,
    ),
    "committer": AgentDefinition(
        id="committer",
        name="Git Commit Agent",
        description="Agent for creating intelligent git commits",
        system_prompt="""You are a git commit agent. Your role is to:
1. Analyze code changes
2. Create meaningful commit messages
3. Stage appropriate files
4. Verify commit quality

When committing:
- Review git status and diff
- Write clear, concise commit messages
- Follow conventional commit format when appropriate
- Ensure only relevant files are staged

Quality commits over quantity.""",
        model="openrouter/auto",
        tools=["execute", "git_status", "git_diff"],
        max_iterations=20,
        timeout_seconds=120,
    ),
}


# Global registry instance
_registry: Optional[AgentRegistry] = None


def get_agent_registry() -> AgentRegistry:
    """Get global agent registry instance."""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()

        # Register default templates
        for template in AGENT_TEMPLATES.values():
            if template.id not in _registry.definitions:
                _registry.register_agent(
                    id=template.id,
                    name=template.name,
                    description=template.description,
                    system_prompt=template.system_prompt,
                    model=template.model,
                    tools=template.tools,
                )

    return _registry
