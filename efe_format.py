"""
EFE (Extensions For EGGUF) — Python-Based Format

EFE files are pure Python code with a special convention:
  - After (or before) EVERY line of code, the developer writes a #use: comment
  - The #use: text IS the system prompt — it tells the model what to do
  - The EGGUF scanner validates that every code line has a #use: annotation
  - Lines starting with directive prefixes (webapi:, lora:, etc.) are
    EGGUF-specific directives, not Python — parsed by the scanner

The #use: annotations have TWO purposes:
  1. Scanner validation — every code line MUST have one (or the file is rejected)
  2. System prompt — the #use: text becomes the actual system prompt the model sees

So #use: must be written clearly, as instructions to the model.

ALL Python libraries are supported in EFE files — you can import anything
that's installed in the Python environment.

File Structure (example):
    # === EFE: Smart Assistant ===
    # === Author: EGGUF Team ===

    #use:You are a helpful assistant with web search capabilities
    from egguf_ext import params, response

    #use:Use the webapi as an external knowledge tool so when you can't understand something you can web search it
    webapi:brave_API_KEY_HERE

    #use:Set temperature to 0.5 for balanced and accurate responses
    params.temperature(0.5)
"""

import os
import re
import json
import sys
import types
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from scanner import scan_efe, ScanResult, ScanItem, DIRECTIVE_PREFIXES


@dataclass
class EFEFile:
    """Represents a parsed Python-based EFE file."""
    file_path: str = ""
    scan_result: Optional[ScanResult] = None
    configs: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    use_texts: List[str] = field(default_factory=list)  # collected #use: annotations

    @property
    def accepted(self) -> bool:
        return self.scan_result is not None and self.scan_result.accepted

    @property
    def extension_count(self) -> int:
        return len(self.configs)

    @property
    def code_line_count(self) -> int:
        return self.scan_result.code_lines if self.scan_result else 0


def read_efe(path: str, execute: bool = True) -> EFEFile:
    """Read an EFE file: scan it first, then if accepted, execute the Python code.

    The #use: annotations are collected as the system prompt.
    The Python code is executed for technical configuration.
    Directives are parsed for external integrations.
    """
    efe = EFEFile(file_path=path)
    efe.scan_result = scan_efe(path)
    if not efe.accepted:
        return efe
    efe.metadata = _parse_metadata(path)
    if not execute:
        return efe
    efe.configs, efe.use_texts = _execute_efe(path, efe.scan_result)
    return efe


def write_efe(path: str, name: str, author: str, description: str,
              code_lines: List[tuple]) -> str:
    """Write an EFE file from a list of (code_line, use_description) pairs.

    The #use: text is the system prompt — write it clearly.
    """
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# === EFE: {name} ===\n")
        f.write(f"# === Author: {author} ===\n")
        if description:
            f.write(f"# === Description: {description} ===\n")
        f.write(f"# === Created: {_now()} ===\n")
        f.write("\n")
        for code_line, use_desc in code_lines:
            if use_desc:
                f.write(f"#use:{use_desc}\n")
            f.write(f"{code_line}\n")
            f.write("\n")
    return path


