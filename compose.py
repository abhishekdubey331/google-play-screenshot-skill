#!/usr/bin/env python3
"""
Store Screenshot Composer
Composites headline text, device frame template, and app screenshot
into a polished store-ready marketing image.
"""

import argparse
import os
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/Library/Fonts/SF-Pro-Display-Black.otf"
ASSET_DIR = os.path.join(os.path.dirname(__file__), "assets")

PRESETS = {
    "play-store-android": {
        "canvas_w": 1242,
        "canvas_h": 2208,
        "device_w": 930,
        "device_y": 610,
        "bezel": 14,
        "screen_corner_r": 58,
        "frame_path": os.path.join(ASSET_DIR, "android_device_frame.png"),
        "text_top": 150,
        "verb_size_max": 220,
        "verb_size_min": 132,
        "desc_size": 102,
        "max_text_ratio": 0.74,
    },
}

VERB_DESC_GAP = 20
DESC_LINE_GAP = 24


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def word_wrap(draw, text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        if draw.textlength(test, font=font) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_font(text, max_w, size_max, size_min):
    """Return the largest font size where text fits within max_w."""
    dummy = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    for size in range(size_max, size_min - 1, -4):
        try:
            font = ImageFont.truetype(FONT_PATH, size)
        except OSError:
            return ImageFont.load_default()
        bbox = dummy.textbbox((0, 0), text, font=font)
        if (bbox[2] - bbox[0]) <= max_w:
            return font
    try:
        return ImageFont.truetype(FONT_PATH, size_min)
    except OSError:
        return ImageFont.load_default()


def draw_centered(draw, y, text, font, canvas_w, max_w=None):
    lines = word_wrap(draw, text, font, max_w) if max_w else [text]
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        h = bbox[3] - bbox[1]
        # Use anchor="mt" (middle-top) for pixel-perfect horizontal centering
        # Adjust y by bbox[1] offset so text top aligns with intended position
        draw.text((canvas_w // 2, y - bbox[1]), line, fill="white", font=font, anchor="mt")
        y += h + DESC_LINE_GAP
    return y


def compose(bg_hex, verb, desc, screenshot_path, output_path, preset_name):
    preset = PRESETS[preset_name]
    bg = hex_to_rgb(bg_hex)
    canvas_w = preset["canvas_w"]
    canvas_h = preset["canvas_h"]
    device_w = preset["device_w"]
    device_y = preset["device_y"]
    bezel = preset["bezel"]
    screen_corner_r = preset["screen_corner_r"]
    frame_path = preset["frame_path"]
    text_top = preset["text_top"]
    max_text_w = int(canvas_w * preset["max_text_ratio"])
    max_verb_w = int(canvas_w * preset["max_text_ratio"])
    screen_w = device_w - 2 * bezel

    # ── 1. Canvas ───────────────────────────────────────────────────
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (*bg, 255))
    draw = ImageDraw.Draw(canvas)

    # ── 2. Measure text, then center between top of canvas & device ─
    verb_font = fit_font(
        verb.upper(),
        max_verb_w,
        preset["verb_size_max"],
        preset["verb_size_min"]
    )
    try:
        desc_font = ImageFont.truetype(FONT_PATH, preset["desc_size"])
    except OSError:
        desc_font = ImageFont.load_default()

    # Measure total text block height (dry run at y=0)
    dummy = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    m_y = 0
    m_y = draw_centered(dummy, m_y, verb.upper(), verb_font, canvas_w)
    m_y += VERB_DESC_GAP
    draw_centered(dummy, m_y, desc.upper(), desc_font, canvas_w, max_w=max_text_w)

    # Device at fixed Y; text starts at fixed position
    # Draw text at centered position
    y = text_top
    y = draw_centered(draw, y, verb.upper(), verb_font, canvas_w)
    y += VERB_DESC_GAP
    draw_centered(draw, y, desc.upper(), desc_font, canvas_w, max_w=max_text_w)
    device_x = (canvas_w - device_w) // 2
    screen_x = device_x + bezel
    screen_y = device_y + bezel

    # ── 4. Screenshot into screen area ──────────────────────────────
    shot = Image.open(screenshot_path).convert("RGBA")

    # Scale to fill screen width
    scale = screen_w / shot.width
    sc_w = screen_w
    sc_h = int(shot.height * scale)
    shot = shot.resize((sc_w, sc_h), Image.LANCZOS)

    # Screen extends to bottom of canvas + overflow
    screen_h = canvas_h - screen_y + 500

    # Screen mask (rounded rect)
    scr_mask = Image.new("L", canvas.size, 0)
    ImageDraw.Draw(scr_mask).rounded_rectangle(
        [screen_x, screen_y, screen_x + screen_w, screen_y + screen_h],
        radius=screen_corner_r,
        fill=255,
    )

    # Black screen bg + screenshot on top
    scr_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(scr_layer).rounded_rectangle(
        [screen_x, screen_y, screen_x + screen_w, screen_y + screen_h],
        radius=screen_corner_r,
        fill=(0, 0, 0, 255),
    )
    scr_layer.paste(shot, (screen_x, screen_y))
    scr_layer.putalpha(scr_mask)

    canvas = Image.alpha_composite(canvas, scr_layer)

    # ── 6. Device frame template ───────────────────────────────────
    frame_template = Image.open(frame_path).convert("RGBA")

    # Place frame template onto canvas-sized layer at calculated position
    frame_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    frame_layer.paste(frame_template, (device_x, device_y))
    canvas = Image.alpha_composite(canvas, frame_layer)

    # ── 7. Save ────────────────────────────────────────────────────
    canvas.convert("RGB").save(output_path, "PNG")
    print(f"✓ {output_path} ({canvas_w}×{canvas_h}, preset={preset_name})")


def main():
    p = argparse.ArgumentParser(description="Compose store screenshot")
    p.add_argument("--bg", required=True, help="Background hex colour (#E31837)")
    p.add_argument("--verb", required=True, help="Action verb (TRACK)")
    p.add_argument("--desc", required=True, help="Benefit descriptor (TRADING CARD PRICES)")
    p.add_argument("--screenshot", required=True, help="Simulator screenshot path")
    p.add_argument("--output", required=True, help="Output file path")
    p.add_argument(
        "--preset",
        default="play-store-android",
        choices=sorted(PRESETS.keys()),
        help="Output preset. Defaults to Play Store / Android portrait."
    )
    args = p.parse_args()

    compose(args.bg, args.verb, args.desc, args.screenshot, args.output, args.preset)


if __name__ == "__main__":
    main()
