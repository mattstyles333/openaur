# AGENTS.md — openaur Code Repository Standards

## Overview
Python FastAPI application — Personal AI assistant with Arch Linux integration. Uses Typer CLI, OpenRouter LLMs, OpenMemory cognitive layer.

## Build/Lint/Test Commands

**Docker Build:**
```bash
make build          # Build containers (--no-cache)
make run            # Start services (-d)
make run-logs       # Start with attached logs
make stop           # Stop services
make clean          # Full cleanup + remove image
```

**Testing (Manual/API-based):**
```bash
make test           # Health check via curl
make crawl BINARY=git       # Register CLI tool
make search QUERY=docker    # Search packages
make install PACKAGE=htop   # Install package
make chat MSG="Hello"       # Chat with assistant
```

**Lint/Format:**
```bash
ruff check .        # Lint
ruff format .       # Format
ruff check --fix .  # Auto-fix issues
```

**Type Check:**
```bash
mypy src/           # Type checking (optional)
```

## Code Style Guidelines

### Imports (Strict Order)
```python
# 1. Standard library
import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

# 2. Third-party (FastAPI, Pydantic, etc.)
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine

# 3. Local (absolute imports ONLY — never relative)
from src.models.schemas import ChatRequest
from src.services.gateway import OpenRouterGateway
```

### Naming Conventions
- **Files:** snake_case.py
- **Functions:** snake_case()
- **Classes:** PascalCase
- **Constants:** UPPER_CASE (module-level)
- **Private:** _leading_underscore
- **Type Variables:** PascalCase

### Type Hints
Required on all public functions:
```python
def process_chat(message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    ...
```

### Error Handling
**Routes:** Raise HTTPException
```python
from fastapi import HTTPException

@router.post("/action")
async def create_action(request: ActionRequest):
    try:
        result = await processor.run(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Services:** Log and return safe defaults
```python
import logging

logger = logging.getLogger(__name__)

def search_packages(query: str) -> List[Dict]:
    try:
        # ... logic ...
    except Exception as e:
        logger.error(f"Error searching packages: {e}")
        return []
```

### FastAPI Patterns
- Use `Depends()` for DB sessions and shared resources
- Use Pydantic models for request/response validation
- Use APIRouter for modular routes
- Implement lifespan context manager for startup/shutdown

### Line Length & Formatting
- **Max 100 characters** per line
- **Docstrings:** Required on public classes/functions
- **Comments:** Brief and helpful, or none
- **No trailing whitespace**

### Project Structure
```
src/
  main.py           # FastAPI entry + lifespan
  cli.py            # Typer CLI commands
  routes/           # API endpoints (one per domain)
  services/         # Business logic
  models/           # Pydantic schemas + SQLAlchemy
  utils/            # Shared utilities
tests/              # Test files (currently empty)
actions/manifests/  # YAML action registry
data/               # SQLite database (runtime)
```

### Key Principles
- **Simplicity over cleverness** — readable > concise
- **Short files (<300 lines), short functions (<50 lines)**
- **One responsibility per file/function**
- **Absolute imports only** — no `from . import`
- **Type hints on public APIs**
- **Docker-first:** All services run in containers
- **No .old, .bak, .tmp files**
- **No commented-out code blocks**

### Environment
- Arch Linux base (Docker)
- FastAPI + Uvicorn on port 8000
- SQLite database in data/
- OpenRouter for LLM calls
- OpenMemory for cognitive layer
