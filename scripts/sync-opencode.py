#!/usr/bin/env python3
"""Generate opencode commands and skills from AI Berkshire skill sources.

opencode (https://opencode.ai) supports two entry points that mirror how
Claude Code users interact with this project:

- Commands (``.opencode/command/<name>.md``): explicit slash commands invoked
  by the user, e.g. ``/investment-research 腾讯``.  The body uses
  ``$ARGUMENTS`` exactly like the Claude Code slash-command sources in
  ``skills/*.md``.
- Skills (``.opencode/skills/<name>/SKILL.md``): auto-triggered by the model
  based on their ``description`` frontmatter.  Useful for reference documents
  such as ``financial-data.md`` and for discoverability of research workflows.

This script mirrors ``scripts/sync-codex-skills.py`` and
``scripts/sync-openclaw-skills.py`` so Claude Code, Codex, OpenClaw, and
opencode users share one canonical workflow source in ``skills/*.md``.

Usage::

    python3 scripts/sync-opencode.py           # generate
    python3 scripts/sync-opencode.py --check   # verify up-to-date, exit 1 if stale
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLAUDE_SKILLS = ROOT / "skills"
OPENCODE_COMMANDS = ROOT / ".opencode" / "command"
OPENCODE_SKILLS = ROOT / ".opencode" / "skills"


# ---------------------------------------------------------------------------
# Helpers (shared with sibling sync scripts)
# ---------------------------------------------------------------------------

def split_frontmatter(text: str) -> tuple[str | None, str]:
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return None, text
    return text[4:end], text[end + 5 :].lstrip("\n")


def first_heading(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def yaml_quote(value: str) -> str:
    value = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{value}"'


def description_for(source_name: str, source_text: str) -> str:
    """Derive a concise description from the first heading."""
    existing, body = split_frontmatter(source_text)
    if existing:
        m = re.search(r"(?m)^description:\s*(.+)$", existing)
        if m:
            return m.group(1).strip().strip('"').strip("'")
    title = first_heading(body, source_name)
    return f"AI Berkshire: {title}"


# ---------------------------------------------------------------------------
# Command generation
# ---------------------------------------------------------------------------

def command_for(source: Path) -> str:
    """Build an opencode command file from a Claude Code skill source.

    opencode commands use the same ``$ARGUMENTS`` placeholder as Claude Code
    slash commands, so the body is passed through unchanged.  We only prepend
    a minimal YAML frontmatter with a ``description`` for the command picker.
    """
    source_text = source.read_text(encoding="utf-8")
    _, body = split_frontmatter(source_text)
    desc = yaml_quote(description_for(source.name, source_text))
    return f"---\ndescription: {desc}\n---\n\n{body.rstrip()}\n"


# ---------------------------------------------------------------------------
# Skill generation
# ---------------------------------------------------------------------------

def skill_for(source: Path) -> str:
    """Build an opencode SKILL.md from a Claude Code skill source.

    Skills are auto-triggered by the model based on their ``description``.
    We prepend an opencode adapter note that maps Claude-only surfaces to
    opencode capabilities, then append the original skill body.
    """
    name = source.stem
    source_text = source.read_text(encoding="utf-8")
    _, body = split_frontmatter(source_text)
    desc = yaml_quote(description_for(source.name, source_text))
    note = (
        "## opencode adapter note\n\n"
        f"This skill is generated from `skills/{source.name}` so Claude Code, "
        "Codex, OpenClaw, and opencode users share one canonical workflow.\n\n"
        "- Treat ``$ARGUMENTS`` as the user's request in the current opencode "
        "session.\n"
        "- When the source mentions Claude-only surfaces such as Task, Agent, "
        "WebSearch, Bash, Read, or Write, use the closest opencode capability "
        "available: ``task`` / subagents for multi-agent work, "
        "``websearch`` / ``webfetch`` for research, ``bash`` for shell commands "
        "and local tools, and ``read`` / ``edit`` / ``write`` for workspace "
        "files.\n"
        "- Use shared project tools from ``tools/`` in this repository. Prefer "
        "running commands from the repository root with paths like "
        "``python3 tools/financial_rigor.py ...``.\n"
        "- Before starting research, run the ``date`` command (via ``bash``) to "
        "confirm today's date; treat it as the baseline for \"latest\" data and "
        "state the data cutoff date in the report header. Never assume the "
        "current date from training data.\n"
        "- Preserve the research quality rules from ``AGENTS.md``: cross-check "
        "financial data, use exact arithmetic tools for valuation/math, and "
        "clearly label uncertainty and source gaps.\n\n"
    )
    return (
        "---\n"
        f"name: {name}\n"
        f"description: {desc}\n"
        "---\n\n"
        f"{note}{body.rstrip()}\n"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    check = "--check" in sys.argv[1:]
    unknown_args = [arg for arg in sys.argv[1:] if arg != "--check"]
    if unknown_args:
        joined = ", ".join(unknown_args)
        raise SystemExit(f"Unknown argument(s): {joined}")

    if not check:
        OPENCODE_COMMANDS.mkdir(parents=True, exist_ok=True)
        OPENCODE_SKILLS.mkdir(parents=True, exist_ok=True)

    count = 0
    stale: list[str] = []

    for source in sorted(CLAUDE_SKILLS.glob("*.md")):
        name = source.stem

        # --- command ---
        cmd_target = OPENCODE_COMMANDS / f"{name}.md"
        cmd_content = command_for(source)
        if check:
            if not cmd_target.exists() or cmd_target.read_text(encoding="utf-8") != cmd_content:
                stale.append(str(cmd_target.relative_to(ROOT)))
        else:
            cmd_target.write_text(cmd_content, encoding="utf-8")

        # --- skill ---
        skill_dir = OPENCODE_SKILLS / name
        skill_target = skill_dir / "SKILL.md"
        skill_content = skill_for(source)
        if check:
            if not skill_target.exists() or skill_target.read_text(encoding="utf-8") != skill_content:
                stale.append(str(skill_target.relative_to(ROOT)))
        else:
            skill_dir.mkdir(parents=True, exist_ok=True)
            skill_target.write_text(skill_content, encoding="utf-8")

        count += 1

    if check:
        if stale:
            print("opencode artifacts are out of date:")
            for path in stale:
                print(f"  {path}")
            raise SystemExit(1)
        print(
            f"Checked {count} opencode commands + {count} skills "
            f"in {OPENCODE_COMMANDS.parent.relative_to(ROOT)}"
        )
        return

    print(
        f"Generated {count} opencode commands in "
        f"{OPENCODE_COMMANDS.relative_to(ROOT)}"
    )
    print(
        f"Generated {count} opencode skills in "
        f"{OPENCODE_SKILLS.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
