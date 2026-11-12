#!/usr/bin/env bash
# Build a .deb package for Тетрис on Debian/Ubuntu.
# Run from the project root directory.
# Prerequisites: python3, python3-pip, python3-venv, dpkg-deb

set -euo pipefail

APP_NAME="tetris"
VERSION="1.0.0"
ARCH="amd64"
DEB_DIR="deb_build/${APP_NAME}_${VERSION}_${ARCH}"

echo "==> Creating virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

echo "==> Installing dependencies..."
pip install --upgrade pip
pip install pygame pyinstaller

echo "==> Building standalone binary with PyInstaller..."
pyinstaller --onefile --noconsole --name "$APP_NAME" tetris.py

echo "==> Preparing .deb package structure..."
rm -rf "$DEB_DIR"
mkdir -p "$DEB_DIR/DEBIAN"
mkdir -p "$DEB_DIR/usr/local/bin"
mkdir -p "$DEB_DIR/usr/share/applications"

cp "dist/$APP_NAME" "$DEB_DIR/usr/local/bin/$APP_NAME"
chmod 755 "$DEB_DIR/usr/local/bin/$APP_NAME"

cat > "$DEB_DIR/DEBIAN/control" <<EOF
Package: $APP_NAME
Version: $VERSION
Section: games
Priority: optional
Architecture: $ARCH
Depends: libsdl2-2.0-0, libsdl2-mixer-2.0-0
Maintainer: Developer <dev@example.com>
Description: Тетрис — standalone Tetris game
 A classic Tetris game with keyboard controls (arrows + WASD).
 Built with Pygame.
EOF

cat > "$DEB_DIR/usr/share/applications/tetris.desktop" <<EOF
[Desktop Entry]
Name=Тетрис
Comment=Classic Tetris game
Exec=/usr/local/bin/tetris
Type=Application
Categories=Game;
Terminal=false
EOF

echo "==> Building .deb package..."
dpkg-deb --build "$DEB_DIR"
mv "deb_build/${APP_NAME}_${VERSION}_${ARCH}.deb" "dist/${APP_NAME}_${VERSION}_${ARCH}.deb"

echo "==> Done! Package: dist/${APP_NAME}_${VERSION}_${ARCH}.deb"
echo "    Install with: sudo dpkg -i dist/${APP_NAME}_${VERSION}_${ARCH}.deb"
deactivate

