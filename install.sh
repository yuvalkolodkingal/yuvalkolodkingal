#!/bin/sh
# Install the github-profile-designer skills into every AI coding agent on
# this machine with one command:
#
#   curl -fsSL https://raw.githubusercontent.com/yuvalkolodkingal/yuvalkolodkingal/main/install.sh | sh
#
# Options go after `sh -s --`:
#
#   ... | sh -s -- --all                      every known agent, detected or not
#   ... | sh -s -- --agents claude,cursor     only these agent ids (see --list)
#   ... | sh -s -- --project                  into this repository (./.claude/skills ...)
#   ... | sh -s -- --list                     show the agents and which were found
#   ... | sh -s -- --uninstall                remove what this script installed
#   ... | sh -s -- --ref v1.2.0               pin a tag, branch or commit
#
# What it does: downloads the repository tarball, finds every skills/<name>/
# SKILL.md in it, copies each skill into the shared store ~/.agents/skills/
# (the location Agent Skills tools already read), and then copies (or, with
# --link, symlinks) that skill into each detected agent's own skills folder.
# Every folder it writes gets a .skill-meta file naming this source, and it
# only ever replaces or removes folders that carry that marker. It never
# executes anything from the download, never asks for input, never needs
# sudo. Prefer to read before you run: curl -fsSLO <url> && less install.sh.
#
# Plain POSIX sh: dash, bash, zsh, busybox and Git Bash on Windows all work.
# The whole script is a function called on the last line, so a download that
# was cut short does nothing at all.

SOURCE_REPO="yuvalkolodkingal/yuvalkolodkingal"
VERSION="1.0.0"

# The agent table. One row per agent:
#   id|label|global skills dir|project skills dir|probe dir|probe binary|confidence
# An agent is "detected" when its probe dir exists or its binary is on PATH.
# "high" rows are documented locations; "medium" are widely used but less
# documented; "low" rows are only touched when detected or asked for by id.
# The universal ~/.agents/skills store is always installed and is what Codex,
# Amp, OpenCode and the `npx skills` CLI read directly.
agents_table() {
    cat <<TABLE
agents|Shared store (~/.agents)|$HOME/.agents/skills|.agents/skills||always|high
claude|Claude Code|$HOME/.claude/skills|.claude/skills|$HOME/.claude|claude|high
codex|OpenAI Codex|$HOME/.codex/skills|.agents/skills|$HOME/.codex|codex|high
cursor|Cursor|$HOME/.cursor/skills|.cursor/skills|$HOME/.cursor|cursor-agent|high
copilot|GitHub Copilot|$HOME/.copilot/skills|.github/skills|$HOME/.copilot|copilot|high
gemini|Gemini CLI|$HOME/.gemini/skills|.gemini/skills|$HOME/.gemini|gemini|high
antigravity|Antigravity|$HOME/.gemini/antigravity/skills|.agent/skills|$HOME/.gemini/antigravity||medium
opencode|OpenCode|$HOME/.config/opencode/skill|.opencode/skill|$HOME/.config/opencode|opencode|medium
amp|Amp|$HOME/.config/agents/skills|.agents/skills|$HOME/.config/amp|amp|medium
windsurf|Windsurf|$HOME/.codeium/windsurf/skills|.windsurf/skills|$HOME/.codeium/windsurf||medium
roo|Roo Code|$HOME/.roo/skills|.roo/skills|$HOME/.roo||medium
kilo|Kilo Code|$HOME/.kilocode/skills|.kilocode/skills|$HOME/.kilocode||medium
goose|Goose|$HOME/.config/goose/skills|.goose/skills|$HOME/.config/goose|goose|medium
droid|Factory Droid|$HOME/.factory/skills|.factory/skills|$HOME/.factory|droid|medium
qwen|Qwen Code|$HOME/.qwen/skills|.qwen/skills|$HOME/.qwen|qwen|medium
cline|Cline|$HOME/.cline/skills|.cline/skills|$HOME/.cline||low
kiro|Kiro|$HOME/.kiro/skills|.kiro/skills|$HOME/.kiro|kiro|low
crush|Crush|$HOME/.config/crush/skills|.crush/skills|$HOME/.config/crush|crush|low
continue|Continue|$HOME/.continue/skills|.continue/skills|$HOME/.continue||low
junie|Junie|$HOME/.junie/skills|.junie/skills|$HOME/.junie||low
augment|Augment|$HOME/.augment/skills|.augment/skills|$HOME/.augment||low
trae|Trae|$HOME/.trae/skills|.trae/skills|$HOME/.trae||low
TABLE
}