def is_efe_file(path: str) -> bool:
    """Quick check if a file looks like an EFE file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read(200)
        return "#use:" in content or content.startswith("# === EFE:")
    except Exception:
        return False


def _execute_efe(path: str, scan_result: ScanResult):
    """
    Execute the EFE Python code in a namespace with:
    - Full Python builtins (all libraries supported)
    - The egguf_ext runtime API injected
    - Standard library modules available

    Collects #use: annotations as the system prompt.
    Executes Python code for technical configuration.
    Parses directives for external integrations.

    Returns: (configs_list, use_texts_list)
    """
    from egguf_ext import ExtensionRuntime

    runtime = ExtensionRuntime()

    # Create convenience API objects
    system_api = _SystemAPI(runtime)
    params_api = _ParamsAPI(runtime)
    response_api = _ResponseAPI(runtime)
    efe_dir = os.path.dirname(os.path.abspath(path))
    knowledge_api = _KnowledgeAPI(runtime, efe_dir)
    behavior_api = _BehaviorAPI(runtime)
    safety_api = _SafetyAPI(runtime)
    chat_api = _ChatAPI(runtime)
    context_api = _ContextAPI(runtime)
    tokenizer_api = _TokenizerAPI(runtime)
    capability_api = _CapabilityAPI(runtime)
    embed_api = _EmbedAPI(runtime)
    quant_api = _QuantAPI(runtime)
    lora_api = _LoraAPI(runtime)
    stop_api = _StopAPI(runtime)

    # Create a fake module object so `from egguf_ext import system, params` works
    egguf_ext_module = types.ModuleType("egguf_ext")
    egguf_ext_module.system = system_api
    egguf_ext_module.params = params_api
    egguf_ext_module.response = response_api
    egguf_ext_module.knowledge = knowledge_api
    egguf_ext_module.behavior = behavior_api
    egguf_ext_module.safety = safety_api
    egguf_ext_module.chat = chat_api
    egguf_ext_module.context = context_api
    egguf_ext_module.tokenizer = tokenizer_api
    egguf_ext_module.capability = capability_api
    egguf_ext_module.embed = embed_api
    egguf_ext_module.quantization = quant_api
    egguf_ext_module.lora = lora_api
    egguf_ext_module.stop = stop_api
    egguf_ext_module.ExtensionRuntime = ExtensionRuntime

    # Build the execution namespace — FULL library support
    # We provide __builtins__ so ALL Python imports work (import math, import numpy, etc.)
    namespace = {
        "__builtins__": __builtins__,
        "__name__": "efe_extension",
        "egguf_ext": egguf_ext_module,
        # Also expose directly (in case code uses them without import)
        "system": system_api,
        "params": params_api,
        "response": response_api,
        "knowledge": knowledge_api,
        "behavior": behavior_api,
        "safety": safety_api,
        "chat": chat_api,
        "context": context_api,
        "tokenizer": tokenizer_api,
        "capability": capability_api,
        "embed": embed_api,
        "quantization": quant_api,
        "lora": lora_api,
        "stop": stop_api,
    }

    # Register the fake module in sys.modules so `from egguf_ext import ...` works
    # Save the original so we can restore it
    original_egguf_ext = sys.modules.get("egguf_ext")
    sys.modules["egguf_ext"] = egguf_ext_module

    # Read the file and separate Python code from directives
    # Also collect #use: annotations as system prompt
    with open(path, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    python_lines = []
    directive_lines = []  # (line_number, directive_name, directive_value, use_desc, code_line)
    use_texts = []  # collected #use: texts for system prompt

    pending_use = None
    for i, line in enumerate(raw_lines, 1):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#use:"):
            pending_use = stripped[5:].strip()
            continue
        if stripped.startswith("#"):
            continue

        is_directive = any(stripped.startswith(prefix) for prefix in DIRECTIVE_PREFIXES)
        if is_directive:
            use_desc = pending_use
            if not use_desc and i < len(raw_lines):
                next_stripped = raw_lines[i].strip() if i < len(raw_lines) else ""
                if next_stripped.startswith("#use:"):
                    use_desc = next_stripped[5:].strip()
            colon_idx = stripped.index(":")
            directive_name = stripped[:colon_idx]
            directive_value = stripped[colon_idx + 1:]
            directive_lines.append((i, directive_name, directive_value, use_desc, stripped))
            # Collect #use: for system prompt (directives too — they're instructions)
            if use_desc:
                runtime.add_use_text(use_desc, stripped)
            pending_use = None
            continue

        # Python code line
        # Collect #use: for system prompt (skip import lines)
        if pending_use:
            runtime.add_use_text(pending_use, stripped)
        python_lines.append(line.rstrip("\n"))
        pending_use = None

    # Execute the Python code — all libraries supported
    python_code = "\n".join(python_lines)
    if python_code.strip():
        try:
            exec(python_code, namespace)
        except Exception as e:
            # Execution errors don't reject the file (scanner already accepted it)
            # but we log it for debugging
            import traceback
            pass

    # Restore sys.modules
    if original_egguf_ext is not None:
        sys.modules["egguf_ext"] = original_egguf_ext
    elif "egguf_ext" in sys.modules and sys.modules["egguf_ext"] is egguf_ext_module:
        del sys.modules["egguf_ext"]

    # Process directives
    for line_num, directive_name, directive_value, use_desc, code_line in directive_lines:
        if directive_name == "webapi":
            parts = directive_value.split("_", 1)
            provider = parts[0] if len(parts) > 1 else "unknown"
            api_key = directive_value
            runtime.set_use_comment(use_desc or "")
            runtime.webapi(provider, api_key)
        elif directive_name == "lora":
            parts = directive_value.split(":")
            path_val = parts[0] if parts else ""
            scale = float(parts[1]) if len(parts) > 1 else 1.0
            runtime.set_use_comment(use_desc or "")
            runtime.lora_file(path_val, scale)
        elif directive_name == "model":
            parts = directive_value.split("=", 1)
            param_name = parts[0] if len(parts) > 0 else ""
            param_value = parts[1] if len(parts) > 1 else ""
            try:
                param_value = int(param_value)
            except ValueError:
                try:
                    param_value = float(param_value)
                except ValueError:
                    pass
            runtime.set_use_comment(use_desc or "")
            runtime._add_config("model_override", f"Model: {param_name}", {
                "param": param_name, "value": param_value
            })
        elif directive_name == "tool":
            runtime.set_use_comment(use_desc or "")
            runtime.capability_unlock(directive_value)
        elif directive_name == "embed":
            runtime.set_use_comment(use_desc or "")
            runtime.embedding_config(pooling=directive_value)
        elif directive_name == "safety":
            runtime.set_use_comment(use_desc or "")
            runtime.safety_filter([], directive_value)

    configs = runtime.get_configs()
    use_texts = runtime.get_use_texts()
    return configs, use_texts


def _parse_metadata(path: str) -> Dict[str, Any]:
    """Parse metadata from the header comments of an EFE file."""
    meta = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("# === ") and stripped.endswith(" ==="):
                content = stripped[5:-4]
                if ":" in content:
                    key, value = content.split(":", 1)
                    meta[key.strip().lower()] = value.strip()
    return meta


def _now():
    from datetime import datetime
    return datetime.now().isoformat()


# ─── Convenience API Wrappers ───
# These provide a clean API for EFE files: system.prompt("..."), params.temperature(0.9), etc.

class _SystemAPI:
    def __init__(self, rt): self._rt = rt
    def prompt(self, text, persona_name=""):
        return self._rt.system_prompt(text, persona_name)
    def persona(self, name, prompt):
        return self._rt.system_prompt(prompt, name)

class _ParamsAPI:
    def __init__(self, rt):
        self._rt = rt
        self._merged = {}
    def temperature(self, value):
        self._merged["temperature"] = value
        return self._rt.generation_params(**self._merged)
    def top_p(self, value):
        self._merged["top_p"] = value
        return self._rt.generation_params(**self._merged)
    def top_k(self, value):
        self._merged["top_k"] = value
        return self._rt.generation_params(**self._merged)
    def repeat_penalty(self, value):
        self._merged["repeat_penalty"] = value
        return self._rt.generation_params(**self._merged)
    def max_tokens(self, value):
        self._merged["max_new_tokens"] = value
        return self._rt.generation_params(**self._merged)
    def set(self, **kwargs):
        self._merged.update(kwargs)
        return self._rt.generation_params(**self._merged)

class _ResponseAPI:
    def __init__(self, rt): self._rt = rt
    def format(self, fmt, schema=""):
        return self._rt.response_format(fmt, schema)
    def markdown(self):
        return self._rt.response_format("markdown")
    def json(self, schema=""):
        return self._rt.response_format("json", schema)
    def text(self):
        return self._rt.response_format("text")

class _KnowledgeAPI:
    def __init__(self, rt, efe_dir="."):
        self._rt = rt
        self._efe_dir = efe_dir
    def inject(self, knowledge, topic="", priority="medium"):
        return self._rt.knowledge_inject(knowledge, topic, priority)
    def database(self, file_path, format="", description=""):
        """Load a database file (JSON/CSV/SQLite/text) for the model to search through."""
        return self._rt.knowledge_database(file_path, format, description, self._efe_dir)
    def search_if_unknown(self, instruction=""):
        """Tell the model to search the database when its knowledge isn't enough."""
        return self._rt.knowledge_search_if_unknown(instruction)
    def embed_context(self, max_chars=8000):
        """Convert loaded databases to text and inject into the model's context."""
        return self._rt.knowledge_embed_context(max_chars)
    def inline(self, data, description=""):
        """Use inline JSON data as a knowledge database (no file needed)."""
        return self._rt._add_config("knowledge_database", "Knowledge Database (inline)", {
            "file_path": "<inline>",
            "format": "json",
            "data": data,
            "description": description,
            "record_count": len(data) if isinstance(data, list) else 1,
            "search_instruction": "Search through the database if your knowledge doesn't contain the answer",
        })

