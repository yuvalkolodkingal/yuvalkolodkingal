#!/usr/bin/env python3
"""Fetch public GitHub stats into a JSON cache: totals, languages, activity.

Uses the REST API. A token is optional but recommended: inside GitHub Actions
the built-in GITHUB_TOKEN raises the limit from 60 to 1000 requests an hour,
which matters because language bytes are one request per repository.

Every section degrades on its own. If the events endpoint fails, the
languages still update and the previous activity list is kept from the old
cache; if everything fails the old cache is kept untouched. This script never
raises, because it runs unattended in a daily job.

Usage:
    python fetch_github.py <username> [data/github.json]
    GITHUB_TOKEN=... python fetch_github.py <username>
"""

import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import requests

API = "https://api.github.com"
MAX_LANGUAGE_REPOS = 60     # newest-pushed repos that get a languages request
MAX_ACTIVITY = 12

# Linguist colours for the languages people actually have on their profiles.
# Anything else falls back to the theme's accent cycle at render time.
LANGUAGE_COLOURS = {
    "Python": "#3572A5", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
    "HTML": "#e34c26", "CSS": "#663399", "SCSS": "#c6538c", "Shell": "#89e051",
    "C": "#555555", "C++": "#f34b7d", "C#": "#178600", "Java": "#b07219",
    "Go": "#00ADD8", "Rust": "#dea584", "Ruby": "#701516", "PHP": "#4F5D95",
    "Swift": "#F05138", "Kotlin": "#A97BFF", "Dart": "#00B4AB", "Scala": "#c22d40",
    "R": "#198CE7", "Julia": "#a270ba", "MATLAB": "#e16737", "Lua": "#000080",
    "Perl": "#0298c3", "Haskell": "#5e5086", "Elixir": "#6e4a7e", "Erlang": "#B83998",
    "Clojure": "#db5855", "OCaml": "#ef7a08", "Zig": "#ec915c", "Nim": "#ffc200",
    "Vue": "#41b883", "Svelte": "#ff3e00", "Astro": "#ff5a03", "Jupyter Notebook": "#DA5B0B",
    "Dockerfile": "#384d54", "Makefile": "#427819", "CMake": "#DA3434", "Nix": "#7e7eff",
    "PowerShell": "#012456", "Vim Script": "#199f4b", "Emacs Lisp": "#c065db",
    "Objective-C": "#438eff", "Assembly": "#6E4C13", "Verilog": "#b2b7f8", "VHDL": "#adb2cb",
    "Solidity": "#AA6746", "GLSL": "#5686a5", "TeX": "#3D6117", "Markdown": "#083fa1",
    "Mojo": "#ff4c1f", "Cuda": "#3A4E3A", "Fortran": "#4d41b1", "Prolog": "#74283c",
    "Groovy": "#4298b8", "Batchfile": "#C1F12E", "Smalltalk": "#596706", "Elm": "#60B5CC",
    "F#": "#b845fc", "Crystal": "#000100", "Gleam": "#ffaff3", "Odin": "#60AFFE",
}