usage() {
    cat <<USAGE
install.sh $VERSION - install the $SOURCE_REPO skills into your AI coding agents

  curl -fsSL https://raw.githubusercontent.com/$SOURCE_REPO/main/install.sh | sh -s -- [options]

Options:
  --all               every agent in the table, not only the detected ones
  --agents a,b,c      only these agent ids (see --list); repeatable
  --project           install into the current repository instead of \$HOME
  --dir PATH          install into this skills directory (repeatable)
  --skill NAME        only this skill from the repository (repeatable)
  --ref REF           branch, tag or commit to download (default: main)
  --from DIR          use a local skills/ folder instead of downloading
  --link              symlink agents to the shared store instead of copying
  --force             replace folders that were not installed by this script
  --uninstall         remove everything this script installed
  --dry-run           print every action, change nothing
  --list              print the agent table with detection results
  --quiet             only warnings and errors
  --version           print the script version
  -h, --help          this text

Environment: SKILLS_REF, SKILLS_AGENTS, SKILLS_ALL=1, SKILLS_LINK=1.
USAGE
}

field() { printf '%s' "$1" | cut -d'|' -f"$2"; }

main() {
    set -eu

    REF="${SKILLS_REF:-main}"
    MODE="install"
    SCOPE="global"
    SELECT="detected"
    AGENT_LIST="${SKILLS_AGENTS:-}"
    [ -n "$AGENT_LIST" ] && SELECT="list"
    [ "${SKILLS_ALL:-0}" = "1" ] && SELECT="all"
    LINK="${SKILLS_LINK:-0}"
    ACTION=""
    FORCE=0
    DRY_RUN=0
    QUIET=0
    FROM_DIR=""
    CUSTOM_DIRS=""
    ONLY_SKILLS=""

    while [ $# -gt 0 ]; do
        case "$1" in
            --all) SELECT="all" ;;
            --agents) [ $# -ge 2 ] || die "--agents needs a value"; SELECT="list"; AGENT_LIST="$AGENT_LIST,$2"; shift ;;
            --agents=*) SELECT="list"; AGENT_LIST="$AGENT_LIST,${1#--agents=}" ;;
            --project) SCOPE="project" ;;
            --dir) [ $# -ge 2 ] || die "--dir needs a value"; CUSTOM_DIRS="$CUSTOM_DIRS
$2"; shift ;;
            --dir=*) CUSTOM_DIRS="$CUSTOM_DIRS
${1#--dir=}" ;;
            --skill) [ $# -ge 2 ] || die "--skill needs a value"; ONLY_SKILLS="$ONLY_SKILLS $2"; shift ;;
            --skill=*) ONLY_SKILLS="$ONLY_SKILLS ${1#--skill=}" ;;
            --ref) [ $# -ge 2 ] || die "--ref needs a value"; REF="$2"; shift ;;
            --ref=*) REF="${1#--ref=}" ;;
            --from) [ $# -ge 2 ] || die "--from needs a value"; FROM_DIR="$2"; shift ;;
            --from=*) FROM_DIR="${1#--from=}" ;;
            --link) LINK=1 ;;
            --copy) LINK=0 ;;
            --force) FORCE=1 ;;
            --uninstall|--remove) MODE="uninstall" ;;
            --dry-run|-n) DRY_RUN=1 ;;
            --list) MODE="list" ;;
            --quiet|-q) QUIET=1 ;;
            --version) printf '%s\n' "$VERSION"; return 0 ;;
            -h|--help) usage; return 0 ;;
            *) die "unknown option: $1 (try --help)" ;;
        esac
        shift
    done

    if [ -z "${HOME:-}" ]; then
        if [ "$SCOPE" = "global" ] && [ -z "$CUSTOM_DIRS" ] && [ "$MODE" != "list" ]; then
            die "HOME is not set; set it, or use --project or --dir PATH"
        fi
        HOME=""
    fi
    if [ "$SCOPE" = "project" ]; then
        STORE="$PWD/.agents/skills"
    else
        STORE="$HOME/.agents/skills"
    fi
    if [ "$LINK" -eq 1 ] && [ "$SCOPE" = "project" ]; then
        warn "--link is ignored with --project: project installs are copies so the repository stays portable"
        LINK=0
    fi

    case "$MODE" in
        list) do_list ;;
        uninstall) do_uninstall ;;
        install) do_install ;;
    esac
}

