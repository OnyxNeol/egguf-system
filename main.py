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
    # Handle double-click file opening (file path passed as first arg)
    # On all platforms, double-clicking a .egguf or .efe file passes the path
    if len(sys.argv) >= 2:
        arg = sys.argv[1]
        # If the first arg is a file path (not a command), open it
        if os.path.isfile(arg) or (not arg.startswith("-") and "." in arg and arg.lower() not in ("help", "--help", "-h")):
            ext = os.path.splitext(arg)[1].lower()
            if ext == ".egguf":
                _open_gui(arg)
                return
            elif ext == ".efe":
                _open_efe_file(arg)
                return
            elif ext == ".gguf":
                # Double-clicking a GGUF offers conversion
                _open_gguf_file(arg)
                return

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


def _open_efe_file(efe_path: str):
    """Open an EFE file — scan it and offer to apply or view."""
    from scanner import scan_efe, format_scan_report
    print(f"Scanning EFE file: {efe_path}")
    print()
    result = scan_efe(efe_path)
    report = format_scan_report(result)
    print(report)

    if result.accepted:
        print()
        print("This EFE file is valid and can be applied to an EGGUF model.")
        print(f"Use: egguf apply <model.egguf> {efe_path}")
        # Try GUI preview
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo("EFE File Valid",
                f"Scanned: {os.path.basename(efe_path)}\n\n"
                f"Code lines: {result.code_lines}\n"
                f"#use: annotations: {result.use_comments}\n\n"
                f"System prompt extracted successfully.\n"
                f"Apply with: egguf apply <model.egguf> {efe_path}")
            root.destroy()
        except Exception:
            pass

def _open_gguf_file(gguf_path: str):
    """Open a GGUF file — offer to convert to EGGUF."""
    print(f"GGUF file detected: {gguf_path}")
    print()
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        result = messagebox.askyesno("Convert to EGGUF?",
            f"GGUF file: {os.path.basename(gguf_path)}\n\n"
            f"Convert to EGGUF format?\n"
            f"This will create an EGGUF file that can be extended with EFE files.")
        if result:
            from converter import convert_gguf_to_egguf
            convert_gguf_to_egguf(gguf_path)
            messagebox.showinfo("Done", "Conversion complete!")
        root.destroy()
    except Exception:
        print("Convert with: egguf convert " + gguf_path)

def _open_gui(egguf_path: str):
    """Open the EGGUF GUI. Falls back to CLI info if tkinter not available."""
    try:
        from gui import EGGUFApp
        app = EGGUFApp(egguf_path)
        app.run()
    except ImportError:
        # tkinter not available (headless) — show CLI info instead
        print(f"\nEGGUF file: {egguf_path}")
        print("GUI not available (tkinter missing). Showing file info:\n")
        from converter import info_egguf
        info_egguf(egguf_path)
        print("\nTo use the GUI, install tkinter:")
        print("  Linux: sudo apt install python3-tk")
        print("  macOS: brew install python-tk")
        print("  Windows: included with Python")


def _open_efe_creator():
    """Open the EFE Creator GUI. Falls back to CLI if tkinter not available."""
    try:
        from efe_creator import EFECreator
        creator = EFECreator()
        creator.win.mainloop()
    except ImportError:
        print("GUI not available (tkinter missing).")
        print("Create EFE files manually — see sample_extensions/ for examples.")
        print("EFE files are Python code with #use: annotations.")
        print("Install tkinter: sudo apt install python3-tk")


if __name__ == "__main__":
    main()