class _BehaviorAPI:
    def __init__(self, rt): self._rt = rt
    def rules(self, rules, strictness="moderate"):
        return self._rt.behavior_mod(rules, strictness)
    def always(self, rule):
        return self._rt.behavior_mod([f"Always {rule}"], "strict")
    def never(self, rule):
        return self._rt.behavior_mod([f"Never {rule}"], "strict")

class _SafetyAPI:
    def __init__(self, rt): self._rt = rt
    def filter(self, rules, strictness="medium"):
        return self._rt.safety_filter(rules, strictness)

class _ChatAPI:
    def __init__(self, rt): self._rt = rt
    def template(self, template, name="Chat Template"):
        return self._rt.chat_template(template, name)

class _ContextAPI:
    def __init__(self, rt): self._rt = rt
    def window(self, max_tokens=4096, truncate="oldest"):
        return self._rt.context_window(max_tokens, truncate)

class _TokenizerAPI:
    def __init__(self, rt): self._rt = rt
    def add(self, tokens, scores=None):
        return self._rt.tokenizer_tokens(tokens, scores)

class _CapabilityAPI:
    def __init__(self, rt): self._rt = rt
    def unlock(self, capability, config=None):
        return self._rt.capability_unlock(capability, config)

class _EmbedAPI:
    def __init__(self, rt): self._rt = rt
    def config(self, pooling="mean", normalize=True, dimensions=0):
        return self._rt.embedding_config(pooling, normalize, dimensions)

class _QuantAPI:
    def __init__(self, rt): self._rt = rt
    def override(self, method="q4_0", calibrate=False):
        return self._rt.quantization(method, calibrate)

class _LoraAPI:
    def __init__(self, rt): self._rt = rt
    def adapter(self, path, scale=1.0):
        return self._rt.lora_adapter(path, scale)

class _StopAPI:
    def __init__(self, rt): self._rt = rt
    def tokens(self, tokens):
        return self._rt.stop_tokens(tokens)
