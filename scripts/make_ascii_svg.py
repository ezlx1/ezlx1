#!/usr/bin/env python3
"""
make_ascii_svg.py — photo -> typing monochrome ASCII portrait (SVG).

Reads source-prepped.png (output of prep_photo.py) and writes avi-ascii.svg:
a self-contained SVG that "types" itself in via SMIL animation when loaded
as a GitHub README <img>.

Usage:
    python scripts/make_ascii_svg.py
    STATIC=1 python scripts/make_ascii_svg.py   # renders the final frame only,
                                                 # useful for local preview

Tune these to taste:
    CONTRAST     - pushes mid-tones darker/lighter before mapping to chars
    GAMMA        - gamma curve applied after contrast
    WHITE_FLOOR  - brightness (0-255) above which a cell is treated as
                   background and rendered blank (keeps the portrait clean)
    ROW_DUR      - seconds each row takes to "type" across
    STAGGER      - seconds between each row's animation start
"""
import os
import numpy as np
from PIL import Image

# ---- tunables ----
INPUT_PATH = "source-prepped.png"
OUTPUT_PATH = "avi-ascii.svg"

COLS = 100                 # character columns
CHAR_ASPECT = 0.55          # terminal chars are taller than wide; corrects grid sampling

CONTRAST = 1.15
GAMMA = 0.9
WHITE_FLOOR = 245           # treat >= this brightness as background -> blank

ROW_DUR = 0.9
STAGGER = 0.05

FONT_SIZE = 9
LINE_HEIGHT = FONT_SIZE * 1.0
CHAR_WIDTH = FONT_SIZE * 0.6
FILL_COLOR = "#9fb0c3"      # single light-gray-blue, monochrome only

# Density ramp: index 0 = darkest/densest char, last = lightest/blank
RAMP = "@%#*+=-:. "
# --------------------

STATIC = os.environ.get("STATIC", "0") == "1"


def load_grid(path, cols, char_aspect):
    img = Image.open(path).convert("L")
    w, h = img.size
    cell_w = w / cols
    cell_h = cell_w / char_aspect
    rows = max(1, int(h / cell_h))
    img_small = img.resize((cols, rows), Image.LANCZOS)
    return np.array(img_small, dtype=np.float32), cols, rows


def apply_tone_curve(arr, contrast, gamma):
    arr = arr / 255.0
    arr = (arr - 0.5) * contrast + 0.5
    arr = np.clip(arr, 0.0, 1.0)
    arr = arr ** gamma
    return np.clip(arr * 255.0, 0, 255)


def brightness_to_char(v, white_floor):
    if v >= white_floor:
        return " "
    # map 0..white_floor -> ramp index (0 = dense/dark)
    frac = v / white_floor
    idx = int(frac * (len(RAMP) - 2))  # never let plain background map to a glyph
    idx = max(0, min(len(RAMP) - 2, idx))
    return RAMP[idx]


def build_rows(arr, cols, rows, white_floor):
    lines = []
    for r in range(rows):
        line = "".join(brightness_to_char(arr[r, c], white_floor) for c in range(cols))
        lines.append(line.rstrip())
    # trim fully-blank rows at top/bottom
    while lines and lines[0].strip() == "":
        lines.pop(0)
    while lines and lines[-1].strip() == "":
        lines.pop()
    return lines


def escape_xml(s):
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def render_svg(lines):
    max_len = max((len(l) for l in lines), default=0)
    width = int(max_len * CHAR_WIDTH) + 20
    height = int(len(lines) * LINE_HEIGHT) + 20

    parts = []
    parts.append(
        f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'xmlns="http://www.w3.org/2000/svg">'
    )
    parts.append(
        f'<style>text {{ font-family: "SFMono-Regular", Consolas, "Liberation Mono", '
        f'Menlo, monospace; font-size: {FONT_SIZE}px; fill: {FILL_COLOR}; '
        f'white-space: pre; }}</style>'
    )

    row_width_px = max_len * CHAR_WIDTH

    for i, line in enumerate(lines):
        y = 15 + i * LINE_HEIGHT
        safe_line = escape_xml(line)
        clip_id = f"rowclip{i}"

        if STATIC:
            parts.append(f'<text x="10" y="{y:.1f}">{safe_line}</text>')
        else:
            begin = i * STAGGER
            parts.append(f'<clipPath id="{clip_id}">')
            parts.append(
                f'<rect x="10" y="{y - LINE_HEIGHT + 2:.1f}" width="0" height="{LINE_HEIGHT:.1f}">'
                f'<animate attributeName="width" from="0" to="{row_width_px:.1f}" '
                f'dur="{ROW_DUR}s" begin="{begin:.2f}s" fill="freeze" '
                f'calcMode="spline" keySplines="0.25 0.1 0.25 1"/>'
                f'</rect>'
            )
            parts.append('</clipPath>')
            parts.append(
                f'<text x="10" y="{y:.1f}" clip-path="url(#{clip_id})">{safe_line}</text>'
            )

    parts.append('</svg>')
    return "\n".join(parts)


def main():
    if not os.path.exists(INPUT_PATH):
        print(f"Missing {INPUT_PATH} — run prep_photo.py first.")
        return
    arr, cols, rows = load_grid(INPUT_PATH, COLS, CHAR_ASPECT)
    arr = apply_tone_curve(arr, CONTRAST, GAMMA)
    lines = build_rows(arr, cols, rows, WHITE_FLOOR)
    svg = render_svg(lines)
    with open(OUTPUT_PATH, "w") as f:
        f.write(svg)
    print(f"Wrote {OUTPUT_PATH} ({'static' if STATIC else 'animated'}, {len(lines)} rows)")


if __name__ == "__main__":
    main()
