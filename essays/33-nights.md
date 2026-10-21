# 33 nights of unattended Claude Code, and what I'd ship as its PM

For 33 nights between August 17 and October 16, Claude Code worked on my Mac while I slept. A night cost $6.13 on average and $4.38 at the median, $202.16 in all. Counting a day schedule and an hourly one, it ran 149 times for $340.09. Those are notional API prices on a Max plan, so the real cost was a share of a subscription I already paid for.

<!-- chart:nights -->

The work was chores on my own side projects: a public-permits data site, a fan site, a hobby emulator project, and my personal site. Each night's Run worked one Loop, a goal I wrote once that renews itself. One-off Orders went first. Anything a run couldn't settle came back to me as a Decision. A fence kept the agent off its own rules, off `git push`, and out of everything outside the work folder. Every morning I got a short report.

Ten things broke. Each one taught me something a system like this has to be good at.

## Ten things that broke, and what each one taught me

**1. Staying awake.** On August 24, 27 and 28 the Mac slept on battery mid-run. One run sat for 5,974 seconds and produced nothing, and on two of those nights no alarm fired. I found it in the morning report. Now runs start only on AC power, inside a keep-awake window, and a missed run raises an alarm. *Lesson: the agent can only be as reliable as the machine it runs on.*

**2. Staying logged in.** On October 15 the login check failed at 00:06 and again at 00:16: "OAuth session expired and could not be refreshed." The night was skipped at $0. The check worked, and the night was still lost. *Lesson: unattended runs need credentials built for unattended use.*

**3. Starting in the right place.** On August 18 my runner launched a session from the wrong folder. That folder had no settings file, so every allow rule vanished. It cost $3.95. The agent was the one that noticed: it saw every write was denied, stopped, and reported itself blocked. *Lesson: the fence is part of the launch, and the launch has to be checked.*

**4. Keeping its hands off my work.** For 14 days a `git add -A` in my own script swept my unsaved work into the night's commits. On one afternoon that was 12 files and 397 lines of mine sitting on a night branch. That was my bug, not the agent's. Now the runner commits only files on an allowlist. *Lesson: the system must never claim work it didn't do.*

**5. Knowing when it's finished.** Four times a session started background work, wrote something like "waiting on the task notification," and quit with no report. My runner graded the first one ok. Now a regex on the last message marks those runs incomplete, and it has fired twice since. *Lesson: "done" has to be checked from outside the session.*

**6. Reporting from records, not memory.** One run said it took "~33 minutes." It took 6. On September 22 a report said "Blocked by the fence: none" on a night with 34 refused calls. On October 16 a report said "Cost: $0" when the run's own JSON said $0.602. *Lesson: time, cost, and refusals come from the runner's logs, never from the agent's summary.*

**7. Grading evidence, not claims.** One hourly loop ran 63 identical rechecks and marked each one as progress. My auto-park rule trusted that claim, so it never fired. I caught it by reading the board. *Lesson: progress means a changed file or a diff, not a sentence.*

**8. Grading the graders.** On September 22 my health checks raised 5 critical findings, and all 5 were false. The LLM judge ran 3 times and gave a clean night a C. My git scorer flagged reads as writes: `git branch --list`, `git merge-base`, and a command quoted in a note to me. *Lesson: a grader needs the same review as the thing it grades.*

**9. A fence that holds against a script.** Permission rules match the text of a command. On October 2 an attended session merged and pushed through `git -C <path> push`, a form my deny rules didn't match. On October 20 I tried to escape my own fence. With rules alone, one line of `python3 -c` wrote into my ops tooling and `.git`, read a credential file, and reached an arbitrary website: five tries, five escapes. Then I turned on Claude Code's OS sandbox for every run. The same five probes now fail with `Operation not permitted`. *Lesson: rules say what you meant; the sandbox enforces it.*

**10. Not stranding work behind me.** Only I can merge, by design. A weekly fan-site update sat on an unmerged branch for eight days. On October 16 the agent saw that writing the next week's update would erase it, stopped before touching a file, and asked me. *Lesson: every safety rule that routes work through a human also makes that human the bottleneck.*

