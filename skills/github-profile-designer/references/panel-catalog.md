# Panel catalog

One section of `profile.toml` turns on one panel. The engine draws it as one
SVG in `assets/`, and `build.py readme` writes one marker block for it in
`README.md` (`<!-- profile:begin NAME -->` to `<!-- profile:end NAME -->`).
Every panel is off until its section exists; a section that exists is on
unless it says `enabled = false`.

| panel | section | block | asset | data | default |
| :-- | :-- | :-- | :-- | :-- | :-- |
| boot | `[boot]` | `boot` | `boot.svg` | build time | off; on with `[boot]` |
| neofetch | `[neofetch]` (+ `[portrait]`) | `neofetch` | `neofetch.svg` | github.json, contributions.json, build time | off; on with `[neofetch]` |
| portrait | `[portrait]` | `whoami` | `portrait.svg` | none (a source file for image/text modes) | off; standalone only when neofetch is off |
| info | `[info]` | `whoami` | `info.svg` | none | off; standalone only when neofetch is off |
| typing | `[typing]` | `typing` | `typing.svg` | none | off; on with `[typing]` |
| snake | `[snake]` | `snake` | `snake.svg` | contributions.json | off; on with `[snake]` |
| plate | `[plate]` | `lab` or `plate` | `plate.svg` | contributions.json (last 96 days) | off; on with `[plate]` |
| systemctl | `[systemctl]`, `[[projects]]` | `lab` or `systemctl` | `systemctl.svg` | build time, github.json (fallbacks) | off; on with `[[projects]]` or `[systemctl]` |
| stack | `[stack]` | `stack` | `stack.svg` | none | off; on with `[stack]` |
| gitlog | `[gitlog]`, `[[timeline]]` | `gitlog` | `gitlog.svg` | none | off; on with `[[timeline]]` or `[gitlog]` |
| activity | `[activity]` | `activity` | `activity.svg` | github.json (public events) | off; on with `[activity]` |
| languages | `[languages]` | `languages` | `languages.svg` | github.json (bytes per language) | off; on with `[languages]` |
| finger | `[finger]` | `finger` | `finger.svg` | build time, github.json (name, blog) | off; on with `[finger]` |
| exit | `[exit]` | `exit` | `exit.svg` | build time | off; on with `[exit]` |
| install | `[install]` | `install` | none (Markdown) | none | off; on with `show = true` |

Keys every panel section takes:

- `enabled` (bool, true): draw the panel or not.
- `heading` (string): the command in the `### \`user@host:~$ cmd\`` heading above the panel; `{user}` and `{host}` expand. An empty string removes the heading. The defaults are the `HEADINGS` table in `build.py` and are listed per panel below.
- `alt` (string): the `alt` of the `<img>` in the README, replacing the generated one.
- `label` (string): the `aria-label` on the SVG root, replacing the generated one. Not on typing or snake, which build theirs from the content.
- `width` (int): only on the panels marked below; everything else is `[theme].width` (860).

"Build time" means the moment `build.py render` ran, as `generated_at`, and the short git sha. Data files come from `build.py fetch`: `data/contributions.json` is the public calendar (no token), `data/github.json` is the REST API (token optional, recommended). A fetch that fails keeps the previous file, so a panel reads stale data before it reads none.

## boot

The page opens like a machine starting: a systemd-style log with rising kernel timestamps, `[  OK  ]` unit lines that describe the person (targets reached, services started, volumes mounted), then the getty banner, `host login: user`, `Password:`, a real `Last login:` stamp from the build, and a prompt with a blinking cursor that every heading below then continues. It imitates `dmesg` followed by a console login.

Section `[boot]`. Block `boot`. No heading by default (the image is the first thing on the page). Asset `boot.svg`.

