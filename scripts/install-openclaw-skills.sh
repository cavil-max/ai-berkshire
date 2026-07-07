#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${OPENCLAW_SKILLS_DIR:-$HOME/.openclaw/workspace/skills}"
MODE="link"

usage() {
  cat <<'EOF'
Usage: install-openclaw-skills.sh [--copy] [--global]

Install AI Berkshire OpenClaw skills into the OpenClaw workspace.

Options:
  --copy     Copy skill directories instead of symlinking (default: symlink).
  --global   Install to ~/.openclaw/skills (all agents) instead of the
             default workspace skills directory.
  -h, --help Show this help.

Default target: $HOME/.openclaw/workspace/skills
Override target: OPENCLAW_SKILLS_DIR=/path/to/skills ./install-openclaw-skills.sh
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --copy) MODE="copy"; shift ;;
    --global) DEST="$HOME/.openclaw/skills"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

python3 "$ROOT/scripts/sync-openclaw-skills.py"
mkdir -p "$DEST"

for skill_dir in "$ROOT"/openclaw-skills/*; do
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

echo "Installed OpenClaw skills to $DEST"
echo "Restart OpenClaw (or start a new session) to pick up the new skills."
echo "If OpenClaw does not discover them, add this directory to skills.load.extraDirs in openclaw.json:"
echo "  $DEST"
