#!/bin/bash
# Ventures night run — invoked by the capture poller (00-ops/capture/poller.sh) at the
# first awake+AC window of the day, any hour, 7 days/week (no fixed schedule); the
# same-day marker makes repeat invocations a no-op. Built from three nights of hand-run
# wrapper duty. Rules learned the hard way, enforced here:
#   1. ALWAYS run from $VENT — the fence anchors to cwd's project (N-06 attempt 1).
#   2. ALWAYS persist the envelope .result to pm/nights/ — the operator's own report file
#      can be a casualty of the very failure being reported.
#   3. Budget preflight BEFORE invoking — the by-hand wrapper let a 3x-over-cap run through.
set -u
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

VENT="${LOOPS_HOME:-$HOME/ventures}"
OPS="$VENT/00-ops/night"
# NIGHT_*_OVERRIDE vars exist for forced-test probes only (same pattern as CAPTURE_*)
STATE="${NIGHT_STATE_OVERRIDE:-$OPS/run-state.json}"
LEDGER="${NIGHT_LEDGER_OVERRIDE:-$OPS/cost-ledger.jsonl}"
ALERT_FILE="$OPS/ALERT.md"
CHARTER="$VENT/pm/CHARTER.md"
ORDERS="${NIGHT_ORDERS_OVERRIDE:-$VENT/pm/ORDERS.md}"
LOOPS="${NIGHT_LOOPS_OVERRIDE:-$VENT/pm/LOOPS.md}"
LOOPSTATE_DIR="${NIGHT_LOOPSTATE_DIR:-$VENT/pm/nights/loops}"
TODAY="$(date +%F)"
LOG="$OPS/logs/$TODAY.log"
CLAUDE_BIN="${CLAUDE_BIN:-$(command -v claude || echo "$HOME/.local/bin/claude")}"
mkdir -p "$OPS/logs"
cd "$VENT" || exit 1   # rule 1

dial() { sed -n "s/^- $1: *//p" "$CHARTER" | head -1 | sed 's/[[:space:]]*#.*//; s/[[:space:]]*$//'; }
MODEL="$(dial model)";                 MODEL="${MODEL:-claude-fable-5}"
EFFORT="$(dial effort)";               EFFORT="${EFFORT:-medium}"
TMIN="$(dial timeout_minutes)";        TIMEOUT_SECS=$(( ${TMIN:-75} * 60 ))
CAP_NIGHT="$(dial cost_cap_per_night_usd)";   CAP_NIGHT="${CAP_NIGHT:-15}"
# charter v2 renamed the weekly cap to rolling_7day; accept either name
CAP_WEEK="$(dial cost_cap_rolling_7day_usd)"
[ -z "$CAP_WEEK" ] && CAP_WEEK="$(dial cost_cap_per_week_usd)"
CAP_WEEK="${CAP_WEEK:-45}"
CAP_MONTH="$(dial monthly_cost_cap_usd)";     CAP_MONTH="${CAP_MONTH:-120}"
NPN="$(dial night_orders_per_night)";         NPN="${NPN:-2}"
PAUSED="$(dial paused)"
PLAN_FLOOR="$(dial plan_floor_percent)";       PLAN_FLOOR="${PLAN_FLOOR:-20}"
FIVE_HOUR_MAX="$(dial five_hour_max_percent)"; FIVE_HOUR_MAX="${FIVE_HOUR_MAX:-90}"
QUOTA="$OPS/quota.py"
AGENT="$(dial agent)";                 AGENT="${AGENT:-claude}"

note() { echo "[wrapper] $(date '+%F %T') $*" >>"$LOG"; }

write_state() { # status rc cost note
  printf '{"date":"%s","status":"%s","rc":%d,"cost_usd":%s,"note":"%s","log":"logs/%s.log","finished":"%s"}\n' \
    "$TODAY" "$1" "$2" "$3" "$4" "$TODAY" "$(date '+%F %T')" >"$STATE"
}