- `lines` (array of `{ kind, text }` or plain strings): the log. `kind` is `kernel` (timestamp prefix), `ok`, `info` or `fail`; a plain string is `ok`. `{kernel}` in a text expands to `kernel`. Text before ` - ` prints bold, like a unit name. Without `lines` the engine writes five generic lines from the profile.
- `kernel` (string, `6.18.0-profile`): the version in the first line.
- `banner` (string, `<name> <title>`): the getty line before the login prompt.
- `title` (string, `tty1`): the title bar.
- `show_login` (bool, true), `show_last_login` (bool, true), `show_prompt` (bool, true): the three closing groups.
- `step` (float, 0.16): seconds between lines. `font` (float, 11.5), `row_height` (int, 19).

Data: build time for the `Last login` stamp, nothing else. Size: 860 x (64 + rows * 19 + 16), rows = lines + 3 login + 2 last-login + 1 prompt; eight lines give 346.

Motion: CSS. Each line fades in (`.05s linear forwards`) at 0.3 s + index * step; the banner, login and password follow with getty-like pauses; the stamp and the prompt come last, about four seconds in for eight lines. The cursor blinks. Reduced motion shows the whole log at once with a steady cursor.

Enable it as the hero of a full session page. Never with typing: one hero.

## neofetch

The `neofetch` card: portrait on the left, system facts on the right, with the person as the machine. `OS` is the role, `Host` the institution, `Kernel` the focus, `Uptime` the account age, `Packages` the repositories, `Memory` the contributions, then the two rows of colour swatches neofetch prints last. It imitates `neofetch` exactly, header rule included.

Section `[neofetch]`. Block `neofetch`. Heading `neofetch`. Asset `neofetch.svg`.

- `rows` (array of `{ key, value, color }`): the facts. `color` is a theme role (`teal`, `yellow`, `blue`, ...) or a hex; default `fg`. A value longer than the column is cut with `…`.
- `title` (string, `neofetch`), `swatches` (bool, true), `portrait_width` (int, 370, the left column when a portrait is present), `font` (float, 11.5), `row_height` (int, 19).

The portrait inside comes from `[portrait]` (below); its `mode`, `source`, `cols`, `rows`, `font`, `ramp`, `invert` and `color` all apply. Without a `[portrait]` section the rows start at the left edge and the card is as tall as the rows need.

Placeholders in any value, filled by `live_values()` from the data files: `{uptime}` (account age, "1 year, 2 months"), `{repos}`, `{original_repos}`, `{stars}`, `{forks}`, `{followers}`, `{following}`, `{contributions}`, `{streak}` ("47d"), `{longest_streak}`, `{active_days}`, `{best_day}` ("Jun 18 (80)"), `{top_language}`, `{languages}` (top three names), `{language_shares}` ("Python 61%, ..."), `{built}` (the build stamp), `{location}` (from the GitHub profile). A placeholder with no data prints `--` and the whole value turns dim, so a missing `data/github.json` shows as `Packages: -- (repos)` rather than a wrong number.

Data: `data/github.json` for repos, stars, uptime, languages and location; `data/contributions.json` for contributions and streaks; build time for `{built}` and the uptime arithmetic. Size: 860 x max(66 + (rows + 2) * 19 + 44, 372 with a portrait); sixteen rows give 452.

Motion: the rows slide in from the left (10 px, 0.45 s ease-out) 60 ms apart from 0.35 s, CSS; the portrait wipes itself in once, SMIL. Reduced motion shows every row at once, drops the portrait clip and hides the cursors.

Enable it as the "who" panel. It replaces the portrait + info pair; when `[neofetch]` is on, `[portrait]` feeds it and `[info]` is ignored.

## portrait (standalone)

An ASCII picture that types itself in row by row, in one ink colour, under a `./portrait.sh` title. Three sources: a photo downsampled through a density ramp, a text file of ready-made art, or the built-in DNA double helix with base labels. The ramp starts with a space so bright areas wash out and only the subject prints.

Section `[portrait]`. Block `whoami`, shared with info as a two-cell table; heading `whoami` (read from `[info].heading` first, then `[portrait].heading`). Asset `portrait.svg`.

