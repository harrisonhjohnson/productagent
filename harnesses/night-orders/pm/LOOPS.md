# Loops — standing orders that renew themselves

The operator edits this file only — the night fence denies it, same as ORDERS.md and
CHARTER.md. Ratified at a standup per the Loops spec (`pm/loops-spec.md`). A loop here is
a standing order: the wrapper decides each night which loops are runnable (cadence,
budgets, no-progress auto-park — all deterministic, wrapper-side) and names them in the
prompt; the session runs one bounded iteration per runnable loop, after explicit Tonight
orders, within `night_orders_per_night` total.

Loop state is machine-owned at `pm/nights/loops/<id>.md` — append-only dated sections,
never rewritten. Each iteration must re-verify the previous iteration's key claim before
extending it, and ends its section with `next:` and `progress: yes|no` lines.
Two consecutive `progress: no` iterations make a loop non-runnable until a standup
revives it. Every loop dies at its `review_by` unless re-ratified — no immortal loops.

To suspend all loops for a night without editing this file: put `loops: off` in the
`## Tonight` section of ORDERS.md.

Recognized `cadence` values: `nightly`, `every-2nd-night`, `every-3rd-night`. A loop whose
`budget_per_iteration_usd` exceeds `cost_cap_per_night_usd`, or whose `review_by` is
missing or past, is skipped with the reason logged.

## L-02 — Portfolio night-watch
- status: active
- ratified: <date> (the probe loop — cheapest, lowest risk; start here)
- scope: read-only verification of portfolio state. Check registry rows against reality
  (status column vs BRIEFs/repos/working tree), whether ORDERS.md hang-dry and blocked
  items are still true, night-branch hygiene (list unmerged `night/*` branches per nested
  repo), and any ALERT files present. Writes ONLY: its state file, the night report, and
  `reports/**`. No registry writes, no BRIEF writes, no fixes — findings are observations.
- iteration: one full pass of the checks above, evidence-cited (file paths / line refs /
  git output), sized to a single cheap session.
- cadence: every-3rd-night
- budget_per_iteration_usd: 2
- budget_loop_total_usd: 20
- stop: review_by, or a standup marks it done
- review_by: <next charter revisit>
- definition_of_done_per_iteration: dated section appended to `pm/nights/loops/L-02.md`
  with a verdict per check and evidence for each; discrepancies surfaced in the night
  report under Observations; `next:` and `progress:` lines present.
- out_of_scope: fixing anything found; writing to REGISTRY.md, any BRIEF, or any venture
  directory; re-litigating finance verdicts; anything outside `~/ventures`.
- if_blocked: record the denial verbatim in the state section and the report, mark
  `progress: no` only if the whole pass was impossible, continue remaining checks.

## L-01 — <build loop template: one backlog item per night on a venture site>
- status: parked — activate after finance prices it; first iteration runs as a supervised
  probe per the charter
- ratified: <date>
- scope: one item per night from `pm/nights/loops/L-01-backlog.md`, top unchecked first,
  implemented in `<NNN>-venture/site/` on branch `night/<date>`. Verify with whatever the
  fence allows (`node --check`, a build, a headless browser only if one exists — probe
  clause). Writes ONLY: `<NNN>-venture/site/**` on the night branch, its state file, the
  night report. Never push, never deploy, never touch `main`, never add a dependency.
- iteration: one backlog item, start to finish, or a plainly reported stop.
- cadence: every-2nd-night
- budget_per_iteration_usd: 6
- budget_loop_total_usd: 45
- stop: backlog empty, review_by, or a standup marks it done
- review_by: <next charter revisit>
- definition_of_done_per_iteration: dated section in `pm/nights/loops/L-01.md` naming the
  item, files touched, the verification run, and before/after screenshots if a browser was
  available; the backlog item ticked; `next:` names the following item; `progress: yes|no`.
- out_of_scope: anything not in the backlog; copy changes; analytics changes; any push or
  deploy.
- if_blocked: record it, leave the branch as-is, `progress: no`; do not try a second item.
- hang-dry: the operator reviews `night/<date>` in the browser each morning, merges to
  `main`, pushes; the host deploys.

## L-03 — <weekly source-watch template: read a public source, write candidates only>
- status: active (first iteration supervised)
- ratified: <date>
- scope: once a week, read <the newest issue of a public source your venture depends on>
  for <the notices that matter>. Write candidates only:
  `<NNN>-venture/data/candidates-<date>.md` with one proposed row or cell change per
  finding, each with its source URL and the exact quoted figure. Never edit the ratified
  data files.
- iteration: one issue of the source plus anything published since the last iteration.
- cadence: every-3rd-night   # the wrapper has no weekly cadence; pair with a fire-by in ORDERS if the day matters
- budget_per_iteration_usd: 5
- budget_loop_total_usd: 30
- stop: review_by
- review_by: <next charter revisit>
- definition_of_done_per_iteration: the candidates file exists (even if it says "nothing
  this week"), every candidate cites a URL, and the night report lists the count;
  `pm/nights/loops/L-03.md` gets a dated section; `next:` names the next issue date.
- out_of_scope: writing to the ratified data; estimating any number; outreach.
- if_blocked (source unreachable, WebSearch denied): write the file with a `## Coverage`
  note saying so, `progress: no`, stop.
- hand-off: the operator or the PM reviews candidates at the next standup and accepts rows
  by hand (attended).
