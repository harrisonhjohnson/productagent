#!/bin/bash
# LLM judge: does the night report match the git evidence? (Braintrust
# LLMClassifier pattern — choice_scores over a fixed rubric, chain-of-thought,
# pinned cheap model.) Human-side tooling: run from your own shell at standup
# ("read the night"); the night session cannot run or edit it (00-ops is fenced).
# Usage: 00-ops/health/judge-night.sh [YYYY-MM-DD]   (default: today)
# Appends {"date","judge":{choice,score,...}} to 00-ops/health/scores.jsonl.
set -u
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
VENT="${LOOPS_HOME:-$HOME/ventures}"; H="$VENT/00-ops/health"
CLAUDE_BIN="${CLAUDE_BIN:-$(command -v claude || echo "$HOME/.local/bin/claude")}"
DATE="${1:-$(date +%F)}"
MODEL="${JUDGE_MODEL:-claude-sonnet-5}"     # pinned on purpose: never inherit /model
REPORT="$VENT/pm/nights/$DATE.md"; ENVELOPE="$VENT/pm/nights/$DATE-envelope.md"
MAXBYTES=80000
cd "$VENT" || exit 1
[ -f "$REPORT" ] || { echo "no report at $REPORT"; exit 2; }

# The true write set comes from the session transcripts (which the run cannot edit),
# not from the commit: the wrapper's sweep-commit (ORDERS blocked item 1) can bundle
# edits from earlier human/day sessions under the night's authorship.
WRITESET="$(python3 - "$DATE" <<'PY'
import json,sys,glob,os,datetime
date=sys.argv[1]; home=os.path.expanduser("~")
vent=os.environ.get("LOOPS_HOME",f"{home}/ventures")
tdir=f"{home}/.claude/projects/-"+vent.strip("/").replace("/","-")
day=datetime.date.fromisoformat(date)
writes=set()
for f in glob.glob(f"{tdir}/*.jsonl"):
    m=datetime.date.fromtimestamp(os.path.getmtime(f))
    if not (day-datetime.timedelta(days=1)<=m<=day): continue
    files=[f]+glob.glob(f"{tdir}/{os.path.basename(f)[:-6]}/subagents/agent-*.jsonl")
    headless=False; ws=set(); tools=0; night=False
    for ff in files:
        for line in open(ff):
            try: r=json.loads(line)
            except: continue
            if r.get("entrypoint")=="sdk-cli": headless=True
            if not night and r.get("type")=="user":
                c=(r.get("message") or {}).get("content")
                t=c if isinstance(c,str) else " ".join(b.get("text","") for b in (c or []) if isinstance(b,dict))
                if "ventures night run" in t: night=True
            ts=r.get("timestamp","")
            m_=r.get("message")
            if not isinstance(m_,dict) or not isinstance(m_.get("content"),list): continue
            for b in m_["content"]:
                if isinstance(b,dict) and b.get("type")=="tool_use":
                    tools+=1
                    if b.get("name") in ("Write","Edit","NotebookEdit") and ts.startswith(date):
                        fp=(b.get("input") or {}).get("file_path","")
                        if fp.startswith(vent+"/"): ws.add(fp[len(vent)+1:])
    if headless and night and tools>=5: writes|=ws
print("\n".join(sorted(writes)))
PY
)"

evidence() {
  local shas; shas="$(git log --author=ventures-night --since="$DATE 00:00" --until="$DATE 23:59:59" --format=%H)"
  echo "## Files the night session(s) actually wrote on $DATE (from transcripts — authoritative)"
  echo "${WRITESET:-(none found)}"
  echo
  echo "## Umbrella night commit(s) $DATE: ${shas:-none}"
  echo "(The wrapper commits the whole dirty tree; paths NOT in the write set above were"
  echo "swept in from earlier human/day sessions — do not hold the report to them.)"
  for s in $shas; do
    git show --stat --format='commit %h %s' "$s" -- . ':!00-ops/capture' ':!00-ops/day'
    if [ -n "$WRITESET" ]; then
      echo "## Diff limited to the session write set"
      printf '%s\n' "$WRITESET" | xargs git show --format= -p "$s" --
    fi
  done
  for d in "$VENT"/0*-*/ "$VENT"/0*-*/site/; do
    [ -d "$d/.git" ] || continue
    git -C "$d" show-ref --quiet "refs/heads/night/$DATE" || continue
    local nshas; nshas="$(git -C "$d" log "night/$DATE" --since="$DATE 00:00" --until="$DATE 23:59:59" --format=%H)"
    [ -n "$nshas" ] || continue
    echo "## $(basename "$d") commits on night/$DATE dated $DATE"
    for s in $nshas; do git -C "$d" show --stat -p --format='commit %h %s' "$s"; done
  done
}
EVID="$(evidence | head -c $MAXBYTES)"
[ "$(printf %s "$EVID" | wc -c)" -ge $MAXBYTES ] && EVID="$EVID
[TRUNCATED at $MAXBYTES bytes]"

PROMPT="$(cat "$H/judge-night.md")

===== REPORT (pm/nights/$DATE.md) =====
$(cat "$REPORT")

===== ENVELOPE (pm/nights/$DATE-envelope.md) =====
$(cat "$ENVELOPE" 2>/dev/null || echo '(missing)')

===== EVIDENCE =====
$EVID"

SCHEMA='{"type":"object","required":["choice","reasoning","unsupported_claims","unmentioned_changes"],"properties":{"choice":{"type":"string","enum":["A","B","C","D","E"]},"reasoning":{"type":"string"},"unsupported_claims":{"type":"array","items":{"type":"string"}},"unmentioned_changes":{"type":"array","items":{"type":"string"}}}}'
OUT="$("$CLAUDE_BIN" -p "$PROMPT" --model "$MODEL" --effort low --tools "" \
  --strict-mcp-config --mcp-config "$VENT/00-ops/night/night-mcp.json" \
  --setting-sources project --output-format json --json-schema "$SCHEMA" </dev/null 2>"$H/.judge-stderr")"
J="$(printf %s "$OUT" | jq -c '.structured_output // empty' 2>/dev/null)"
if [ -z "$J" ]; then
  J="$(printf %s "$OUT" | jq -r '.result // empty' 2>/dev/null | sed -n '/{/,/}/p' | jq -c . 2>/dev/null)"
fi
[ -z "$J" ] && { echo "judge returned no JSON:"; printf %s "$OUT" | tail -c 600; cat "$H/.judge-stderr"; exit 1; }
COST="$(printf %s "$OUT" | jq -r '.total_cost_usd // 0')"
# choice_scores — A=1 B=0.6 C=0.3 D=0 E=skip
SCORE="$(printf %s "$J" | jq -r '{A:1,B:0.6,C:0.3,D:0,E:null}[.choice]')"
printf '{"date":"%s","lane":"night","judge":%s,"cost_usd":%s}\n' "$DATE" \
  "$(printf %s "$J" | jq -c --argjson s "$SCORE" '. + {score:$s, model:"'"$MODEL"'"}')" "$COST" >>"$H/scores.jsonl"
echo "night $DATE — judge $(printf %s "$J" | jq -r '.choice') (score $SCORE, \$$COST, $MODEL)"
printf %s "$J" | jq .
