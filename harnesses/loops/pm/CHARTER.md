# Charter

The terms every run works under. You edit this file; the agent reads it first and never
overrides it. Runs **cannot edit it**: the fence denies `pm/CHARTER.md`, so caps and rules
only change while a person is at the keyboard.

To change behavior, edit here. Everything below the line `## Dials` is read by the runner,
so keep the `- key: value` shape.

## Who this is for

<one or two sentences: your product, your team, and what "good" looks like. Example: "A
four-person team building a scheduling app for clinics. Good means fewer support tickets
and a shorter path from signup to first booking.">

## Where the work lives

- This folder (`~/loops` by default) holds the machine: `00-ops/`, `pm/`, `docs/`.
- Put each product repo you want worked on inside it as its own folder, for example
  `~/loops/app/`. Any folder here with its own `.git` gets a `night/<date>` branch before
  each run, and the run's changes are committed there. Your `main` is never touched.
- In the morning you review the branch, merge it yourself, and push it yourself.

## Dials

- paused: no
- night_orders_per_night: 2   # orders + loop runs per night, in total
- wip_limit: 2                # a guideline for you: keep this many loops running at most

### Agent and model
- agent: claude   # claude | codex
- model: claude-sonnet-5   # default for loops that don't name one
- effort: medium

### Budget
On a Claude or ChatGPT plan, dollars here are API-equivalent estimates. What you actually
spend is your plan's weekly allowance; the caps keep a night from eating it.
- timeout_minutes: 75
- cost_cap_per_night_usd: 15
- cost_cap_rolling_7day_usd: 45
- monthly_cost_cap_usd: 120
- plan_floor_percent: 20      # don't start if less than this share of the plan's week is left
- five_hour_max_percent: 90   # don't start if the five-hour window is this full
- plan_weekly_usd_equivalent:  # optional; leave blank until a few runs calibrate it
- codex_usd_per_m_input: 1.25  # Codex only: it reports tokens, not dollars
- codex_usd_per_m_output: 10

### Power
- min_battery_percent: 30
- planner: off   # off | rules | model; experimental, leave off

Every report ends with a cost line. Two overruns in a row pause night runs until you
look.

## When it runs

- On power. A Mac with the lid shut on battery sleeps mid-run, so the checker waits for
  the charger. Lid open on battery works if the charge is at least 50%.
- In the first window the Mac is awake and plugged in, not at a fixed hour.
- The watchdog alarms only when a run *could* have happened and didn't. A laptop in a
  drawer for a week alarms no one.

## Orders and loops

- An **order** is one-off work for tonight, in `pm/ORDERS.md` under `## Tonight`. Orders
  run first.
- A **loop** is a standing goal in `pm/LOOPS.md`. It runs one bounded step per night on
  its cadence until it is done, parked, or past its `review_by` date.
- Every order and loop states three things or it does not run: **definition of done**,
  **out of scope**, and **if blocked**.
- New loops start as `trial`. You read the first three runs before trusting the output,
  then change the status to `active` yourself.
- Two runs in a row with `progress: no` park a loop. It stays parked until you resume it.
- Every loop has a `review_by` date. Past that date it stops.
- `loops: off` under `## Tonight` skips every loop for one night.
- The runner decides what is runnable (cadence, budgets, parking). The agent never
  re-decides.

## The morning report

Every loop's section in `pm/nights/<date>.md` ends with four lines, each under 25 words,
plain speech:

- Trying to: the goal, in a sentence.
- Did: what changed, with file paths.
- Decided: any call the run made on its own, so you can reverse it.
- Need from you: the calls that are yours, or "nothing".

A run without the four lines is not done. Every "Need from you" line becomes a pending
decision in `pm/DECISIONS.md`.

To check a report against the actual diff, run
`bash ~/loops/00-ops/health/judge-night.sh`. A second model grades the report against
`git diff main...night/<date>`.

## What a run may touch

Allowed:
- `pm/nights/**`: reports and loop state. Append only.
- `pm/DECISIONS.md` and `pm/LOG.md`: append only.
- Product repos inside this folder, on the `night/<date>` branch the runner made.
- `reports/**` for research and notes that don't belong in a repo.

Never, with no one awake:
- `git push`, merge, deploy, publish, or any change to `main`.
- Spending money, signing up for anything, or creating keys.
- Sending email or messages. Runs start with zero MCP servers, so mail, chat, CRMs and
  deploy hosts don't exist inside them.
- Writing outside this folder.
- Editing `00-ops/`, `.claude/`, `pm/CHARTER.md`, `pm/ORDERS.md` or `pm/LOOPS.md`. The
  agent can't rewrite its own orders, raise its own budget, or hide a failed run.
- Adding a dependency, or deleting files it did not create tonight.

`.claude/settings.json` enforces this list, and the macOS sandbox backs it up. When a run
hits the fence, it writes the denial into the report and moves on. A plainly reported
denial counts as a good run.

## What a run decides alone, and what it only proposes

Decides alone: how to do the step it was given, inside its scope. It notes each choice
under "Decided" so you can reverse it.

Only proposes, under "Need from you":
- anything outside the loop's scope
- product calls: pricing, copy that ships, naming, what to cut
- anything that needs a login, a person, or money
- a new loop, or a change to an existing one
