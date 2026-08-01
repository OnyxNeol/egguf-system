#!/usr/bin/env python3
"""
EGGUF Registry Publisher

Publishes the EGGUF and EFE file types to the Windows Registry
(HKEY_CLASSES_ROOT) so Windows recognizes:
  .egguf files as "EGGUF Model File (Extensible GGUF)"
  .efe files as "EFE Extension File (Extensions For EGGUF)"

On Windows:  Registers file types in the registry (requires admin)
On Linux:    Registers XDG mime types and desktop associations
On macOS:    Prints instructions for manual setup

Usage:
  python publish_registry.py              # Auto-detect paths
  python publish_registry.py --python "C:\\Python311\\python.exe" --egguf-dir "C:\\EGGUF"

After running on Windows, .egguf and .efe files will have:
  - Custom icons
  - Right-click context menu options (Open, Apply EFE, Export, Info, Scan)
  - "Convert to EGGUF" option on .gguf files
"""

import os
import sys
import platform
import argparse
import subprocess


def main():
    parser = argparse.ArgumentParser(
        description="Publish EGGUF and EFE file types to the system registry"
    )
    parser.add_argument("--python", default=sys.executable,
                       help="Path to Python executable")
    parser.add_argument("--egguf-dir", default=os.path.dirname(os.path.abspath(__file__)),
                       help="Path to EGGUF system directory")
    args = parser.parse_args()

    python_exe = args.python
    egguf_dir = args.egguf_dir
    main_script = os.path.join(egguf_dir, "main.py")
    converter_script = os.path.join(egguf_dir, "gguf2egguf.py")

    print("=" * 55)
    print("  EGGUF Registry Publisher")
    print("  Publishing .egguf and .efe to system registry")
    print("=" * 55)
    print(f"  Python:  {python_exe}")
    print(f"  EGGUF:   {egguf_dir}")
    print()

    system = platform.system()

    if system == "Windows":
        _publish_windows(python_exe, egguf_dir, main_script, converter_script)
    elif system == "Linux":
        _publish_linux(python_exe, egguf_dir, main_script)
    elif system == "Darwin":
        _publish_macos(python_exe, egguf_dir)
    else:
        print(f"Unknown system: {system}")
        print("Manual setup required.")
        sys.exit(1)

    print()
    print("=" * 55)
    print("  Publishing Complete!")
    print("=" * 55)
    print()
    print("Registered file types:")
    print("  .egguf  →  EGGUF Model File (Extensible GGUF)")
    print("  .efe    →  EFE Extension File (Extensions For EGGUF)")
    print("  .gguf   →  'Convert to EGGUF' context menu option")
    print()
    print("Context menu options:")
    print("  .egguf:  Open | Apply EFE Extension | Export GGUF | Info")
    print("  .efe:    Open Creator | Scan (Validate #use:)")
    print("  .gguf:   Convert to EGGUF")
    print()


# ═══════════════════════════════════════════════════════════
#  WINDOWS REGISTRATION (HKEY_CLASSES_ROOT)
# ═══════════════════════════════════════════════════════════

def _publish_windows(python_exe, egguf_dir, main_script, converter_script):
    """Publish .egguf and .efe to HKEY_CLASSES_ROOT on Windows."""
    try:
        import winreg
    except ImportError:
        print("ERROR: winreg module not available (Windows only)")
        sys.exit(1)

    # Normalize paths for Windows registry (double backslashes)
    py = python_exe.replace("/", "\\")
    ms = main_script.replace("/", "\\")
    cs = converter_script.replace("/", "\\")

    registrations = [
        # ─── .egguf file type ───
        (r".egguf", "", "EGGUFFile"),
        (r".egguf", "Content Type", "application/x-egguf"),
        (r"EGGUFFile", "", "EGGUF Model File"),
        (r"EGGUFFile", "FriendlyTypeName", "EGGUF Model File (Extensible GGUF)"),
        # Open command
        (r"EGGUFFile\shell", "", "open"),
        (r"EGGUFFile\shell\open", "", "Open with EGGUF"),
        (r"EGGUFFile\shell\open\command", "",
         f'"{py}" "{ms}" open "%1"'),
        # Apply EFE
        (r"EGGUFFile\shell\apply", "", "Apply EFE Extension..."),
        (r"EGGUFFile\shell\apply\command", "",
         f'"{py}" "{ms}" apply "%1"'),
        # Export GGUF
        (r"EGGUFFile\shell\export", "", "Export GGUF..."),
        (r"EGGUFFile\shell\export\command", "",
         f'"{py}" "{ms}" export "%1"'),
        # Info
        (r"EGGUFFile\shell\info", "", "Show EGGUF Info"),
        (r"EGGUFFile\shell\info\command", "",
         f'"{py}" "{ms}" info "%1"'),

        # ─── .efe file type ───
        (r".efe", "", "EFEFile"),
        (r".efe", "Content Type", "application/x-efe"),
        (r"EFEFile", "", "EFE Extension File"),
        (r"EFEFile", "FriendlyTypeName", "EFE Extension File (Extensions For EGGUF)"),
        # Open
        (r"EFEFile\shell", "", "open"),
        (r"EFEFile\shell\open", "", "Open EFE Creator"),
        (r"EFEFile\shell\open\command", "",
         f'"{py}" "{ms}" create-efe'),
        # Scan
        (r"EFEFile\shell\scan", "", "Scan (Validate #use:)"),
        (r"EFEFile\shell\scan\command", "",
         f'"{py}" "{ms}" scan "%1"'),

        # ─── .gguf → Convert to EGGUF ───
        (r".gguf", "", "GGUFFile"),
        (r"GGUFFile\shell\convertToEGGUF", "", "Convert to EGGUF..."),
        (r"GGUFFile\shell\convertToEGGUF\command", "",
         f'"{py}" "{cs}" "%1"'),
    ]

    success = 0
    failed = 0

    for key_path, value_name, value_data in registrations:
        try:
            # Split into parent key and subkey
            parts = key_path.rsplit("\\", 1)
            if len(parts) == 2:
                parent, subkey = parts
                with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path) as key:
                    winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, value_data)
            else:
                with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path) as key:
                    winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, value_data)
            success += 1
        except PermissionError:
            print(f"  [DENIED] HKCR\\{key_path} — needs admin privileges")
            failed += 1
        except Exception as e:
            print(f"  [ERROR] HKCR\\{key_path}: {e}")
            failed += 1

    print(f"  [OK] {success} registry entries created in HKEY_CLASSES_ROOT")
    if failed:
        print(f"  [WARN] {failed} entries failed — run as Administrator")

    # Notify shell to refresh
    try:
        import ctypes
        ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
        print("  [OK] Shell notified to refresh file associations")
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════
#  LINUX REGISTRATION (XDG)
# ═══════════════════════════════════════════════════════════

