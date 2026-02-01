"""Managers module initialization."""

try:
    from .chatbot_manager_new import ChatbotManager
except ImportError:
    try:
        from .chatbot_manager import ChatbotManager
    except ImportError:
        ChatbotManager = None

__all__ = [
    'ChatbotManager',
]
