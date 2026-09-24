# skills/

Two [Agent Skills](https://agentskills.io) any AI coding agent can load:

| Skill | What it does |
| :-- | :-- |
| [`github-profile-designer/`](./github-profile-designer/) | Designs and builds a terminal-style profile README like the one in this repository: a boot-log hero, `neofetch`, the contribution snake, a 96-well plate, `ls` of the stack, `git log` of milestones, `systemctl status` for a project, `finger` for contact, `exit`. Self-contained animated SVGs rendered by Python from `profile.toml`, refreshed daily by GitHub Actions. |
| [`github-profile-review/`](./github-profile-review/) | Audits any existing profile README for what silently breaks on github.com and returns a scored report with fixes. |

## Install into every agent on your machine

```sh
curl -fsSL https://raw.githubusercontent.com/yuvalkolodkingal/yuvalkolodkingal/main/install.sh | sh
```

The script copies both skills into `~/.agents/skills/` and into the skills
folder of every agent it detects (Claude Code, Codex, Cursor, GitHub
Copilot, Gemini CLI, Antigravity, OpenCode, Amp, Windsurf, Roo Code, Kilo
Code, Goose, Kiro, Factory Droid, Qwen Code, and more). It runs nothing from
the download and only ever replaces folders it installed itself.

```sh
... | sh -s -- --list               # which agents were found
... | sh -s -- --all                # every agent in the table
... | sh -s -- --agents claude,cursor
... | sh -s -- --project            # into this repository's .claude/skills etc.
... | sh -s -- --uninstall
```

Other ways in:

- `npx skills add yuvalkolodkingal/yuvalkolodkingal`
- Claude Code plugins: `/plugin marketplace add yuvalkolodkingal/yuvalkolodkingal`
  then `/plugin install github-profile-designer`
- Read first: `curl -fsSLO https://raw.githubusercontent.com/yuvalkolodkingal/yuvalkolodkingal/main/install.sh && less install.sh && sh install.sh`
- By hand: `git clone --depth 1 https://github.com/yuvalkolodkingal/yuvalkolodkingal && cp -R yuvalkolodkingal/skills/* ~/.agents/skills/`

Then open your agent and say: *design my GitHub profile with github-profile-designer*.

## Use the engine directly

```sh
pip install -r skills/github-profile-designer/scripts/requirements.txt
python skills/github-profile-designer/scripts/build.py init --username <you>
python skills/github-profile-designer/scripts/build.py all
```
