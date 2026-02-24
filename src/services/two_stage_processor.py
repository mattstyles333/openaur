"""Two-stage LLM processing for OpenAura.

Uses fast/cheap model (gpt-oss-20b:nitro) for preprocessing tasks:
- Intent analysis
- Action detection
- Memory retrieval
- Sentiment analysis

Then uses quality model (openrouter/auto) for final response.
"""

from typing import Dict, Any, Optional, List
import httpx
import os


class TwoStageProcessor:
    """Two-stage LLM processor for cost/performance optimization."""

    # Fast model for preprocessing
    FAST_MODEL = "openai/gpt-oss-20b:nitro"

    # Quality model for final response
    QUALITY_MODEL = "openrouter/auto"

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://openaura.local",
            "X-Title": "OpenAura",
        }

    async def _call_fast(self, system_prompt: str, user_message: str) -> str:
        """Call fast model for quick analysis."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        payload = {
            "model": self.FAST_MODEL,
            "messages": messages,
            "max_tokens": 500,  # Keep it short and fast
            "temperature": 0.3,  # Lower temp for more consistent analysis
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30.0,
            )

            if response.status_code != 200:
                print(f"Fast model error: {response.text}")
                return "{}"  # Return empty JSON on error

            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def analyze_intent(self, user_message: str) -> Dict[str, Any]:
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

    async def analyze_sentiment(self, user_message: str) -> Dict[str, Any]:
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

    async def extract_memory_query(self, user_message: str) -> Optional[str]:
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
        self, user_message: str, available_tools: List[str]
    ) -> List[Dict[str, Any]]:
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
        self, system_prompt: str, user_message: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call quality model with full context."""
        # Build enriched messages
        messages = []

        # Add system context
        context_str = f"""You are OpenAura, an AI assistant running in Arch Linux.

CONTEXT ANALYSIS:
- Intent: {context.get("intent", {}).get("intent", "chat")}
- Sentiment: {context.get("sentiment", {}).get("sentiment", "neutral")}
- Emotion: {context.get("sentiment", {}).get("emotion", "neutral")}
- Urgency: {context.get("sentiment", {}).get("urgency", 0.5)}
- Complexity: {context.get("sentiment", {}).get("complexity", "medium")}

SYSTEM INFO:
- Arch Linux with pacman/yay
- OpenAura CLI: /home/laptop/Documents/code/openaur/openaur
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


# Singleton instance
_processor: Optional[TwoStageProcessor] = None


def get_processor() -> TwoStageProcessor:
    """Get singleton processor instance."""
    global _processor
    if _processor is None:
        _processor = TwoStageProcessor()
    return _processor
