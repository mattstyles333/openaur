# OpenAura 🐧

> **Give your AI a memory and a shell.**  
> OpenAura makes AI assistants personal by adding persistent memory, Linux system access, and an empathy engine—all safely sandboxed in Docker.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-2496ED.svg?logo=docker&logoColor=white)](https://docker.com/)

```bash
# One-line setup
git clone https://github.com/mattstyles333/openaur.git && cd openaur && cp .env.example .env && docker-compose up -d
```

---

## What is OpenAura?

LLMs are incredible at reasoning, but they have a major limitation: **they don't know you**. Every conversation starts from scratch. They can't see your system, remember your preferences, or actually do things on your behalf.

**OpenAura bridges that gap.**

It's a self-hosted AI assistant that:
- 🧠 **Remembers everything** - Conversations, preferences, system state via OpenMemory
- 🐧 **Works with your Linux system** - Install packages, run commands, manage services
- 💬 **Adapts to your mood** - Empathy engine adjusts tone based on sentiment
- 🔒 **Runs in a sandbox** - Docker container keeps your host system safe
- 🔌 **Works with any LLM** - OpenRouter integration (Claude, GPT-4, DeepSeek, etc.)

Think of it as giving your favorite LLM a long-term memory and a bash shell, wrapped in a nice API.

---

## Why OpenAura?

### The Problem with Chatbots

You know the drill. You spend 20 minutes explaining your nginx setup to ChatGPT, it gives you great advice, you fix the issue. A week later, same problem happens. You open a new chat and... **start from zero.** It doesn't remember your config, your architecture, or that conversation.

**OpenAura solves this.** It persists context across sessions, so your AI actually learns about you and your systems over time.

### When to Use OpenAura vs Others

| Use Case | Best Tool | Why |
|----------|-----------|-----|
| General knowledge questions | Latest LLMs (ChatGPT, Claude, etc.) | Optimized for broad reasoning |
| Your specific system setup | **OpenAura** | Remembers your configs, packages, preferences |
| Installing/configuring Arch packages | **OpenAura** | Native AUR integration, can actually run commands |
| Complex reasoning tasks | Latest LLMs | State-of-the-art models |
| Long-running automation | **OpenAura** | Tmux-based async execution |
| Code review across sessions | **OpenAura** | Remembers your codebase context |

**Bottom line:** OpenAura isn't trying to replace those tools. It's for when you want an AI that knows *your* systems and can *actually do things* for you.

---

## Key Features

### 🧠 Cognitive Memory (OpenMemory)

Unlike cloud AI that forgets when you close the tab, OpenAura remembers:
- **Conversations** - Context across sessions
- **Preferences** - How you like things configured
- **System state** - What packages are installed, your configs
- **CLI tools** - Every command you've taught it

```python
# Example: Month 1
User: "I need to analyze nginx logs"
OpenAura: "I see you have nginx installed. Checking /var/log/nginx/error.log..."

# Month 3, same user
User: "That nginx issue again"
OpenAura: "Looking at your nginx setup... same config from March? 
           Let me check if that SSL cert renewal script I wrote for you is still working."
```

### 🐧 Arch Linux Native

Built for Arch users who live in the terminal:
- **AUR support** - Install any package via yay
- **System-aware** - Knows what's installed
- **Tmux execution** - Run long tasks async
- **Auto-discover** - Crawls man pages to learn your tools

```bash
# Make OpenAura aware of your tools
make crawl BINARY=git
make crawl BINARY=docker
make crawl BINARY=your-custom-script

# Now it can help you use them
make chat MSG="What's the safest way to rewrite my last 3 git commits?"
```

### 💬 Empathy Engine

Analyzes your sentiment and adapts:
- **Frustrated?** → Calm, step-by-step guidance
- **Excited?** → Matches your energy
- **Confused?** → Patient explanations with examples
- **Focused?** → Concise and technical

```bash
curl http://localhost:8000/heart
# { "mood": "focused", "empathy_level": 0.8 }
```

### 🔒 Docker Sandbox

Everything runs in containers:
- ✅ Your API keys stay local
- ✅ Can't accidentally break your host system
- ✅ Easy to wipe and restart
- ✅ Network isolated by default

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenRouter API key ([free at openrouter.ai](https://openrouter.ai/keys))

### 30-Second Setup

```bash
# 1. Clone
git clone https://github.com/mattstyles333/openaur.git
cd openaur

# 2. Configure
cp .env.example .env
# Edit .env: OPENROUTER_API_KEY=your_key_here

# 3. Start
docker-compose up -d

# 4. Test
make test
# ✅ Health check passed
```

### First Conversation

```bash
make chat MSG="What can you help me with?"

# Or register a tool first
make crawl BINARY=git
make chat MSG="How do I undo my last commit safely?"
```

---

## Example Interaction

```
$ openaur chat

╔═══════════════════════════════════════════════════════════╗
║         Personal AI Assistant with Arch Linux              ║
╚═══════════════════════════════════════════════════════════╝

You: My nginx is broken after the update

OpenAura: I see you're frustrated. Let me check your setup...

🔍 Found: nginx 1.25.3 (installed via pacman)
📄 Config: /etc/nginx/nginx.conf (modified 2 days ago)
📊 Last conversation: "Setting up SSL certificates" (3 weeks ago)
⚠️  Error in config: worker_connections exceeds limit

I remember you prefer fixing root causes over band-aids. 
The issue is your nginx config expects more connections than 
your system allows. Two options:

1. Lower worker_connections in nginx.conf (quick fix)
2. Increase system limits in /etc/security/limits.conf (proper fix)

Which would you prefer? I can apply either.
```

---

## API Endpoints

OpenAI-compatible + custom extensions:

| Endpoint | Description |
|----------|-------------|
| `/v1/chat/completions` | OpenAI-compatible chat |
| `/chat` | Enhanced with memory & empathy |
| `/memory/query` | Search your memory |
| `/packages/search` | Find Arch/AUR packages |
| `/packages/install` | Install packages |
| `/actions/crawl` | Learn a CLI tool |
| `/agents/spawn` | Run task in background |
| `/heart` | Empathy status |

[Full API docs →](https://mattstyles333.github.io/openaur/docs/)

---

## Common Use Cases

### Arch Linux Users
```bash
# "Find me a terminal with GPU support"
make search QUERY=alacritty

# "What broke after my update?"
make chat MSG="Check pacman.log for errors from yesterday"
```

### Developers
```bash
# "How do I squash these commits?"
make chat MSG="Interactive rebase last 3 commits"

# "Review this code"
make chat MSG="Check src/main.py for issues"
```

### DevOps
```bash
# "Check all my services"
make chat MSG="Which systemd services are failing?"

# Background task
openaur agents spawn server-monitor
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│   Docker Container (sandboxed)                              │
│                                                             │
│   ┌────────────┐    ┌───────────┐    ┌──────────────────┐   │
│   │  FastAPI   │───▶│  Gateway  │───▶│  OpenRouter LLM  │   │
│   │   Server   │    │           │    │  (Claude/GPT-4)  │   │
│   └────────────┘    └───────────┘    └──────────────────┘   │
│          │                                                  │
│          ▼                                                  │
│   ┌────────────┐    ┌───────────┐    ┌──────────────┐     │
│   │ OpenMemory │    │   yay     │    │    tmux      │     │
│   │  (SQLite)  │    │  (AUR)    │    │  (async)     │     │
│   └────────────┘    └───────────┘    └──────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Components:**
- **FastAPI** - REST API server
- **OpenRouter** - Access to best LLMs (Claude, GPT-4, etc.)
- **OpenMemory** - Persistent cognitive layer
- **yay** - Arch/AUR package management
- **tmux** - Background task execution
- **Empathy Engine** - Sentiment analysis

---

## CLI Usage

```bash
# Server
openaur server start      # Start containers
openaur server logs       # View logs

# Chat
openaur chat              # Interactive mode
openaur chat "message"    # One-shot

# Packages
openaur packages search <query>
openaur packages install <name>

# Actions (CLI registry)
openaur actions crawl <binary>
openaur actions list

# Development
ruff check . && ruff format .  # Lint & format
```

---

## Configuration

`.env` file:

```bash
# Required
OPENROUTER_API_KEY=your_key_here

# Optional
DEBUG=false
OPENMEMORY_DB_PATH=./data/openmemory.db
```

---

## Development

```bash
# Build locally
make build

# Run with logs attached
make run-logs

# Reset everything
make reset-db

# Run tests
make test
```

---

## Contributing

Contributions welcome! See [AGENTS.md](AGENTS.md) for code guidelines.

1. Fork it
2. Branch: `git checkout -b feature/cool-thing`
3. Commit: `git commit -m 'Add cool thing'`
4. Push: `git push origin feature/cool-thing`
5. PR it

---

## Roadmap

- [ ] Web UI (no CLI required)
- [ ] Plugin system
- [ ] Voice interface
- [ ] More distros (Ubuntu, Fedora)
- [ ] Kubernetes deployment
- [ ] Team/multi-user support

---

## License

MIT - See [LICENSE](LICENSE)

---

## Acknowledgments

**OpenAura stands on the shoulders of giants:**

### Core Stack
- [FastAPI](https://fastapi.tiangolo.com/) - The high-performance web framework
- [Typer](https://typer.tiangolo.com/) - CLI framework for the terminal interface
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database toolkit
- [Uvicorn](https://www.uvicorn.org/) - ASGI server

### Terminal & UI
- [Rich](https://github.com/Textualize/rich) - Beautiful terminal formatting
- [Open WebUI](https://github.com/open-webui/open-webui) - Web interface companion

### AI & Memory
- [OpenRouter](https://openrouter.ai/) - Universal LLM API
- [OpenMemory](https://github.com/yourusername/openmemory) - Cognitive memory layer

### System Tools
- [tmux](https://github.com/tmux/tmux) - Terminal multiplexer for async tasks
- [yay](https://github.com/Jguer/yay) - AUR helper for package management
- [Arch Linux](https://archlinux.org/) - Foundation OS
- [Docker](https://www.docker.com/) - Container sandbox
- [psutil](https://github.com/giampaolo/psutil) - System monitoring

### Python Ecosystem
- [httpx](https://www.python-httpx.org/) - HTTP client
- [PyYAML](https://pyyaml.org/) - YAML parsing
- [python-jose](https://github.com/mpdavis/python-jose) & [passlib](https://passlib.readthedocs.io/) - Security
- [aiofiles](https://github.com/Tinche/aiofiles) - Async file operations

**To all open source maintainers: thank you for sharing your work.**

---

## Questions?

- 🐛 [Issues](../../issues)
- 💬 [Discussions](../../discussions)
- 📖 [Website](https://mattstyles333.github.io/openaur/)
- 📚 [Docs](https://mattstyles333.github.io/openaur/docs/)

**[⭐ Star this repo](https://github.com/mattstyles333/openaur)** if you find it useful!
