---
name: prototype-swarm
description: Swarm-expand a multi-screen HTML prototype by crawling its click paths — review every screen for new clickable entry points, spawn a generator agent per undefined destination with a handoff packet written by the source screen, splice the new screens into the file, and repeat down the click graph until it's covered or capped. Never redesigns pages the real product already has, and never generates destinations the prototype holds back on purpose. Use when the user says "swarm the prototype", "expand the click paths", "fill in the missing screens", "run prototype-swarm", or "/prototype-swarm <file>". Not for creating a prototype from scratch (use flow-design) and not for real app code.
---

# Prototype Swarm

One invariant makes this system work: **every new screen is designed from a handoff packet written by the screen that links to it.** A screen's reviewer finds an undefined click, writes the brief (what state the user arrives in, what data carries over, what the primary action is, which constraints bind), and a generator builds the destination from that brief — then reviews its own screen the same way. Context chains down click paths.

Two hard fences:
1. **Never redesign existing product pages.** Clicks that lead to surfaces the real app already has are terminal.
2. **Never generate held-back destinations.** If the prototype's own constraints list says a surface is deliberately absent, honor it.

## Phase 0 — Setup

1. **Resolve the prototype file**: the argument if given, else the most recent multi-screen `*.html` mockup discussed in conversation, else ask. The expected idiom: `<!-- ══ SCREEN N ══ -->` banner comments, `.screen-label` headings ("Screen N · Name"), `.flowcap` Before/After captions, `.frame` app chrome, optionally an action-matrix table and a "Held back on purpose" list. If the file lacks screen labels, stop and say the file needs them first.
2. **Build the existing-product manifest** (terminal destinations), best source first: (a) the real app's routes file if a repo is reachable (e.g. `frontend/app/routes.ts` locally or via `gh api`); (b) else the prototype's own nav chrome — sidebar items, breadcrumb roots; (c) else ask the user for the list. Record which source you used.
3. **Insert the splice anchor** if absent: a line `<!-- swarm:insert -->` immediately before the first trailing section after the last screen (action-matrix `.screen-label`, else `.summary`, else the final `</div>`).
4. **Read or init the ledger**: a `<!-- swarm:ledger {json} -->` comment at end of file holding `{manifest, manifest_source, generated:[], remaining_frontier:[], declined:[], ambiguous:[]}`. The ledger travels with the file; a re-run resumes its frontier. Create `.swarm/` next to the file for fragment output.

## The click-point finding (schema all agents return)

```json
{
  "id": "s1-delete-suite",
  "source_screen": "Screen 1 · Suite list",
  "element": "🗑 iconbtn, title=\"Delete suite\", on each suite row",
  "action": "what the click does, per captions/action matrix",
  "dest_name": "Delete suite confirm",
  "dest_kind": "dialog | screen | inline-state | external",
  "classification": "defined | existing_product | intentionally_absent | undefined",
  "evidence": "matched Screen N label / matched manifest / matched held-back item / no match",
  "confidence": "high | medium | low",
  "handoff": {
    "before": "one sentence: the state the user arrives in (becomes the new screen's Before caption)",
    "must_show": ["concrete data/elements the destination must carry from the source screen"],
    "primary_action": "the thing that advances the flow from the new screen",
    "exits": ["where clicks on the new screen plausibly lead, incl. back to source"],
    "constraints": ["standing rules that bind this screen, quoted from held-back list / action matrix"]
  }
}
```

`handoff` is required iff classification is `undefined` — it is the parent screen briefing the child. `dest_name` is the dedupe key for the whole run.

## Phase 1 — Seed review

Run one reviewer agent per existing screen, **in parallel**, with this template (fill `{{...}}`):

```
You are a click-point reviewer for an HTML product prototype. READ-ONLY: modify nothing.

Read {{FILE}}. Focus on the screen labeled "{{SCREEN_LABEL}}" (from its <!-- SCREEN --> banner
to the end of its .annomap table). Also read: the stage-head intro, every .screen-label in the
file, the action matrix, and the "Held back on purpose" list.

Find EVERY clickable affordance in this screen's .frame: buttons, icon buttons, hoverable rows,
nav links, breadcrumb segments, filter chips/pills, inline links, and anything the captions
describe as clicked. Classify each destination:
- "defined": a screen already in this file. Match by (a) explicit "→ Screen N" references in
  flowcaps, then (b) name-matching against every .screen-label and in-frame <h2> (normalize:
  lowercase, strip punctuation and filler words page/view/screen/dialog/the/a; match if either
  token set contains the other).
- "existing_product": destination is in the MANIFEST below — the real app already has this
  page. Terminal; we never redesign existing product pages.
- "intentionally_absent": the held-back list or captions say this deliberately isn't built, or
  the affordance mutates in place (inline rename/edit) with no destination surface.
- "undefined": leads somewhere new that no screen depicts. These are the product.

EXISTING PRODUCT MANIFEST (terminal): {{MANIFEST}}
ALREADY QUEUED/GENERATED (also terminal): {{KNOWN_DESTS}}

For each "undefined" finding, write the handoff object as if this screen is briefing the
designer of the next one — use the concrete fake data visible in the frame (names, counts,
costs), and quote the standing constraints that bind the destination.

Return ONLY a JSON array of findings in the click-point schema. No prose.
```

