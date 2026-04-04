#!/usr/bin/env python3
"""
Generate Android device frame template PNG.
Output:
- assets/android_device_frame.png for Google Play preset
"""

import os
from PIL import Image, ImageDraw, ImageChops

ANDROID = {
    "device_w": 930,
    "device_h": 2250,
    "corner_r": 72,
    "bezel": 14,
    "screen_corner_r": 58,
    "output": "assets/android_device_frame.png",
}


def generate_android():
    device_w = ANDROID["device_w"]
    device_h = ANDROID["device_h"]
    corner_r = ANDROID["corner_r"]
    bezel = ANDROID["bezel"]
    screen_corner_r = ANDROID["screen_corner_r"]
    screen_w = device_w - 2 * bezel
    screen_h = device_h - 2 * bezel

    frame = Image.new("RGBA", (device_w, device_h), (0, 0, 0, 0))
    fd = ImageDraw.Draw(frame)

    fd.rounded_rectangle(
        [0, 0, device_w - 1, device_h - 1],
        radius=corner_r,
        fill=(28, 28, 28, 255),
    )
    fd.rounded_rectangle(
        [1, 1, device_w - 2, device_h - 2],
        radius=corner_r - 1,
        fill=(18, 18, 18, 255),
    )

    screen_x = bezel
    screen_y = bezel
    cutout = Image.new("L", (device_w, device_h), 255)
    ImageDraw.Draw(cutout).rounded_rectangle(
        [screen_x, screen_y, screen_x + screen_w, screen_y + screen_h],
        radius=screen_corner_r,
        fill=0,
    )
    frame.putalpha(ImageChops.multiply(frame.getchannel("A"), cutout))

    # Punch-hole camera cutout for a modern Android look.
    hole_r = 16
    hole_x = device_w // 2
    hole_y = screen_y + 34
    ImageDraw.Draw(frame).ellipse(
        [hole_x - hole_r, hole_y - hole_r, hole_x + hole_r, hole_y + hole_r],
        fill=(0, 0, 0, 255),
    )

    btn_color = (22, 22, 22, 255)
    fd2 = ImageDraw.Draw(frame)
    fd2.rounded_rectangle(
        [device_w, 320, device_w + 4, 510],
        radius=2, fill=btn_color,
    )
    fd2.rounded_rectangle(
        [device_w, 560, device_w + 4, 680],
        radius=2, fill=btn_color,
    )

    out = os.path.join(os.path.dirname(__file__), ANDROID["output"])
    frame.save(out, "PNG")
    print(f"✓ {out}")


if __name__ == "__main__":
    generate_android()

