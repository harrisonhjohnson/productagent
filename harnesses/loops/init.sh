#!/bin/bash
# Loops · first-loop setup. Runs at the end of install.sh when a terminal is present,
# or any time by hand:  bash ~/loops/00-ops/init.sh
#
# Asks four things, writes one loop, grants the folder trust the fence needs, dry-runs the
# machine, and tells you what will happen tonight. Reads answers from the terminal device,
# so it works even when the script itself arrives through `curl | bash`.
set -u
LOOPS_HOME="${LOOPS_HOME:-$HOME/loops}"
CHARTER="$LOOPS_HOME/pm/CHARTER.md"; LOOPS="$LOOPS_HOME/pm/LOOPS.md"
RUNNER="$LOOPS_HOME/00-ops/night/run-night.sh"

# ---- terminal ------------------------------------------------------------
if ! { : </dev/tty; } 2>/dev/null; then
  echo "Loops: no terminal to ask questions on. Write a loop by hand in $LOOPS and run:"
  echo "  NIGHT_PROBE=1 LOOPS_HOME=$LOOPS_HOME bash $RUNNER"
  exit 0
fi
[ -f "$CHARTER" ] && [ -f "$LOOPS" ] && [ -f "$RUNNER" ] || { echo "Loops: nothing installed at $LOOPS_HOME. Run the installer first."; exit 1; }

B=$'\033[1m'; D=$'\033[2m'; R=$'\033[0m'
say()  { printf '%s\n' "$*" >/dev/tty; }
ask()  { # var prompt default
  local v="$1" p="$2" d="${3:-}" a
  if [ -n "$d" ]; then printf '%s %s[%s]%s ' "$p" "$D" "$d" "$R" >/dev/tty; else printf '%s ' "$p" >/dev/tty; fi
  IFS= read -r a </dev/tty; a="${a:-$d}"; printf -v "$v" '%s' "$a"
}
setdial() { # key value  — replace or append a "- key: value" line in the charter
  if grep -qE "^- $1:" "$CHARTER"; then
    python3 - "$CHARTER" "$1" "$2" <<'PY'
import re,sys; p,k,v=sys.argv[1:4]; s=open(p).read()
s=re.sub(r"^- %s:.*$"%re.escape(k), "- %s: %s"%(k,v), s, count=1, flags=re.M); open(p,'w').write(s)
PY
  else printf -- '- %s: %s\n' "$1" "$2" >>"$CHARTER"; fi
}

say ""
say "${B}Loops · your first loop${R}"
say "${D}Four questions. One file gets written. Nothing runs until tonight, and only if the laptop is plugged in.${R}"
say ""

# ---- 1. which agent ------------------------------------------------------
HAVE_CLAUDE=0; HAVE_CODEX=0
command -v claude >/dev/null && HAVE_CLAUDE=1
command -v codex  >/dev/null && HAVE_CODEX=1
if [ $HAVE_CLAUDE = 1 ] && [ $HAVE_CODEX = 1 ]; then
  say "${B}1 · Which agent runs the night?${R}  ${D}both are installed${R}"
  say "   1) Claude Code   ${D}per-path fence; can read the web${R}"
  say "   2) Codex         ${D}sandbox with the network off; harder no-push, no web${R}"
  ask A "   choose" 1; case "$A" in 2|codex) AGENT=codex ;; *) AGENT=claude ;; esac
elif [ $HAVE_CODEX = 1 ]; then AGENT=codex; say "${B}1 · Agent:${R} Codex ${D}(the only one on PATH)${R}"
else AGENT=claude; say "${B}1 · Agent:${R} Claude Code"; [ $HAVE_CLAUDE = 1 ] || say "   ${D}claude is not on PATH yet. Install Claude Code before tonight.${R}"; fi
say ""

