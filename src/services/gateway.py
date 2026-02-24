import httpx
import os
from typing import Optional, List, Dict


class OpenRouterGateway:
    """OpenRouter API gateway for LLM requests."""

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")

    async def chat(
        self,
        message: str,
        system_prompt: str = "You are a helpful assistant.",
        session_id: Optional[str] = None,
    ) -> Dict:
        """Send chat request to OpenRouter."""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://openaura.local",
            "X-Title": "OpenAura",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": message})

        payload = {"model": self.model, "messages": messages}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0,
            )

            if response.status_code != 200:
                raise Exception(f"OpenRouter error: {response.text}")

            data = response.json()

            return {
                "content": data["choices"][0]["message"]["content"],
                "model": data.get("model"),
                "session_id": session_id or f"session_{os.urandom(4).hex()}",
                "usage": data.get("usage", {}),
            }

    async def list_models(self) -> List[Dict]:
        """List available models."""
        headers = {"Authorization": f"Bearer {self.api_key}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/models", headers=headers)

            if response.status_code != 200:
                raise Exception(f"Failed to fetch models: {response.text}")

            return response.json().get("data", [])
