#!/bin/bash
# Ventures absence watchdog — hourly (com.ventures.capture-watchdog, StartInterval 3600,
# RunAtLoad true). Law 4: the alarm lives outside the thing it watches.
#
# Charter v2 (variable presence): alarms are OPPORTUNITY-BASED, never calendar-based.
# Raw days-of-silence cannot distinguish deliberate rest from a dead system, and a month
# of variable presence is full of deliberate rest. Two conditions alarm; everything else is legal silence:
#   1. POLLER DEAD — this watchdog observes a live AC window right now, but the poller
#      (10-min interval) hasn't stamped last-ac today. Caught within the hour.
#   2. WRAPPER HUNG — a lane was invoked on a previous day (attempts file) but its
#      run-state never concluded that day. Caught next day.
# A closed laptop in a drawer for a week alarms no one.
# WATCH_*/CAPTURE_DIR env overrides exist for forced tests only.
set -u
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

VENT="${LOOPS_HOME:-$HOME/ventures}"
CAP="${CAPTURE_DIR:-$VENT/00-ops/capture}"
TODAY="$(date +%F)"
mkdir -p "$CAP"

alert() { # stamp-key alert-file title body...
  local key="$1" alert_file="$2" title="$3"; shift 3
  local stamp="$CAP/last-absence-alert-$key"
  [ "$(cat "$stamp" 2>/dev/null)" = "$TODAY" ] && return 1   # one alert per key per day
  { echo "# $title — $TODAY (absence watchdog)"; echo
    for line in "$@"; do echo "$line"; done; echo
    echo "Poller log: $CAP/logs/poller.log"
    echo "_Hourly opportunity-based watchdog (capture/watchdog-absence.sh). Delete once acknowledged._"
  } >"$alert_file"
  echo "$TODAY" >"$stamp"
  /usr/bin/osascript -e "display notification \"$title\" with title \"Ventures capture\" subtitle \"$TODAY\" sound name \"Basso\"" >/dev/null 2>&1
  return 0
}

rc=0

# ---- 1. poller-dead: live window observed, poller not stamping -----------------
# Only meaningful on AC (the poller always stamps last-ac when on AC). Require >30 min
# of uptime so a fresh boot's RunAtLoad race can't false-alarm.
uptime_secs() {
  local boot; boot="$(sysctl -n kern.boottime 2>/dev/null | sed -E 's/.*sec = ([0-9]+).*/\1/')"
  [ -n "$boot" ] && echo $(( $(date +%s) - boot )) || echo 0
}
if pmset -g batt | grep -q "AC Power" && [ "$(uptime_secs)" -gt 1800 ]; then
  if [ "$(cat "$CAP/last-ac" 2>/dev/null)" != "$TODAY" ] && [ ! -f "$CAP/PAUSED" ]; then
    alert poller "$CAP/ALERT.md" "POLLER DEAD" \
      "The machine is on AC power right now, but the 10-min poller has not stamped last-ac today." \
      "Either launchd job com.ventures.capture is unloaded/broken, or poller.sh is failing before the stamp." \
      "Check: launchctl list | grep ventures.capture" && rc=1
  fi
fi

# ---- 2. wrapper-hung: invoked on a prior day, never concluded ------------------
check_lane() { # lane state-file alert-file title
  local lane="$1" state="$2" alert_file="$3" title="$4"
  local att_date="" att_n="" run_date=""
  read -r att_date att_n 2>/dev/null <"$CAP/$lane.attempts" || true
  [ -n "$att_date" ] || return 0
  [ "$att_date" = "$TODAY" ] && return 0                    # today's run may still be going
  run_date="$(jq -r '.date // empty' "$state" 2>/dev/null)"
  [ "$run_date" = "$att_date" ] && return 0                  # invoked and concluded — healthy
  # concluded later than invoked is also healthy (state date sorts after attempts date)
  [ -n "$run_date" ] && [[ "$run_date" > "$att_date" ]] && return 0
  alert "$lane" "$alert_file" "$title" \
    "The $lane lane was invoked on $att_date (attempt $att_n) but its run-state never concluded that day (state dated ${run_date:-never})." \
    "The wrapper is hanging or dying before writing state." \
    "State: $state" && return 1
  return 0
}

check_lane night \
  "${WATCH_NIGHT_STATE:-$VENT/00-ops/night/run-state.json}" \
  "${WATCH_NIGHT_ALERT:-$VENT/00-ops/night/ALERT.md}" "NIGHT WRAPPER HUNG" || rc=1
check_lane day \
  "${WATCH_DAY_STATE:-$VENT/00-ops/day/run-state.json}" \
  "${WATCH_DAY_ALERT:-$VENT/00-ops/day/ALERT.md}" "DAY WRAPPER HUNG" || rc=1
exit "$rc"
