#!/usr/bin/env python3
"""
Crop and resize one or more screenshot outputs to an exact target size.

The crop preserves the top edge and trims equally from the left/right sides.
"""

import argparse
from pathlib import Path

from PIL import Image


def resize_image(input_path: Path, target_w: int, target_h: int) -> Path:
    output_path = input_path.with_name(f"{input_path.stem}-resized{input_path.suffix}")

    with Image.open(input_path).convert("RGB") as image:
        crop_w = round(image.height * target_w / target_h)
        crop_w = min(crop_w, image.width)
        offset_x = max((image.width - crop_w) // 2, 0)
        cropped = image.crop((offset_x, 0, offset_x + crop_w, image.height))
        resized = cropped.resize((target_w, target_h), Image.LANCZOS)
        resized.save(output_path, "JPEG" if output_path.suffix.lower() in {".jpg", ".jpeg"} else "PNG")

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Crop and resize outputs to an exact target size")
    parser.add_argument("--target-w", type=int, required=True, help="Target width in pixels")
    parser.add_argument("--target-h", type=int, required=True, help="Target height in pixels")
    parser.add_argument("--inputs", nargs="+", required=True, help="Input image paths")
    args = parser.parse_args()

    for path_str in args.inputs:
        output = resize_image(Path(path_str), args.target_w, args.target_h)
        print(f"✓ {output} ({args.target_w}x{args.target_h})")


if __name__ == "__main__":
    main()
