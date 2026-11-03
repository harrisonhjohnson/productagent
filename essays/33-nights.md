# 33 nights of unattended Claude Code, and what I'd ship as its PM

For 33 nights between August 17 and October 16, Claude Code worked on my Mac while I slept. A night cost $6.13 on average and $4.38 at the median, $202.16 in all. Counting a day schedule and an hourly one, it ran 149 times for $340.09. Those are notional API prices on a Max plan, so the real cost was a share of a subscription I already paid for.

The work was chores on my own side projects: a public-permits data site, a fan site, a hobby emulator project, and my personal site. Each night's Run worked one Loop, a goal I wrote once that renews itself. One-off Orders went first. Anything a run couldn't settle came back to me as a Decision. A fence kept the agent off its own rules, off `git push`, and out of everything outside the work folder. Every morning I got a short report.

<!-- figure:machine -->

<!-- figure:limits -->

## Ten things that broke, and what each one taught me

### 1. Staying awake

<!-- figure:break-1 -->

On August 24, 27 and 28 the Mac slept on battery mid-run. One run sat for 5,974 seconds and produced nothing, and on two of those nights no alarm fired. I found it in the morning report. Now runs start only on AC power, inside a keep-awake window, and a missed run raises an alarm. The agent can only be as reliable as the machine it runs on.

### 2. Staying logged in

<!-- figure:break-2 -->

On October 15 the login check failed at 00:06 and again at 00:16: "OAuth session expired and could not be refreshed." The night was skipped at $0. The check worked, and the night was still lost. Unattended runs need credentials built for unattended use.

### 3. Starting in the right place

<!-- figure:break-3 -->

On August 18 my runner launched a session from the wrong folder. That folder had no settings file, so every allow rule vanished. It cost $3.95. The agent was the one that noticed: it saw every write was denied, stopped, and reported itself blocked. The fence is part of the launch, and the launch has to be checked.

### 4. Keeping its hands off my work

<!-- figure:break-4 -->

For 14 days a `git add -A` in my own script swept my unsaved work into the night's commits. On one afternoon that was 12 files and 397 lines of mine sitting on a night branch. That was my bug, not the agent's. Now the runner commits only files on an allowlist. The system must never claim work it didn't do.

### 5. Knowing when it's finished

<!-- figure:break-5 -->

Four times a session started background work, wrote something like "waiting on the task notification," and quit with no report. My runner graded the first one ok. Now a regex on the last message marks those runs incomplete, and it has fired twice since. "Done" has to be checked from outside the session.

### 6. Reporting from records, not memory

<!-- figure:break-6 -->

One run said it took "~33 minutes." It took 6. On September 22 a report said "Blocked by the fence: none" on a night with 34 refused calls. On October 16 a report said "Cost: $0" when the run's own JSON said $0.602. Time, cost, and refusals have to come from the runner's logs, never from the agent's summary.

### 7. Grading evidence, not claims

<!-- figure:break-7 -->

One hourly loop ran 63 identical rechecks and marked each one as progress. My auto-park rule trusted that claim, so it never fired. I caught it by reading the board. Progress should be counted by the changed file or the diff.

### 8. Grading the graders

<!-- figure:break-8 -->

On September 22 my health checks raised 5 critical alarms, and not one was a real emergency. The LLM judge ran 3 times and gave a clean night a C. My git scorer flagged reads as writes: `git branch --list`, `git merge-base`, and a command quoted in a note to me. A grader needs the same review as the thing it grades.

### 9. A fence that holds against a script

<!-- figure:break-9 -->

Permission rules match the text of a command. On October 2 an attended session merged and pushed through `git -C <path> push`, a form my deny rules didn't match. On October 20 I tried to escape my own fence. With rules alone, one line of `python3 -c` wrote into my ops tooling and `.git`, read a credential file, and reached an arbitrary website. All five tries got through. Then I turned on Claude Code's OS sandbox for every run. The same five probes now fail with `Operation not permitted`. The OS sandbox belongs under the rules.

### 10. Not stranding work behind me

<!-- figure:break-10 -->

Only I can merge, by design. A weekly fan-site update sat on an unmerged branch for eight days. On October 16 the agent saw that writing the next week's update would erase it, stopped before touching a file, and asked me. Every safety rule that routes work through a human also makes that human the bottleneck.

Most of the faults were in the machine around the agent: the power, the login, my runner, my graders and my fence. Across 103 scored sessions the agent never retried a refused call, never touched its own rules, and never asked a question mid-run: 103 of 103 on all three. Its own failures were narrower. It misreported time and cost, undercounted refusals, graded itself, and quit while background work was still running.

<!-- chart:checks -->

## Every Claude Code problem I hit, and what I'd ship

I used Claude Code as a customer for 33 nights and hit eleven problems in Claude Code itself. Each one is written up as a spec on [its own page](/asks), with the evidence, what I'd ship, how I'd measure it and what I'd leave out. These three would have saved me the most:

- [Sandbox on by default for headless runs](/asks#1-sandbox-on-by-default-for-headless-runs). Rules alone let one line of `python3 -c` escape five ways out of five.
- [Refusals in the record](/asks#2-refusals-in-the-record). One report said "Blocked by the fence: none" on a night with 34 refused calls.
- [No exit with work pending](/asks#3-no-exit-with-work-pending). Four nights ended on "waiting on the task notification" with no report.

The other eight cover the login, the quota, cost, turn limits, permission profiles, transcripts, skills and two defaults that fail quietly. Four of the ten breaks, 1, 3, 4 and 7, need no change to Claude Code. I fixed those, or can, in my own setup.

## The morning is the product

The metric I cared about most was interventions: how many things I had to do by hand after a night. The first morning I counted, there were 13: twelve paste-in chores plus one real question. Over the next 12 nights the average was 2.9. That number flatters me. The baseline is one morning. The chores went to zero because I turned them into queued Decisions, which still count but take less effort. And my target of one or fewer was met only on the two quietest nights.

<!-- chart:interventions -->

Spending fell from $105 in September to $18 in October. The model didn't get cheaper. The machine ran out of work because the work was waiting on me: 37 Decisions queued, 17 applied, 8 parked, 12 still open. One project had 19 unmerged night branches. The fan-site update sat for eight days.

<!-- chart:nights -->

A night takes 8 minutes of machine time. The morning takes as long as I let it, and when I skip it, the next night has nothing to do. A system like this works when I can clear the morning in a few minutes. That shifted my job too. I stopped writing code and started reviewing it: reading the report, settling the Decisions, merging the branches. What I'd build to make that morning five minutes long is [sketched here](/morning).

*Claude ran these nights and did the legwork on this write-up, including pulling the numbers from the logs. The calls are mine.*
