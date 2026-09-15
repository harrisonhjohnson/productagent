#!/bin/bash
# Ventures capture poller — fires every 10 min while the machine is awake
# (com.ventures.capture, StartInterval 600, RunAtLoad true). Fixed-time firing was
# replaced by opportunistic compute capture — a lane runs at the first
# window, any hour, until terminal for the day. The wrappers stay the sole authority on
# gates/budget/state/git; this script decides only WHEN to invoke them.
# Charter v2 (variable presence): BOTH lanes run 7 days/week. Windows differ by
# physics — night requires AC (a lid-closed battery Mac dark-wakes ~30 min and
# caffeinate -s is AC-only: the run dies mid-flight); day runs on AC OR lid-open
# battery >=50% (shorter runs, -i holds lid-open; the cost is drain, not death).
# CAPTURE_* env overrides exist for forced tests only; launchd runs the bare defaults.
set -u
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

VENT="${LOOPS_HOME:-$HOME/ventures}"
CAP="${CAPTURE_DIR:-$VENT/00-ops/capture}"
NIGHT_WRAPPER="${CAPTURE_NIGHT_WRAPPER:-$VENT/00-ops/night/run-night.sh}"
NIGHT_STATE="${CAPTURE_NIGHT_STATE:-$VENT/00-ops/night/run-state.json}"
DAY_WRAPPER="${CAPTURE_DAY_WRAPPER:-$VENT/00-ops/day/run-prospect.sh}"
DAY_STATE="${CAPTURE_DAY_STATE:-$VENT/00-ops/day/run-state.json}"
TODAY="$(date +%F)"
MAX_ATTEMPTS="${CAPTURE_MAX_ATTEMPTS:-2}"   # wrapper invocations per lane per day
DAY_MIN_BATT="${CAPTURE_DAY_MIN_BATT:-50}"  # battery floor for a lid-open day window
mkdir -p "$CAP/logs"

# bounded verb: a "pause" command from any attended surface drops this sentinel; "resume" removes it
[ -f "$CAP/PAUSED" ] && exit 0

log() { echo "[poller] $(date '+%F %T') $*" >>"$CAP/logs/poller.log"; }

# ---- lock (guards manual runs; launchd never double-starts one label) ----
if ! mkdir "$CAP/lock" 2>/dev/null; then
  pid="$(cat "$CAP/lock/pid" 2>/dev/null || true)"
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then exit 0; fi
  log "stealing stale lock (pid=${pid:-none})"
  rm -rf "$CAP/lock"; mkdir "$CAP/lock" 2>/dev/null || exit 0
fi
echo $$ >"$CAP/lock/pid"
trap 'rm -rf "$CAP/lock"' EXIT

# ---- window predicates ---------------------------------------------------
on_ac()    { pmset -g batt | grep -q "AC Power"; }
batt_pct() { pmset -g batt | grep -Eo '[0-9]+%' | head -1 | tr -d '%'; }
lid_open() { ! ioreg -r -k AppleClamshellState -d 4 2>/dev/null | grep -q '"AppleClamshellState" = Yes'; }

night_window() { on_ac; }
day_window()   { # AC, or lid-open battery >= floor (charter v2 relaxed trigger)
  on_ac && return 0
  lid_open || return 1
  local p; p="$(batt_pct)"
  [ -n "$p" ] && [ "$p" -ge "$DAY_MIN_BATT" ]
}

# no window of any kind: a quiet poll is not an event
night_window || day_window || exit 0

# window stamps for the absence watchdog: last-ac = an AC window existed today;
# last-window = any lane-runnable window existed today (incl. lid-open battery)
on_ac && { [ "$(cat "$CAP/last-ac" 2>/dev/null)" = "$TODAY" ] || echo "$TODAY" >"$CAP/last-ac"; }
[ "$(cat "$CAP/last-window" 2>/dev/null)" = "$TODAY" ] || echo "$TODAY" >"$CAP/last-window"

terminal_today() { # state-file terminal-regex
  [ -f "$1" ] && grep -q "\"$TODAY\"" "$1" && grep -qE "$2" "$1"
}

attempts_today() { # lane -> echoes N
  local d="" n=""
  # 2>/dev/null must precede the input redirect: a missing file errors during
  # redirection setup, before a trailing stderr redirect would apply
  read -r d n 2>/dev/null <"$CAP/$1.attempts" || true
  if [ "$d" = "$TODAY" ]; then echo "${n:-0}"; else echo 0; fi
}

run_lane() { # lane wrapper-path state-file terminal-regex
  local lane="$1" wrapper="$2" state="$3" tregex="$4" n
  [ -f "$wrapper" ] || return 0   # a lane without a wrapper is not installed; skip silently
  terminal_today "$state" "$tregex" && return 0
  n="$(attempts_today "$lane")"
  [ "$n" -ge "$MAX_ATTEMPTS" ] && return 0
  echo "$TODAY $((n + 1))" >"$CAP/$lane.attempts"
  log "invoking $lane (attempt $((n + 1))/$MAX_ATTEMPTS)"
  /usr/bin/caffeinate -i -m -s /bin/bash "$wrapper"
  log "$lane wrapper exited rc=$?"
}

# night first, then day — serialized by construction; re-check windows between
# lanes (an unplug mid-night-run must not start a day run the window can't hold)
night_window && run_lane night "$NIGHT_WRAPPER" "$NIGHT_STATE" '"status":"(ok|no-orders|budget-stop)"'
day_window && run_lane day "$DAY_WRAPPER" "$DAY_STATE" '"status":"(ok|budget-stop)"'
exit 0
