# OpenAur - Personal AI Assistant Documentation

## Overview

OpenAur is a personal AI assistant that combines FastAPI backend, SvelteKit dashboard, and Arch Linux integration with powerful cognitive memory capabilities via OpenMemory.

## Features

- **🤖 AI Chat Interface** - Chat with OpenRouter LLMs (DeepSeek, Claude, etc.)
- **🧠 Cognitive Memory** - HMD2 architecture with SQLite fallback
- **📦 Package Management** - Search, install, remove Arch Linux packages
- **📋 Session Management** - Tmux-based persistent command execution
- **🎯 Action System** - Ingest CLI tools and register actions
- **💓 Health Monitoring** - Real-time heart status dashboard
- **🌐 Web Dashboard** - SvelteKit-based monitoring UI

## Quick Start

### 1. Start the Services

```bash
make run
```

Or with CLI:

```bash
openaur server start
```

### 2. Access the Dashboard

- **Dashboard**: http://localhost:8001
- **API**: http://localhost:8000
- **WebUI**: http://localhost:3000

### 3. Configure API Key

Your OpenRouter API key is already configured in `.env`:

```bash
OPENROUTER_API_KEY=your_api_key_here
```

## CLI Commands

### Server Management

```bash
openaur server start      # Start all containers
openaur server stop       # Stop all containers
openaur server restart    # Restart containers
openaur server status     # Show container status
openaur server logs       # View logs
openaur server shell      # Open container shell
```

### Chat

```bash
openaur chat "Hello, how are you?"
openaur chat              # Interactive mode
```

### Package Management

```bash
openaur packages search docker          # Search for packages
openaur packages install docker         # Install a package
openaur packages remove htop            # Remove a package
openaur packages cleanup                # Clean unused dependencies
```

### Memory Management

```bash
openaur ingest memory "Learned about Docker today" --tag learning --tag docker
openaur ingest status                   # Show ingestion status
```

### Action Ingestion

```bash
openaur ingest action git               # Ingest git documentation
openaur ingest action docker --depth 15 # Ingest with custom depth
openaur actions                         # List registered actions
```

### Sessions

```bash
openaur session list                    # List active sessions
openaur session kill <session_id>       # Kill a session
openaur session attach <session_name>   # Attach to tmux session
```

### System

```bash
openaur heart                           # Show heart status
openaur test                            # Run health tests
openaur --help                          # Show all commands
```

## Dashboard Features

### Overview Page
- Real-time memory statistics
- Heart status with pulse indicator
- Quick stats cards

### Memory Browser
- **Search**: Full-text search across memories
- **Filter by Type**: User queries, assistant responses, action learning, system
- **Filter by Tag**: Click any tag to filter
- **Edit Tags**: Click the tag icon to add/remove tags
- **Delete**: Click trash icon to remove memories
- **Export/Import**: Backup and restore memories as JSON

### Heart Status
- Physical health (database, services)
- Emotional state with mood visualization
- Version and timestamp info

### Sessions Monitor
- List active tmux sessions
- View command execution status

### Agents Monitor
- View running subagents
- Check task queue status

### Settings
- Toggle instant preview
- Enable/disable analytics
- Model selection

## API Endpoints

### Chat
- `POST /chat/` - Send a chat message

### Memory
- `GET /memory/stats` - Get memory statistics
- `POST /memory/store` - Store a memory
- `POST /memory/retrieve` - Search memories
- `DELETE /memory/{id}` - Delete a memory
- `PATCH /memory/{id}/tags` - Update memory tags
- `GET /memory/sectors` - List memory sectors

### Ingest
- `POST /ingest/action` - Ingest a CLI tool
- `POST /ingest/memory` - Ingest a memory
- `GET /ingest/status` - Get ingestion status

### Actions
- `GET /actions/` - List registered actions

### Packages
- `GET /packages/search?q={query}` - Search packages
- `POST /packages/install` - Install package
- `POST /packages/remove` - Remove package
- `POST /packages/cleanup` - Clean unused packages
- `GET /packages/installed` - List installed packages

### Sessions
- `GET /sessions/` - List active sessions
- `POST /sessions/create` - Create new session
- `GET /sessions/{id}` - Get session status
- `POST /sessions/{id}/kill` - Kill session
- `GET /sessions/{id}/output` - Get session output

### Heart
- `GET /heart/` - Get heart status
- `GET /health` - Health check

## Configuration

### Environment Variables

```bash
# Required
OPENROUTER_API_KEY=your_key_here

# Optional
OPENMEMORY_DB_PATH=./data/openmemory.db
DEBUG=false
DEFAULT_MODEL=deepseek/deepseek-chat
ENABLE_ANALYTICS=false
```

