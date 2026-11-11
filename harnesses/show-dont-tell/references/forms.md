# Forms catalog

Each form: when it wins, when it doesn't, and a build recipe that a model can execute in plain SVG/HTML. Sizes assume a 720 px content column; use `viewBox` and `width:100%` so it scales down to 390 px.

Shared tokens (define on `:root`, redefine for dark mode):
`--ink` (text), `--muted` (secondary text, grid), `--line` (strokes), `--surface` (cards), `--accent` (the one thing that matters), `--accent-2` (optional second, used sparingly). Text in SVG uses `fill="currentColor"` or the tokens, never hard-coded black.

---

## 1. Flowchart / swimlane (how)

**Wins:** steps with branches, handoffs between people/systems, "if X then Y".
**Loses:** a linear list of 3 steps (use a numbered strip).

Recipe:
- Steps flow left→right (or top→bottom on narrow pages). One row per actor for swimlanes; actor name pinned at the left edge.
- Rounded rects for actions, diamonds only for real decisions with labeled exits ("yes"/"no").
- Grid: columns every 160 px, rows every 90 px. Boxes 130×48, text 13–14 px, max 4 words per box.
- Arrows: one `<marker>` arrowhead, `stroke-width:1.5`, orthogonal paths (`M x y H x2 V y2`). The happy path in `--accent`, everything else `--line`.
- Never more than ~12 boxes. Split into "overview" + "zoom into step 3".

## 2. Numbered strip (linear how / when)

**Wins:** 3–6 sequential steps, a short process, onboarding.
Recipe: CSS grid `repeat(auto-fit, minmax(150px, 1fr))`. Each cell: big step number in `--accent`, an icon, a 2–5 word label, one line of detail. A thin connecting line behind the cells. Wraps naturally on mobile.

## 3. Timeline (when)

**Wins:** 4+ dated events, phases, history.
Recipe: one horizontal axis; ticks at real proportional dates (accuracy: spacing must reflect time, or label it "not to scale"). Events as dots above/below alternating to avoid label collisions. Phases as translucent bands. On mobile switch to a vertical axis with events on the right.

## 4. Small multiples (when / compare)

**Wins:** a state that changes across steps or groups. Usually better than animation: the eye compares frames side by side.
Recipe: identical mini-panels, same scale and axes, in a grid. Only the changing part differs; highlight the change in `--accent`. Title each panel with the step or group name. 3–9 panels.

## 5. Before / after pair (compare, change)

**Wins:** a fix, a redesign, a policy effect, "what changes".
Recipe: two panels, same layout, left labeled "Before", right "After". Differences marked with `--accent`; everything identical is muted. A one-line caption names the change.

## 6. Comparison table / cards (compare)

**Wins:** 2–4 options across 3–8 attributes.
Recipe: options as columns, attributes as rows. Cells use short words or symbols (filled/half/empty circles drawn in SVG or CSS, not emoji). Highlight the recommended column with a top border in `--accent`. Put the verdict in the title.

## 7. 2x2 matrix (trade-off)

**Wins:** two independent dimensions that create four meaningfully different quadrants (effort/impact, risk/reward).
**Loses:** when the dimensions aren't independent, or when you'd have to invent the positions. Place items only where the source justifies it; otherwise place them by quadrant (not by coordinate) and say so.
Recipe: square 400×400, axes labeled at the ends with direction ("low → high"), quadrant names in muted caps in each corner, items as labeled dots. The quadrant that matters gets a faint `--accent` wash.

## 8. Bar / dot plot (how much)

**Wins:** comparing magnitudes. Position and length read most accurately (Cleveland & McGill), so this is the default for numbers.
Recipe: horizontal bars, sorted, labels left, values at the bar end, no y-axis gridlines needed. Bars start at zero. Highlighted bar in `--accent`, rest in `--muted`. Use a dot plot when the zero baseline is meaningless or to show two values per row (dumbbell). Load **dataviz** for anything beyond ~10 rows or with axes.

## 9. Unit chart / Isotype / icon array (how much, felt)

**Wins:** counts and proportions that people should *feel* ("3 in 10 people"), risk ("1 in 50").
Recipe: a grid of identical glyphs, one glyph = one unit (state the unit: "each ● = 1,000 users"). Count must be exact; for fractions, use a partial glyph only with a note. 10×10 grid for percentages. Highlighted units in `--accent`, filled first from top-left. Simple glyphs (circle, person silhouette built from a circle + rounded rect) render cheaply and consistently.

```svg
<svg viewBox="0 0 220 220" role="img" aria-label="30 of 100 highlighted">
  <!-- generate in JS or by hand: for i in 0..99: x=(i%10)*22+11, y=floor(i/10)*22+11 -->
  <circle cx="11" cy="11" r="8" fill="var(--accent)"/>
  <!-- … -->
</svg>
```

## 10. Part-to-whole: stacked bar / waffle / treemap

**Wins:** shares of a total. Single 100% stacked bar for ≤5 parts with direct labels; waffle (10×10) when the audience is general; treemap for a hierarchy of shares. Avoid pies with more than 3 slices.

## 11. Scale comparison (how much, abstract)

