"""
Install Script for EGGUF System

This script:
  1. Verifies Python and tkinter are available
  2. Registers .egguf and .efe file associations
  3. Creates a launcher script
  4. Checks for sample EFE files (optional — system works without them)

Run with: python install.py
"""

import os
import sys
import platform
import subprocess


def main():
    print("=" * 50)
    print("  EGGUF System Installer")
    print("  Extensible GGUF")
    print("=" * 50)
    print()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(script_dir, "main.py")

    # Check Python version
    if sys.version_info < (3, 7):
        print("ERROR: Python 3.7+ required")
        sys.exit(1)
    print(f"[OK] Python {platform.python_version()}")

    # Check tkinter
    try:
        import tkinter
        print("[OK] tkinter available")
    except ImportError:
        print("[ERROR] tkinter not found. Please install python3-tk")
        print("  Ubuntu/Debian: sudo apt install python3-tk")
        print("  macOS: brew install python-tk")
        print("  Windows: Included with Python")
        sys.exit(1)

    # Check for sample EFE files (optional)
    samples_dir = os.path.join(script_dir, "sample_extensions")
    if os.path.isdir(samples_dir):
        efe_count = len([f for f in os.listdir(samples_dir) if f.endswith(".efe")])
        if efe_count > 0:
            print(f"[OK] {efe_count} sample EFE files found in sample_extensions/")
        else:
            print("[INFO] sample_extensions/ exists but has no .efe files")
    else:
        print("[INFO] No sample_extensions/ directory (system works without it)")

    # Create launcher script
    launcher_path = os.path.join(script_dir, "egguf_launcher.py")
    with open(launcher_path, "w") as f:
        f.write(f'''#!/usr/bin/env python3
"""EGGUF Launcher — handles file association clicks"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if len(sys.argv) < 2:
    print("No file specified. Usage: egguf_launcher.py <file>")
    sys.exit(1)

filepath = sys.argv[1]
ext = os.path.splitext(filepath)[1].lower()

if ext == ".egguf":
    from gui import EGGUFApp
    app = EGGUFApp(filepath)
    app.run()
elif ext == ".efe":
    from efe_creator import EFECreator
    creator = EFECreator()
    creator.win.mainloop()
else:
    print(f"Unsupported file type: {{ext}}")
    sys.exit(1)
''')
    print(f"[OK] Launcher created: {launcher_path}")

    # Register file associations (platform-specific)
    system = platform.system()
    if system == "Windows":
        _register_windows(script_dir, launcher_path)
    elif system == "Darwin":
        _register_macos(script_dir, launcher_path)
    elif system == "Linux":
        _register_linux(script_dir, launcher_path)
    else:
        print(f"[INFO] File association not automated for {system}")
        print(f"       Open files with: python main.py open <file.egguf>")

    print()
    print("=" * 50)
    print("  Installation Complete!")
    print("=" * 50)
    print()
    print("Quick Start:")
    print("  1. Convert a GGUF model:  python main.py convert model.gguf")
    print("  2. Open the EGGUF file:   python main.py open model.egguf")
    print("  3. Add extensions:         Click 'Yes' when the popup appears")
    print("  4. Create your own EFE:    python main.py create-efe")
    print()
    print("The #use: text in EFE files IS the system prompt.")
    print("All Python libraries are supported in EFE files.")
    print()


def _register_windows(script_dir, launcher_path):
    """Register file associations on Windows."""
    try:
        import winreg
        python_exe = sys.executable

        for ext, desc in [(".egguf", "EGGUF File"), (".efe", "EFE Extension File")]:
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, ext) as key:
                winreg.SetValue(key, "", winreg.REG_SZ, f"EGGUF{ext[1:].upper()}File")
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, f"EGGUF{ext[1:].upper()}File") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, desc)
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, f"EGGUF{ext[1:].upper()}File\\shell\\open\\command") as key:
                winreg.SetValue(key, "", winreg.REG_SZ, f'"{python_exe}" "{launcher_path}" "%1"')
        print("[OK] Windows file associations registered (.egguf, .efe)")
    except Exception as e:
        print(f"[INFO] Could not auto-register: {e}")
        print("       Associate manually in Windows Settings > Apps > Default apps")


def _register_macos(script_dir, launcher_path):
    """Register file associations on macOS."""
    print("[INFO] macOS file association requires manual setup:")
    print("       1. Right-click a .egguf file -> Get Info")
    print("       2. Open with -> Other -> select Python")
    print(f"       3. Set launcher: {launcher_path}")
    print("       Repeat for .efe files")


def _register_linux(script_dir, launcher_path):
    """Register file associations on Linux (XDG)."""
    desktop_dir = os.path.expanduser("~/.local/share/applications")
    os.makedirs(desktop_dir, exist_ok=True)

    desktop_file = os.path.join(desktop_dir, "egguf.desktop")
    python_exe = sys.executable

    with open(desktop_file, "w") as f:
        f.write(f"""[Desktop Entry]
Type=Application
Name=EGGUF
Comment=Extensible GGUF
Exec={python_exe} {launcher_path} %f
Terminal=false
MimeType=application/x-egguf;application/x-efe;
Categories=Development;AI;
""")

    mime_dir = os.path.expanduser("~/.local/share/mime/packages")
    os.makedirs(mime_dir, exist_ok=True)
    mime_file = os.path.join(mime_dir, "egguf-mime.xml")
    with open(mime_file, "w") as f:
        f.write("""<?xml version="1.0"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
  <mime-type type="application/x-egguf">
    <comment>EGGUF File</comment>
    <glob pattern="*.egguf"/>
  </mime-type>
  <mime-type type="application/x-efe">
    <comment>EFE Extension File</comment>
    <glob pattern="*.efe"/>
  </mime-type>
</mime-info>
""")

    try:
        subprocess.run(["update-desktop-database", desktop_dir], capture_output=True)
        subprocess.run(["update-mime-database", os.path.expanduser("~/.local/share/mime")], capture_output=True)
    except Exception:
        pass

    print("[OK] Linux file associations registered (.egguf, .efe)")


if __name__ == "__main__":
    main()
