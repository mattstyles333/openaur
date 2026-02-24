"""Context manager for openaur chat system.

Analyzes user queries, manages actions, retrieves memories, and builds context.
"""

from typing import Any

from src.services.openmemory import get_memory
from src.services.package_manager import PackageManager
from src.utils.yaml_registry import YamlRegistry


class IntentAnalyzer:
    """Analyzes user intent from queries."""

    # Action-related keywords
    ACTION_KEYWORDS = [
        "install",
        "run",
        "execute",
        "build",
        "compile",
        "deploy",
        "commit",
        "push",
        "pull",
        "clone",
        "create",
        "delete",
        "search",
        "find",
        "list",
        "show",
        "get",
        "set",
        "configure",
        "setup",
        "update",
        "upgrade",
        "clean",
        "remove",
        "start",
        "stop",
    ]

    # Package-related keywords
    PACKAGE_KEYWORDS = [
        "package",
        "install",
        "pacman",
        "yay",
        "aur",
        "dependency",
        "library",
        "tool",
        "software",
        "program",
        "app",
    ]

    # Memory-related keywords
    MEMORY_KEYWORDS = [
        "remember",
        "recall",
        "forget",
        "memory",
        "previous",
        "before",
        "earlier",
        "last time",
        "you said",
        "we discussed",
    ]

    def analyze(self, query: str) -> dict[str, Any]:
        """Analyze user query for intent."""
        query_lower = query.lower()

        # Check for action intent
        needs_action = any(kw in query_lower for kw in self.ACTION_KEYWORDS)

        # Check for package intent
        needs_package = any(kw in query_lower for kw in self.PACKAGE_KEYWORDS)

        # Check for memory recall
        needs_memory = any(kw in query_lower for kw in self.MEMORY_KEYWORDS)

        # Extract potential tool names
        tools_mentioned = self._extract_tools(query_lower)

        # Determine primary intent
        intent = "chat"
        if needs_action and tools_mentioned:
            intent = "action"
        elif needs_package:
            intent = "package"
        elif needs_memory:
            intent = "memory"

        return {
            "intent": intent,
            "needs_action": needs_action,
            "needs_package": needs_package,
            "needs_memory": needs_memory,
            "tools_mentioned": tools_mentioned,
            "confidence": self._calculate_confidence(query_lower, intent),
        }

    def _extract_tools(self, query: str) -> list[str]:
        """Extract potential tool names from query."""
        # Common CLI tools
        common_tools = [
            "git",
            "docker",
            "curl",
            "wget",
            "npm",
            "pip",
            "cargo",
            "make",
            "gcc",
            "python",
            "node",
            "nvim",
            "vim",
            "code",
            "glab",
            "gh",
            "aws",
            "gcloud",
            "kubectl",
            "helm",
            "cargo",
            "rust",
            "go",
            "php",
            "ruby",
            "java",
            "1password",
            "op",
            "bitwarden",
            "bw",
            "neovim",
            "nvim",
            "emacs",
            "nano",
        ]

        found = []
        for tool in common_tools:
            if tool in query:
                found.append(tool)

        return found

    def _calculate_confidence(self, query: str, intent: str) -> float:
        """Calculate confidence score for intent."""
        scores = {
            "action": 0.7 if any(kw in query for kw in self.ACTION_KEYWORDS) else 0.3,
            "package": 0.8 if any(kw in query for kw in self.PACKAGE_KEYWORDS) else 0.2,
            "memory": 0.6 if any(kw in query for kw in self.MEMORY_KEYWORDS) else 0.2,
            "chat": 0.5,
        }
        return scores.get(intent, 0.5)


