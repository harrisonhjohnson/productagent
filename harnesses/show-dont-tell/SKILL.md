---
name: show-dont-tell
description: Turn text-heavy artifacts and abstract concepts into cheap, accurate, code-drawn visuals (diagrams, charts, unit charts, 2x2s, timelines, flows, comic strips, small multiples, icon rows) instead of more prose or expensive video. Use when the user says "make this visual", "show don't tell", "too much text", "visualize this", "turn this into a diagram/comic/infographic", "this is hard to explain", or hands over a doc, report, plan, README, research write-up, or artifact and wants it easier to grasp. Also use proactively when you are about to ship a page that is a wall of text explaining structure, process, comparison, magnitude, change over time, or cause and effect. Not for building a dashboard from a dataset (use dataviz / the Dashboard type) or generating images or video.
---

# Show, don't tell

LLMs default to writing. People take in structure, quantity, sequence, and space faster through their eyes. This skill finds the passages where a picture beats a paragraph, picks the form the research says fits, and draws it in code (SVG, HTML/CSS, a chart library). Everything it draws must trace back to the source.

Evidence for every rule below is in `references/evidence.md`. The form catalog with recipes is in `references/forms.md`. Read `forms.md` before drawing anything. Read `evidence.md` when the user wants the reasoning or you need to defend a choice.

Pair this skill with the others:
- Charts of data: load **dataviz** before writing chart code.
- Diagrams in an artifact: load **artifact-diagramming** for the SVG mechanics and theming.
- Publishing a page: load **artifact-design** first, as always.

## The four tests

Every visual must pass all four. If one fails, keep the text.

1. **Accurate.** Every node, edge, number, label, and icon comes from the source. No invented data, no rounded numbers passed off as exact, no arrows implying a cause the text doesn't claim. A unit chart with 7 icons means 7.
2. **Insightful.** The visual makes one claim. Write it as the title in a full sentence ("Most churn happens in week 1"), not a topic label ("Churn by week"). If you can't write that sentence, the visual has nothing to say.
3. **Cheap.** Text-to-code: inline SVG, CSS grid, HTML, a pinned chart library. No image generation, no video, no raster assets you have to fetch. Motion only as a CSS/SVG step sequence, and only when the idea is change itself.
4. **Beautiful through restraint.** One accent color for the thing that matters, grey for context, direct labels on the marks, no legend if a label fits, no decoration that carries no information. Simple and clear looks better than elaborate.

## Process

### 1. Audit the text and find each idea's shape

Read the whole artifact. Split it into ideas (usually a section or a paragraph). Tag each one with its **shape**, meaning the structure the words are describing:

| Shape (the question it answers) | Tell-tale words | Default form |
|---|---|---|
| **Who / what** (identity, parts) | "consists of", "the components", "made up of" | Labeled anatomy diagram, icon + name grid |
| **How much** (magnitude) | numbers, %, "x times", "most", "few" | Bar / dot plot; unit chart (Isotype) for counts people should *feel* |
| **Compared to what** | "vs", "unlike", "whereas", "better/worse" | Side-by-side table, aligned bars, before/after pair |
| **Trade-off** (two forces) | "but", "at the cost of", "balance" | 2x2 matrix or a slider-free annotated scatter |
| **Where** (space, position) | locations, layers, "inside", "above" | Map, cross-section, layered stack |
| **When** (time) | dates, "then", "phase", "over time" | Timeline; small multiples for state at each step |
| **How** (process) | "first", "step", "then", "if…else" | Flowchart / swimlane; numbered strip for linear steps |
| **Why** (cause, feedback) | "because", "leads to", "drives", "loop" | Causal diagram; causal loop with +/- arrows for feedback |
| **Part of a whole** | "share", "split", "breakdown" | Stacked bar, treemap, 100-square waffle |
| **Hierarchy / taxonomy** | "types of", "falls under", "levels" | Tree, nested boxes, indented outline with icons |
| **Network / relations** | "connects", "depends on", "related" | Node-link graph (≤ ~15 nodes) or adjacency table |
| **Abstract idea** | definitions, principles, jargon | Concrete metaphor or worked example, drawn |
| **Human story / interaction** | people, dialogue, a user doing a thing | Comic strip / storyboard (3–6 panels) |
| **Uncertainty / range** | "about", "between", "likely", CI | Range bars, dot clouds, "1 in N" icon array |
| **Argument / nuance** | qualifications, caveats, opinion | **Keep as text** |

