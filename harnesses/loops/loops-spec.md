# Loops — product spec

**Status:** RATIFIED — v1 implemented and probe-verified the same session. Divergence
from spec, for the record: runnable-loop selection went wrapper-side in v1 (the §8 v2
idea, nearly free since the wrapper builds the prompt); per-loop budget is enforced as an
iteration-count cap (`total // per_iteration`), deterministic without per-loop cost
attribution.
**Author:** PM (Claude), directed by the operator
**Problem window:** a month of variable presence (charter v2)

---

## 0. v1.1 addendum — the four knobs and five states (September)

Ratified after a month of runs. Two things changed: the loop section gained `goal` and
`model` lines, and `status` became a closed set. Nothing else in this spec moved.

**Knobs a person touches** (everything else in a section is scope and rails):

| Line | Meaning |
|---|---|
| `goal` | One plain sentence a stranger understands. Rendered on every view and in every report. |
| `budget_per_iteration_usd` / `budget_loop_total_usd` | Dollars per run, dollars for the loop. Runs allowed = total ÷ per-run. |
| `cadence` | `nightly` · `every-2nd-night` · `every-3rd-night` · `weekly` |
| `model` | Per-loop Claude id. Falls back to the charter's `model` dial when absent. A cost dial. |

**States** (`status` line, first word; anything after it is a note):

`draft` → `trial` → `active` → `parked` | `done`

- `draft`: has a goal, never run. Not runnable.
- `trial`: runnable; the first three runs, each reviewed before its output is acted on.
- `active`: runnable, unattended.
- `parked`: off the line until a person resumes it. Two consecutive `progress: no` runs park a loop automatically.
- `done`: finished; kept for the record.

The runner treats `trial` and `active` as runnable and everything else as not. Promotion
from `trial` to `active` is a human act (from the desk or the phone), never automatic.

**The four lines.** Every run ends its loop section, in the report and in the state file,
with `- Trying to:` · `- Did:` · `- Decided:` · `- Need from you:` (plus `- Where to
look:` for paths). Each ≤ 25 words, plain speech, no jargon. A run without the four lines
is not done; the definition of done says so and the morning judge checks it.

## 1. Problem

The night lane only runs when `ORDERS.md § Tonight` has fresh orders, and only the
operator can write orders, and only at a standup. Charter v2 makes standups irregular by
design ("standup-on-appearance"). The consequence is visible fast: ORDERS.md reads
**"Tonight — no orders queued"** and the wrapper's no-orders skip means the machine idles
every night until the next appearance.

The machine is a loop with a human dispatcher in the middle. When the dispatcher is
(correctly) mostly absent, the loop doesn't run.

**What Loops solves:** work the operator has *already ratified* can continue across many
nights without a new order each time. A zero-standup week no longer means a zero-work week
— while changing nothing about what the machine is allowed to touch.

## 2. What a Loop is

A **Loop is a standing order that renews itself.** The operator ratifies it once, at a standup,
with a scope, a budget, and a deterministic stop condition. Each night the lane runs the
loop's *next iteration*: read the loop's state, do one bounded increment of the work, verify
it, append the new state, report. The next iteration reads that state and continues.

This is the same artifact-chain pattern the night machine already uses (order → run →
envelope → report), extended one level: the *intent persists across nights* instead of
dying with each order. It is the Maintain→intent→restart step of the AI-native SDLC,
implemented inside the existing fence.

**A Loop is not autonomy.** The machine still originates nothing. The operator originates the
loop; the machine executes iterations of it. Ratifying a loop *is* "orders set when a human
is present" — set once, for N nights, instead of nightly.

## 3. Non-goals

- **Not a way for the machine to write its own orders.** LOOPS.md is operator-edited only,
  same as CHARTER.md and ORDERS.md. The asymmetry holds.
- **Not a widening of the blast radius.** Iterations write only what the night lane may
  already write. No new allows in v1 (see §5 — state lives under `pm/nights/`, already legal).
- **No network, spend, deploy, or MCP.** A loop cannot do anything a night order can't.
- **Not for judgment work.** Grading outreach drafts as sendable, finance verdicts, anything
  Decision-column — stays human. A loop that drifts toward judgment gets parked (§6).
- **Not anything outside `~/ventures`.** Out of the PM's scope per charter; no loop touches it.

