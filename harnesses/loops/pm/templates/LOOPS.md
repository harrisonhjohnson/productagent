# Loops

You edit this file. The agent never can. Each loop is a section with four knobs plus a
review date and a scope. A loop runs only while `status: active`, only on its cadence,
only under its budgets, and never past `review_by`.

Nothing below is active yet. Copy the example out of the comment, give it a real goal
and a real `review_by` date, change `status: draft` to `status: active`, and plug the
laptop in tonight.

<!--
## L-01 — Ship one small fix a night
- status: draft
- goal: Ship one improvement from the backlog each run, verified before it is reported.
- cadence: every-2nd-night
- model: claude-sonnet-5
- budget_per_iteration_usd: 6
- budget_loop_total_usd: 45
- review_by: 2026-10-31
- scope: one item per run from `pm/backlog.md`, top unchecked first, on branch `night/<date>`.
  Never push, never deploy, never touch `main`, never add a dependency.
- definition_of_done_per_iteration: the change is made, checked with whatever the fence
  allows, and a dated section is appended to `pm/nights/loops/L-01.md` ending with
  `next:` and `progress: yes|no`.
- if_blocked: say so plainly in the state file and stop; never guess.
-->
