#!/bin/bash
# Loops installer — productagent.dev
#
#   curl -fsSL https://productagent.dev/install.sh | bash
#
# Lays down the machine (runner, checker, watchdog, health desk, fence, charter) in
# $LOOPS_HOME (default ~/loops), with an EMPTY loops file. It installs the machine,
# not anyone else's loops. Nothing runs until you write a loop with a real review date.
#
# Options / env:
#   LOOPS_HOME=~/somewhere   where to install (default ~/loops)
#   --no-arm                 lay files down but do not load the launchd jobs
#   --no-init                skip the first-loop questions at the end
#   --off                    unload the launchd jobs and exit (files stay)
#   LOOPS_SOURCE=/path       install from a local checkout of harnesses/loops (dev only)
set -euo pipefail

LOOPS_HOME="${LOOPS_HOME:-$HOME/loops}"
LAUNCH_AGENTS="${LAUNCH_AGENTS_DIR:-$HOME/Library/LaunchAgents}"
ARM=1; INIT=1
for a in "$@"; do
  case "$a" in
    --no-arm) ARM=0 ;;
    --no-init) INIT=0 ;;
    --off)
      for l in com.ventures.capture com.ventures.capture-watchdog; do
        launchctl bootout "gui/$(id -u)/$l" 2>/dev/null || true
      done
      echo "Loops: schedule unloaded. Files in $LOOPS_HOME untouched."; exit 0 ;;
    *) echo "unknown option: $a" >&2; exit 2 ;;
  esac
done

say()  { printf '\033[1m%s\033[0m\n' "$*"; }
note() { printf '  %s\n' "$*"; }
die()  { printf 'Loops: %s\n' "$*" >&2; exit 1; }

[ "$(uname -s)" = Darwin ] || die "this machine is built for macOS (launchd, pmset, caffeinate)."
command -v python3 >/dev/null || die "python3 is required."
command -v jq >/dev/null || note "jq not found (brew install jq). The runner needs it before the first real run."
command -v claude >/dev/null || note "claude not found on PATH. Install Claude Code before the first real run."

# ---- fetch ---------------------------------------------------------------
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
if [ -n "${LOOPS_SOURCE:-}" ]; then
  SRC="$LOOPS_SOURCE"
else
  say "Downloading loops"
  curl -fsSL https://codeload.github.com/harrisonhjohnson/productagent/tar.gz/main \
    | tar -xz -C "$TMP" productagent-main/harnesses/loops
  SRC="$TMP/productagent-main/harnesses/loops"
fi
[ -f "$SRC/ops/night/run-night.sh" ] || die "download looked wrong (no runner found)."

# ---- lay out -------------------------------------------------------------
say "Installing to $LOOPS_HOME"
mkdir -p "$LOOPS_HOME"/{.claude,00-ops,pm/nights/loops,docs}
cp -R "$SRC/ops/." "$LOOPS_HOME/00-ops/"                 # machine: always refreshed
find "$LOOPS_HOME/00-ops" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
cp "$SRC"/{README.md,MACHINE.md,loops-spec.md} "$LOOPS_HOME/docs/"
cp "$SRC/install.sh" "$LOOPS_HOME/00-ops/install.sh"
cp "$SRC/init.sh" "$LOOPS_HOME/00-ops/init.sh"
chmod +x "$LOOPS_HOME"/00-ops/*/*.sh "$LOOPS_HOME/00-ops/install.sh" "$LOOPS_HOME/00-ops/init.sh"

keep_or_copy() { # src dst  — never overwrite a file the operator may have edited
  if [ -e "$2" ]; then note "kept   ${2#"$LOOPS_HOME"/}"; else cp "$1" "$2"; note "wrote  ${2#"$LOOPS_HOME"/}"; fi
}
keep_or_copy "$SRC/pm/CHARTER.md"           "$LOOPS_HOME/pm/CHARTER.md"
keep_or_copy "$SRC/pm/templates/LOOPS.md"   "$LOOPS_HOME/pm/LOOPS.md"
keep_or_copy "$SRC/pm/templates/ORDERS.md"  "$LOOPS_HOME/pm/ORDERS.md"

# the fence: Claude Code permission paths are absolute, so fill in this machine's paths
if [ ! -e "$LOOPS_HOME/.claude/settings.json" ]; then
  sed -e "s|/Users/YOU/ventures|$LOOPS_HOME|g" -e "s|/Users/YOU|$HOME|g" \
    "$SRC/settings.json" >"$LOOPS_HOME/.claude/settings.json"
  note "wrote  .claude/settings.json (the fence, with your paths filled in)"
else
  note "kept   .claude/settings.json"
fi

# the runner commits its own state; it needs a repo to commit into
if [ ! -d "$LOOPS_HOME/.git" ]; then
  git -C "$LOOPS_HOME" init -q && note "wrote  .git (the runner commits its reports here)"
fi

# ---- schedule ------------------------------------------------------------
write_plist() { # label script interval
  cat >"$LAUNCH_AGENTS/$1.plist" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$1</string>
  <key>ProgramArguments</key><array><string>/bin/bash</string><string>$LOOPS_HOME/00-ops/capture/$2</string></array>
  <key>EnvironmentVariables</key><dict>
    <key>LOOPS_HOME</key><string>$LOOPS_HOME</string>
    <key>PATH</key><string>$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
  </dict>
  <key>StartInterval</key><integer>$3</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>$LOOPS_HOME/00-ops/capture/logs/$1.out</string>
  <key>StandardErrorPath</key><string>$LOOPS_HOME/00-ops/capture/logs/$1.err</string>
</dict></plist>
PL
}
mkdir -p "$LAUNCH_AGENTS" "$LOOPS_HOME/00-ops/capture/logs"
write_plist com.ventures.capture          poller.sh           600
write_plist com.ventures.capture-watchdog watchdog-absence.sh 3600
note "wrote  ~/Library/LaunchAgents/com.ventures.capture{,-watchdog}.plist"

if [ "$ARM" = 1 ]; then
  for l in com.ventures.capture com.ventures.capture-watchdog; do
    launchctl bootout "gui/$(id -u)/$l" 2>/dev/null || true
    launchctl bootstrap "gui/$(id -u)" "$LAUNCH_AGENTS/$l.plist"
  done
  say "Armed. The checker looks every ten minutes; nothing runs until you write a loop."
else
  say "Files are in place. Schedule not loaded (--no-arm)."
fi

# ---- first loop, if someone is at the keyboard ---------------------------
if [ "$INIT" = 1 ] && { : </dev/tty; } 2>/dev/null; then
  LOOPS_HOME="$LOOPS_HOME" bash "$LOOPS_HOME/00-ops/init.sh"
  exit 0
fi
cat <<TXT

Next, in this order:
  1. Write your first loop     bash $LOOPS_HOME/00-ops/init.sh    (four questions; also trusts the folder for Claude Code)
  2. Plug the laptop in tonight. Read pm/nights/ in the morning.

Read the concept page:   $LOOPS_HOME/docs/README.md
Stop the schedule:       bash $LOOPS_HOME/00-ops/install.sh --off
TXT
