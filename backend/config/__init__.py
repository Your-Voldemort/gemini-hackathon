"""Configuration module initialization."""

try:
    from .settings import get_settings
    
    # Backwards compatibility alias
    def initialize_ai_agent_settings():
        """Backwards compatible function (deprecated)."""
        return get_settings()
    
except ImportError:
    initialize_ai_agent_settings = None
    get_settings = None

__all__ = [
    'initialize_ai_agent_settings',
    'get_settings',
]