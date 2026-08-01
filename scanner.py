"""
EGGUF File Scanner

The scanner is the validation gate inside EGGUF. Before an EFE
file is accepted and applied to a model, the scanner:

1. Reads the EFE file line by line
2. Classifies each line: #use: (system prompt), Python code, directive, header, or blank
3. Validates that EVERY code/directive line has an associated #use: annotation
   (either immediately before OR after it)
4. Returns a structured ScanResult with the full breakdown
5. If any code/directive line is missing a #use: annotation → REJECT the file

IMPORTANT: The #use: text IS the system prompt. It serves two purposes:
  1. Validation — every code line must have one (scanner checks this)
  2. System prompt — the #use: text becomes the actual instructions the model sees

So #use: must be written clearly, as instructions to the model.

Supported directive prefixes (non-Python lines parsed by EGGUF):
  webapi:    External web API configuration (e.g. webapi:brave_API_KEY)
  lora:      LoRA adapter file reference (e.g. lora:path:scale)
  model:     Direct model parameter override (e.g. model:temperature=0.8)
  tool:      Enable a capability (e.g. tool:code_execution)
  embed:     Embedding configuration (e.g. embed:mean)
  safety:    Safety strictness level (e.g. safety:high)

Usage:
  from scanner import scan_efe
  result = scan_efe("creative_writer.efe")
  if result.accepted:
      print("File accepted!")
      for item in result.items:
          print(f"  {item.code_line}")
          print(f"    #use: {item.use_description}")
  else:
      print(f"REJECTED: {result.error}")
"""

import os
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


# Directives that are NOT Python code but EGGUF-specific configuration lines
DIRECTIVE_PREFIXES = ("webapi:", "lora:", "model:", "tool:", "embed:", "safety:")


@dataclass
class ScanItem:
    """A single code/directive line with its #use: system prompt annotation."""
    line_number: int
    code_line: str
    use_description: str  # the #use: text — this IS the system prompt
    line_type: str  # "python" or "directive"
    directive_name: str = ""  # e.g. "webapi" for directive lines
    is_import: bool = False  # True if this is an import line (not part of system prompt)


@dataclass
class ScanResult:
    """Result of scanning an EFE file."""
    accepted: bool
    items: List[ScanItem] = field(default_factory=list)
    error: str = ""
    error_line: int = 0
    total_lines: int = 0
    code_lines: int = 0
    use_comments: int = 0
    header_lines: int = 0
    file_path: str = ""

    @property
    def system_prompt_lines(self) -> List[ScanItem]:
        """Return only the items whose #use: text contributes to the system prompt
        (i.e. not import lines)."""
        return self.items

    @property
    def system_prompt_text(self) -> str:
        """The system prompt built from ALL #use: annotations. Every #use: text IS the system prompt."""
        texts = [item.use_description for item in self.items]
        if not texts:
            return ""
        return "\n".join(f"- {t}" for t in texts)


