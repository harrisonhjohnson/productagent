---
name: todo
description: Add, complete, or list TODOs. Listing aggregates ~/TODO.md (Navi format) plus Linear issues and Attio tasks assigned to you. Use when the user says "add a TODO", "mark done", "complete a task", "show my TODOs", "check my TODOs", or "add to my list". Ensures every ~/TODO.md item has a unique T+3 alphanumeric ID and the <!-- id:XXXX --> comment on the line after — the format Navi reads.
---

# todo

Manages `~/TODO.md` — the single source of truth shared between Claude Code and Navi (Telegram bot).

## File format (CRITICAL — Navi parses this exactly)

Every TODO item must follow this two-line format:
```
- [ ] Task description here
<!-- id:TXXX -->
```

Rules:
- ID format: `T` + exactly 3 uppercase alphanumeric characters (e.g., `TN01`, `TK3M`, `T7X2`)
- Completed items use `- [x]` (keep the `<!-- id:XXXX -->` line — never delete it)
- Optional metadata on the `<!-- id -->` line: `<!-- id:TXXX due:2026-07-01 -->`
- The `<!-- id:XXXX -->` line must immediately follow the checkbox line — no blank line between

## File structure

```
# To-Do List

**Last Updated:** YYYY-MM-DD

---

## Decide
(items requiring a decision before acting)

## Do
(actionable items)

## Waiting
(blocked on someone else)

---
```

## Generating IDs

Before adding any item:
1. Read `~/TODO.md` and collect all existing IDs (grep for `<!-- id:T`)
2. Generate a T + 3 char ID that does NOT already exist in the file
3. Use uppercase letters and digits only (A-Z, 0-9)
4. Prefer short memorable ones (TN01, TD42, TW7X) over random noise

## Modes

**add** — add a new TODO:
- Ask which section if not obvious from context: Decide / Do / Waiting
- Default to `## Do` if unspecified
- Generate a unique ID (check existing first)
- Append to the correct section
- Update the `**Last Updated:**` date

**complete** — mark a TODO done:
- Find the item by ID or text match
- Change `- [ ]` to `- [x]`
- Do NOT remove the `<!-- id:XXXX -->` line — Navi uses it for history

**list** — show open TODOs from all three sources:

1. **Personal (`~/TODO.md`)**
   - Display only `- [ ]` items grouped by section (Decide / Do / Waiting)
   - Show ID next to each item: `[TN01] Task text`

2. **Linear** (optional — only if the Linear MCP is connected; load with ToolSearch if deferred)
   - Call `mcp__linear__list_issues` twice with `assignee: "me"`, `limit: 50`, `includeArchived: false` — once with `state: "started"`, once with `state: "unstarted"`
   - IMPORTANT: `includeArchived` defaults to true and archived-but-incomplete issues come back looking open — always set it false (or drop any issue with a non-null `archivedAt`)
   - Show as `[ABC-123] Title — due date if set`, flag overdue items

3. **Attio** (optional — only if the Attio MCP is connected; load with ToolSearch if deferred)
   - Get your workspace member ID from `mcp__attio__whoami`
   - Call `mcp__attio__list-tasks` with that `assignee_workspace_member_id`, `is_completed: false`, `limit: 10`; paginate with `offset` if `has_more`

Run the Linear and Attio calls in parallel. Skip any source whose MCP is not connected. Present the sources as separate sections, most urgent first (overdue → due today/tomorrow → undated). Where an Attio task is a prerequisite for a Linear issue (e.g. an enrichment task feeding an outreach batch), note the link.

**add / complete / remove** only touch `~/TODO.md` — never create or complete Linear issues or Attio tasks unless the user explicitly asks for that system by name.

**remove** — delete a TODO entirely:
- Only do this if the user explicitly says "delete" or "remove" (not "complete" or "done")
- Remove both the `- [ ]` line and the `<!-- id:XXXX -->` line

## Navi compatibility check

After any write, the item is valid for Navi if:
- `- [ ]` or `- [x]` on one line
- `<!-- id:TXXX -->` on the very next line
- No extra blank lines between them
- ID is unique in the file

If you write a TODO any other way, Navi won't parse the ID and the task will be invisible to `/todo` filters and `/prework`.
