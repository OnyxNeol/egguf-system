# EGGUF Deployment Guide

## Quick Start

### Linux
```bash
# 1. Build the executable (or download from GitHub Releases)
python3 build_full.py

# 2. Install file type associations
chmod +x deploy/install_linux.sh
sudo ./deploy/install_linux.sh

# 3. Done! Double-click any .egguf file
```

### Windows
```powershell
# 1. Build the executable
python build_full.py

# 2. Install file type associations (right-click → Run with PowerShell)
powershell -ExecutionPolicy Bypass -File deploy\install_windows.ps1

# 3. Done! Double-click any .egguf file
```

### macOS
```bash
# 1. Build the executable
python3 build_full.py

# 2. Install .app bundle + file types
chmod +x deploy/install_macos.sh
sudo ./deploy/install_macos.sh

# 3. Done! Double-click any .egguf file
```

## What Gets Registered

| File Type | Extension | Behavior |
|-----------|-----------|----------|
| EGGUF | `.egguf` | Opens GUI — "Do you want to add extensions?" popup |
| EFE | `.efe` | Opens EFE scanner — validates and previews |
| GGUF | `.gguf` | Offers to convert to EGGUF format |

## Building from Source (All Platforms)

```bash
# Install PyInstaller
pip install pyinstaller

# Build the full system
python3 build_full.py

# Output:
#   Linux:   dist/egguf
#   macOS:   dist/egguf
#   Windows: dist/egguf.exe
```

## GitHub Actions (Automated Builds)

Push a `v*` tag to trigger automatic builds for all 3 platforms:
```bash
git tag v1.0
git push origin v1.0
```

This creates a GitHub Release with:
- `egguf-linux.zip` — executable + Linux installer
- `egguf-macos.zip` — executable + macOS installer
- `egguf-windows.zip` — executable + Windows installer

## Icon

**None.** The logo is completely blank — no icon file is included or referenced.
The file types show with the system default file icon on all platforms.

## CLI Usage

```bash
egguf open model.egguf              # Open EGGUF GUI
egguf convert model.gguf            # Convert GGUF → EGGUF
egguf scan extension.efe            # Validate EFE file
egguf apply model.egguf extension.efe  # Apply extensions
egguf create-efe                    # Open EFE Creator GUI
egguf info model.egguf              # Show file info (CLI)
egguf export model.egguf            # Export GGUF from EGGUF
egguf samples                       # List sample EFE files
```

## Uninstalling

### Linux
```bash
sudo rm /usr/local/bin/egguf
sudo rm /usr/share/applications/egguf.desktop
sudo rm /usr/share/mime/packages/egguf-mime.xml
sudo update-desktop-database /usr/share/applications
sudo update-mime-database /usr/share/mime
```

### Windows
```powershell
powershell -ExecutionPolicy Bypass -File deploy\uninstall_windows.ps1
```

### macOS
```bash
sudo rm -rf /Applications/EGGUF.app
```
