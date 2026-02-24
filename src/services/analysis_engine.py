"""Enhanced analysis engine for OpenAura.

Uses fast model (gpt-oss-20b:nitro) for sentiment/action/memory analysis,
then quality model (openrouter/auto) for final response.

Returns thinking/analysis visible to user in OpenWebUI.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from src.services.two_stage_processor import get_processor
from src.services.openmemory import get_memory
from src.services.context_manager import ContextBuilder
from src.utils.yaml_registry import YamlRegistry


@dataclass
class AnalysisResult:
    """Result of fast model analysis."""

    sentiment: Dict[str, Any]
    intent: Dict[str, Any]
    actions: Dict[str, Any]
    relevant_memories: List[Dict[str, Any]]
    thinking_summary: str


class AnalysisEngine:
    """Fast analysis using gpt-oss-20b:nitro, then quality response."""

    def __init__(self):
        self.processor = get_processor()
        self.memory = get_memory()
        self.context_builder = ContextBuilder()
        self.yaml_reg = YamlRegistry()

    async def analyze(self, user_message: str, session_id: str) -> AnalysisResult:
        """Fast analysis using cheap model."""
        # Parallel fast analysis calls
        sentiment_task = self.processor.analyze_sentiment(user_message)
        intent_task = self.processor.analyze_intent(user_message)

        sentiment = await sentiment_task
        intent = await intent_task

        # Get available tools
        available_tools = self._get_available_tools(intent.get("tools_mentioned", []))

        # Get action suggestions if needed
        actions = {"available": [], "suggested": []}
        if intent.get("needs_action"):
            actions = await self._suggest_actions(user_message, available_tools)

        # Get relevant memories
        memory_query = await self.processor.extract_memory_query(user_message)
        relevant_memories = []
        if memory_query:
            memories = self.memory.retrieve(memory_query, limit=5)
            relevant_memories = [
                {
                    "content": m.content,
                    "type": m.memory_type,
                    "importance": m.importance,
                    "tags": m.tags,
                }
                for m in memories
            ]

        # Build thinking summary for user visibility
        thinking_summary = self._build_thinking_summary(
            sentiment, intent, actions, relevant_memories, available_tools
        )

        return AnalysisResult(
            sentiment=sentiment,
            intent=intent,
            actions=actions,
            relevant_memories=relevant_memories,
            thinking_summary=thinking_summary,
        )

    def _get_available_tools(self, mentioned: List[str]) -> List[str]:
        """Get list of available CLI tools."""
        # Common tools to check
        common_tools = [
            "git",
            "docker",
            "npm",
            "pip",
            "cargo",
            "make",
            "curl",
            "glab",
            "gh",
            "kubectl",
            "nvim",
            "code",
            "yay",
            "pacman",
        ]

        # Check which are registered
        available = []
        for tool in mentioned + common_tools:
            if self.yaml_reg.load_action(tool):
                available.append(tool)

        return list(set(available))

    async def _suggest_actions(
        self, user_message: str, available_tools: List[str]
    ) -> Dict[str, Any]:
        """Suggest actions based on user intent."""
        suggestions = await self.processor.suggest_actions(
            user_message, available_tools
        )

        return {
            "available": available_tools,
            "suggested": suggestions,
            "can_execute": len(suggestions) > 0,
        }

    def _build_thinking_summary(
        self,
        sentiment: Dict[str, Any],
        intent: Dict[str, Any],
        actions: Dict[str, Any],
        memories: List[Dict[str, Any]],
        tools: List[str],
    ) -> str:
        """Build human-readable thinking summary."""
        lines = ["💭 **Analysis**"]

        # Sentiment
        emotion = sentiment.get("emotion", "neutral")
        urgency = sentiment.get("urgency", 0.5)
        lines.append(f"• Mood: {emotion} (urgency: {urgency:.1f}/1.0)")

        # Intent
        intent_type = intent.get("intent", "chat")
        confidence = intent.get("confidence", 0.5)
        lines.append(f"• Intent: {intent_type} ({confidence:.0%} confidence)")

        # Actions
        if intent.get("needs_action"):
            lines.append("• Action request detected")
            if actions.get("available"):
                lines.append(
                    f"  - Available tools: {', '.join(actions['available'][:5])}"
                )
            if actions.get("suggested"):
                suggested = actions["suggested"][:3]
                lines.append(f"  - Suggestions: {len(suggested)} actions")

        # Memories
        if memories:
            lines.append(f"• Found {len(memories)} relevant memories")
            for mem in memories[:2]:
                content = (
                    mem["content"][:60] + "..."
                    if len(mem["content"]) > 60
                    else mem["content"]
                )
                lines.append(f"  - [{mem['type']}] {content}")

        return "\n".join(lines)

    async def get_quality_response(
        self,
        user_message: str,
        analysis: AnalysisResult,
        session_id: str,
    ) -> Dict[str, Any]:
        """Get quality response using full context."""
        # Build enriched system prompt
        system_prompt = self._build_quality_prompt(analysis, session_id)

        # Call quality model
        response = await self.processor.call_quality(
            system_prompt=system_prompt,
            user_message=user_message,
            context={
                "intent": analysis.intent,
                "sentiment": analysis.sentiment,
                "relevant_memories": analysis.relevant_memories,
            },
        )

        # Store in memory
        self._store_interaction(
            user_message=user_message,
            assistant_response=response["content"],
            analysis=analysis,
            session_id=session_id,
        )

        return response

    def _build_quality_prompt(self, analysis: AnalysisResult, session_id: str) -> str:
        """Build system prompt for quality model."""
        sentiment = analysis.sentiment
        intent = analysis.intent

        prompt = f"""You are OpenAura, an AI assistant running in Arch Linux.