class ActionSuggester:
    """Suggests actions based on user intent."""

    def __init__(self):
        self.yaml_reg = YamlRegistry()
        self.pkg_manager = PackageManager()

    def suggest(self, intent: dict[str, Any]) -> dict[str, Any]:
        """Suggest actions based on intent."""
        tools = intent.get("tools_mentioned", [])
        suggestions = {
            "available": [],
            "can_install": [],
            "needs_installation": [],
        }

        for tool in tools:
            # Check if already registered
            tree = self.yaml_reg.load_action(tool)
            if tree:
                suggestions["available"].append(
                    {"tool": tool, "commands": list(tree.get("tree", {}).keys())[:5]}
                )
            else:
                # Check if can be installed
                if self._can_install(tool):
                    suggestions["can_install"].append(
                        {
                            "tool": tool,
                            "install_cmd": f"yay -S {tool}"
                            if tool in self._get_aur_packages()
                            else f"pacman -S {tool}",
                        }
                    )
                else:
                    suggestions["needs_installation"].append(tool)

        return suggestions

    def _can_install(self, tool: str) -> bool:
        """Check if tool can be installed."""
        # Check official repos and AUR
        return tool in self._get_official_packages() or tool in self._get_aur_packages()

    def _get_official_packages(self) -> set:
        """Get list of available official packages."""
        # This would ideally query pacman
        return {"neovim", "vim", "git", "docker", "curl", "wget", "nodejs", "python"}

    def _get_aur_packages(self) -> set:
        """Get list of common AUR packages."""
        return {"1password", "visual-studio-code-bin", "google-chrome", "slack-desktop"}


class MemoryManager:
    """Manages conversation memory."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.memory = get_memory()

    def store_interaction(
        self,
        user_query: str,
        assistant_response: str,
        intent: dict[str, Any],
        actions_used: list[str] | None = None,
    ):
        """Store interaction in memory."""
        # Store user query
        self.memory.store(
            content=user_query,
            memory_type="user_query",
            importance=0.7,
            tags=["conversation", intent.get("intent", "chat") or "chat"],
            metadata={"intent": intent, "session_id": self.session_id},
        )

        # Store assistant response
        self.memory.store(
            content=assistant_response,
            memory_type="assistant_response",
            importance=0.6,
            tags=["conversation", "assistant"],
            metadata={"actions_used": actions_used or []},
        )

        # Store action learnings
        if actions_used:
            for action in actions_used:
                self.memory.store(
                    content=f"User used {action} to accomplish: {user_query}",
                    memory_type="action_learning",
                    importance=0.8,
                    tags=["action", action, "learning"],
                )

    def get_relevant_context(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Get relevant memories for context."""
        memories = self.memory.retrieve(query, limit=limit, min_importance=0.3)

        return [
            {
                "content": m.content,
                "type": m.memory_type,
                "importance": m.importance,
                "tags": m.tags,
            }
            for m in memories
        ]

    def get_session_summary(self) -> str:
        """Get summary of current session."""
        # Get recent memories
        memories = self.memory.retrieve("*", limit=10, min_importance=0.0)

        if not memories:
            return "No previous context."

        # Build summary
        queries = [m.content for m in memories if m.memory_type == "user_query"]
        actions = set()
        for m in memories:
            if "action" in m.tags:
                for tag in m.tags:
                    if tag != "action":
                        actions.add(tag)

        summary = f"Session has {len(queries)} interactions. "
        if actions:
            summary += f"Actions used: {', '.join(actions)}."

        return summary


