#!/usr/bin/env bash
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREFIX="${PREFIX:-$HOME/.local}"
HYPR="$HOME/.config/hypr"
KEEP=0
[ "${1:-}" = "--keep" ] && KEEP=1

main() {
  cd "$SRC"

  echo "==> Installing dependencies"
  if command -v pacman >/dev/null; then
    sudo pacman -S --needed --noconfirm python python-gobject gtk4 libadwaita
  else
    echo "Non-pacman distro: install python-gobject, GTK4 and libadwaita manually."
  fi

  echo "==> Installing app"
  install -Dm755 hyprland-settings.py "$PREFIX/bin/hyprland-settings"
  install -Dm644 hyprland-settings.desktop "$PREFIX/share/applications/hyprland-settings.desktop"

  echo "==> Hooking into Hyprland config"
  mkdir -p "$HYPR"
  touch "$HYPR/hyprland.conf" "$HYPR/hyprland-settings.conf"
  local LINE="source = ~/.config/hypr/hyprland-settings.conf"
  if ! grep -qxF "$LINE" "$HYPR/hyprland.conf"; then
    cp "$HYPR/hyprland.conf" "$HYPR/hyprland.conf.bak"
    printf '\n# hyprland-settings (keep last so it overrides)\n%s\n' "$LINE" >> "$HYPR/hyprland.conf"
  fi
}

cleanup() {
  # Only delete if this really is the project folder, never $HOME or /
  if [ "$KEEP" -eq 0 ] && [ "$SRC" != "$HOME" ] && [ "$SRC" != "/" ] \
     && [ -f "$SRC/hyprland-settings.py" ] && [ -f "$SRC/install.sh" ]; then
    echo "==> Removing downloaded files"
    cd "$HOME"
    rm -rf -- "$SRC"
  fi
}

main
cleanup
echo "Done. Run 'hyprland-settings' (make sure $PREFIX/bin is in your PATH)."
exit 0
