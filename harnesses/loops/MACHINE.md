# The machine behind Loops


_This is the engineering page. For what a loop is and how to use one, start at [README.md](README.md)._
A captain's night order book, for a portfolio of small ventures run by one person and
one coding agent: judgment written down at dusk, executed by the watch overnight, the
captain woken only under named conditions.

This is the machine that lets Claude Code work unattended on `~/ventures` while its
operator sleeps, travels, or is simply away from the laptop — without ever being able to
spend money, push code, widen its own permissions, or rewrite its own orders. It was built
by the operator with Claude over about a month of nightly runs; every rule below was
promoted from something that went wrong first.

## The five laws

1. **Separate judgment from labor in time.** An order is frozen judgment; the meeting is
   where judgment lives, the night is where labor lives.
2. **Trust is structural, not behavioral.** Arrange the world so the bad thing is
   impossible or absent; a branch is a fact you can diff, a rule is a hope.
3. **Grade evidence, never claims.** Reports where lying is detectable; the wrapper's
   envelope, not the model, is the authority on time and cost.
4. **The alarm never lives inside the thing it watches.** A system cannot report its own
   absence.
5. **Learnings compound only at the point of use**, and recurring ones get promoted until
   they become physics.

## The six pieces

| Piece | Files | What it does |
|---|---|---|
| **The fence** | `settings.json` | Claude Code project permissions: an explicit allowlist scoped to `~/ventures`, read-only git verbs, no shells, no `rm`, no `push`, no MCP auth. Deny rules keep the run out of its own charter, orders, loops, ops tooling, and every dotfile. |
| **The captain's book** | `pm/CHARTER.md`, `pm/LOOPS.md` (plus `ORDERS.md` and `LOG.md`, not shipped) | Human-edited only. The charter holds the dials (model, effort, budget caps, WIP limit) and the blast radius. Loops are standing orders that renew themselves nightly under a budget and a TTL. |
| **The night runner** | `ops/night/run-night.sh`, `night-prompt.md`, `night-mcp.json` | The wrapper: reads dials from the charter, skips if nothing is runnable, preflights the cost ledger, runs an auth canary, snapshots nested repos onto `night/<date>` branches, invokes `claude -p` with zero MCP servers and a hard timeout, persists the envelope, commits the tree, appends the ledger row, writes an alert file on anything but `ok`. |
| **Capture and watchdog** | `ops/capture/poller.sh`, `watchdog-absence.sh` | Fires every 10 minutes while the machine is awake; runs a lane at the first window that fits its physics (night needs AC power; day accepts lid-open battery ≥ 50%). The watchdog alarms only when a window existed and nothing ran, never on calendar silence. |
| **Health desk** | `ops/health/fleet-health.py`, `judge-night.sh`, `judge-night.md` | Morning ground truth. Deterministic trajectory scorers over the session transcripts the run cannot edit (step budget, repeat loops, denied-then-retried, protected-path writes, git mutations), plus an LLM judge that grades the night's report against the diff of what it actually wrote. |
| **The disciplines** | `skills/{pm,brand,growth,finance,launch-business}` | Five Claude Code skills. `pm` is the chief of staff and runs the standup; the other four each own one thing (voice and design, the honest signal, the economic verdict, the launch pipeline) and refuse the others'. |

## How a night runs

1. The poller sees AC power, stamps the window, and invokes the wrapper under `caffeinate`.
2. The wrapper reads the charter dials, counts unchecked `## Tonight` orders, and asks a
   deterministic Python block which loops are runnable (cadence, budget by iteration
   count, two-consecutive-no-progress auto-park). Nothing runnable means a one-line state
   file and exit.
3. Budget preflight against the cost ledger: rolling 7-day and monthly caps, and a pause
   after two consecutive over-cap nights.
4. An auth canary (`Reply with exactly: READY`) proves the CLI is logged in before any
   real spend.
5. Every nested venture repo gets a pre-night snapshot commit and a `night/<date>` branch.
6. `claude -p` runs the night prompt with `--strict-mcp-config` against an empty MCP
   config, project-only settings, and a hard timeout. One retry on a non-timeout failure.
7. The result envelope is persisted to `pm/nights/<date>-envelope.md` before anything
   else can fail. The tree is committed as `ventures-night`. A ledger row is appended.
