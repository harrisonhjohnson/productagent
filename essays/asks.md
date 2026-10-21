# Eleven Claude Code asks, written as specs

These are the eleven Claude Code problems from [33 nights of unattended runs](/33-nights), written the way I would hand them to an engineering team: the problem, the evidence from my own nights, what I'd ship, how I'd know it worked, and what I'd leave out. They are ranked by how much each would have saved me.

I wrote them as a customer. I don't know the roadmap, and some of these may already be in progress or shipped by the time you read this. The evidence is real and dated; the numbers are on [the receipts](/evidence).

## 1. Sandbox on by default for headless runs

**Problem.** Permission rules match the text of a command. They miss forms the author didn't think of, and they can't see inside an interpreter at all.

**Evidence.** On August 18, `git status:*` didn't match `git -C <path> status`. On October 2, `git -C <path> push` got past my push deny in an attended session. On October 20, with rules alone, one line of `python3 -c` wrote into my ops tooling and `.git`, read a credential file, and reached an arbitrary website: five tries, five escapes. With the OS sandbox on, all five fail with `Operation not permitted`.

**Ship.** `claude -p` runs inside the OS sandbox by default and refuses to start if the sandbox is unavailable, with an explicit flag to opt out. Rules for git and other common CLIs match the parsed verb, not the prefix. A read-only git preset ships in the box.

**Measure.** Share of headless sessions that run sandboxed. A public escape-probe suite that passes on every release.

**Not doing.** Turning the sandbox on by default for interactive sessions. There, a person reads the prompts, and a surprise break costs more than it saves.

## 2. Refusals in the record

**Problem.** The headless output doesn't reliably list refused calls, and the agent's own summary undercounts them.

**Evidence.** In my first probe, the JSON listed a `git push` denial and missed all three Edit denials. On September 22 a report said "Blocked by the fence: none" on a night with 34 refused calls.

**Ship.** Every refused call in `--output-format json`: the tool, its input, the rule that fired, and the settings file that rule came from.

**Measure.** The refusal count in the JSON matches the count in the transcript on every run.

**Not doing.** Asking the model to report refusals more carefully. Counts belong to the runner, not the agent.

## 3. No exit with work pending

**Problem.** A headless session can end while its own background shells or subagents are still running, and leave no result.

**Evidence.** Four nights ended on "waiting on the task notification" with no report. My runner graded the first one ok.

**Ship.** `claude -p` waits for background work, or stops it, before it exits, with a timeout I can set. The result says how many tasks were pending and what happened to each.

**Measure.** Headless sessions that exit with untracked background work: zero.

**Not doing.** Retrying automatically. Whether to retry is the runner's call.

## 4. A login made for unattended runs

**Problem.** A scheduled job has no cheap way to know, before it starts, whether its login will hold.

**Evidence.** On October 15 the login check failed at 00:06 and again at 00:16: "OAuth session expired and could not be refreshed." The night was skipped. My runner spends a model call before every night just to learn whether it is logged in.

**Ship.** `claude auth status --json` that makes no model call and says when the login expires, plus a warning in interactive sessions days before it does.

**Measure.** Nights lost to an expired login: zero. Cost of the check: zero.

**Not doing.** Silent re-login from a scheduled job. Credentials should change only when a person is there.

## 5. A quota I can read

**Problem.** On a plan, the real limit is quota, and a script can't read it. Each model has its own weekly allowance, so a job with no model pin can drain the wrong one.

**Evidence.** My rule was to stop at 85% of the weekly plan. It never fired: the usage cache I read went 313 hours stale, then threw a KeyError. Before this project, one scheduled job with no model pin used about 96% of the top model's week.

**Ship.** `claude usage --json` per model with reset times. A quota ceiling flag on `claude -p`. A warning when a headless run starts with no pinned model.

**Measure.** Unattended runs that cross the ceiling the user set: zero.

**Not doing.** Choosing a cheaper model on the user's behalf when quota runs low. Say so and stop; let the person choose.

## 6. Cost in the currency I pay

**Problem.** On a plan, the result reports dollars at API prices. That number is a proxy; the limit that bites is quota.

**Evidence.** 149 runs came to $340.09 at API prices, all on a plan I already paid for. The number I needed, the share of the week each run used, was not in the result.

**Ship.** Quota used, per model, next to `total_cost_usd` in the result.

**Measure.** Users on a plan who can answer "what share of my week did last night use" from the result alone.

**Not doing.** Dropping the dollar figure. It is still the best way to compare runs.

## 7. A turn limit in the CLI

**Problem.** `--max-turns` exists in the SDK but not the CLI, so wall-clock time is the only hard ceiling on a headless run.

**Evidence.** My step budget of 300 tool calls could only be checked after the fact, by scoring transcripts the next morning.

**Ship.** `--max-turns` and a tool-call budget on `claude -p`. When the budget runs out, the session stops cleanly and the result says so.

**Measure.** Headless runs that stop on budget instead of on a timeout kill.

**Not doing.** A default budget. The right number depends on the job.

## 8. Named permission profiles

**Problem.** One settings file serves two kinds of session: the agent alone at night, and me at the keyboard in the morning.

**Evidence.** Closing the git hole for the night also blocked my own merges in the morning.

**Ship.** Named profiles in settings, chosen per run (`--profile night`). The profile name goes in the transcript and the result.

**Measure.** Users running unattended jobs who keep one settings file instead of two folders.

**Not doing.** Inheritance between profiles. Each profile is read on its own, so nothing leaks from the looser one.

## 9. Transcripts I can query

**Problem.** Session files on disk are undocumented, so any tool that reads them breaks when they change.

**Evidence.** My health checks work by reverse-engineering the session files. Telling a night run from a day run meant reading the first prompt.

**Ship.** A documented session index (id, start time, folder, model, cost, outcome) and a `--tag` flag on `claude -p` that lands in it.

**Measure.** Third-party tools that read the index instead of the raw files.

**Not doing.** A hosted dashboard. A file on disk is enough, and it stays on the user's machine.

## 10. Skills without user permissions

**Problem.** `--setting-sources` loads skills, permissions, and hooks together, so a fenced run can't have my skills without my looser permissions.

**Evidence.** Loading only project settings, which the fence needs, also dropped my user skills. I worked around it with symlinks.

**Ship.** Choose the source of skills, permissions, and hooks separately.

**Measure.** Symlink workarounds in public harnesses: gone.

**Not doing.** Merging permissions across sources. Stricter wins, and that stays.

## 11. Defaults that fail quietly

**Problem.** Two defaults change a headless run without saying so.

**Evidence.** The 60-second default hook timeout silently killed a hook that needed ten minutes. `claude -p` waits 3 seconds for input unless you pass `</dev/null`.

**Ship.** One line in the output whenever a hook hits its timeout or the stdin wait changes a run.

**Measure.** Bug reports that trace back to either default.

**Not doing.** Changing the defaults themselves. They are reasonable; they just need to be visible.

## Two things that worked better than I expected

A new deny rule binds a running session at once, without a restart. And structured output made the morning judge easy to build: one schema, and every grade came back in the same shape.

*Claude helped draft these from the run record and the essay. The calls, and any mistakes, are mine.*
