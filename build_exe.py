#!/usr/bin/env python3
"""
Build Script — Creates the gguf2egguf.exe standalone executable

Uses PyInstaller to bundle the GGUF-to-EGGUF converter into a single
executable file that can be run on any Windows machine without Python.

Usage:
  python build_exe.py              # Build gguf2egguf.exe
  python build_exe.py --clean      # Clean build artifacts first

Output:
  dist/gguf2egguf.exe              # Standalone converter executable
"""

import os
import sys
import shutil
import subprocess
import argparse


def main():
    parser = argparse.ArgumentParser(description="Build gguf2egguf.exe")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts first")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    entry_point = os.path.join(script_dir, "gguf2egguf.py")

    if not os.path.exists(entry_point):
        print(f"ERROR: Entry point not found: {entry_point}")
        sys.exit(1)

    if args.clean:
        print("Cleaning build artifacts...")
        for d in ["build", "dist", "__pycache__"]:
            path = os.path.join(script_dir, d)
            if os.path.exists(path):
                shutil.rmtree(path)
                print(f"  Removed {d}/")
        spec_file = os.path.join(script_dir, "gguf2egguf.spec")
        if os.path.exists(spec_file):
            os.remove(spec_file)
            print("  Removed gguf2egguf.spec")

    print()
    print("=" * 50)
    print("  Building gguf2egguf.exe")
    print("  GGUF to EGGUF Converter — Standalone Executable")
    print("=" * 50)
    print()
    print(f"  Entry point: {entry_point}")
    print()

    # Build with PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                    # Single executable
        "--name", "gguf2egguf",         # Output name
        "--noconfirm",                  # Overwrite existing
        "--clean",                      # Clean PyInstaller cache
        "--console",                    # Keep console for CLI output
        # Include tkinter for GUI mode
        "--hidden-import", "tkinter",
        "--hidden-import", "tkinter.filedialog",
        "--hidden-import", "tkinter.messagebox",
        # Add metadata
        "--add-data", os.path.join(script_dir, "egguf_format.py") + os.pathsep + ".",
        "--add-data", os.path.join(script_dir, "efe_format.py") + os.pathsep + ".",
        "--add-data", os.path.join(script_dir, "scanner.py") + os.pathsep + ".",
        "--add-data", os.path.join(script_dir, "egguf_ext.py") + os.pathsep + ".",
        "--add-data", os.path.join(script_dir, "extensions.py") + os.pathsep + ".",
        "--add-data", os.path.join(script_dir, "converter.py") + os.pathsep + ".",
        entry_point,
    ]

    # Skip --add-data for files that don't exist
    filtered_cmd = [sys.executable, "-m", "PyInstaller",
                    "--onefile", "--name", "gguf2egguf", "--noconfirm",
                    "--clean", "--console",
                    "--hidden-import", "tkinter",
                    "--hidden-import", "tkinter.filedialog",
                    "--hidden-import", "tkinter.messagebox"]

    # Add existing source files as data
    for fname in ["egguf_format.py", "efe_format.py", "scanner.py",
                   "egguf_ext.py", "extensions.py", "converter.py"]:
        fpath = os.path.join(script_dir, fname)
        if os.path.exists(fpath):
            sep = ";" if sys.platform == "win32" else ":"
            filtered_cmd.extend(["--add-data", f"{fpath}{sep}."])

    filtered_cmd.append(entry_point)

    print("Running PyInstaller...")
    print(f"  {' '.join(filtered_cmd[:5])} ... {entry_point}")
    print()

    result = subprocess.run(filtered_cmd, cwd=script_dir)

    if result.returncode == 0:
        exe_path = os.path.join(script_dir, "dist", "gguf2egguf")
        if sys.platform == "win32":
            exe_path += ".exe"
        print()
        print(f"  [OK] Build successful!")
        print(f"  Executable: {exe_path}")
        if os.path.exists(exe_path):
            size = os.path.getsize(exe_path)
            print(f"  Size: {size / (1024*1024):.1f} MB")
        print()
        print("  Usage:")
        print("    gguf2egguf model.gguf              # Convert (creates model.egguf)")
        print("    gguf2egguf model.gguf -o out.egguf # Convert with custom output")
        print("    gguf2egguf                        # GUI mode (file picker)")
    else:
        print()
        print(f"  [ERROR] Build failed (exit code {result.returncode})")
        sys.exit(1)


if __name__ == "__main__":
    main()
