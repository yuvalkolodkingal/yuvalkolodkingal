---
name: github-profile-review
description: Audit and score an existing GitHub profile README (the README.md in the repository named after the user) and return a 0-100 score with the concrete fixes, in a fixed report format. Use whenever someone asks to review, rate, grade, audit, critique, roast, check, improve or fix their GitHub profile or profile README, asks why their profile looks broken, empty, dated or ugly, asks whether their profile is good enough or what recruiters see, pastes a github.com/<user> URL or the text of a profile README, or mentions broken images, stats cards, badges, visitor counters, dark mode, typing effects or animations on their profile. Fire even when the word "review" is absent ("look at my GitHub", "thoughts on my README?"). Companion of github-profile-designer, which rebuilds a profile.
---

# GitHub profile README review

Produce one thing: the report at the end of this file, filled in with a
score out of 100 and fixes the user can apply today. Everything before that
is how to get the numbers right.

The ground truth for what GitHub renders is
`../github-profile-designer/references/github-readme-constraints.md`
(installed next to this skill). Read it before your first review; the rubric
in `references/scoring-rubric.md` quotes the rules that carry points. Do not
invent GitHub behaviour: if a claim is not in the constraints file, verify it
or leave it out.

## 1. Get the README

Only `<user>/<user>/README.md` on the default branch shows on the profile.
Getting the file from anywhere else reviews the wrong thing.

- In a checkout: read `README.md` and confirm with `git remote -v` that the
  repository is named after the user. A profile README in `docs/` or in a
  differently named repo is invisible, which is itself the first finding.
- From a username or URL: `curl -fsSL https://raw.githubusercontent.com/<user>/<user>/HEAD/README.md`.
  With the GitHub CLI: `gh api repos/<user>/<user>/readme --jq .content | base64 -d`.
- Pasted text: save it to a file and say in the report that assets and
  workflows were not inspected.
- 404 means there is no profile README. Do not score an absence; say so and
  point to the designer skill (section 7).

Also fetch what the README depends on, because most breakage lives there:
the files under `assets/` it references, `.github/workflows/`, and the
rendered page at `https://github.com/<user>` in both themes if you can open
a browser. The sanitiser and camo proxy act at render time, so the source
alone never shows a stripped tag or a broken image.

## 2. Run the checker

```sh
python3 scripts/check_readme.py README.md --fetch-images            # local checkout
python3 scripts/check_readme.py <user> --check-links --fetch-images  # by username
python3 scripts/check_readme.py https://github.com/<user> --format json --out report.json
```

Stdlib only, no install. It prints a human summary and a JSON report with
`findings` (severity error/warn/info, dimension, line, URL), an inventory,
and `dimensions` with a preliminary score each. `--fetch-images` reads the
committed SVGs and reports `<script>`, external fonts or images, animation
type, `prefers-reduced-motion` and loop length. `--check-links` HEADs every
absolute URL. `--user <name>` in local mode improves same-repo detection.

Run it every time: it catches `<style>` blocks, `class=` attributes, visitor
counters and missing alt text that eyes skip over. Then override it where it
says `needs human judgement` or `partial`: it cannot see contrast, clutter or
whether the writing says anything. The preliminary score is a floor for
the mechanical checks, not the verdict.

## 3. Look at the rendered page

Do these by hand, or from the sources when no browser is available:

- First screen at desktop width and at 400 px: can a stranger tell who this
  is, what they do and where, without scrolling? Tables wider than two
  columns overflow on phones; images with `width` shrink, tables do not.
- Switch between light and dark themes. A dark terminal panel on a light page
  is an intentional window and passes; grey text on a transparent background
  that vanishes in one theme fails.
- Watch one full loop of every animation. It must loop cleanly or settle;
  a panel frozen mid-transition, or two typewriters racing, fails.
- Click the project links. A profile that links to nothing real is a
  business card with no phone number.

## 4. Score the eight dimensions (100 points)

Start each dimension at full points and deduct per finding; the exact
amounts are in `references/scoring-rubric.md`. The reasons matter more than
the numbers, so here is what each dimension protects.

| | Dimension | Pts | Pass | Fail |
|:--|:--|--:|:--|:--|
| a | Renders correctly | 20 | Only the HTML subset GitHub keeps; every image resolves; no image depends on a rate-limited third-party server | `<style>`, `<script>`, `<iframe>`, `style=`/`class=` (all stripped silently); broken images; readme-stats, streak-stats, typing-svg, capsule-render, trophies and friends |
| b | Self-contained | 15 | Images committed in the repo, referenced by relative path; flat shields.io badges are the accepted exception | Panels rendered by someone else's server; hotlinked images from hosts the user does not control |
| c | Light and dark | 10 | Readable in both themes: `<picture>` with `prefers-color-scheme` sources plus an `<img>` fallback, or panels with their own opaque background | Text that disappears in one theme; `<picture>` without fallback; legacy `#gh-dark-mode-only` fragments (works, minus points for fragility) |
| d | Motion | 10 | Every animation loops or freezes settled; loops of 8 to 25 s; CSS animations gated by `prefers-reduced-motion`; at most one typing effect | Two or more typewriters; GIFs (cannot honour reduced motion); panels that stop mid-transition; loops over 30 s |
| e | Content | 20 | Who, what and where in the first screen; two or three real projects with links; one contact route; no visitor counter; fewer than 20 badges | Unfilled template lines; counters (vanity plus a tracker); badge walls; no links; no way to reach the person |
| f | Accessibility | 10 | Alt text that states what the image says; one H1 or none, no skipped levels; tables of at most two columns | Missing or generic alt ("banner"); 3+ column tables outside `<details>`; heading soup |
| g | Freshness | 8 | A scheduled GitHub Actions workflow regenerates anything that is a number or a graph; no stale years | Stats that nothing refreshes; "currently learning X" from three years ago; a repo untouched for a year |
| h | Coherence | 7 | One palette, one metaphor (terminal, dashboard, plain text), three or four panels that belong together | Cards from three services in three palettes; emoji as bullet points everywhere; a gallery of twelve images |

