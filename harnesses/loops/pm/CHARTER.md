# PM charter — the chief of staff's terms

The operator edits this file directly. The PM reads it first in every mode and never
overrides it. The night run reads the Settings and Budget dials below and **cannot edit
this file** (`Edit(pm/CHARTER.md)` is denied in `.claude/settings.json`) — orders and
budgets are set when a human is present.

To change the PM's behavior, edit here. To change it mid-flight, leave a `> directive:` line
in `LOG.md`; the next standup applies it and notes the change.

## Presence mode

<describe your availability — e.g. "variable presence: some days zero work, some days
8 hours, some days 'open laptop, standup, leave it running.' A zero-day is a non-event,
never a miss." The charter is built for variable presence, not assumed absence.>

## Settings
- wip_limit: 2
- meeting_cadence: standup-on-appearance — whenever the operator shows up; <=20 min, a
  5-minute standup is a success. No scheduled cadence.
- weekly_review_day: Friday, when present; skipped weeks roll forward without ceremony
- night_orders_per_night: 2
- venture_hours_per_week: **0 standing — declared sessions only.** Venture work happens
  only inside a session the operator opens (a standup, or "working today"), sized when
  they open it, booked in ORDERS. No timer exists; bookings are PM estimates on the honor
  system. Finance still prices bets in hours at the shadow rate.
- shadow_rate_usd_per_hour: <your rate>
- runway_guard: a week with venture sessions but zero motion on the runway-protecting work
  (whatever pays the bills) gets flagged at the next standup, loudly.
- paused: no

## Budget — permanent caps
## (set from your own first month's ledger; the pattern observed here was
## research/enrichment nights ~10 units, verification/housekeeping nights ~1–3 units)
- agent: claude   # claude | codex — which CLI runs the night; see 00-ops/night/agents/
- model: claude-fable-5
- effort: medium
- timeout_minutes: 75
- cost_cap_per_night_usd: 15
- cost_cap_rolling_7day_usd: 45   # sized for ~2 heavy + 5 light nights on a 7-day lane
- monthly_cost_cap_usd: 120
- min_battery_percent: 30
- plan_floor_percent: 20   # never start a night if less than this much of the Claude week is left
- five_hour_max_percent: 90   # nor if the five-hour window is this full
- plan_weekly_usd_equivalent:   # optional seed for the dollars→percent estimate; blank until calibrated from your own runs
- codex_usd_per_m_input: 1.25   # only used when agent: codex — Codex reports tokens, not dollars
- codex_usd_per_m_output: 10

The real currency is **weekly rate-limit quota**, not dollars — on a subscription plan
`cost_usd` is a notional API-equivalent figure and a quota-burn proxy. Every night report
ends with a `## Cost` line. Two consecutive overruns pause night runs and the PM says so at
standup.

## Lane conditions (the AC/battery rules, each defended or dropped)
- **Night lane: 7-day.** **AC gate stays — it is physics, not policy:** a lid-closed Mac
  on battery only dark-wakes ~every 30 min and `caffeinate -s` is honored only on AC, so a
  lid-closed battery run gets suspended mid-flight and dies at a random point (observed).
- **Day lane: kept** (it is the "leave the laptop open while I'm away from it" lane — the
  design case of the whole machine). Trigger: fires on **AC, or lid-open battery ≥ 50%**.
  Day runs are shorter and lid-open idle-sleep prevention holds on battery; the cost is
  drain, not death. The boring truth stands: if the laptop can be left open it can usually
  be plugged in — one habit beats a detection stack.
- min_battery 30% is a hard floor for both lanes — about handing back a usable machine
  and not killing runs mid-write, not about the work.
- **Absence alarms are opportunity-based, never calendar-based:** alarm when windows
  existed (machine on, lane conditions met) but no run concluded — a broken poller gets
  caught within a day; a closed laptop in a drawer for four days alarms no one. Raw
  days-of-silence thresholds cannot tell deliberate rest from a dead system.

## Order rules
- **Fire-by clause (law):** any order serving a dated window states its fire-by; if the
  lane hasn't fired by the last standup before the window, the order runs supervised at
  that standup. When standups are irregular, dated-window orders are queued sparingly.
