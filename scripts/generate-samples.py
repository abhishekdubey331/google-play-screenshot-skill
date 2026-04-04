#!/usr/bin/env python3
"""
Generate sample simulator screenshots and deterministic scaffold outputs.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SIM_DIR = ROOT / "samples" / "simulator"
SCAFFOLD_DIR = ROOT / "samples" / "scaffolds"
FEATURE_GRAPHIC = ROOT / "samples" / "feature-graphic.png"

SAMPLE_SCREENS = [
    ("screen-01-market.png", "Market Dashboard", "#1F6FEB"),
    ("screen-02-search.png", "Card Search", "#0E8A6A"),
    ("screen-03-portfolio.png", "Portfolio", "#AA4A00"),
]

SAMPLE_COMPOSE = [
    ("TRACK", "CARD PRICES LIVE", "screen-01-market.png", "01-track-card-prices.png"),
    ("SEARCH", "ANY CARD INSTANTLY", "screen-02-search.png", "02-search-any-card.png"),
    ("BUILD", "YOUR COLLECTION EDGE", "screen-03-portfolio.png", "03-build-collection.png"),
]


def ensure_dirs() -> None:
    SIM_DIR.mkdir(parents=True, exist_ok=True)
    SCAFFOLD_DIR.mkdir(parents=True, exist_ok=True)


def make_simulator_image(filename: str, title: str, accent_hex: str) -> None:
    w, h = 1179, 2556
    img = Image.new("RGB", (w, h), "#0F172A")
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, w, 220], fill="#111827")
    draw.rectangle([60, 300, w - 60, 600], fill=accent_hex)
    draw.rectangle([60, 650, w - 60, 1220], fill="#111827")
    draw.rectangle([60, 1270, w - 60, h - 120], fill="#1E293B")

    # Lightweight fake rows/cards to make screenshots feel "real".
    y = 700
    for i in range(6):
        draw.rounded_rectangle([100, y, w - 100, y + 68], radius=16, fill="#334155")
        draw.rounded_rectangle([120, y + 20, 360, y + 48], radius=10, fill="#94A3B8")
        draw.rounded_rectangle([w - 320, y + 20, w - 130, y + 48], radius=10, fill="#60A5FA")
        y += 84

    draw.text((80, 80), title, fill="#E5E7EB")
    draw.text((80, 360), "Sample data for README demo", fill="#E2E8F0")
    draw.text((80, 1320), "Top Movers", fill="#E2E8F0")

    img.save(SIM_DIR / filename, "PNG")


def run_compose(verb: str, desc: str, screenshot_name: str, output_name: str) -> None:
    compose_py = ROOT / "compose.py"
    screenshot = SIM_DIR / screenshot_name
    output = SCAFFOLD_DIR / output_name

    cmd = [
        sys.executable,
        str(compose_py),
        "--bg",
        "#2563EB",
        "--verb",
        verb,
        "--desc",
        desc,
        "--screenshot",
        str(screenshot),
        "--output",
        str(output),
        "--preset",
        "play-store-android",
    ]
    subprocess.run(cmd, check=True)


def main() -> None:
    ensure_dirs()
    for filename, title, accent in SAMPLE_SCREENS:
        make_simulator_image(filename, title, accent)
    for verb, desc, sim_name, output_name in SAMPLE_COMPOSE:
        run_compose(verb, desc, sim_name, output_name)
    run_feature_graphic()
    print("Generated samples in samples/simulator, samples/scaffolds, and samples/feature-graphic.png")


def run_feature_graphic() -> None:
    feature_py = ROOT / "generate_feature_graphic.py"
    screenshot = SIM_DIR / "screen-01-market.png"
    cmd = [
        sys.executable,
        str(feature_py),
        "--bg",
        "#2563EB",
        "--title",
        "TRACK",
        "--subtitle",
        "CARD PRICES LIVE",
        "--screenshot",
        str(screenshot),
        "--output",
        str(FEATURE_GRAPHIC),
    ]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
