# productagent

An AI operating system for product managers.

Your job runs on four questions: **who owns this, what's the status, where's the data, when is it due.** productagent gives you four agents — one per question — connected to the tools your team already uses.

---

## How it works

1. **Fill in `context.md`** — your people, initiatives, and projects in one file. This is what makes the agents useful; they read it on every query.
2. **Connect your tools** — plug in MCPs for Asana, Slack, Google Drive, GitHub, Databricks, or whatever your stack is. Start with one.
3. **Ask questions** — invoke an agent by name or just describe what you need.

```
@who  Who owns the Canada checkout project?
@what What shipped last week on the iOS team?
@where Where's the PRD for the onboarding redesign?
@when When is the Q3 data migration due?
```

---

## The four agents

| Agent | Question | Goes to |
|-------|----------|---------|
| `who` | Ownership, people, contacts | `context.md` → Slack |
| `what` | Status, tasks, blockers | `context.md` → Asana / GitHub |
| `where` | Documents, data, code | `context.md` → Google Drive / Databricks / GitHub |
| `when` | Deadlines, timelines, roadmap | `context.md` → Asana / calendar |

The agents handle information retrieval. You handle judgment.

---

## Harnesses

The `harnesses/` folder holds the Claude Code harnesses I actually run, scrubbed for reuse: design-interview and prototype skills, a strategy agent, a fenced unattended night lane with a morning judge, and a Telegram bridge. Browse them at **[productagent.dev](https://productagent.dev)** or start at [harnesses/README.md](harnesses/README.md).

---

## What's in this repo

```
context.md        # your people, initiatives, and projects — fill this in first
CLAUDE.md         # the OS layer — how the system works
agents/
  who.md          # People & Ownership agent
  what.md         # Work & Status agent
  where.md        # Data & Source agent
  when.md         # Timeline & Schedule agent
mcps/
  setup.md        # how to connect your tools
harnesses/        # the harnesses behind productagent.dev — see harnesses/README.md
site/             # the productagent.dev site (Next.js, reads this repo at build time)
```

---

## Getting started

**1. Clone the repo**
```bash
git clone https://github.com/harrisonhjohnson/productagent
cd productagent
```

**2. Fill in context.md**

Replace the example data with your own people, initiatives, and projects. This is the only file you need to maintain.

**3. Connect at least one MCP**

See `mcps/setup.md`. Asana or Slack are good starting points.

**4. Open Claude Code in this directory**

```bash
claude
```

The agents are available immediately.

---

## Keeping it current

The agents are only as good as your `context.md`. A recommended practice: run a quick sync before planning meetings or at the start of your week.

> "Sync my context — check context.md against Asana and Slack and flag anything stale."

This triangulates your written context against live tool data so answers stay accurate.

---

## Requirements

- [Claude Code](https://claude.ai/code)
- One or more MCP integrations (see `mcps/setup.md`)
