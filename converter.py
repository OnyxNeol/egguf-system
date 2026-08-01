"""
GGUF <-> EGGUF Converter

Provides command-line and programmatic conversion between GGUF and EGGUF formats,
and applying Python-based EFE extensions to EGGUF files.
"""

import os
import sys
from datetime import datetime

from egguf_format import (
    EGGUFFile, EGGUFExtension, read_egguf, write_egguf,
    create_egguf_from_gguf, extract_gguf
)
from efe_format import read_efe
from extensions import apply_efe_to_egguf
from scanner import scan_efe, format_scan_report


def convert_gguf_to_egguf(gguf_path: str, output_path: str = None,
                          name: str = "", description: str = "") -> str:
    """Convert a GGUF file to EGGUF format. Returns the output path."""
    if output_path is None:
        base = os.path.splitext(gguf_path)[0]
        output_path = base + ".egguf"

    egguf = create_egguf_from_gguf(gguf_path, output_path, name, description)
    print(f"Converted {gguf_path} -> {output_path}")
    print(f"  Model name: {egguf.metadata.get('name', 'unknown')}")
    print(f"  Architecture: {egguf.metadata.get('architecture', 'unknown')}")
    print(f"  GGUF size: {egguf.gguf_size_mb:.2f} MB")
    return output_path


def apply_efe_file_to_egguf(egguf_path: str, efe_path: str,
                            output_path: str = None,
                            selected_names=None) -> str:
    """
    Apply an EFE extension file to an EGGUF file.
    The EFE file is scanned first — if the scanner rejects it, the file is NOT applied.
    Returns the output path.
    """
    if output_path is None:
        output_path = egguf_path

    # Step 1: Scan the EFE file
    print(f"Scanning EFE file: {efe_path}")
    scan_result = scan_efe(efe_path)
    print(format_scan_report(scan_result))

    if not scan_result.accepted:
        print(f"\n❌ EFE file REJECTED by scanner. Not applying to model.")
        print(f"   Error: {scan_result.error}")
        return egguf_path

    # Step 2: Read and execute the EFE file
    print(f"\nExecuting EFE code...")
    efe = read_efe(efe_path, execute=True)
    
    if not efe.accepted:
        print(f"\n❌ EFE file was rejected. Not applying.")
        return egguf_path

    print(f"  Configurations extracted: {efe.extension_count}")
    for c in efe.configs:
        print(f"    - {c['name']} ({c['ext_type']})")

    # Step 3: Apply to EGGUF
    egguf = read_egguf(egguf_path)
    applied = apply_efe_to_egguf(egguf, efe.configs, selected_names)
    write_egguf(output_path, egguf)

    print(f"\n✅ Applied {len(applied)} extension(s) from {efe_path}")
    for name in applied:
        print(f"  + {name}")
    return output_path


def export_gguf_from_egguf(egguf_path: str, output_path: str = None) -> str:
    """Extract the original GGUF data from an EGGUF file. Returns the output path."""
    if output_path is None:
        base = os.path.splitext(egguf_path)[0]
        output_path = base + ".gguf"

    extract_gguf(egguf_path, output_path)
    print(f"Exported GGUF: {egguf_path} -> {output_path}")
    return output_path


def scan_efe_file(efe_path: str) -> bool:
    """Scan an EFE file and print the report. Returns True if accepted."""
    result = scan_efe(efe_path)
    print(format_scan_report(result))
    return result.accepted


def info_egguf(egguf_path: str) -> dict:
    """Print and return info about an EGGUF file."""
    egguf = read_egguf(egguf_path)
    info = {
        "file": egguf_path,
        "version": egguf.version,
        "name": egguf.metadata.get("name", "unnamed"),
        "architecture": egguf.metadata.get("architecture", "unknown"),
        "base_model": egguf.metadata.get("base_model", "unknown"),
        "gguf_size_mb": egguf.gguf_size_mb,
        "extension_count": egguf.extension_count,
        "extensions": egguf.get_extension_names(),
        "created_date": egguf.metadata.get("created_date", "unknown"),
        "metadata": egguf.metadata,
    }
    print(f"EGGUF File: {egguf_path}")
    print(f"  Name: {info['name']}")
    print(f"  Architecture: {info['architecture']}")
    print(f"  Base Model: {info['base_model']}")
    print(f"  GGUF Size: {info['gguf_size_mb']:.2f} MB")
    print(f"  Extensions ({info['extension_count']}):")
    for name in info["extensions"]:
        print(f"    - {name}")
    return info
