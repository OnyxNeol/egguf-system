"""
EGGUF (Extensible GGUF) Binary Format Specification and Implementation

File Structure:
    [5 bytes]  Magic: b"EGGUF"
    [4 bytes]  Version (uint32, little-endian)
    [4 bytes]  Flags (uint32, little-endian)
    [8 bytes]  GGUF data size (uint64, little-endian)
    [N bytes]  GGUF data (the original/underlying model file)
    [4 bytes]  Extension count (uint32)
    For each extension:
        [4 bytes]  Type name length (uint32)
        [T bytes]  Type name (UTF-8 string)
        [4 bytes]  Extension name length (uint32)
        [N bytes]  Extension name (UTF-8 string)
        [4 bytes]  Description length (uint32)
        [D bytes]  Description (UTF-8 string)
        [8 bytes]  Data size (uint64)
        [M bytes]  Extension data (raw bytes, interpreted by type)
    [8 bytes]  Metadata size (uint64)
    [K bytes]  Metadata (JSON: name, description, base_model, created_date, etc.)

The GGUF data is stored verbatim — no modification to the underlying model.
Extensions are layered on top and applied at inference time.
"""

import struct
import json
import os
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

EGGUF_MAGIC = b"EGGUF"
EGGUF_VERSION = 1


@dataclass
class EGGUFExtension:
    """An extension applied to an EGGUF file."""
    ext_type: str        # e.g. "system_prompt", "lora_adapter", "tokenizer"
    name: str            # human-readable name
    description: str     # what this extension does
    data: bytes          # raw extension data (format depends on type)


@dataclass
class EGGUFFile:
    """Represents a parsed EGGUF file."""
    version: int = EGGUF_VERSION
    flags: int = 0
    gguf_data: bytes = b""
    extensions: List[EGGUFExtension] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def has_gguf(self) -> bool:
        return len(self.gguf_data) > 0

    @property
    def gguf_size_mb(self) -> float:
        return len(self.gguf_data) / (1024 * 1024)

    @property
    def extension_count(self) -> int:
        return len(self.extensions)

    def get_extension_names(self) -> List[str]:
        return [ext.name for ext in self.extensions]

    def get_extensions_by_type(self, ext_type: str) -> List[EGGUFExtension]:
        return [ext for ext in self.extensions if ext.ext_type == ext_type]

    def add_extension(self, ext: EGGUFExtension):
        """Add an extension to this EGGUF file."""
        # Remove any existing extension with the same name (replace)
        self.extensions = [e for e in self.extensions if e.name != ext.name]
        self.extensions.append(ext)

    def remove_extension(self, name: str) -> bool:
        """Remove an extension by name. Returns True if found and removed."""
        before = len(self.extensions)
        self.extensions = [e for e in self.extensions if e.name != name]
        return len(self.extensions) < before


def write_egguf(path: str, egguf: EGGUFFile):
    """Write an EGGUFFile to disk."""
    with open(path, "wb") as f:
        # Magic
        f.write(EGGUF_MAGIC)
        # Version
        f.write(struct.pack("<I", egguf.version))
        # Flags
        f.write(struct.pack("<I", egguf.flags))
        # GGUF data size + data
        f.write(struct.pack("<Q", len(egguf.gguf_data)))
        f.write(egguf.gguf_data)
        # Extension count
        f.write(struct.pack("<I", len(egguf.extensions)))
        for ext in egguf.extensions:
            _write_extension(f, ext)
        # Metadata
        meta_json = json.dumps(egguf.metadata, indent=2, default=str).encode("utf-8")
        f.write(struct.pack("<Q", len(meta_json)))
        f.write(meta_json)


def read_egguf(path: str) -> EGGUFFile:
    """Read an EGGUF file from disk."""
    with open(path, "rb") as f:
        magic = f.read(5)
        if magic != EGGUF_MAGIC:
            raise ValueError(f"Not an EGGUF file (bad magic: {magic!r})")
        version = struct.unpack("<I", f.read(4))[0]
        if version > EGGUF_VERSION:
            raise ValueError(f"Unsupported EGGUF version: {version} (max: {EGGUF_VERSION})")
        flags = struct.unpack("<I", f.read(4))[0]
        gguf_size = struct.unpack("<Q", f.read(8))[0]
        gguf_data = f.read(gguf_size)
        ext_count = struct.unpack("<I", f.read(4))[0]
        extensions = []
        for _ in range(ext_count):
            extensions.append(_read_extension(f))
        meta_size = struct.unpack("<Q", f.read(8))[0]
        meta_json = f.read(meta_size)
        metadata = json.loads(meta_json.decode("utf-8")) if meta_json else {}
        return EGGUFFile(
            version=version,
            flags=flags,
            gguf_data=gguf_data,
            extensions=extensions,
            metadata=metadata,
        )


def _write_extension(f, ext: EGGUFExtension):
    """Write a single extension to the file."""
    type_bytes = ext.ext_type.encode("utf-8")
    f.write(struct.pack("<I", len(type_bytes)))
    f.write(type_bytes)
    name_bytes = ext.name.encode("utf-8")
    f.write(struct.pack("<I", len(name_bytes)))
    f.write(name_bytes)
    desc_bytes = ext.description.encode("utf-8")
    f.write(struct.pack("<I", len(desc_bytes)))
    f.write(desc_bytes)
    f.write(struct.pack("<Q", len(ext.data)))
    f.write(ext.data)


