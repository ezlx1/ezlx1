#!/usr/bin/env python3
"""
render_heatmap_svg.py — data/contributions.json -> contrib-heatmap.svg

A GitHub-style grid of boxes that reveal cell by cell, with a Less->More
legend and real streak stats underneath. Monochrome blue-gray levels only.

Usage:
    python scripts/render_heatmap_svg.py
"""
import os
import json
from datetime import datetime

IN_PATH = os.path.join("data", "contributions.json")
OUT_PATH = "contrib-heatmap.svg"

CELL = 11
GAP = 3
LEFT_PAD = 30
TOP_PAD = 20
BOTTOM_PAD = 46

# monochrome blue-gray levels, light -> saturated (no rainbow)
LEVEL_COLORS = ["#1b2430", "#2f4457", "#3f6485", "#5c8fb3", "#84c1e6"]

REVEAL_DUR = 0.25
REVEAL_STAGGER = 0.012  # per-cell offset, ordered by week then day


def main():
    if not os.path.exists(IN_PATH):
        print(f"Missing {IN_PATH} — run fetch_contributions.py first.")
        return

    with open(IN_PATH) as f:
        data = json.load(f)

    days = data["days"]
    if not days:
        print("No days in contributions data.")
        return

    # bucket into weeks (columns), Sunday-start, matching GitHub's layout
    first_date = datetime.strptime(days[0]["date"], "%Y-%m-%d")
    lead_gap = (first_date.weekday() + 1) % 7  # convert Mon=0 to Sun=0 offset

    weeks = []
    week = [None] * lead_gap
    for d in days:
        week.append(d)
        if len(week) == 7:
            weeks.append(week)
            week = []
    if week:
        while len(week) < 7:
            week.append(None)
        weeks.append(week)

    n_weeks = len(weeks)
    width = LEFT_PAD + n_weeks * (CELL + GAP) + 20
    height = TOP_PAD + 7 * (CELL + GAP) + BOTTOM_PAD

    parts = []
    parts.append(
        f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'xmlns="http://www.w3.org/2000/svg">'
    )
    parts.append(
        f'<style>text {{ font-family: "SFMono-Regular", Consolas, "Liberation Mono", '
        f'Menlo, monospace; font-size: 11px; fill: #9fb0c3; }}</style>'
    )
    parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="none"/>')

    idx = 0
    for wi, week in enumerate(weeks):
        for di, d in enumerate(week):
            if d is None:
                continue
            x = LEFT_PAD + wi * (CELL + GAP)
            y = TOP_PAD + di * (CELL + GAP)
            level = min(4, max(0, d["level"]))
            color = LEVEL_COLORS[level]
            begin = idx * REVEAL_STAGGER
            title = f'{d["count"]} contributions on {d["date"]}'
            parts.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" '
                f'fill="{color}" opacity="0">'
                f'<title>{title}</title>'
                f'<animate attributeName="opacity" from="0" to="1" '
                f'dur="{REVEAL_DUR}s" begin="{begin:.3f}s" fill="freeze"/>'
                f'</rect>'
            )
            idx += 1

    # legend: Less -> More
    legend_y = TOP_PAD + 7 * (CELL + GAP) + 18
    parts.append(f'<text x="{LEFT_PAD}" y="{legend_y}">Less</text>')
    lx = LEFT_PAD + 34
    for lvl, color in enumerate(LEVEL_COLORS):
        parts.append(
            f'<rect x="{lx}" y="{legend_y - 9}" width="{CELL}" height="{CELL}" rx="2" fill="{color}"/>'
        )
        lx += CELL + GAP
    parts.append(f'<text x="{lx + 4}" y="{legend_y}">More</text>')

    # stats line
    stats_y = legend_y + 20
    stats = (
        f'{data["total"]} contributions   |   '
        f'current streak {data["current_streak"]}d   |   '
        f'longest streak {data["longest_streak"]}d'
    )
    parts.append(f'<text x="{LEFT_PAD}" y="{stats_y}">{stats}</text>')

    parts.append('</svg>')

    with open(OUT_PATH, "w") as f:
        f.write("\n".join(parts))
    print(f"Wrote {OUT_PATH} ({n_weeks} weeks, {len(days)} days)")


if __name__ == "__main__":
    main()
