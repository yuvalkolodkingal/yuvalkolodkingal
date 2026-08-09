#!/usr/bin/env python3
"""Scrape the public contribution calendar into data/contributions.json.

GitHub serves the calendar as a plain HTML fragment at
https://github.com/users/<username>/contributions, the same markup the
profile page itself renders. It is public, so this needs no GraphQL API and
no personal access token.

Usage:
    python scripts/fetch_contributions.py [username]
"""

import json
import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = "yuvalkolodkingal"
URL = "https://github.com/users/{user}/contributions"
OUT = Path(__file__).resolve().parent.parent / "data" / "contributions.json"

# "No contributions on January 1st." / "12 contributions on March 3rd."
COUNT_RE = re.compile(r"^\s*(No|[\d,]+)\s+contribution")
TOTAL_RE = re.compile(r"([\d,]+)\s+contributions?\s+in\s+the\s+last\s+year")


def fetch_html(user):
    response = requests.get(
        URL.format(user=user),
        headers={
            "User-Agent": "profile-readme-art/1.0 (+https://github.com/%s)" % user,
            "Accept": "text/html",
            "X-Requested-With": "XMLHttpRequest",
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.text


def parse_days(html):
    """Return [{date, count, level}, ...] sorted oldest first."""
    soup = BeautifulSoup(html, "html.parser")

    # Counts live in <tool-tip for="..."> siblings rather than on the cell
    # itself in the current markup, so index them by the id they point at.
    tooltips = {}
    for tip in soup.find_all("tool-tip"):
        target = tip.get("for")
        if target:
            tooltips[target] = tip.get_text(" ", strip=True)

    days = {}
    for cell in soup.select("td.ContributionCalendar-day"):
        day = cell.get("data-date")
        if not day:
            continue

        count = cell.get("data-count")
        if count is None:
            text = tooltips.get(cell.get("id", ""), "") or cell.get(
                "aria-label", ""
            )
            match = COUNT_RE.match(text)
            count = 0 if not match else (
                0 if match.group(1) == "No" else int(match.group(1).replace(",", ""))
            )
        else:
            count = int(count)

        days[day] = {
            "date": day,
            "count": count,
            "level": int(cell.get("data-level") or 0),
        }

    return [days[key] for key in sorted(days)]


def parse_total(html, days):
    match = TOTAL_RE.search(html)
    if match:
        return int(match.group(1).replace(",", ""))
    return sum(day["count"] for day in days)


def streaks(days):
    """Current and longest run of consecutive days with any activity.

    A zero on today does not break the current streak, because the day is not
    over yet. That is how GitHub's own streak reads.
    """
    longest = run = 0
    for day in days:
        run = run + 1 if day["count"] > 0 else 0
        longest = max(longest, run)

    current = 0
    for index, day in enumerate(reversed(days)):
        if day["count"] > 0:
            current += 1
        elif index == 0:
            continue  # today is still in progress
        else:
            break

    return current, longest


def summarise(days, total):
    best = max(days, key=lambda day: day["count"]) if days else {"date": None, "count": 0}
    months = {}
    for day in days:
        months[day["date"][:7]] = months.get(day["date"][:7], 0) + day["count"]

    current, longest = streaks(days)
    active = sum(1 for day in days if day["count"] > 0)

    return {
        "username": USERNAME,
        "generated": date.today().isoformat(),
        "total": total,
        "days": days,
        "stats": {
            "current_streak": current,
            "longest_streak": longest,
            "active_days": active,
            "best_day": best["date"],
            "best_day_count": best["count"],
            "monthly": months,
        },
    }


def empty_calendar():
    """A blank 53-week grid, used only if the scrape fails and no cache exists.

    The daily workflow overwrites this with real data on its first run, so it
    exists purely to keep the SVG renderable rather than crashing the build.
    """
    end = date.today()
    # weekday() is Monday=0..Sunday=6, so this backs up to the most recent Sunday.
    start = end - timedelta(days=(end.weekday() + 1) % 7)
    start = start - timedelta(weeks=52)
    days = [
        {"date": (start + timedelta(days=offset)).isoformat(), "count": 0, "level": 0}
        for offset in range((end - start).days + 1)
    ]
    return summarise(days, 0)


def main():
    user = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GH_USERNAME", USERNAME)

    try:
        html = fetch_html(user)
        days = parse_days(html)
        if not days:
            raise ValueError("no contribution cells found in the response")
        payload = summarise(days, parse_total(html, days))
    except Exception as error:  # network down, markup changed, rate limited
        print(f"warning: could not fetch contributions for {user}: {error}")
        if OUT.exists():
            print(f"keeping the existing {OUT.name}")
            return 0
        print("writing an empty calendar as a placeholder")
        payload = empty_calendar()

    payload["username"] = user
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")

    stats = payload["stats"]
    print(
        f"{OUT}: {payload['total']} contributions, "
        f"{len(payload['days'])} days, "
        f"current streak {stats['current_streak']}, "
        f"longest {stats['longest_streak']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
