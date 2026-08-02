#!/bin/bash
# EGGUF Linux Installer — Registers .egguf and .efe file types
# No logo, no icon — completely blank as requested.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="/usr/local/bin"
APP_DIR="/usr/share/applications"
MIME_DIR="/usr/share/mime/packages"

echo "=========================================="
echo "  EGGUF Linux Installer"
echo "  Extensible GGUF System"
echo "=========================================="
echo

# Check for executable
EXE=""
for name in egguf egguf.bin; do
    if [ -f "$SCRIPT_DIR/$name" ]; then
        EXE="$SCRIPT_DIR/$name"
        break
    fi
    if [ -f "$SCRIPT_DIR/bin/$name" ]; then
        EXE="$SCRIPT_DIR/bin/$name"
        break
    fi
done

if [ -z "$EXE" ]; then
    echo "ERROR: egguf executable not found."
    echo "Expected: $SCRIPT_DIR/egguf or $SCRIPT_DIR/bin/egguf"
    echo
    echo "Build it with: python build_full.py"
    exit 1
fi

# Install executable
echo "[1/5] Installing executable to $INSTALL_DIR/egguf ..."
sudo cp "$EXE" "$INSTALL_DIR/egguf"
sudo chmod +x "$INSTALL_DIR/egguf"

# Install .desktop file
echo "[2/5] Installing .desktop file ..."
sudo cp "$SCRIPT_DIR/linux/egguf.desktop" "$APP_DIR/egguf.desktop"
sudo sed -i "s|^Exec=egguf|Exec=$INSTALL_DIR/egguf|" "$APP_DIR/egguf.desktop"

# Install MIME type definitions
echo "[3/5] Installing MIME type definitions ..."
sudo mkdir -p "$MIME_DIR"
sudo cp "$SCRIPT_DIR/linux/egguf-mime-fdo.xml" "$MIME_DIR/egguf-mime.xml"

# Update databases
echo "[4/5] Updating desktop and MIME databases ..."
sudo update-desktop-database "$APP_DIR" 2>/dev/null || true
sudo update-mime-database /usr/share/mime 2>/dev/null || true

# Set default application for .egguf and .efe
echo "[5/5] Setting default applications ..."
xdg-mime default egguf.desktop application/x-egguf 2>/dev/null || true
xdg-mime default egguf.desktop application/x-efe 2>/dev/null || true

echo
echo "=========================================="
echo "  Installation complete!"
echo "=========================================="
echo
echo "  .egguf files now open with EGGUF"
echo "  .efe files now open with EGGUF"
echo
echo "  Double-click any .egguf file to start."
echo "  Double-click any .gguf to convert."
echo
echo "  CLI: egguf open model.egguf"
echo "       egguf convert model.gguf"
echo "       egguf scan extension.efe"
echo "       egguf apply model.egguf extension.efe"
echo

# Uninstall instructions
echo "  To uninstall:"
echo "    sudo rm $INSTALL_DIR/egguf"
echo "    sudo rm $APP_DIR/egguf.desktop"
echo "    sudo rm $MIME_DIR/egguf-mime.xml"
echo "    sudo update-desktop-database $APP_DIR"
echo "    sudo update-mime-database /usr/share/mime"