8. Anything but `ok` writes `ALERT.md` and fires a macOS notification. The morning
   standup reads the alert, then the health desk, then the report, then the diff.

## Agent adapters

`run-night.sh` never calls a CLI directly. It reads `agent:` from the charter (default
`claude`), sources `00-ops/night/agents/<agent>.sh`, and calls three functions:
`agent_canary <out>` (must leave READY in `out`), `agent_run <out> <promptfile> <model>
<effort> <timeout>` (must leave a JSON envelope with `result` and `total_cost_usd` in
`out`), and `agent_relogin_hint`. Everything downstream, the envelope persist, the ledger
row, the NIGHT-BLOCKED check and the health desk, reads that envelope.

- `claude.sh`: `claude -p … --output-format json --setting-sources project` with the empty
  MCP config. The envelope is Claude Code's own.
- `codex.sh`: `codex exec --json -o <last-message> --sandbox workspace-write` with
  `sandbox_workspace_write.network_access=false` and `approval_policy="never"`. The
  adapter folds the JSONL events into the envelope shape, takes `result` from the last
  message, and prices `turn.completed` usage with the two `codex_usd_per_m_*` dials
  (`cost_is_estimate: true`). A failed turn becomes a `NIGHT-BLOCKED` result so the
  runner records `blocked`, not `ok`.

Known gap: the health desk's transcript scorers read `~/.claude/projects`; Codex sessions
live under `~/.codex/sessions` and are not scored yet.

## launchd wiring (plists not shipped)

Two user LaunchAgents, both `RunAtLoad`:

- `com.ventures.capture`: runs `ops/capture/poller.sh` with `StartInterval 600`.
- `com.ventures.capture-watchdog`: runs `ops/capture/watchdog-absence.sh` with
  `StartInterval 3600`.

The wrapper itself has no schedule. Opportunistic capture replaced fixed-time firing
after fixed times kept landing on a closed laptop.

## Adopting it

`install.sh` in this folder is what `curl -fsSL https://productagent.dev/install.sh | bash`
runs. It lays the folder out as `$LOOPS_HOME/{.claude/settings.json, 00-ops/{night,capture,health}, pm/}`
(default `~/loops`), fills `/Users/YOU` and the ventures path into the fence, copies the
templates in `pm/templates/` as an empty `LOOPS.md` and `ORDERS.md`, initialises a git
repo for the runner to commit into, writes and loads the two LaunchAgents below with
`LOOPS_HOME` in their environment, and, when a terminal is present, hands off to
`init.sh`. That script reads answers from `/dev/tty` (so it works through `curl | bash`),
appends one `## L-NN` section to `pm/LOOPS.md`, sets `agent:` and `model:` in the charter,
raises `cost_cap_per_night_usd` if the per-run budget exceeds it, sets
`projects[<folder>].hasTrustDialogAccepted` in `~/.claude.json` for Claude Code, runs the
runner with `NIGHT_PROBE=1`, and reports the probe's note. Without a terminal it prints the
steps instead. Every script reads `LOOPS_HOME` and falls back to
`~/ventures`. Re-running it refreshes the machine and never overwrites the charter, loops,
orders or fence you have edited.

By hand, the same steps are:

1. Copy this folder's contents so the layout above holds.
2. Replace `/Users/YOU` in `settings.json` with your home directory. Claude Code
   permission paths are absolute.
3. Edit `pm/CHARTER.md`: presence mode, shadow rate, budget caps. Write `pm/ORDERS.md`
   with a `## Tonight` section of `- [ ]` orders, each with Definition of done, Out of
   scope, and If blocked.
4. Optional env: `NIGHT_GIT_NAME` / `NIGHT_GIT_EMAIL` for snapshot commits,
   `CLAUDE_BIN` if the CLI is not on PATH, `JUDGE_MODEL` for the health desk.
5. Run `NIGHT_PROBE=1 bash 00-ops/night/run-night.sh` first. It exercises every guard and
   stops before invoking the model.
6. Load the two LaunchAgents. Read `00-ops/health/REPORT.md` the next morning.

Everything in here was written with Claude Code; the judgment about what to fence and why
is the operator's.
