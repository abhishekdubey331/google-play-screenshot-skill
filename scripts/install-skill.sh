#!/usr/bin/env bash
set -euo pipefail

# Install this skill into Codex and/or Claude Code skill directories.
#
# Usage:
#   ./scripts/install-skill.sh codex
#   ./scripts/install-skill.sh claude
#   ./scripts/install-skill.sh both
#   ./scripts/install-skill.sh both my-custom-skill-name

PLATFORM="${1:-both}"
SKILL_NAME="${2:-aso-store-screenshots}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

copy_skill() {
  local target_dir="$1"
  mkdir -p "$target_dir"
  rsync -a --delete \
    --exclude ".git" \
    --exclude ".DS_Store" \
    --exclude "__pycache__" \
    --exclude "*.pyc" \
    --exclude "screenshots" \
    "$ROOT_DIR"/ "$target_dir"/
  echo "Installed to: $target_dir"
}

case "$PLATFORM" in
  codex)
    copy_skill "$HOME/.codex/skills/$SKILL_NAME"
    ;;
  claude)
    copy_skill "$HOME/.claude/skills/$SKILL_NAME"
    ;;
  both)
    copy_skill "$HOME/.codex/skills/$SKILL_NAME"
    copy_skill "$HOME/.claude/skills/$SKILL_NAME"
    ;;
  *)
    echo "Unknown platform: $PLATFORM"
    echo "Expected one of: codex | claude | both"
    exit 1
    ;;
esac

