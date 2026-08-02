#!/usr/bin/env python3
"""
Full Build Script — Creates the `egguf` executable for all platforms

Builds a standalone executable that handles:
  - Double-click .egguf files → GUI with "Do you want to add extensions?" popup
  - Double-click .efe files → scan and preview
  - Double-click .gguf files → convert to EGGUF
  - CLI: open, convert, scan, apply, create-efe, info, export

NO ICON — logo is completely blank as requested.

Usage:
  python build_full.py              # Build for current platform
  python build_full.py --clean      # Clean + build

Output:
  dist/egguf (Linux/macOS) or dist/egguf.exe (Windows)
"""

import os
import sys
import shutil
import subprocess


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    entry_point = os.path.join(script_dir, "main.py")

    if not os.path.exists(entry_point):
        print(f"ERROR: main.py not found at {entry_point}")
        sys.exit(1)

    # Clean
    for d in ["build", "dist"]:
        path = os.path.join(script_dir, d)
        if os.path.exists(path):
            shutil.rmtree(path)
            print(f"  Cleaned {d}/")
    spec = os.path.join(script_dir, "egguf.spec")
    if os.path.exists(spec):
        os.remove(spec)

    print()
    print("=" * 55)
    print("  Building egguf — Full EGGUF System Executable")
    print("  Platform: " + ("Windows" if sys.platform == "win32" else
                            "macOS" if sys.platform == "darwin" else "Linux"))
    print("  Icon: NONE (blank as requested)")
    print("=" * 55)
    print()

    # Source files to bundle
    source_files = [
        "egguf_format.py", "efe_format.py", "scanner.py", "egguf_ext.py",
        "extensions.py", "converter.py", "gui.py", "efe_creator.py",
    ]

    sep = ";" if sys.platform == "win32" else ":"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "egguf",
        "--noconfirm",
        "--clean",
        "--console",  # Keep console for CLI; GUI still works
    ]

    # Hidden imports for tkinter (GUI)
    cmd.extend([
        "--hidden-import", "tkinter",
        "--hidden-import", "tkinter.filedialog",
        "--hidden-import", "tkinter.messagebox",
        "--hidden-import", "tkinter.ttk",
    ])

    # Hidden imports for database formats
    cmd.extend([
        "--hidden-import", "csv",
        "--hidden-import", "sqlite3",
        "--hidden-import", "json",
    ])

    # Add source files as data (so they can be imported at runtime)
    for fname in source_files:
        fpath = os.path.join(script_dir, fname)
        if os.path.exists(fpath):
            cmd.extend(["--add-data", f"{fpath}{sep}."])

    # Add sample extensions if they exist
    samples_dir = os.path.join(script_dir, "sample_extensions")
    if os.path.isdir(samples_dir):
        cmd.extend(["--add-data", f"{samples_dir}{sep}sample_extensions"])
        print(f"  Including sample_extensions/ ({len(os.listdir(samples_dir))} files)")

    # NO ICON — no --icon flag
    print("  Icon: NONE (blank)")

    cmd.append(entry_point)

    print()
    print("Running PyInstaller...")
    result = subprocess.run(cmd, cwd=script_dir)

    if result.returncode == 0:
        exe_name = "egguf.exe" if sys.platform == "win32" else "egguf"
        exe_path = os.path.join(script_dir, "dist", exe_name)

        print()
        if os.path.exists(exe_path):
            size = os.path.getsize(exe_path)
            print(f"  [OK] Build successful!")
            print(f"  Executable: {exe_path}")
            print(f"  Size: {size / (1024*1024):.1f} MB")
        else:
            print(f"  [OK] Build completed (check dist/)")
        print()
        print("  Usage:")
        print(f"    {exe_name} model.egguf              # Double-click: open EGGUF GUI")
        print(f"    {exe_name} convert model.gguf       # Convert GGUF to EGGUF")
        print(f"    {exe_name} scan extension.efe       # Validate EFE file")
        print(f"    {exe_name} apply model.egguf ext.efe # Apply extensions")
        print(f"    {exe_name} create-efe               # Open EFE Creator GUI")
        print(f"    {exe_name} open model.egguf         # Open EGGUF GUI explicitly")
        print()
        print("  Deploy with:")
        plat = "windows" if sys.platform == "win32" else "macos" if sys.platform == "darwin" else "linux"
        print(f"    deploy/install_{plat}.ps1  (Windows)")
        print(f"    deploy/install_{plat}.sh    (macOS/Linux)")
    else:
        print()
        print(f"  [ERROR] Build failed (exit code {result.returncode})")
        sys.exit(1)


if __name__ == "__main__":
    main()
