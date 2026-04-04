# Platform Adapters

This project is designed as a single reusable skill with lightweight platform adapters.

## Core vs Adapter

- Core logic: `SKILL.md`, `compose.py`, `generate_frame.py`, `showcase.py`
- Adapter layer: install location + platform-specific tool availability

The workflow should remain in `SKILL.md` as the source of truth. Platform differences should be handled as thin wrappers only.

## Supported Platforms

1. Codex
- Skill path: `~/.codex/skills/<skill-name>`
- Install: `./scripts/install-skill.sh codex`

2. Claude Code
- Skill path: `~/.claude/skills/<skill-name>`
- Install: `./scripts/install-skill.sh claude`

## Recommended Portability Rules

1. Keep platform-specific paths out of the core prompt when possible.
2. Use generic tool language in `SKILL.md` where capabilities overlap.
3. Gate optional steps (for example, AI image enhancement) behind capability checks.
4. Keep script interfaces stable and platform-neutral.

## Adding Another Platform

1. Identify skill install path convention.
2. Add a new case in `scripts/install-skill.sh`.
3. Document platform-specific constraints here.
4. Avoid forking `SKILL.md`; prefer one shared prompt unless behavior must diverge.