# ---- 2. the goal ---------------------------------------------------------
S_GOAL=(
  "Watch three competitors' changelogs. Tell me what changed and whether it matters."
  "Ship one small fix from the backlog. Verify it renders before you report it."
  "Read yesterday's support tickets. Cluster them. Name the top three themes."
  "Check every box on the launch checklist against the repo. Flag the ones that lie."
  "Draft the weekly update from this week's reports. I edit. I send."
  "Find ten companies that look like our best customer. Say why, with links."
)
S_TITLE=("Competitor changelogs" "One backlog fix a night" "Support ticket themes" "Launch checklist audit" "Weekly update draft" "Lookalike companies")
S_CAD=(weekly every-2nd-night nightly every-2nd-night weekly every-3rd-night)
S_BRAIN=(fast deep fast fast deep fast)
S_BUD=(2 6 3 2 4 3)
say "${B}2 · What should it work on?${R}  ${D}pick a number, or type your own goal in one sentence${R}"
for i in "${!S_GOAL[@]}"; do say "   $((i+1))) ${S_GOAL[$i]}"; done
ask G "   goal" 2
if [[ "$G" =~ ^[1-6]$ ]]; then i=$((G-1)); GOAL="${S_GOAL[$i]}"; TITLE="${S_TITLE[$i]}"; DCAD="${S_CAD[$i]}"; DBRAIN="${S_BRAIN[$i]}"; DBUD="${S_BUD[$i]}"
else GOAL="$G"; TITLE="$(python3 -c "import sys; t=sys.argv[1].rstrip('.'); print(t if len(t)<=48 else t[:48].rsplit(' ',1)[0])" "$G")"; DCAD=every-2nd-night; DBRAIN=fast; DBUD=3; fi
say ""

# ---- 3. cadence + brain --------------------------------------------------
say "${B}3 · How often, and how much brain?${R}"
say "   cadence: nightly · every-2nd-night · every-3rd-night · weekly"
ask CAD "   cadence" "$DCAD"
case "$CAD" in nightly|every-2nd-night|every-3rd-night|weekly) ;; *) say "   ${D}unknown cadence, using $DCAD${R}"; CAD="$DCAD" ;; esac
if [ "$AGENT" = claude ]; then
  say "   brain: fast (Sonnet) · deep (Opus) · frontier (Fable)"
  ask BRAIN "   brain" "$DBRAIN"
  case "$BRAIN" in deep|opus) MODEL=claude-opus-5 ;; frontier|fable) MODEL=claude-fable-5-1 ;; claude-*) MODEL="$BRAIN" ;; *) MODEL=claude-sonnet-5 ;; esac
else
  CFG_MODEL="$(sed -n 's/^model *= *"\(.*\)"/\1/p' "$HOME/.codex/config.toml" 2>/dev/null | head -1)"
  say "   brain: a Codex model id ${D}(your Codex default is ${CFG_MODEL:-unset})${R}"
  ask BRAIN "   model" "${CFG_MODEL:-gpt-5.5}"; MODEL="$BRAIN"
fi
say ""