- `mode` (string, `helix`): `helix`, `image` or `text`.
- `source` (string): path relative to the repository root for `image` (needs Pillow) or `text`. A missing file prints a note and draws the helix.
- `cols` (int, 84), `rows` (int, 47), `font` (float, 6.8): the grid. The defaults land the file at 371 x 372 so it lines up with a 490-wide info card.
- `ramp` (string, `` " .`:-=+*cs#%@" ``): dark to light glyphs for `image` and `helix`.
- `invert` (bool, false): flip the photo before ramping. `color` (string): the ink; default is the theme's `ink`.
- `title` (string, `./portrait.sh`), `width` (int, 370): the README cell width.

Data: none. Size: (cols * font * 0.6 + 28) x (rows * font + 52); 371 x 372 by default.

Motion: SMIL. Each non-blank row wipes left to right over 0.34 s with a block cursor riding the edge, each row 45 ms after the one above, once, then frozen. Forty-seven rows finish in about 2.5 s. Reduced motion removes the clips and hides the cursors.

Enable it standalone only with `[info]` and without `[neofetch]`. The neofetch card is the current home for the portrait.

## info (standalone)

A key/value card that slides in one row at a time, with the same swatch strip neofetch ends with. It carries what a graph cannot say: what the person works on, where, with what. It imitates the right half of `neofetch`.

Section `[info]`. Block `whoami` (with portrait). Heading `whoami`. Asset `info.svg`.

- `rows` (required; array of `{ key, value, color }` or `["key", "value", "color"]` arrays). No placeholders: values are typed by hand, so keep numbers out of it and put them in neofetch.
- `title` (string, `user@host`), `key_color` (string, accent), `show_swatches` (bool, true), `swatches` (array of colour roles, default `dim, pink, teal, yellow, blue, purple, cyan, fg`).
- `value_x` (int, 122): where values start, in pixels. `pad` (int, 20), `font` (float, 11.5), `row_height` (int, 21), `width` (int, 490).

Data: none. Size: 490 x (66 + rows * 21 + 50); 284 for eight rows. Set `width = 860` when there is no portrait beside it.

Motion: CSS slide-in, 60 ms apart from 0.25 s. Reduced motion shows all rows.

Enable it for the legacy pair (portrait + info) or as a plain card on a minimal page. It cannot show live numbers, which is why neofetch replaced it.

## typing (alternative hero)

One line of large text types itself out, holds with a blinking cursor, backspaces, and moves on to the next line, forever. It imitates a shell with someone at the keyboard, and is the one loop the design principles allow on a page.

Section `[typing]`. Block `typing`. No heading. Asset `typing.svg`.

- `lines` (required; array of strings).
- `font` (float, 27), `height` (int, 78), `color` (string, accent), `per_char` (float, 0.075) typing speed, `erase_char` (float, 0.028) backspacing, `hold` (float, 1.7) pause on the full line, `gap` (float, 0.35) pause when empty, `blink` (float, 0.5) cursor period while holding.

Data: none. Size: 860 x 78. Characters above U+2500 count as two columns; keep the lines ASCII so the cursor lands on the edge of the text.

Motion: SMIL, looping. The cycle is the sum over lines of `chars * per_char + hold + chars * erase_char + gap`; three 30-character lines give about 15 s. There is no still form and no CSS block, so `build.py check` reports the file as animated without a reduced-motion rule. Keep the lines short and few, or use boot, which freezes.

Enable it only on a minimal page instead of boot. One typewriter per page; exit already types once, which is fine because it stops.

## snake

The whole contribution calendar, not a decoration next to one: month and day labels, 53 week columns of 12 px squares, the Less/More legend and a footer with the year total, the streaks and the best day. A snake crawls the grid in a serpentine (down one column, up the next); every square it reaches flashes and empties; when it leaves the far side the calendar regrows in a wave from the left and the run starts over. It imitates `git-cal` with a game on top.

