
__version__ = "1.0.0"
__author__ = "AI Debate System"
__description__ = "A debate system using AutoGen's groupchat with multiple AI personalities powered by local GGUF models"

from .main import main
from .debate_manager import DebateManager
from .agents import DebateAgentFactory
from .config import AGENT_PERSONALITIES, MODEL_CONFIG

__all__ = [
    "main",
    "DebateManager", 
    "DebateAgentFactory",
    "AGENT_PERSONALITIES",
    "MODEL_CONFIG"
]