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

from src.services.analysis_engine import analyze_and_respond, get_analysis_engine
from src.services.context_manager import preload_openaura_context

router = APIRouter()

# Track if context has been preloaded
_context_preloaded = False


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


class APIKeyRequest(BaseModel):
    api_key: str


def has_valid_api_key() -> bool:
    """Check if OpenRouter API key is configured."""
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    return bool(api_key and api_key != "your_openrouter_api_key_here" and len(api_key) > 20)


def ensure_context_loaded():
    """Ensure openaur context is preloaded in memory."""
    global _context_preloaded
    if not _context_preloaded:
        count = preload_openaura_context()
        print(f"✓ Pre-loaded {count} context items into OpenMemory")
        _context_preloaded = True


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


@router.post("/config/api-key")
async def save_api_key(request: APIKeyRequest):
    """Save OpenRouter API key to environment."""
    if not request.api_key or len(request.api_key) < 20:
        raise HTTPException(status_code=400, detail="Invalid API key format")

    # Update environment variable
    os.environ["OPENROUTER_API_KEY"] = request.api_key

    # Reinitialize the analysis engine with new key
    from src.services.two_stage_processor import get_processor

    processor = get_processor()
    processor.api_key = request.api_key
    processor.headers["Authorization"] = f"Bearer {request.api_key}"
    processor.has_valid_api_key = True

    return {"status": "success", "message": "API key saved successfully"}


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

        # Check if user is providing an API key
        if not has_valid_api_key():
            # Check if the message contains an API key (sk-or-v1-...)
            import re

            msg_stripped = user_message.strip()

            # Try to extract API key from message (handles pasted keys with extra text)
            api_key_match = re.search(r"(sk-or-v1-[a-f0-9]+)", msg_stripped)

            if api_key_match:
                api_key = api_key_match.group(1)
                if len(api_key) > 50:
                    # Save the API key
                    os.environ["OPENROUTER_API_KEY"] = api_key
                    from src.services.two_stage_processor import get_processor

                    processor = get_processor()
                    processor.api_key = api_key
                    processor.headers["Authorization"] = f"Bearer {api_key}"
                    processor.has_valid_api_key = True

                    return OpenAIChatResponse(
                        id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
                        created=int(datetime.utcnow().timestamp()),
                        model=request.model,
                        choices=[
                            OpenAIChoice(
                                index=0,
                                message=OpenAIMessage(
                                    role="assistant",
                                    content="✅ API key saved! You can now start chatting.",
                                ),
                                finish_reason="stop",
                            )
                        ],
                        usage=OpenAIUsage(),
                    )

            # Return helpful message asking for API key
            setup_message = """⚠️ **OpenRouter API Key Required**

To use openaur's AI features, you need to configure your OpenRouter API key.

**How to get an API key:**
1. Visit https://openrouter.ai/keys
2. Create a free account
3. Generate an API key
4. **Paste it directly into chat**

**Your API key will be used for:**
- Fast sentiment/intent analysis
- Quality AI responses
- Memory processing

Please paste your API key (it should start with `sk-or-v1-`) to continue."""

            choices = [
                OpenAIChoice(
                    index=0,
                    message=OpenAIMessage(role="assistant", content=setup_message),
                    finish_reason="stop",
                )
            ]

            return OpenAIChatResponse(
                id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
                created=int(datetime.utcnow().timestamp()),
                model=request.model,
                choices=choices,
                usage=OpenAIUsage(),
            )

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