### Model Selection

Available models via OpenRouter:
- `deepseek/deepseek-chat` (default)
- `anthropic/claude-3.5-sonnet`
- `anthropic/claude-3-opus`
- `meta-llama/llama-3.1-70b`
- And more...

## Memory System Architecture

### HMD2 (Hierarchical Memory Decomposition)

The memory system uses a 5-sector architecture:

1. **Episodic** - Events, conversations, interactions
2. **Semantic** - Facts, knowledge, preferences  
3. **Procedural** - How-to, actions, steps
4. **Emotional** - Feelings, sentiment, mood
5. **Reflective** - Insights, summaries, learnings

### Memory Lifecycle

1. **Store** → Automatic sector classification
2. **Retrieve** → Composite scoring (similarity + salience + recency)
3. **Reinforce** → Boost salience on successful recall
4. **Decay** → Unused memories fade over time
5. **Consolidate** → Important memories move to long-term

## Troubleshooting

### Container Won't Start

```bash
docker-compose down
make clean
make build
make run
```

### API Connection Errors

```bash
# Check if container is running
docker ps | grep openaura

# Check logs
docker logs openaura

# Restart
docker-compose restart openaura
```

### Dashboard Not Loading

```bash
# Rebuild dashboard
docker-compose build openaur-dashboard
docker-compose up -d openaur-dashboard
```

### Database Issues

```bash
# Reset database (WARNING: destroys all data)
docker exec openaura rm /home/aura/app/data/openaura.db
docker-compose restart openaura
```

## Development

### Adding New CLI Commands

Edit `src/cli.py` and add Typer commands:

```python
@app.command()
def my_command():
    """My new command."""
    console.print("Hello!")
```

### Adding API Routes

1. Create route file in `src/routes/`
2. Add router to `src/main.py`
3. Implement Pydantic models in `src/models/schemas.py`

### Dashboard Development

Dashboard code is in `apps/dashboard/`:
- SvelteKit + TypeScript
- Tailwind CSS for styling
- Custom neon theme

Build locally:
```bash
cd apps/dashboard
npm install
npm run dev
```

## Security Notes

- API key stored in `.env` (not committed)
- Container runs as non-root user
- All actions are sandboxed in Docker
- Session data stored in SQLite
- No external network access required

## Backup & Restore

### Export Memories

Via Dashboard:
1. Go to Memory Browser
2. Click "Export" button
3. Download JSON file

Via CLI:
```bash
# (coming in future release)
```

### Import Memories

Via Dashboard:
1. Go to Memory Browser
2. Click "Import" button
3. Paste JSON content

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                      User Layer                         │
│  ┌──────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ CLI      │  │ Dashboard    │  │ Open WebUI      │  │
│  │ (Typer)  │  │ (SvelteKit)  │  │ (3000)          │  │
│  └────┬─────┘  └──────┬───────┘  └────────┬────────┘  │
└───────┼───────────────┼───────────────────┼───────────┘
        │               │                   │
        └───────────────┴───────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│                   API Layer (8000)                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────────┐  │
│  │ Chat    │ │ Memory  │ │ Actions │ │ Packages     │  │
│  │ Routes  │ │ Routes  │ │ Routes  │ │ Routes       │  │
│  └────┬────┘ └────┬────┘ └────┬────┘ └──────┬───────┘  │
└───────┼───────────┼───────────┼────────────┼──────────┘
        │           │           │            │
┌───────▼───────────▼───────────▼────────────▼──────────┐
│                 Services Layer                         │
│  ┌───────────┐ ┌──────────┐ ┌─────────────────────┐   │
│  │ OpenRouter│ │ OpenMemory│ │ Package Manager   │   │
│  │ Gateway   │ │ (HMD2)    │ │ (yay/pacman)      │   │
│  └─────┬─────┘ └────┬─────┘ └─────────┬───────────┘   │
└────────┼────────────┼───────────────────┼───────────────┘
         │            │                   │
┌────────▼────────────▼───────────────────▼───────────────┐
│                   Data Layer                             │
│  ┌────────────────┐  ┌──────────────────────────────┐   │
│  │ SQLite (app.db)│  │ Tmux Sessions                │   │
│  │ - Memories     │  │ - Persistent execution       │   │
│  │ - Sessions     │  └──────────────────────────────┘   │
│  │ - Actions      │                                      │
│  │ - Packages     │                                      │
│  └────────────────┘                                      │
└────────────────────────────────────────────────────────┘
```

## Support

- **Issues**: Report at https://github.com/anomalyco/openaur/issues
- **Documentation**: This file
- **CLI Help**: `openaur --help`

## License

MIT License - See LICENSE file for details
