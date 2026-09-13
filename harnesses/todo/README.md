# TODO

A TODO list for product managers that lives in one markdown file and answers from wherever you
are: the terminal you're already working in, or the phone in your pocket. No app, no account,
no sync. One file, two doors.

```
- [ ] Draft the Canada launch checklist
<!-- id:TK3M due:2026-09-20 -->
```

That's an item. A checkbox line, then an ID on the next line. Everything below is built on it.

## What it's for

**Capture without switching context.** In Claude Code, say "add a TODO: chase legal on the DPA".
On Telegram, text the bot "remind me to send the roadmap deck by Friday". Either way the item lands
in `~/TODO.md` with an ID and a due date. Voice notes work too.

**See what's due.** `/duetoday`, `/dueweek`, `/overdue` on the phone. `/todo` in the terminal
shows the same list and, if Linear or Attio are connected, folds in the tickets and tasks assigned
to you so one glance covers personal and team work.

**Triage.** Items live under three headings: `Decide` (needs a call from you), `Do` (actionable),
`Waiting` (blocked on someone). Move things between them in plain language. `/priorities` and
`/quickwins` reorder by what will actually move.

**Hand an item to an agent.** `/prework TK3M` has Claude draft a plan for the item; `/approve`
runs it with a fixed set of tools and reports back; `/draft` writes the follow-up message so you
only have to press send. Anything the agent wants to do outside its allowlist is sent to you as a
Telegram approve/deny before it happens.

**Start and end the day.** `/morning` and `/summary` on a schedule, a weekly review, and a
"war room" that asks the hard question you're avoiding.

## Quick start

1. Copy `skill/` to `~/.claude/skills/todo/`. Open Claude Code and say "show my TODOs".
2. Optional, for the phone: follow `bot/BOT.md`. It needs a Telegram bot token and a machine that
   stays on. Ten minutes.
3. Keep `~/TODO.md` in a synced folder if you use more than one machine.

## Why it's built this way

- **Markdown, not a database.** Greppable, diffable, editable in any editor, survives every tool
  change you'll make this decade.
- **IDs in HTML comments.** Invisible when rendered, stable when referenced from a phone with
  autocorrect on.
- **Two thin clients, zero sync.** Both doors open the same file, so there is nothing to
  reconcile and nothing to trust but the filesystem.
- **Agents on a leash.** Background runs get an explicit tool allowlist and route everything else
  to you. See the security model in `bot/BOT.md`.

## Layout

```
skill/SKILL.md   the Claude Code door
bot/             the Telegram door (called Navi in the code); start with bot/BOT.md
```
