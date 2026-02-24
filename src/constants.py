"""Centralized constants for openaur.

All magic strings, default values, and configuration constants live here.
"""


# API Configuration
class APIConfig:
    """API-related constants."""

    DEFAULT_TIMEOUT = 60.0
    FAST_TIMEOUT = 30.0
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0

    # Rate limiting
    RATE_LIMIT_REQUESTS = 100
    RATE_LIMIT_WINDOW = 60


# Model Configuration
class ModelConfig:
    """AI model constants."""

    # Quality models
    DEFAULT_CHAT_MODEL = "deepseek/deepseek-chat"
    QUALITY_MODEL = "openrouter/auto"

    # Fast models for preview/analysis
    DEFAULT_HEART_MODEL = "openai/gpt-oss-20b:nitro"
    FALLBACK_HEART_MODEL = "meta-llama/llama-3.1-8b-instruct:nitro"

    # Available models for selection
    CHAT_MODELS = [
        ("openrouter/auto", "Auto (Default)"),
        ("moonshotai/kimi-k2.5", "Kimi K2.5"),
        ("minimax/minimax-m2.5", "MiniMax M2.5"),
        ("deepseek/deepseek-v3.2", "DeepSeek V3.2"),
    ]

    HEART_MODELS = [
        ("openai/gpt-oss-20b:nitro", "GPT-OSS 20B Nitro"),
        ("meta-llama/llama-3.1-8b-instruct:nitro", "Llama 3.1 8B Nitro"),
        ("meta-llama/llama-4-scout:nitro", "Llama 4 Scout Nitro"),
    ]


# Memory Configuration
class MemoryConfig:
    """Memory system constants."""

    DEFAULT_SECTORS = ["episodic", "semantic", "procedural", "emotional", "reflective"]
    MAX_IMPORTANCE = 1.0
    MIN_IMPORTANCE = 0.0
    DEFAULT_IMPORTANCE = 0.5
    RETRIEVAL_LIMIT = 10

    # HMD2 specific
    HMD2_DIMENSIONS = 768
    SALIENCE_DECAY_DAYS = 30


# Package Management
class PackageConfig:
    """Package manager constants."""

    BINARY_PACMAN = "/usr/bin/pacman"
    BINARY_YAY = "/usr/bin/yay"
    SCRIPT_INSTALL = "/home/aura/.local/bin/aura-pkg-add"

    SEARCH_LIMIT = 20
    DEFAULT_TIMEOUT = 300  # 5 minutes for install


# Session Management
class SessionConfig:
    """Tmux session constants."""

    DEFAULT_TIMEOUT = 3600  # 1 hour
    MAX_OUTPUT_SIZE = 1048576  # 1MB
    TMUX_SOCKET = "/tmp/tmux-openaur"


# Response Status
class ResponseStatus:
    """Standardized response status codes."""

    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    PARTIAL = "partial"


# Emotional States
class EmotionalState:
    """Empathy engine constants."""

    MOODS = ["happy", "sad", "frustrated", "excited", "confused", "neutral"]
    SENTIMENTS = ["positive", "negative", "neutral"]
    TONES = ["casual", "formal", "technical", "urgent"]

    DEFAULT_MOOD = "neutral"
    DEFAULT_SENTIMENT = "neutral"
    DEFAULT_URGENCY = 0.5


# Intent Types
class IntentType:
    """Intent classification constants."""

    ACTION = "action"
    PACKAGE = "package"
    MEMORY = "memory"
    CHAT = "chat"
    UNKNOWN = "unknown"


# Error Messages
class ErrorMessages:
    """Standardized error messages."""

    PACKAGE_NOT_FOUND = "Package '{}' not found in repositories or AUR"
    INVALID_API_KEY = "Invalid API key format. Must start with 'sk-or-v1-'"
    CONTAINER_NOT_RUNNING = "openaur container is not running"
    SESSION_NOT_FOUND = "Session '{}' not found"
    MEMORY_EMPTY = "Memory content cannot be empty"


# File Paths
class FilePath:
    """Path constants."""

    DATA_DIR = "./data"
    ACTIONS_DIR = "./actions/manifests"
    LOG_DIR = "./logs"

    # Database
    DB_FILE = "data/openaura.db"

    # Config
    ENV_FILE = ".env"
    ENV_EXAMPLE = ".env.example"


# CLI Display
class CLIDisplay:
    """CLI formatting constants."""

    TABLE_MAX_WIDTH = 100
    TRUNCATE_LENGTH = 37
    SPINNER_INTERVAL = 0.1


# Health Check
class HealthCheck:
    """Health monitoring constants."""

    HEARTBEAT_INTERVAL = 30
    DB_TIMEOUT = 5
    API_TIMEOUT = 10