The first six rows are Dan Roam's who/what, how much, where, when, how, why. The rest extend it. When an idea has two shapes, draw the one the reader most needs, and say the other in a caption.

### 2. Decide what to draw (the budget)

Not every idea earns a picture. Rank the tagged ideas by **how much harder it is to get from text than from a picture**:

- High: process with branches, anything with 3+ numbers to compare, spatial layout, feedback loops, a hierarchy deeper than 2 levels, before/after.
- Medium: a single trade-off, a timeline of 4+ events, a definition that a metaphor nails.
- Low / skip: one number (make it big type instead), a single linear list of 3 (a list is fine), argument, nuance, tone, instructions the reader will copy-paste.

Draw the high ones. Draw medium ones only if the page is still text-heavy after that. A good result usually cuts the word count by 40–70% and keeps the arguments in prose. Show the user the shortlist (idea → shape → form, one line each) before drawing if there are more than 5 or the artifact isn't yours.

### 3. Extract the structure before drawing

For each chosen idea, write the data the visual will hold as a short structured block first (in your reasoning or a scratch file):

- Diagram: list of nodes and edges with labels, each edge with its source sentence.
- Chart: the table of values with units and the source of each.
- Comic: panel list with who, what they say, and what the panel shows.
- Timeline: events with dates.

This is the accuracy step. Check every item against the source. Anything you would have to guess, leave out or mark as an assumption on the visual. The drawing is a render of this block, nothing more.

### 4. Draw it cheaply

Pick the form's recipe in `references/forms.md`. Defaults:

- **Inline SVG** for diagrams, flows, 2x2s, comics, icon rows, unit charts. Hand-place with a grid; use `viewBox` so it scales.
- **CSS grid / HTML** for tables, comparison cards, timelines, small multiples.
- **A chart library** (pinned version, per dataviz) only for real quantitative charts with axes.
- **Icons:** draw simple geometric glyphs inline or use one consistent set (Lucide, Phosphor, or Material Symbols, all on cdnjs/jsdelivr). One style, one stroke weight, one size per row. Icons label and count; they never decorate.
- **Motion:** only for a process or a change. Prefer a static strip of 3–6 frames (small multiples). If it must move, use a CSS step animation with a pause and a replay control, respect `prefers-reduced-motion`, and make the final frame a complete static picture.

### 5. Wire text and picture together

- Title = the one claim. Caption = one or two sentences on what to notice.
- Put labels on the marks (spatial contiguity), not in a legend or a paragraph below.
- Delete the paragraph the visual replaces. Don't print the same long explanation next to the picture. Keep only the claim, the caveat, and what the picture can't say.
- Use the accent color in the caption on the same word that's highlighted in the visual (signaling).
- Keep a text version for screen readers: `role="img"` + `aria-label` or a `<figcaption>` with the claim and the key numbers.

### 6. Verify by looking

Render it and look at it before calling it done. Compiling is not rendering.

- Screenshot the page (Playwright or Chrome tools) at desktop and at 390 px wide.
- Check: no overlapping text, no clipped labels, arrows hit their targets, it works in dark mode, the claim is readable in 5 seconds.
- Re-check the structure block from step 3 against what's on screen: same nodes, same numbers, same counts.
- If a visual takes longer to read than the paragraph it replaced, cut it and restore the text.

## Anti-patterns

- **Mind-map soup.** Radial maps with unlabeled lines. Use concept-map style instead: every link carries a verb ("causes", "is part of").
- **Decoration posing as insight.** Stock-looking icons beside every heading, gradients, 3D, emoji confetti.
- **Diagram of the table of contents.** Boxes for section names say nothing. Draw the content's structure, not the document's.
- **Pie with 7 slices, dual axes, area-as-value bubbles.** Use position and length; people read those most accurately.
- **Animation as a stand-in for clarity.** Moving pictures that are too fast to follow and show nothing a static strip wouldn't.
- **Arrows everywhere.** Each arrow must mean one thing. If arrows mean both "causes" and "comes after", split them by style and say so.
- **False precision.** A smooth curve through 3 points, a tidy 2x2 placement the text never justified.
- **Metaphor drift.** A metaphor that's vivid but maps wrongly onto the mechanism. Check that each part of the metaphor matches a part of the real thing.

## Output

When converting an existing artifact: return the revised artifact (same place it lives), then a short note listing each visual added, the idea it replaced, and anything left as text on purpose and why. When the source is a concept ("explain X"): give one page with 2–5 visuals in reading order, each with its claim title.