def _publish_linux(python_exe, egguf_dir, main_script):
    """Publish .egguf and .efe as XDG mime types on Linux."""
    # Desktop file
    desktop_dir = os.path.expanduser("~/.local/share/applications")
    os.makedirs(desktop_dir, exist_ok=True)
    desktop_file = os.path.join(desktop_dir, "egguf.desktop")

    with open(desktop_file, "w") as f:
        f.write(f"""[Desktop Entry]
Type=Application
Name=EGGUF
Comment=Extensible GGUF System
Exec={python_exe} {main_script} open %f
Terminal=false
MimeType=application/x-egguf;application/x-efe;
Categories=Development;AI;
""")
    print(f"  [OK] Desktop file: {desktop_file}")

    # Mime types
    mime_dir = os.path.expanduser("~/.local/share/mime/packages")
    os.makedirs(mime_dir, exist_ok=True)
    mime_file = os.path.join(mime_dir, "egguf-mime.xml")

    with open(mime_file, "w") as f:
        f.write("""<?xml version="1.0"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
  <mime-type type="application/x-egguf">
    <comment>EGGUF Model File (Extensible GGUF)</comment>
    <glob pattern="*.egguf"/>
  </mime-type>
  <mime-type type="application/x-efe">
    <comment>EFE Extension File (Extensions For EGGUF)</comment>
    <glob pattern="*.efe"/>
  </mime-type>
</mime-info>
""")
    print(f"  [OK] Mime types: {mime_file}")

    # Update databases
    try:
        subprocess.run(["update-desktop-database", desktop_dir], capture_output=True)
        subprocess.run(["update-mime-database", os.path.expanduser("~/.local/share/mime")], capture_output=True)
        print("  [OK] Desktop and mime databases updated")
    except Exception:
        print("  [INFO] Run update-desktop-database and update-mime-database manually")

    # .gguf → Convert to EGGUF (desktop action)
    gguf_desktop = os.path.join(desktop_dir, "gguf2egguf.desktop")
    converter = os.path.join(egguf_dir, "gguf2egguf.py")
    with open(gguf_desktop, "w") as f:
        f.write(f"""[Desktop Entry]
Type=Application
Name=GGUF to EGGUF Converter
Comment=Convert GGUF to Extensible GGUF
Exec={python_exe} {converter} %f
Terminal=true
MimeType=application/x-gguf;
Categories=Development;AI;
""")
    print(f"  [OK] GGUF converter: {gguf_desktop}")


# ═══════════════════════════════════════════════════════════
#  macOS REGISTRATION
# ═══════════════════════════════════════════════════════════

def _publish_macos(python_exe, egguf_dir):
    """Print instructions for macOS manual setup."""
    print("  macOS requires manual file association setup:")
    print()
    print("  1. Right-click a .egguf file → Get Info")
    print("  2. 'Open with' → Other → select Python")
    print(f"     Launcher: {os.path.join(egguf_dir, 'egguf_launcher.py')}")
    print("  3. Click 'Change All...' to apply to all .egguf files")
    print("  4. Repeat for .efe files")
    print()
    print("  For the GGUF converter:")
    print(f"     python {os.path.join(egguf_dir, 'gguf2egguf.py')} model.gguf")


if __name__ == "__main__":
    main()
