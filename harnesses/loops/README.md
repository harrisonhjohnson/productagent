# Loops

A loop is a piece of work you describe once and an agent keeps doing, one bounded run at
a time, while you are asleep or away. You set four knobs. The machine does the rest inside
a fence it cannot climb. In the morning you read four sentences per loop and make the
decisions only you can make.

This is the harness I run on my own portfolio every night. Everything here is copied off
my machine and scrubbed. Start with this page; go to [MACHINE.md](MACHINE.md) when you
want to know how the runner, the fence and the morning judge actually work.

## Four words

| Word | Meaning |
|---|---|
| **Loop** | Work with a goal that renews itself. Lives in `pm/LOOPS.md`. You edit that file; the agent never can. |
| **Run** | One bounded pass at one loop. Happens unattended, on a schedule, under a budget and a timeout. |
| **Order** | A one-off instruction for tonight. Orders go first; loops fill the remaining slots. |
| **Decision** | Anything the run could not settle on its own. It comes back to you in the morning, never gets guessed at. |

## Four knobs

Every loop is a section in `pm/LOOPS.md` with these lines. Everything else in the section
is scope and safety rails; these four are what you touch day to day.

```
## L-03 — Site improvements
- status: trial
- goal: Ship one improvement from the backlog each run, verified before it is reported.
- budget_per_iteration_usd: 6
- budget_loop_total_usd: 45
- cadence: every-2nd-night
- model: claude-sonnet-5
```

- **goal** — one plain sentence a stranger would understand.
- **budget** — dollars per run, and dollars for the whole loop. The runner counts runs and stops the loop when the total is spent.
- **cadence** — `nightly`, `every-2nd-night`, `every-3rd-night`, or `weekly`.
- **model** — which Claude runs it. Cheap watch loops on Sonnet, build loops on Opus or Fable. A cost dial, not a quality flag.

## Five states

`draft` (has a goal, never run) → `trial` (first three runs, you review each one) →
`active` (unattended) → `parked` or `done`. A loop that makes no progress two runs in a
row parks itself. Every loop has a review-by date; nothing runs forever.

## What you read in the morning

Each run ends with four lines per loop, in plain speech, each claim pointing at the file
it came from:

```
## L-03
- Trying to: ship the "sort permits by county" backlog item.
- Did: added the county filter and checked the page renders in a headless browser.
- Decided: left the mobile layout alone; it is a separate backlog item.
- Need from you: merge branch night/2026-09-14 if the screenshot looks right.
- Where to look: pm/nights/loops/L-03.md, 009-site/app/permits.tsx
```

If the four lines are missing, the run is not done. That rule is in the loop's
definition of done, and the morning judge checks for it.

## From your phone

The [TODO harness](../todo/README.md) ships the Telegram bot that is the write path for
loops: `/loops` lists every loop with its state, knobs and last run; `/loop L-03 budget 5`,
`/loop L-03 model sonnet`, `/loop L-03 pause` change the knobs; `/loops standup` reads
back this morning's four lines. Every edit lands in `pm/LOOPS.md`, dated and marked as
yours.

## While you sleep, literally

Close the laptop at night. Open it in the morning to work that got done. The hours you
are asleep become the hours the agent works, on your own Mac and your own Claude plan,
with no server to rent and nothing phoning home.

A Mac naps the second you close it. This folder carries the settings that keep it working
under a closed lid for as long as a run takes, then let it sleep again.

Fine print: by default the machine waits until the Mac is plugged in and never runs under
thirty percent battery, so you do not wake up to a dead laptop. Both are settings in
`pm/CHARTER.md`. To skip a night, tell the bot `pause`.

## What it will never do

Spend beyond the budget dial, push code, merge, widen its own permissions, edit its own
orders or loops, ask you a question mid-run, or claim a time or a cost (the wrapper's
envelope is the only authority on those). See the fence in [settings.json](settings.json).

## Adopting it

1. Copy `settings.json` into your project's `.claude/` and read every allow and deny line.
2. Copy `pm/CHARTER.md` and set the dials: model, caps, orders per night.
3. Write one loop in `pm/LOOPS.md` with a goal you would be happy to see done badly the first time.
4. Wire `ops/capture/poller.sh` to launchd (see [MACHINE.md](MACHINE.md)) or run `ops/night/run-night.sh` by hand for a week first.
5. Read the four lines each morning. Promote the loop to `active` after three runs you were happy with.

The spec that ratified all this, with the reasoning and the failure modes, is in
[loops-spec.md](loops-spec.md).
