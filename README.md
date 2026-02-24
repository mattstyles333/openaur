# OpenAura 🐧

Personal AI Assistant with Arch Linux Action Registry

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)

## Features

- 🤖 **AI Gateway** - FastAPI proxy to OpenRouter with multiple LLM support
- 🧠 **Cognitive Memory** - OpenMemory for contextual learning across sessions
- 💬 **Empathy Engine** - Emotional adaptation based on sentiment analysis
- 🐧 **Arch Linux Integration** - Native AUR support via `aura-pkg-add`
- 📦 **Package Management** - Search and install official + AUR packages
- 🔧 **Action Registry** - Auto-discover CLI tools with BFS documentation crawling
- ⚡ **Async Execution** - Tmux-based non-blocking command execution
- 🌐 **OpenAI Compatible** - Drop-in replacement for OpenAI API endpoints

## Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenRouter API key ([get one free](https://openrouter.ai/keys))

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/openaura.git
cd openaura

# Copy environment template and add your API key
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY

# Build and run
docker-compose up -d

# Verify it's running
make test
```

### Usage

```bash
# Crawl a CLI tool to add it to the registry
make crawl BINARY=git

# Search for packages
make search QUERY=docker

# Install a package
make install PACKAGE=htop

# Chat with the assistant
make chat MSG="What can you help me with?"
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/chat/completions` | POST | OpenAI-compatible chat |
| `/v1/models` | GET | OpenAI-compatible models list |
| `/chat` | POST | Enhanced chat with memory |
| `/packages/search` | GET | Search Arch packages |
| `/packages/install` | POST | Install packages |
| `/actions` | POST | Register CLI tools |
| `/memory` | GET/POST | Cognitive memory layer |
| `/heart` | GET | Health + empathy status |

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Client    │────▶│   FastAPI    │────▶│  OpenRouter │
│  (Web UI)   │     │   Gateway    │     │   (LLMs)    │
└─────────────┘     └──────────────┘     └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  OpenMemory  │
                     │   (SQLite)   │
                     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ Arch Linux   │
                     │ + AUR (yay)  │
                     └──────────────┘
```

- **Base**: Arch Linux (Docker) with AUR support
- **Gateway**: FastAPI → OpenRouter (Claude, GPT-4, DeepSeek, etc.)
- **Memory**: OpenMemory + SQLite for persistent context
- **Execution**: Tmux sessions for async commands
- **Packages**: yay for AUR + official repos

## Development

```bash
# Build locally
make build

# Run with attached logs
make run-logs

# Shell into container
make shell

# View logs
make logs

# Reset database
make reset-db
```

### Project Structure

```
.
├── src/
│   ├── main.py           # FastAPI app entry
│   ├── cli.py            # Typer CLI
│   ├── routes/           # API endpoints
│   ├── services/         # Business logic
│   └── models/           # Database + schemas
├── actions/manifests/    # YAML tool registry
├── data/                 # SQLite database
├── tests/                # Test suite
├── Dockerfile            # Arch Linux image
└── docker-compose.yml    # Services orchestration
```

## Configuration

Create a `.env` file:

```bash
# Required
OPENROUTER_API_KEY=your_key_here

# Optional
DEBUG=false
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure your code follows the project's style guidelines (see [AGENTS.md](AGENTS.md)).

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- [OpenRouter](https://openrouter.ai/) - Unified LLM API
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Arch Linux](https://archlinux.org/) - The best Linux distro

## Support

- 🐛 [Report bugs](../../issues)
- 💡 [Request features](../../issues)
- 📖 [Read the docs](https://github.com/yourusername/openaura/wiki)