USER STATE:
- Mood: {sentiment.get("emotion", "neutral")}
- Urgency: {sentiment.get("urgency", 0.5)}/1.0
- Tone: {sentiment.get("tone", "casual")}

INTENT: {intent.get("intent", "chat")}
"""

        # Add emotional adaptation
        if sentiment.get("emotion") == "frustrated":
            prompt += "\nThe user is frustrated. Be patient, offer step-by-step help."
        elif sentiment.get("urgency", 0) > 0.7:
            prompt += "\nThis is urgent. Be concise and prioritize safety."

        # Add available actions
        if analysis.actions.get("available"):
            prompt += f"\n\nAvailable CLI tools: {', '.join(analysis.actions['available'][:10])}"

        # Add memories context
        if analysis.relevant_memories:
            prompt += "\n\nRelevant context from previous conversations:\n"
            for mem in analysis.relevant_memories[:3]:
                prompt += f"- {mem['content'][:100]}\n"

        # Add OpenAura capabilities
        prompt += """

OPENAURA CAPABILITIES:
- CLI tool at /home/laptop/Documents/code/openaur/openaur
- Commands: heart, chat, ingest action <tool>, packages, sessions, test
- Sub-agents: deep, quick, code-reviewer, test-runner, committer
- Package management: pacman (official), yay (AUR)
- Memory system stores conversations and learns from actions
- All commands run in isolated tmux sessions

Respond naturally without referencing this analysis unless relevant."""

        return prompt

    def _store_interaction(
        self,
        user_message: str,
        assistant_response: str,
        analysis: AnalysisResult,
        session_id: str,
    ):
        """Store interaction in memory with rich context."""
        # Store user query with intent
        self.memory.store(
            content=user_message,
            memory_type="user_query",
            importance=0.7,
            tags=[
                "conversation",
                analysis.intent.get("intent", "chat"),
                f"emotion:{analysis.sentiment.get('emotion', 'neutral')}",
            ],
            metadata={
                "session_id": session_id,
                "intent": analysis.intent,
                "sentiment": analysis.sentiment,
            },
        )

        # Store assistant response
        self.memory.store(
            content=assistant_response,
            memory_type="assistant_response",
            importance=0.6,
            tags=["conversation", "assistant"],
            metadata={
                "session_id": session_id,
                "tools_used": analysis.actions.get("available", []),
            },
        )

        # Store action learning if tools were used
        if analysis.actions.get("available"):
            for tool in analysis.actions["available"]:
                self.memory.store(
                    content=f"User query '{user_message[:50]}...' involved tool: {tool}",
                    memory_type="action_learning",
                    importance=0.8,
                    tags=["action", tool, "learning"],
                    metadata={"session_id": session_id, "query": user_message},
                )


# Singleton
_analysis_engine: Optional[AnalysisEngine] = None


def get_analysis_engine() -> AnalysisEngine:
    """Get singleton analysis engine."""
    global _analysis_engine
    if _analysis_engine is None:
        _analysis_engine = AnalysisEngine()
    return _analysis_engine


async def analyze_and_respond(user_message: str, session_id: str) -> Dict[str, Any]:
    """Convenience function: analyze with fast model, respond with quality model."""
    engine = get_analysis_engine()

    # Fast analysis
    analysis = await engine.analyze(user_message, session_id)

    # Quality response
    response = await engine.get_quality_response(user_message, analysis, session_id)

    return {
        "thinking": analysis.thinking_summary,
        "response": response["content"],
        "model": response.get("model"),
        "usage": response.get("usage", {}),
        "analysis": {
            "sentiment": analysis.sentiment,
            "intent": analysis.intent,
            "actions_available": analysis.actions.get("available", []),
        },
    }
