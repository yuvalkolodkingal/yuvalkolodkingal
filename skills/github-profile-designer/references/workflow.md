# The daily job

`assets/workflow.template.yml` is written to
`.github/workflows/profile.yml` by `build.py init` and again by
`build.py eject` with the engine path filled in. What it does, and why.

## Triggers

- `schedule`: once a day. Pick a minute that is not `0` so the job does not
  queue behind everyone else's hourly cron.
- `workflow_dispatch`: run it by hand from the Actions tab after the first
  push, so the live rows fill in without waiting a day.
- `push` to `main` when `profile.toml`, the engine or the workflow change.

## Permissions and token

`permissions: contents: write` lets the job commit. `GITHUB_TOKEN` is
passed to `build.py all`; it reads public data at 1000 requests an hour
(60 without a token, shared by every job on the runner's IP, which is not
enough). No personal token, no secret to create.

Requests per run: 1 for the contribution calendar (HTML, no token), 1 for
the user, 1 per 100 repositories, 1 per repository for language bytes
(capped by `[data].max_language_repos`), 1 for public events when
`[activity]` is on, 1 for the rate limit. A typical profile is under 60.

## Degradation

`fetch` never fails the job. Each source keeps its previous JSON on any
error, `data/build.json` records `fresh`, `partial`, `cached` or `empty`
per source with the time it was last fresh, the job writes a table to the
step summary, and a source that is not fresh emits a `::warning::`
annotation. The snake footer appends `(cached YYYY-MM-DD)` when the
calendar is stale; neofetch rows with no data show `--`.

## The commit

`stefanzweifel/git-auto-commit-action` commits `data/*.json`,
`assets/*.svg` and `README.md` when they changed, authored by
`github-actions[bot]`. That author is deliberate: a job that commits as the
user paints a square on the contribution graph every day and turns the
streak into a measurement of cron. Pushes made with `GITHUB_TOKEN` never
trigger other workflows, so no `[skip ci]` is needed.

## Caching and camo

GitHub proxies README images through camo and caches them; a changed SVG
at the same path can take minutes to show. Do not add `?v=` cache busters
to the README, the daily commit is enough.

## Running it elsewhere

Locally: `GITHUB_TOKEN=$(gh auth token) python scripts/profile-engine/build.py all`.
Without network: `build.py all --no-fetch` renders from the caches.
In CI for pull requests: `build.py check --strict` and `build.py render --static`.
