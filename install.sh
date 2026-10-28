#!/usr/bin/env bash
set -euo pipefail

source_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
app_dir="${XDG_DATA_HOME:-$HOME/.local/share}/mini-tetris"
applications_dir="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
icons_dir="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/scalable/apps"
desktop_file="$applications_dir/mini-tetris.desktop"

mkdir -p "$app_dir" "$applications_dir" "$icons_dir"
install -m 644 "$source_dir/index.html" "$app_dir/index.html"
install -m 644 "$source_dir/tetris.svg" "$icons_dir/mini-tetris.svg"

escape_desktop_arg() {
  local value="$1"
  value=${value//\\/\\\\}
  value=${value//\"/\\\"}
  value=${value//\$/\\\$}
  value=${value//\`/\\\`}
  printf '%s' "$value"
}

escaped_game="$(escape_desktop_arg "$app_dir/index.html")"
escaped_icon="$(escape_desktop_arg "${icons_dir}/mini-tetris.svg")"
cat > "$desktop_file" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Тетрис
Comment=Классическая игра Тетрис
Exec=xdg-open "$escaped_game"
Icon=$escaped_icon
Terminal=false
Categories=Game;
EOF

chmod 644 "$desktop_file"
printf 'Тетрис установлен. Найдите «Тетрис» в меню приложений.\n'