**Wins:** numbers too big or small to imagine ("a billion seconds is 31 years").
Recipe: nested squares or a row of objects drawn at true relative area/length, each labeled. Anchor to something familiar. Use length when possible; if using area, scale by √value and say "area to scale".

## 12. Anatomy / labeled diagram (who / what, where)

**Wins:** parts of a system, a screen, a product, an organization.
Recipe: draw the object as simple geometry (boxes for components, layers as stacked bands). Leader lines from each part to a label in the margin, labels aligned in a column. Number the parts if labels would crowd, with a short key beside it.

## 13. Layered stack / cross-section (where, hierarchy)

**Wins:** architectures, abstraction levels, "built on top of".
Recipe: full-width horizontal bands, top = closest to the user. Each band: name left, examples right as small chips. Highlight the layer under discussion.

## 14. Tree / nested boxes (hierarchy)

**Wins:** taxonomies, org structure, decision trees.
Recipe: indented tree (left-aligned, vertical) is the most robust at any width. Node-link tree for ≤ 3 levels × ≤ 5 children. Nested boxes (containment) when "is inside" matters more than "is a kind of".

## 15. Concept map (relations, abstract)

**Wins:** how ideas connect. Better than a mind map because every link has a verb, which turns it into readable propositions ("Prompt cache → cuts → latency").
Recipe: ≤ 12 nodes. Each edge has a short verb label at its midpoint. Lay out with the central concept top or center; avoid crossing edges (reorder before you add curves). Verify: read each node–verb–node triple aloud; each must be a true sentence from the source.

## 16. Causal loop diagram (why, feedback)

**Wins:** systems with feedback ("more users → more data → better model → more users").
Recipe: variables as plain text (no boxes), curved arrows between them labeled `+` (same direction) or `−` (opposite). Mark each loop with a circled `R` (reinforcing) or `B` (balancing) in its center. ≤ 8 variables. Only draw links the source asserts.

## 17. Comic strip / storyboard (human story, interaction, abstract explanation)

**Wins:** a user's experience, a conversation, a misconception and its correction, a before/after told as a story, explaining an abstract idea through characters (data comics). Comics keep word count low and engagement high; the gutter between panels lets the reader fill in the step (closure).
**Loses:** precise data (put a small chart *inside* a panel instead), long processes.
Recipe:
- 3–6 panels in a row (wrap to 2 columns on mobile). Panel 260×200, 2px `--ink` border, 12px gutter.
- Characters: simple and consistent (circle head + rounded body, or an icon), distinguished by one color each. Simple faces read as "anyone", which helps the reader identify (McCloud).
- Speech balloons: rounded rect + small triangle tail toward the speaker. ≤ 15 words per balloon, ≤ 2 balloons per panel.
- Captions (narration) in a rectangular box at panel top.
- Panel arc: setup → problem → turn → result. The last panel holds the claim.
- Data comics: a panel can be a chart; the next panel zooms or annotates it.

## 18. Concrete metaphor (abstract idea)

**Wins:** jargon, invisible mechanisms (caching = keeping your keys by the door).
Recipe: draw the familiar thing with the parts labeled in the *real* terms. Under it, a two-column mapping: metaphor part → real part. If any real part has no counterpart, or the metaphor implies something false, say where it breaks in one line ("unlike keys, cached data can go stale").

## 19. Annotated chart / annotated screenshot (how much + why)

**Wins:** a chart that needs its story told. Narrative visualization research: annotation is how a chart turns into an explanation.
Recipe: the chart, plus 1–3 callouts (thin leader line + short text) pointing at the exact feature: the spike, the crossover, the outlier. The title states the main point; the callouts carry the rest.

## 20. Big number (how much, single)

**Wins:** one number that matters. Don't chart it.
Recipe: the number at 48–64 px in `--accent`, a 4–8 word label under it, a comparison line in muted text ("up from 12% last year").

## 21. Step animation (change over time, only when motion *is* the idea)

**Wins:** a mechanism with motion (a queue draining, a packet moving, an algorithm step).
Recipe: build it as a set of static frames first (that's form 4). Then animate between them with CSS `@keyframes` using `steps()` or short ease transitions, ≥ 1.5 s per state, a pause at each state, a visible step counter and a replay button. `@media (prefers-reduced-motion: reduce)` shows the strip instead. No GIFs unless the output must go somewhere that can't render HTML (Slack, email); then record the SVG/CSS with a browser tool, not a video model.

---

## Icons

- One set per artifact. Lucide (stroke, 24 grid) is the default; Phosphor and Material Symbols are fine. Load from cdnjs/jsdelivr with an exact version, or inline the few SVG paths you need.
- Size 20–24 px inline, 32–40 px as a cell header. Stroke weight matches the diagram's line weight.
- Icons sit next to words, not in place of them (unfamiliar icons are ambiguous without labels). Exception: icon arrays, where the unit is stated once.
- Never use emoji as icons in a polished visual; they render differently per platform and can't take theme colors.

## Picking under doubt

- Two candidate forms? Pick the one with fewer marks.
- Can't place something accurately? Use a form that needs less precision (table instead of scatter; quadrants instead of coordinates).
- Unsure it helps? Draw it, then do the 5-second test: cover the caption, look for 5 seconds, say the claim. If you can't, simplify or delete.