Section `[snake]` (may be empty). Block `snake`. Heading `git-cal --snake`. Asset `snake.svg`. No title bar.

- `step` (float, 0.045): seconds per square.
- `regrow` (float, 3.2): the regrowth wave; `pause` (float, 1.0): the beat before the next run.
- `lead_in` (int, 6): squares of run-up before the first column.
- `footer` (bool, true).
- `cached_note` (string): a date printed dim after the footer. `build.py` sets it from `data/build.json` when the calendar could not be refreshed and the old file was kept.

Data: `data/contributions.json`. When it is missing the build draws a blank 53-week grid (`fetch_contributions.empty_calendar`) so the page still renders: no coloured squares, `0 contributions` in the footer. Size: 860 x 214 (192 without the footer).

Motion: SMIL, looping; about 21.7 s for a full year at the default step (389 squares of path, regrow, pause). The head carries a glow filter and the seven body segments follow it a square behind each. Reduced motion swaps the moving layer for a still twin: the full calendar, no snake.

Enable it for every account. It is real data, needs no token, and is the one big number panel the layout wants second.

## plate

A 96-well plate: eight rows A to H by twelve columns, loaded column by column the way a plate is filled, oldest day at A1, one well per day of the last 96 days, heat by contribution level. A reader beam sweeps left to right once and each column lights as it passes. The caption counts the wells, the positives and the read date. It imitates a plate reader's output, and it is the one panel only a lab would draw.

Section `[plate]`. Block `lab` beside systemctl (a two-cell table, heading `plate-reader --last 96d; systemctl status`, taken from `[systemctl].heading`), or `plate` alone (heading `plate-reader --last 96d`). Asset `plate.svg`.

- `days` (int, 96): 8 x 12 wells; fewer days leave the last wells empty.
- `pitch` (float, 20): well spacing; `radius` (float, 6.5).
- `title` (string, `plate-reader --last 96d`), `width` (int, 370). The card grows if the wells need more.

Data: the tail of `data/contributions.json`; missing data means the blank calendar, every well empty, `0 positive`. Size: 370 x 256.

Motion: SMIL, once. A gradient beam moves across in 3.36 s from 0.3 s; the positive wells in each column fade from 15% to full 0.28 s per column as it passes. Reduced motion shows the still twin with every well lit and no beam.

Enable it for people who work in a lab. It shows the same data as the snake from a different angle, so it earns its place only when the metaphor fits the person.

## systemctl

Flagship projects printed like `systemctl status`: a coloured dot, `name.service - description`, `Loaded`, `Active: active (running) since ...; 10 months ago`, `Docs`, `Main PID`, `Tasks`, `Memory`, `CPU`, `CGroup`, then up to four journal lines stamped with the build time. A live project is a running service, and systemd already prints exactly that.

Section `[systemctl]` for the card, `[[projects]]` for the units. Block `lab` (with plate) or `systemctl`. Heading `systemctl status`. Asset `systemctl.svg`.

`[systemctl]` keys:

- `title` (string): default `systemctl status <units>`.
- `host` (string): in the journal lines; default the profile host. `empty` (string, `no units found`), `font` (11.5), `row_height` (21).
- `width` (int): default 860 minus the plate width when plate is on, else 860.

`[[projects]]` entry fields:

- `name` (required): the unit; `.service` is appended.
- `description`, `url`, `docs` (defaults to `url`).
- `since` (ISO date): the `Active ... since` stamp and the "N months ago" from the build date.
- `status` (string, `active (running)`): the first word colours the dot. `active` green, `activating`, `reloading`, `deactivating` yellow, `failed` red, `inactive` dim.
- `lines` (array, first four used): journal messages.
- `exec` (string): the process name after the PID; default from the language of the matching repo in `data/github.json`, else `node`.
- README only: `label` (link text, default `name`) and `links` (array of `{ label, url }`). The block prints them as an `xdg-open` line under the card, because an SVG in an `<img>` cannot carry a link.

