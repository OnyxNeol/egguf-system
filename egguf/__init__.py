"""
EGGUF Library - Modular AI Skills Framework

A Python library for building extensible AI systems where a base GGUF model
can be augmented with headless skill extensions (video, image, code, etc.) via
a side-panel metadata system.

Classes:
    EGGUF - Core model manager with skill extensions
    EGGUF_VID - Video skill extension
    EGGUF_IMG - Image skill extension
    EGGUF_AGENT - Agentic skills orchestrator
"""

from .core import (
    EGGUF,
    EGGUF_VID,
    EGGUF_IMG,
    EGGUF_AGENT,
    SidePanel,
    ExtensionDef,
    RoutingRules,
)

__all__ = [
    "EGGUF",
    "EGGUF_VID",
    "EGGUF_IMG",
    "EGGUF_AGENT",
    "SidePanel",
    "ExtensionDef",
    "RoutingRules",
]