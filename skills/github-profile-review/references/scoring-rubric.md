# Scoring rubric for GitHub profile READMEs

Eight dimensions, 100 points. Start each dimension at its maximum and
deduct per finding; a dimension never goes below zero. Caps stop one
repeated mistake (25 badges without alt) from wiping out a dimension that
also has other problems worth naming. `scripts/check_readme.py` applies the
mechanical rows automatically and marks the rest for the reviewer.

The rules cited as "constraints" come from
`references/github-readme-constraints.md`. That file
wins if the two ever disagree.

## a. Renders correctly (20)

What GitHub shows is a sanitised subset of Markdown plus HTML. Anything
outside the subset disappears without an error, and every image goes through
the camo proxy, which only passes image content types.

| Finding | Points | Severity |
|:--|--:|:--|
| `<style>`, `<script>`, `<iframe>`, `<object>`, `<embed>`, `<form>`, `<video>`, `<audio>`, `<canvas>`, inline `<svg>` (constraints: all stripped) | -5 each | error |
| `style=`, `class=`, `id=`, `on*=` attributes (stripped; layout only via `align`, `width`, `height`, `valign`, `<table>`) | -1 each distinct tag/attr pair, cap -5 | warn |
| Image from a third-party stats/decoration service (list below) | -4 each, cap -12 | error (warn for icon and decoration services) |
| Image URL returns non-2xx/3xx (`--check-links`), or a relative image missing from the repo (`--fetch-images`) | -5 each, cap -15 | error |
| Image URL serves `text/html` (camo shows a broken icon) | -5 each | error |
| `http://` image (camo may refuse it) | -2 each, cap -4 | warn |
| `<img>` without `src` | -3 each | error |
| SVG containing `<script>` (never runs inside `<img>`) | -3 each | warn |
| SVG loading an external font, image or stylesheet (blocked inside `<img>`; renders in fallback font or blank) | -3 each, cap -6 | warn |
| SVG with `<foreignObject>` (renders blank) | -3 each | warn |
| Single SVG over 300 KB | -1 each | warn |
| Images total over 1.5 MB | -2 | warn |

Pass: only the surviving subset is used, every image resolves, nothing is
rendered by a shared host that can rate-limit.

## b. Self-contained (15)

An image committed to the repo cannot go down, cannot change under you, and
is cached by camo. An image rendered on request by another server can do all
three.

| Finding | Points | Severity |
|:--|--:|:--|
| Image rendered by a third-party service (stats card, typing header, counter, trophies, capsule header) | -5 each, cap -15 | error |
| Hotlinked image on a host the user does not control (not GitHub, not a known service) | -3 each, cap -9 | warn |
| Image on GitHub's upload CDN (`user-images.githubusercontent.com`, `github.com/user-attachments`) or another repo's raw URL: served by GitHub but not versioned here, cannot be regenerated | -1 each, cap -3 | info |
| Flat shields.io / badgen badges | 0 | info |

Badges are the accepted exception: they are tiny, cached, and a broken badge
is a small grey box, not a hole in the layout. They are still counted
elsewhere (content) when there are too many.

## c. Light and dark (10)

GitHub has both themes and the viewer picks. Constraints: a dark terminal
panel on a light page reads as an intentional window and is fine; for a true
light variant use `<picture>` with `prefers-color-scheme` sources and an
`<img>` fallback for clients that ignore `<picture>`.

| Finding | Points | Severity |
|:--|--:|:--|
| `<picture>` with dark and light sources and an `<img>` fallback | 10 | pass |
| `<picture>` without `<img>` fallback (feed readers, older mobile app show nothing) | -3 each | warn |
| `<picture>` offering only one scheme | -2 each | info |
| Legacy `#gh-dark-mode-only` / `#gh-light-mode-only` fragments (still works, but legacy) | -2 | info |
| No `<picture>`, panels with opaque backgrounds: preliminary 7, reviewer confirms both themes | 7 to 10 | needs human judgement |
| Text or icons that vanish in one theme (transparent background, hard-coded grey) | -3 per panel | human |
| Text only, badges only: Markdown adapts on its own | 10 | pass |

## d. Motion (10)

Constraints: every animation loops or freezes in a settled state; one typing
effect per page; honour `prefers-reduced-motion` in CSS-driven panels; SMIL
cannot be gated, so SMIL panels are gentle or play once; loops between 8
and 25 seconds.