alert() { # headline detail
  { echo "# NIGHT RUN ALERT — $TODAY"; echo; echo "$1"; echo; echo "$2"; echo
    echo "Log:   $LOG"; echo "State: $STATE"; echo
    echo "_The morning meeting reads this first. Delete this file once acknowledged._"
  } >"$ALERT_FILE"
  /usr/bin/osascript -e "display notification \"$1\" with title \"Ventures night run\" subtitle \"$TODAY\" sound name \"Basso\"" >/dev/null 2>&1
}

run_with_timeout() { # secs outfile cmd...
  local secs="$1" out="$2"; shift 2
  local pid waited=0 rc=0
  "$@" >"$out" 2>&1 &
  pid=$!
  while kill -0 "$pid" 2>/dev/null; do
    if [ "$waited" -ge "$secs" ]; then
      echo "[wrapper] timeout after ${secs}s — killing $pid" >>"$out"
      kill "$pid" 2>/dev/null; sleep 5; kill -9 "$pid" 2>/dev/null
      rc=124; break
    fi
    sleep 15; waited=$((waited + 15))
  done
  [ "$rc" -eq 0 ] && { wait "$pid"; rc=$?; }
  return "$rc"
}

# ---- agent adapter (claude | codex): agent_canary, agent_run, agent_relogin_hint ----
if [ ! -f "$OPS/agents/$AGENT.sh" ]; then
  echo "[wrapper] unknown agent '$AGENT' (no $OPS/agents/$AGENT.sh)" >>"$LOG"; exit 1
fi
# shellcheck source=/dev/null
. "$OPS/agents/$AGENT.sh"

# ---- guards -------------------------------------------------------------
[ "$PAUSED" = "yes" ] && exit 0
# terminal-for-the-day statuses never re-run or re-alert on repeat invocations;
# failed/auth-failed stay retryable (a later same-day capture window may succeed)
if [ -f "$STATE" ] && grep -q "\"$TODAY\"" "$STATE" && grep -qE '"status":"(ok|no-orders|budget-stop|skipped-quota)"' "$STATE"; then
  exit 0
fi
# orders + runnable loops (Loops v1). The wrapper is the sole
# authority on loop runnability: cadence, budget-by-iteration-count, and the
# two-consecutive-no-progress auto-park are all decided here, deterministically.
PENDING="$(awk '/^## Tonight/{f=1;next} /^## /{f=0} f' "$ORDERS" | grep -c '^- \[ \]' || true)"
LOOPCHECK="$(python3 - "$LOOPS" "$LOOPSTATE_DIR" "$ORDERS" "$CAP_NIGHT" "$TODAY" "$PENDING" "$NPN" <<'PYEOF'
import re,sys,os,datetime
loops_f,state_dir,orders_f,cap_night,today_s,pending_s,npn_s=sys.argv[1:8]
cap_night=float(cap_night); today=datetime.date.fromisoformat(today_s)
slots=max(0,int(npn_s)-int(pending_s))  # orders outrank loops; both count against npn
def out(runnable,skips):
    print("runnable:"+(" ".join(runnable) if runnable else " none"))
    for s in skips: print("skip: "+s)
try: orders=open(orders_f).read()
except FileNotFoundError: orders=""
tonight=re.search(r"^## Tonight.*?(?=^## |\Z)",orders,re.M|re.S)
if tonight and re.search(r"^loops: *off",tonight.group(0),re.M):
    out([],["ALL loops: off in Tonight section"]); sys.exit()
try: text=open(loops_f).read()
except FileNotFoundError:
    out([],[]); sys.exit()