## 4. Design

### 4.1 The loop registry — `pm/LOOPS.md`

New file, operator-edited only (not in the night allowlist → denied by default, no fence
change needed). One section per loop:

```markdown
## L-01 — <name>
- status: active | parked | done
- ratified: <date> (standup)
- scope: <one paragraph — what iterations may work on. The boundary clause.>
- iteration: <what ONE night's increment looks like, sized to one session>
- cadence: nightly | every-2nd-night | every-3rd-night
- budget_per_iteration_usd: <n>       # ≤ cost_cap_per_night_usd
- budget_loop_total_usd: <n>          # lifetime cap for the whole loop
- stop: <deterministic condition(s) — date, count, artifact-exists, external event>
- review_by: <date>                   # hard TTL; every loop dies at the next charter revisit
                                      # unless re-ratified
- definition_of_done_per_iteration: <...>
- out_of_scope: <...>
- if_blocked: <...>
```

Definition of done / out of scope / if blocked are mandatory, same as orders — a loop
without them does not activate. `review_by` is mandatory and may not exceed the next
scheduled charter revisit: **no immortal loops.**

### 4.2 Loop state — `pm/nights/loops/<id>.md`

Machine-owned state, one file per loop, **append-only dated sections** (same rule as
BRIEF.md: supersede, never rewrite). Lives under `pm/nights/**`, which the night lane may
already write — **zero fence change in v1.**

Each iteration appends: date, what was done, what was verified (with the evidence), the
cursor for the next iteration ("next: …"), iterations-elapsed count, spend-to-date estimate,
and a `progress: yes|no` self-assessment against the loop's definition of done.

### 4.3 Night selection — precedence order

Amend `00-ops/night/night-prompt.md`:

1. **Explicit `Tonight` orders always win.** Loops fill remaining capacity only.
2. Capacity = `night_orders_per_night` (2). Loop iterations count against it — a night is
   at most 2 units of work regardless of where they come from.
3. Among runnable loops (status active, cadence due, budgets clear, stop not met), run in
   LOOPS.md order. Skipped loops are named in the report with the reason.
4. An iteration begins by reading the loop's state file **and verifying the previous
   iteration's key claim** before building on it (the control-rebuild habit, made law —
   see §6, compounding error).

### 4.4 Wrapper change — the one real code change in v1

`run-night.sh`'s **no-orders skip becomes a no-work skip**: skip only when `Tonight` is
empty AND no loop is runnable. Runnable-loop detection must be cheap and deterministic
(grep LOOPS.md for `status: active`, check cadence against the state file's last dated
entry, check budgets against the ledger). Everything else in the wrapper — budget preflight,
envelope persistence, cd $VENT, ledger row — is unchanged and applies to loop nights
identically.

Per house rules, this ships with a **probe**, not an assumption: forced tests for
(a) no orders + runnable loop → runs, (b) no orders + no runnable loop → skips,
(c) orders present + loop due → orders first, loop takes slot 2,
(d) loop budget exhausted → skip with reason in state/report.

### 4.5 Enforcement honesty — what holds each rule

House culture: say which wall enforces what, and never claim prompt-level rules are fences.

| Rule | Enforced by |
|---|---|
| LOOPS.md is operator-only | **Fence** (not in allowlist; deny by default) |
| Blast radius of iterations | **Fence** (unchanged night allowlist) |
| Per-night cost cap, 7-day, monthly | **Wrapper** preflight (existing) |
| Per-loop lifetime budget | **Wrapper** (new check) + ledger; prompt as backstop |
| Cadence, capacity, precedence | **Wrapper** (runnable check) + **prompt** |
| Scope boundary, verify-predecessor, append-only state | **Prompt** + morning `git diff` audit (the authoritative record, per NOTES.md) |
| Stop conditions | **Wrapper** where mechanical (date/budget); **prompt** where semantic |

Known gap, stated plainly: scope drift is prompt-enforced in v1. The mitigation is §6's
no-progress parking plus the existing morning audit (`git diff main...night/<date>` /
fleet-health transcript checks), not a fence. If drift is observed in practice, that's the
trigger for v2 (wrapper-side iteration instantiation), not a reason to build it now.

## 5. Governance changes (the ratification ask)

