"""
OpenAI-compatible API endpoints for Open WebUI integration

Enhanced with two-stage processing:
1. Fast model (gpt-oss-20b:nitro) for sentiment/action/memory analysis
2. Quality model (openrouter/auto) for final response
3. Thinking/analysis visible to user in conversation
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
import os

from src.services.analysis_engine import analyze_and_respond
from src.services.context_manager import preload_openaura_context

router = APIRouter()

# Track if context has been preloaded
_context_preloaded = False


def ensure_context_loaded():
    """Ensure OpenAura context is preloaded in memory."""
    global _context_preloaded
    if not _context_preloaded:
        count = preload_openaura_context()
        print(f"✓ Pre-loaded {count} context items into OpenMemory")
        _context_preloaded = True


# OpenAI-compatible models
class OpenAIMessage(BaseModel):
    role: str
    content: str


class OpenAIChatRequest(BaseModel):
    model: str = "openaura/default"
    messages: List[OpenAIMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False


class OpenAIDelta(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None


class OpenAIChoice(BaseModel):
    index: int = 0
    message: Optional[OpenAIMessage] = None
    delta: Optional[OpenAIDelta] = None
    finish_reason: Optional[str] = None


class OpenAIUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class OpenAIChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[OpenAIChoice]
    usage: OpenAIUsage


class OpenAIModel(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str = "openaura"


class OpenAIModelsResponse(BaseModel):
    object: str = "list"
    data: List[OpenAIModel]


@router.get("/models")
async def list_openai_models() -> OpenAIModelsResponse:
    """List available models in OpenAI-compatible format."""
    return OpenAIModelsResponse(
        data=[
            OpenAIModel(
                id="openaura/default",
                created=int(datetime.utcnow().timestamp()),
            ),
            OpenAIModel(
                id="openaura/claude-3.5-sonnet",
                created=int(datetime.utcnow().timestamp()),
            ),
            OpenAIModel(
                id="openaura/gpt-4o",
                created=int(datetime.utcnow().timestamp()),
            ),
        ]
    )


@router.post("/chat/completions")
async def openai_chat(request: OpenAIChatRequest) -> OpenAIChatResponse:
    """OpenAI-compatible chat with two-stage processing and visible thinking."""
    try:
        # Ensure context is preloaded
        ensure_context_loaded()

        # Extract the last user message
        user_message = ""
        for msg in request.messages:
            if msg.role == "user":
                user_message = msg.content

        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found")

        # Generate session ID
        session_id = f"session_{os.urandom(4).hex()}"

        # Two-stage processing: fast analysis + quality response
        result = await analyze_and_respond(user_message, session_id)

        # Build choices array with thinking visible as first assistant message
        choices = []

        # First choice: thinking + response (for non-streaming)
        thinking_content = result["thinking"]
        response_content = result["response"]

        # Combine thinking and response
        full_content = f"{thinking_content}\n\n---\n\n{response_content}"

        choices.append(
            OpenAIChoice(
                index=0,
                message=OpenAIMessage(role="assistant", content=full_content),
                finish_reason="stop",
            )
        )

        return OpenAIChatResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
            created=int(datetime.utcnow().timestamp()),
            model=request.model,
            choices=choices,
            usage=OpenAIUsage(
                prompt_tokens=result.get("usage", {}).get("prompt_tokens", 0),
                completion_tokens=result.get("usage", {}).get("completion_tokens", 0),
                total_tokens=result.get("usage", {}).get("total_tokens", 0),
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/embeddings")
async def openai_embeddings():
    """OpenAI-compatible embeddings endpoint (placeholder)."""
    # Return empty embeddings for now
    return {
        "object": "list",
        "data": [],
        "model": "text-embedding-3-small",
        "usage": {"prompt_tokens": 0, "total_tokens": 0},
    }
