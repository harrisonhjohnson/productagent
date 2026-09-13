# harnesses

The Claude Code harnesses I actually run, copied out of my machine and scrubbed so someone else can adopt them. Browse them at [productagent.dev](https://productagent.dev) or read them here.

"Harness" is used loosely: a skill, an agent definition, a slash command, a permissions fence, a set of shell scripts wired to launchd, or a whole bot. What they share is that each one turns a repeated judgment call into something written down that an agent can execute.

Every folder carries a `harness.json` (name, tier, one-line summary, where it came from on my machine, which file to read first). The site reads those to build its index.

| Harness | Tier | What it does |
|---|---|---|
| [flow-design](flow-design/) | global | A progressive design interview: one question per screen, ending in a clickable HTML prototype of a linear user journey (onboarding, checkout, wizard). |
| [prototype-swarm](prototype-swarm/) | global | Crawls a multi-screen HTML prototype for undefined click destinations and spawns one generator agent per missing screen, with a handoff packet written by the source screen, until the click graph is covered. |
| [pm-strategist](pm-strategist/) | global | A product and strategy advisor agent that blends three lenses (build taste, business structure, PM execution) and pressure-tests ideas instead of cheerleading. |
| [TODO](todo/) | system | One markdown TODO list with two doors: a Claude Code skill in the terminal and a Telegram bot on your phone, both reading and writing the same file. |
| [Night Orders](night-orders/) | system | An unattended nightly Claude Code lane fenced by settings.json, driven by a captain's-night-orders charter and self-renewing loops, graded next morning by deterministic trajectory scorers and an LLM judge. |
| [rev-intel-harness](https://github.com/harrisonhjohnson/rev-intel-harness) | link | A CSV of companies in, the people out: point your existing AI subscriptions at target accounts. Open source, MIT. |

Tiers: **global** lives in `~/.claude` and applies everywhere; **system** is a multi-file machine with more than one moving part; **link** points at a separate public repo.

## The harnesses

### flow-design

A progressive design interview: one question per screen, ending in a clickable HTML prototype of a linear user journey (onboarding, checkout, wizard). Source: `~/.claude/skills/flow-design`. Start with [SKILL.md](flow-design/SKILL.md).

### prototype-swarm

Crawls a multi-screen HTML prototype for undefined click destinations and spawns one generator agent per missing screen, with a handoff packet written by the source screen, until the click graph is covered. Source: `~/.claude/skills/prototype-swarm`. Start with [SKILL.md](prototype-swarm/SKILL.md).

### pm-strategist

A product and strategy advisor agent that blends three lenses (build taste, business structure, PM execution) and pressure-tests ideas instead of cheerleading. Source: `~/.claude/agents/pm-strategist.md`. Start with [pm-strategist.md](pm-strategist/pm-strategist.md).

### TODO

One markdown TODO list with two doors: a Claude Code skill in the terminal and a Telegram bot on your phone, both reading and writing the same file. Source: `~/.claude/skills/todo + ~/tools/navi`. Start with [README.md](todo/README.md).

### Night Orders

An unattended nightly Claude Code lane fenced by settings.json, driven by a captain's-night-orders charter and self-renewing loops, graded next morning by deterministic trajectory scorers and an LLM judge. Source: `~/ventures/.claude + ~/ventures/00-ops + ~/ventures/pm`. Start with [README.md](night-orders/README.md).

### rev-intel-harness

A CSV of companies in, the people out: point your existing AI subscriptions at target accounts. Open source, MIT. Source: `github.com/harrisonhjohnson/rev-intel-harness`.

## What was scrubbed

Personal paths became `/Users/YOU` or `$HOME`. Rates, budgets, and ledger lines became placeholders or round caps. Client and employer names, record IDs, and anything tied to a specific job are gone. Every file was checked against this gate before publishing, which must return nothing:

```
grep -rnEi \
  -e 'switchboard|orchard|orange|agent-bench|job search|paternity|harrison\.build' \
  -e '/Users/harrison(johnson)?|-Users-harrisonjohnson|harrisonhjohnson@|@gmail\.com' \
  -e '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}' \
  -e 'sk-[A-Za-z0-9_-]{16,}|xox[abp]-[A-Za-z0-9-]{10,}|gh[pos]_[A-Za-z0-9]{20,}|[0-9]{8,10}:AA[A-Za-z0-9_-]{30,}|AKIA[A-Z0-9]{16}' \
  harnesses/
```

Built by Harrison Johnson with Claude. The agents did the copying and the first pass of scrubbing; the judgment about what to publish is mine.
