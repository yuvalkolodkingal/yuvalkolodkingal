# scripts/

The generators moved to
[`skills/github-profile-designer/scripts/`](../skills/github-profile-designer/scripts/),
where they double as the engine of the `github-profile-designer` Agent Skill.

```sh
pip install -r skills/github-profile-designer/scripts/requirements.txt
python skills/github-profile-designer/scripts/build.py all      # fetch, render, update README, check
python skills/github-profile-designer/scripts/build.py --help
```

Everything is driven by [`profile.toml`](../profile.toml) at the repository root.
