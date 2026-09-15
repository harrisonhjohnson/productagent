#!/bin/bash
# Agent adapter: OpenAI Codex CLI (`codex exec`). Sourced by run-night.sh.
# Same contract as claude.sh. Differences worth knowing:
#   - The fence is Codex's sandbox, not a rules file: workspace-write inside $VENT with network
#     off, so the agent cannot push, fetch, or reach the internet at all. Coarser than Claude
#     Code's per-path rules, and it also means WebFetch-style research loops will not work.
#   - Codex reports tokens, not dollars. Cost is estimated from two charter dials
#     (codex_usd_per_m_input, codex_usd_per_m_output) and marked as an estimate in the envelope.
#   - Codex reads AGENTS.md in the working directory, not CLAUDE.md.
CODEX_BIN="${CODEX_BIN:-$(command -v codex || echo "/opt/homebrew/bin/codex")}"
CODEX_IN="$(dial codex_usd_per_m_input)";   CODEX_IN="${CODEX_IN:-1.25}"
CODEX_OUT="$(dial codex_usd_per_m_output)"; CODEX_OUT="${CODEX_OUT:-10}"

_codex_args() { # model effort sandbox
  printf '%s\n' --json --skip-git-repo-check -C "$VENT" \
    --sandbox "$3" \
    -c 'sandbox_workspace_write.network_access=false' \
    -c 'approval_policy="never"' \
    -c "model_reasoning_effort=\"$2\"" \
    -m "$1"
}

# Turn a JSONL event stream into the runner's envelope: {result, total_cost_usd, ...}
_codex_envelope() { # eventsfile lastmsgfile outfile
  python3 - "$1" "$2" "$3" "$CODEX_IN" "$CODEX_OUT" <<'PY'
import json, sys, os
ev, last, out, p_in, p_out = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]), float(sys.argv[5])
usage, errors, msgs = None, [], []
for line in open(ev, errors="replace"):
    line = line.strip()
    if not line: continue
    try: e = json.loads(line)
    except ValueError: continue
    t = e.get("type", "")
    if t == "turn.completed" and isinstance(e.get("usage"), dict): usage = e["usage"]
    elif t in ("error", "turn.failed"):
        m = e.get("message") or (e.get("error") or {}).get("message") or ""
        if m: errors.append(m)
    elif t == "item.completed":
        it = e.get("item") or {}
        if it.get("type") == "agent_message" and it.get("text"): msgs.append(it["text"])
        if it.get("type") == "error" and it.get("message"): errors.append(it["message"])
result = open(last).read() if os.path.exists(last) else ("\n\n".join(msgs))
if not result and errors: result = "NIGHT-BLOCKED: codex failed before producing a report\n" + "\n".join(errors)
cost = None
if usage:
    i = float(usage.get("input_tokens", 0) or 0) - float(usage.get("cached_input_tokens", 0) or 0)
    o = float(usage.get("output_tokens", 0) or 0)
    cost = round(max(i, 0) / 1e6 * p_in + o / 1e6 * p_out, 6)
json.dump({
    "agent": "codex", "result": result, "total_cost_usd": cost if cost is not None else 0,
    "cost_is_estimate": True, "cost_known": cost is not None, "usage": usage, "errors": errors,
}, open(out, "w"))
PY
}

agent_canary() { # outfile
  local ev; ev="$(mktemp)"
  run_with_timeout 180 "$ev" "$CODEX_BIN" exec $(_codex_args "$MODEL" low read-only) \
    -o "$1" 'Reply with exactly: READY' </dev/null
  local rc=$?
  # surface the failure where the runner's grep/tail will see it: JSON error events if any, else raw output
  if [ ! -s "$1" ]; then
    grep -E '"type": *"(error|turn\.failed)"' "$ev" | tail -2 >"$1"
    [ -s "$1" ] || tail -3 "$ev" >"$1"
  fi
  rm -f "$ev"; return $rc
}

agent_run() { # outfile promptfile model effort timeout
  local ev last; ev="$(mktemp)"; last="$(mktemp)"; : >"$last"
  run_with_timeout "$5" "$ev" "$CODEX_BIN" exec $(_codex_args "$3" "$4" workspace-write) -o "$last" "$(cat "$2")" </dev/null
  local rc=$?
  _codex_envelope "$ev" "$last" "$1"
  cat "$ev" >>"$LOG"; rm -f "$ev" "$last"
  return $rc
}

agent_relogin_hint() { echo "Run 'codex login' (or check https://chatgpt.com/codex/settings/usage for the usage limit)."; }