text=re.sub(r"<!--.*?-->","",text,flags=re.S)  # commented-out loops are not loops
cadence_n={"nightly":1,"every-2nd-night":2,"every-3rd-night":3,"weekly":7}
runnable,skips=[],[]
for m in re.finditer(r"^## (L-\d+)[^\n]*\n(.*?)(?=^## |\Z)",text,re.M|re.S):
    lid,body=m.group(1),m.group(2)
    def field(k,d=""):
        f=re.search(r"^- %s: *(.+)$"%k,body,re.M); return f.group(1).strip() if f else d
    if not field("status").startswith("active"):
        skips.append(f"{lid} status={field('status')[:30] or 'missing'}"); continue
    n=cadence_n.get(field("cadence"))
    try:
        per=float(field("budget_per_iteration_usd")); tot=float(field("budget_loop_total_usd"))
    except ValueError: per=tot=0
    if not n or per<=0 or tot<=0 or per>cap_night:
        skips.append(f"{lid} misconfigured (cadence/budget fields)"); continue
    rb=field("review_by")
    try:
        if datetime.date.fromisoformat(rb)<=today:
            skips.append(f"{lid} past review_by {rb}"); continue
    except ValueError:
        skips.append(f"{lid} missing/bad review_by"); continue
    sects=[]
    try:
        st=open(os.path.join(state_dir,lid+".md")).read()
        sects=re.findall(r"^## (\d{4}-\d{2}-\d{2})[^\n]*\n(.*?)(?=^## |\Z)",st,re.M|re.S)
    except FileNotFoundError: pass
    if len(sects)>=int(tot//per):
        skips.append(f"{lid} loop budget exhausted ({len(sects)} iterations x ${per})"); continue
    if len(sects)>=2 and all(re.search(r"^progress: *no",b,re.M) for _,b in sects[-2:]):
        skips.append(f"{lid} auto-parked: 2 consecutive progress:no"); continue
    if sects:
        last=datetime.date.fromisoformat(sects[-1][0])
        if (today-last).days<n:
            skips.append(f"{lid} not due (last {last}, cadence {field('cadence')})"); continue
    if len(runnable)>=slots:
        skips.append(f"{lid} due but no slot ({pending_s} orders fill night_orders_per_night={npn_s})"); continue
    runnable.append(lid)
out(runnable,skips)
PYEOF
)"
RUNNABLE="$(printf '%s\n' "$LOOPCHECK" | sed -n 's/^runnable: *//p')"
[ "$RUNNABLE" = "none" ] && RUNNABLE=""
printf '%s\n' "$LOOPCHECK" | grep '^skip:' | while read -r l; do note "loopcheck $l"; done
if [ "${PENDING:-0}" -eq 0 ] && [ -z "$RUNNABLE" ]; then
  note "no unchecked Tonight orders and no runnable loops — skipping"
  write_state "no-orders" 0 0 "no unchecked orders, no runnable loops"
  rm -f "$ALERT_FILE"
  exit 0
fi
# budget preflight (rule 3): week + month sums, and two-consecutive-overrun pause
BUDGET="$(python3 - "$LEDGER" "$CAP_NIGHT" "$CAP_WEEK" "$CAP_MONTH" <<'PYEOF'
import json,sys,datetime
led,capn,capw,capm=sys.argv[1],float(sys.argv[2]),float(sys.argv[3]),float(sys.argv[4])
rows=[]
try:
    rows=[json.loads(l) for l in open(led) if l.strip()]
except FileNotFoundError: pass
today=datetime.date.today()
def d(r): return datetime.date.fromisoformat(r["date"])
wk=sum(r["cost_usd"] for r in rows if (today-d(r)).days<7)
mo=sum(r["cost_usd"] for r in rows if r["date"][:7]==today.strftime("%Y-%m"))
over2=len(rows)>=2 and all(r["cost_usd"]>capn for r in rows[-2:])
if over2: print(f"stop two-consecutive-overruns last2>{capn}")
elif wk>=capw: print(f"stop week {wk:.2f}>={capw}")
elif mo>=capm: print(f"stop month {mo:.2f}>={capm}")
else: print(f"ok wk={wk:.2f} mo={mo:.2f}")
PYEOF
)"
if [ "${BUDGET%% *}" = "stop" ]; then
  write_state "budget-stop" 0 0 "$BUDGET"
  alert "Night run SKIPPED — budget" "$BUDGET. Adjust caps in pm/CHARTER.md to resume."
  exit 0