PID, tasks, memory, CPU and the start time are decoration derived from a hash of the unit name, so they never change between builds. The journal timestamps are the build time.

Data: build time. Without `[[projects]]` the top starred repo from `data/github.json` becomes the unit; without that too the card prints `empty`. Size: 490 x (66 + (rows - 1) * 21 + 28); one unit with three journal lines is 13 rows, 346 high, and a second unit adds a blank row plus its own.

Motion: CSS rows 50 ms apart from 0.2 s; the dot pulses (SMIL opacity, 2.4 s loop) with a still twin. Reduced motion shows all rows and a steady dot.

Enable it for one or two things that are live. A project that is a repository and not a service reads better as a gitlog line.

## stack

The tools someone uses, printed as `ls -F --color=auto ~/stack`: each group is a directory in bold accent with a trailing slash, its tools are the files below it, indented two columns and coloured by group (blue, teal, purple, yellow, cycling). Groups sit side by side like `ls` in a wide terminal and wrap when they do not fit. A group named `shipped`, or with `exec = true`, marks its items with `*`. It says what a badge wall says, in the theme's colours.

Section `[stack]`. Block `stack`. Heading `ls -F --color=auto ~/stack`. Asset `stack.svg`.

- `groups` (array of `{ name, items, exec }`).
- `columns` (int, 0): groups per row; 0 fits as many as the width allows.
- `gap` (int, 2): blank columns between groups.
- `show_prompt` (bool, true): a prompt with a blinking cursor after the listing. `title` (string, `ls -F --color=auto ~/stack`), `empty` (string, the `ls: cannot access` error), `font` (11.5), `row_height` (21).

Data: none. Size: 860 x (66 + lines * 21 + 30, or + 12 without the prompt), lines = the tallest group per row plus one blank line between rows. Four groups, the tallest six items, no prompt: 225.

Motion: CSS. Each visual line slides in 70 ms after the previous, top to bottom across all columns, the way a terminal prints. Reduced motion shows the listing and a steady cursor.

Enable it whenever the person wants a stack section. Prefer it to shields.io badges every time.

## gitlog

Milestones as `git log --oneline --decorate --date=short`, newest first: a seven-character hash in yellow, the date in dim, decorations in git's colours (`HEAD -> main, origin/main` on the first line, `tag: x` when set), then the subject. The hash is derived from the entry, so it is stable between builds. This is curated history, so it reads the same in a quiet month as in a busy one.

Section `[gitlog]` for the card, `[[timeline]]` for the entries. Block `gitlog`. Heading `git log --oneline --decorate --date=short`. Asset `gitlog.svg`.

`[gitlog]` keys: `branch` (string, `main`), `limit` (int, 12), `title`, `empty` (the `fatal: ... does not have any commits yet` line), `font` (11.5), `row_height` (21).

`[[timeline]]` entry fields:

- `subject` (required): write it like a commit subject, `cert:`, `feat:`, `poster:`, `join:`.
- `date` (string): `YYYY`, `YYYY-MM` or `YYYY-MM-DD`. Entries sort by this as text, descending; an empty date prints `----` and sorts last.
- `tag` (string): a `tag:` decoration.

Data: none. Size: 860 x (66 + rows * 21 + 12); six entries give 204.

Motion: CSS fade, 70 ms apart. Reduced motion shows every line.

Enable it for anything with a date: certificates, talks, jobs, releases. It replaces a certificates table for people with a few, and pairs with a collapsed table for people with many.

## activity

Recent public events as `git log --oneline --all`: a hash-like id, a tag for the kind (`push` green, `pull` purple, `issue` orange, `new` teal, `star` yellow, `fork` cyan, `tag` pink, `talk` dim, `review` purple, `open` teal), the summary, the title or commit message in dim, and how long ago on the right; then a pager-style `(END)` marker with a blinking cursor. Consecutive pushes to one repository fold into one line with the total commit count.

