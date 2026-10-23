#!/usr/bin/env python3
"""Generate a GitHub-safe SVG activity card for a profile README."""

from __future__ import annotations

import argparse
import json
import os
import urllib.request
from datetime import UTC, date, datetime
from html import escape
from pathlib import Path


QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays { contributionCount date weekday }
        }
      }
      commitContributionsByRepository(maxRepositories: 100) {
        repository { name url }
        contributions { totalCount }
      }
    }
  }
}
"""

BLUE = ("#1a2433", "#0e376d", "#1558b0", "#1f6feb", "#58a6ff")


def github_data(login: str, token: str) -> dict:
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "profile-activity-card",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    user = payload.get("data", {}).get("user")
    if not user:
        raise RuntimeError(f"GitHub user {login!r} was not found")
    return user["contributionsCollection"]


def sample_data() -> dict:
    days = []
    start = date(2025, 10, 19)
    active = {12: 2, 18: 3, 43: 1, 86: 4, 133: 2, 174: 3, 219: 1, 263: 4, 301: 2, 342: 3, 355: 4, 361: 2}
    for offset in range(371):
        current = date.fromordinal(start.toordinal() + offset)
        days.append({
            "date": current.isoformat(),
            "weekday": (current.weekday() + 1) % 7,
            "contributionCount": active.get(offset, 0),
        })
    weeks = [{"contributionDays": days[index:index + 7]} for index in range(0, len(days), 7)]
    return {
        "totalCommitContributions": 51,
        "totalIssueContributions": 1,
        "totalPullRequestContributions": 1,
        "contributionCalendar": {"totalContributions": 222, "weeks": weeks},
        "commitContributionsByRepository": [
            {"repository": {"name": "lth-on-nid", "url": "#"}, "contributions": {"totalCount": 33}},
            {"repository": {"name": "rseyfullayev", "url": "#"}, "contributions": {"totalCount": 14}},
            {"repository": {"name": "SNN", "url": "#"}, "contributions": {"totalCount": 3}},
            {"repository": {"name": "tripweave", "url": "#"}, "contributions": {"totalCount": 1}},
        ],
    }


def level(count: int, maximum: int) -> int:
    if count <= 0:
        return 0
    ratio = count / max(maximum, 1)
    if ratio < 0.25:
        return 1
    if ratio < 0.5:
        return 2
    if ratio < 0.75:
        return 3
    return 4


def render(data: dict, login: str) -> str:
    calendar = data["contributionCalendar"]
    weeks = calendar["weeks"][-53:]
    all_days = [day for week in weeks for day in week["contributionDays"]]
    maximum = max((day["contributionCount"] for day in all_days), default=1)
    commits = data.get("totalCommitContributions", 0)
    prs = data.get("totalPullRequestContributions", 0)
    issues = data.get("totalIssueContributions", 0)
    all_repos = data.get("commitContributionsByRepository", [])
    repos = all_repos[:4]
    repository_count = len(all_repos)
    total = calendar.get("totalContributions", 0)
    max_repo = max((item["contributions"]["totalCount"] for item in repos), default=1)

    cells = []
    for column, week in enumerate(weeks):
        for day in week["contributionDays"]:
            x = 58 + column * 20
            y = 286 + day["weekday"] * 20
            color = BLUE[level(day["contributionCount"], maximum)]
            cells.append(f'<rect x="{x}" y="{y}" width="14" height="14" rx="3" fill="{color}"/>')

    repo_rows = []
    for index, item in enumerate(repos):
        name = escape(item["repository"]["name"])
        count = item["contributions"]["totalCount"]
        y = 514 + index * 34
        bar = int(170 * count / max_repo)
        repo_rows.append(
            f'<text x="72" y="{y}" class="repo">{name}</text>'
            f'<text x="350" y="{y}" class="muted" text-anchor="end">{count} commits</text>'
            f'<rect x="380" y="{y - 11}" width="170" height="8" rx="4" fill="#21262d"/>'
            f'<rect x="380" y="{y - 11}" width="{bar}" height="8" rx="4" fill="#2f81f7"/>'
        )

    updated = datetime.now(UTC).strftime("%d %b %Y")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="660" viewBox="0 0 1200 660" role="img" aria-labelledby="title desc">
<title id="title">{escape(login)} development activity</title>
<desc id="desc">A summary of GitHub contributions, commits, pull requests, issues, and top repositories.</desc>
<style>
  .title {{ font: 700 28px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill: #f0f3f6; }}
  .number {{ font: 700 28px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill: #f0f3f6; }}
  .label {{ font: 400 14px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill: #8b949e; }}
  .section {{ font: 650 18px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill: #f0f3f6; }}
  .repo {{ font: 500 14px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill: #f0f3f6; }}
  .muted {{ font: 400 12px -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; fill: #8b949e; }}
</style>
<rect width="1200" height="660" rx="18" fill="#0d1117"/>
<text x="44" y="54" class="title">Development activity</text>
<text x="1156" y="50" class="muted" text-anchor="end">Updated {updated}</text>

<g>
  <rect x="44" y="82" width="264" height="112" rx="12" fill="#161b22" stroke="#30363d"/>
  <circle cx="84" cy="138" r="24" fill="#12253f"/><path d="M74 149v-10m10 10v-22m10 22v-31" stroke="#58a6ff" stroke-width="5" stroke-linecap="round"/>
  <text x="126" y="132" class="number">{total}</text><text x="126" y="155" class="label">contributions</text>
  <rect x="326" y="82" width="264" height="112" rx="12" fill="#161b22" stroke="#30363d"/>
  <circle cx="366" cy="138" r="24" fill="#12253f"/><path d="M356 128h20m-20 0v20m20-20v20" stroke="#58a6ff" stroke-width="3" stroke-linecap="round"/><circle cx="356" cy="128" r="4" fill="#58a6ff"/><circle cx="376" cy="148" r="4" fill="#58a6ff"/>
  <text x="408" y="132" class="number">{commits}</text><text x="408" y="155" class="label">commits</text>
  <rect x="608" y="82" width="264" height="112" rx="12" fill="#161b22" stroke="#30363d"/>
  <circle cx="648" cy="138" r="24" fill="#12253f"/><path d="M638 126h20v24h-20z" fill="none" stroke="#58a6ff" stroke-width="3"/>
  <text x="690" y="132" class="number">{repository_count}</text><text x="690" y="155" class="label">repositories</text>
  <rect x="890" y="82" width="266" height="112" rx="12" fill="#161b22" stroke="#30363d"/>
  <circle cx="930" cy="138" r="24" fill="#12253f"/><circle cx="930" cy="138" r="9" fill="none" stroke="#58a6ff" stroke-width="3"/><path d="M930 124v-5m0 38v-5" stroke="#58a6ff" stroke-width="3"/>
  <text x="972" y="132" class="number">{prs}</text><text x="972" y="155" class="label">pull requests</text>
</g>

<rect x="44" y="216" width="1112" height="236" rx="12" fill="#161b22" stroke="#30363d"/>
<text x="66" y="252" class="section">Contribution history</text>
<text x="66" y="420" class="muted">Less activity</text>
<rect x="142" y="410" width="12" height="12" rx="3" fill="#1a2433"/><rect x="160" y="410" width="12" height="12" rx="3" fill="#0e376d"/><rect x="178" y="410" width="12" height="12" rx="3" fill="#1558b0"/><rect x="196" y="410" width="12" height="12" rx="3" fill="#1f6feb"/><rect x="214" y="410" width="12" height="12" rx="3" fill="#58a6ff"/>
<text x="236" y="420" class="muted">More activity</text>
{''.join(cells)}

<rect x="44" y="474" width="530" height="154" rx="12" fill="#161b22" stroke="#30363d"/>
<text x="66" y="500" class="section">Top repositories</text>
{''.join(repo_rows)}

<rect x="592" y="474" width="564" height="154" rx="12" fill="#161b22" stroke="#30363d"/>
<text x="614" y="500" class="section">At a glance</text>
<text x="614" y="536" class="repo">{commits} commits across public repositories</text>
<line x1="614" y1="550" x2="1134" y2="550" stroke="#30363d"/>
<text x="614" y="578" class="repo">{prs} pull requests · {issues} issues</text>
<text x="614" y="606" class="muted">Public activity reported by GitHub</text>
</svg>'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--login", default=os.getenv("GITHUB_REPOSITORY_OWNER", "rseyfullayev"))
    parser.add_argument("--token", default=os.getenv("GITHUB_TOKEN"))
    parser.add_argument("--output", default="assets/development-activity.svg")
    parser.add_argument("--sample", action="store_true")
    args = parser.parse_args()
    data = sample_data() if args.sample else github_data(args.login, args.token or "")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(data, args.login), encoding="utf-8")


if __name__ == "__main__":
    main()
