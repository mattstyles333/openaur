"""Configuration routes - API key management and settings.

Provides endpoints for managing API keys and system configuration.
"""

import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class ApiKeyRequest(BaseModel):
    api_key: str


class ModelsRequest(BaseModel):
    chat_model: str
    heart_model: str
    instant_preview: bool = False


@router.get("/status")
async def get_config_status():
    """Check configuration status."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    has_key = api_key is not None and len(api_key) > 10 if api_key else False

    chat_model = os.getenv("CHAT_MODEL", "openrouter/auto")
    heart_model = os.getenv("HEART_MODEL", "openai/gpt-oss-20b:nitro")
    instant_preview = os.getenv("INSTANT_PREVIEW", "false").lower() == "true"

    return {
        "has_api_key": has_key,
        "message": "API key configured" if has_key else "API key not configured",
        "chat_model": chat_model,
        "heart_model": heart_model,
        "instant_preview": instant_preview,
    }


@router.post("/api-key")
async def save_api_key(request: ApiKeyRequest):
    """Save OpenRouter API key to environment."""
    if not request.api_key or len(request.api_key) < 20:
        raise HTTPException(
            status_code=400, detail="Invalid API key. Must be at least 20 characters."
        )

    # Validate key format (should start with sk-or-v1-)
    if not request.api_key.startswith("sk-or-v1-"):
        raise HTTPException(
            status_code=400, detail="Invalid API key format. Must start with 'sk-or-v1-'"
        )

    # Set in environment for current process
    os.environ["OPENROUTER_API_KEY"] = request.api_key

    # Try to persist to .env file
    try:
        env_path = "/home/aura/app/.env"
        env_lines = []
        key_set = False

        # Read existing .env if it exists
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.startswith("OPENROUTER_API_KEY="):
                        env_lines.append(f"OPENROUTER_API_KEY={request.api_key}\n")
                        key_set = True
                    else:
                        env_lines.append(line)

        # Add key if not found
        if not key_set:
            env_lines.append(f"OPENROUTER_API_KEY={request.api_key}\n")

        # Write back
        with open(env_path, "w") as f:
            f.writelines(env_lines)

    except Exception as e:
        # Log error but don't fail - env var is set for current session
        print(f"Warning: Could not persist API key to .env file: {e}")

    return {
        "success": True,
        "message": "API key saved successfully",
    }


@router.get("/api-key")
async def get_api_key_status():
    """Get API key status without exposing the key."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    has_key = api_key is not None and len(api_key) > 10 if api_key else False

    # Mask the key for display
    masked_key = None
    if api_key and len(api_key) > 10:
        masked_key = api_key[:6] + "..." + api_key[-4:]

    return {
        "has_api_key": has_key,
        "masked_key": masked_key,
    }


@router.post("/models")
async def save_models(request: ModelsRequest):
    """Save model preferences."""
    # Validate models are not empty
    if not request.chat_model or not request.heart_model:
        raise HTTPException(status_code=400, detail="Both chat_model and heart_model are required")

    # Set in environment for current process
    os.environ["CHAT_MODEL"] = request.chat_model
    os.environ["HEART_MODEL"] = request.heart_model
    os.environ["INSTANT_PREVIEW"] = "true" if request.instant_preview else "false"

    # Try to persist to .env file
    try:
        env_path = "/home/aura/app/.env"
        env_lines = []
        chat_set = False
        heart_set = False
        instant_preview_set = False

        # Read existing .env if it exists
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.startswith("CHAT_MODEL="):
                        env_lines.append(f"CHAT_MODEL={request.chat_model}\n")
                        chat_set = True
                    elif line.startswith("HEART_MODEL="):
                        env_lines.append(f"HEART_MODEL={request.heart_model}\n")
                        heart_set = True
                    elif line.startswith("INSTANT_PREVIEW="):
                        env_lines.append(
                            f"INSTANT_PREVIEW={'true' if request.instant_preview else 'false'}\n"
                        )
                        instant_preview_set = True
                    else:
                        env_lines.append(line)

        # Add settings if not found
        if not chat_set:
            env_lines.append(f"CHAT_MODEL={request.chat_model}\n")
        if not heart_set:
            env_lines.append(f"HEART_MODEL={request.heart_model}\n")
        if not instant_preview_set:
            env_lines.append(f"INSTANT_PREVIEW={'true' if request.instant_preview else 'false'}\n")

        # Write back
        with open(env_path, "w") as f:
            f.writelines(env_lines)

    except Exception as e:
        # Log error but don't fail - env vars are set for current session
        print(f"Warning: Could not persist models to .env file: {e}")

    return {
        "success": True,
        "message": "Model settings saved successfully",
        "chat_model": request.chat_model,
        "heart_model": request.heart_model,
        "instant_preview": request.instant_preview,
    }


@router.get("/models")
async def get_models():
    """Get current model settings."""
    chat_model = os.getenv("CHAT_MODEL", "openrouter/auto")
    heart_model = os.getenv("HEART_MODEL", "openai/gpt-oss-20b:nitro")
    instant_preview = os.getenv("INSTANT_PREVIEW", "false").lower() == "true"

    return {
        "chat_model": chat_model,
        "heart_model": heart_model,
        "instant_preview": instant_preview,
    }
