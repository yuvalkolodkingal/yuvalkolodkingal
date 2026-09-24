# The interview

Ten questions. Ask them in one message when the person is present, or
answer as many as you can from their existing README, repositories and
public profile when they are not, and list what you assumed. Never fill a
gap with a guess: a shorter card with true rows beats a full card with
invented ones.

| # | Ask | Goes to |
| :-- | :-- | :-- |
| 1 | Your name as it should appear, and a short handle for the prompt (like `yuval`). | `[profile].name`, `[profile].user` |
| 2 | Where would the prompt say you are logged in: a lab, company, university or project name? | `[profile].host`, `[boot]` banner |
| 3 | What do you do and where, in one line each? (role, institution) | `[neofetch]` OS and Host rows, `[boot]` lines, `[finger].office` |
| 4 | Your focus in a few words, and the tools you actually use, grouped: languages, frontend, backend, infra. | `[neofetch]` Kernel row, `[stack].groups` |
| 5 | One flagship project: name, one-line description, URL. If you know when it launched, the date. | `[[projects]]`, `[boot]` "Started x.service" line |
| 6 | Three to six milestones with dates you are sure of (a launch, a talk, a certificate, joining somewhere). Leave the date blank if unsure. | `[[timeline]]` |
| 7 | How should people reach you: email, site, LinkedIn or others. | `[finger]`, `[finger].links` |
| 8 | Do you work in a lab or with physical samples? | `[plate].enabled`, lab flavour in boot lines |
| 9 | Portrait: a photo (send a file), ready-made text art, or the built-in DNA helix? | `[portrait]` |
| 10 | A colour scheme, if you have one: Tokyo Night, Catppuccin, Dracula, Nord, Gruvbox, One Dark, Rose Pine, Solarized, GitHub, Monokai, Everforest, Kanagawa. Light mode twin wanted? | `[theme]` |

## Turning answers into config

- Boot lines: two `kernel` lines (a version string that names their
  runtime, and a command line), then three to five `ok` lines, one per
  thing they do, written as systemd unit descriptions: `Reached target
  <focus>.target - <focus in words>.`, `Started <project>.service - <one
  line>.`, `Mounted /<place> - <institution>.` End with
  `Reached target multi-user.target - Multi-User System.`
- neofetch rows: keep neofetch's own keys (OS, Host, Kernel, Uptime,
  Packages, Shell, Resolution, DE, WM, Terminal, CPU, GPU, Memory, Locale)
  and fill them with the person. `Uptime: {uptime}`, `Packages: {repos}
  (repos)`, `Memory: {contributions} contributions / 365 days`, `Top:
  {top_language}` are the live ones. A playful CPU or GPU row is fine if it
  is about them (a biologist's `CPU: Bacillus subtilis @ 37.0C`).
- Stack groups: four groups, three to six items each, the names people
  recognise. Skip a group rather than pad it.
- Timeline: newest first is done by the engine; write `date` as
  `"YYYY-MM"` or `"YYYY"`, `""` when unknown. Subjects read like commit
  messages: `feat: ship x`, `talk: y at z`, `cert: ...`, `join: ...`.
- Project unit: only set `since` when the person gave a date. Put the two
  or three facts that matter into `lines`.
- finger: `office`, `mail`, `site`, extra `fields` for LinkedIn or others,
  two `plan` lines (what they are on now), and `links` for the clickable
  line under the card.
- Photo portrait: run `scripts/prep_photo.py photo.jpg` (needs pillow,
  numpy, opencv-python, rembg) to produce `source-prepped.png`, then set
  `[portrait] mode = "image"` and `source = "source-prepped.png"`. Add the
  photo files to `.gitignore`; the SVG is what gets committed.

## What not to ask

Visitor counters, follower goals, "fun facts", a quote. They date the page
and the terminal metaphor has no place for them.
