# CLAUDE.md

This file provides guidance to coding agents working with this repository.

## What This Is

A reusable screenshot-generation skill (`aso-store-screenshots`) focused on Google Play Store conversion, with optional App Store output support.

## Core Files

- `SKILL.md`: Main workflow prompt (recall -> benefits -> pairing -> generation).
- `compose.py`: Deterministic scaffold renderer with store presets.
- `generate_frame.py`: Regenerates iOS and Android frame templates in `assets/`.
- `showcase.py`: Builds a side-by-side preview image from final screenshots.
- `assets/android_device_frame.png`: Android frame template (Play default).
- `assets/device_frame.png`: iOS frame template (optional iOS export).

## Current Defaults

- Default preset in `compose.py` is `play-store-android` (`1242x2208`).
- Optional iOS preset is `app-store-ios` (`1290x2796`).
- `SKILL.md` is Play-first and keeps iOS dimensions as optional targets.

## Running Scripts

Install dependency:

```bash
pip install -r requirements.txt
```

Generate scaffold:

```bash
python3 compose.py \
  --bg "#2563EB" \
  --verb "TRACK" \
  --desc "CARD PRICES" \
  --screenshot path/to/simulator.png \
  --output output.png \
  --preset play-store-android
```

Regenerate frame assets:

```bash
python3 generate_frame.py
```

Create showcase image:

```bash
python3 showcase.py \
  --screenshots screenshots/final/01.jpg screenshots/final/02.jpg screenshots/final/03.jpg \
  --output screenshots/showcase.png \
  --github "https://github.com/<org>/<repo>"
```

## Maintenance Notes

- Keep prompt instructions and script behavior aligned when changing presets, dimensions, or file naming.
- Treat crop/resize as mandatory after AI enhancement outputs.
- Keep generated screenshots and secrets out of version control.
