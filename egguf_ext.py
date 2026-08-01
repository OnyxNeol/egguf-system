"""
EGGUF Extension Runtime API

This module provides the API that EFE (Python-based) extension files use
to configure model behavior. When an EFE file is executed, this module
is injected into the namespace so the code can call functions like:

    egguf_ext.system_prompt("You are a helpful assistant")
    egguf_ext.generation_params(temperature=0.9)
    egguf_ext.response_format("markdown")
    egguf_ext.webapi("brave", "brave_api_key_here")

KEY CONCEPT: The #use: annotations in EFE files ARE the system prompt.
The text after #use: for each code line becomes part of the system prompt
that gets injected into the model. The runtime collects these texts and
builds the system prompt automatically.

The code/directive lines configure the technical aspects (temperature,
response format, web APIs, etc.) while the #use: text configures the
behavioral/instructional aspects (the system prompt).
"""

import json
from typing import Dict, Any, List, Optional


class ExtensionRuntime:
    """Captures extension configurations from executing EFE Python code.

    The #use: annotations are collected as the system prompt text.
    Technical configs come from the Python code and directives.
    """

    def __init__(self):
        self.configs: List[Dict[str, Any]] = []
        self.use_texts: List[str] = []  # collected #use: annotations → system prompt
        self._current_use = None

    def add_use_text(self, use_text: str, code_line: str = ""):
        """Collect a #use: annotation as part of the system prompt.
        
        ALL #use: texts are part of the system prompt — no exceptions.
        The #use: text IS the system prompt, so every annotation matters.
        """
        if not use_text:
            return
        self.use_texts.append(use_text)
        self._current_use = use_text

    def set_use_comment(self, use_text: str):
        """Set the #use: comment for the next code/directive line."""
        self._current_use = use_text

    def _add_config(self, ext_type: str, name: str, data: dict, description: str = ""):
        """Internal: record a configuration."""
        config = {
            "ext_type": ext_type,
            "name": name,
            "description": description or self._current_use or "",
            "data": data,
        }
        self.configs.append(config)
        self._current_use = None
        return config

    # ─── System Prompt (from #use: annotations) ───

    def build_system_prompt(self) -> Optional[Dict[str, Any]]:
        """Build the system prompt config from collected #use: annotations.
        
        The #use: texts are the system prompt — they tell the model what to do.
        Returns a config dict, or None if no #use: texts were collected.
        """
        if not self.use_texts:
            return None

        # Join all #use: texts as the system prompt
        prompt_text = "\n".join(f"- {t}" for t in self.use_texts)

        # Check if a system.prompt() was also called — merge them
        existing_prompt = ""
        for c in self.configs:
            if c["ext_type"] == "system_prompt" and c["name"] == "EGGUF System Prompt (from #use:)":
                existing_prompt = c["data"].get("prompt", "")
                break

        if existing_prompt:
            prompt_text = prompt_text + "\n\n" + existing_prompt

        return {
            "ext_type": "system_prompt",
            "name": "EGGUF System Prompt (from #use:)",
            "description": "System prompt built from #use: annotations in the EFE file",
            "data": {
                "prompt": prompt_text,
                "persona_name": "EGGUF Extension",
                "use_texts": self.use_texts,
            },
        }

    # ─── Model Behavior APIs ───

    def system_prompt(self, prompt: str, persona_name: str = ""):
        """Set an additional system prompt / persona for the model.
        
        This is APPENDED to the #use:-derived system prompt.
        The #use: annotations are the primary system prompt.
        """
        return self._add_config("system_prompt", persona_name or "Additional System Prompt",
                                {"prompt": prompt, "persona_name": persona_name})

    def generation_params(self, temperature: float = 0.8, top_p: float = 0.95,
                          top_k: int = 40, repeat_penalty: float = 1.1,
                          max_new_tokens: int = 2048):
        """Set generation parameters."""
        return self._add_config("generation_params", "Generation Parameters", {
            "temperature": temperature, "top_p": top_p, "top_k": top_k,
            "repeat_penalty": repeat_penalty, "max_new_tokens": max_new_tokens
        })

    def response_format(self, fmt: str = "text", schema: str = ""):
        """Set response format (text, json, markdown, xml)."""
        return self._add_config("response_format", "Response Format",
                                {"format": fmt, "schema": schema})

    def prompt_template(self, template: str, name: str = "Custom Template"):
        """Set a prompt formatting template."""
        return self._add_config("prompt_template", name, {"template": template, "name": name})

    def chat_template(self, template: str, name: str = "Chat Template"):
        """Set a Jinja-style chat formatting template."""
        return self._add_config("chat_template", name, {"template": template, "name": name})

    def context_window(self, max_tokens: int = 4096, truncate_strategy: str = "oldest"):
        """Modify context window settings."""
        return self._add_config("context_window", "Context Window", {
            "max_tokens": max_tokens, "truncate_strategy": truncate_strategy
        })

    def tokenizer_tokens(self, tokens: list, scores: list = None):
        """Add custom tokens to the tokenizer."""
        return self._add_config("tokenizer", "Custom Tokens", {
            "tokens": tokens, "scores": scores or []
        })

    def quantization(self, method: str = "q4_0", calibrate: bool = False):
        """Override quantization settings."""
        return self._add_config("quantization", "Quantization Override", {
            "method": method, "calibrate": calibrate
        })

    def safety_filter(self, rules: list, strictness: str = "medium"):
        """Add safety filtering rules."""
        return self._add_config("safety_filter", "Safety Filter", {
            "rules": rules, "strictness": strictness
        })

    def stop_tokens(self, tokens: list):
        """Add custom stop tokens."""
        return self._add_config("stop_tokens", "Stop Tokens", {"tokens": tokens})

    def embedding_config(self, pooling: str = "mean", normalize: bool = True,
                         dimensions: int = 0):
        """Configure embedding generation."""
        return self._add_config("embedding_config", "Embedding Config", {
            "pooling": pooling, "normalize": normalize,
            "dimensions": dimensions if dimensions > 0 else None
        })

    def knowledge_inject(self, knowledge: str, topic: str = "", priority: str = "medium"):
        """Inject domain knowledge into the model's context."""
        return self._add_config("knowledge_inject", f"Knowledge: {topic}" if topic else "Knowledge Injection", {
            "knowledge": knowledge, "topic": topic, "priority": priority
        })

    def knowledge_database(self, file_path: str, format: str = "", description: str = "",
                           efe_dir: str = "."):
        """Load a database file and store it as a searchable knowledge extension.

        Supports JSON, CSV, SQLite, and text files.
        The database is embedded in the EGGUF extension so the model
        can search through it when its own knowledge isn't enough.

        The #use: annotation on the knowledge.database() line should
        instruct the model to search the database when needed.
        """
        import os as _os

        # Resolve path relative to EFE file directory
        full_path = file_path
        if not _os.path.isabs(full_path):
            full_path = _os.path.join(efe_dir, file_path)

        if not _os.path.exists(full_path):
            # Store a reference even if file not found (for portable EFE files)
            return self._add_config("knowledge_database",
                f"Knowledge Database: {_os.path.basename(file_path)}", {
                    "file_path": file_path,
                    "format": format or self._detect_db_format(file_path),
                    "data": None,
                    "description": description,
                    "error": f"Database file not found: {full_path}",
                    "search_instruction": "Search through the database if your knowledge doesn't contain the answer",
                })

        # Detect format from extension
        if not format:
            format = self._detect_db_format(file_path)

        # Load and parse the database
        data = self._load_database(full_path, format)

        return self._add_config("knowledge_database",
            f"Knowledge Database: {_os.path.basename(file_path)}", {
                "file_path": file_path,
                "format": format,
                "data": data,
                "description": description,
                "record_count": len(data) if isinstance(data, list) else 1,
                "search_instruction": "Search through the database if your knowledge doesn't contain the answer",
            })

    def knowledge_search_if_unknown(self, instruction: str = ""):
        """Add a system prompt instruction telling the model to search the database
        when its built-in knowledge doesn't contain the answer."""
        instr = instruction or (
            "Search through the AI/database if your knowledge doesn't contain "
            "the answer to the user. When you search the database, cite which "
            "record the answer came from."
        )
        return self._add_config("knowledge_inject", "Database Search Instruction", {
            "knowledge": instr, "topic": "database_search", "priority": "high"
        })

    def knowledge_embed_context(self, max_chars: int = 8000):
        """Convert loaded databases to text context for the system prompt.
        This injects the database content directly into the model's context window
        so it can search through it at inference time."""
        # Find all knowledge_database configs and convert them to text
        contexts = []
        for c in self.configs:
            if c.get("ext_type") == "knowledge_database":
                data = c.get("data", {}).get("data")
                if data is None:
                    continue
                text = self._database_to_text(data, c["data"].get("format", "json"))
                if len(text) > max_chars:
                    text = text[:max_chars] + "\n... (truncated)"
                contexts.append({
                    "source": c["name"],
                    "text": text,
                })

        if contexts:
            full_context = "\n\n".join(
                f"=== {ctx['source']} ===\n{ctx['text']}" for ctx in contexts
            )
            return self._add_config("knowledge_inject", "Database Context (Embedded)", {
                "knowledge": full_context,
                "topic": "embedded_database",
                "priority": "high",
            })
        return None

    def _detect_db_format(self, path: str) -> str:
        """Detect database format from file extension."""
        ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
        return {
            "json": "json",
            "csv": "csv",
            "tsv": "csv",
            "txt": "text",
            "md": "text",
            "db": "sqlite",
            "sqlite": "sqlite",
            "sqlite3": "sqlite",
        }.get(ext, "json")

    def _load_database(self, path: str, format: str):
        """Load and parse a database file based on its format."""
        import json as _json
        import csv as _csv

        if format == "json":
            with open(path, "r", encoding="utf-8") as f:
                return _json.load(f)

        elif format == "csv":
            records = []
            with open(path, "r", encoding="utf-8", newline="") as f:
                reader = _csv.DictReader(f)
                for row in reader:
                    records.append(dict(row))
            return records

        elif format == "text":
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            return [{"line": i+1, "content": line.strip()} for line in lines if line.strip()]

        elif format == "sqlite":
            import sqlite3 as _sqlite3
            conn = _sqlite3.connect(path)
            cursor = conn.cursor()
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            result = {}
            for table in tables:
                cursor.execute(f"SELECT * FROM {table}")
                columns = [desc[0] for desc in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
                result[table] = rows
            conn.close()
            return result

        else:
            # Fallback: try JSON, then text
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return _json.load(f)
            except Exception:
                with open(path, "r", encoding="utf-8") as f:
                    return [{"content": f.read()}]

    def _database_to_text(self, data, format: str = "json") -> str:
        """Convert parsed database data to searchable text."""
        import json as _json

        if isinstance(data, list):
            lines = []
            for i, record in enumerate(data):
                if isinstance(record, dict):
                    fields = " | ".join(f"{k}: {v}" for k, v in record.items())
                    lines.append(f"Record {i+1}: {fields}")
                else:
                    lines.append(str(record))
            return "\n".join(lines)
        elif isinstance(data, dict):
            # Could be SQLite (table_name → records) or a single JSON object
            lines = []
            for key, value in data.items():
                if isinstance(value, list):
                    lines.append(f"\n=== Table: {key} ===")
                    for i, record in enumerate(value):
                        if isinstance(record, dict):
                            fields = " | ".join(f"{k}: {v}" for k, v in record.items())
                            lines.append(f"  Record {i+1}: {fields}")
                        else:
                            lines.append(f"  {record}")
                else:
                    lines.append(f"{key}: {value}")
            return "\n".join(lines)
        else:
            return str(data)

    def behavior_mod(self, rules: list, strictness: str = "moderate"):
        """Add behavior modification rules."""
        return self._add_config("behavior_mod", "Behavior Modification", {
            "rules": rules, "strictness": strictness
        })

    def capability_unlock(self, capability: str, config: dict = None):
        """Unlock a specific capability."""
        return self._add_config("capability_unlock", f"Capability: {capability}", {
            "capability": capability, "config": config or {}
        })

    def lora_adapter(self, path: str, scale: float = 1.0):
        """Reference a LoRA adapter file to apply."""
        return self._add_config("lora_adapter", "LoRA Adapter", {
            "path": path, "scale": scale
        })

    # ─── External Integrations ───

    def webapi(self, provider: str, api_key: str):
        """Configure an external web API for knowledge augmentation.
        
        When the model encounters something it doesn't know, it can
        use this API to search for information.
        """
        return self._add_config("webapi", f"WebAPI: {provider}", {
            "provider": provider, "api_key": api_key
        })

    def lora_file(self, path: str, scale: float = 1.0):
        """Reference a LoRA adapter file."""
        return self._add_config("lora_adapter", "LoRA Adapter", {
            "path": path, "scale": scale
        })

    # ─── Results ───

    def get_configs(self) -> List[Dict[str, Any]]:
        """Return all captured configurations, with the #use: system prompt first."""
        configs = []

        # Build system prompt from #use: annotations — this goes FIRST
        sp = self.build_system_prompt()
        if sp:
            configs.append(sp)

        # Add all other configs (skip any system_prompt that was merged)
        for c in self.configs:
            if c["ext_type"] == "system_prompt" and c["name"] == "EGGUF System Prompt (from #use:)":
                continue  # already added above
            configs.append(c)

        return configs

    def get_use_texts(self) -> List[str]:
        """Return the collected #use: annotations."""
        return self.use_texts

    def get_summary(self) -> str:
        """Return a human-readable summary of all extensions."""
        lines = []
        if self.use_texts:
            lines.append("  System Prompt (from #use: annotations):")
            for t in self.use_texts:
                lines.append(f"    - {t}")
        for c in self.configs:
            lines.append(f"  [{c['ext_type']}] {c['name']}")
            if c.get("description"):
                lines.append(f"    → {c['description']}")
        return "\n".join(lines)
