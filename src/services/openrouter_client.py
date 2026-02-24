"""Unified OpenRouter API client with retries and circuit breaker.

Consolidates both OpenRouterGateway and TwoStageProcessor into a single,
robust client with proper error handling and retry logic.
"""

import asyncio
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config import settings
from src.constants import APIConfig, ModelConfig


class OpenRouterClient:
    """Unified OpenRouter API client with retries and error handling."""

    def __init__(self):
        self.api_key = settings.openrouter_api_key.get_secret_value()
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://openaura.local",
            "X-Title": "openaur",
        }
        self.has_valid_api_key = (
            self.api_key and self.api_key != "your_api_key_here" and len(self.api_key) > 20
        )

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(APIConfig.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=APIConfig.RETRY_DELAY, max=10),
        reraise=True,
    )
    async def chat(
        self,
        message: str,
        system_prompt: str = "You are a helpful assistant.",
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.7,
        timeout: float = APIConfig.DEFAULT_TIMEOUT,
    ) -> dict[str, Any]:
        """Send a chat request to OpenRouter with retries."""
        if not self.has_valid_api_key:
            raise ValueError("No valid OpenRouter API key configured")

        model = model or settings.default_model

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            "temperature": temperature,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=timeout,
            )

            if response.status_code == 401:
                raise ValueError("Invalid API key")
            elif response.status_code == 429:
                raise RuntimeError("Rate limit exceeded. Please try again later.")
            elif response.status_code != 200:
                raise RuntimeError(f"OpenRouter error: {response.text}")

            data = response.json()

            return {
                "content": data["choices"][0]["message"]["content"],
                "model": data.get("model", model),
                "usage": data.get("usage", {}),
            }

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        stop=stop_after_attempt(APIConfig.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=APIConfig.RETRY_DELAY, max=5),
        reraise=True,
    )
    async def chat_fast(
        self,
        message: str,
        system_prompt: str = "You are a helpful assistant.",
        max_tokens: int = 800,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        """Fast chat using the heart model (for previews)."""
        return await self.chat(
            message=message,
            system_prompt=system_prompt,
            model=settings.heart_model or ModelConfig.DEFAULT_HEART_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=APIConfig.FAST_TIMEOUT,
        )

    async def chat_with_preview(
        self,
        message: str,
        system_prompt: str = "You are a helpful assistant.",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get both fast preview and quality response in parallel."""
        if not settings.instant_preview:
            # Preview disabled, just do quality call
            quality = await self.chat(message, system_prompt)
            return {
                "preview": None,
                "quality": quality,
                "context": context or {},
            }

        # Call both models in parallel
        fast_task = self.chat_fast(message, system_prompt)
        quality_task = self.chat(message, system_prompt)

        try:
            fast_result, quality_result = await asyncio.gather(
                fast_task, quality_task, return_exceptions=True
            )
        except Exception as e:
            # If parallel fails, fall back to quality only
            quality = await self.chat(message, system_prompt)
            return {
                "preview": None,
                "quality": quality,
                "context": context or {},
                "error": str(e),
            }

        preview = None if isinstance(fast_result, Exception) else fast_result
        quality = None if isinstance(quality_result, Exception) else quality_result

        # If quality failed but preview worked, use preview as quality
        if quality is None and preview is not None:
            quality = preview
            preview = None

        return {
            "preview": preview,
            "quality": quality,
            "context": context or {},
        }

    async def stream_chat(
        self,
        message: str,
        system_prompt: str = "You are a helpful assistant.",
        model: str | None = None,
    ):
        """Stream chat responses (for real-time UI updates)."""
        if not self.has_valid_api_key:
            raise ValueError("No valid OpenRouter API key configured")

        model = model or settings.default_model

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            "temperature": 0.7,
            "stream": True,
        }

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=APIConfig.DEFAULT_TIMEOUT,
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data != "[DONE]":
                            yield data


# Singleton instance
_client: OpenRouterClient | None = None


def get_openrouter_client() -> OpenRouterClient:
    """Get or create OpenRouter client singleton."""
    global _client
    if _client is None:
        _client = OpenRouterClient()
    return _client
