#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="${OPENCODE_COMMANDS_DIR:-$HOME/.config/opencode/commands}"
MODE="link"
INSTALL_SKILLS=false

usage() {
  cat <<'EOF'
Usage: install-opencode.sh [--copy] [--global] [--skills]

Install AI Berkshire opencode commands (and optionally skills).

Options:
  --copy     Copy files/directories instead of symlinking (default: symlink).
  --global   Placeholder for consistency with sibling install scripts.
             Default target is already $HOME/.config/opencode/commands.
  --skills   Also install skills to $HOME/.config/opencode/skills.
  -h, --help Show this help.

Default target: $HOME/.config/opencode/commands
Override target: OPENCODE_COMMANDS_DIR=/path/to/commands ./install-opencode.sh
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --copy) MODE="copy"; shift ;;
    --global) shift ;;
    --skills) INSTALL_SKILLS=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

python3 "$ROOT/scripts/sync-opencode.py"
mkdir -p "$DEST"

for cmd_file in "$ROOT"/.opencode/command/*.md; do
  [ -f "$cmd_file" ] || continue
  name="$(basename "$cmd_file")"
  rm -f "$DEST/$name"
  if [ "$MODE" = "copy" ]; then
    cp "$cmd_file" "$DEST/$name"
  else
    ln -s "$cmd_file" "$DEST/$name"
  fi
done

if [ "$INSTALL_SKILLS" = true ]; then
  SKILLS_DEST="$HOME/.config/opencode/skills"
  mkdir -p "$SKILLS_DEST"
  for skill_dir in "$ROOT"/.opencode/skills/*; do
    [ -d "$skill_dir" ] || continue
    name="$(basename "$skill_dir")"
    rm -rf "$SKILLS_DEST/$name"
    if [ "$MODE" = "copy" ]; then
      cp -R "$skill_dir" "$SKILLS_DEST/$name"
    else
      ln -s "$skill_dir" "$SKILLS_DEST/$name"
    fi
  done
fi

chmod +x "$ROOT"/tools/*.py "$ROOT"/tools/*.sh 2>/dev/null || true

echo "Installed opencode commands to $DEST"
if [ "$INSTALL_SKILLS" = true ]; then
  echo "Installed opencode skills to $SKILLS_DEST"
fi
echo "Restart opencode (or start a new session) to pick up the new commands."
