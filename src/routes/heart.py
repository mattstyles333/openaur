from datetime import datetime
from typing import Any

from fastapi import APIRouter

from src.services.analysis_engine import get_analysis_engine

router = APIRouter()
analysis_engine = get_analysis_engine()


@router.get("/")
async def heart() -> dict[str, Any]:
    """
    The Heart of openaur - combines system health and emotional state.

    Uses fast model (gpt-oss-20b:nitro) for sentiment analysis.
    """
    # Physical health
    health_status = {
        "status": "healthy",
        "service": "openaura",
        "analysis_engine": "operational",
        "two_stage_processing": "active",
    }

    return {
        "heart": {
            "physical": health_status,
            "emotional": {
                "state": "neutral",
                "mood": "balanced",
                "awareness": "active",
                "model": "gpt-oss-20b:nitro (fast)",
            },
            "vitals": {
                "timestamp": datetime.utcnow().isoformat(),
                "version": "2.0.0",
                "status": "beating",
            },
        },
        "message": "openaur's heart is beating with two-stage intelligence",
        "pulse": "✓✓",
    }


@router.post("/check")
async def heart_check(message: str = "How are you feeling?") -> dict[str, Any]:
    """
    Check the heart with sentiment analysis using fast model.

    Analyzes emotional content and returns adaptation strategy.
    """
    # Use analysis engine for smart sentiment detection
    analysis = await analysis_engine.analyze(message, session_id="heart_check")

    sentiment = analysis.sentiment
    intent = analysis.intent

    return {
        "heart": {
            "input": message,
            "analysis": {
                "sentiment": sentiment.get("sentiment", "neutral"),
                "emotion": sentiment.get("emotion", "neutral"),
                "urgency": sentiment.get("urgency", 0.5),
                "tone": sentiment.get("tone", "casual"),
                "complexity": sentiment.get("complexity", "medium"),
            },
            "intent": {
                "type": intent.get("intent", "chat"),
                "needs_action": intent.get("needs_action", False),
                "tools_mentioned": intent.get("tools_mentioned", []),
                "confidence": intent.get("confidence", 0.5),
            },
            "adaptation": analysis.thinking_summary,
            "beat": "thump-thump",
        },
        "empathy": "active (fast model)",
        "model": "gpt-oss-20b:nitro",
    }
