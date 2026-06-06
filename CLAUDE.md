# productagent

An AI operating system for product managers. Four agents answer the four questions your job runs on — who, what, where, and when. You handle the how and the why.

## Setup

1. Fill in `context.md` with your people, initiatives, and projects.
2. Connect the MCPs for your tools (see `mcps/setup.md`).
3. Ask questions.

## context.md

`context.md` is the load-bearing file. Agents read it first on every query. Keep it current — a stale `context.md` is the only thing that produces bad answers.

## The four agents

Each agent has a single job. Invoke by name for reliable results.

| Agent | Ask it | Primary source |
|-------|--------|---------------|
| `who` | Who owns X? Who's on Y? Who should I talk to? | `context.md` → Slack |
| `what` | What's the status? What's blocked? What shipped? | `context.md` → Asana / GitHub |
| `where` | Where's the PRD? Where's the data? Where does this live? | `context.md` → Google Drive / GitHub |
| `when` | When is X due? What's on the roadmap? When did Y ship? | `context.md` → Asana / calendar |

## Integrations

The agents are modular — they use whatever MCPs you have connected and skip what you don't. The example stack this system was built on:

| Tool | Category | What the agents use it for |
|------|----------|---------------------------|
| Asana | Project management | Tasks, status, due dates, blockers |
| Slack | Communications | Channels, threads, people |
| Google Drive | Documents | PRDs, specs, briefs |

Any MCP that exposes your tools works here. Start with one, add more as needed. See `mcps/setup.md`.

## Keeping context current

`context.md` is only as good as its last update. A recommended (not required) practice: run a sync before a high-stakes moment — a planning meeting, a stakeholder review, a morning standup. The sync triangulates across your connected MCPs (Asana tasks, Slack threads, Drive docs) and flags anything in `context.md` that looks stale or missing.

This can be a manual prompt ("sync my context"), a morning routine, or an automated skill on a schedule. The cadence is yours — the point is that information retrieval is only trustworthy if someone has recently checked it against the live tools.

## What this system doesn't do

These agents answer information questions. They don't make decisions, set priorities, or tell you what to do next. That's your job. The goal is to eliminate the lookup tax so you spend your time on judgment, not retrieval.

## About you
<!-- Customize this section. The agents use it for context on every query. -->

- **Name:** Your Name
- **Role:** Product Manager
- **Timezone:** Your timezone
- **Org:** Your company or team
