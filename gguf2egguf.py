#!/usr/bin/env python3
"""
GGUF to EGGUF Converter — Standalone Executable

Converts GGUF model files to EGGUF (Extensible GGUF) format.
The converter adds the #use: system framework as a base extension,
so the model is ready to receive EFE (Extensions For EGGUF) files.

Usage:
  gguf2egguf.exe model.gguf              # Convert (creates model.egguf)
  gguf2egguf.exe model.gguf -o out.egguf # Convert with custom output
  gguf2egguf.exe                         # Opens file picker (GUI mode)
  gguf2egguf.exe --gui                   # Force GUI mode
"""

import sys
import os
import struct
import json
import argparse
from datetime import datetime

# ─── EGGUF Binary Format (embedded for standalone exe) ───

EGGUF_MAGIC = b"EGGUF"
EGGUF_VERSION = 1
EGGUF_FLAGS = 0


class EGGUFExtension:
    def __init__(self, ext_type, name, description, data):
        self.ext_type = ext_type
        self.name = name
        self.description = description
        self.data = data  # bytes (JSON-encoded)


def _write_str(f, s):
    encoded = s.encode('utf-8')
    f.write(struct.pack('<I', len(encoded)))
    f.write(encoded)


def _read_str(f):
    length = struct.unpack('<I', f.read(4))[0]
    return f.read(length).decode('utf-8')


def _parse_gguf_metadata(gguf_data):
    """Extract key metadata from a GGUF file's binary data."""
    meta = {}
    try:
        offset = 0
        magic = gguf_data[offset:offset+4]
        offset += 4
        if magic != b'GGUF':
            return meta

        version = struct.unpack_from('<I', gguf_data, offset)[0]
        offset += 4

        if version >= 1:
            tensor_count = struct.unpack_from('<Q', gguf_data, offset)[0]
            offset += 8
        if version >= 2:
            kv_count = struct.unpack_from('<Q', gguf_data, offset)[0]
            offset += 8
        else:
            kv_count = struct.unpack_from('<I', gguf_data, offset)[0]
            offset += 4

        GGUF_TYPE_NAMES = {
            0: "UINT8", 1: "INT8", 2: "UINT16", 3: "INT16",
            4: "UINT32", 5: "INT32", 6: "FLOAT32", 7: "BOOL",
            8: "STRING", 9: "ARRAY", 10: "UINT64", 11: "INT64", 12: "FLOAT64"
        }

        for _ in range(kv_count):
            key_len = struct.unpack_from('<Q', gguf_data, offset)[0]
            offset += 8
            key = gguf_data[offset:offset+key_len].decode('utf-8', errors='replace')
            offset += key_len

            value_type = struct.unpack_from('<I', gguf_data, offset)[0]
            offset += 4

            if value_type == 8:  # STRING
                str_len = struct.unpack_from('<Q', gguf_data, offset)[0]
                offset += 8
                value = gguf_data[offset:offset+str_len].decode('utf-8', errors='replace')
                offset += str_len
            elif value_type in (4, 5):  # UINT32, INT32
                value = struct.unpack_from('<i', gguf_data, offset)[0]
                offset += 4
            elif value_type == 6:  # FLOAT32
                value = struct.unpack_from('<f', gguf_data, offset)[0]
                offset += 4
            elif value_type == 7:  # BOOL
                value = struct.unpack_from('<B', gguf_data, offset)[0]
                offset += 1
            elif value_type == 10:  # UINT64
                value = struct.unpack_from('<Q', gguf_data, offset)[0]
                offset += 8
            elif value_type == 11:  # INT64
                value = struct.unpack_from('<q', gguf_data, offset)[0]
                offset += 8
            elif value_type == 12:  # FLOAT64
                value = struct.unpack_from('<d', gguf_data, offset)[0]
                offset += 8
            elif value_type == 0:  # UINT8
                value = struct.unpack_from('<B', gguf_data, offset)[0]
                offset += 1
            elif value_type == 1:  # INT8
                value = struct.unpack_from('<b', gguf_data, offset)[0]
                offset += 1
            elif value_type == 2:  # UINT16
                value = struct.unpack_from('<H', gguf_data, offset)[0]
                offset += 2
            elif value_type == 3:  # INT16
                value = struct.unpack_from('<h', gguf_data, offset)[0]
                offset += 2
            elif value_type == 9:  # ARRAY
                value = f"[array:{GGUF_TYPE_NAMES.get(value_type, '?')}]"
                # Skip array — we'd need to parse each element
                break
            else:
                value = f"[type:{value_type}]"
                break

            meta[key] = value
    except Exception:
        pass

    return meta


