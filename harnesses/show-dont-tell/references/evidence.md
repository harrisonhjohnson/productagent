# Evidence base

What the research and practice say, and which rule in the skill each finding backs. Effect sizes are noted where the source reports them; treat practitioner sources (Roam, McCloud, Tufte) as craft knowledge, not experiments.

## Why pictures at all

- **Larkin & Simon (1987), "Why a Diagram is (Sometimes) Worth Ten Thousand Words."** Diagrams group related information by location, so the reader doesn't search for it, and they make relations perceptually obvious instead of requiring inference. The "sometimes" matters: the gain comes from spatial layout of structure, not from pictures per se. → *Draw structure (process, hierarchy, cause), not decoration.*
- **Paivio, dual coding theory.** Information encoded both verbally and visually is remembered better than either alone. → *Pair a short claim with a picture.*
- **Mayer, multimedia learning (Cognitive Theory of Multimedia Learning; many experiments).** Words + pictures beat words alone (the multimedia principle). His design principles map directly to the skill:
  - *Coherence:* cut extraneous material. → no decoration.
  - *Signaling:* highlight the essential. → one accent color, used in caption and visual together.
  - *Spatial contiguity:* put words next to the parts they describe. → direct labels, no legend.
  - *Redundancy:* don't show the same long text next to a graphic it narrates. → delete the paragraph the visual replaces.
  - *Segmenting:* break complex material into learner-paced pieces. → small multiples, step controls, comic panels.
- **Sweller, cognitive load theory.** Working memory is small; split attention between a diagram and separate text that must be mentally merged raises load. → integrate labels into the picture.

## Which visual encodings people read accurately

- **Cleveland & McGill (1984).** Ranked accuracy of judging quantities: position on a common scale > position on unaligned scales > length > angle/slope > area > volume/color saturation. Replicated by Heer & Bostock (2010) with crowdsourcing. → *bars and dots by default; avoid pies, bubbles, 3D.*
- **Bertin, *Semiology of Graphics* (1967).** Visual variables (position, size, value, texture, color, orientation, shape) and which suit which data types. → choose the variable by data type.
- **Preattentive processing (Treisman; Healey & Enns).** Color hue, size, orientation, and motion "pop out" in under ~250 ms if only one thing differs. → *one accent* makes the point land at a glance; many colors cancel each other out.
- **Gestalt principles (proximity, similarity, enclosure, connection).** The eye groups things that are near, alike, boxed, or linked. → layout encodes structure; misplaced proximity implies relations that aren't there.
- **Munzner, *Visualization Analysis & Design* (2014).** What/why/how framework: the task decides the encoding. → step 1 tags each idea's shape before choosing a form.

## Memorability, titles, "chartjunk"

- **Borkin et al. (2013), "What Makes a Visualization Memorable?"** Visualizations with human-recognizable objects, color, and visual density were more memorable; common charts were less memorable.
- **Borkin, Bylinskii et al. (2015), "Beyond Memorability."** Eye tracking on 393 visualizations: titles and supporting text carry the message; the best titles state the takeaway concisely; pictograms do not interfere with understanding and can improve recognition; redundancy (saying it in the title and the graphic) helps. → *title = the claim; icons are fine when they label.*
- **Bateman et al. (2010), "Useful Junk?"** Embellished charts (Nigel Holmes style) were as accurate as plain ones and better remembered after 2–3 weeks. → beauty and memorable form aren't the enemy; *meaningless* ornament is. This softens Tufte's data-ink rule.
- **Tufte (*The Visual Display of Quantitative Information*, *Envisioning Information*, *Visual Explanations*).** Data-ink ratio, small multiples, sparklines, "show the data", graphical integrity (the lie factor). → small multiples over animation; scale honesty.
- **Cairo, *The Functional Art* / *How Charts Lie*.** Function constrains form; misleading charts via truncated axes, wrong encodings, cherry-picked ranges. → accuracy test.

## Narrative visualization and data comics