Section `[activity]`. Block `activity`. Heading `git log --oneline --all --since=90.days`. Asset `activity.svg`.

- `limit` (int, 10): rows; the fetcher keeps at most 12.
- `title` (string, `git log --oneline --all`), `empty` (string, `no public activity in the last 90 days`), `font` (11.5), `row_height` (21).

Data: `activity` in `data/github.json`, from `/users/{u}/events/public`, minus `[data].exclude_repos`; missing data prints `empty`. Size: 860 x (66 + rows * 21 + 30); ten rows give 306.

Motion: CSS slide-in, 70 ms apart; the cursor blinks. Reduced motion shows all rows and a steady cursor.

Enable it only for accounts with steady public activity. The events API covers about 90 days and 300 events, so a quiet month prints the `empty` line, which is worse than no panel.

## languages

Language share printed like `du -sh languages/* | sort -rh`: one row per language with the percentage, the name in its linguist colour (Python is always that blue; unknown languages cycle the theme accents) and a bar that grows in from the left.

Section `[languages]`. Block `languages`. Heading `du -sh languages/* | sort -rh`. Asset `languages.svg`.

- `limit` (int, 6).
- `title`, `empty` (string, `no language data yet`), `font` (11.5), `row_height` (24).

Data: `languages` in `data/github.json`: bytes per language across original, non-archived repositories, newest-pushed first up to `[data].max_language_repos`, with no repository allowed more than `[data].cap_share` of the total (0.4) so one vendored bundle does not change who the person is. Without a token the fetcher falls back to counting primary languages. Missing data prints `empty`. Size: 860 x (66 + rows * 24 + 12); six rows give 222.

Motion: CSS. Rows fade in 90 ms apart and each bar scales from 0 to its width over 0.9 s. Reduced motion shows the full bars.

Enable it or neofetch's `{top_language}` / `{languages}` row, not both; the same number twice on one page reads as padding.

## finger

The contact card as `finger user` on a BSD box: `Login` and `Name` on one line, `Directory` and `Shell` on the next, then `Office`, `Mail`, `Site`, any extra fields, an `On since ... on pts/0 from github-actions` line that doubles as the build stamp, and the `Plan:` block underneath. Addresses print in the link colour; the README prints a Markdown link line under the card for the real anchors.

Section `[finger]`. Block `finger`. Heading `finger {user}`. Asset `finger.svg`.

