import os

from fastapi import APIRouter, HTTPException

from src.models.schemas import ChatRequest, ChatResponse
from src.services.empathy import EmpathyEngine
from src.services.gateway import OpenRouterGateway
from src.services.two_stage_processor import get_processor
from src.utils.yaml_registry import YamlRegistry

router = APIRouter()
gateway = OpenRouterGateway()
empathy = EmpathyEngine()


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint with optional Instant Preview."""
    try:
        # Check if Instant Preview is enabled
        instant_preview = os.getenv("INSTANT_PREVIEW", "false").lower() == "true"

        # 1. Analyze sentiment/emotion
        emotional_state = empathy.analyze(request.message)

        # 2. Retrieve relevant tools from registry (2-level tree)
        yaml_reg = YamlRegistry()
        relevant_tools = []

        # Simple keyword matching for now
        message_lower = request.message.lower()
        for binary in ["git", "docker", "curl", "glab"]:
            if binary in message_lower:
                tree = yaml_reg.load_action(binary)
                if tree:
                    relevant_tools.append({"binary": binary, "tree": tree.get("tree", {})})

        # 3. Build Arch Linux context-aware system prompt
        arch_context = """You are openaur, an AI assistant running in an Arch Linux environment.

CRITICAL CONTEXT - This is Arch Linux:
- Package manager: pacman (official repos) and yay (AUR helper)
- To install packages: pacman -S <package> OR yay -S <aur-package>
- User has passwordless sudo access
- System runs in a Docker container with tmux for session management

ABOUT OPENAURA CLI:
openaur has its own CLI tool called 'openaur' located at /home/laptop/Documents/code/openaur/openaur
Available commands:
  openaur heart           - Health check with empathy
  openaur chat            - Interactive chat interface
  openaur ingest action   - Ingest CLI tools (e.g., openaur ingest action git)
  openaur packages        - Package management (search, install, cleanup)
  openaur sessions        - Tmux session management
  openaur test            - Run tests

Available CLI tools in registry:
"""
        # Add registered tools to context
        for tool in relevant_tools:
            arch_context += f"- {tool['binary']}: action registry available\n"

        base_prompt = (
            arch_context
            + """
When asked about installing software:
1. Check if it's in official repos: pacman -Ss <package>
2. If not found, use AUR via yay: yay -S <package>
3. For 1Password CLI specifically: yay -S 1password (AUR package)
4. NEVER give Ubuntu/Windows instructions

Always prefer Arch-specific solutions."""
        )

        system_prompt = empathy.adapt_prompt(
            base_prompt=base_prompt,
            emotional_state=emotional_state,
            tools=relevant_tools,
        )

        # 4. Call AI (with or without Instant Preview)
        if instant_preview:
            # Get both fast preview and quality response
            processor = get_processor()
            result = await processor.chat_with_preview(
                user_message=request.message,
                system_prompt=system_prompt,
                context={"sentiment": emotional_state},
            )

            # Check for error
            if result.get("error"):
                print(f"Chat with preview error: {result['error']}")
                # Fall back to standard chat
                response = await gateway.chat(
                    message=request.message,
                    system_prompt=system_prompt,
                    session_id=request.session_id,
                )
                return ChatResponse(
                    response=response["content"],
                    session_id=request.session_id or response["session_id"],
                    tools_used=[t["binary"] for t in relevant_tools],
                    emotional_adaptation=emotional_state.get("sentiment"),
                    preview_used=False,
                )

            # Format response with both preview and quality
            # FIX: Handle None values properly
            preview_data = result.get("preview") or {}
            quality_data = result.get("quality") or {}
            preview_content = preview_data.get("content", "")
            quality_content = quality_data.get("content", "")

            # If quality is empty but preview exists, use preview as quality
            if not quality_content and preview_content:
                quality_content = preview_content
                preview_content = ""

            # Combine responses: preview shown as draft, then quality
            if preview_content and quality_content and preview_content != quality_content:
                combined_response = f"*{preview_content}*\n\n---\n\n{quality_content}"
                preview_used = True
            elif quality_content:
                combined_response = quality_content
                preview_used = True
            elif preview_content:
                combined_response = preview_content
                preview_used = True
            else:
                # Both empty - fallback
                response = await gateway.chat(
                    message=request.message,
                    system_prompt=system_prompt,
                    session_id=request.session_id,
                )
                combined_response = response["content"]
                preview_used = False

            return ChatResponse(
                response=combined_response,
                session_id=request.session_id or f"session_{os.urandom(4).hex()}",
                tools_used=[t["binary"] for t in relevant_tools],
                emotional_adaptation=emotional_state.get("sentiment"),
                preview_used=preview_used,
            )
        else:
            # Standard single-model response
            response = await gateway.chat(
                message=request.message,
                system_prompt=system_prompt,
                session_id=request.session_id,
            )

            return ChatResponse(
                response=response["content"],
                session_id=request.session_id or response["session_id"],
                tools_used=[t["binary"] for t in relevant_tools],
                emotional_adaptation=emotional_state.get("sentiment"),
                preview_used=False,
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def list_models():
    """List available models from OpenRouter."""
    try:
        models = await gateway.list_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
