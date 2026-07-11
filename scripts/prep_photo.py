#!/usr/bin/env python3
"""
prep_photo.py — one-time local prep for the ASCII portrait.

Usage:
    python scripts/prep_photo.py path/to/your-photo.jpg source-prepped.png

What it does:
    1. Removes the background with rembg, so the subject sits on blank space.
    2. Converts to grayscale.
    3. Applies CLAHE (contrast-limited adaptive histogram equalization) so the
       face has real local contrast (highlights/shadows) instead of flattening
       into a dark blob.

Tune `clipLimit` below if the face still looks too flat or too harsh.
"""
import sys
import numpy as np
import cv2
from rembg import remove
from PIL import Image

# ---- tunables ----
clipLimit = 3.0        # higher = more local contrast punch
tileGridSize = (8, 8)   # size of the local regions CLAHE equalizes over
# ------------------


def main():
    if len(sys.argv) != 3:
        print("Usage: python prep_photo.py <input.jpg> <output.png>")
        sys.exit(1)

    in_path, out_path = sys.argv[1], sys.argv[2]

    print(f"Reading {in_path} ...")
    with open(in_path, "rb") as f:
        input_bytes = f.read()

    print("Removing background (rembg) ...")
    output_bytes = remove(input_bytes)

    # rembg returns RGBA PNG bytes with background made transparent
    rgba = Image.open(__import__("io").BytesIO(output_bytes)).convert("RGBA")
    rgba_np = np.array(rgba)

    alpha = rgba_np[:, :, 3]
    rgb = rgba_np[:, :, :3]

    # Grayscale on the subject only
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    # CLAHE for local contrast
    clahe = cv2.createCLAHE(clipLimit=clipLimit, tileGridSize=tileGridSize)
    gray_eq = clahe.apply(gray)

    # Put alpha back so background stays transparent/blank
    out_rgba = np.dstack([gray_eq, gray_eq, gray_eq, alpha])
    out_img = Image.fromarray(out_rgba, mode="RGBA")

    # Flatten onto white background (blank space, not transparency, for the
    # ASCII step which reads plain grayscale values)
    white_bg = Image.new("RGBA", out_img.size, (255, 255, 255, 255))
    flattened = Image.alpha_composite(white_bg, out_img).convert("L")

    flattened.save(out_path)
    print(f"Saved {out_path} ({flattened.size[0]}x{flattened.size[1]})")


if __name__ == "__main__":
    main()