Merge results; dedupe by normalized `dest_name`. Then show the user the seed frontier (one line per undefined destination: dest ← source element) and confirm **proceed all / trim** before spending generation budget. `confidence: low` findings never generate — they go to the ambiguous list in the report.

## Phase 2 — The frontier loop

Caps: **8 new screens per run** (override via `--max N`), **depth 3** handoffs from seed, **3 generators per wave**.

```
frontier  = ledger.remaining_frontier + dedupe(seed undefined findings)
N         = highest existing screen number; generated = 0
while frontier and generated < MAX:
    wave = pop up to 3 items; assign each item.N = ++N, its label, its fragment path
    launch one generator agent per item IN PARALLEL (Agent tool; Workflow for big waves)
    for each result, in assigned-N order (orchestrator only, serial):
        Edit: replace "<!-- swarm:insert -->" with fragment + "\n<!-- swarm:insert -->"
        generated += 1
        for f in result.findings where undefined:
            if normalized dest_name unseen and depth ≤ 3 and confidence ≠ low:
                frontier.push(f)
            elif confidence == low: ambiguous.push(f)
    update the ledger comment (one Edit per wave)
```

The orchestrator is the **only writer** to the shared file. Generators write fragment files and return findings — never touching the prototype. Sequential fallback for small prototypes: same loop, wave size 1.

## Generator brief (template)

```
You are a screen generator for an HTML product prototype. You extend one shared mockup by
writing ONE new screen as a self-contained fragment file. Do NOT edit {{FILE}} itself.

Read first: {{FILE}}'s <style> block (design tokens + classes), the full source screen
"{{SOURCE_SCREEN}}", and one other screen as a structural example.
Your assignment (a click-point finding): {{FINDING_JSON}}
Standing constraints (held-back list + action matrix): honor them; if your screen would
violate one, depict the constrained version and say so in the flowcap.
You are "{{ASSIGNED_LABEL}}". Pin ids are scoped to your screen number ({{N}}a, {{N}}b, …).

Write {{FRAGMENT_PATH}} containing, in order:
  <!-- ══════════ SCREEN {{N}} ══════════ -->
  <div class="screen-label">{{ASSIGNED_LABEL}}</div>
  <div class="flowcap"><span><b>Before:</b> [from handoff.before — name the source screen and
    clicked element]</span><span><b>After:</b> [each exit and where it leads]</span></div>
  <div class="frame"> … </div>   — reuse existing classes; keep the source screen's sidebar/
    topbar chrome with breadcrumbs advanced; use concrete fake data consistent with
    handoff.must_show. dest_kind "dialog": render the source screen dimmed underneath with
    the dialog overlaid. dest_kind "inline-state": render the source frame in that state.
  <div class="annomap"><table> … </table></div>  — pin rows with EXISTS/REUSE/NEW statuses,
    honest about what is net-new.
If you need CSS no existing class covers, add a <style> block at the TOP of your fragment
with all new class names prefixed "s{{N}}-". Prefer existing classes.

Then review your own screen using the reviewer procedure and classification rules provided,
and return ONLY: { "fragment": "{{FRAGMENT_PATH}}", "label": "{{ASSIGNED_LABEL}}",
"findings": [ … ] }
```

(Inline the reviewer classification rules, manifest, and known-destinations list into each generator's prompt — the generator's self-review is what chains the handoffs.)

## Termination & re-runs

- The frontier only grows from `undefined` findings and dedupes against screens-in-file ∪ manifest ∪ generated ∪ queued ∪ declined — destinations are named surfaces, the graph is finite, the frontier runs dry.
- **The file is the state.** A re-run's Phase 1 re-reads all screen labels, so prior screens classify as `defined` and are skipped. The ledger carries the unfinished frontier and the user's declines so nothing is re-proposed.
- `.swarm/` fragments are disposable cache; delete on a clean finish.

## Report & republish

End every run with, in this order:
1. **Screens added** — label + one-line Before each.
2. **Frontier remaining** — each: dest ← source element; "run again to continue" (never silently dropped).
3. **Terminal product clicks** — proof nothing existing was redesigned.
4. **Intentionally-absent skips** — with the constraint quoted.
5. **Ambiguous matches** — needing a human call.

Then, if the prototype is a published artifact, **republish it at its existing URL** (same file path; pass `url` if publishing from a different conversation) and give the link.

## Back-annotation (after every splice)

A generated screen defines the arrowhead; the tail must be updated too. After splicing
Screen N, edit every source screen that links to it: append "→ Screen N" to the source's
flowcap After span for that affordance, and update any annomap pin that described the
destination as endpoint-only. The click graph is only documented when both ends name the
edge — explicit "→ Screen N" references are also what makes the next run's reviewer
matching cheap and unambiguous.
