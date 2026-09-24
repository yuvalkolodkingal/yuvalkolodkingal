"""Load and validate profile.toml.

TOML because Python 3.11 reads it with no dependency and it takes comments,
which a config an agent fills in for a person badly needs. Every section is
optional except [profile].username; a missing section means that panel is
not rendered.
"""

import sys
from pathlib import Path

try:
    import tomllib
except ImportError:  # Python < 3.11
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:  # pragma: no cover
        tomllib = None

from theme import LIGHT_PARTNER, PALETTES, get_theme

PANELS = ("boot", "typing", "neofetch", "portrait", "info", "snake", "plate", "systemctl", "stack", "gitlog", "activity", "languages", "finger", "exit", "install")


class ConfigError(ValueError):
    pass


def load(path):
    path = Path(path)
    if tomllib is None:
        raise ConfigError("reading TOML needs Python 3.11+ or `pip install tomli`")
    if not path.exists():
        raise ConfigError(f"{path} not found; run `build.py init` to create one")
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"{path}: {error}") from error
    return validate(data, path)


def validate(data, path="profile.toml"):
    profile = data.get("profile") or {}
    if not profile.get("username"):
        raise ConfigError(f"{path}: [profile].username is required")
    profile.setdefault("name", profile["username"])
    profile.setdefault("user", profile["username"].split("-")[0].lower()[:12])
    profile.setdefault("host", "github")
    profile.setdefault("prompt", "{user}@{host}:~$")
    data["profile"] = profile

    theme = data.get("theme") or {}
    theme.setdefault("dark", "tokyo-night")
    theme.setdefault("light", "")
    theme.setdefault("width", 860)
    if theme["dark"] not in PALETTES:
        raise ConfigError(f"{path}: unknown theme.dark {theme['dark']!r}; known: {', '.join(sorted(PALETTES))}")
    if theme["light"] == "auto":
        theme["light"] = LIGHT_PARTNER.get(theme["dark"], "")
    if theme["light"] and theme["light"] not in PALETTES:
        raise ConfigError(f"{path}: unknown theme.light {theme['light']!r}; known: {', '.join(sorted(PALETTES))}")
    try:
        theme["width"] = int(theme["width"])
    except (TypeError, ValueError):
        raise ConfigError(f"{path}: theme.width must be an integer")
    data["theme"] = theme

    paths = data.get("paths") or {}
    paths.setdefault("assets", "assets")
    paths.setdefault("data", "data")
    paths.setdefault("readme", "README.md")
    data["paths"] = paths

    for panel in PANELS:
        section = data.get(panel)
        if section is None:
            continue
        if not isinstance(section, dict):
            raise ConfigError(f"{path}: [{panel}] must be a table")
        section.setdefault("enabled", True)

    if "typing" in data and data["typing"].get("enabled") and not data["typing"].get("lines"):
        raise ConfigError(f"{path}: [typing].lines is empty")
    if "info" in data and data["info"].get("enabled") and not data["info"].get("rows"):
        raise ConfigError(f"{path}: [info].rows is empty")
    return data


def themes(data):
    """(dark_theme, light_theme_or_None) for the config."""
    section = data["theme"]
    overrides = section.get("colors") or {}
    dark = get_theme(section["dark"], overrides.get("dark") if isinstance(overrides.get("dark"), dict) else overrides)
    light = None
    if section.get("light"):
        light = get_theme(section["light"], overrides.get("light") if isinstance(overrides.get("light"), dict) else None)
    return dark, light


def enabled(data, panel):
    section = data.get(panel)
    return bool(section) and bool(section.get("enabled", True))


if __name__ == "__main__":
    try:
        config = load(sys.argv[1] if len(sys.argv) > 1 else "profile.toml")
    except ConfigError as error:
        print(f"error: {error}")
        raise SystemExit(1)
    dark, light = themes(config)
    on = [panel for panel in PANELS if enabled(config, panel)]
    print(f"ok: {config['profile']['username']} theme {dark.name}" + (f" + {light.name}" if light else "") + f", panels: {', '.join(on)}")