- `login` (default the profile `user`), `name` (default the profile `name`, then the GitHub name), `directory` (`/home/<login>`), `shell` (`/bin/zsh`).
- `office`, `mail`, `site` (default the GitHub profile's blog): printed only when set.
- `fields` (array of `{ key, value, color }`, `"Key: value"` strings or `[key, value, color]`): extra rows. Keys `mail`, `site`, `url`, `web`, `www`, `email`, `e-mail`, `homepage`, `blog` take the link colour by default.
- `plan` (string or array of strings): the `.plan`; empty prints `no_plan` (`No Plan.`) in dim.
- `title` (`finger <login>`), `column` (int, 40): where the second pair on a line starts, `tty` (`pts/0`), `origin` (`github-actions`), `font` (11.5), `row_height` (21).
- README only: `links` (array of `{ label, url }`) for the `xdg-open` line. Without it, `mail` becomes an `Email` link and `site` a `Website` link.

Data: build time for `On since`; `data/github.json` only for the name and blog fallbacks. Size: 860 x (66 + (rows - 1) * 21 + 28); office, mail, site, one field and a two-line plan make ten rows, 283.

Motion: CSS slide-in, 60 ms apart from 0.25 s. Reduced motion shows all rows.

Enable it always. Readers scan the bottom of a profile for how to reach the person, and this is that block.

## exit

The session ends the way it began, at a prompt: `user@host:~$ exit` types itself out with a block cursor, the shell answers `logout`, and `Connection to host closed.` carries the build stamp on the right, which is the honest place for it. The README block also carries a collapsed `man <username>` page listing every asset, its generator, its source and its refresh cadence, generated from the `SOURCES` table.

Section `[exit]`. Block `exit`. Heading `exit`. Asset `exit.svg`. No title bar.

- `command` (string, `exit`).
- `farewell` (string, `Connection to {host} closed.`): `{host}` and `{user}` expand.
- `show_build` (bool, true): the `last build 2026-09-24 16:48 UTC · 8e37abb` stamp. It is dropped when it would run into the farewell.
- `host` (string): default the profile host.
- `per_char` (float, 0.06), `begin` (float, 0.4), `font` (11.5), `row_height` (20).

Data: build time and the git sha. Size: 860 x 84.

Motion: SMIL typewriter that plays once and freezes (about 1.2 s for the default line), then `logout` and the farewell reveal in CSS. Reduced motion removes the clip, hides the cursor and shows all three lines.

Enable it on every page that has headings in the prompt style; without a logout the session just stops.

## install (Markdown only)

A heading with a `curl ... | sh` one-liner and a short paragraph inviting the reader to install the skill and design their own profile. No SVG; the block is text.

Section `[install]`. Block `install`. The heading is the one-liner itself.

- `show` (bool): the only switch. `enabled` is ignored here.
- `repo` (string, `yuvalkolodkingal/yuvalkolodkingal`): the repository that hosts `install.sh`.

Enable it only when the person ships the skill from their profile repository. Most profiles leave it out.

## Composing a page

`blocks()` emits the blocks in this order and `build.py readme` inserts any missing ones at `<!-- profile:insert -->` (or at the end). After that, the page order is the order of the marker blocks in `README.md`, so move whole blocks to reorder. Hand-written sections (research, a certificates table in `<details>`) go between blocks and survive every rebuild.

Recommended default order: `boot`, `neofetch`, `snake`, `lab` (plate + systemctl), `stack`, `gitlog`, then `activity` or `languages` if enabled, your prose, `finger`, `install` if shown, `exit`. That is the section order from the design principles: who, the big number, what they use, what they made, contact, how the page is built.

Three layouts:

- Full terminal session (this repository): `[boot]`, `[portrait]` + `[neofetch]`, `[snake]`, `[plate]` + `[[projects]]`, `[stack]`, `[[timeline]]`, a `cat ~/research.txt` prose section and an `ls ~/certs` table by hand, `[finger]`, `[install]`, `[exit]`. Ten prompts, two of them typed by hand.
- Minimal: `[typing]`, `[snake]`, `[info]` with `width = 860`, and `[exit]`. Three images, no data file beyond the calendar, no token. Use it for someone who wants a light page or has little to list yet.
- Lab: `[boot]` with mounted volumes and reached targets named after the lab, `[portrait]` in helix mode inside `[neofetch]`, `[snake]`, `[plate]` beside one `[[projects]]` unit, `[[timeline]]` for posters and papers, `[finger]` with the office, `[exit]`. Skip stack, activity and languages: a lab page is about the work, not the toolchain.

Turning a panel off: delete its section, or set `enabled = false` in it. Two exceptions: `systemctl` stays on while `[[projects]]` entries exist and `gitlog` while `[[timeline]]` entries exist, so comment those out; and `install` turns off with `show = false`. When neofetch is on, `[portrait]` is drawn inside it and `[info]` is ignored. The next `build.py readme` removes the block of any panel that is no longer enabled; the old SVG in `assets/` is not deleted, so remove it by hand.

Width: `[theme].width` (860) is every full-width panel. Side-by-side panels add up to it: plate 370 + systemctl 490, or portrait 370 + info 490. Set `[theme].light = "auto"` to render a light twin of every panel (`name-dark.svg`, `name-light.svg`) and have the README use `<picture>`.
