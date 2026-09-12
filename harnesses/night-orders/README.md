# Night Orders

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

## launchd wiring (plists not shipped)

Two user LaunchAgents, both `RunAtLoad`:

- `com.ventures.capture`: runs `ops/capture/poller.sh` with `StartInterval 600`.
- `com.ventures.capture-watchdog`: runs `ops/capture/watchdog-absence.sh` with
  `StartInterval 3600`.

The wrapper itself has no schedule. Opportunistic capture replaced fixed-time firing
after fixed times kept landing on a closed laptop.

## Adopting it

1. Copy this folder's contents into `~/ventures/` so the layout is
   `~/ventures/.claude/settings.json`, `~/ventures/.claude/skills/*`,
   `~/ventures/00-ops/{night,capture,health}`, `~/ventures/pm/`.
2. Replace `/Users/YOU` in `settings.json` with your home directory. Claude Code
   permission paths are absolute.
3. Edit `pm/CHARTER.md`: presence mode, shadow rate, budget caps. Write an `ORDERS.md`
   with a `## Tonight` section of `- [ ]` orders, each with Definition of done, Out of
   scope, and If blocked.
4. Optional env: `NIGHT_GIT_NAME` / `NIGHT_GIT_EMAIL` for snapshot commits,
   `CLAUDE_BIN` if the CLI is not on PATH, `JUDGE_MODEL` for the health desk.
5. Run `NIGHT_PROBE=1 bash 00-ops/night/run-night.sh` first. It exercises every guard and
   stops before invoking the model.
6. Load the two LaunchAgents. Read `00-ops/health/REPORT.md` the next morning.

Everything in here was written with Claude Code; the judgment about what to fence and why
is the operator's.
