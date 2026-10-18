"""
EGGUF Library - Modular AI Skills Framework

A Python library for building extensible AI systems where a base GGUF model
can be augmented with headless skill extensions (video, image, code, etc.) via
a side-panel metadata system.

Classes:
    EGGUF - Core model manager
    EGGUF_VID - Video skill extension
    EGGUF_IMG - Image skill extension
    EGGUF_AGENT - Agentic skills orchestrator
"""

from .core import EGGUF, SidePanel, ExtensionDef, RoutingRules
from .video import EGGUF_VID
from .image import EGGUF_IMG
from .agent import EGGUF_AGENT

__all__ = [
    "EGGUF",
    "EGGUF_VID",
    "EGGUF_IMG",
    "EGGUF_AGENT",
    "SidePanel",
    "ExtensionDef",
    "RoutingRules",
]