# ---- 4. budget, with the math shown --------------------------------------
say "${B}4 · What may it spend?${R}  ${D}dollars per run; the loop stops itself at the total${R}"
ask PER "   per run" "$DBUD"
[[ "$PER" =~ ^[0-9]+([.][0-9]+)?$ ]] || PER="$DBUD"
DTOT="$(python3 -c "print(int(round(float('$PER')*8)))")"
ask TOT "   total for this loop" "$DTOT"
[[ "$TOT" =~ ^[0-9]+([.][0-9]+)?$ ]] || TOT="$DTOT"
case "$CAD" in nightly) PM=30 ;; every-2nd-night) PM=15 ;; every-3rd-night) PM=10 ;; weekly) PM=4 ;; esac
NIGHT_CAP="$(sed -n 's/^- cost_cap_per_night_usd: *\([0-9.]*\).*/\1/p' "$CHARTER" | head -1)"; NIGHT_CAP="${NIGHT_CAP:-15}"
RUNS="$(python3 -c "import math; print(int(float('$TOT')//float('$PER')))")"
say "   ${D}at most \$$(python3 -c "v=float('$PER')*$PM; print(int(v) if v==int(v) else round(v,2))") a month at this cadence; this loop ends after $RUNS runs (\$$TOT); the night cap in the charter is \$$NIGHT_CAP${R}"
if python3 -c "import sys; sys.exit(0 if float('$PER')>float('$NIGHT_CAP') else 1)"; then
  say "   ${D}per-run is above the night cap, so the runner would skip it. Raising the night cap to \$$PER.${R}"; setdial cost_cap_per_night_usd "$PER"
fi
REVIEW="$(date -v+45d +%F 2>/dev/null || python3 -c "import datetime;print((datetime.date.today()+datetime.timedelta(days=45)).isoformat())")"
say ""

# ---- write ---------------------------------------------------------------
ID="$(python3 - "$LOOPS" <<'PY'
import re,sys; s=re.sub(r"<!--.*?-->","",open(sys.argv[1]).read(),flags=re.S)
n=max([int(m) for m in re.findall(r"^## L-(\d+)",s,re.M)]+[0])+1; print("L-%02d"%n)
PY
)"
cat >>"$LOOPS" <<EOF

## $ID — $TITLE
- status: active
- goal: $GOAL
- cadence: $CAD
- model: $MODEL
- budget_per_iteration_usd: $PER
- budget_loop_total_usd: $TOT
- review_by: $REVIEW
- scope: work only inside this folder, on branch \`night/<date>\`. Never push, never deploy,
  never touch \`main\`, never add a dependency. Write findings to \`pm/nights/loops/$ID.md\`.
- definition_of_done_per_iteration: a dated section appended to \`pm/nights/loops/$ID.md\`
  ending with \`next:\` and \`progress: yes|no\`, and the four lines in the night report.
- if_blocked: say so plainly in the state file and stop; never guess.
EOF
setdial agent "$AGENT"; setdial model "$MODEL"
say "${B}Written${R}  $LOOPS  ${D}($ID, review by $REVIEW)${R}"

# ---- trust (Claude Code ignores the fence's allow rules in an untrusted folder) ----
if [ "$AGENT" = claude ]; then
  python3 - "$LOOPS_HOME" <<'PY' && say "${B}Trusted${R}  $LOOPS_HOME in ~/.claude.json  ${D}(so the fence's allow rules apply)${R}"
import json,os,sys
p=os.path.expanduser('~/.claude.json'); home=sys.argv[1]
try: d=json.load(open(p))
except FileNotFoundError: d={}
except ValueError: sys.exit(1)
d.setdefault('projects',{}).setdefault(home,{})['hasTrustDialogAccepted']=True
tmp=p+'.tmp'; json.dump(d,open(tmp,'w'),indent=2); os.replace(tmp,p)
PY
fi

# ---- dry run -------------------------------------------------------------
say ""
say "${B}Dry run${R}  ${D}every guard, no model call, no spend${R}"
STATE="$LOOPS_HOME/00-ops/night/run-state.json"; rm -f "$STATE"
NIGHT_PROBE=1 NIGHT_POWER_OVERRIDE=ac LOOPS_HOME="$LOOPS_HOME" bash "$RUNNER" >/dev/null 2>&1
NOTE="$(python3 -c "import json;print(json.load(open('$STATE')).get('note',''))" 2>/dev/null)"
case "$NOTE" in
  *"loops=$ID"*) say "   tonight the machine would run $ID. ✓" ;;
  *) say "   the machine would NOT run $ID tonight: ${NOTE:-no state written}"; say "   ${D}see $LOOPS_HOME/00-ops/night/logs/$(date +%F).log${R}" ;;
esac
rm -f "$STATE"   # a probe must never block the real run

# ---- what happens next ---------------------------------------------------
say ""
say "${B}Tonight${R}   plug the laptop in. Lid open or shut. The checker looks every ten minutes and takes the first window."
say "${B}Morning${R}   read $LOOPS_HOME/pm/nights/$(date +%F).md  ${D}four lines per loop: trying · did · decided · need from you${R}"
say "${B}Any time${R}  edit $LOOPS · pause with 'paused: yes' in the charter · stop the schedule: bash $LOOPS_HOME/00-ops/install.sh --off"
say ""
