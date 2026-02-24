"""Dependency injection providers.

Factory functions for creating service instances.
"""

from functools import lru_cache
from typing import Any

from src.config import settings
from src.constants import ModelConfig
from src.services.empathy import EmpathyEngine
from src.services.gateway import OpenRouterGateway
from src.services.openmemory import MemoryService
from src.services.openrouter_client import OpenRouterClient
from src.services.two_stage_processor import TwoStageProcessor
from src.utils.yaml_registry import YamlRegistry


# API Client
@lru_cache()
def get_openrouter_client() -> OpenRouterClient:
    """Get cached OpenRouter client."""
    return OpenRouterClient()


@lru_cache()
def get_openrouter_gateway() -> OpenRouterGateway:
    """Get cached OpenRouter gateway (legacy)."""
    return OpenRouterGateway()


# Processing
@lru_cache()
def get_two_stage_processor() -> TwoStageProcessor:
    """Get cached two-stage processor."""
    return TwoStageProcessor()


@lru_cache()
def get_empathy_engine() -> EmpathyEngine:
    """Get cached empathy engine."""
    return EmpathyEngine()


# Memory
@lru_cache()
def get_memory_service() -> MemoryService:
    """Get cached memory service."""
    return MemoryService()


# Registry
@lru_cache()
def get_yaml_registry() -> YamlRegistry:
    """Get cached YAML registry."""
    return YamlRegistry()


# Configuration helpers
def get_default_chat_model() -> str:
    """Get default chat model from settings."""
    return settings.default_model


def get_default_heart_model() -> str:
    """Get default heart model from settings."""
    return settings.heart_model or ModelConfig.DEFAULT_HEART_MODEL


def is_instant_preview_enabled() -> bool:
    """Check if instant preview is enabled."""
    return settings.instant_preview