fi
# plan floor: never eat the part of the week the operator wants for themselves.
# Uses the CLI's cached utilization if it is under 12h old; if there is no cache, no gate.
if [ -f "$QUOTA" ] && [ "$AGENT" = claude ]; then
  QGATE="$(LOOPS_HOME="$VENT" python3 "$QUOTA" status 2>/dev/null)"
  QREASON="$(python3 - "$QGATE" "$PLAN_FLOOR" "$FIVE_HOUR_MAX" <<'PYEOF'
import json,sys
s=json.loads(sys.argv[1] or "{}"); floor=float(sys.argv[2]); fmax=float(sys.argv[3])
if not s.get("available") or s.get("age_h") is None or s["age_h"]>12: sys.exit()
w=s.get("week_pct"); f=s.get("five_hour_pct")
if w is not None and 100-w < floor: print(f"week {w:g}% used, under the {floor:g}% floor you keep for yourself; resets {s.get('week_resets_at')}")
elif f is not None and f > fmax: print(f"five-hour window {f:g}% used (max {fmax:g}%); resets {s.get('five_hour_resets_at')}")
PYEOF
)"
  if [ -n "$QREASON" ]; then
    note "skipped: $QREASON"
    write_state "skipped-quota" 0 0 "$QREASON"
    exit 0
  fi
fi
# silent AC backstop: the poller only invokes on AC; this catches the unplug race.
# No alert — the next capture window retries, and the absence watchdog owns silence.
POWER=battery; pmset -g batt | grep -q "AC Power" && POWER=ac
POWER="${NIGHT_POWER_OVERRIDE:-$POWER}"
if [ "$POWER" = battery ]; then
  write_state "skipped-power" 0 0 "raced off AC"
  exit 0
fi
note "starting (model=$MODEL effort=$EFFORT timeout=${TIMEOUT_SECS}s orders=$PENDING loops=${RUNNABLE:-none} $BUDGET power=$POWER)"
# probe hook: forced tests stop here — guards exercised, no claude invocation, no spend.
# "probe-ok" is NOT a terminal status, so a probe never blocks the real run that day.
if [ "${NIGHT_PROBE:-0}" = "1" ]; then
  write_state "probe-ok" 0 0 "probe: would run orders=$PENDING loops=${RUNNABLE:-none}"
  exit 0
fi

# ---- auth canary --------------------------------------------------------
CANARY="$(mktemp)"
agent_canary "$CANARY"
if ! grep -q READY "$CANARY"; then
  note "auth canary FAILED: $(tail -2 "$CANARY" | tr '\n' ' ')"
  cat "$CANARY" >>"$LOG"; rm -f "$CANARY"
  write_state "auth-failed" 1 0 "canary failed"
  alert "Auth preflight FAILED — night skipped" "$(agent_relogin_hint)"
  exit 1
fi
rm -f "$CANARY"

# ---- git: umbrella stays on main; nested venture repos get night branches
snapshot_repo() { # dir
  local d="$1"
  [ -d "$d/.git" ] || return 0
  if [ -n "$(git -C "$d" status --porcelain)" ]; then
    git -C "$d" add -A
    git -C "$d" -c user.name="${NIGHT_GIT_NAME:-night-snapshot}" -c user.email="${NIGHT_GIT_EMAIL:-night@local}" \
      commit -q -m "pre-night snapshot $(date '+%F %T')"
  fi
  git -C "$d" switch -q -c "night/$TODAY" 2>/dev/null || git -C "$d" switch -q "night/$TODAY"
}
commit_repo() { # dir label
  local d="$1"
  [ -d "$d/.git" ] || return 0
  if [ -n "$(git -C "$d" status --porcelain)" ]; then
    git -C "$d" add -A
    git -C "$d" -c user.name="ventures-night" -c user.email="night@local" \
      commit -q -m "night run $TODAY${2:+: $2}"
    note "committed in $d: $(git -C "$d" log --oneline -1)"
  fi
}
NESTED=""
for d in "$VENT"/0*-*/; do
  [ -d "$d/.git" ] && { snapshot_repo "$d"; NESTED="$NESTED $d"; }
