#!/usr/bin/env python3
"""
EGGUF — Extensible GGUF System

Entry point. Works standalone — no sample files required.

Commands:
  open <file.egguf>              Open an EGGUF file in the GUI
  convert <file.gguf> [out]      Convert GGUF to EGGUF format
  scan <file.efe>                Scan an EFE file (validate #use: + show system prompt)
  apply <file.egguf> <ext.efe>   Scan + apply EFE extensions to an EGGUF file
  create-efe                     Open the EFE Creator GUI
  info <file.egguf>              Show EGGUF file information (CLI)
  export <file.egguf> [out]      Export the underlying GGUF data
  samples                        List sample EFE files (if any exist)

The #use: annotations in EFE files ARE the system prompt.
All Python libraries are supported in EFE files.
"""

import sys
import os


def main():
    if len(sys.argv) < 2:
        _print_usage()
        return

    cmd = sys.argv[1].lower()

    if cmd == "open":
        if len(sys.argv) < 3:
            print("Usage: python main.py open <file.egguf>")
            sys.exit(1)
        _open_gui(sys.argv[2])

    elif cmd == "convert":
        if len(sys.argv) < 3:
            print("Usage: python main.py convert <file.gguf> [output.egguf]")
            sys.exit(1)
        from converter import convert_gguf_to_egguf
        output = sys.argv[3] if len(sys.argv) > 3 else None
        convert_gguf_to_egguf(sys.argv[2], output)

    elif cmd == "apply":
        if len(sys.argv) < 4:
            print("Usage: python main.py apply <file.egguf> <ext.efe>")
            sys.exit(1)
        from converter import apply_efe_file_to_egguf
        output = sys.argv[4] if len(sys.argv) > 4 else None
        apply_efe_file_to_egguf(sys.argv[2], sys.argv[3], output)

    elif cmd == "scan":
        if len(sys.argv) < 3:
            print("Usage: python main.py scan <file.efe>")
            sys.exit(1)
        from converter import scan_efe_file
        accepted = scan_efe_file(sys.argv[2])
        sys.exit(0 if accepted else 1)

    elif cmd == "create-efe":
        _open_efe_creator()

    elif cmd == "info":
        if len(sys.argv) < 3:
            print("Usage: python main.py info <file.egguf>")
            sys.exit(1)
        from converter import info_egguf
        info_egguf(sys.argv[2])

    elif cmd == "export":
        if len(sys.argv) < 3:
            print("Usage: python main.py export <file.egguf> [output.gguf]")
            sys.exit(1)
        from converter import export_gguf_from_egguf
        output = sys.argv[3] if len(sys.argv) > 3 else None
        export_gguf_from_egguf(sys.argv[2], output)

    elif cmd == "samples":
        _list_samples()

    elif cmd in ("--help", "-h", "help"):
        _print_usage()

    else:
        print(f"Unknown command: {cmd}")
        _print_usage()
        sys.exit(1)


def _list_samples():
    """List sample EFE files if the directory exists. Works standalone without it."""
    samples_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_extensions")
    if not os.path.isdir(samples_dir):
        print("No sample_extensions/ directory found.")
        print("The system works without samples — create your own EFE files with:")
        print("  python main.py create-efe")
        return

    efe_files = [f for f in sorted(os.listdir(samples_dir)) if f.endswith(".efe")]
    if not efe_files:
        print("No .efe files found in sample_extensions/")
        print("Create your own with: python main.py create-efe")
        return

    print(f"Sample EFE files ({len(efe_files)}):")
    for f in efe_files:
        print(f"  {f}")
    print()
    print("Scan one with: python main.py scan sample_extensions/<file>.efe")


def _print_usage():
    print("""
EGGUF — Extensible GGUF System
================================

Commands:
  open <file.egguf>              Open an EGGUF file in the GUI
  convert <file.gguf> [out]      Convert GGUF to EGGUF format
  scan <file.efe>                Scan an EFE file (validate #use: + show system prompt)
  apply <file.egguf> <ext.efe>   Scan + apply EFE extensions to an EGGUF file
  create-efe                     Open the EFE Creator GUI
  info <file.egguf>              Show EGGUF file information (CLI)
  export <file.egguf> [out]      Export the underlying GGUF data
  samples                        List sample EFE files (if any exist)

EFE Format:
  EFE files are Python code with #use: annotations.
  The #use: text IS the system prompt — it tells the model what to do.
  Every code/directive line MUST have a #use: comment.
  The scanner validates these before accepting the file.
  ALL Python libraries are supported.

Examples:
  python main.py convert model.gguf
  python main.py open model.egguf
  python main.py scan my_extension.efe
  python main.py apply model.egguf my_extension.efe
  python main.py create-efe
""")


def _open_gui(egguf_path: str):
    """Open the EGGUF GUI."""
    from gui import EGGUFApp
    app = EGGUFApp(egguf_path)
    app.run()


def _open_efe_creator():
    """Open the EFE Creator GUI."""
    from efe_creator import EFECreator
    creator = EFECreator()
    creator.win.mainloop()


if __name__ == "__main__":
    main()
