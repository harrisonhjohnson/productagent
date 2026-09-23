# Self-maintenance lane

The morning after an unattended run used to be a paste session. The night would find a
loop that should slow down, a rule that needed one more line, a fenced file that needed a
five-line fix, and it would write all of that up as "need from you" prose. One morning I
counted thirteen interventions: twelve paste blocks and one real decision. The machine was
doing the thinking and handing me the typing.

This lane inverts that. The unattended run may keep its own registry tidy, but only
downward, and every ask it cannot settle becomes a row in one file that I can settle with
one command. A "need from you" is a decision, never a paste. The number the machine is
judged by is how many times the morning had to act.

This is the harness I run alongside [Loops](../loops/). It is one Python file, one
vendored helper, and three conventions. Everything here is copied off my machine and
scrubbed.

## The rule

An unattended run may:

- **park** a loop, **finish** a loop, or **slow** its cadence. Never the reverse: no loop
  goes from parked to active, no goal, budget or review date changes, without a human.
- **queue a decision** for anything else, carrying the command or the patch that would do
  the work once you say so.
- **log an environment issue** and its workaround, so the next run does not rediscover it.

You, at a terminal, **apply** or **park** each decision. That is the whole interface.

## The commands

The night or day lane runs these:

```
loopctl.py park    L-NN "<why>"            status → parked
loopctl.py done    L-NN "<why>"            status → done
loopctl.py cadence L-NN <cadence>          nightly | every-2nd-night | every-3rd-night | weekly
loopctl.py decide  <pod> "<one sentence>"  [--apply "<command>"] [--patch <file>]
loopctl.py issue   <pod> "<error verbatim>" "<workaround>"
loopctl.py interventions [YYYY-MM-DD]      the metric
```

You run these:

```
loopctl.py apply  D-NNN          run the row's apply command or git-apply its patch, tick it
loopctl.py park-decision D-NNN   tick it as parked; nothing runs
```

Three newer commands ship in the same file because they share its plumbing: `check` runs a
loop's `checks:` block as facts, `model` moves a loop's model pin behind a floor, and
`guard` puts a loop back on the default model after repeated failures. They are one week old
on my machine and the charter has not yet granted the night the right to use `model`. Read
the code before relying on them; the six commands above are the harness.

## The decisions file

`pm/nights/DECISIONS.md`, append-only for the machine. One row per ask:

```
- [ ] D-011 · ops · 2026-09-22 · The runner should append the envelope's refused calls to every report. Apply third.
      patch: pm/nights/patches/2026-09-22-report-fence-section.patch
- [ ] D-013 · site · 2026-09-23 · Move the permit-watch loop to a cheaper model? The floor is met.
      apply: LOOPCTL_ATTENDED=1 python3 00-ops/night/loopctl.py model L-10 claude-sonnet-5
```

The pod is which product or venture the ask belongs to. A row with an `apply:` line runs
that shell command from the workspace root. A row with a `patch:` line runs `git apply` on
that file. A row with neither is a judgment call: decide, then tick it by hand. `apply`
ticks `[x]`, `park-decision` ticks `[~]`. The ticks are the audit trail; rows are never
deleted. See [examples/DECISIONS.md](examples/DECISIONS.md).

## Patches for fenced files

The night lane cannot write to its own runner, its charter, or its health desk. That fence
is the point. So when a run finds a fix those files need, it writes the diff to
`pm/nights/patches/<date>-<name>.patch` and queues a decision with a `patch:` line. It never
applies it. The morning after, one command per patch.

This is also how I work in an attended session when the same fence is on. Today's example:
four patches to the runner, the prompt, the health desk and the watchdog, built against
copies, checked on a mirror tree, queued as four rows, applied with four commands.

## Pod issues

`pm/nights/pods/<pod>-issues.md`, append-only. An environment error the run worked around,
verbatim, with the workaround beside it. The prompt tells every run to read its pod's file
before starting a loop there, so a portal with a broken certificate is discovered once, not
nightly. See [examples/pods/site-issues.md](examples/pods/site-issues.md).

## The metric

```
$ python3 00-ops/night/loopctl.py interventions 2026-09-22
2026-09-22 interventions=4 (need-lines=2 paste-blocks=0 decisions-queued=2 errors-seen=1)
```

Need lines that are not "nothing", indented paste blocks in the report, and decisions
queued that day. The runner stamps this line on the bottom of every report. Baseline was
thirteen. The target is at most one per pod per night, and a queued decision with an
`apply:` line counts as one because that is what a decision costs you: one word.

## Install

1. Copy `loopctl.py` and `loops_registry.py` into `00-ops/night/` beside the Loops runner.
   `LOOPS_HOME` names the workspace root (default `~/ventures`).
2. Add the lane to the charter's blast-radius section. Mine reads, in short: the machine may
   edit `pm/LOOPS.md` only through `loopctl park | done | cadence`; it may append to
   `pm/nights/DECISIONS.md`, `pm/nights/patches/**` and `pm/nights/pods/**`; every write is
   logged; nothing else in the registry moves without a human.
3. Deny the lane's own edit tools on `pm/LOOPS.md`, so loopctl is the only door.
4. In the prompt, replace "tell the user what to paste" with: queue it. The wording I use is
   in the Loops harness prompt under "A need is a decision, never a paste."
5. Have the runner call `interventions` after each run and stamp the line on the report.

## Security notes

- `apply` runs a shell line read from a markdown file the unattended lane can append to. The
  `LANE` guard stops a lane applying its own rows, but a row with a hostile `apply:` line waits
  for your hand. Treat the decisions file as a queue of pull requests, not a to-do list: read
  the row, and the patch, before you apply it.
- `git apply` touches only what the diff names, but a diff can name anything the repo holds.
  Read it.
- Leave `loopctl_may_set_model: no` in the charter until the bench has produced settled passes
  on real work. Granting it lets an unattended run rewrite a loop's model pin.
- The checks are advisory. A failing check never stops the run; the fence is the gate.
