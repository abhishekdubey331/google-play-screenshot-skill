# Platform Adapters

This project is designed as a single reusable skill with lightweight install adapters.

## Core vs Adapter

- Core logic: `SKILL.md`, `compose.py`, `generate_frame.py`, `generate_feature_graphic.py`, `showcase.py`
- Adapter layer: install location + platform-specific tool availability

The workflow remains in `SKILL.md`, but runtime support depends on the agent exposing memory plus image view/edit/generation capabilities.

## Supported Platforms

1. Codex
- Skill path: `~/.codex/skills/<skill-name>`
- Install: `./scripts/install-skill.sh codex`

2. Claude Code
- Skill path: `~/.claude/skills/<skill-name>`
- Install: `./scripts/install-skill.sh claude`

## Current Scope

1. Installation is supported for Codex and Claude Code.
2. The prompt is written in agent-neutral language where practical.
3. Full end-to-end runtime still requires compatible memory and image-tool support.
4. Local Python scripts are platform-neutral; image-edit workflow depends on agent integrations.

## Adding Another Platform

1. Identify skill install path convention.
2. Add a new case in `scripts/install-skill.sh`.
3. Document platform-specific constraints here.
4. Avoid forking `SKILL.md`; prefer one shared prompt unless behavior must diverge.
