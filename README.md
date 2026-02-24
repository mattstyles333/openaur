# OpenAura 🐧

> **AI That Remembers, Understands, and Acts**  
> The first personal AI assistant with Arch Linux integration, emotional intelligence, and cognitive memory.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-2496ED.svg?logo=docker&logoColor=white)](https://docker.com/)

**One-line setup:**
```bash
docker-compose up -d && curl http://localhost:8000/health
```

---

## 🤔 Why OpenAura?

Most AI assistants are **stateless black boxes**. OpenAura is different:

| Feature | OpenAura | ChatGPT | Claude | Others |
|---------|----------|---------|--------|--------|
| **Cognitive Memory** | ✅ Persistent context | ❌ Per-session only | ❌ Limited | ❌ No |
| **Emotional Intelligence** | ✅ Empathy engine | ❌ No | ❌ No | ❌ No |
| **System Integration** | ✅ Arch Linux native | ❌ Cloud-only | ❌ Cloud-only | ❌ Limited |
| **Package Management** | ✅ AUR + official | ❌ N/A | ❌ N/A | ❌ No |
| **Action Registry** | ✅ Auto-discover CLI | ❌ No | ❌ No | ❌ No |
| **OpenAI Compatible** | ✅ Drop-in API | N/A | N/A | N/A |
| **Self-Hosted** | ✅ Your data stays local | ❌ Cloud | ❌ Cloud | ❌ Cloud |

**OpenAura doesn't just answer questions—it remembers, adapts, and takes action on your system.**

---

## ✨ What Makes It Special

### 🧠 Cognitive Memory (OpenMemory)
Unlike other AIs that forget everything when you close the tab, OpenAura remembers:
- **Conversations** - Context across sessions
- **Preferences** - How you like things done
- **System state** - What packages are installed, what configs exist
- **Actions** - CLI tools you've registered and how to use them

```python
# Example: OpenAura remembers this conversation
User: "I need to analyze nginx logs"
OpenAura: "I see you have nginx installed (registered in actions). 
           Would you like me to check /var/log/nginx/error.log?"
```

### 💬 Empathy Engine
OpenAura analyzes sentiment and adapts its tone:
- **Frustrated?** → Offers clear, step-by-step guidance
- **Excited?** → Matches your energy with enthusiasm  
- **Confused?** → Simplifies and explains more carefully

```bash
# Check the empathy status
curl http://localhost:8000/heart
# Returns: { "mood": "focused", "tone": "technical", "empathy_level": 0.8 }
```

### 🔧 Action Registry
Auto-discover and register CLI tools with deep documentation:

```bash
# Crawl git's man pages and help text
make crawl BINARY=git

# Now OpenAura knows every git command, flag, and use case
make chat MSG="How do I undo my last 3 commits safely?"
```

### 🐧 Arch Linux Native
First AI assistant built for Arch users:
- **AUR support** - Install any package from Arch User Repository
- **Pacman integration** - Native package management
- **Tmux sessions** - Async command execution without blocking
- **System-aware** - Knows what's installed and what isn't

```bash
# Search both official repos and AUR
make search QUERY=neovim
# Results: neovim (official), neovim-git (AUR), neovim-nightly (AUR)...

# Install from AUR with one command
make install PACKAGE=neovim-git
```

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenRouter API key ([free at openrouter.ai](https://openrouter.ai/keys))

### 1. Clone & Setup (30 seconds)
```bash
git clone https://github.com/mattstyles333/openaur.git
cd openaur

# Setup environment
cp .env.example .env
# Edit .env: OPENROUTER_API_KEY=your_key_here

# Start everything
docker-compose up -d
```

### 2. Test It (10 seconds)
```bash
make test
# ✅ Health check passed
```

### 3. First Chat (5 seconds)
```bash
make chat MSG="What can you help me with?"
```

### 4. Register Your Tools (Optional)
```bash
# Make OpenAura aware of your CLI tools
make crawl BINARY=docker
make crawl BINARY=kubectl
make crawl BINARY=ffmpeg
```

---

## 📸 Terminal Demo

```
$ openaur

╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   ██████╗ ██████╗ ███████╗███╗   ██╗ █████╗ ██╗   ██╗██████╗  ║
║  ██╔═══██╗██╔══██╗██╔════╝████╗  ██║██╔══██╗██║   ██║██╔══██╗ ║
║  ██║   ██║██████╔╝█████╗  ██╔██╗ ██║███████║██║   ██║██████╔╝ ║
║  ██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║██╔══██║██║   ██║██╔══██╗ ║
║  ╚██████╔╝██║     ███████╗██║ ╚████║██║  ██║╚██████╔╝██║  ██║ ║
║   ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝ ║
║                                                           ║
║         Personal AI Assistant with Arch Linux              ║
╚═══════════════════════════════════════════════════════════╝

$ openaur chat
You: My nginx is broken after the update

OpenAura: I see you're frustrated about nginx. Let me help you troubleshoot.
         I found nginx in your action registry. Checking your system...

         🔍 Found: nginx 1.25.3 installed
         📄 Config: /etc/nginx/nginx.conf (last modified 2 days ago)
         ⚠️  Error in config: "worker_connections 4096" exceeds limit

         Fix: Edit /etc/nginx/nginx.conf line 23 and change to 1024,
         or increase the system limit in /etc/security/limits.conf

         Shall I apply the fix? [Y/n]
```

---

## 🎯 Use Cases

### For Arch Linux Users
- **Package discovery** - "Find me a better terminal than Alacritty"
- **Troubleshooting** - "Why did my system update break?"
- **Configuration** - "Set up nginx with SSL and rate limiting"

### For Developers
- **CLI assistant** - "How do I squash these commits?"
- **System automation** - Run long tasks in background tmux sessions
- **Code review** - "Check this Python code for issues"

### For DevOps/SRE
- **Server management** - "Show me which services are failing"
- **Log analysis** - "Find errors in /var/log today"
- **Action registry** - Document your custom scripts and tools

### For Power Users
- **Memory** - Build up knowledge over months
- **Sub-agents** - Spawn specialized AIs for different tasks
- **Email integration** - Query your inbox with natural language

---

## 📊 Dashboard & Monitoring

OpenAura includes a real-time dashboard showing:

```bash
$ curl http://localhost:8000/dashboard | jq
{
  "services": {
    "openaura_api": "running",
    "open_webui": "connected",
    "memory_layer": "active",
    "email_ingestion": "ready"
  },
  "memory": {
    "total_memories": 1427,
    "sessions": 23,
    "last_interaction": "2 minutes ago"
  },
  "system": {
    "cpu_percent": 12.4,
    "memory_used_gb": 3.2,
    "disk_percent": 67
  }
}
```

---

## 🌐 API Endpoints

OpenAI-compatible + Extended:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/chat/completions` | POST | OpenAI-compatible streaming chat |
| `/v1/models` | GET | List available LLMs via OpenRouter |
| `/chat` | POST | Enhanced chat with memory & empathy |
| `/memory` | GET/POST | Cognitive memory operations |
| `/memory/ui` | GET | Memory visualization endpoint |
| `/agents` | GET/POST | Sub-agent management |
| `/agents/register` | POST | Create new specialized agents |
| `/agents/spawn` | POST | Spawn agent for async task |
| `/actions` | GET/POST | Action registry |
| `/actions/crawl` | POST | Auto-discover CLI tools |
| `/packages/search` | GET | Search Arch repos + AUR |
| `/packages/install` | POST | Install packages |
| `/sessions` | GET | List tmux sessions |
| `/sessions/execute` | POST | Execute command in tmux |
| `/emails` | GET/POST | Email query and sync |
| `/emails/sync` | POST | Sync email from gogcli/offlineimap |
| `/dashboard` | GET | System overview |
| `/heart` | GET | Health + empathy status |
| `/ingest` | POST | Ingest documents/memories |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        OpenAura                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────────┐  │
│   │   Client    │──▶│   FastAPI   │──▶│  LLM Gateway    │  │
│   │  (CLI/Web)  │   │   Gateway   │   │  (OpenRouter)   │  │
│   └─────────────┘   └─────────────┘   └─────────────────┘  │
│                             │                               │
│         ┌───────────────────┼───────────────────┐            │
│         ▼                   ▼                   ▼            │
│   ┌───────────┐      ┌──────────┐      ┌──────────────┐     │
│   │OpenMemory │      │  Agents  │      │ Action Reg   │     │
│   │ (SQLite)  │      │  Service │      │  (YAML)      │     │
│   └───────────┘      └──────────┘      └──────────────┘     │
│                             │                               │
│         ┌───────────────────┼───────────────────┐            │
│         ▼                   ▼                   ▼            │
│   ┌───────────┐      ┌──────────┐      ┌──────────────┐     │
│   │  Empathy  │      │  Email   │      │ Arch Linux   │     │
│   │  Engine   │      │  Service │      │ + AUR (yay)  │     │
│   └───────────┘      └──────────┘      └──────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Key Components:**
- **Base**: Arch Linux (Docker) with AUR support via yay
- **API**: FastAPI with async request handling
- **LLM Gateway**: OpenRouter (Claude, GPT-4, DeepSeek, Llama, etc.)
- **Memory**: OpenMemory with SQLite persistence
- **Empathy**: Real-time sentiment analysis and tone adaptation
- **Execution**: Tmux-based async command execution
- **Sub-agents**: Spawn specialized AIs with isolated contexts

---

## 🛠️ CLI Commands

The `openaur` CLI provides rich terminal interaction:

```bash
# Server management
openaur server start      # Start containers
openaur server stop       # Stop containers
openaur server logs       # View logs
openaur server status     # Check status

# Chat with memory
openaur chat              # Interactive chat mode
openaur chat "message"    # One-shot message

# Package management
openaur packages search <query>    # Search Arch + AUR
openaur packages install <name>    # Install package
openaur packages list              # List installed

# Action registry
openaur actions list               # List registered tools
openaur actions crawl <binary>   # Auto-discover docs
openaur actions show <name>        # Show tool details

# Agent management
openaur agents list                # List sub-agents
openaur agents spawn <id>          # Spawn agent for task

# System
openaur sessions                   # List tmux sessions
openaur test                     # Run health checks
openaur dashboard                # View system stats
```

---

## 🧪 Development

```bash
# Setup
make build

# Run with logs
make run-logs

# Shell into container
make shell

# View logs
make logs

# Reset database
make reset-db

# Lint & format
ruff check . && ruff format .
```

---

## ⚙️ Configuration

`.env` file:

```bash
# Required
OPENROUTER_API_KEY=your_key_here

# Optional
DEBUG=false                    # Enable debug logging
OPENMEMORY_DB_PATH=./data/openmemory.db
```

---

## 🤝 Contributing

We welcome contributions! See [AGENTS.md](AGENTS.md) for code style guidelines.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📈 Roadmap

- [ ] Web UI (React/Vue frontend)
- [ ] Multi-user support with authentication
- [ ] Plugin system for custom integrations
- [ ] Voice interface (Whisper + TTS)
- [ ] Mobile app companion
- [ ] Kubernetes deployment charts
- [ ] More email providers (Gmail API, Outlook)
- [ ] Home Assistant integration

---

## 🙏 Acknowledgments

- [OpenRouter](https://openrouter.ai/) - Unified LLM API
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Rich](https://github.com/Textualize/rich) - Terminal formatting
- [Arch Linux](https://archlinux.org/) - Best Linux distro
- [OpenMemory](https://github.com/yourusername/openmemory) - Cognitive memory layer

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 💬 Community & Support

- 🐛 [Report bugs](../../issues)
- 💡 [Request features](../../issues)
- 📖 [Documentation](../../wiki)
- 💬 [Discussions](../../discussions)

**Star ⭐ this repo if you find it useful!**
