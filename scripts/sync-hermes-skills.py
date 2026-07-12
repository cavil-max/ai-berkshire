#!/usr/bin/env python3
"""Generate Hermes skills from AI Berkshire Claude command files.

Hermes (https://hermes-agent.nousresearch.com) is an AI agent platform by
NousResearch. Its skills system is compatible with the AgentSkills spec
(agentskills.io), the same open standard used by OpenClaw. Each skill lives
in a directory containing a SKILL.md with YAML frontmatter (name, description)
and a markdown body.

This script mirrors scripts/sync-openclaw-skills.py so Claude Code, Codex,
OpenClaw, opencode, and Hermes users share one canonical workflow source
in skills/*.md.

Usage::

    python3 scripts/sync-hermes-skills.py           # generate
    python3 scripts/sync-hermes-skills.py --check    # verify up-to-date
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLAUDE_SKILLS = ROOT / "skills"
HERMES_SKILLS = ROOT / "hermes-skills"


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


def metadata_for(name: str, source_name: str, source_text: str) -> str:
    """Build Hermes-compatible YAML frontmatter.

    Reuse name/description from source frontmatter when present, otherwise
    derive them from the first heading so all systems stay in sync.
    """
    existing, body = split_frontmatter(source_text)
    if existing:
        has_name = re.search(r"(?m)^name:\s*", existing) is not None
        has_description = re.search(r"(?m)^description:\s*", existing) is not None
        lines = []
        if not has_name:
            lines.append(f"name: {name}")
        if not has_description:
            title = first_heading(body, name)
            lines.append(
                "description: "
                + yaml_quote(f"AI Berkshire skill: {title}. Source: skills/{source_name}.")
            )
        lines.append(existing.rstrip())
        lines.append("metadata:")
        lines.append("  hermes:")
        lines.append("    requires:")
        lines.append("      bins:")
        lines.append("        - python3")
        return "---\n" + "\n".join(lines) + "\n---\n\n"

    title = first_heading(source_text, name)
    description = f"AI Berkshire skill: {title}. Source: skills/{source_name}."
    return (
        "---\n"
        f"name: {name}\n"
        f"description: {yaml_quote(description)}\n"
        "metadata:\n"
        "  hermes:\n"
        "    requires:\n"
        "      bins:\n"
        "        - python3\n"
        "---\n\n"
    )


def hermes_body(name: str, source_name: str, source_text: str) -> str:
    _, body = split_frontmatter(source_text)
    note = (
        "## Hermes adapter note\n\n"
        f"This skill is generated from `skills/{source_name}` so Claude Code, "
        "Codex, OpenClaw, opencode, and Hermes users share one canonical "
        "workflow.\n\n"
        "- Treat `$ARGUMENTS` as the user's request in the current Hermes "
        "session.\n"
        "- When the source mentions Claude-only surfaces such as Task, Agent, "
        "WebSearch, Bash, Read, or Write, use the closest Hermes capability "
        "available: `terminal` for shell commands and local tools, `web_search` "
        "/ `web_extract` for research, `read_file` / `write_file` for workspace "
        "files, and `skill_manage` for skill operations.\n"
        "- Use shared project tools from `tools/` in this repository. Prefer "
        "running commands from the repository root with paths like "
        "`python3 tools/financial_rigor.py ...`; if the current session starts "
        "outside the repo, locate the actual checkout path first instead of "
        "assuming a fixed home-directory path.\n"
        "- Before starting research, run the `date` command (via `terminal`) to "
        "confirm today's date; treat it as the baseline for \"latest\" data and "
        "state the data cutoff date in the report header. Never assume the "
        "current date from training data.\n"
        "- Preserve the research quality rules from `AGENTS.md`: cross-check "
        "financial data, use exact arithmetic tools for valuation/math, and "
        "clearly label uncertainty and source gaps.\n\n"
    )
    return note + body.rstrip() + "\n"


def main() -> None:
    check = "--check" in sys.argv[1:]
    unknown_args = [arg for arg in sys.argv[1:] if arg != "--check"]
    if unknown_args:
        joined = ", ".join(unknown_args)
        raise SystemExit(f"Unknown argument(s): {joined}")

    if not check:
        HERMES_SKILLS.mkdir(exist_ok=True)

    count = 0
    stale: list[str] = []
    for source in sorted(CLAUDE_SKILLS.glob("*.md")):
        name = source.stem
        source_text = source.read_text(encoding="utf-8")
        target_dir = HERMES_SKILLS / name
        target = target_dir / "SKILL.md"
        content = metadata_for(name, source.name, source_text) + hermes_body(
            name, source.name, source_text
        )
        if check:
            if not target.exists() or target.read_text(encoding="utf-8") != content:
                stale.append(str(target.relative_to(ROOT)))
        else:
            target_dir.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        count += 1

    if check:
        if stale:
            print("Hermes skills are out of date:")
            for path in stale:
                print(f"  {path}")
            raise SystemExit(1)
        print(f"Checked {count} Hermes skills in {HERMES_SKILLS.relative_to(ROOT)}")
        return

    print(f"Generated {count} Hermes skills in {HERMES_SKILLS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()