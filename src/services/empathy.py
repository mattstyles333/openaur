import os
import re
from typing import Dict, Optional, Tuple


class EmpathyEngine:
    """Sentiment analysis and emotional adaptation engine."""

    def __init__(self):
        # Simple keyword-based sentiment (can be replaced with ML model)
        self.positive_words = [
            "great",
            "awesome",
            "excellent",
            "perfect",
            "love",
            "happy",
            "thanks",
            "thank",
            "appreciate",
            "helpful",
            "amazing",
            "good",
        ]

        self.negative_words = [
            "frustrated",
            "annoying",
            "stuck",
            "broken",
            "error",
            "fail",
            "failing",
            "problem",
            "issue",
            "trouble",
            "difficult",
            "hard",
            "confusing",
            "why",
            "doesn't work",
            "not working",
        ]

        self.stress_indicators = [
            "urgent",
            "asap",
            "deadline",
            "emergency",
            "critical",
            "production",
            "down",
            "outage",
            "broken",
            "lost",
        ]

        self.confidence_indicators = [
            "just",
            "need",
            "want",
            "run",
            "build",
            "deploy",
            "create",
            "update",
            "delete",
            "push",
            "pull",
        ]

    def analyze(self, message: str) -> Dict:
        """Analyze message for emotional content."""
        message_lower = message.lower()

        # Count sentiment indicators
        positive_count = sum(1 for word in self.positive_words if word in message_lower)
        negative_count = sum(1 for word in self.negative_words if word in message_lower)
        stress_count = sum(
            1 for word in self.stress_indicators if word in message_lower
        )
        confidence_count = sum(
            1 for word in self.confidence_indicators if word in message_lower
        )

        # Determine sentiment
        if negative_count > positive_count:
            sentiment = "frustrated"
            intensity = min(negative_count / 3, 1.0)
        elif stress_count > 0:
            sentiment = "stressed"
            intensity = min(stress_count / 2, 1.0)
        elif confidence_count > 0 and positive_count >= negative_count:
            sentiment = "confident"
            intensity = min(confidence_count / 3, 1.0)
        elif positive_count > negative_count:
            sentiment = "positive"
            intensity = min(positive_count / 2, 1.0)
        else:
            sentiment = "neutral"
            intensity = 0.5

        # Detect context
        context = self._detect_context(message_lower)

        return {
            "sentiment": sentiment,
            "intensity": round(intensity, 2),
            "keywords": self._extract_keywords(message_lower),
            "context": context,
            "urgent": stress_count > 0,
        }

    def _detect_context(self, message: str) -> str:
        """Detect context/topic of message."""
        contexts = {
            "git": ["git", "commit", "push", "pull", "branch", "merge"],
            "docker": ["docker", "container", "image", "build", "deploy"],
            "development": ["code", "debug", "test", "run", "build"],
            "system": ["install", "update", "configure", "setup"],
            "error": ["error", "bug", "issue", "problem", "fail", "broken"],
        }

        for context, keywords in contexts.items():
            if any(kw in message for kw in keywords):
                return context

        return "general"

    def _extract_keywords(self, message: str) -> list:
        """Extract relevant keywords."""
        words = re.findall(r"\b[a-z]{4,}\b", message)
        return list(set(words))[:10]

    def adapt_prompt(self, base_prompt: str, emotional_state: Dict, tools: list) -> str:
        """Adapt system prompt based on emotional state."""
        sentiment = emotional_state.get("sentiment", "neutral")
        intensity = emotional_state.get("intensity", 0.5)
        urgent = emotional_state.get("urgent", False)

        adaptations = []

        if sentiment == "frustrated":
            adaptations.append(
                "The user is frustrated. Be patient and offer simple, step-by-step solutions."
            )
        elif sentiment == "stressed":
            adaptations.append(
                "The user is under time pressure. Be concise and direct."
            )
        elif sentiment == "confident":
            adaptations.append("The user is confident. You can be technical and brief.")

        if urgent:
            adaptations.append(
                "This is urgent. Prioritize safety and provide quick solutions."
            )

        if intensity > 0.7:
            adaptations.append(
                "The user feels strongly about this. Match their energy level."
            )

        # Add tool context
        if tools:
            tool_names = [t.get("binary", "") for t in tools]
            adaptations.append(f"Available tools: {', '.join(tool_names)}")

        # Combine adaptations
        if adaptations:
            adaptation_text = "\n".join([f"- {a}" for a in adaptations])
            return f"{base_prompt}\n\nContext:\n{adaptation_text}"

        return base_prompt