def _read_extension(f) -> EGGUFExtension:
    """Read a single extension from the file."""
    tlen = struct.unpack("<I", f.read(4))[0]
    ext_type = f.read(tlen).decode("utf-8")
    nlen = struct.unpack("<I", f.read(4))[0]
    name = f.read(nlen).decode("utf-8")
    dlen = struct.unpack("<I", f.read(4))[0]
    description = f.read(dlen).decode("utf-8")
    dsize = struct.unpack("<Q", f.read(8))[0]
    data = f.read(dsize)
    return EGGUFExtension(ext_type=ext_type, name=name, description=description, data=data)


def create_egguf_from_gguf(
    gguf_path: str,
    output_path: str,
    name: str = "",
    description: str = "",
) -> EGGUFFile:
    """Convert a GGUF file to an EGGUF file."""
    with open(gguf_path, "rb") as f:
        gguf_data = f.read()

    # Try to extract model name from GGUF metadata
    gguf_meta = _parse_gguf_metadata(gguf_data)
    model_name = name or gguf_meta.get("name", "") or os.path.basename(gguf_path)

    egguf = EGGUFFile(
        version=EGGUF_VERSION,
        flags=0,
        gguf_data=gguf_data,
        extensions=[],
        metadata={
            "name": model_name,
            "description": description,
            "base_model": gguf_meta.get("name", os.path.basename(gguf_path)),
            "architecture": gguf_meta.get("architecture", "unknown"),
            "source_gguf": os.path.basename(gguf_path),
            "created_date": datetime.now().isoformat(),
            "gguf_version": gguf_meta.get("version", "unknown"),
        },
    )
    write_egguf(output_path, egguf)
    return egguf


def extract_gguf(egguf_path: str, output_path: str):
    """Extract the underlying GGUF data from an EGGUF file."""
    egguf = read_egguf(egguf_path)
    if not egguf.has_gguf:
        raise ValueError("This EGGUF file contains no GGUF data")
    with open(output_path, "wb") as f:
        f.write(egguf.gguf_data)


def _parse_gguf_metadata(gguf_data: bytes) -> Dict[str, Any]:
    """Parse the metadata header from a GGUF file (best-effort)."""
    meta = {}
    try:
        if gguf_data[:4] != b"GGUF":
            return meta
        version = struct.unpack("<I", gguf_data[4:8])[0]
        meta["version"] = str(version)
        tensor_count = struct.unpack("<Q", gguf_data[8:16])[0]
        kv_count = struct.unpack("<Q", gguf_data[16:24])[0]
        meta["tensor_count"] = tensor_count

        offset = 24
        for _ in range(kv_count):
            key_len = struct.unpack("<Q", gguf_data[offset:offset+8])[0]
            offset += 8
            key = gguf_data[offset:offset+key_len].decode("utf-8", errors="replace")
            offset += key_len
            vtype = struct.unpack("<I", gguf_data[offset:offset+4])[0]
            offset += 4
            value, offset = _read_gguf_value(gguf_data, offset, vtype)
            meta[key] = value
            if key == "general.architecture":
                meta["architecture"] = value
            if key == "general.name":
                meta["name"] = value
    except Exception:
        pass
    return meta


def _read_gguf_value(data: bytes, offset: int, vtype: int):
    """Read a GGUF metadata value. Returns (value, new_offset)."""
    GGUF_UINT8 = 0; GGUF_INT8 = 1; GGUF_UINT16 = 2; GGUF_INT16 = 3
    GGUF_UINT32 = 4; GGUF_INT32 = 5; GGUF_FLOAT32 = 6; GGUF_BOOL = 7
    GGUF_STRING = 8; GGUF_ARRAY = 9; GGUF_UINT64 = 10; GGUF_INT64 = 11; GGUF_FLOAT64 = 12

    if vtype == GGUF_UINT8:
        return data[offset], offset + 1
    elif vtype == GGUF_INT8:
        return struct.unpack("<b", data[offset:offset+1])[0], offset + 1
    elif vtype == GGUF_UINT16:
        return struct.unpack("<H", data[offset:offset+2])[0], offset + 2
    elif vtype == GGUF_INT16:
        return struct.unpack("<h", data[offset:offset+2])[0], offset + 2
    elif vtype == GGUF_UINT32:
        return struct.unpack("<I", data[offset:offset+4])[0], offset + 4
    elif vtype == GGUF_INT32:
        return struct.unpack("<i", data[offset:offset+4])[0], offset + 4
    elif vtype == GGUF_FLOAT32:
        return struct.unpack("<f", data[offset:offset+4])[0], offset + 4
    elif vtype == GGUF_BOOL:
        return data[offset] != 0, offset + 1
    elif vtype == GGUF_STRING:
        slen = struct.unpack("<Q", data[offset:offset+8])[0]
        offset += 8
        return data[offset:offset+slen].decode("utf-8", errors="replace"), offset + slen
    elif vtype == GGUF_UINT64:
        return struct.unpack("<Q", data[offset:offset+8])[0], offset + 8
    elif vtype == GGUF_INT64:
        return struct.unpack("<q", data[offset:offset+8])[0], offset + 8
    elif vtype == GGUF_FLOAT64:
        return struct.unpack("<d", data[offset:offset+8])[0], offset + 8
    elif vtype == GGUF_ARRAY:
        elem_type = struct.unpack("<I", data[offset:offset+4])[0]
        offset += 4
        count = struct.unpack("<Q", data[offset:offset+8])[0]
        offset += 8
        values = []
        for _ in range(count):
            v, offset = _read_gguf_value(data, offset, elem_type)
            values.append(v)
        return values, offset
    else:
        return None, offset
