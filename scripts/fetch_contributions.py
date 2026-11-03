"""Scrape the public contribution calendar (no token needed) into data/contributions.json."""
import json
import os
import re
from collections import OrderedDict
from datetime import date

import requests
from bs4 import BeautifulSoup

USER = os.environ.get("GH_USER", "Elxeoo")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "contributions.json")


def fetch_days():
    r = requests.get(
        f"https://github.com/users/{USER}/contributions",
        headers={"User-Agent": "profile-readme-bot"},
        timeout=30,
    )
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    tips = {t.get("for"): t.get_text(" ", strip=True) for t in soup.find_all("tool-tip")}
    days = []
    for td in soup.select("td.ContributionCalendar-day[data-date]"):
        tip = tips.get(td.get("id"), "")
        m = re.match(r"([\d,]+) contributions?", tip)
        days.append({
            "date": td["data-date"],
            "count": int(m.group(1).replace(",", "")) if m else 0,
            "level": int(td.get("data-level", 0)),
        })
    days.sort(key=lambda d: d["date"])
    if not days:
        raise SystemExit("no contribution cells found - GitHub markup may have changed")
    return days


def stats(days):
    total = sum(d["count"] for d in days)
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] else 0
        longest = max(longest, run)
    # current streak: today may still be empty, so start from yesterday in that case
    current = 0
    rev = list(reversed(days))
    if rev and rev[0]["count"] == 0:
        rev = rev[1:]
    for d in rev:
        if not d["count"]:
            break
        current += 1
    best = max(days, key=lambda d: d["count"])
    months = OrderedDict()
    for d in days:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["count"]
    active = sum(1 for d in days if d["count"])
    return {
        "total": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "active_days": active,
        "months": months,
    }


def main():
    days = fetch_days()
    data = {"user": USER, "generated": date.today().isoformat(), "stats": stats(days), "days": days}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=1)
    s = data["stats"]
    print(f"{USER}: {s['total']} contributions, streak {s['current_streak']} (longest {s['longest_streak']})")


if __name__ == "__main__":
    main()
