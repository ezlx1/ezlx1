#!/usr/bin/env python3
"""
fetch_contributions.py — scrapes your real GitHub contribution calendar from
the public profile page. No token/auth required (this is the same data GitHub
renders on your profile for anyone to see).

Usage:
    GH_PROFILE_USER=your-username python scripts/fetch_contributions.py

Writes data/contributions.json:
    {
      "user": "...",
      "generated_at": "...",
      "days": [{"date": "2026-07-11", "count": 3, "level": 2}, ...],
      "total": 1234,
      "current_streak": 7,
      "longest_streak": 41
    }
"""
import os
import re
import json
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

USER = os.environ.get("GH_PROFILE_USER", "").strip()
OUT_PATH = os.path.join("data", "contributions.json")


def fetch_html(user):
    url = f"https://github.com/users/{user}/contributions"
    resp = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0 (profile-art-script)"},
        timeout=20,
    )
    resp.raise_for_status()
    return resp.text


def parse_days(html):
    soup = BeautifulSoup(html, "html.parser")
    days = []

    # Newer GitHub markup: <table>/<td> or <rect> elements with data-date
    cells = soup.select("[data-date]")
    for cell in cells:
        date = cell.get("data-date")
        if not date:
            continue

        level = cell.get("data-level")
        count = cell.get("data-count")

        if count is not None:
            count = int(count)
        else:
            # fall back to parsing the tooltip text, e.g. "5 contributions on ..."
            tip_id = cell.get("id")
            tooltip_text = None
            if tip_id:
                tip = soup.find(attrs={"for": tip_id})
                if tip:
                    tooltip_text = tip.get_text(strip=True)
            if not tooltip_text:
                tooltip_text = cell.get("aria-label", "") or cell.get("title", "")
            m = re.search(r"(\d+)\s+contribution", tooltip_text or "")
            if m:
                count = int(m.group(1))
            elif "No contributions" in (tooltip_text or ""):
                count = 0
            else:
                count = 0

        if level is not None:
            level = int(level)
        else:
            # rough bucket if GitHub didn't give us a level
            if count == 0:
                level = 0
            elif count <= 2:
                level = 1
            elif count <= 5:
                level = 2
            elif count <= 9:
                level = 3
            else:
                level = 4

        days.append({"date": date, "count": count, "level": level})

    days.sort(key=lambda d: d["date"])
    return days


def compute_streaks(days):
    total = sum(d["count"] for d in days)
    longest = 0
    current = 0
    running = 0
    for d in days:
        if d["count"] > 0:
            running += 1
            longest = max(longest, running)
        else:
            running = 0
    # current streak = trailing run of active days, from the end
    for d in reversed(days):
        if d["count"] > 0:
            current += 1
        else:
            break
    return total, current, longest


def main():
    if not USER:
        print("Set GH_PROFILE_USER to your GitHub username.")
        return

    print(f"Fetching contributions for {USER} ...")
    html = fetch_html(USER)
    days = parse_days(html)

    if not days:
        print("No contribution cells found — GitHub may have changed its markup.")
        return

    total, current, longest = compute_streaks(days)

    payload = {
        "user": USER,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "days": days,
        "total": total,
        "current_streak": current,
        "longest_streak": longest,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"Wrote {OUT_PATH}: {len(days)} days, {total} total, "
          f"current streak {current}, longest streak {longest}")


if __name__ == "__main__":
    main()
