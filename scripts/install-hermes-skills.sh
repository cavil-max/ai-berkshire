#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${HERMES_SKILLS_DIR:-$HOME/.hermes/skills}"
MODE="link"

usage() {
  cat <<'EOF'
Usage: install-hermes-skills.sh [--copy] [--global]

Install AI Berkshire Hermes Agent skills into the Hermes skills directory.

Options:
  --copy     Copy skill directories instead of symlinking (default: symlink).
  --global   Placeholder for consistency; Hermes uses a single skills directory.
  -h, --help Show this help.

Default target: $HOME/.hermes/skills
Override target: HERMES_SKILLS_DIR=/path/to/skills ./install-hermes-skills.sh
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --copy) MODE="copy"; shift ;;
    --global) shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

python3 "$ROOT/scripts/sync-hermes-skills.py"
mkdir -p "$DEST"

for skill_dir in "$ROOT"/hermes-skills/*; do
  [ -d "$skill_dir" ] || continue
  name="$(basename "$skill_dir")"
  rm -rf "$DEST/$name"
  if [ "$MODE" = "copy" ]; then
    cp -R "$skill_dir" "$DEST/$name"
  else
    ln -s "$skill_dir" "$DEST/$name"
  fi
done

chmod +x "$ROOT"/tools/*.py "$ROOT"/tools/*.sh 2>/dev/null || true

echo "Installed Hermes skills to $DEST"
echo "Restart Hermes or start a new session to pick up the new skills."
