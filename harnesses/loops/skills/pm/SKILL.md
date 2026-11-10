---
name: pm
description: The morning skill for Loops. Reads last night's runs, checks the reports against the diffs, puts the open decisions in front of you, and writes tonight's orders. Use for the morning check-in ("morning", "read the night", "standup"), to write or change a loop, or to queue a one-off order for tonight.
---

# pm: the morning

Loops does the work at night. This skill is the person-present half: it reads what the
night did, shows you the calls that are yours, and writes down what runs next. It never
lets a report stand in for the diff.

All paths are relative to the Loops folder (`~/loops` by default).

## Read first

1. `pm/CHARTER.md`: the terms. Never override them.
2. `00-ops/night/run-state.json` and `00-ops/night/ALERT.md`. If the last run failed or
   was missed, lead with that.
3. The newest `pm/nights/<date>.md` and `pm/DECISIONS.md` (pending entries only).
4. `pm/ORDERS.md` and `pm/LOOPS.md`.

## Modes

### Morning (the default)

1. **Check the night.** Run `python3 00-ops/health/fleet-health.py --hours 48`, then
   `bash 00-ops/health/judge-night.sh`. The judge grades the report against the diff, A to
   E. Then read `git -C <repo> diff main...night/<date>` yourself for anything graded
   below A.
2. **The board, in eight lines or fewer.** What ran, what changed, which loops are
   parked, what was blocked by the fence. End with *"Nothing here needs you"* or
   *"Two things need you."*
3. **The decisions.** Each pending "Need from you", one at a time, with the evidence and
   a recommendation. Record the answer in `pm/DECISIONS.md`.
4. **Tonight.** Ask one question: *"Anything you want in or out of tonight?"* Then
   update `pm/ORDERS.md`.

A morning that ends in five minutes is a good morning.

### Write a loop

Interview for the parts of a loop section in `pm/LOOPS.md`: goal (one sentence a
stranger understands), scope, cadence, model, per-run and total budget, `review_by`,
definition of done, out of scope, if blocked. New loops start as `trial`. Push back on
any loop that:

- needs a login, a payment, or a person to reply to finish a step
- has no check the run can do itself (a build, a test, a cited source)
- quietly hands judgment to the run ("whatever seems reasonable" is the tell). Make that
  call now, or write it into the loop as a "Need from you".

### Order for tonight

A one-off goes under `## Tonight` in `pm/ORDERS.md` with a definition of done, out of
scope, and if blocked, or it doesn't go out. The first time an order uses something a
run has never tried (a new tool, a network call, a system command), add a cheap probe
and say that a plainly reported denial counts as success.

## Rules

- Sort work before queueing it. Labor with a checkable result goes to the night.
  Judgment, or anything only you can answer, gets done now, in the meeting. Hands-on QA
  (how it feels in a browser or on a device) goes on your list, with the night's branch
  ready for it.
- The diff is the evidence. A report you believed without reading the diff wasn't
  reviewed.
- A blocked run reported straight is a good run.
- A decision that lives only in chat will be made again. Write it to `pm/DECISIONS.md`
  before moving on.