| Finding | Points | Severity |
|:--|--:|:--|
| Two or more typing effects (typing-svg images, SVGs with `steps()` text reveals, files named typing/typewriter) | -3 | warn |
| CSS-animated SVG without a `prefers-reduced-motion` rule | -2 each, cap -4 | warn |
| SMIL-only animated SVG (cannot be gated; check it is gentle or short) | 0 | info |
| Animated GIF (heavy, cannot respect reduced motion) | -2 each, cap -4 | warn |
| Longest animation over 30 s | -1 each | info |
| Panel that stops mid-transition or never settles (reviewer, one full loop) | -3 per panel | human |
| No animated images at all | 10 | pass (nothing to break) |
| Animated images not inspected (`--fetch-images` not run) | preliminary 7 | needs human judgement |

## e. Content (20)

The first screen has one job: who, what, where. Everything else is
supporting evidence.

| Finding | Points | Severity |
|:--|--:|:--|
| GitHub's default template still present ("I'm currently working on ...", the "special repository" comment) | -8 | error |
| Visitor or profile-views counter (komarev, visitor-badge, hits, "Profile views" text) | -4 | error |
| 20 to 39 badges | -3 | warn |
| 40 or more badges | -6 | warn |
| No outbound link to a project or repository | -5 | warn |
| No contact route (mailto, LinkedIn, X, Mastodon, Bluesky, email in text, a contact heading) | -3 | warn |
| Dead link (`--check-links`, 404/410/5xx/timeout; 401/403/429/999 are "unverifiable", not dead) | -2 each, cap -6 | warn |
| Under 60 words and no images besides badges | -5 | warn |
| Who/what/where not visible in the first screen (reviewer) | -5 | human |
| Projects listed without a sentence on what each does (reviewer) | -2 each, cap -6 | human |
| Empty file or not text | dimension 0, all dimensions 0 | error |

## f. Accessibility (10)

Constraints: every `<img>` gets an `alt` that states what the image says,
not "banner"; keep tables to two columns because they do not shrink on
phones.

| Finding | Points | Severity |
|:--|--:|:--|
| Image without alt (or empty alt) | -1 each, cap -5 | warn (badges aggregated into one warning) |
| Generic alt: banner, image, logo, header, stats, badge | -1 each, cap -3 | info |
| More than one H1 | -1 | info |
| Skipped heading levels (H1 straight to H3) | -1 | info |
| Long page (over 40 lines) with no headings | -1 | info |
| Table with 3+ columns outside `<details>` | -1 each, cap -3 | warn |
| Table with 3+ columns inside `<details>` (collapsed by default) | 0 | info |
| SVG root without `role="img"` / `aria-label` (alt on `<img>` still applies) | 0 | info |

## g. Freshness (8)

Numbers and graphs go stale the day after they are committed unless
something regenerates them. Constraints: the contribution calendar and the
REST API are reachable from GitHub Actions with the built-in token, so a
daily workflow is free.

| Finding | Points | Severity |
|:--|--:|:--|
| Workflow with `on: schedule:` present | 8 | pass |
| Workflow present but push-only | -2 | info |
| Dynamic content (stats, graphs, snakes, streaks) and no workflow | -4 | warn |
| Static text profile and no workflow | -2 | info (fine as long as it stays true) |
| Newest year mentioned is more than one year old | -2 | warn |
| Last commit over 365 days ago (username mode) | -2 | warn |
| Last commit over 180 days ago | -1 | info |
| Workflows not inspectable (pasted text, no repo access) | preliminary 6 | partial |

## h. Coherence (7)

One palette, one metaphor, nothing competing for attention. Mostly a human
call; the script flags the usual causes.

| Finding | Points | Severity |
|:--|--:|:--|
| Cards from three or more different services (three palettes, three fonts) | -2 | warn |
| More than 12 images besides badges | -1 | warn |
| More than 30 emoji | -1 | info |
| More than 12 headings | -1 | info |
| capsule-render plus typing-svg plus trophies (the template look) | 0 | info |
| Panels that do not share a palette or metaphor (reviewer) | -2 to -4 | human |
| Sections that repeat the same information (reviewer) | -1 each | human |

## Known third-party services and why each is a risk