def scan_efe(file_path: str) -> ScanResult:
    """
    Scan an EFE file and validate all #use: annotations.

    The #use: text is the system prompt — it must be present for every
    code/directive line, and it must be clear.

    Returns a ScanResult. If accepted=False, the file is rejected
    and should not be applied to any EGGUF model.
    """
    if not os.path.exists(file_path):
        return ScanResult(accepted=False, error=f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        raw_lines = f.read().splitlines()

    result = ScanResult(accepted=True, total_lines=len(raw_lines), file_path=file_path)

    parsed = []
    pending_use = None
    bracket_depth = 0  # Track multi-line expressions: (), [], {}

    for i, line in enumerate(raw_lines, 1):
        stripped = line.strip()

        if not stripped:
            if bracket_depth == 0:
                parsed.append((i, line, "blank", None))
            continue

        if stripped.startswith("#use:"):
            if bracket_depth == 0:
                use_text = stripped[5:].strip()
                parsed.append((i, line, "use", use_text))
                result.use_comments += 1
                pending_use = use_text
            continue

        if stripped.startswith("#"):
            if bracket_depth == 0:
                parsed.append((i, line, "header", None))
                result.header_lines += 1
            continue

        # Track bracket depth for multi-line expressions
        open_brackets = stripped.count("(") + stripped.count("[") + stripped.count("{")
        close_brackets = stripped.count(")") + stripped.count("]") + stripped.count("}")

        is_directive = (bracket_depth == 0 and 
                       any(stripped.startswith(prefix) for prefix in DIRECTIVE_PREFIXES))

        if is_directive:
            colon_idx = stripped.index(":")
            directive_name = stripped[:colon_idx]
            use_desc = pending_use
            parsed.append((i, stripped, "directive", {
                "use": use_desc,
                "directive": directive_name,
                "pending_use": pending_use is not None
            }))
            pending_use = None
            result.code_lines += 1
            # Update bracket depth in case directive has brackets
            bracket_depth += open_brackets - close_brackets
            continue

        if bracket_depth > 0:
            # We're inside a multi-line expression — this is a continuation line
            # Don't require #use: for continuation lines
            parsed.append((i, stripped, "continuation", {
                "use": None,
                "is_continuation": True
            }))
            bracket_depth += open_brackets - close_brackets
            continue

        use_desc = pending_use
        is_import = stripped.startswith("import ") or stripped.startswith("from ")
        parsed.append((i, stripped, "code", {
            "use": use_desc,
            "pending_use": pending_use is not None,
            "is_import": is_import
        }))
        pending_use = None
        result.code_lines += 1
        bracket_depth += open_brackets - close_brackets

    for idx, (line_num, text, category, data) in enumerate(parsed):
        if category not in ("code", "directive"):
            continue  # skip blank, use, header, and continuation lines

        use_before = data["use"] if isinstance(data, dict) and data.get("use") else None

        use_after = None
        if idx + 1 < len(parsed):
            next_line = parsed[idx + 1]
            if next_line[2] == "use":
                use_after = next_line[3]

        final_use = use_before or use_after

        if final_use is None:
            result.accepted = False
            result.error_line = line_num
            line_type = "directive" if category == "directive" else "code"
            result.error = (
                f"Line {line_num} is missing a #use: annotation.\n"
                f"  -> {text}\n\n"
                f"Every {line_type} line MUST have a #use: comment.\n"
                f"The #use: text IS the system prompt — it tells the model what to do.\n"
                f"Place #use: either immediately BEFORE or AFTER the code line.\n"
                f"Write it clearly, as an instruction to the model."
            )
            return result

        directive_name = ""
        is_import = False
        if category == "directive" and isinstance(data, dict):
            directive_name = data.get("directive", "")
        if category == "code" and isinstance(data, dict):
            is_import = data.get("is_import", False)

        item = ScanItem(
            line_number=line_num,
            code_line=text,
            use_description=final_use,
            line_type=category,
            directive_name=directive_name,
            is_import=is_import,
        )
        result.items.append(item)

    return result


def scan_result_to_dict(result: ScanResult) -> Dict[str, Any]:
    """Convert a ScanResult to a dict for display/serialization."""
    return {
        "accepted": result.accepted,
        "error": result.error,
        "error_line": result.error_line,
        "total_lines": result.total_lines,
        "code_lines": result.code_lines,
        "use_comments": result.use_comments,
        "header_lines": result.header_lines,
        "system_prompt": result.system_prompt_text,
        "items": [
            {
                "line_number": item.line_number,
                "code_line": item.code_line,
                "use_description": item.use_description,
                "line_type": item.line_type,
                "directive_name": item.directive_name,
                "is_import": item.is_import,
            }
            for item in result.items
        ],
    }


def format_scan_report(result: ScanResult) -> str:
    """Format a scan result as a readable report string."""
    lines = []
    lines.append("=" * 60)
    lines.append("  EGGUF FILE SCANNER REPORT")
    lines.append("=" * 60)
    lines.append(f"  File: {os.path.basename(result.file_path)}")
    lines.append(f"  Total lines: {result.total_lines}")
    lines.append(f"  Code/directive lines: {result.code_lines}")
    lines.append(f"  #use: annotations: {result.use_comments}")
    lines.append(f"  Header/comments: {result.header_lines}")
    lines.append("")

    if not result.accepted:
        lines.append(f"  REJECTED")
        lines.append(f"  Error (line {result.error_line}):")
        lines.append(f"  {result.error}")
        lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)

    lines.append(f"  ACCEPTED - All code lines have #use: annotations")
    lines.append("")

    # Show the system prompt built from ALL #use: annotations
    lines.append("  System Prompt (from #use: annotations):")
    lines.append("  " + "-" * 56)
    for item in result.items:
        tag = f"[{item.directive_name}]" if item.line_type == "directive" else "[code]"
        if item.is_import:
            tag = "[import]"
        lines.append(f"  Line {item.line_number:3d} {tag}")
        lines.append(f"    Code: {item.code_line}")
        lines.append(f"    #use: {item.use_description}")
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)
