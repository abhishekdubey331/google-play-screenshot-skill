#!/usr/bin/env python3
"""
Generate device frame template PNGs.
Outputs both:
- assets/device_frame.png for iPhone / App Store preset
- assets/android_device_frame.png for Android / Play Store preset
"""

import os
from PIL import Image, ImageDraw, ImageChops

ASSET_DIR = os.path.join(os.path.dirname(__file__), "assets")

IOS = {
    "device_w": 1030,
    "device_h": 2800,
    "corner_r": 77,
    "bezel": 15,
    "screen_corner_r": 62,
    "output": "assets/device_frame.png",
}

ANDROID = {
    "device_w": 930,
    "device_h": 2250,
    "corner_r": 72,
    "bezel": 14,
    "screen_corner_r": 58,
    "output": "assets/android_device_frame.png",
}


def generate_ios():
    device_w = IOS["device_w"]
    device_h = IOS["device_h"]
    corner_r = IOS["corner_r"]
    bezel = IOS["bezel"]
    screen_corner_r = IOS["screen_corner_r"]
    screen_w = device_w - 2 * bezel
    screen_h = device_h - 2 * bezel
    di_w = 130
    di_h = 38
    di_top = 14

    frame = Image.new("RGBA", (device_w, device_h), (0, 0, 0, 0))
    fd = ImageDraw.Draw(frame)

    # Device body
    fd.rounded_rectangle(
        [0, 0, device_w - 1, device_h - 1],
        radius=corner_r,
        fill=(30, 30, 30, 255),
    )
    fd.rounded_rectangle(
        [1, 1, device_w - 2, device_h - 2],
        radius=corner_r - 1,
        fill=(20, 20, 20, 255),
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

    di_x = (device_w - di_w) // 2
    di_y = screen_y + di_top
    ImageDraw.Draw(frame).rounded_rectangle(
        [di_x, di_y, di_x + di_w, di_y + di_h],
        radius=di_h // 2,
        fill=(0, 0, 0, 255),
    )

    btn_color = (25, 25, 25, 255)
    fd2 = ImageDraw.Draw(frame)
    fd2.rounded_rectangle(
        [device_w, 340, device_w + 4, 460],
        radius=2, fill=btn_color,
    )
    fd2.rounded_rectangle(
        [-4, 280, 0, 360],
        radius=2, fill=btn_color,
    )
    fd2.rounded_rectangle(
        [-4, 380, 0, 460],
        radius=2, fill=btn_color,
    )
    fd2.rounded_rectangle(
        [-4, 180, 0, 220],
        radius=2, fill=btn_color,
    )

    out = os.path.join(os.path.dirname(__file__), IOS["output"])
    frame.save(out, "PNG")
    print(f"✓ {out}")


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
    generate_ios()
    generate_android()