- **Segel & Heer (2010), "Narrative Visualization: Telling Stories with Data."** Seven genres: magazine style, annotated chart, partitioned poster, flow chart, comic strip, slide show, film/video/animation. Most of these are static and cheap; video is one genre of seven. → the forms catalog covers six without video.
- **Hullman & Diakopoulos (2011); Kosara & Mackinlay (2013).** Framing, annotation, and sequence shape what readers conclude. → annotated charts; claim titles.
- **Bach, Riche et al. (2017–2018), data comics and "Design Patterns for Data Comics."** Panel layouts, transitions, and zooms for presenting data in sequence.
- **Wang, Bach et al. (CHI 2019), "Comparing Effectiveness and Engagement of Data Comics and Infographics."** Lab and in-the-wild studies: data comics were preferred for enjoyment and focus and improved understanding and recall versus infographics and illustrated text. A 2024 medical-data study and a 2026 education study (Shan et al., arXiv 2607.02361, 60 students) found comics beat text on recall and insight comprehension. → comic strip form, for explanation not just entertainment.
- **McCloud, *Understanding Comics* (1993).** Closure: readers fill the gutter between panels with the implied action. Amplification through simplification: simple cartoon faces let more readers see themselves in them. → simple consistent characters; 3–6 panels with an arc.
- **Eisner, *Comics and Sequential Art*.** Panel as unit of time; balloons ordered left→right, top→bottom.
- **Neurath & Arntz, Isotype (1920s–40s).** Repeated pictograms, one glyph = fixed quantity, for public education. Modern risk-communication research finds icon arrays help people grasp probabilities (e.g., Galesic, Garcia-Retamero & Gigerenzer 2009; Garcia-Retamero & Cokely reviews). → unit chart form; exact counts.

## Animation vs static

- **Tversky, Morrison & Bétrancourt (2002), "Animation: Can It Facilitate?"** Reviewing the studies, animations rarely beat equivalent static graphics; apparent wins usually came from extra information or interactivity, not motion. Congruence principle: format should match the concept (change → motion is plausible). Apprehension principle: animations are often too fast or complex to perceive accurately.
- **Höffler & Leutner (2007) meta-analysis (26 studies).** A medium advantage for dynamic over static visualizations (d ≈ 0.37), largest when the animation shows *procedural-motor* knowledge and is realistic (e.g., video of a skill). → motion pays for showing motion; it doesn't pay for decorating static ideas.
- **Robertson et al. (2008), "Effectiveness of Animation in Trend Visualization."** Gapminder-style animation was enjoyable but less accurate than small multiples and traces for analysis. → *small multiples first; animate only when change is the idea, with pause and replay.*
- **Heer & Robertson (2007), animated transitions.** Staged, simple transitions help people track objects between states. → if animating, stage it and slow it down.

## Concept maps vs mind maps

- **Nesbit & Adesope (2006) meta-analysis (55 studies, 5,818 participants)** and **Schroeder, Nesbit, Anguiano & Adesope (2017) (142 effect sizes, pooled g ≈ 0.58; constructing g ≈ 0.72, studying g ≈ 0.43).** Concept and knowledge maps improve retention compared with reading text or lists. Studying a ready-made map has a smaller but real effect.
- Mind maps (Buzan) have a thinner and more mixed evidence base, and their unlabeled links don't state relations. → the skill prefers concept-map style: labeled links that read as sentences.
- **Novak & Cañas, concept maps.** Node–link–node forms a proposition. → verify each triple as a true sentence.

## Visual thinking frameworks (practice)

- **Dan Roam, *The Back of the Napkin* (2008).** Six ways of seeing (who/what, how much, where, when, how, why) map to six picture types (portrait, chart, map, timeline, flowchart, multivariable plot). → the shape table's first six rows.
- **Mike Rohde, *The Sketchnote Handbook*.** Simple shapes + type hierarchy + containers + arrows produce clear visual notes fast. → cheap glyphs, few primitives.
- **Bret Victor, "Explorable Explanations"; Nicky Case's explorables; Distill.pub; The Pudding; NYT Upshot.** Interactive, reactive diagrams for abstract ideas. Expensive to build well; use for at most one centerpiece per artifact.
- **Systems thinking (Meadows, *Thinking in Systems*; Sterman).** Causal loop diagrams with polarity and loop labels. → causal loop recipe.
- **Lakoff & Johnson, *Metaphors We Live By*.** We understand abstractions through concrete source domains. → metaphor form, with the mapping made explicit and the break point stated.

## LLMs drawing visuals

- LLMs generate diagrams most reliably as code: SVG, Mermaid, Vega-Lite, HTML/CSS. Benchmarks are young: **MermaidSeqBench (2025, arXiv 2511.14967)** found big gaps between models on Mermaid sequence-diagram correctness; **DiagramEval (2025, arXiv 2510.25761)** proposes scoring diagrams as graphs (nodes and edges) because image-similarity metrics miss structural errors. → step 3: extract the node/edge/value structure first, draw from it, then re-check the render against it.
- **LIDA (Dibia, Microsoft 2023), Data Formulator (Microsoft Research)** generate charts from data + goals by having the model write plotting code, then self-evaluate and repair. → render, look, fix loop (step 6).
- Common failure modes in model-drawn SVG: overlapping labels, text overflowing boxes, arrows that miss targets, hard-coded colors that vanish in dark mode, coordinates that look plausible but encode nothing. → the verification checklist.
- Cost: an SVG diagram is a few hundred to a few thousand output tokens. A generated video is orders of magnitude more expensive and can't be fact-checked node by node.
