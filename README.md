# ASO App Screenshot Generator Skill

A reusable skill for generating high-converting mobile store screenshots.

## Origin and Credits

This project is adapted from the App Store-focused skill:
`https://github.com/adamlyttleapps/claude-skill-aso-appstore-screenshots`

This repository keeps the same core approach, but is tuned for **Google Play** screenshot workflows.

It guides an agent through:
1. Discovering the most compelling user benefits from your app.
2. Pairing each benefit with the best simulator screenshot.
3. Building polished, store-ready images with a deterministic layout plus AI enhancement.

The pipeline is Google Play-only:
- Google Play (Android portrait default: `1242x2208`)

## Repository Contents

- `SKILL.md`: Skill workflow and prompting logic.
- `compose.py`: Deterministic screenshot scaffold generator.
- `generate_feature_graphic.py`: Google Play feature graphic generator (`1024x500`).
- `generate_frame.py`: Device frame asset generator.
- `showcase.py`: Side-by-side preview generator.
- `assets/`: Frame templates used by the composer.

## Prerequisites

- Python 3.10+
- Pillow
- SF Pro fonts on macOS (optional, recommended for best typography)
- Gemini MCP server for AI image enhancement (`@houtini/gemini-mcp`)

Install Python dependency:

```bash
pip install -r requirements.txt
```

Install Gemini MCP:

```bash
npm install -g @houtini/gemini-mcp
```

Then register it in your agent MCP config so image generation/edit tools are available.
Reference setup: `https://github.com/nicobailon/gemini-mcp`

## Install The Skill Locally

Use the helper installer (recommended):

```bash
./scripts/install-skill.sh both
```

Or install manually:

### Codex

```bash
mkdir -p ~/.codex/skills/aso-store-screenshots
cp -R . ~/.codex/skills/aso-store-screenshots
```

### Claude Code

```bash
mkdir -p ~/.claude/skills/aso-store-screenshots
cp -R . ~/.claude/skills/aso-store-screenshots
```

## Platform Compatibility

This repo is structured to stay portable across agent platforms:

- Shared core workflow in `SKILL.md` (single source of truth)
- Platform install targets handled by `scripts/install-skill.sh`
- Platform guidance and extension points in `docs/PLATFORMS.md`

Today supported:
- Codex (`~/.codex/skills/<skill-name>`)
- Claude Code (`~/.claude/skills/<skill-name>`)

## Quickstart

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Install the skill:

```bash
./scripts/install-skill.sh both
```

3. Open your app project and invoke the skill:
- Claude Code: run `/aso-store-screenshots`
- Codex: ask the agent to use `aso-store-screenshots`

4. Follow the guided flow (benefits -> screenshot pairing -> generation).

## Sample Assets

This repo includes ready sample files for local testing:

- Input simulator screenshots: `samples/simulator/`
- Deterministic scaffold outputs: `samples/scaffolds/`
- Showcase preview (no footer link): `samples/showcase.png`
- Feature graphic sample (`1024x500`): `samples/feature-graphic.png`

Regenerate sample assets:

```bash
python3 scripts/generate-samples.py
python3 showcase.py \
  --screenshots samples/scaffolds/01-track-card-prices.png samples/scaffolds/02-search-any-card.png samples/scaffolds/03-build-collection.png \
  --output samples/showcase.png
```

`showcase.py` supports an optional footer link via `--github`, but it is omitted in the sample so the preview stays clean.

## Usage (Direct Scripts)

These scripts are optional utilities used by the skill pipeline. Most users should run the skill via the quickstart above.

Typical direct script usage:

```bash
python3 compose.py \
  --bg "#2563EB" \
  --verb "Track" \
  --desc "Card prices in real time" \
  --screenshot ./simulator/price-screen.png \
  --output ./screenshots/scaffold.png \
  --preset play-store-android
```

Generate/refresh frame assets:

```bash
python3 generate_frame.py
```

Generate a Google Play feature graphic (`1024x500`):

```bash
python3 generate_feature_graphic.py \
  --bg "#2563EB" \
  --title "TRACK" \
  --subtitle "CARD PRICES LIVE" \
  --screenshot ./simulator/price-screen.png \
  --output ./screenshots/feature-graphic.png
```

Create showcase image:

```bash
python3 showcase.py \
  --screenshots ./screenshots/final/01.jpg ./screenshots/final/02.jpg ./screenshots/final/03.jpg \
  --output ./screenshots/showcase.png \
  --github "https://github.com/<your-org>/<your-repo>"
```

## Open Source Notes

- Keep generated output (`screenshots/`) out of version control.
- Do not commit API keys, local MCP config, or private app screenshots.
- Review `SKILL.md` prompts if you want to tune tone, phase ordering, or quality bars.

## License

MIT (see `LICENSE`).