1. **CHARTER.md** — add under Order rules: *"A ratified loop in LOOPS.md is a standing
   order. Iterations count against night_orders_per_night. LOOPS.md is edited only by
   the operator. Every loop carries a review_by no later than the next charter revisit."*
2. **Blast radius** — no change. State under `pm/nights/loops/**` is already legal. (Listing
   it explicitly in the charter's allowed-writes bullet is cosmetic and recommended.)
3. **ORDERS.md** — `Tonight` gains one convention: `loops: on|off` line, letting a standup
   suspend all loops for a night without editing LOOPS.md.
4. **Finance prices every loop before ratification** — a loop is a standing bet
   (iterations × budget, against quota); it goes through the same pricing as any order
   class. The probe clause applies: first iteration of any new loop class runs as a
   supervised probe before the loop goes unattended.

## 6. Failure modes → mitigations

- **Compounding error ("organized nonsense at industrial scale").** Same model, same
  context, every night — a wrong claim in iteration 3 becomes load-bearing by iteration 7.
  → Each iteration re-verifies its predecessor's key claim against ground truth before
  extending (4.3.4). State sections must cite evidence, not conclusions.
- **Zombie loops.** A loop that keeps running because nothing stops it.
  → Mandatory `review_by` ≤ next charter revisit; mandatory deterministic `stop`.
- **No-progress churn.** Iterations that burn quota without advancing.
  → **Two consecutive `progress: no` iterations auto-park the loop** (mirrors the
  two-overrun budget pause), flagged for the next standup. Parked ≠ dead: the operator revives
  or kills.
- **Scope drift.** Iteration N "discovers" adjacent work.
  → Boundary clause is law: out-of-scope findings go in the report's Observations as a
  *proposed* order/loop for the operator — never into the iteration.
- **Budget runaway.** → Per-iteration cap ≤ night cap; per-loop lifetime cap; all existing
  caps (night/7-day/month) bind unchanged, wrapper-preflight enforced.
- **Loop starves real orders.** → Precedence rule: explicit orders always first; loops are
  residual capacity only.

## 7. Launch candidates (finance prices; standup ratifies)

- **L-02 — Portfolio night-watch.** Scope: cheap verification pass — registry rows vs
  reality, hang-dry list still true, night-branch hygiene, observations for the morning.
  Iteration ~1–2 units of nightly budget, cadence every 3rd night. Stop: review_by.
  *Rationale: the "diagnosis nights are cheap" profile from the first month's ledger, made
  standing. Start here — it is the probe loop.*
- **L-01 — Build loop (template).** Scope: one backlog item per night on a venture's site,
  on a `night/<date>` branch, never pushed. Iteration ~6 units, loop total ~45, cadence
  every 2nd night. Stop: backlog empty or review_by.
  *Rationale: keeps a live venture moving without touching the human-gated deploy step.*
- **L-03 — Source watch (template).** Scope: read one public source your venture depends
  on, write candidate rows with URLs — never edit ratified data. Iteration ~5 units, loop
  total ~30.

Explicitly **not** proposed as loops: anything with a send step (the operator's), anything
needing network/analytics beyond what the fence already allows, polish on ventures the
current priority says no to.

## 8. v1 / v2 line

**v1 (ships after one standup):** LOOPS.md + night-prompt amendment + wrapper no-work skip
+ probe suite + charter line + L-02 as the probe loop (cheapest, lowest risk), then the rest.

**v2 (only if v1 shows drift or the manual audit gets expensive):** wrapper-side iteration
instantiation (deterministic order file generated from LOOPS.md + state, so the model never
interprets the registry), per-loop ledger accounting, fleet-health.py loop-aware grading.

**Deliberately never:** loops that write LOOPS.md/ORDERS.md, loops with network access,
loops without a TTL, loop-proposed loops that activate without ratification.

## 9. Open questions for the standup

1. Confirm iterations count against `night_orders_per_night` (spec assumes yes).
2. Loop sizing: is N iterations × the per-iteration budget the right bet this month, or is
   L-02 alone the answer? (Finance call.)
3. Does the day lane get loops too, or night-only for v1? (Spec assumes night-only.)
4. Where does the per-loop budget check live in v1 — wrapper (grep ledger) or accept
   prompt+state enforcement until v2? (Spec recommends wrapper; it's a small addition to an
   existing preflight.)