def convert_gguf_to_egguf(gguf_path, output_path=None):
    """Convert a GGUF file to EGGUF format with the #use: system framework built in.

    The converter adds a base system prompt extension that sets up the
    #use: extension framework, so the model knows it can receive EFE
    extensions with #use: annotations.
    """
    if not os.path.exists(gguf_path):
        print(f"ERROR: GGUF file not found: {gguf_path}")
        return False

    if output_path is None:
        output_path = os.path.splitext(gguf_path)[0] + ".egguf"

    print(f"Converting: {gguf_path}")
    print(f"Output:     {output_path}")

    # Read the GGUF file
    with open(gguf_path, 'rb') as f:
        gguf_data = f.read()

    gguf_size = len(gguf_data)
    print(f"GGUF size:  {gguf_size / (1024*1024):.2f} MB")

    # Parse GGUF metadata
    gguf_meta = _parse_gguf_metadata(gguf_data)
    model_name = gguf_meta.get("general.name", os.path.basename(gguf_path))
    architecture = gguf_meta.get("general.architecture", "unknown")
    file_type = gguf_meta.get("general.file_type", "unknown")

    print(f"Model:      {model_name}")
    print(f"Arch:       {architecture}")
    print(f"Quant:      {file_type}")

    # Build the #use: system framework base extension
    # This is a system prompt that tells the model about the EGGUF extension system
    use_system_prompt = (
        "You are an EGGUF-enhanced AI model. The EGGUF (Extensible GGUF) format "
        "allows extensions to be applied to your model through EFE (Extensions For EGGUF) files.\n\n"
        "EFE files use #use: annotations as the system prompt. Each #use: line "
        "is an instruction that configures your behavior. The EGGUF scanner validates "
        "that every code line in an EFE file has a #use: annotation before accepting it.\n\n"
        "When extensions are applied, they may modify:\n"
        "- Your system prompt (from #use: annotations)\n"
        "- Generation parameters (temperature, top_p, top_k, etc.)\n"
        "- Response format (markdown, json, text)\n"
        "- Behavior rules (always/never rules)\n"
        "- Knowledge injection (domain-specific information)\n"
        "- External web APIs (for searching unknown information)\n"
        "- Safety filters\n"
        "- Chat templates\n"
        "- Context window settings\n\n"
        "You are ready to receive EFE extensions. When a user opens your .egguf file "
        "and applies an EFE extension, the #use: annotations become your new system prompt."
    )

    base_extension = EGGUFExtension(
        ext_type="system_prompt",
        name="EGGUF #use: System Framework",
        description="Base system prompt that sets up the #use: extension framework",
        data=json.dumps({
            "prompt": use_system_prompt,
            "persona_name": "EGGUF Base",
            "is_base_framework": True
        }).encode('utf-8')
    )

    # Build EGGUF metadata
    egguf_metadata = {
        "name": model_name,
        "description": f"EGGUF wrapper for {model_name}",
        "base_model": os.path.basename(gguf_path),
        "architecture": architecture,
        "quantization": str(file_type),
        "created_date": datetime.now().isoformat(),
        "gguf_size": gguf_size,
        "egguf_version": EGGUF_VERSION,
        "has_use_system": True,
    }
    metadata_bytes = json.dumps(egguf_metadata, indent=2).encode('utf-8')

    # Write the EGGUF file
    with open(output_path, 'wb') as f:
        # Header
        f.write(EGGUF_MAGIC)
        f.write(struct.pack('<I', EGGUF_VERSION))
        f.write(struct.pack('<I', EGGUF_FLAGS))

        # GGUF data
        f.write(struct.pack('<Q', gguf_size))
        f.write(gguf_data)

        # Extensions (1 base extension: the #use: system framework)
        f.write(struct.pack('<I', 1))
        _write_str(f, base_extension.ext_type)
        _write_str(f, base_extension.name)
        _write_str(f, base_extension.description)
        f.write(struct.pack('<Q', len(base_extension.data)))
        f.write(base_extension.data)

        # Metadata
        f.write(struct.pack('<Q', len(metadata_bytes)))
        f.write(metadata_bytes)

    egguf_size = os.path.getsize(output_path)
    print(f"EGGUF size: {egguf_size / (1024*1024):.2f} MB")
    print(f"Extensions: 1 (#use: System Framework)")
    print(f"Done! {output_path} created successfully.")
    return True