Why third-party stats cards cost points in two dimensions: they are the most
common reason a profile shows a broken-image icon (shared hosts rate-limit
and go down), and they cannot be versioned or styled. The constraints file
says to generate the same thing locally and commit it; the designer skill
does exactly that, so the fix is cheap.

Why the badge threshold is 20: past ten badges nobody reads them, past
twenty the page is a logo wall and the first screen says nothing.

Why counters fail outright: the number means nothing to a visitor, the image
is served by a third party that logs every view, and it is one more request
that can break.

## 5. Write the report

Always use this template, in this order, with these headings. The score is
the sum of the eight dimensions after your own adjustments, not the script's
preliminary number.

```markdown
# Profile review: <user>

**Score: NN/100.** <One line verdict: what a stranger sees and the single biggest lever.>

| Dimension | Score | Most important fix |
|:--|--:|:--|
| a. Renders correctly | n/20 | <one fix or "nothing"> |
| b. Self-contained | n/15 | ... |
| c. Light and dark | n/10 | ... |
| d. Motion | n/10 | ... |
| e. Content | n/20 | ... |
| f. Accessibility | n/10 | ... |
| g. Freshness | n/8 | ... |
| h. Coherence | n/7 | ... |

## Top 3 fixes
1. <Fix, why it matters in one sentence, then the exact snippet or diff to paste.>
2. ...
3. ...

## What already works
- <Two to five specific things to keep. Name the file or line.>

## Next step
<Either "apply the three fixes above" with the order, or "rebuild with github-profile-designer" when warranted (section 7), with the install command.>
```

Rules for the fixes: quote the offending line, show the replacement, and
prefer a diff or a snippet over a description. "Add alt text" is not a fix;
`alt="Contribution graph for the last year"` on line 7 is.

## 6. Worked example

README of a fictional user: a `<style>` block, a komarev counter, a
readme-stats card, a streak card, two typing-svg headers, 25 shields
badges without alt text, a four-column stats table, the default template's
"I'm currently working on ..." lines still present, no project links, no
contact, last date 2021.

- a. Renders: `<style>` -5; six third-party images, capped at -12; `style=`
  and `class=` on the H1, -2. 20 - 19 = 1, rounded to 0 with the broken
  iframe. **0/20**
- b. Self-contained: five service-rendered images at -5 each, capped. **0/15**
- c. Light and dark: no `<picture>`, cards have opaque backgrounds, text
  readable in both themes on inspection. **8/10**
- d. Motion: two typewriters -3; nothing settles, the counter reloads. **4/10**
- e. Content: template scaffold -8, counter -4, badge wall -3, no project
  links -5. **0/20**
- f. Accessibility: 25 images without alt (capped -5), four-column table
  -1, H1 to H4 skip -1. **3/10**
- g. Freshness: nothing regenerates the numbers -4, newest year 2021 -2. **2/8**
- h. Coherence: six services, six palettes -2; template look. **3/7**

Total **20/100**. Verdict: "Nothing on the page is yours: every panel is
rendered elsewhere and the words are the template's. Rebuild." Next step
points to the designer skill.

For contrast, a profile with four committed animated SVG panels, 18 badges
with alt text, real project links, contact, a daily workflow and one typing
effect scores 97 preliminary; after confirming both themes by eye it lands
at 97 to 100, and the report's top fixes become polish (the two three-column
tables inside `<details>`, a `<picture>` variant for light mode).

## 7. When to send them to the designer skill

Recommend a rebuild instead of patches when any of these hold: score under
50; dimension a or b at 0 (every visual is third-party); the page is the
unfilled template; the user asks for a new look. Patching a page whose
every image belongs to another server is slower than regenerating it.

The companion skill `github-profile-designer` builds terminal-themed,
self-contained animated SVG panels from the user's real data with a
scheduled workflow, which clears a, b, d and g in one pass. Install both:

```sh
curl -fsSL https://raw.githubusercontent.com/yuvalkolodkingal/yuvalkolodkingal/main/install.sh | sh
```

## Rules of thumb

- Score what renders, not what was intended. A beautiful SVG that loads a
  web font renders in the viewer's fallback font; judge the fallback.
- Never reward volume. More badges, more cards, more sections cost points.
- Say what to keep. A review with no "already works" section reads as a
  teardown and gets ignored.
- Give line numbers and snippets. The user should be able to fix the top
  three in ten minutes without asking a follow-up question.
- Re-run the checker after the user applies fixes and report the delta.
