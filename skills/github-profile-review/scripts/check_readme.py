#!/usr/bin/env python3
"""
check_readme.py - audit a GitHub profile README using only the Python
standard library.

  python3 check_readme.py README.md                        # local file
  python3 check_readme.py octocat                          # downloads octocat/octocat/README.md
  python3 check_readme.py https://github.com/octocat --check-links --fetch-images

Prints a human summary followed by a JSON report (use --format json or
--format text for one of them). Exit code is 0 unless the README itself
cannot be read or downloaded, in which case it is 2.

Scoring follows references/scoring-rubric.md of the github-profile-review
skill. Dimensions the script cannot judge are marked "needs human judgement"
and carry a preliminary number that the reviewer confirms by looking at the
rendered profile.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

USER_AGENT = "github-profile-review/1.0 (+stdlib urllib)"

# ---------------------------------------------------------------------------
# What GitHub strips. Source of truth:
# skills/github-profile-designer/references/github-readme-constraints.md
# ---------------------------------------------------------------------------
STRIPPED_TAGS = {
    "style", "script", "iframe", "object", "embed", "form", "input", "textarea",
    "button", "select", "video", "audio", "canvas", "svg", "link", "meta",
    "base", "noscript",
}
STRIPPED_ATTRS = {"style", "class", "id"}  # plus every on* handler

# Third-party services. kind: stats | counter | typing | decor | icons | badge | other
SERVICES = [
    {"key": "komarev", "kind": "counter", "label": "komarev profile-views counter",
     "patterns": [r"komarev\.com"]},
    {"key": "visitor-counter", "kind": "counter", "label": "visitor / hit counter",
     "patterns": [r"visitor-badge", r"visitorbadge\.io", r"hits\.seeyoufarm", r"hits\.sh/",
                  r"count\.getloli", r"profile-counter", r"visitcount", r"page-views",
                  r"profile-views", r"hits\.dwyl", r"visitors\.", r"badges\.pufler\.dev/visits"]},
    {"key": "wakatime", "kind": "stats", "label": "WakaTime coding-time card",
     "patterns": [r"wakatime\.com", r"api=wakatime", r"/api/wakatime"]},
    {"key": "github-readme-stats", "kind": "stats", "label": "github-readme-stats card",
     "patterns": [r"github-readme-stats", r"readme-stats[\w.-]*\.(vercel\.app|herokuapp\.com)",
                  r"/api/top-langs", r"/api/pin\?", r"/api/gist\?"]},
    {"key": "streak-stats", "kind": "stats", "label": "streak-stats card",
     "patterns": [r"streak-stats", r"github-readme-streak"]},
    {"key": "github-profile-trophy", "kind": "stats", "label": "github-profile-trophy",
     "patterns": [r"github-profile-trophy"]},
    {"key": "activity-graph", "kind": "stats", "label": "activity-graph card",
     "patterns": [r"activity-graph"]},
    {"key": "readme-typing-svg", "kind": "typing", "label": "readme-typing-svg",
     "patterns": [r"readme-typing-svg", r"typing-svg"]},
    {"key": "capsule-render", "kind": "decor", "label": "capsule-render header/footer",
     "patterns": [r"capsule-render"]},
    {"key": "spotify", "kind": "stats", "label": "Spotify now-playing card",
     "patterns": [r"spotify-github-profile", r"spotify-recently-played", r"novatorem",
                  r"spotify-now-playing", r"now-playing", r"spotify"]},
    {"key": "skillicons", "kind": "icons", "label": "skillicons.dev",
     "patterns": [r"skillicons\.dev"]},
    {"key": "metrics", "kind": "stats", "label": "hosted lowlighter/metrics",
     "patterns": [r"metrics\.lecoq\.io"]},
    {"key": "other-stats", "kind": "stats", "label": "other hosted stats card",
     "patterns": [r"github-profile-summary-cards", r"ghchart\.rshah", r"badges\.pufler",
                  r"github-widgetbox", r"stats\.jaysahu", r"readme-quotes", r"quotes-github-readme",
                  r"readme-jokes", r"leetcard", r"leetcode-stats", r"codersrank", r"holopin\.me",
                  r"contrib\.rocks", r"star-history\.com", r"github-readme-medium",
                  r"github-readme-youtube", r"github-readme-blog-post", r"gh-card\.dev",
                  r"lanyard", r"codestats\.net", r"github-readme-remote-code", r"dev-metrics",
                  r"github-stats-", r"readme-stats"]},
    {"key": "shields", "kind": "badge", "label": "shields.io / badgen badge",
     "patterns": [r"img\.shields\.io", r"shields\.io", r"badgen\.net", r"badge\.fury\.io",
                  r"forthebadge\.com"]},
]
for _s in SERVICES:
    _s["rx"] = [re.compile(p, re.I) for p in _s["patterns"]]

GITHUB_CDN = re.compile(
    r"(user-images\.githubusercontent\.com|github\.com/user-attachments|"
    r"avatars\.githubusercontent\.com|github\.com/[^/]+/[^/]+/(raw|blob)/)", re.I)
RAW_GH = re.compile(r"raw\.githubusercontent\.com/([^/]+)/([^/]+)/", re.I)
SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*:", re.I)
GENERIC_ALTS = {"", "banner", "image", "img", "logo", "header", "picture", "photo", "gif",
                "svg", "png", "badge", "icon", "stats", "profile", "readme"}
SOCIAL_HOSTS = ("linkedin.com", "twitter.com", "x.com", "mastodon", "bsky.app", "t.me",
                "discord", "instagram.com", "facebook.com", "youtube.com", "twitch.tv",
                "dev.to", "medium.com", "hashnode", "stackoverflow.com", "reddit.com",
                "threads.net", "telegram")
WHO_WORDS = re.compile(
    r"\b(i['’]?m|i am|hi|hello|hey|welcome|developer|engineer|student|researcher|"
    r"scientist|designer|founder|maintainer|building|working on|based in|phd|undergrad|"
    r"freelance|about me|who am i)\b", re.I)
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿\U0001F1E6-\U0001F1FF]")
TEMPLATE_MARKERS = [
    re.compile(r"is a\s+\S*\s*_special_\s*\S*\s+repository", re.I),
    re.compile(r"I['’]?m currently (working on|learning|looking to)\s*\.\.\.", re.I),
    re.compile(r"(Ask me about|How to reach me|Pronouns|Fun fact):?\s*\.\.\.", re.I),
    re.compile(r"lorem ipsum", re.I),
]


# ---------------------------------------------------------------------------
# HTTP helpers (urllib honours HTTPS_PROXY / SSL_CERT_FILE from the environment)
# ---------------------------------------------------------------------------
def _request(url, method="GET", timeout=10, headers=None, max_bytes=None):
    """Return dict(status, body, content_type, final_url, error). Never raises."""
    hdrs = {"User-Agent": USER_AGENT}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, method=method, headers=hdrs)
    out = {"status": None, "body": b"", "content_type": "", "final_url": url, "error": None}
    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            out["status"] = resp.status
            out["content_type"] = resp.headers.get("Content-Type", "") or ""
            out["final_url"] = resp.geturl()
            if method != "HEAD":
                out["body"] = resp.read(max_bytes) if max_bytes else resp.read()
    except urllib.error.HTTPError as e:
        out["status"] = e.code
        out["error"] = "HTTP %s" % e.code
        out["content_type"] = (e.headers.get("Content-Type", "") if e.headers else "") or ""
    except urllib.error.URLError as e:
        out["error"] = "URL error: %s" % getattr(e, "reason", e)
    except (TimeoutError, OSError, ValueError) as e:
        out["error"] = "%s: %s" % (type(e).__name__, e)
    except Exception as e:  # noqa: BLE001 - never crash on a network oddity
        out["error"] = "%s: %s" % (type(e).__name__, e)
    return out


def head_or_get(url, timeout):
    r = _request(url, "HEAD", timeout)
    if r["status"] in (403, 405, 501) or (r["status"] is None and r["error"]):
        r = _request(url, "GET", timeout, max_bytes=1024)
    return r


def gh_api_headers():
    h = {"Accept": "application/vnd.github+json"}
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
    if re.match(r"^(gh[pousr]_|github_pat_)[A-Za-z0-9_]+$", tok):
        h["Authorization"] = "Bearer " + tok
    return h


# ---------------------------------------------------------------------------
# Markdown pre-processing
# ---------------------------------------------------------------------------
FENCE_RX = re.compile(r"^([ \t]{0,3})(`{3,}|~{3,})[^\n]*\n(.*?)^\1\2[ \t]*$", re.M | re.S)
INLINE_CODE_RX = re.compile(r"(`+)([^`\n]|[^`\n][^`]*?[^`\n])\1")


def blank_fences(text):
    """Replace fenced code blocks with blank lines of the same count."""
    fences = []

    def repl(m):
        fences.append(m.group(0))
        return "\n" * m.group(0).count("\n")

    return FENCE_RX.sub(repl, text), len(fences)


def neutralise_inline_code(text, mode):
    """mode='escape': turn <> into entities so the HTML parser ignores code spans.
    mode='space': replace the span with spaces (same length, same lines)."""
    def repl(m):
        s = m.group(0)
        if mode == "space":
            return re.sub(r"[^\n]", " ", s)
        return s.replace("<", "&lt;").replace(">", "&gt;")

    return INLINE_CODE_RX.sub(repl, text)


# ---------------------------------------------------------------------------
# HTML parsing (GitHub-flavoured markdown allows an HTML subset)
# ---------------------------------------------------------------------------
class ReadmeParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.images, self.links, self.headings, self.tables = [], [], [], []
        self.pictures, self.stripped_tags, self.stripped_attrs = [], [], []
        self.comments, self.details_ranges, self.text_parts = [], [], []
        self._details_stack, self._tables, self._picture = [], [], None
        self._heading, self._heading_buf, self._link_depth, self._raw = None, [], 0, None
        self.tag_counts = {}

    def line(self):
        return self.getpos()[0]

    def handle_starttag(self, tag, attrs):
        a = {}
        for k, v in attrs:
            a[k.lower()] = v if v is not None else ""
        line = self.line()
        self.tag_counts[tag] = self.tag_counts.get(tag, 0) + 1
        if tag in STRIPPED_TAGS:
            self.stripped_tags.append({"tag": tag, "line": line})
            if tag in ("style", "script"):
                self._raw = tag
        for k in a:
            if k in STRIPPED_ATTRS or k.startswith("on"):
                self.stripped_attrs.append({"tag": tag, "attr": k, "line": line})
        if tag == "img":
            img = {"src": (a.get("src") or "").strip(), "alt": a.get("alt"),
                   "width": a.get("width"), "height": a.get("height"), "line": line,
                   "in_picture": self._picture is not None, "linked": self._link_depth > 0,
                   "source": "html"}
            self.images.append(img)
            self.text_parts.append(" [img: %s] " % (a.get("alt") or ""))
            if self._picture is not None:
                self._picture["fallback"] = True
        elif tag == "a":
            self._link_depth += 1
            self.links.append({"href": (a.get("href") or "").strip(), "line": line, "source": "html"})
        elif tag == "picture":
            self._picture = {"line": line, "sources": [], "fallback": False}
        elif tag == "source" and self._picture is not None:
            self._picture["sources"].append({"media": a.get("media", ""), "srcset": a.get("srcset", "")})
        elif tag == "table":
            self._tables.append({"line": line, "rows": 0, "max_cols": 0, "_cells": 0, "source": "html"})
        elif tag == "tr" and self._tables:
            t = self._tables[-1]
            t["rows"] += 1
            t["_cells"] = 0
        elif tag in ("td", "th") and self._tables:
            t = self._tables[-1]
            t["_cells"] += 1
            t["max_cols"] = max(t["max_cols"], t["_cells"])
        elif re.fullmatch(r"h[1-6]", tag):
            self._heading = (int(tag[1]), line)
            self._heading_buf = []
        elif tag == "details":
            self._details_stack.append(line)
        elif tag in ("br", "p", "div", "tr", "li"):
            self.text_parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("style", "script"):
            self._raw = None
        elif tag == "a":
            self._link_depth = max(0, self._link_depth - 1)
        elif tag == "picture" and self._picture is not None:
            self.pictures.append(self._picture)
            self._picture = None
        elif tag == "table" and self._tables:
            t = self._tables.pop()
            t.pop("_cells", None)
            t["in_details"] = bool(self._details_stack)
            self.tables.append(t)
        elif re.fullmatch(r"h[1-6]", tag) and self._heading:
            level, line = self._heading
            self.headings.append({"level": level, "text": "".join(self._heading_buf).strip(),
                                  "line": line, "source": "html"})
            self._heading = None
        elif tag == "details" and self._details_stack:
            self.details_ranges.append((self._details_stack.pop(), self.line()))

    def handle_data(self, data):
        if self._raw:
            return
        self.text_parts.append(data)
        if self._heading:
            self._heading_buf.append(data)

    def handle_comment(self, data):
        self.comments.append({"line": self.line(), "text": data.strip()[:200]})

    def close(self):
        try:
            super().close()
        except Exception:  # noqa: BLE001
            pass
        while self._tables:
            t = self._tables.pop()
            t.pop("_cells", None)
            t["in_details"] = False
            self.tables.append(t)
        if self._picture is not None:
            self.pictures.append(self._picture)
            self._picture = None
        while self._details_stack:
            self.details_ranges.append((self._details_stack.pop(), 10 ** 9))


def parse_html(text):
    p = ReadmeParser()
    try:
        p.feed(text)
    except Exception:  # noqa: BLE001 - html.parser is lenient, but be safe
        pass
    p.close()
    return p


# ---------------------------------------------------------------------------
# Markdown syntax extraction
# ---------------------------------------------------------------------------
MD_IMG_RX = re.compile(r"!\[([^\]]*)\]\(\s*<?([^\s)>]+)>?(?:\s+[\"'(][^)]*)?\s*\)")
MD_IMG_REF_RX = re.compile(r"!\[([^\]]*)\]\[([^\]]*)\]")
MD_LINK_RX = re.compile(r"(?<!!)\[([^\]]*)\]\(\s*<?([^\s)>]+)>?(?:\s+[\"'(][^)]*)?\s*\)")
MD_LINK_REF_RX = re.compile(r"(?<!!)\[([^\]]+)\]\[([^\]]*)\]")
MD_REFDEF_RX = re.compile(r"^[ ]{0,3}\[([^\]]+)\]:[ \t]*<?(\S+?)>?(?:[ \t]+.*)?$", re.M)
MD_AUTOLINK_RX = re.compile(r"<(https?://[^>\s]+)>")
MD_HEADING_RX = re.compile(r"^[ ]{0,3}(#{1,6})[ \t]+(.*?)[ \t]*#*[ \t]*$", re.M)
TABLE_SEP_RX = re.compile(r"^\s*\|?\s*:?-{1,}:?\s*(\|\s*:?-{1,}:?\s*)*\|?\s*$")


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def extract_markdown(body, body_nocode):
    refdefs = {m.group(1).strip().lower(): m.group(2) for m in MD_REFDEF_RX.finditer(body_nocode)}
    images, links, headings, tables = [], [], [], []
    for m in MD_IMG_RX.finditer(body_nocode):
        images.append({"src": m.group(2).strip(), "alt": m.group(1), "width": None, "height": None,
                       "line": line_of(body_nocode, m.start()), "in_picture": False,
                       "linked": False, "source": "md"})
    for m in MD_IMG_REF_RX.finditer(body_nocode):
        key = (m.group(2) or m.group(1)).strip().lower()
        images.append({"src": refdefs.get(key, ""), "alt": m.group(1), "width": None, "height": None,
                       "line": line_of(body_nocode, m.start()), "in_picture": False,
                       "linked": False, "source": "md"})
    # remove images so nested [![badge](img)](link) resolves as a link
    stripped = MD_IMG_RX.sub(lambda m: "IMG" + " " * max(0, len(m.group(0)) - 3), body_nocode)
    stripped = MD_IMG_REF_RX.sub(lambda m: "IMG" + " " * max(0, len(m.group(0)) - 3), stripped)
    for m in MD_LINK_RX.finditer(stripped):
        links.append({"href": m.group(2).strip(), "line": line_of(stripped, m.start()),
                      "source": "md", "text": m.group(1)})
    for m in MD_LINK_REF_RX.finditer(stripped):
        key = (m.group(2) or m.group(1)).strip().lower()
        if key in refdefs:
            links.append({"href": refdefs[key], "line": line_of(stripped, m.start()),
                          "source": "md", "text": m.group(1)})
    for m in MD_AUTOLINK_RX.finditer(stripped):
        links.append({"href": m.group(1), "line": line_of(stripped, m.start()), "source": "md",
                      "text": m.group(1)})
    for m in MD_HEADING_RX.finditer(body):
        headings.append({"level": len(m.group(1)), "text": m.group(2).replace("`", "").strip(),
                         "line": line_of(body, m.start()), "source": "md"})
    lines = body.split("\n")
    for i, ln in enumerate(lines):
        if i == 0 or not lines[i - 1].strip():
            continue
        s = ln.strip()
        prev = lines[i - 1].strip()
        if re.fullmatch(r"=+", s) and not prev.startswith(("<", "|", "-", "*", "#", ">")):
            headings.append({"level": 1, "text": prev, "line": i, "source": "md-setext"})
        elif re.fullmatch(r"-{3,}", s) and "|" in prev and TABLE_SEP_RX.match(s):
            pass
    # markdown tables
    i = 0
    while i < len(lines) - 1:
        hdr, sep = lines[i], lines[i + 1]
        if "|" in hdr and "|" in sep and TABLE_SEP_RX.match(sep) and hdr.strip():
            cells = [c for c in sep.strip().strip("|").split("|")]
            cols = len(cells)
            rows = 0
            j = i + 2
            while j < len(lines) and "|" in lines[j] and lines[j].strip():
                rows += 1
                j += 1
            tables.append({"line": i + 1, "rows": rows, "max_cols": cols, "source": "md"})
            i = j
        else:
            i += 1
    headings.sort(key=lambda h: h["line"])
    return images, links, headings, tables


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------
def classify_service(url):
    u = url or ""
    for s in SERVICES:
        for rx in s["rx"]:
            if rx.search(u):
                return s
    return None


def classify_image(img, username):
    src = img.get("src") or ""
    svc = classify_service(src)
    img["service"] = svc["key"] if svc else None
    img["service_kind"] = svc["kind"] if svc else None
    if not src:
        img["kind"] = "missing-src"
    elif svc and svc["kind"] == "badge":
        img["kind"] = "badge"
    elif svc:
        img["kind"] = "service"
    elif not SCHEME.match(src) and not src.startswith("//"):
        img["kind"] = "relative"
    else:
        m = RAW_GH.search(src)
        if m and username and m.group(1).lower() == username.lower() and m.group(2).lower() == username.lower():
            img["kind"] = "same-repo-raw"
        elif m:
            img["kind"] = "github-raw"
        elif GITHUB_CDN.search(src):
            img["kind"] = "github-cdn"
        else:
            img["kind"] = "hotlinked"
    ext = re.sub(r"[?#].*$", "", src).lower().rsplit(".", 1)
    img["ext"] = ext[1] if len(ext) == 2 and len(ext[1]) <= 5 else ""
    img["insecure"] = src.lower().startswith("http://")
    img["dark_mode_fragment"] = bool(re.search(r"#gh-(dark|light)-mode-only", src))
    alt = img.get("alt")
    img["alt_present"] = alt is not None and alt.strip() != ""
    img["alt_generic"] = img["alt_present"] and alt.strip().lower() in GENERIC_ALTS
    img["typing_like"] = bool(re.search(r"typing|typewriter|typed", src, re.I)) or img["service"] == "readme-typing-svg"
    return img


def flatten_text(parts):
    t = "".join(parts)
    t = MD_IMG_RX.sub(lambda m: " [img: %s] " % m.group(1), t)
    t = MD_LINK_RX.sub(lambda m: m.group(1), t)
    t = re.sub(r"[#*_>|`]+", " ", t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n\s*\n+", "\n", t)
    return t.strip()


# ---------------------------------------------------------------------------
# SVG / image inspection
# ---------------------------------------------------------------------------
def inspect_svg(data):
    txt = data.decode("utf-8", "replace")
    low = txt.lower()
    info = {"is_svg": "<svg" in low}
    if not info["is_svg"]:
        return info
    info["has_script"] = "<script" in low
    info["foreign_object"] = "<foreignobject" in low
    ext = []
    for m in re.finditer(r"<(image|use|feImage)\b[^>]*?(?:xlink:)?href\s*=\s*[\"']([^\"']+)", txt, re.I):
        if re.match(r"https?:|//", m.group(2).strip(), re.I):
            ext.append("%s -> %s" % (m.group(1), m.group(2)[:80]))
    for m in re.finditer(r"@import\s+(?:url\()?[\"']?([^\"')\s;]+)", txt, re.I):
        ext.append("@import -> %s" % m.group(1)[:80])
    for m in re.finditer(r"@font-face[^}]*url\(\s*[\"']?([^\"')]+)", txt, re.I | re.S):
        if re.match(r"https?:|//", m.group(1).strip(), re.I):
            ext.append("@font-face -> %s" % m.group(1)[:80])
    info["external_refs"] = ext
    info["smil_animations"] = len(re.findall(r"<(animate|animateTransform|animateMotion|set)\b", txt))
    info["css_keyframes"] = len(re.findall(r"@keyframes", txt))
    info["css_animation_props"] = len(re.findall(r"\banimation(?:-name)?\s*:", txt))
    info["animated"] = bool(info["smil_animations"] or info["css_keyframes"] or info["css_animation_props"])
    info["reduced_motion"] = "prefers-reduced-motion" in low
    durs = []
    for m in re.finditer(r"\bdur\s*=\s*[\"']([\d.]+)(ms|s)[\"']", txt):
        durs.append(float(m.group(1)) / (1000 if m.group(2) == "ms" else 1))
    for m in re.finditer(r"\banimation(?:-duration)?\s*:\s*([^;}]*)", txt):
        for d in re.finditer(r"([\d.]+)(ms|s)\b", m.group(1)):
            durs.append(float(d.group(1)) / (1000 if d.group(2) == "ms" else 1))
    info["max_duration_s"] = round(max(durs), 2) if durs else 0.0
    info["indefinite"] = ("indefinite" in low) or ("infinite" in low)
    # A typewriter is text revealed through a clipPath whose width is animated
    # and that loops forever; a play-once typed line or a blinking cursor is not.
    clip_typing = bool(re.search(r"<clippath[^>]*>\s*<rect[^>]*>\s*<animate[^>]*attributename=\"width\"[^>]*repeatcount=\"indefinite\"", low))
    info["typing_like"] = clip_typing or bool(re.search(r"class=\"[^\"]*(typing|typewriter)", low))
    info["role_img"] = 'role="img"' in low or "role='img'" in low
    info["aria_label"] = bool(re.search(r"aria-label\s*=", txt, re.I))
    info["has_viewbox"] = "viewbox" in low
    return info


def fetch_image_bytes(img, target, timeout):
    """Return (data|None, where, error)."""
    src = img["src"]
    clean = re.sub(r"[?#].*$", "", src)
    if img["kind"] == "relative":
        rel = clean[2:] if clean.startswith("./") else clean.lstrip("/")
        rel = urllib.parse.unquote(rel)
        if target["mode"] == "local":
            p = (Path(target["path"]).parent / rel)
            try:
                return p.read_bytes(), str(p), None
            except OSError as e:
                return None, str(p), "not on disk (%s)" % e.strerror
        url = "https://raw.githubusercontent.com/%s/%s/%s/%s" % (
            target["username"], target["username"], target["branch"], urllib.parse.quote(rel))
    elif img["kind"] in ("same-repo-raw", "github-raw", "github-cdn", "hotlinked"):
        url = src
    else:
        return None, src, "skipped (third-party service or badge)"
    r = _request(url, "GET", timeout, max_bytes=8 * 1024 * 1024)
    if r["error"] or (r["status"] and r["status"] >= 400):
        return None, url, r["error"] or ("HTTP %s" % r["status"])
    return r["body"], url, None


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
class Dim:
    def __init__(self, key, name, maximum):
        self.key, self.name, self.max = key, name, maximum
        self.score = float(maximum)
        self.status = "auto"
        self.notes = []
        self.fix = None

    def deduct(self, pts, note, fix=None):
        self.score = max(0.0, self.score - pts)
        self.notes.append("-%g: %s" % (pts, note))
        if fix and not self.fix:
            self.fix = fix

    def note(self, text):
        self.notes.append(text)

    def as_dict(self):
        return {"key": self.key, "name": self.name, "max": self.max,
                "score": int(round(self.score)), "status": self.status,
                "notes": self.notes, "most_important_fix": self.fix}


class Findings:
    def __init__(self):
        self.items = []

    def add(self, severity, dim, code, message, line=None, url=None):
        f = {"severity": severity, "dimension": dim, "code": code, "message": message}
        if line:
            f["line"] = line
        if url:
            f["url"] = url
        self.items.append(f)


def capped(counter, per, cap):
    """Deduction for the n-th occurrence so that the total never exceeds cap."""
    used = counter["used"]
    d = min(per, max(0, cap - used))
    counter["used"] += d
    return d


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------
def analyse(text, target, args):
    F = Findings()
    now = datetime.now(timezone.utc)
    dims = {
        "a": Dim("a", "Renders correctly", 20), "b": Dim("b", "Self-contained", 15),
        "c": Dim("c", "Light and dark", 10), "d": Dim("d", "Motion", 10),
        "e": Dim("e", "Content", 20), "f": Dim("f", "Accessibility", 10),
        "g": Dim("g", "Freshness", 8), "h": Dim("h", "Coherence", 7),
    }
    username = target.get("username")

    body, fence_count = blank_fences(text)
    body_nocode = neutralise_inline_code(body, "space")
    html_text = neutralise_inline_code(body, "escape")
    p = parse_html(html_text)
    md_images, md_links, md_headings, md_tables = extract_markdown(body, body_nocode)

    images = [classify_image(i, username) for i in p.images + md_images]
    images.sort(key=lambda i: i["line"])
    links = p.links + md_links
    links = [l for l in links if l.get("href")]
    headings = sorted(p.headings + md_headings, key=lambda h: h["line"])
    for t in md_tables:
        t["in_details"] = any(a <= t["line"] <= b for a, b in p.details_ranges)
    tables = sorted(p.tables + md_tables, key=lambda t: t["line"])
    flat = flatten_text(p.text_parts)
    first_screen = flat[:700]
    lines_total = text.count("\n") + 1
    words = len(re.findall(r"\w+", flat))
    undecodable = text.count("\ufffd") / max(1, len(text))

    # ------------------------------------------------------------ (a) renders
    a = dims["a"]
    for st in p.stripped_tags:
        a.deduct(5, "<%s> at line %d is stripped by GitHub" % (st["tag"], st["line"]),
                 "remove <%s>; put colour, fonts and motion inside a committed SVG instead" % st["tag"])
        F.add("error", "a", "stripped-tag",
              "<%s> is removed by GitHub's sanitiser; whatever it was meant to do does not happen" % st["tag"],
              st["line"])
    attr_cap = {"used": 0}
    seen_attr = set()
    for sa in p.stripped_attrs:
        key = (sa["tag"], sa["attr"])
        if key in seen_attr:
            continue
        seen_attr.add(key)
        d = capped(attr_cap, 1, 5)
        if d:
            a.deduct(d, "%s= on <%s> (line %d) is stripped" % (sa["attr"], sa["tag"], sa["line"]),
                     "drop %s= attributes; only align, width, height, valign, src, href, alt survive" % sa["attr"])
        F.add("warn", "a", "stripped-attr",
              "%s= on <%s> is stripped; layout must come from align=, width= and <table>" % (sa["attr"], sa["tag"]),
              sa["line"])
    svc_cap = {"used": 0}
    services_seen = {}
    for img in images:
        if img["kind"] == "service":
            services_seen.setdefault(img["service"], []).append(img["src"])
            sev = "warn" if img["service_kind"] in ("icons", "decor") else "error"
            d = capped(svc_cap, 4, 12)
            if d:
                a.deduct(d, "%s image (line %d) depends on a third-party server" % (img["service"], img["line"]),
                         "replace the %s image with an SVG generated by a workflow and committed to the repo" % img["service"])
            F.add(sev, "a", "third-party-service",
                  "%s: shared hosts rate-limit and go down, then the profile shows a broken image" % img["service"],
                  img["line"], img["src"])
        if img["kind"] == "missing-src":
            a.deduct(3, "image without src at line %d" % img["line"])
            F.add("error", "a", "missing-src", "<img> without a src renders as a broken icon", img["line"])
        if img["insecure"]:
            a.deduct(2, "http:// image at line %d" % img["line"])
            F.add("warn", "a", "insecure-src", "http:// image; camo may refuse it, use https://", img["line"], img["src"])
    if p.tag_counts.get("svg"):
        F.add("error", "a", "inline-svg", "inline <svg> is stripped; reference it as an <img> file instead")

    # ------------------------------------------------------ (b) self-contained
    b = dims["b"]
    kinds = {}
    for img in images:
        kinds[img["kind"]] = kinds.get(img["kind"], 0) + 1
    svc_b = {"used": 0}
    hot_b = {"used": 0}
    cdn_b = {"used": 0}
    for img in images:
        if img["kind"] == "service":
            d = capped(svc_b, 5, 15)
            if d:
                b.deduct(d, "%s is rendered by someone else's server (line %d)" % (img["service"], img["line"]),
                         "generate the same panel locally and commit it under assets/")
        elif img["kind"] == "hotlinked":
            d = capped(hot_b, 3, 9)
            if d:
                b.deduct(d, "hotlinked image at line %d" % img["line"], "copy the image into the repo and use a relative path")
            F.add("warn", "b", "hotlinked-image", "image lives on a host you do not control", img["line"], img["src"])
        elif img["kind"] in ("github-cdn", "github-raw"):
            d = capped(cdn_b, 1, 3)
            if d:
                b.deduct(d, "image on GitHub's CDN but not in this repo (line %d)" % img["line"])
            F.add("info", "b", "cdn-image", "served by GitHub but not versioned in this repo; cannot be regenerated", img["line"], img["src"])
    badges = [i for i in images if i["kind"] == "badge"]
    non_badge = [i for i in images if i["kind"] not in ("badge", "missing-src")]
    if not images:
        b.note("no images: nothing to hotlink")
    if badges:
        F.add("info", "b", "badges", "%d shields.io-style badges; flat badges are the accepted exception, they are cached by camo and cheap" % len(badges))
    committed = [i for i in images if i["kind"] in ("relative", "same-repo-raw")]
    b.note("%d committed, %d third-party, %d badges" % (len(committed), kinds.get("service", 0), len(badges)))

    # --------------------------------------------------------- (c) light+dark
    c = dims["c"]
    pics = p.pictures
    if pics:
        for pic in pics:
            media = " ".join(s.get("media", "") for s in pic["sources"]).lower()
            has_dark = "dark" in media and "prefers-color-scheme" in media
            has_light = "light" in media and "prefers-color-scheme" in media
            if not pic["fallback"]:
                c.deduct(3, "<picture> at line %d has no <img> fallback" % pic["line"],
                         "add <img src=... alt=...> inside the <picture> for clients that ignore <source>")
                F.add("warn", "c", "picture-no-fallback", "<picture> without <img> fallback shows nothing in some clients", pic["line"])
            if not (has_dark and has_light):
                c.deduct(2, "<picture> at line %d does not offer both schemes" % pic["line"])
                F.add("info", "c", "picture-one-scheme", "<picture> lists only one colour scheme", pic["line"])
        c.note("%d <picture> block(s) with prefers-color-scheme sources" % len(pics))
        c.status = "auto"
    elif any(i["dark_mode_fragment"] for i in images):
        c.deduct(2, "uses legacy #gh-dark-mode-only fragments", "switch to <picture> with prefers-color-scheme sources")
        F.add("info", "c", "legacy-mode-fragment", "#gh-dark-mode-only still works but is legacy; prefer <picture>")
        c.status = "partial"
    elif non_badge:
        c.score = 7
        c.status = "needs human judgement"
        c.note("no <picture>: a dark terminal panel on a light page is acceptable; open the profile in both themes and check every panel's text contrast")
    else:
        c.note("only text and badges: markdown adapts to both themes on its own")

    # -------------------------------------------------------------- (d) motion
    d_ = dims["d"]
    typing_count = sum(1 for i in images if i["typing_like"])
    gifs = [i for i in images if i["ext"] == "gif"]
    gif_cap = {"used": 0}
    for g in gifs:
        dd = capped(gif_cap, 2, 4)
        if dd:
            d_.deduct(dd, "GIF at line %d cannot honour prefers-reduced-motion" % g["line"],
                      "replace GIFs with SVG panels whose CSS freezes under prefers-reduced-motion")
        F.add("warn", "d", "gif", "animated GIFs are heavy and cannot respect reduced-motion", g["line"], g["src"])

    # ------------------------------------------------------------- (e) content
    e = dims["e"]
    template_hits = []
    for rx in TEMPLATE_MARKERS:
        for src in (text,):
            m = rx.search(src)
            if m:
                template_hits.append(m.group(0)[:60])
    if template_hits:
        e.deduct(8, "unfilled GitHub template text: %s" % template_hits[0],
                 "delete the template scaffold and write three real sentences: who, what, where")
        F.add("error", "e", "template-left", "the default profile template is still there: %s" % "; ".join(template_hits))
    counter_imgs = [i for i in images if i["service_kind"] == "counter"]
    counter_text = re.search(r"\b(profile views|visitor count|visitors|page views)\b", flat, re.I)
    if counter_imgs or counter_text:
        e.deduct(4, "visitor / profile-views counter", "remove the counter: visitors do not care about the number and it is a tracker")
        F.add("error", "e", "visitor-counter",
              "visitor counter found (%s): reads as vanity, tracks every visitor, and it is a third-party image"
              % (counter_imgs[0]["src"] if counter_imgs else counter_text.group(0)),
              counter_imgs[0]["line"] if counter_imgs else None)
    if len(badges) >= 40:
        e.deduct(6, "%d badges: a badge wall" % len(badges), "keep at most ten badges that say something a visitor cannot guess")
        F.add("warn", "e", "badge-wall", "%d badges; nobody reads past the tenth" % len(badges))
    elif len(badges) >= 20:
        e.deduct(3, "%d badges" % len(badges), "cut the badge list to the tools you would defend in an interview")
        F.add("warn", "e", "badge-wall", "%d badges; the constraint is fewer than 20" % len(badges))
    hrefs = [l["href"] for l in links]

    def is_contact(h):
        hl = h.lower()
        return hl.startswith("mailto:") or any(s in hl for s in SOCIAL_HOSTS)

    project_links, repo_links, contact_links = [], [], []
    for h in hrefs:
        hl = h.lower()
        if is_contact(h):
            contact_links.append(h)
        elif classify_service(h) and classify_service(h)["kind"] == "badge":
            continue
        elif hl.startswith(("http://", "https://")):
            project_links.append(h)
            m = re.search(r"github\.com/([^/]+)/([^/#?]+)", hl)
            if m and m.group(2) not in ("", "sponsors") and not (username and m.group(1) == username.lower() and m.group(2) == username.lower()):
                repo_links.append(h)
    email_in_text = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", flat)
    has_contact_heading = any(re.search(r"contact|reach|connect|find me", h["text"], re.I) for h in headings)
    if not project_links:
        e.deduct(5, "no links to projects or repositories", "link two or three real repositories with one line on what each does")
        F.add("warn", "e", "no-project-links", "no outbound link to a project or repository")
    if not (contact_links or email_in_text or has_contact_heading):
        e.deduct(3, "no contact route", "add one contact line: email or LinkedIn is enough")
        F.add("warn", "e", "no-contact", "no email, LinkedIn or other contact link")
    who = WHO_WORDS.search(first_screen)
    if not who:
        F.add("info", "e", "first-screen", "could not find a who/what statement in the first screen; check by hand that name, role and place are visible without scrolling")
    if words < 60 and not non_badge:
        e.deduct(5, "very short (%d words, no images)" % words, "write three sentences: who you are, what you build, where to find it")
        F.add("warn", "e", "thin", "profile has %d words and no images besides badges" % words)
    e.status = "partial"
    e.note("script checks counters, badges, links and template leftovers; judge the writing yourself")

    # -------------------------------------------------------- (f) accessibility
    f = dims["f"]
    alt_cap = {"used": 0}
    gen_cap = {"used": 0}
    badges_no_alt = []
    for img in images:
        if img["kind"] == "missing-src":
            continue
        if not img["alt_present"]:
            dd = capped(alt_cap, 1, 5)
            if dd:
                f.deduct(dd, "image without alt at line %d" % img["line"], "give every <img> an alt that says what the image says")
            if img["kind"] == "badge":
                badges_no_alt.append(img)
                continue
            F.add("warn", "f", "no-alt", "image has no alt text", img["line"], img["src"])
        elif img["alt_generic"]:
            dd = capped(gen_cap, 1, 3)
            if dd:
                f.deduct(dd, "generic alt '%s' at line %d" % (img["alt"], img["line"]))
            F.add("info", "f", "generic-alt", "alt '%s' says nothing; describe the content" % img["alt"], img["line"], img["src"])
    if badges_no_alt:
        F.add("warn", "f", "no-alt-badges", "%d of %d badges have no alt text; alt=\"Python\" is enough" % (len(badges_no_alt), len(badges)), badges_no_alt[0]["line"])
    h1s = [h for h in headings if h["level"] == 1]
    if len(h1s) > 1:
        f.deduct(1, "%d H1 headings" % len(h1s))
        F.add("info", "f", "multiple-h1", "%d level-1 headings; one page, one H1 (or none)" % len(h1s))
    prev = 0
    skipped = False
    for h in headings:
        if prev and h["level"] > prev + 1:
            skipped = True
        prev = h["level"]
    if skipped:
        f.deduct(1, "heading levels skip (e.g. H1 to H3)")
        F.add("info", "f", "heading-skip", "heading levels are skipped; screen readers use them as an outline")
    if not headings and lines_total > 40:
        f.deduct(1, "no headings in %d lines" % lines_total)
        F.add("info", "f", "no-headings", "long page without headings")
    tbl_cap = {"used": 0}
    for t in tables:
        if t["max_cols"] > 2:
            if t.get("in_details"):
                F.add("info", "f", "wide-table-collapsed", "%d-column table inside <details>; fine while collapsed, still scrolls on phones" % t["max_cols"], t["line"])
            else:
                dd = capped(tbl_cap, 1, 3)
                if dd:
                    f.deduct(dd, "%d-column table at line %d" % (t["max_cols"], t["line"]), "keep tables to two columns; they do not shrink on phones")
                F.add("warn", "f", "wide-table", "%d-column table does not shrink to phone width" % t["max_cols"], t["line"])

    # ------------------------------------------------------------ (g) freshness
    g = dims["g"]
    workflows = target.get("workflows")  # list of {name, scheduled}
    years = [int(y) for y in re.findall(r"\b(20[0-4][0-9])\b", flat)]
    dynamic = bool(kinds.get("service")) or any(re.search(r"snake|contrib|graph|stats|streak", i["src"], re.I) for i in images)
    if workflows is None:
        g.status = "partial"
        g.note("could not inspect .github/workflows (no repo access); ask the user or run in username mode")
        g.score = 6
    elif any(w["scheduled"] for w in workflows):
        g.note("scheduled workflow: %s" % ", ".join(w["name"] for w in workflows if w["scheduled"]))
    elif workflows:
        g.deduct(2, "workflow exists but has no schedule", "add `on: schedule: - cron: \"17 6 * * *\"` so the data refreshes daily")
        F.add("info", "g", "workflow-no-schedule", "workflow only runs on push; nothing refreshes while you are away")
    elif dynamic:
        g.deduct(4, "numbers or graphs shown, nothing regenerates them", "add a daily GitHub Actions workflow that regenerates the panels and commits them")
        F.add("warn", "g", "no-automation", "profile shows data that goes stale (stats, graph) but has no workflow")
    else:
        g.deduct(2, "no automation; fine for a static page")
        F.add("info", "g", "static", "no workflow; acceptable for a text-only profile, add one if you show numbers")
    if years and max(years) < now.year - 1:
        g.deduct(2, "newest year mentioned is %d" % max(years), "update or remove dated lines")
        F.add("warn", "g", "stale-year", "newest year in the text is %d" % max(years))
    last_commit = target.get("last_commit")
    if last_commit:
        try:
            age = (now - datetime.fromisoformat(last_commit.replace("Z", "+00:00"))).days
            g.note("last commit %d days ago" % age)
            if age > 365:
                g.deduct(2, "no commit in %d days" % age)
                F.add("warn", "g", "stale-repo", "last commit %d days ago" % age)
            elif age > 180:
                g.deduct(1, "no commit in %d days" % age)
                F.add("info", "g", "aging-repo", "last commit %d days ago" % age)
        except ValueError:
            pass

    # ------------------------------------------------------------ (h) coherence
    h_ = dims["h"]
    distinct_services = sorted(services_seen)
    if len(distinct_services) >= 3:
        h_.deduct(2, "%d different stats services, each with its own palette" % len(distinct_services),
                  "pick one visual system; the designer skill renders every panel from one theme file")
        F.add("warn", "h", "mixed-services", "cards from %s do not share a palette" % ", ".join(distinct_services))
    emoji_count = len(EMOJI.findall(flat))
    if emoji_count > 30:
        h_.deduct(1, "%d emoji" % emoji_count)
        F.add("info", "h", "emoji-heavy", "%d emoji; they read as noise past a handful" % emoji_count)
    if len(non_badge) > 12:
        h_.deduct(1, "%d images besides badges" % len(non_badge))
        F.add("warn", "h", "image-clutter", "%d non-badge images; a page needs three or four panels, not a gallery" % len(non_badge))
    if len(headings) > 12:
        h_.deduct(1, "%d headings" % len(headings))
        F.add("info", "h", "many-headings", "%d headings; fold secondary sections into <details>" % len(headings))
    if {"capsule-render", "readme-typing-svg", "github-profile-trophy"} & set(distinct_services):
        F.add("info", "h", "kitchen-sink", "capsule-render / typing-svg / trophies are the template look every third profile has")
    h_.status = "needs human judgement"
    h_.note("check by eye: one palette, one metaphor, nothing that competes for attention")

    # ---------------------------------------------------- optional: link check
    link_report = None
    if args.check_links:
        link_report = []
        urls = []
        for img in images:
            if img["src"].lower().startswith(("http://", "https://")):
                urls.append(("image", img["src"], img["line"]))
        for l in links:
            if l["href"].lower().startswith(("http://", "https://")):
                urls.append(("link", l["href"], l["line"]))
        seen = set()
        img_cap = {"used": 0}
        dead_cap = {"used": 0}
        for kind, url, line in urls[: args.max_links]:
            if url in seen:
                continue
            seen.add(url)
            r = head_or_get(url, args.timeout)
            ok = r["status"] is not None and 200 <= r["status"] < 400
            blocked = r["status"] in (401, 403, 429, 999)
            ctype = r["content_type"].split(";")[0].strip().lower()
            entry = {"kind": kind, "url": url, "line": line, "status": r["status"], "ok": ok,
                     "blocked": blocked, "content_type": ctype, "error": r["error"]}
            link_report.append(entry)
            if blocked:
                F.add("info", "a" if kind == "image" else "e", "link-unverifiable",
                      "host answers %s to automated requests (LinkedIn does this); open it in a browser to confirm" % r["status"], line, url)
                continue
            if kind == "image":
                if not ok:
                    dd = capped(img_cap, 5, 15)
                    if dd:
                        a.deduct(dd, "image %s returns %s" % (url[:60], r["status"] or r["error"]), "fix or remove the broken image")
                    F.add("error", "a", "broken-image", "image URL returns %s" % (r["status"] or r["error"]), line, url)
                elif ctype.startswith("text/html"):
                    a.deduct(5, "image URL serves HTML (line %d)" % line)
                    F.add("error", "a", "image-not-image", "URL used as an image serves %s; camo shows a broken icon" % ctype, line, url)
            elif not ok:
                dd = capped(dead_cap, 2, 6)
                if dd:
                    e.deduct(dd, "dead link %s (%s)" % (url[:60], r["status"] or r["error"]), "fix or drop dead links")
                F.add("warn", "e", "dead-link", "link returns %s" % (r["status"] or r["error"]), line, url)
        if a.status == "auto":
            a.note("all %d absolute URLs checked" % len(seen))
    elif any(i["src"].lower().startswith(("http://", "https://")) for i in images):
        a.status = "partial"
        a.note("absolute image URLs not verified; run with --check-links")

    # -------------------------------------------------- optional: fetch images
    image_files = None
    if args.fetch_images:
        image_files = []
        total_bytes = 0
        anim_cap = {"used": 0}
        ext_cap = {"used": 0}
        miss_cap = {"used": 0}
        animated_count = 0
        fetched_typing = 0
        for img in images:
            if img["kind"] in ("badge", "service", "missing-src"):
                continue
            data, where, err = fetch_image_bytes(img, target, args.timeout)
            entry = {"src": img["src"], "line": img["line"], "where": where, "bytes": len(data) if data else 0, "error": err}
            if data is None:
                if err and not err.startswith("skipped"):
                    dd = capped(miss_cap, 5, 15)
                    if dd:
                        a.deduct(dd, "image %s cannot be fetched: %s" % (img["src"], err), "commit the missing file or fix the path")
                    F.add("error", "a", "image-missing", "image cannot be fetched (%s)" % err, img["line"], img["src"])
                image_files.append(entry)
                continue
            total_bytes += len(data)
            info = inspect_svg(data) if (img["ext"] == "svg" or data[:300].lstrip().lower().startswith((b"<svg", b"<?xml"))) else {"is_svg": False}
            entry.update(info)
            image_files.append(entry)
            if len(data) > 300 * 1024 and info.get("is_svg"):
                F.add("warn", "a", "large-svg", "SVG is %d KB; keep panels under about 300 KB" % (len(data) // 1024), img["line"], img["src"])
                a.deduct(1, "SVG over 300 KB (line %d)" % img["line"])
            if not info.get("is_svg"):
                continue
            if info["has_script"]:
                a.deduct(3, "SVG with <script> (line %d)" % img["line"], "scripts never run inside <img>; animate with SMIL or CSS in the SVG")
                F.add("warn", "a", "svg-script", "SVG contains <script>; it will not run through <img>", img["line"], img["src"])
            if info["foreign_object"]:
                a.deduct(3, "SVG with <foreignObject> (line %d)" % img["line"])
                F.add("warn", "a", "svg-foreignobject", "<foreignObject> renders blank through <img>", img["line"], img["src"])
            for ref in info["external_refs"]:
                dd = capped(ext_cap, 3, 6)
                if dd:
                    a.deduct(dd, "SVG loads an external resource (%s)" % ref, "inline the font/image or use a system font stack")
                F.add("warn", "a", "svg-external-ref", "external resource is blocked inside <img>: %s" % ref, img["line"], img["src"])
            if info["animated"]:
                animated_count += 1
                if info["typing_like"]:
                    fetched_typing += 1
                if info["css_keyframes"] and not info["reduced_motion"]:
                    dd = capped(anim_cap, 2, 4)
                    if dd:
                        d_.deduct(dd, "CSS-animated SVG without prefers-reduced-motion (line %d)" % img["line"],
                                  "add @media (prefers-reduced-motion: reduce) { * { animation: none } } inside the SVG, frozen at the final frame")
                    F.add("warn", "d", "no-reduced-motion", "CSS animation without a prefers-reduced-motion rule", img["line"], img["src"])
                elif not info["css_keyframes"] and not info["reduced_motion"]:
                    F.add("info", "d", "smil-only", "SMIL animation cannot be gated by reduced-motion; keep it gentle or play-once (max dur %.1fs)" % info["max_duration_s"], img["line"], img["src"])
                if info["max_duration_s"] > 30:
                    d_.deduct(1, "animation of %.0fs (line %d)" % (info["max_duration_s"], img["line"]))
                    F.add("info", "d", "long-loop", "longest animation is %.0fs; loops of 8 to 25 s read best" % info["max_duration_s"], img["line"], img["src"])
            if not info["role_img"] and not info["aria_label"]:
                F.add("info", "f", "svg-no-role", "SVG root lacks role=\"img\" / aria-label (alt on <img> still applies)", img["line"], img["src"])
        if total_bytes > 1.5 * 1024 * 1024:
            a.deduct(2, "images total %.1f MB" % (total_bytes / 1048576))
            F.add("warn", "a", "heavy-page", "images total %.1f MB; keep under about 1.5 MB for phones" % (total_bytes / 1048576))
        typing_count = max(typing_count, fetched_typing + sum(1 for i in images if i["service"] == "readme-typing-svg"))
        if animated_count == 0 and not gifs:
            d_.note("no animated images found")
        d_.note("%d animated SVG(s) inspected" % animated_count)
    else:
        if non_badge:
            d_.status = "needs human judgement"
            d_.score = min(d_.score, 7)
            d_.note("SVG contents not inspected; run with --fetch-images")
        else:
            d_.note("no images to animate")

    if typing_count > 1:
        d_.deduct(3, "%d typing effects" % typing_count, "keep one typewriter; two read as noise")
        F.add("warn", "d", "two-typewriters", "%d typing effects on one page" % typing_count)

    # ---------------------------------------------- nothing to review at all
    empty = None
    if undecodable > 0.02:
        empty = "file is not UTF-8 text (%.0f%% undecodable bytes); this is not a README" % (undecodable * 100)
    elif words < 20 and not images:
        empty = "the README is empty (%d words, no images); there is no profile to score" % words
    if empty:
        F.items = [fi for fi in F.items if fi["dimension"] not in ("e", "f", "g", "h")]
        F.add("error", "e", "nothing-to-review", empty)
        for d in dims.values():
            d.score, d.status, d.notes, d.fix = 0.0, "auto", ["0: " + empty], None
        dims["e"].fix = "write the profile first; the github-profile-designer skill builds one from a short questionnaire"

    # ------------------------------------------------------------- assemble
    dim_list = [dims[k].as_dict() for k in "abcdefgh"]
    prelim = sum(d["score"] for d in dim_list)
    auto_max = sum(d["max"] for d in dim_list if d["status"] == "auto")
    sev = {"error": 0, "warn": 0, "info": 0}
    for fi in F.items:
        sev[fi["severity"]] = sev.get(fi["severity"], 0) + 1
    report = {
        "target": {k: v for k, v in target.items() if k not in ("workflows",)},
        "workflows": target.get("workflows"),
        "stats": {
            "lines": lines_total, "words": words, "fenced_code_blocks": fence_count,
            "images": len(images), "images_committed": len(committed),
            "images_third_party": kinds.get("service", 0), "images_hotlinked": kinds.get("hotlinked", 0),
            "badges": len(badges), "links": len(links), "project_links": len(project_links),
            "repo_links": len(repo_links), "contact_links": len(contact_links),
            "headings": len(headings), "tables": len(tables),
            "max_table_columns": max([t["max_cols"] for t in tables] or [0]),
            "pictures": len(pics), "details_blocks": len(p.details_ranges),
            "html_comments": len(p.comments), "emoji": emoji_count, "typing_effects": typing_count,
        },
        "services": services_seen,
        "stripped_html": {"tags": p.stripped_tags, "attributes": p.stripped_attrs},
        "headings": headings, "tables": tables, "pictures": pics,
        "images": [{k: v for k, v in i.items() if k in ("src", "alt", "alt_present", "width", "line", "kind", "service", "ext", "in_picture", "linked")} for i in images],
        "first_screen_excerpt": first_screen,
        "links_checked": link_report, "image_files": image_files,
        "findings": F.items, "finding_counts": sev,
        "dimensions": dim_list,
        "preliminary_score": prelim, "total_max": 100, "automatable_max": auto_max,
        "empty": empty,
        "note": "preliminary_score is what the script could measure; dimensions with status 'partial' or 'needs human judgement' must be confirmed by looking at the rendered profile in both themes",
    }
    return report


# ---------------------------------------------------------------------------
# Target resolution
# ---------------------------------------------------------------------------
def resolve_target(arg, args):
    p = Path(arg)
    if p.exists() and p.is_file():
        t = {"mode": "local", "path": str(p.resolve()), "username": args.user, "branch": args.branch}
        wf_dir = p.resolve().parent / ".github" / "workflows"
        if wf_dir.is_dir():
            t["workflows"] = []
            for f in sorted(wf_dir.iterdir()):
                if f.suffix in (".yml", ".yaml"):
                    try:
                        content = f.read_text("utf-8", "replace")
                    except OSError:
                        content = ""
                    t["workflows"].append({"name": f.name, "scheduled": bool(re.search(r"^\s*schedule\s*:", content, re.M))})
        else:
            t["workflows"] = [] if (p.resolve().parent / ".git").exists() else None
        return t, None
    m = re.match(r"^(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9-]+)/?(?:[A-Za-z0-9-]+/?)?(?:[?#].*)?$", arg.strip())
    username = m.group(1) if m else arg.strip().lstrip("@").rstrip("/")
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}", username):
        return None, "'%s' is neither an existing file nor a valid GitHub username" % arg
    url = "https://raw.githubusercontent.com/%s/%s/%s/README.md" % (username, username, args.branch)
    r = _request(url, "GET", args.timeout, max_bytes=4 * 1024 * 1024)
    if r["error"] or not r["body"]:
        hint = ""
        if r["status"] == 404:
            hint = " (no public repo named %s/%s with a README.md on %s?)" % (username, username, args.branch)
        return None, "could not download %s: %s%s" % (url, r["error"] or "empty response", hint)
    t = {"mode": "remote", "username": username, "url": url, "branch": args.branch,
         "text": r["body"].decode("utf-8", "replace")}
    if not args.no_api:
        api = "https://api.github.com/repos/%s/%s" % (username, username)
        wf = _request(api + "/contents/.github/workflows", "GET", args.timeout, gh_api_headers(), 512 * 1024)
        if wf["status"] == 200:
            t["workflows"] = []
            try:
                for item in json.loads(wf["body"].decode("utf-8", "replace")):
                    name = item.get("name", "")
                    if not name.endswith((".yml", ".yaml")):
                        continue
                    raw = _request(item.get("download_url") or "", "GET", args.timeout, max_bytes=256 * 1024)
                    content = raw["body"].decode("utf-8", "replace") if raw["body"] else ""
                    t["workflows"].append({"name": name, "scheduled": bool(re.search(r"^\s*schedule\s*:", content, re.M))})
            except (ValueError, AttributeError, TypeError):
                t["workflows"] = None
        elif wf["status"] == 404:
            t["workflows"] = []
        else:
            t["workflows"] = None
            t["api_note"] = "workflow listing failed: %s" % (wf["error"] or wf["status"])
        cm = _request(api + "/commits?per_page=1", "GET", args.timeout, gh_api_headers(), 512 * 1024)
        if cm["status"] == 200:
            try:
                t["last_commit"] = json.loads(cm["body"].decode("utf-8", "replace"))[0]["commit"]["committer"]["date"]
            except (ValueError, KeyError, IndexError, TypeError):
                pass
    else:
        t["workflows"] = None
    return t, None


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def human_summary(rep):
    out = []
    t = rep["target"]
    where = t.get("path") or t.get("url")
    out.append("GitHub profile README check")
    out.append("Target: %s (%s, %d lines)" % (where, t["mode"], rep["stats"]["lines"]))
    out.append("Preliminary score: %d/100   (auto-checked dimensions cover %d points; the rest need a human look)"
               % (rep["preliminary_score"], rep["automatable_max"]))
    if rep.get("empty"):
        out.append("Verdict: " + rep["empty"] + ". Do not review it; build one with the github-profile-designer skill.")
    out.append("")
    out.append("  %-3s %-20s %7s  %s" % ("dim", "dimension", "score", "status / most important fix"))
    for d in rep["dimensions"]:
        fix = d["most_important_fix"] or ""
        out.append("  %-3s %-20s %3d/%-3d  %s%s" % (d["key"], d["name"], d["score"], d["max"], d["status"],
                                                   (": " + fix) if fix else ""))
    s = rep["stats"]
    out.append("")
    out.append("Inventory: %d images (%d committed, %d third-party, %d hotlinked, %d badges), %d links (%d to projects, %d contact), %d headings, %d tables (max %d cols), %d <picture>, %d typing effect(s)"
               % (s["images"], s["images_committed"], s["images_third_party"], s["images_hotlinked"], s["badges"],
                  s["links"], s["project_links"], s["contact_links"], s["headings"], s["tables"],
                  s["max_table_columns"], s["pictures"], s["typing_effects"]))
    if rep["services"]:
        out.append("Third-party services: " + ", ".join("%s (%d)" % (k, len(v)) for k, v in rep["services"].items()))
    if rep.get("workflows") is not None:
        wf = rep["workflows"]
        out.append("Workflows: " + (", ".join("%s%s" % (w["name"], " [scheduled]" if w["scheduled"] else "") for w in wf) if wf else "none"))
    c = rep["finding_counts"]
    out.append("")
    out.append("Findings: %d errors, %d warnings, %d info" % (c.get("error", 0), c.get("warn", 0), c.get("info", 0)))
    order = {"error": 0, "warn": 1, "info": 2}
    for fi in sorted(rep["findings"], key=lambda x: (order.get(x["severity"], 3), x.get("line") or 0)):
        loc = ("line %d" % fi["line"]) if fi.get("line") else ""
        url = (" <%s>" % fi["url"][:70]) if fi.get("url") else ""
        out.append("  %-5s %s %-9s %s%s" % (fi["severity"].upper(), fi["dimension"], loc, fi["message"], url))
    if rep.get("first_screen_excerpt"):
        out.append("")
        out.append("First screen (text and alt, first 300 chars): " + rep["first_screen_excerpt"][:300].replace("\n", " / "))
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Audit a GitHub profile README (stdlib only).")
    ap.add_argument("target", help="path to README.md, a GitHub username, or a github.com profile URL")
    ap.add_argument("--check-links", action="store_true", help="HEAD every absolute image and link URL")
    ap.add_argument("--fetch-images", action="store_true", help="download committed images and inspect SVG internals")
    ap.add_argument("--branch", default="HEAD", help="branch or ref for raw.githubusercontent (default HEAD)")
    ap.add_argument("--user", default=None, help="GitHub username when auditing a local file (improves same-repo detection)")
    ap.add_argument("--timeout", type=float, default=10.0, help="seconds per network request")
    ap.add_argument("--max-links", type=int, default=100, help="upper bound on URLs checked with --check-links")
    ap.add_argument("--no-api", action="store_true", help="skip api.github.com calls (workflow listing, last commit)")
    ap.add_argument("--format", choices=("both", "json", "text"), default="both")
    ap.add_argument("--out", default=None, help="also write the JSON report to this file")
    args = ap.parse_args(argv)

    target, err = resolve_target(args.target, args)
    if err:
        print("error: " + err, file=sys.stderr)
        return 2
    if target["mode"] == "local":
        try:
            text = Path(target["path"]).read_text("utf-8", "replace")
        except OSError as e:
            print("error: cannot read %s: %s" % (target["path"], e), file=sys.stderr)
            return 2
    else:
        text = target.pop("text")

    try:
        report = analyse(text, target, args)
    except Exception as e:  # noqa: BLE001 - report the failure instead of a traceback
        report = {"target": target, "error": "analysis failed: %s: %s" % (type(e).__name__, e),
                  "findings": [{"severity": "error", "dimension": "-", "code": "internal", "message": str(e)}],
                  "finding_counts": {"error": 1}, "dimensions": [], "preliminary_score": 0,
                  "automatable_max": 0, "stats": {"lines": text.count("\n") + 1}, "services": {}}
    if args.out:
        try:
            Path(args.out).write_text(json.dumps(report, indent=2, ensure_ascii=False), "utf-8")
        except OSError as e:
            print("warning: could not write %s: %s" % (args.out, e), file=sys.stderr)
    if args.format in ("both", "text"):
        if "error" in report:
            print("GitHub profile README check\n" + report["error"])
        else:
            print(human_summary(report))
    if args.format == "both":
        print("\n---- JSON ----")
    if args.format in ("both", "json"):
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
