#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install it from https://github.com/astral-sh/uv"
  exit 1
fi

uv venv --system-site-packages --python /usr/bin/python3
uv pip install -e ".$([ "${1:-}" = "--dev" ] && echo '[dev]' || true)"
"$ROOT/.venv/bin/python" -c "from clippy_xfce.sprites import ensure_assets; ensure_assets(); print('sprites ready')"

BIN="$HOME/.local/bin"
mkdir -p "$BIN"
ln -sfn "$ROOT/.venv/bin/clippy" "$BIN/clippy"

"$ROOT/.venv/bin/python" - <<'PY'
from clippy_xfce.config import load_settings
from clippy_xfce.desktop import install_desktop_files
from clippy_xfce.sprites import ensure_assets
ensure_assets()
install_desktop_files(load_settings().autostart)
print("desktop files installed")
PY

echo
echo "Clippy is installed."
echo "  Run:    clippy"
echo "  Or:     $ROOT/.venv/bin/clippy"
echo "  Hotkey: Ctrl+Alt+C (after Clippy is running)"
echo "Put your Anthropic key in Settings, or export ANTHROPIC_API_KEY."