# --- output -----------------------------------------------------------------

say() { [ "$QUIET" -eq 1 ] || printf '%s\n' "$*"; }
warn() { printf 'warning: %s\n' "$*" >&2; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

run() {
    if [ "$DRY_RUN" -eq 1 ]; then
        printf '  would: %s\n' "$*"
    else
        "$@"
    fi
}

# --- detection --------------------------------------------------------------

detected() {
    # $1 = probe dir, $2 = probe binary
    [ "$2" = "always" ] && return 0
    [ -n "$1" ] && [ -d "$1" ] && return 0
    [ -n "$2" ] && command -v "$2" >/dev/null 2>&1 && return 0
    return 1
}

selected_agents() {
    agents_table | while IFS= read -r row; do
        id="$(field "$row" 1)"
        probe_dir="$(field "$row" 5)"
        probe_bin="$(field "$row" 6)"
        case "$SELECT" in
            all) printf '%s\n' "$row" ;;
            list)
                case ",$AGENT_LIST," in
                    *",$id,"*) printf '%s\n' "$row" ;;
                    *) if [ "$id" = "agents" ]; then printf '%s\n' "$row"; fi ;;
                esac ;;
            *) if detected "$probe_dir" "$probe_bin"; then printf '%s\n' "$row"; fi ;;
        esac
    done
}

do_list() {
    printf '%-12s %-26s %-9s %-11s %s\n' "id" "agent" "found" "confidence" "global skills dir"
    agents_table | while IFS= read -r row; do
        if detected "$(field "$row" 5)" "$(field "$row" 6)"; then found="yes"; else found="-"; fi
        printf '%-12s %-26s %-9s %-11s %s\n' "$(field "$row" 1)" "$(field "$row" 2)" "$found" "$(field "$row" 7)" "$(field "$row" 3)"
    done
}

# --- ownership --------------------------------------------------------------

