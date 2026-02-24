"""
OpenAI-compatible API endpoints for Open WebUI integration

Enhanced with two-stage processing:
1. Fast model (gpt-oss-20b:nitro) for sentiment/action/memory analysis
2. Quality model (openrouter/auto) for final response
3. Thinking/analysis visible to user in conversation
"""

import os
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.services.analysis_engine import analyze_and_respond
from src.services.context_manager import preload_openaura_context

router = APIRouter()

# Track if context has been preloaded
_context_preloaded = False


class OpenAIMessage(BaseModel):
    role: str
    content: str


class OpenAIChatRequest(BaseModel):
    model: str = "openaura/default"
    messages: list[OpenAIMessage]
    temperature: float | None = 0.7
    max_tokens: int | None = None
    stream: bool = False
    # Control whether to show analysis/thinking in output
    show_thinking: bool = False
    # Force quick mode (bypass OpenRouter for simple queries)
    quick_mode: bool | None = None


class OpenAIDelta(BaseModel):
    role: str | None = None
    content: str | None = None


class OpenAIChoice(BaseModel):
    index: int = 0
    message: OpenAIMessage | None = None
    delta: OpenAIDelta | None = None
    finish_reason: str | None = None


class OpenAIUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class OpenAIChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[OpenAIChoice]
    usage: OpenAIUsage


class OpenAIModel(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str = "openaura"


class OpenAIModelsResponse(BaseModel):
    object: str = "list"
    data: list[OpenAIModel]


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


@router.get("/config/status")
async def get_config_status():
    """Get current configuration status."""
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    has_valid_key = api_key and api_key != "your_openrouter_api_key_here" and len(api_key) > 20

    return {
        "has_api_key": has_valid_key,
        "api_key_preview": api_key[:10] + "..." if has_valid_key else None,
    }


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

        # Determine quick mode: either explicitly set or auto-detect for simple queries
        use_quick_mode = (
            request.quick_mode if request.quick_mode is not None else True
        )  # Default to quick mode

        # Two-stage processing: fast analysis + quality response
        result = await analyze_and_respond(
            user_message,
            session_id,
            use_quick_mode=use_quick_mode,
            include_thinking=request.show_thinking,
        )

        # Build response content
        if request.show_thinking and result["thinking"]:
            full_content = f"{result['thinking']}\n\n---\n\n{result['response']}"
        else:
            full_content = result["response"]

        choices = [
            OpenAIChoice(
                index=0,
                message=OpenAIMessage(role="assistant", content=full_content),
                finish_reason="stop",
            )
        ]

        return OpenAIChatResponse(
            id=f"chatcmpl-{uuid.uuid4().hex[:8]}",
            created=int(datetime.utcnow().timestamp()),
            model=result.get("model", request.model),
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
