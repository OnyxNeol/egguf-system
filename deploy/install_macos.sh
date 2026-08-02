#!/bin/bash
# EGGUF macOS Installer — Creates .app bundle and registers file types
# No logo, no icon — completely blank as requested.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="EGGUF.app"
APP_DIR="/Applications/$APP_NAME"

echo "=========================================="
echo "  EGGUF macOS Installer"
echo "  Extensible GGUF System"
echo "=========================================="
echo

# Find executable
EXE=""
for name in egguf; do
    for d in "$SCRIPT_DIR" "$SCRIPT_DIR/bin" "$SCRIPT_DIR/dist"; do
        if [ -f "$d/$name" ]; then
            EXE="$d/$name"
            break 2
        fi
    done
done

if [ -z "$EXE" ]; then
    echo "ERROR: egguf executable not found."
    echo "Expected: $SCRIPT_DIR/egguf or $SCRIPT_DIR/dist/egguf"
    echo
    echo "Build it with: python build_full.py"
    exit 1
fi

echo "[1/5] Creating .app bundle structure ..."
sudo mkdir -p "$APP_DIR/Contents/MacOS"
sudo mkdir -p "$APP_DIR/Contents/Resources"

echo "[2/5] Copying executable ..."
sudo cp "$EXE" "$APP_DIR/Contents/MacOS/egguf"
sudo chmod +x "$APP_DIR/Contents/MacOS/egguf"

echo "[3/5] Installing Info.plist ..."
sudo cp "$SCRIPT_DIR/macos/Info.plist" "$APP_DIR/Contents/Info.plist"

# Create a minimal PkgInfo (8 bytes, no icon)
echo -n "APPL????" | sudo tee "$APP_DIR/Contents/PkgInfo" > /dev/null

echo "[4/5] Registering file types ..."
# Register the app with Launch Services
/System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister -f "$APP_DIR" 2>/dev/null || true

# Set EGGUF as default for .egguf and .efe
duti -s com.egguf.app .egguf all 2>/dev/null || true
duti -s com.egguf.app .efe all 2>/dev/null || true
duti -s com.egguf.app .gguf all 2>/dev/null || true

echo "[5/5] Verifying installation ..."
if [ -d "$APP_DIR" ]; then
    echo "  [OK] $APP_DIR created"
else
    echo "  [WARN] App bundle not found at expected location"
fi

echo
echo "=========================================="
echo "  Installation complete!"
echo "=========================================="
echo
echo "  .egguf files now open with EGGUF"
echo "  .efe files now open with EGGUF"
echo "  .gguf files now open with EGGUF (converts)"
echo
echo "  Double-click any .egguf file to start."
echo
echo "  App location: /Applications/EGGUF.app"
echo "  CLI: /Applications/EGGUF.app/Contents/MacOS/egguf open model.egguf"
echo
echo "  To uninstall: rm -rf $APP_DIR"