ours() {
    # A path this script may replace or remove: a directory carrying our
    # .skill-meta marker, or a symlink into the store whose target carries it.
    # A symlink someone else made into ~/.agents/skills is not ours.
    target="$1"
    if [ -L "$target" ]; then
        link="$(readlink "$target")"
        case "$link" in
            "$STORE"/*) ;;
            *) return 1 ;;
        esac
        [ -f "$link/.skill-meta" ] || return 1
        grep -q "^source=$SOURCE_REPO$" "$link/.skill-meta" 2>/dev/null
        return $?
    fi
    [ -f "$target/.skill-meta" ] || return 1
    grep -q "^source=$SOURCE_REPO$" "$target/.skill-meta" 2>/dev/null
}

checksum() {
    # A content checksum of a skill folder, marker excluded.
    (cd "$1" && find . -type f ! -name .skill-meta ! -name '*.pyc' ! -path '*/__pycache__/*' | LC_ALL=C sort | while IFS= read -r f; do
        printf '%s\n' "$f"; cat "$f"
    done | cksum | cut -d' ' -f1)
}

installed_checksum() {
    [ -f "$1/.skill-meta" ] && sed -n 's/^checksum=//p' "$1/.skill-meta" | head -n 1
}

write_meta() {
    # $1 = target dir, $2 = checksum
    [ "$DRY_RUN" -eq 1 ] && return 0
    {
        printf 'source=%s\n' "$SOURCE_REPO"
        printf 'ref=%s\n' "$REF"
        printf 'installed_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date)"
        printf 'checksum=%s\n' "$2"
        printf 'installer_version=%s\n' "$VERSION"
    } > "$1/.skill-meta"
}

copy_skill() {
    # $1 = source skill dir, $2 = destination dir, $3 = checksum. Sets ACTION.
    src="$1"; dst="$2"; sum="$3"
    if [ -e "$dst" ] || [ -L "$dst" ]; then
        if ours "$dst"; then
            if [ ! -L "$dst" ] && [ "$(installed_checksum "$dst")" = "$sum" ]; then
                ACTION="up-to-date"
                return 0
            fi
            run rm -rf "$dst"
            ACTION="updated"
        elif [ "$FORCE" -eq 1 ]; then
            run rm -rf "$dst"
            ACTION="replaced"
        else
            ACTION="SKIPPED (exists, not installed by this script; use --force)"
            return 0
        fi
    else
        ACTION="installed"
    fi
    run mkdir -p "$(dirname "$dst")"
    if [ "$DRY_RUN" -eq 0 ]; then
        cp -R "$src" "$dst"
        find "$dst" -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
        write_meta "$dst" "$sum"
    fi
}

link_skill() {
    # $1 = store skill dir, $2 = destination, $3 = checksum. Sets ACTION; falls back to a copy.
    src="$1"; dst="$2"; sum="$3"
    if [ -e "$dst" ] || [ -L "$dst" ]; then
        if ours "$dst"; then
            if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
                ACTION="up-to-date"
                return 0
            fi
            run rm -rf "$dst"
        elif [ "$FORCE" -eq 1 ]; then
            run rm -rf "$dst"
        else
            ACTION="SKIPPED (exists, not installed by this script; use --force)"
            return 0
        fi
    fi
    run mkdir -p "$(dirname "$dst")"
    if [ "$DRY_RUN" -eq 1 ]; then
        run ln -s "$src" "$dst"
        ACTION="linked"
        return 0
    fi
    if ln -s "$src" "$dst" 2>/dev/null; then
        ACTION="linked"
    else
        cp -R "$src" "$dst" && write_meta "$dst" "$sum"
        ACTION="copied (symlinks unavailable)"
    fi
}

# --- source -----------------------------------------------------------------

TMP=""
cleanup() { if [ -n "$TMP" ]; then rm -rf "$TMP"; fi; return 0; }

fetch_source() {
    # Sets SRC to a directory containing <skill>/SKILL.md folders.
    if [ -n "$FROM_DIR" ]; then
        SRC="$FROM_DIR"
        [ -d "$SRC" ] || die "no such directory: $SRC"
        return 0
    fi
    TMP="$(mktemp -d 2>/dev/null || mktemp -d "${TMPDIR:-/tmp}/skills.XXXXXX" 2>/dev/null)" || true
    if [ -z "$TMP" ] || [ ! -d "$TMP" ]; then
        die "could not create a temporary directory (check TMPDIR)"
    fi
    trap cleanup EXIT INT TERM
    url="https://codeload.github.com/$SOURCE_REPO/tar.gz/$REF"
    say "Downloading $SOURCE_REPO@$REF ..."
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "$url" -o "$TMP/src.tar.gz" || die "download failed: $url"
    elif command -v wget >/dev/null 2>&1; then
        wget -q "$url" -O "$TMP/src.tar.gz" || die "download failed: $url"
    else
        die "need curl or wget. Alternative: git clone --depth 1 https://github.com/$SOURCE_REPO && cp -R $(basename "$SOURCE_REPO")/skills/* ~/.agents/skills/"
    fi
    mkdir -p "$TMP/src"
    tar -xzf "$TMP/src.tar.gz" -C "$TMP/src" || die "could not extract the download"
    SRC="$(find "$TMP/src" -maxdepth 2 -type d -name skills | head -n 1)"
    [ -n "$SRC" ] || die "the download has no skills/ folder (ref $REF)"
    find "$SRC" \( -name __pycache__ -o -name '*.pyc' \) -exec rm -rf {} + 2>/dev/null || true
}

skill_names() {
    # Every <name>/SKILL.md under SRC, filtered by --skill when given.
    for dir in "$SRC"/*/; do
        [ -f "$dir/SKILL.md" ] || continue
        name="$(basename "$dir")"
        if [ -n "$ONLY_SKILLS" ]; then
            case " $ONLY_SKILLS " in
                *" $name "*) ;;
                *) continue ;;
            esac
        fi
        printf '%s\n' "$name"
    done
}

