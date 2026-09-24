# profile.toml schema

TOML, read with Python's standard `tomllib`. Every section except
`[profile]` is optional: leaving a section out leaves that panel off the
page. Inside a section, every key has a default; only write the ones you
change. Strings that name colours accept a theme role (`fg`, `dim`,
`accent`, `blue`, `purple`, `teal`, `yellow`, `pink`, `green`, `orange`,
`red`, `cyan`) or a hex value.

## [profile] (required)

| key | type | default | meaning |
| :-- | :-- | :-- | :-- |
| `username` | str | required | GitHub login; names the profile repository and every API call |
| `name` | str | username | display name (neofetch, finger, alt text) |
| `user` | str | first word of username | the user in every prompt |
| `host` | str | `"github"` | the host in every prompt: a lab, a company, a project |
| `prompt` | str | `"{user}@{host}:~$"` | the heading prompt template |

## [theme]

| key | type | default | meaning |
| :-- | :-- | :-- | :-- |
| `dark` | str | `"tokyo-night"` | palette for the dark render (`build.py themes` lists them) |
| `light` | str | `""` | `""` = dark only; `"auto"` = the matching light palette; or a name. When set, every panel is rendered twice and the README uses `<picture>` |
| `width` | int | 860 | width of full-width panels in CSS pixels |
| `colors` | table | | overrides: `{ accent = "#ff0000", dim = "#888888" }` applied to both palettes, or `{ dark = {...}, light = {...} }` |

Palettes: tokyo-night, tokyo-day, catppuccin-mocha, catppuccin-latte,
dracula, nord, gruvbox-dark, gruvbox-light, one-dark, rose-pine,
rose-pine-dawn, solarized-dark, solarized-light, github-dark, github-light,
monokai, everforest-dark, kanagawa.

## [paths]

| key | default | meaning |
| :-- | :-- | :-- |
| `assets` | `"assets"` | where SVGs are written |
| `data` | `"data"` | where the JSON caches live |
| `readme` | `"README.md"` | the file whose marker blocks are rewritten |

## [data]

Options for the GitHub fetcher (`data/github.json`).

| key | type | default | meaning |
| :-- | :-- | :-- | :-- |
| `exclude_repos` | list[str] | `["<u>/<u>"]` | repositories left out of languages and activity; the profile repo by default |
| `max_language_repos` | int | 40 | newest-pushed repositories that get a languages request (one request each) |
| `cap_share` | float | 0.4 | the most any single repository may contribute to the language bytes; 1 disables |

## Panels

Every panel section accepts `enabled = false` to switch it off, `heading`
to change the command in the README heading (`""` for none), `alt` for the
image alt text, and `title` for the text in the card's title bar. The
per-panel keys are documented in `panel-catalog.md`; this is the summary.

| section | panel | notes |
| :-- | :-- | :-- |
| `[boot]` | boot-log hero | `kernel`, `lines` (list of `{kind, text}` or plain strings), `banner`, `show_login`, `show_last_login`, `show_prompt` |
| `[typing]` | looping typewriter hero | `lines` (list[str], required), `color`, speed knobs |
| `[portrait]` | ASCII portrait | `mode` = `helix`, `image` or `text`; `source` file; `cols`, `rows`, `font`, `ramp`, `invert`, `color`. Drawn inside neofetch when both are enabled |
| `[neofetch]` | facts card | `rows` (list of `{key, value, color}`), `swatches`, `portrait_width`. Values may contain live placeholders |
| `[info]` | legacy key/value card | `rows`, `title`, `width`; used with `[portrait]` when `[neofetch]` is absent |
| `[snake]` | contribution calendar with the snake | `step`, `regrow`, `pause`, `lead_in`, `footer` |
| `[plate]` | 96-well plate of the last 96 days | `enabled` (default true when the section exists), `days`, `pitch`, `radius`, `width` |
| `[systemctl]` + `[[projects]]` | project as a systemd unit | `title`, `host`, `width`; each project: `name`, `label`, `description`, `url`, `docs`, `since` (ISO date, only if real), `status`, `lines`, `links` |
| `[stack]` | `ls -F` listing | `groups` (list of `{name, items, exec}`), `columns`, `gap`, `show_prompt` |
| `[gitlog]` + `[[timeline]]` | milestones as `git log` | `branch`, `limit`; each entry: `date` (`"2026-02"`, `"2026"` or `""`), `subject`, `tag` |
| `[activity]` | live public events | `limit`; needs `data/github.json`; off unless the section exists |
| `[languages]` | language share bars | `limit`; needs `data/github.json`; off unless the section exists |
| `[finger]` | contact block | `office`, `mail`, `site`, `fields` (list of `{key, value, color}`), `plan` (list[str]), `links` (list of `{label, url}` printed as a Markdown line under the card), `shell`, `directory` |
| `[install]` | Markdown block with the installer one-liner | `show` (default false), `repo` |
| `[exit]` | the closing line | `command`, `farewell` (`{host}`, `{user}`), `show_build` |

## Live placeholders

Any `[neofetch]` row value may contain these; the daily build fills them
from `data/github.json` and `data/contributions.json`. A placeholder with no
data renders `--` in dim.

`{uptime}` account age · `{repos}` · `{original_repos}` · `{stars}` ·
`{forks}` · `{followers}` · `{following}` · `{contributions}` ·
`{streak}` · `{longest_streak}` · `{active_days}` · `{best_day}` ·
`{top_language}` · `{languages}` (top three) · `{language_shares}` ·
`{built}` · `{location}`

## README blocks

`build.py readme` rewrites the text between each pair of markers and
leaves everything else alone:

```
<!-- profile:begin neofetch -->
... generated ...
<!-- profile:end neofetch -->
```

Block names: `boot`, `typing`, `neofetch` (or `whoami` for the legacy
portrait + info pair), `snake`, `lab` (plate beside systemctl) or `plate`
or `systemctl`, `stack`, `gitlog`, `activity`, `languages`, `finger`,
`install`, `exit`. A block that is enabled but has no markers is inserted
at `<!-- profile:insert -->` if present, else appended. A block whose panel
is no longer enabled is removed.

## Validation

`build.py check` fails (exit 2) on: an SVG that is not well-formed, contains
`<script>` or `<foreignObject>`, references an external resource, or is
animated without a `prefers-reduced-motion` rule; and on README image
paths that do not exist. It warns on low text contrast, SVGs over 300 KB,
non-ASCII glyphs and third-party image hosts. `--strict` turns warnings
into failures.