def _session(token):
    session = requests.Session()
    session.headers.update({
        "Accept": "application/vnd.github+json",
        "User-Agent": "github-profile-designer/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
    return session


def _get(session, url, **params):
    response = session.get(url, params=params or None, timeout=30)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def _paginate(session, url, **params):
    page = 1
    while True:
        chunk = _get(session, url, page=page, per_page=100, **params) or []
        yield from chunk
        if len(chunk) < 100 or page >= 5:
            return
        page += 1


def _age(iso, now):
    then = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    seconds = max(0, int((now - then).total_seconds()))
    for unit, size in (("y", 31536000), ("mo", 2592000), ("w", 604800), ("d", 86400), ("h", 3600), ("m", 60)):
        if seconds >= size:
            return f"{seconds // size}{unit} ago"
    return "just now"


def fetch_user(session, user):
    data = _get(session, f"{API}/users/{user}")
    if not data:
        raise ValueError(f"no such user {user!r}")
    return {
        "login": data.get("login", user),
        "name": data.get("name") or user,
        "bio": data.get("bio") or "",
        "company": data.get("company") or "",
        "location": data.get("location") or "",
        "blog": data.get("blog") or "",
        "avatar_url": data.get("avatar_url") or "",
        "followers": int(data.get("followers") or 0),
        "following": int(data.get("following") or 0),
        "public_repos": int(data.get("public_repos") or 0),
        "created_at": (data.get("created_at") or "")[:10],
    }


def fetch_repos(session, user):
    repos = []
    for repo in _paginate(session, f"{API}/users/{user}/repos", type="owner", sort="pushed"):
        repos.append({
            "name": repo["name"],
            "full_name": repo.get("full_name", f"{user}/{repo['name']}"),
            "description": repo.get("description") or "",
            "url": repo.get("html_url", ""),
            "stars": int(repo.get("stargazers_count") or 0),
            "forks": int(repo.get("forks_count") or 0),
            "language": repo.get("language") or "",
            "fork": bool(repo.get("fork")),
            "archived": bool(repo.get("archived")),
            "pushed_at": repo.get("pushed_at") or "",
            "topics": list(repo.get("topics") or []),
        })
    return repos


def fetch_languages(session, repos, max_repos=MAX_LANGUAGE_REPOS, cap_share=0.4, exclude=()):
    """Bytes per language across original, non-archived repos.

    cap_share limits how much of the grand total any single repository may
    contribute (0.4 = 40 percent), so one vendored bundle does not turn a
    Python developer into a JavaScript one. Set it to 1 to disable.
    """
    per_repo = []
    candidates = [r for r in repos if not r["fork"] and not r["archived"] and r["full_name"] not in exclude and r["name"] not in exclude]
    candidates.sort(key=lambda r: r["pushed_at"], reverse=True)
    for repo in candidates[:max_repos]:
        try:
            bytes_by_language = _get(session, f"{API}/repos/{repo['full_name']}/languages") or {}
        except requests.HTTPError as error:  # rate limited part way: keep what we have
            print(f"warning: languages for {repo['full_name']}: {error}")
            break
        if bytes_by_language:
            per_repo.append({name: int(size) for name, size in bytes_by_language.items()})
    totals = {}
    if per_repo:
        grand_raw = sum(sum(r.values()) for r in per_repo) or 1
        ceiling = grand_raw * float(cap_share) if 0 < float(cap_share) < 1 else None
        for languages in per_repo:
            size = sum(languages.values())
            scale = min(1.0, ceiling / size) if ceiling and size > ceiling else 1.0
            for name, value in languages.items():
                totals[name] = totals.get(name, 0) + int(value * scale)
    if not totals:  # no token and nothing readable: count primary languages instead
        for repo in candidates:
            if repo["language"]:
                totals[repo["language"]] = totals.get(repo["language"], 0) + 1
    grand = sum(totals.values()) or 1
    ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)
    return [
        {
            "name": name,
            "bytes": size,
            "percent": round(size / grand * 100, 1),
            "color": LANGUAGE_COLOURS.get(name, ""),
        }
        for name, size in ranked
    ]


def _describe(event):
    kind = event.get("type", "")
    payload = event.get("payload", {}) or {}
    repo = (event.get("repo") or {}).get("name", "")
    if kind == "PushEvent":
        commits = payload.get("commits") or []
        count = max(int(payload.get("size") or 0), len(commits), 1)
        head = commits[-1].get("message", "").splitlines()[0] if commits else ""
        return "push", f"{count} commit{'s' if count != 1 else ''} to {repo}", head
    if kind == "PullRequestEvent":
        pr = payload.get("pull_request") or {}
        action = payload.get("action", "")
        if action == "closed" and pr.get("merged"):
            action = "merged"
        return "pr", f"{action} PR #{pr.get('number', '')} in {repo}", pr.get("title", "")
    if kind == "IssuesEvent":
        issue = payload.get("issue") or {}
        return "issue", f"{payload.get('action', '')} issue #{issue.get('number', '')} in {repo}", issue.get("title", "")
    if kind == "CreateEvent":
        ref_type = payload.get("ref_type", "")
        ref = payload.get("ref") or ""
        if ref_type == "repository":
            return "create", f"created repository {repo}", ""
        return "create", f"created {ref_type} {ref} in {repo}", ""
    if kind == "WatchEvent":
        return "star", f"starred {repo}", ""
    if kind == "ForkEvent":
        return "fork", f"forked {repo}", ""
    if kind == "ReleaseEvent":
        release = payload.get("release") or {}
        return "release", f"released {release.get('tag_name', '')} of {repo}", release.get("name", "")
    if kind == "IssueCommentEvent":
        issue = payload.get("issue") or {}
        return "comment", f"commented on #{issue.get('number', '')} in {repo}", issue.get("title", "")
    if kind == "PullRequestReviewEvent":
        pr = payload.get("pull_request") or {}
        return "review", f"reviewed PR #{pr.get('number', '')} in {repo}", pr.get("title", "")
    if kind == "PublicEvent":
        return "public", f"open-sourced {repo}", ""
    return "", "", ""


def fetch_activity(session, user, now):
    events = _get(session, f"{API}/users/{user}/events/public", per_page=100) or []
    lines, last_key = [], None
    for event in events:
        kind, summary, detail = _describe(event)
        if not kind:
            continue
        repo = (event.get("repo") or {}).get("name", "")
        payload = event.get("payload", {}) or {}
        commits = int(summary.split(" ")[0]) if kind == "push" else 0
        key = (kind, repo)
        if kind == "push" and last_key == key and lines:
            # Fold a run of pushes to the same repo into one line that
            # carries the total commit count and keeps the newest message.
            previous = lines[-1]
            previous["count"] = previous.get("count", 1) + 1
            previous["commits"] = previous.get("commits", 0) + commits
            total = previous["commits"]
            previous["summary"] = f"{total} commit{'s' if total != 1 else ''} to {repo}"
            if not previous["detail"] and detail:
                previous["detail"] = detail[:80]
            continue
        last_key = key
        lines.append({
            "type": kind,
            "summary": summary,
            "detail": detail[:80],
            "repo": repo,
            "commits": commits,
            "count": 1,
            "at": event.get("created_at", ""),
            "ago": _age(event["created_at"], now) if event.get("created_at") else "",
            "sha": ((payload.get("head") or "") if kind == "push" else "")[:7] or (event.get("id") or "")[-7:],
        })
        if len(lines) >= MAX_ACTIVITY:
            break
    # Folding can leave a merged push slightly out of order; the panel reads
    # newest first, so sort by time before handing the list over.
    lines.sort(key=lambda line: line.get("at", ""), reverse=True)
    return lines


LAST_STATUS = {"status": "fresh", "sources": {}, "rate_remaining": ""}


def fetch(user, out, token=None, options=None):
    """Fetch every section independently and write the cache.

    options: exclude_repos (list), max_language_repos (int), cap_share (float).
    """
    options = options or {}
    exclude = set(options.get("exclude_repos") or [])
    out = Path(out)
    previous = {}
    if out.exists():
        try:
            previous = json.loads(out.read_text(encoding="utf-8"))
        except ValueError:
            previous = {}

    now = datetime.now(timezone.utc)
    session = _session(token)
    payload = dict(previous)
    payload["username"] = user
    payload["generated"] = date.today().isoformat()
    payload["generated_at"] = now.strftime("%Y-%m-%d %H:%M UTC")
    ok = 0

    try:
        payload["user"] = fetch_user(session, user)
        ok += 1
    except Exception as error:
        print(f"warning: user profile: {error}")

    repos = None
    try:
        repos = fetch_repos(session, user)
        originals = [r for r in repos if not r["fork"]]
        payload["totals"] = {
            "repos": len(repos),
            "original_repos": len(originals),
            "stars": sum(r["stars"] for r in repos),
            "forks": sum(r["forks"] for r in repos),
            "followers": payload.get("user", {}).get("followers", previous.get("totals", {}).get("followers", 0)),
            "following": payload.get("user", {}).get("following", previous.get("totals", {}).get("following", 0)),
        }
        payload["top_repos"] = sorted(
            [r for r in originals if not r["archived"]],
            key=lambda r: (r["stars"], r["pushed_at"]),
            reverse=True,
        )[:6]
        ok += 1
    except Exception as error:
        print(f"warning: repositories: {error}")

    if repos is not None:
        try:
            payload["languages"] = fetch_languages(
                session, repos,
                max_repos=int(options.get("max_language_repos") or MAX_LANGUAGE_REPOS),
                cap_share=float(options.get("cap_share", 0.4)),
                exclude=exclude,
            )
            ok += 1
        except Exception as error:
            print(f"warning: languages: {error}")

    try:
        payload["activity"] = [e for e in fetch_activity(session, user, now) if e.get("repo") not in exclude]
        ok += 1
    except Exception as error:
        print(f"warning: activity: {error}")

    try:
        probe = session.get(f"{API}/rate_limit", timeout=15)
        LAST_STATUS["rate_remaining"] = str(probe.headers.get("X-RateLimit-Remaining", ""))
    except Exception:
        LAST_STATUS["rate_remaining"] = ""

    LAST_STATUS["status"] = "fresh" if ok == 4 else ("cached" if ok == 0 and previous else ("partial" if ok else "empty"))
    if ok == 0:
        if previous:
            print(f"keeping the existing {out.name}: nothing could be fetched")
            return previous
        payload.setdefault("totals", {"repos": 0, "original_repos": 0, "stars": 0, "forks": 0, "followers": 0, "following": 0})
        payload.setdefault("languages", [])
        payload.setdefault("activity", [])
        payload.setdefault("top_repos", [])

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    totals = payload.get("totals", {})
    print(
        f"{out}: {totals.get('repos', 0)} repos, {totals.get('stars', 0)} stars, "
        f"{totals.get('followers', 0)} followers, {len(payload.get('languages', []))} languages, "
        f"{len(payload.get('activity', []))} events"
    )
    return payload


def main():
    user = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GH_USERNAME")
    if not user:
        print("usage: fetch_github.py <username> [out.json]")
        return 2
    out = sys.argv[2] if len(sys.argv) > 2 else "data/github.json"
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    fetch(user, out, token, {"exclude_repos": [f"{user}/{user}"]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
