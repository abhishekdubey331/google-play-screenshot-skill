#!/usr/bin/env python3
"""
Generate a Google Play feature graphic (1024x500).

The output is intended for the Play Store "Feature Graphic" slot:
https://support.google.com/googleplay/android-developer/answer/9866151
"""

import argparse
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_PATH = "/Library/Fonts/SF-Pro-Display-Black.otf"
CANVAS_W = 1024
CANVAS_H = 500


def load_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except OSError:
        return ImageFont.load_default()


def hex_to_rgb(h):
    h = h.lstrip("#")
    if len(h) != 6:
        raise ValueError("Hex colour must be in RRGGBB format.")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def fit_font(text, max_w, size_max, size_min, step=2):
    dummy = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    for size in range(size_max, size_min - 1, -step):
        font = load_font(size)
        width = dummy.textbbox((0, 0), text, font=font)[2]
        if width <= max_w:
            return font
    return load_font(size_min)


def build_feature_graphic(bg_hex, title, subtitle, screenshot_path, output_path):
    bg = hex_to_rgb(bg_hex)
    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), bg)
    draw = ImageDraw.Draw(canvas)

    # Left text block area
    left_pad = 64
    text_max_w = 510
    title_font = fit_font(title.upper(), text_max_w, 86, 44)
    subtitle_font = fit_font(subtitle.upper(), text_max_w, 42, 24)

    # Right screenshot card area
    card_w, card_h = 330, 420
    card_x, card_y = CANVAS_W - card_w - 76, 40
    card_r = 26

    shot = Image.open(screenshot_path).convert("RGB")
    scale = max(card_w / shot.width, card_h / shot.height)
    resized = shot.resize((int(shot.width * scale), int(shot.height * scale)), Image.LANCZOS)
    crop_x = (resized.width - card_w) // 2
    crop_y = (resized.height - card_h) // 2
    shot_cropped = resized.crop((crop_x, crop_y, crop_x + card_w, crop_y + card_h))

    # Soft shadow for the screenshot card
    shadow = Image.new("RGBA", (card_w + 20, card_h + 20), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([10, 10, card_w + 10, card_h + 10], radius=card_r, fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(8))
    canvas.paste(shadow, (card_x - 10, card_y - 8), shadow)

    mask = Image.new("L", (card_w, card_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, card_w, card_h], radius=card_r, fill=255)
    canvas.paste(shot_cropped, (card_x, card_y), mask)

    # Text rendering
    title_y = 148
    draw.text((left_pad, title_y), title.upper(), font=title_font, fill="white")
    draw.text((left_pad, title_y + 116), subtitle.upper(), font=subtitle_font, fill=(235, 245, 255))

    canvas.save(output_path, "PNG")
    print(f"✓ {output_path} ({CANVAS_W}x{CANVAS_H})")


def main():
    parser = argparse.ArgumentParser(description="Generate Google Play feature graphic (1024x500)")
    parser.add_argument("--bg", required=True, help="Background hex colour (e.g. #2563EB)")
    parser.add_argument("--title", required=True, help="Primary headline (e.g. TRACK)")
    parser.add_argument("--subtitle", required=True, help="Secondary line (e.g. CARD PRICES LIVE)")
    parser.add_argument("--screenshot", required=True, help="Input screenshot path")
    parser.add_argument("--output", required=True, help="Output PNG path")
    args = parser.parse_args()

    build_feature_graphic(args.bg, args.title, args.subtitle, args.screenshot, args.output)


if __name__ == "__main__":
    main()

