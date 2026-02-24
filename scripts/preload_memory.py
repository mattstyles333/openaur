#!/usr/bin/env python3
"""Preload OpenMemory with openaur design context.

Run this to initialize the memory system with knowledge about
how openaur works, its architecture, and capabilities.
"""

import sys

sys.path.insert(0, "/home/laptop/Documents/code/openaur")

from src.services.context_manager import preload_openaura_context
from src.services.openmemory import get_memory


def preload_memory():
    """Preload memory with openaur design context."""
    print("🧠 Preloading OpenMemory with openaur context...")

    # Preload from context_manager
    count = preload_openaura_context()
    print(f"✓ Loaded {count} base context items")

    # Additional detailed context
    memory = get_memory()

    detailed_context = [
        {
            "content": """openaur Architecture:
            - Base: Arch Linux Docker container with AUR support via yay
            - Gateway: FastAPI (port 8000) connecting to OpenRouter AI models
            - Memory: OpenMemory cognitive layer with SQLite persistence
            - Execution: Tmux-based async command execution
            - CLI Tools: YAML-based action registry for CLI documentation
            - WebUI: Open WebUI integration via OpenAI-compatible API (port 3000)""",
            "type": "system",
            "importance": 0.95,
            "tags": ["openaura", "architecture", "design"],
        },
        {
            "content": """Two-Stage Processing:
            1. Fast model (openai/gpt-oss-20b:nitro) handles:
               - Sentiment analysis (mood, urgency, tone)
               - Intent detection (action, package, memory, chat)
               - Action detection (what tools/commands needed)
               - Memory retrieval (relevant past context)
            2. Quality model (openrouter/auto) generates final response with full context""",
            "type": "system",
            "importance": 0.95,
            "tags": ["openaura", "two-stage", "processing", "models"],
        },
        {
            "content": """Heart Agent (EmpathyEngine):
            - Analyzes user sentiment and emotional state
            - Detects 5 sentiment categories: positive, confident, neutral, frustrated, stressed
            - Measures emotional intensity (0.0 to 1.0)
            - Detects context: git, docker, development, system, error
            - Adapts prompts based on emotional state""",
            "type": "system",
            "importance": 0.9,
            "tags": ["openaura", "heart", "empathy", "sentiment"],
        },
        {
            "content": """OpenMemory System:
            - Two-tier architecture: short-term (50 items) + session memory
            - Importance scoring with time decay (0.95 per hour)
            - Memory types: context, user_query, assistant_response, action_learning
            - Keyword-based retrieval with relevance scoring
            - Stores: user queries, assistant responses, action patterns""",
            "type": "system",
            "importance": 0.9,
            "tags": ["openaura", "memory", "openmemory"],
        },
        {
            "content": """Action Registry:
            - Stores CLI tool documentation as YAML in actions/manifests/
            - BFS crawler extracts: subcommands, descriptions, arguments
            - Crawls --help output to depth 12
            - Safety levels: 1 (read), 2 (write), 3 (destructive)
            - Register new tools: openaur ingest action <binary>""",
            "type": "system",
            "importance": 0.9,
            "tags": ["openaura", "actions", "registry", "cli"],
        },
        {
            "content": """Sub-Agent System:
            - Agents: deep (research, 100 iter), quick (fast, 20 iter), 
              code-reviewer, test-runner, committer
            - Each runs in isolated tmux session
            - Agent states: idle, running, paused, completed, error
            - Parent-child relationships for agent hierarchies
            - Task queue and iteration tracking""",
            "type": "system",
            "importance": 0.85,
            "tags": ["openaura", "agents", "sub-agents", "tmux"],
        },
        {
            "content": """CLI Tool (openaur):
            - Server management: start, stop, restart, status, logs, shell
            - Core: heart, chat, sessions
            - Ingestion: action, memory, email, status
            - Package: search, install
            - Testing: test endpoint validation
            - Rich terminal output with spinners and tables""",
            "type": "system",
            "importance": 0.85,
            "tags": ["openaura", "cli", "commands"],
        },
        {
            "content": """Package Management (Arch Linux):
            - Uses yay for AUR packages
            - Uses pacman for official repos
            - Search: yay -Ss <query> or pacman -Ss <query>
            - Install official: pacman -S <package>
            - Install AUR: yay -S <package>
            - Never use apt, brew, or Ubuntu commands""",
            "type": "system",
            "importance": 0.9,
            "tags": ["arch", "packages", "pacman", "yay"],
        },
        {
            "content": """Context Manager:
            - IntentAnalyzer: Detects user intent (action, package, memory, chat)
            - ActionSuggester: Checks registered tools, suggests installation
            - MemoryManager: Stores/retrieves conversation context
            - ContextBuilder: Builds complete context for LLM calls
            - Integrates intent + memories + actions + session summary""",
            "type": "system",
            "importance": 0.85,
            "tags": ["openaura", "context", "manager"],
        },
        {
            "content": """Analysis Engine (Enhanced Heart):
            - Uses fast model for: sentiment, intent, action detection, memory retrieval
            - Shows thinking/analysis visible to user in OpenWebUI
            - Properly saves interactions with rich context
            - Preloads memory with openaur design context
            - Adapts responses based on emotional state and urgency""",
            "type": "system",
            "importance": 0.95,
            "tags": ["openaura", "analysis", "engine", "heart"],
        },
    ]

    for item in detailed_context:
        memory.store(
            content=item["content"],
            memory_type=item["type"],
            importance=item["importance"],
            tags=item["tags"],
        )

    print(f"✓ Loaded {len(detailed_context)} detailed context items")

    # Print stats
    stats = memory.stats()
    print("\n📊 Memory Stats:")
    print(f"   Total memories: {stats['total_memories']}")
    print(f"   By type: {stats['by_type']}")
    print(f"   Utilization: {stats['utilization']:.1%}")

    print("\n✅ OpenMemory preloaded with openaur context!")
    return stats["total_memories"]


if __name__ == "__main__":
    total = preload_memory()
    sys.exit(0 if total > 0 else 1)