def gui_mode():
    """Open a file picker dialog to select a GGUF file."""
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox
    except ImportError:
        print("ERROR: tkinter not available. Use CLI mode:")
        print("  gguf2egguf.exe model.gguf")
        return

    root = tk.Tk()
    root.title("GGUF to EGGUF Converter")
    root.geometry("500x350")
    root.configure(bg="#1a1a2e")

    # Title
    title = tk.Label(root, text="EGGUF Converter", font=("Arial", 18, "bold"),
                     fg="#e94560", bg="#1a1a2e")
    title.pack(pady=20)

    subtitle = tk.Label(root, text="Convert GGUF models to Extensible GGUF format",
                       font=("Arial", 10), fg="#a0a0b0", bg="#1a1a2e")
    subtitle.pack(pady=5)

    # File path display
    path_var = tk.StringVar(value="No file selected")
    path_label = tk.Label(root, textvariable=path_var, font=("Consolas", 9),
                         fg="#0f3460", bg="#16213e", width=50, height=2,
                         relief="sunken", anchor="w", padx=10)
    path_label.pack(pady=10)

    # Buttons
    btn_frame = tk.Frame(root, bg="#1a1a2e")
    btn_frame.pack(pady=15)

    def select_file():
        path = filedialog.askopenfilename(
            title="Select GGUF Model File",
            filetypes=[("GGUF Files", "*.gguf"), ("All Files", "*.*")]
        )
        if path:
            path_var.set(path)

    def do_convert():
        gguf_path = path_var.get()
        if gguf_path == "No file selected":
            messagebox.showwarning("No File", "Please select a GGUF file first.")
            return
        if not os.path.exists(gguf_path):
            messagebox.showerror("Error", f"File not found: {gguf_path}")
            return
        output = os.path.splitext(gguf_path)[0] + ".egguf"
        success = convert_gguf_to_egguf(gguf_path, output)
        if success:
            messagebox.showinfo("Success", f"Converted to:\n{output}\n\nThe #use: system framework has been added.")
        else:
            messagebox.showerror("Error", "Conversion failed.")

    select_btn = tk.Button(btn_frame, text="Select GGUF File", command=select_file,
                          font=("Arial", 11), bg="#e94560", fg="white",
                          padx=20, pady=8, relief="raised", cursor="hand2")
    select_btn.pack(side="left", padx=10)

    convert_btn = tk.Button(btn_frame, text="Convert", command=do_convert,
                           font=("Arial", 11, "bold"), bg="#0f3460", fg="white",
                           padx=20, pady=8, relief="raised", cursor="hand2")
    convert_btn.pack(side="left", padx=10)

    # Info
    info = tk.Label(root, text="The converter adds the #use: system framework\n"
                   "so the model is ready for EFE extensions.",
                   font=("Arial", 9), fg="#a0a0b0", bg="#1a1a2e", justify="center")
    info.pack(pady=15)

    root.mainloop()


def main():
    parser = argparse.ArgumentParser(
        description="Convert GGUF files to EGGUF (Extensible GGUF) format"
    )
    parser.add_argument("input", nargs="?", help="Input GGUF file path")
    parser.add_argument("-o", "--output", help="Output EGGUF file path")
    parser.add_argument("--gui", action="store_true", help="Open in GUI mode")
    args = parser.parse_args()

    if args.input is None or args.gui:
        gui_mode()
        return

    output = args.output or os.path.splitext(args.input)[0] + ".egguf"
    success = convert_gguf_to_egguf(args.input, output)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