done
# ventures whose site is its own nested repo (deploys from a push you make by hand)
for d in "$VENT"/0*-*/site/; do
  [ -d "$d/.git" ] && { snapshot_repo "$d"; NESTED="$NESTED $d"; }
done

# ---- the run ------------------------------------------------------------
LAST_ATT="$(mktemp)"; START=$(date +%s)
PROMPT_FILE="$(mktemp)"
{ cat "$OPS/night-prompt.md"; echo; echo "[wrapper] Today is $TODAY. Runnable loops tonight, cadence and budgets already enforced: ${RUNNABLE:-none}."; } >"$PROMPT_FILE"
run_agent() {
  agent_run "$LAST_ATT" "$PROMPT_FILE" "$MODEL" "$EFFORT" "$TIMEOUT_SECS"
  local rc=$?; cat "$LAST_ATT" >>"$LOG"; return $rc
}
PRIOR_COST=0
note "agent=$AGENT"
run_agent; rc=$?
if [ "$rc" -ne 0 ] && [ "$rc" -ne 124 ]; then
  PRIOR_COST="$(jq -r '.total_cost_usd // 0' "$LAST_ATT" 2>/dev/null || echo 0)"
  note "attempt 1 failed (rc=$rc, cost=\$$PRIOR_COST) — retrying once"
  run_agent; rc=$?
fi
ELAPSED=$(( $(date +%s) - START ))

COST="$(jq -r '.total_cost_usd // 0' "$LAST_ATT" 2>/dev/null || echo 0)"
# attempt 1's spend is real quota burn even though attempt 2 overwrote its envelope
COST="$(python3 -c "print(round(${PRIOR_COST:-0}+${COST:-0},6))" 2>/dev/null || echo "$COST")"
jq -r '.result // empty' "$LAST_ATT" >"$VENT/pm/nights/$TODAY-envelope.md" 2>/dev/null   # rule 2

if [ "$rc" -eq 0 ] && grep -q "NIGHT-BLOCKED" "$LAST_ATT"; then status=blocked; rc=2
elif [ "$rc" -eq 0 ]; then status=ok
else status=failed; fi
rm -f "$LAST_ATT"

# ---- git: land the night's work ----------------------------------------
for d in $NESTED; do commit_repo "$d" ""; done
commit_repo "$VENT" "pm state + reports"

printf '{"date":"%s","cost_usd":%s,"secs":%d,"status":"%s","finished":"%s","model":"%s"}\n' "$TODAY" "$COST" "$ELAPSED" "$status" "$(date '+%F %T')" "$MODEL" >>"$LEDGER"
# the morning line: dollars, the share of the week they are worth, and where the week stands
if [ -f "$QUOTA" ]; then
  QLINE="$(LOOPS_HOME="$VENT" python3 "$QUOTA" line --usd "$COST" --model "$MODEL" 2>/dev/null)"
  [ -n "$QLINE" ] && { note "quota: $QLINE"; [ -f "$VENT/pm/nights/$TODAY.md" ] && printf '\n_%s_\n' "$QLINE" >>"$VENT/pm/nights/$TODAY.md"; }
fi
write_state "$status" "$rc" "$COST" "elapsed=${ELAPSED}s"
note "finished status=$status rc=$rc cost=\$$COST elapsed=${ELAPSED}s"
OVER=""
awk -v c="$COST" -v cap="$CAP_NIGHT" 'BEGIN{exit !(c>cap)}' && OVER=" (OVER the \$$CAP_NIGHT/night cap)"
if [ "$status" != "ok" ]; then
  alert "Night run $status (rc=$rc)" "Cost \$$COST$OVER. Work is on the night/$TODAY branches; nothing merged."
else
  rm -f "$ALERT_FILE"
fi
exit "$rc"