# --- install ----------------------------------------------------------------

do_install() {
    fetch_source
    names="$(skill_names)"
    [ -n "$names" ] || die "no skills found in $SRC"

    if [ -n "$CUSTOM_DIRS" ]; then
        printf '%s\n' "$CUSTOM_DIRS" | while IFS= read -r dir; do
            [ -n "$dir" ] || continue
            for name in $names; do
                sum="$(checksum "$SRC/$name")"
                copy_skill "$SRC/$name" "$dir/$name" "$sum"
                say "  $name -> $dir/$name: $ACTION"
            done
        done
        say "Done."
        return 0
    fi

    say "Skills: $(printf '%s\n' "$names" | tr '\n' ' ')"
    say "Store:  $STORE"
    skipped=""
    for name in $names; do
        sum="$(checksum "$SRC/$name")"
        copy_skill "$SRC/$name" "$STORE/$name" "$sum"
        say "  $name: $ACTION"
        case "$ACTION" in SKIPPED*) skipped="$skipped $name " ;; esac
    done

    rows="$(selected_agents)"
    say "Agents:"
    count=0
    printf '%s\n' "$rows" | while IFS= read -r row; do
        [ -n "$row" ] || continue
        id="$(field "$row" 1)"
        [ "$id" = "agents" ] && continue
        label="$(field "$row" 2)"
        if [ "$SCOPE" = "project" ]; then dir="$PWD/$(field "$row" 4)"; else dir="$(field "$row" 3)"; fi
        [ "$dir" = "$STORE" ] && continue
        for name in $names; do
            sum="$(checksum "$SRC/$name")"
            if [ "$LINK" -eq 1 ] && [ "$SCOPE" = "global" ]; then
                case "$skipped" in
                    *" $name "*) ACTION="SKIPPED (the store copy was not installed by this script; use --force)" ;;
                    *) link_skill "$STORE/$name" "$dir/$name" "$sum" ;;
                esac
            else
                copy_skill "$SRC/$name" "$dir/$name" "$sum"
            fi
            say "  $label: $dir/$name: $ACTION"
        done
    done
    count="$(printf '%s\n' "$rows" | grep -c . || true)"
    if [ "$count" -le 1 ]; then
        warn "no agents detected besides the shared store. Use --all, --agents <ids> or --list."
    fi
    say ""
    say "Installed $(printf '%s\n' "$names" | grep -c .) skill(s) for $count location(s)."
    say "Next: open your agent and say \"design my GitHub profile with github-profile-designer\"."
    say "Update: run this command again.  Remove: add --uninstall."
}

# --- uninstall --------------------------------------------------------------

remove_ours_in() {
    # Remove every skill folder in $1 that this script installed.
    dir="$1"
    [ -d "$dir" ] || return 0
    for entry in "$dir"/*/ "$dir"/*; do
        entry="${entry%/}"
        [ -e "$entry" ] || [ -L "$entry" ] || continue
        case "$entry" in *"/*") continue ;; esac
        if ours "$entry"; then
            run rm -rf "$entry"
            say "  removed $entry"
        fi
    done
}

do_uninstall() {
    say "Removing skills installed from $SOURCE_REPO"
    if [ -n "$CUSTOM_DIRS" ]; then
        printf '%s\n' "$CUSTOM_DIRS" | while IFS= read -r dir; do
            [ -n "$dir" ] && remove_ours_in "$dir"
        done
        say "Done."
        return 0
    fi
    limited=0
    if [ "$SELECT" = "list" ]; then limited=1; else SELECT="all"; fi
    selected_agents | while IFS= read -r row; do
        id="$(field "$row" 1)"
        [ "$id" = "agents" ] && continue
        if [ "$SCOPE" = "project" ]; then dir="$PWD/$(field "$row" 4)"; else dir="$(field "$row" 3)"; fi
        [ "$dir" = "$STORE" ] && continue
        remove_ours_in "$dir"
    done
    if [ "$limited" -eq 0 ]; then
        remove_ours_in "$STORE"
    else
        say "  kept the shared store $STORE (run --uninstall without --agents to remove it)"
    fi
    say "Done. Folders without the .skill-meta marker were left alone."
}

main "$@"