class ContextBuilder:
    """Builds complete context for LLM calls."""

    def __init__(self):
        self.intent_analyzer = IntentAnalyzer()
        self.action_suggester = ActionSuggester()

    def build(self, user_query: str, session_id: str) -> dict[str, Any]:
        """Build complete context for a query."""
        # Analyze intent
        intent = self.intent_analyzer.analyze(user_query)

        # Get memory context
        memory_mgr = MemoryManager(session_id)
        relevant_memories = memory_mgr.get_relevant_context(user_query)

        # Get action suggestions
        action_suggestions = self.action_suggester.suggest(intent)

        # Get session summary
        session_summary = memory_mgr.get_session_summary()

        return {
            "intent": intent,
            "relevant_memories": relevant_memories,
            "action_suggestions": action_suggestions,
            "session_summary": session_summary,
            "memory_manager": memory_mgr,
        }

    def build_system_prompt(self, context: dict[str, Any]) -> str:
        """Build system prompt with full context."""
        # Base openaur context
        base = """You are openaur, an AI assistant running in an Arch Linux environment.

CRITICAL CONTEXT - This is Arch Linux:
- Package manager: pacman (official repos) and yay (AUR helper)
- To install packages: pacman -S <package> OR yay -S <aur-package>
- User has passwordless sudo access

ABOUT OPENAURA:
openaur is a personal AI assistant with these capabilities:
- CLI tool: /home/laptop/Documents/code/openaur/openaur
  * heart: Health check with empathy
  * chat: Interactive chat
  * ingest action <tool>: Register CLI tools (e.g., ingest action git)
  * packages: Package management (search, install, cleanup)
  * sessions: Tmux session management
  * test: Run tests
- API: http://localhost:8000
- Open WebUI: http://localhost:3000
- Sub-agents: deep, quick, code-reviewer, test-runner, committer (each runs in isolated tmux)

OPENMEMORY:
You have access to a memory system that:
- Stores user queries and your responses
- Tracks which actions/tools were used
- Retrieves relevant context from previous conversations
- Learns from user patterns

When users ask about openaur capabilities, reference these features."""

        # Add intent context
        intent = context.get("intent", {})
        intent_str = f"\n\nUSER INTENT: {intent.get('intent', 'chat')}"
        if intent.get("tools_mentioned"):
            intent_str += f" (tools: {', '.join(intent['tools_mentioned'])})"

        # Add action suggestions
        action_str = ""
        suggestions = context.get("action_suggestions", {})
        if suggestions.get("available"):
            action_str += "\n\nAVAILABLE ACTIONS:"
            for action in suggestions["available"]:
                action_str += (
                    f"\n- {action['tool']}: {', '.join(action['commands'][:3])}"
                )

        if suggestions.get("can_install"):
            action_str += "\n\nCAN INSTALL:"
            for action in suggestions["can_install"]:
                action_str += f"\n- {action['tool']}: {action['install_cmd']}"

        # Add relevant memories
        memory_str = ""
        memories = context.get("relevant_memories", [])
        if memories:
            memory_str += "\n\nRELEVANT MEMORIES:"
            for mem in memories[:3]:
                memory_str += f"\n- [{mem['type']}] {mem['content'][:100]}"

        # Add session context
        session = context.get("session_summary", "")
        if session:
            base += f"\n\nSESSION CONTEXT: {session}"

        return base + intent_str + action_str + memory_str


def preload_openaura_context():
    """Pre-load OpenMemory with openaur design context."""
    memory = get_memory()

    context_items = [
        {
            "content": "openaur is a personal AI assistant with Arch Linux, OpenRouter, and OpenMemory integration",
            "type": "system",
            "importance": 1.0,
            "tags": ["openaura", "overview"],
        },
        {
            "content": "The openaur CLI is located at /home/laptop/Documents/code/openaur/openaur and has commands: heart, chat, ingest action, packages, sessions, test",
            "type": "system",
            "importance": 0.9,
            "tags": ["openaura", "cli", "commands"],
        },
        {
            "content": "On Arch Linux, use 'pacman -S <pkg>' for official repos and 'yay -S <pkg>' for AUR packages",
            "type": "system",
            "importance": 0.9,
            "tags": ["arch", "packages", "install"],
        },
        {
            "content": "openaur has sub-agents: deep (research), quick (fast tasks), code-reviewer, test-runner, committer - each runs in isolated tmux sessions",
            "type": "system",
            "importance": 0.8,
            "tags": ["openaura", "agents", "sub-agents"],
        },
        {
            "content": "The OpenMemory API is at /memory with endpoints for store, retrieve, context, and stats",
            "type": "system",
            "importance": 0.8,
            "tags": ["openaura", "memory", "api"],
        },
        {
            "content": "Action registry stores CLI tool documentation via BFS crawling (depth 12). Use 'openaur ingest action <tool>' to register new tools",
            "type": "system",
            "importance": 0.8,
            "tags": ["openaura", "actions", "registry"],
        },
        {
            "content": "openaur API runs on port 8000, Open WebUI on port 3000. Both are in docker-compose.",
            "type": "system",
            "importance": 0.7,
            "tags": ["openaura", "ports", "docker"],
        },
        {
            "content": "1Password CLI can be installed via AUR: yay -S 1password or yay -S 1password-cli",
            "type": "system",
            "importance": 0.7,
            "tags": ["1password", "aur", "install"],
        },
    ]

    for item in context_items:
        memory.store(
            content=item["content"],
            memory_type=item["type"],
            importance=item["importance"],
            tags=item["tags"],
        )

    return len(context_items)
