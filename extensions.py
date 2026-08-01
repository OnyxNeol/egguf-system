"""
Extension Application Logic (Python-based EFE format)

Handles applying scanned-and-executed EFE extensions to EGGUF files.
The EGGUF file stores the extension configs as JSON in its extension slots.
"""

import json
from typing import List, Dict, Any, Optional

from egguf_format import EGGUFFile, EGGUFExtension


def apply_efe_to_egguf(egguf: EGGUFFile, efe_configs: List[Dict[str, Any]],
                       selected_names: Optional[List[str]] = None) -> List[str]:
    """
    Apply EFE extension configs (from executing an EFE file) to an EGGUF file.
    
    Args:
        egguf: The EGGUF file to modify
        efe_configs: List of config dicts from EFEFile.configs
        selected_names: Optional list of extension names to apply (None = apply all)
    
    Returns:
        List of applied extension names
    """
    applied = []
    
    for config in efe_configs:
        name = config.get("name", "Unknown")
        if selected_names is not None and name not in selected_names:
            continue
        
        ext_type = config.get("ext_type", "unknown")
        description = config.get("description", "")
        data = config.get("data", {})
        
        egguf_ext = EGGUFExtension(
            ext_type=ext_type,
            name=name,
            description=description,
            data=json.dumps(data).encode("utf-8"),
        )
        egguf.add_extension(egguf_ext)
        applied.append(name)
    
    # Update metadata
    if "applied_extensions" not in egguf.metadata:
        egguf.metadata["applied_extensions"] = []
    egguf.metadata["applied_extensions"].extend(applied)
    from datetime import datetime
    egguf.metadata["last_modified"] = datetime.now().isoformat()
    
    return applied


def get_extension_summary(egguf: EGGUFFile) -> List[Dict[str, Any]]:
    """Get a summary of all extensions applied to an EGGUF file."""
    summaries = []
    for ext in egguf.extensions:
        info = {
            "type": ext.ext_type,
            "name": ext.name,
            "description": ext.description,
            "data_size": len(ext.data),
        }
        if ext.data:
            try:
                info["data"] = json.loads(ext.data.decode("utf-8"))
            except Exception:
                info["data"] = "<binary>"
        summaries.append(info)
    return summaries


# Extension type display names (for the GUI)
EXTENSION_TYPE_DISPLAY = {
    "system_prompt": "System Prompt / Persona",
    "prompt_template": "Prompt Template",
    "context_window": "Context Window",
    "tokenizer": "Custom Tokenizer Tokens",
    "quantization": "Quantization Override",
    "lora_adapter": "LoRA Adapter",
    "safety_filter": "Safety Filter",
    "response_format": "Response Format",
    "generation_params": "Generation Parameters",
    "stop_tokens": "Stop Tokens",
    "embedding_config": "Embedding Configuration",
    "chat_template": "Chat Template",
    "knowledge_inject": "Knowledge Injection",
    "behavior_mod": "Behavior Modification",
    "capability_unlock": "Capability Unlock",
    "webapi": "External Web API",
    "model_override": "Model Parameter Override",
    "knowledge_database": "Knowledge Database (Searchable)",
}


def get_type_display(ext_type: str) -> str:
    """Get a human-readable display name for an extension type."""
    return EXTENSION_TYPE_DISPLAY.get(ext_type, ext_type)
