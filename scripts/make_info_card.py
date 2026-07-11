#!/usr/bin/env python3
"""
make_info_card.py — your experience/stack/highlights -> neofetch-style panel SVG.

EDIT THE ROWS LIST AND HOST BELOW, then run:
    python scripts/make_info_card.py
-> produces info-card.svg

Keep H the same as avi-ascii.svg's rendered height; if this overflows, bump H.
"""
import os

# ---- EDIT ME ----
USER = "aws"
HOST = "sec-space"

ROWS = [
    ("Role", "SOC Analyst / Red Team (junior)"),
    ("Location", "Amman, Jordan"),
    ("Education", "B.Sc. Computer Science, Tafila Technical University ('26)"),
    ("Project", "SEC-SPACE — security toolkit + blog (co-founder)"),
    ("Experience", "PCI DSS ASV vuln assessments — Banyamer Security"),
    ("Track record", "TryHackMe top 5% (310+ rooms), ~80% HTB tracks"),
    ("Certs", "eJPTv2 Prep, TryHackMe SOC path, Edraak Cyber Security"),
    ("Focus", "SIEM (Wazuh), Active Directory attack paths, malware triage"),
]

W = 490
H = 370
# ------------------

FONT_SIZE = 13
LINE_HEIGHT = 22
LABEL_COLOR = "#7fa8c9"     # muted blue for labels, still monochrome-adjacent
VALUE_COLOR = "#9fb0c3"     # matches the portrait's gray
ACCENT = "#9fb0c3"

ROW_DUR = 0.35
STAGGER = 0.09

STATIC = os.environ.get("STATIC", "0") == "1"
OUTPUT_PATH = "info-card.svg"


def escape_xml(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    parts = []
    parts.append(
        f'<svg viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'xmlns="http://www.w3.org/2000/svg">'
    )
    parts.append(
        f'<style>'
        f'text {{ font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace; '
        f'font-size: {FONT_SIZE}px; white-space: pre; }}'
        f'.label {{ fill: {LABEL_COLOR}; font-weight: bold; }}'
        f'.value {{ fill: {VALUE_COLOR}; }}'
        f'.header {{ fill: {ACCENT}; font-weight: bold; font-size: {FONT_SIZE + 2}px; }}'
        f'.rule {{ stroke: {ACCENT}; stroke-width: 1; opacity: 0.4; }}'
        f'</style>'
    )

    y = 30
    header = f"{USER}@{HOST}"
    entries = [("__header__", header)] + [("__rule__", "")] + ROWS

    row_i = 0
    for kind, *rest in entries:
        if kind == "__header__":
            text = rest[0]
            if STATIC:
                parts.append(f'<text x="20" y="{y}" class="header">{escape_xml(text)}</text>')
            else:
                clip = f'clip_h'
                width_px = len(text) * (FONT_SIZE * 0.62)
                parts.append(f'<clipPath id="{clip}"><rect x="20" y="{y-16}" width="0" height="24">'
                              f'<animate attributeName="width" from="0" to="{width_px:.1f}" '
                              f'dur="0.6s" begin="0s" fill="freeze"/></rect></clipPath>')
                parts.append(f'<text x="20" y="{y}" class="header" clip-path="url(#{clip})">{escape_xml(text)}</text>')
            y += LINE_HEIGHT + 6
        elif kind == "__rule__":
            parts.append(f'<line x1="20" y1="{y-14}" x2="{W-20}" y2="{y-14}" class="rule"/>')
            y += 10
        else:
            label, value = kind, rest[0]
            full_line = f"{label:<12}: {value}"
            if STATIC:
                parts.append(f'<text x="20" y="{y}">'
                              f'<tspan class="label">{escape_xml(label)}</tspan>'
                              f'<tspan class="value">: {escape_xml(value)}</tspan></text>')
            else:
                clip = f'clip_r{row_i}'
                width_px = len(full_line) * (FONT_SIZE * 0.62)
                begin = row_i * STAGGER
                parts.append(f'<clipPath id="{clip}"><rect x="20" y="{y-14}" width="0" height="18">'
                              f'<animate attributeName="width" from="0" to="{width_px:.1f}" '
                              f'dur="{ROW_DUR}s" begin="{begin:.2f}s" fill="freeze"/></rect></clipPath>')
                parts.append(f'<text x="20" y="{y}" clip-path="url(#{clip})">'
                              f'<tspan class="label">{escape_xml(label)}</tspan>'
                              f'<tspan class="value">: {escape_xml(value)}</tspan></text>')
            row_i += 1
            y += LINE_HEIGHT

    parts.append('</svg>')

    with open(OUTPUT_PATH, "w") as f:
        f.write("\n".join(parts))
    print(f"Wrote {OUTPUT_PATH} ({'static' if STATIC else 'animated'}, height budget {H}, used ~{y})")


if __name__ == "__main__":
    main()
