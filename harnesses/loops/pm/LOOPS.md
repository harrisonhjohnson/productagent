# Loops

You edit this file. Runs never can; the fence denies it. Each loop is one section: a goal,
a cadence, a model, a budget, a review date, and the rails around it.

The runner reads this file each night and decides which loops may run (status, cadence,
budgets, parking). The agent runs one bounded step per runnable loop, after any orders in
`pm/ORDERS.md`, within `night_orders_per_night`.

Each run appends a dated section to `pm/nights/loops/<id>.md`. It re-checks the last
run's main claim before building on it, and ends with `next:`, `progress: yes|no`, and
the four lines (Trying to, Did, Decided, Need from you).

- `status`: `draft` · `trial` · `active` · `parked` · `done`. Only `trial` and `active` run.
- `cadence`: `nightly` · `every-2nd-night` · `every-3rd-night` · `weekly`.
- Runs allowed = `budget_loop_total_usd` ÷ `budget_per_iteration_usd`.
- A loop whose per-run budget is above `cost_cap_per_night_usd`, or whose `review_by` is
  missing or past, is skipped and the reason is logged.

The three loops below are examples for a product team. Change the repo paths, goals and
dates before setting any of them to `trial`.

## L-01 — Ship one backlog fix a night
- status: draft
- goal: Close one small item from the product backlog each run, checked before it is reported.
- cadence: every-2nd-night
- model: claude-sonnet-5
- budget_per_iteration_usd: 6
- budget_loop_total_usd: 45
- review_by: <a date about four weeks out>
- scope: one item per run from `pm/backlog.md`, top unchecked first, in `app/` on the
  `night/<date>` branch. Check it with the project's own build and tests. Writes only the
  repo, its state file, and the night report.
- iteration: one backlog item, start to finish, or a plainly reported stop.
- definition_of_done_per_iteration: the change builds and its tests pass; the state file
  names the item, the files touched and the command that checked it; the item is ticked
  in the report (not in `pm/backlog.md`, which you tick when you merge); `next:` names
  the following item.
- out_of_scope: anything not on the backlog; copy that ships; new dependencies; analytics.
- if_blocked: record it, leave the branch as is, `progress: no`, and don't start a second item.
- morning: review `night/<date>`, merge it yourself, push it yourself.

## L-02 — Repo health check
- status: draft
- goal: Tell me each week what is broken, stale or drifting in the repo, with evidence, and fix nothing.
- cadence: weekly
- model: claude-haiku-4-5
- budget_per_iteration_usd: 2
- budget_loop_total_usd: 20
- review_by: <a date about six weeks out>
- scope: read only. Run the build and tests and record failures. List TODOs older than 90
  days, unmerged `night/*` branches, and docs that name files that no longer exist.
  Writes only its state file and the night report.
- iteration: one full pass of the checks above.
- definition_of_done_per_iteration: one verdict per check, each with a path, line or
  command output as evidence.
- out_of_scope: fixing anything it finds. Findings go under "Need from you" as proposed
  orders.
- if_blocked: record the denial word for word, keep going with the other checks, and mark
  `progress: no` only if no check could run.

## L-03 — Weekly research digest
- status: draft
- goal: Read what changed this week in <a competitor, a standard, or a customer forum> and write up what matters to us.
- cadence: weekly
- model: claude-sonnet-5
- budget_per_iteration_usd: 4
- budget_loop_total_usd: 30
- review_by: <a date about six weeks out>
- scope: public pages only. Write `reports/research-<date>.md`: up to five findings, each
  with its source URL, a quote, and one line on why it matters to the product.
- iteration: everything published since the last run's date.
- definition_of_done_per_iteration: the report exists, even if it says "nothing new this
  week"; every finding cites a URL; `next:` gives the date to read from.
- out_of_scope: guessing numbers, logging in anywhere, contacting anyone.
- if_blocked (source unreachable or web access denied): write the report with a
  `## Coverage` note saying so, `progress: no`, stop.
