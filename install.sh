#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PREFIX="${PREFIX:-$HOME/.local}"
HYPR="$HOME/.config/hypr"

echo "==> Installing dependencies"
if command -v pacman >/dev/null; then       # Arch / CachyOS / EndeavourOS / Manjaro
  sudo pacman -S --needed --noconfirm python python-gobject gtk4 libadwaita
else
  echo "Non-pacman distro: make sure python-gobject, GTK4 and libadwaita are installed."
fi

echo "==> Installing app"
install -Dm755 hyprland-settings.py "$PREFIX/bin/hyprland-settings"
install -Dm644 hyprland-settings.desktop "$PREFIX/share/applications/hyprland-settings.desktop"

echo "==> Hooking into Hyprland config"
mkdir -p "$HYPR"; touch "$HYPR/hyprland.conf" "$HYPR/hyprland-settings.conf"
LINE="source = ~/.config/hypr/hyprland-settings.conf"
grep -qxF "$LINE" "$HYPR/hyprland.conf" || {
  cp "$HYPR/hyprland.conf" "$HYPR/hyprland.conf.bak"
  printf '\n# hyprland-settings (keep last so it overrides)\n%s\n' "$LINE" >> "$HYPR/hyprland.conf"
}
echo "Done. Run 'hyprland-settings' (make sure $PREFIX/bin is in your PATH)."
