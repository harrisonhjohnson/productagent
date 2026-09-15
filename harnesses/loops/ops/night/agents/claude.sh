#!/bin/bash
# Agent adapter: Claude Code. Sourced by run-night.sh after run_with_timeout is defined.
# Contract (same for every adapter):
#   agent_canary <outfile>                       -> outfile contains READY on success
#   agent_run    <outfile> <promptfile> <model> <effort> <timeout_secs>
#                                                -> outfile is JSON {result, total_cost_usd, ...}
CLAUDE_BIN="${CLAUDE_BIN:-$(command -v claude || echo "$HOME/.local/bin/claude")}"

agent_canary() {
  run_with_timeout 180 "$1" "$CLAUDE_BIN" -p 'Reply with exactly: READY' \
    --model "$MODEL" --effort low --setting-sources project \
    --strict-mcp-config --mcp-config "$OPS/night-mcp.json" </dev/null
}

agent_run() { # outfile promptfile model effort timeout
  run_with_timeout "$5" "$1" \
    "$CLAUDE_BIN" -p "$(cat "$2")" \
      --model "$3" --effort "$4" \
      --output-format json \
      --setting-sources project \
      --strict-mcp-config --mcp-config "$OPS/night-mcp.json" </dev/null
}

agent_relogin_hint() { echo "Run 'claude' interactively to re-login."; }