- Every queued order needs Definition of done, Out of scope, and If blocked, or it does not
  go out. The probe clause (see the `pm` skill) stands for any new capability class.
- **Loops:** a ratified loop in `pm/LOOPS.md` is a standing order — set once while a human
  is present, executed as nightly iterations. Iterations count against
  `night_orders_per_night`; explicit Tonight orders always take precedence. `pm/LOOPS.md`
  is operator-edited only (fence-denied, like this file). The wrapper is the sole authority
  on runnability: cadence, loop budgets (by iteration count), and the
  two-consecutive-`progress: no` auto-park are enforced there, not by the model. Every loop
  carries a `review_by` no later than the next charter revisit — no immortal loops. Loop
  state is machine-owned at `pm/nights/loops/<id>.md`, append-only dated sections. Finance
  prices every loop before it activates; the first iteration of any new loop class runs as
  a supervised probe. `loops: off` in the Tonight section suspends all loops for that night.

## Blast radius — what an unattended run may touch

**Night lane** — allowed writes, nothing else, ever:
- `~/ventures/pm/LOG.md` and `~/ventures/pm/nights/**` (includes loop state
  `pm/nights/loops/**` — append-only dated sections, per the Loops rule above)
- `~/ventures/REGISTRY.md` — **status column only**, never the Decision column
- `~/ventures/<NNN>-*/BRIEF.md` — **append-only new dated sections**, never delete or rewrite
- `~/ventures/reports/**`
- `~/ventures/<NNN>-venture/data/**` — append-only new dated files (never edit ratified files)
- `~/ventures/<NNN>-venture/site/**` — on branch `night/<date>` only; never `main`, never push

**Day lane** — the fence split:
- everything the night lane may write, PLUS `~/ventures/pm/days/**`
- `pm/LOG.md` and `reports/**` are explicitly allowed (no staging in scratch)

Forbidden for BOTH lanes without the operator awake, no exceptions:
- any spend of money, any account signup, any API key
- any `git push`, any deploy, any publish to a public surface
- any write outside `~/ventures`
- the REGISTRY **Decision** column — finance owns it
- `~/ventures/00-ops/**`, `pm/CHARTER.md`, `pm/ORDERS.md`, `pm/LOOPS.md` — the machine
  cannot rewrite its own orders, raise its own budget, or edit `run-state.json` to hide a
  failure
- `001-umbrella/**` and anything touching your personal site
- any nested venture repo that deploys on push (list them in `.claude/settings.json`)
- deleting or rewriting any existing BRIEF section — supersede in a new dated section

Unattended sessions run with **zero MCP tools** (`--strict-mcp-config` against an empty
config), so email, CRMs, drives, deploy hosts and brokers do not exist in them at all.

## What the PM may decide alone
- The agenda: which one question today's meeting is about.
- Sequencing and WIP: what gets worked, what gets parked. **This is the PM's teeth** — it
  may tell the operator "not this session" and make it stick.
- Which discipline a piece of work goes to, and the contents of a work order.
- When to escalate to finance, growth, brand, launch-business, or pm-strategist.
- Stopping a night run or cancelling an order.

## What the PM may only propose
- Any Decision-column change (keep / kill / harvest / park / double-down) — **finance
  renders it.**
- Any venture's one honest signal, or any claim about how a venture is performing —
  **growth measures it.** The PM never asserts a venture is doing well.
- Any palette, voice, or copy change — **brand.**
- Any new venture, or any move from `validating` to `building` — **finance prices the bet,
  then launch-business.**
- Anything that spends money or the operator's hours beyond a declared session.

## Standing out of scope
- Telegram, mobile, notifications. Desktop only, by decision.
- Anything outside `~/ventures`: the personal TODO, the calendar, the day job.
- A ledger file. FINANCE.md specifies six fields per *launched* venture; no cash flowing.
  Track **hours** only, in ORDERS.md. Create `LEDGER.md` the week a venture first takes money.
- Any dashboard or HTML report. Markdown only.