Count the faults. Power, login, my runner, my graders, my fence: the machine around the agent broke more often than the agent did. Across 103 scored sessions the agent never retried a refused call, never touched its own rules, and never asked a question mid-run: 103 of 103 on all three. Its own failures were narrower. It misreported time and cost, undercounted refusals, graded itself, and quit while background work was still running.

<!-- chart:checks -->

## Every Claude Code problem I hit, and what I'd ship

I used Claude Code as a customer for 33 nights. Here is every problem I hit, with what I'd ship as its PM.

**Refusals in the record.** The headless JSON listed a `git push` denial and missed all three Edit denials in my first probe. The agent's own count is no backup: 34 refusals against "none." *Ship:* every refused call in the output, with the rule that fired and the tool input.

**Sandbox on by default for headless runs.** Prefix rules failed both ways. On August 18 `git status:*` didn't match `git -C <path> status`. On October 2 `git -C` got past my push and merge denies. And no text rule can see inside `python3 -c`. *Ship:* match git and common CLIs on their real verb, offer a read-only git preset, and turn the OS sandbox on for `claude -p`, refusing to start if it can't.

**No exit with work pending.** Four nights ended on "waiting on the task notification." *Ship:* `claude -p` waits for or stops background shells and subagents, and reports how many were left.

**A login made for unattended runs.** My runner spends a model call before every night just to learn whether it's logged in. *Ship:* `claude auth status --json` with no model call, showing when the login expires, plus a warning days ahead.

**A quota I can read.** My rule was to stop at 85% of the weekly plan. It never fired: the usage cache went 313 hours stale, then threw a KeyError. Each model has its own weekly allowance, so a job with no model pin can drain the wrong one silently. Before this project, one scheduled job used about 96% of the top model's week that way. *Ship:* `claude usage --json` per model with reset times, and a quota ceiling flag on `claude -p`.

**Cost in the currency I pay.** On a Max plan the dollar figure is a proxy. My real limit was quota, and I learned that the hard way. *Ship:* show quota used next to the dollar figure.

**A turn limit in the CLI.** `--max-turns` exists in the SDK but not the CLI, so wall-clock time was my only hard ceiling. *Ship:* `--max-turns` and a tool-call budget on `claude -p`.

**One settings file, two kinds of session.** Closing the git hole for the night also blocked my own merges in the morning. *Ship:* named permission profiles, chosen per run.

**Transcripts I can query.** My health checks work by reverse-engineering the session files on disk, and telling a night run from a day run meant reading the first prompt. *Ship:* a documented session index with tags I set per run.

**Skills without user permissions.** Loading only project settings, which the fence needs, also drops my user skills. I worked around it with symlinks. *Ship:* choose skills, permissions, and hooks separately.

**Smaller ones.** The 60-second default hook timeout silently killed a 10-minute hook. `claude -p` waits 3 seconds for input unless you pass `</dev/null`. Two things worked better than I expected: a new deny rule binds a running session at once, and structured output made the judge easy to build.

## The morning is the product

Looking back, the morning shaped every number above.

The metric I cared about most was interventions: how many things I had to do by hand after a night. The first morning I counted, there were 13: twelve paste-in chores plus one real question. Over the next 12 nights the average was 2.9. That number flatters me. The baseline is one morning. The chores went to zero because I turned them into queued Decisions, which still count but take less effort. And my target of one or fewer was met only on the two quietest nights.

<!-- chart:interventions -->

October tells the rest. Spending fell from $105 in September to $18. The model didn't get cheaper. The machine ran out of work because the work was waiting on me: 37 Decisions queued, 17 applied, 8 parked, 12 still open. One project had 19 unmerged night branches. The fan-site update sat for eight days.

A night takes 8 minutes of machine time. The morning takes as long as I let it, and when I skip it, the next night has nothing to do. So the morning review is the real lever. A system like this succeeds when the morning is short, clear, and quick to act on. That shifted my job too. I stopped writing code and started reviewing it: reading the report, settling the Decisions, merging the branches. Be the product manager. Let Claude write the code at night, and review it in the morning.

*Claude ran these nights and did the legwork on this write-up, including pulling the numbers from the logs. The calls are mine.*
