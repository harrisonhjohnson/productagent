# TODO

One list, two doors. A plain `~/TODO.md` that a Claude Code skill and a Telegram bot both read and
write, so a task captured from your phone at the bus stop is the same task the terminal sees an hour
later, and vice versa.

The file is the product. Everything else is a way to reach it.

## The file

```
- [ ] Draft the Canada launch checklist
<!-- id:TK3M due:2026-09-20 -->
```

Two lines per item: a checkbox line and an ID comment on the line directly after. IDs are `T` plus
three characters. Items live under `## Decide`, `## Do`, and `## Waiting`. Completed items flip to
`[x]` and keep their ID so history survives. That's the whole contract; both doors enforce it.

## Door one: Claude Code (`skill/`)

`skill/SKILL.md` is a `/todo` skill. Add, complete, list, remove. Listing can also fold in Linear
issues and Attio tasks assigned to you when those MCPs are connected, so one command shows the
personal list next to the work tracker. The skill never writes to Linear or Attio unless asked by
name.

Install: copy `skill/` to `~/.claude/skills/todo/`.

## Door two: Telegram (`bot/`)

`bot/` is the Telegram bridge (called Navi in the code). Send "add review the Q1 budget to Do" or
"what's on my list" and it edits the same file. It also runs `/todo` filters, voice notes, and can
spawn a background Claude agent on a single item and draft the follow-up. `bot/mcp_server.py`
exposes the list as MCP tools so any agent can use it.

Start with `bot/BOT.md`. Read its security notes before running it unattended; it ships with the
tradeoffs of a personal bot, documented rather than hidden.

## Why it's shaped like this

- **Markdown, not a database.** Greppable, diffable, editable in any editor, survives every tool
  change.
- **IDs in comments.** Invisible when rendered, stable when referenced from a phone.
- **Two thin clients, zero sync.** Both doors open the same file, so there's nothing to reconcile.