Every one of these renders an image on request on a host the user does not
control. The risks repeat, so they are abbreviated: **RL** rate limits on
shared hosts (the public instance is one Vercel or Heroku app for everyone,
and it returns a broken image or a "rate limited" card at peak hours);
**DT** downtime and abandoned deployments (Heroku free tier shut down in
2022 and many `herokuapp.com` cards are dead); **TR** tracking (every
profile view is a request to their server with the viewer's IP); **ST**
cannot be styled to match the rest of the page beyond the themes they offer.

| Service | Match | Risks | Committed replacement |
|:--|:--|:--|:--|
| github-readme-stats | `github-readme-stats`, `/api/top-langs`, `/api/pin?` | RL DT TR ST | info card and language bars rendered from the REST API by a workflow (`render_info.py`) |
| streak-stats | `streak-stats`, `github-readme-streak-stats` | RL DT TR | streak computed from the public contribution calendar and baked into the card |
| readme-typing-svg | `readme-typing-svg` | DT TR ST | a committed typing SVG (`render_typing.py`); SMIL, no server |
| capsule-render | `capsule-render` | DT TR ST | a header panel in the page's own palette |
| komarev / visitor counters | `komarev.com`, `visitor-badge`, `hits.seeyoufarm`, `hits.sh`, `count.getloli`, `profile-counter` | TR, vanity | remove; nothing to replace |
| github-profile-trophy | `github-profile-trophy` | RL DT ST | remove; trophies say nothing a visitor cannot see on the profile itself |
| activity-graph | `activity-graph` | RL DT TR | contribution calendar / snake rendered daily by a workflow (`render_snake.py`) |
| wakatime cards | `wakatime.com`, `api=wakatime` | RL DT TR, needs an external account | a committed bar chart from the WakaTime export, if the numbers matter at all |
| spotify now-playing | `spotify-github-profile`, `novatorem`, `spotify-recently-played` | DT TR, personal data | remove |
| skillicons.dev | `skillicons.dev` | DT ST | shields.io badges (cached) or a committed icon row |
| hosted lowlighter/metrics | `metrics.lecoq.io` | RL DT | run the metrics action in your own workflow and commit its SVG |
| other hosted cards | summary-cards, ghchart, pufler, widgetbox, leetcard, quotes, jokes, holopin, contrib.rocks, star-history | RL DT TR ST | usually remove; commit an SVG if the data is worth showing |
| shields.io / badgen | `img.shields.io`, `badgen.net` | DT (mild; cached by camo) | keep, fewer than 20, with alt text |

## Common fixes

### Light and dark variant of a panel

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/info-card-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="./assets/info-card-light.svg">
  <img src="./assets/info-card-dark.svg" width="860" alt="Info card listing role, stack, location and contact">
</picture>
```

The `<img>` inside is not optional: it is what feed readers and older mobile
clients show.

### Replace a stats card with a committed SVG

Before:

```html
<img src="https://github-readme-stats.vercel.app/api?username=octocat&show_icons=true" />
```

After (file generated by a script in the repo and refreshed by a workflow):

```html
<img src="./assets/info-card.svg" width="490" alt="Info card: 42 public repos, Python and TypeScript, Berlin" />
```

Workflow that regenerates it daily with the built-in token (constraints:
`permissions: contents: write` is enough, 1000 requests an hour):

```yaml
name: Update profile art
on:
  schedule:
    - cron: "17 6 * * *"
  workflow_dispatch: {}
permissions:
  contents: write
jobs:
  render:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: python scripts/fetch_contributions.py && python scripts/render_snake_svg.py
      - uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "chore: refresh profile art [skip ci]"
          file_pattern: "assets/*.svg data/*.json"
```

The `github-profile-designer` skill ships the render scripts; its SKILL.md
covers the panel types.

### Remove a visitor counter

Delete the line. There is no replacement; the number is not information for
a visitor.

```diff
-<img src="https://komarev.com/ghpvc/?username=octocat&color=green" />
```

### Alt text that says something

```diff
-<img src="./assets/snake.svg" width="860" />
+<img src="./assets/snake.svg" width="860" alt="Contribution graph for the last year, with a snake eating its way across it" />
```

For badges the label is enough: `alt="Python"`.

### Honour reduced motion inside a CSS-animated SVG

Inside the SVG's own `<style>` (the README cannot carry CSS, the image can):

```css
@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; transition: none !important; }
  .reveal { opacity: 1; }          /* final frame, fully visible */
}
```

SMIL (`<animate>`) cannot be gated this way; keep those panels gentle or
play them once with `fill="freeze"`.

### Two typewriters to one

Keep the header typing effect, turn the second one into static text or a
heading in the terminal style: `### \`user@github ~ $ cat about.txt\``.

### Three-column table to two

```markdown
| Project | What it is |
| :-- | :-- |
| [CalcuLab](https://www.calculab.bio/) | Molecular biology calculators for the bench. Python, React. 2026. |
```

Fold the third column (date, stack, issuer) into the sentence. If a wide
table must stay, put it inside `<details>` so phones only see it on request.

### Stripped HTML

```diff
-<h1 align="center" style="color:#58a6ff" class="title">Hi</h1>
+<h1 align="center">Hi</h1>
```

`align` survives, `style` and `class` do not. Colour, font and motion belong
inside a committed SVG.

### Badge wall to a short list

Keep the badges you would defend in an interview, group them by role
(languages, frameworks, tooling) with `<br/>` between rows, give each an
`alt`, and stop before 20.
