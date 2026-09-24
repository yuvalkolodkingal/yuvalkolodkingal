---
name: github-profile-designer
description: Design, generate and maintain an animated terminal-style GitHub profile README (a boot-log hero that logs in, a neofetch card with an ASCII portrait, a contribution-graph snake, a 96-well plate, an ls listing of the stack, a git log of milestones, systemctl status for the flagship project, a finger contact block and an exit line) as self-contained animated SVGs that Python renders from profile.toml and GitHub Actions refreshes daily, with no third-party stats services. Use this whenever someone wants to create, redesign, upgrade, animate, theme, automate or "make cooler" their GitHub profile, profile README, username/username repository, contribution snake, typing header, neofetch card or stats cards, or says "make my GitHub look like yuvalkolodkingal", even if they do not say "skill" or "README". Runs a short interview, writes profile.toml, renders assets/, injects README blocks between markers without touching hand-written prose, and vendors the engine and the workflow into their repository. Not for ordinary project READMEs.
---

# GitHub profile designer

You are about to turn someone's profile page into one uninterrupted terminal
session: the machine boots, the person logs in, every heading is the next
command at the same prompt, and the page ends with `exit`. Every panel is an
SVG this skill's engine renders from `profile.toml`; nothing on the page
depends on another server. Read `references/design-principles.md` before
you design and `references/github-readme-constraints.md` before you touch
markup: most profile READMEs look broken because of rules in that file.

## What you produce

In the repository named after the user (`<user>/<user>`, public, README at
the root):

- `profile.toml` at the root, the one file the person edits afterwards.
- `assets/*.svg`, rendered, committed.
- `README.md` with generated blocks between `<!-- profile:begin NAME -->`
  and `<!-- profile:end NAME -->` markers and the person's own prose
  outside them.
- `data/` with the fetched caches, and a daily GitHub Actions workflow.
- The engine itself, vendored by `build.py eject`, so the workflow runs on
  GitHub's runners without this skill being installed there.

## The engine

`scripts/build.py` is the only entry point. Python 3.11+ (it reads TOML
with the standard library), `pip install -r scripts/requirements.txt` for
the fetchers (requests, beautifulsoup4). Run it from the repository root.

```
build.py init --username U [--name N] [--palette P]   profile.toml, README, workflow, folders
build.py fetch                                        data/ from GitHub (token optional)
build.py render [--only a,b] [--static]               assets/*.svg
build.py readme                                       rewrite the marker blocks
build.py all [--no-fetch]                             fetch, render, readme, check
build.py check [--strict]                             config, SVG rules, README references
build.py eject [--out scripts/profile-engine]         copy the engine into the repository
build.py list | themes                                enabled panels | palettes
```

Exit codes: 0 ok, 1 usage or runtime error, 2 check failure, 3 config
error. A network failure never fails a build; the fetchers keep their last
cache and the SVGs say so.

## Workflow

Follow these steps in order. Stop and ask when a step needs a fact you do
not have; never invent a role, a date, a project or a link (see principle 7
in the design principles).

1. **Find the repository.** It is `<login>/<login>`. If it exists, read its
   README first: the person may have prose, links and certificates worth
   keeping. If it does not exist, tell them to create it (public, with a
   README) or create it for them if you have the means.

2. **Interview.** Use `references/interview.md`. Ten questions, most of
   them answerable in a few words: name and short handle, what they do and
   where, their focus in one line, a flagship project with a URL, their
   stack in four groups, milestones with real dates, contact links, whether
   they work in a lab (enables the plate), a portrait choice (photo, text
   art, or the built-in DNA helix), a palette. Anything they skip, leave
   out of the config.

3. **Scaffold.** From the repository root:
   `python <skill>/scripts/build.py init --username <login> --name "<name>"`.
   This writes a commented `profile.toml`, a README with marker blocks (or
   leaves an existing README alone and appends blocks at
   `<!-- profile:insert -->` or at the end), the workflow, and empty
   `assets/` and `data/`.

4. **Fill `profile.toml`.** Schema in `references/profile-schema.md`,
   every panel and its keys in `references/panel-catalog.md`, the complete
   worked example in `assets/examples/yuvalkolodkingal.toml`. Write the
   boot lines, the neofetch rows, the project unit, the stack groups, the
   timeline and the finger block from the interview. Keep the prompt user
   short and the host meaningful (a lab, a company, a project name).

5. **Move the prose.** Anything from the old README worth keeping (an about
   paragraph, a certificates table, research notes) goes outside the
   markers under a prompt heading of its own, for example
   `### \`user@host:~$ cat ~/about.txt\``. Retire badge walls, visitor
   counters and third-party stats cards; the panels replace them with real,
   committed data.

6. **Build and look.** `python <skill>/scripts/build.py all` (add
   `--no-fetch` when offline). Read the check output. Then open the SVGs:
   render `README.md` to HTML or load each `assets/*.svg` in a browser, and
   fix anything that overflows, clips or reads wrong. If you can run
   headless Chromium, screenshot the panels at 300 ms and 3 s and once with
   reduced motion emulated on a page that loads the SVG directly.

7. **Vendor the engine and wire the workflow.**
   `python <skill>/scripts/build.py eject` copies `scripts/` into
   `scripts/profile-engine/` in their repository and points the workflow at
   it. Commit `profile.toml`, `README.md`, `assets/`, `data/`,
   `scripts/profile-engine/` and `.github/workflows/profile.yml`. The
   workflow uses the built-in `GITHUB_TOKEN`; no secret to create. Its
   refresh commits are authored by `github-actions[bot]` so the daily job
   does not paint the contribution graph it draws.

8. **Hand off.** Tell the person: edit `profile.toml` and push to change
   anything; the workflow re-renders daily at the cron time and on every
   push that touches the config; `build.py check` runs in CI; the
   `github-profile-review` skill can audit the result. Mention that the
   `{uptime}`, `{repos}` and `{top_language}` rows show `--` until the
   first workflow run fills `data/github.json`.

## Rules that keep the result good

- One prompt, real commands. Headings are `user@host:~$ <command>` and the
  command must plausibly print what follows (`neofetch`, `git log`, `ls`,
  `cat`, `finger`, `exit`). No invented `./scripts` unless the config makes
  one real.
- One palette. Every colour comes from the theme; badges and emoji bring
  colours and glyphs that break it. The engine emits ASCII only.
- Real data or none. Numbers come from `data/`; a missing number renders
  `--`, never a guess.
- Motion serves reading: one looping panel (the snake), everything else
  plays once and freezes, and every animated file honours
  `prefers-reduced-motion`. `build.py check` refuses an animated SVG that
  does not.
- Hand-written prose lives outside the markers and is never touched.
- Keep the page under about 1.5 MB of images and each SVG under 300 KB.

## Files in this skill

- `scripts/`: the engine. `build.py`, `profile_config.py`, `theme.py` (18
  palettes), `fetch_contributions.py`, `fetch_github.py`, one
  `render_<panel>.py` per panel, `prep_photo.py` for photo portraits.
- `references/design-principles.md`: the taste rules.
- `references/github-readme-constraints.md`: what GitHub renders and strips.
- `references/profile-schema.md`: every config key.
- `references/panel-catalog.md`: every panel, its keys, its data.
- `references/interview.md`: the questions and how to turn answers into config.
- `references/workflow.md`: the Actions job, tokens, rate limits, degradation.
- `references/svg-animation-cookbook.md`: how the animations are built.
- `assets/profile.example.toml`, `assets/README.template.md`,
  `assets/workflow.template.yml`, `assets/examples/yuvalkolodkingal.toml`.
