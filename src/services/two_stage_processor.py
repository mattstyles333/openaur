"""Two-stage LLM processing for openaur.

Uses fast/cheap model (gpt-oss-20b:nitro) for preprocessing tasks:
- Intent analysis
- Action detection
- Memory retrieval
- Sentiment analysis
- Quick preview responses (when Instant Preview enabled)

Then uses quality model (openrouter/auto) for final response.
"""

import asyncio
import os
from typing import Any

import httpx


class TwoStageProcessor:
    """Two-stage LLM processor for cost/performance optimization."""

    # Quality model for final response
    QUALITY_MODEL = "openrouter/auto"

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        # Fast model for preprocessing (empathy/analysis) - can be configured
        self.fast_model = os.getenv("HEART_MODEL", "openai/gpt-oss-20b:nitro")
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://openaura.local",
            "X-Title": "openaur",
        }
        # Check if API key is valid (not placeholder)
        self.has_valid_api_key = (
            self.api_key
            and self.api_key != "your_openrouter_api_key_here"
            and len(self.api_key) > 20
        )

    async def _call_fast(self, system_prompt: str, user_message: str) -> str:
        """Call fast model for quick analysis."""
        # Skip if no valid API key - return generic response
        if not self.has_valid_api_key:
            # Return basic analysis based on simple heuristics
            return self._fallback_analysis(system_prompt, user_message)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        payload = {
            "model": self.fast_model,
            "messages": messages,
            "max_tokens": 500,  # Keep it short and fast
            "temperature": 0.3,  # Lower temp for more consistent analysis
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=30.0,
                )

                if response.status_code != 200:
                    print(f"Fast model error: {response.text}")
                    return self._fallback_analysis(system_prompt, user_message)

                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Fast model exception: {e}")
            return self._fallback_analysis(system_prompt, user_message)

    def _fallback_analysis(self, system_prompt: str, user_message: str) -> str:
        """Provide basic analysis without API call."""
        msg_lower = user_message.lower()

        # Simple keyword-based intent detection
        if any(word in msg_lower for word in ["install", "package", "apt", "yay", "pacman"]):
            return '{"intent": "package", "needs_action": true, "needs_package": true, "needs_memory": false, "tools_mentioned": ["pacman", "yay"], "confidence": 0.7}'
        elif any(
            word in msg_lower for word in ["run", "execute", "command", "git", "docker", "build"]
        ):
            return '{"intent": "action", "needs_action": true, "needs_package": false, "needs_memory": false, "tools_mentioned": [], "confidence": 0.7}'
        elif any(word in msg_lower for word in ["remember", "previous", "before", "said"]):
            return '{"intent": "memory", "needs_action": false, "needs_package": false, "needs_memory": true, "tools_mentioned": [], "confidence": 0.6}'
        else:
            return '{"intent": "chat", "needs_action": false, "needs_package": false, "needs_memory": false, "tools_mentioned": [], "confidence": 0.9}'

    def is_simple_query(self, user_message: str) -> bool:
        """Detect if query is simple enough for heart-only response."""
        msg_lower = user_message.lower().strip()

        # Simple greeting patterns
        greetings = ["hi", "hello", "hey", "howdy", "greetings", "yo", "sup"]
        if msg_lower in greetings or any(msg_lower.startswith(g) for g in greetings):
            return True

        # Simple status/check queries
        simple_patterns = [
            "how are you",
            "status",
            "health",
            "heart",
            "what can you do",
            "help",
            "info",
            "about",
            "time",
            "date",
            "weather",
            "ok",
            "thanks",
            "thank you",
            "bye",
            "goodbye",
        ]
        if any(pattern in msg_lower for pattern in simple_patterns):
            return True

        # Very short queries (likely simple)
        if len(msg_lower) < 20 and "?" not in msg_lower:
            return True

        return False

    async def analyze_intent(self, user_message: str) -> dict[str, Any]:
        """Analyze user intent using fast model."""
        system_prompt = """You are an intent analysis system. Analyze the user's query and return a JSON object with:
{
  "intent": "action|package|memory|chat",
  "needs_action": true/false,
  "needs_package": true/false,
  "needs_memory": true/false,
  "tools_mentioned": ["tool1", "tool2"],
  "confidence": 0.0-1.0
}

Intents:
- action: User wants to run a command or tool
- package: User wants to install/remove software
- memory: User is referencing previous conversation
- chat: General conversation

Be concise. Return ONLY the JSON object."""

        try:
            result = await self._call_fast(system_prompt, user_message)
            # Extract JSON from response
            import json

            # Handle potential markdown code blocks
            result = result.strip()
            if result.startswith("```json"):
                result = result[7:]
            if result.startswith("```"):
                result = result[3:]
            if result.endswith("```"):
                result = result[:-3]
            result = result.strip()

            return json.loads(result)
        except Exception as e:
            print(f"Intent analysis error: {e}")
            return {
                "intent": "chat",
                "needs_action": False,
                "needs_package": False,
                "needs_memory": False,
                "tools_mentioned": [],
                "confidence": 0.5,
            }

    async def analyze_sentiment(self, user_message: str) -> dict[str, Any]:
        """Analyze sentiment using fast model."""
        system_prompt = """You are a sentiment analysis system. Analyze the user's message and return a JSON object with:
{
  "sentiment": "positive|negative|neutral",
  "emotion": "happy|sad|angry|frustrated|excited|confused|neutral",
  "urgency": 0.0-1.0,
  "complexity": "simple|medium|complex",
  "tone": "casual|formal|technical|urgent"
}

Be concise. Return ONLY the JSON object."""

        try:
            result = await self._call_fast(system_prompt, user_message)
            import json

            result = result.strip()
            if result.startswith("```"):
                result = result.split("```")[1]
                if result.startswith("json"):
                    result = result[4:]
            result = result.strip()

            return json.loads(result)
        except Exception as e:
            print(f"Sentiment analysis error: {e}")
            return {
                "sentiment": "neutral",
                "emotion": "neutral",
                "urgency": 0.5,
                "complexity": "medium",
                "tone": "casual",
            }

    async def extract_memory_query(self, user_message: str) -> str | None:
        """Extract if user is asking about previous context."""
        system_prompt = """You are a memory query extractor. If the user is asking about something from a previous conversation, return the search query to find relevant memories. Otherwise return "NONE".

Examples:
User: "What did we discuss earlier?" -> "previous discussion"
User: "What was that command you mentioned?" -> "command"
User: "How do I install neovim?" -> "NONE"

Return ONLY the search query or "NONE"."""

        try:
            result = await self._call_fast(system_prompt, user_message)
            result = result.strip().strip('"')
            if result == "NONE" or result == "none":
                return None
            return result
        except Exception as e:
            print(f"Memory extraction error: {e}")
            return None

    async def suggest_actions(
        self, user_message: str, available_tools: list[str]
    ) -> list[dict[str, Any]]:
        """Suggest relevant actions using fast model."""
        system_prompt = f"""You are an action suggestion system. Based on the user's query and available tools, suggest which actions to use.

Available tools: {", ".join(available_tools)}

Return a JSON array of suggestions:
[
  {{"tool": "tool_name", "command": "suggested_command", "confidence": 0.0-1.0}}
]

Return ONLY the JSON array."""

        try:
            result = await self._call_fast(system_prompt, user_message)
            import json

            result = result.strip()
            if "```" in result:
                result = result.split("```")[1]
                if result.startswith("json"):
                    result = result[4:]
            result = result.strip()

            suggestions = json.loads(result)
            return suggestions if isinstance(suggestions, list) else []
        except Exception as e:
            print(f"Action suggestion error: {e}")
            return []

    async def call_quality(
        self, system_prompt: str, user_message: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Call quality model with full context."""
        # Build enriched messages
        messages = []

        # Add system context
        context_str = f"""You are openaur, an AI assistant running in Arch Linux.

CONTEXT ANALYSIS:
- Intent: {context.get("intent", {}).get("intent", "chat")}
- Sentiment: {context.get("sentiment", {}).get("sentiment", "neutral")}
- Emotion: {context.get("sentiment", {}).get("emotion", "neutral")}
- Urgency: {context.get("sentiment", {}).get("urgency", 0.5)}
- Complexity: {context.get("sentiment", {}).get("complexity", "medium")}

SYSTEM INFO:
- Arch Linux with pacman/yay
- openaur CLI: /home/laptop/Documents/code/openaur/openaur
- API: http://localhost:8000
- WebUI: http://localhost:3000

{system_prompt}"""

        messages.append({"role": "system", "content": context_str})

        # Add relevant memories as context
        memories = context.get("relevant_memories", [])
        if memories:
            memory_context = "Relevant previous context:\n"
            for mem in memories[:3]:
                memory_context += f"- {mem.get('content', '')[:150]}\n"
            messages.append({"role": "system", "content": memory_context})

        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": self.QUALITY_MODEL,
            "messages": messages,
            "temperature": 0.7,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=60.0,
            )

            if response.status_code != 200:
                raise Exception(f"Quality model error: {response.text}")

            data = response.json()

            return {
                "content": data["choices"][0]["message"]["content"],
                "model": data.get("model"),
                "usage": data.get("usage", {}),
            }

    async def chat_with_preview(
        self,
        user_message: str,
        system_prompt: str = "You are a helpful assistant.",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get both fast preview and quality response in parallel.

        Returns:
            {
                "preview": {"content": str, "model": str},  # Fast model response
                "quality": {"content": str, "model": str},   # Quality model response
                "context": dict  # Analysis context
            }
        """
        if context is None:
            context = {}

        try:
            # Build quality model messages (full context)
            quality_messages = [{"role": "system", "content": system_prompt}]

            # Add sentiment/context info
            sentiment = context.get("sentiment", {})
            if sentiment:
                context_str = f"""USER CONTEXT:
- Mood: {sentiment.get("mood", "neutral")}
- Urgency: {sentiment.get("urgency", 0.5)}
- State: {sentiment.get("state", "neutral")}

{system_prompt}"""
                quality_messages[0] = {"role": "system", "content": context_str}

            # Add relevant memories
            memories = context.get("relevant_memories", [])
            if memories:
                memory_context = "Relevant context:\n"
                for mem in memories[:3]:
                    memory_context += f"- {mem.get('content', '')[:150]}\n"
                quality_messages.append({"role": "system", "content": memory_context})

            quality_messages.append({"role": "user", "content": user_message})

            # Build fast model messages (simpler prompt for quick response)
            # The fast model gets a simplified prompt to avoid confusion
            fast_system = (
                "You are a helpful assistant. Answer the user's question directly and concisely."
            )
            fast_messages = [
                {"role": "system", "content": fast_system},
                {"role": "user", "content": user_message},
            ]

            # Build payloads for both models
            fast_payload = {
                "model": self.fast_model,
                "messages": fast_messages,
                "max_tokens": 800,
                "temperature": 0.7,  # Slightly higher for more natural responses
            }

            quality_payload = {
                "model": self.QUALITY_MODEL,
                "messages": quality_messages,
                "temperature": 0.7,
            }

            # Call both models in parallel
            async with httpx.AsyncClient() as client:
                fast_task = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=fast_payload,
                    timeout=30.0,
                )
                quality_task = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=quality_payload,
                    timeout=60.0,
                )

                results = await asyncio.gather(fast_task, quality_task, return_exceptions=True)

            # Parse responses
            preview = None
            quality = None

            fast_result, quality_result = results[0], results[1]

            # Check if result is a response (not an exception)
            if not isinstance(fast_result, Exception):
                try:
                    if fast_result.status_code == 200:
                        data = fast_result.json()
                        preview = {
                            "content": data["choices"][0]["message"]["content"],
                            "model": data.get("model", self.fast_model),
                        }
                except Exception as e:
                    print(f"Error parsing fast model response: {e}")
            else:
                print(f"Fast model error: {fast_result}")

            if not isinstance(quality_result, Exception):
                try:
                    if quality_result.status_code == 200:
                        data = quality_result.json()
                        quality = {
                            "content": data["choices"][0]["message"]["content"],
                            "model": data.get("model", self.QUALITY_MODEL),
                        }
                except Exception as e:
                    print(f"Error parsing quality model response: {e}")
            else:
                print(f"Quality model error: {quality_result}")

            # If quality failed but preview succeeded, use preview as quality
            if quality is None and preview is not None:
                quality = preview
                preview = None

            return {
                "preview": preview,
                "quality": quality,
                "context": context,
            }
        except Exception as e:
            print(f"Error in chat_with_preview: {e}")
            import traceback

            print(traceback.format_exc())
            # Return empty response on error
            return {
                "preview": None,
                "quality": None,
                "context": context,
                "error": str(e),
            }


# Singleton instance
_processor: TwoStageProcessor | None = None


def get_processor() -> TwoStageProcessor:
    """Get singleton processor instance."""
    global _processor
    if _processor is None:
        _processor = TwoStageProcessor()
    return _processor
