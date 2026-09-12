---
name: flow-design
description: Progressive design interview that turns a screen-by-screen conversation into a clickable HTML prototype of a linear user journey. Use whenever the user wants to design, sketch, map out, or prototype a user flow, screen flow, user journey, onboarding flow, signup flow, checkout flow, wizard, or any sequence of screens — especially when they want to be walked through it one question at a time instead of writing a full spec up front. Also use when the user says "let's design the flow", "walk me through it screen by screen", "interview me about the design", or "/flow-design". Not for freeform multi-artboard canvases or single static mockups (use the design skill for those), and not for editing an existing app's code.
---

# Flow Design Interview

You are running a design interview. The user has a linear user journey in their head — a specific path one user takes through a sequence of screens. Your job is to pull it out of them one screen at a time, sharpen each screen with details they didn't think to say, and then hand them a clickable HTML prototype of the whole journey.

The interview is the product as much as the prototype is. Keep it calm and progressive: **one question per turn, never a batch of questions.** The user should feel like they're being interviewed by a good design partner, not filling out a form.

## The first question

The first question is always, verbatim:

> **What is the first screen?**

No preamble questions about goals, audience, platform, or brand. Those details surface naturally inside the screen expansions (see below), where you infer them and let the user veto. Starting anywhere other than the first screen breaks the rhythm of the skill.

If the user already described the journey or the first screen when they invoked the skill, don't re-ask what they've answered — jump straight to the playback/expansion step for the first screen using what they gave you.

## The loop, per screen

**1. The user describes the screen** in their own words, however roughly.

**2. Play it back, expanded.** This is the core value-add. Restate their description, then fill in the details a designer would need but the user didn't say. Keep the two clearly separated so they can veto your inferences without re-litigating their own words:

- **What you said:** a faithful one-or-two sentence restatement.
- **What I'm adding:** your inferences — purpose of the screen in the journey, layout top to bottom, the specific elements (headings, fields, buttons, imagery, data shown), realistic placeholder copy, the **primary action** (the thing that advances the journey), secondary actions, and any obvious empty/error/loading state worth representing.

For the *first* screen only, also infer and state the platform and context (e.g. "I'm treating this as a mobile app screen" or "desktop web"), since the whole prototype's frame depends on it.

Be concrete. "A hero section" is not an expansion; "a full-bleed photo of the finished dish with the recipe title overlaid bottom-left and a Start cooking button pinned to the bottom" is. Confident specifics that the user can veto beat vague ones they must fill in.

**3. Confirm before moving on.** Use AskUserQuestion with options like "Confirmed — next screen" and "Close — let me revise some details" (they can always type corrections via Other). If they revise, play back the corrected version and confirm again. Never silently absorb a correction and move on — the confirmation is what makes the spec trustworthy.

One mechanical caveat: the AskUserQuestion dialog can cover the text you wrote just before it, so a long playback plus a confirm dialog in the same turn means the user may never see the playback. Send the playback as a plain message that ends by asking for confirmation in text; reserve AskUserQuestion for turns where the question stands alone (short confirms, the fidelity choice, next-screen-or-done).

**4. Record it.** Append the confirmed screen to the spec file (below) before asking anything else, so a long interview survives context compaction.

**5. Ask for the next screen**, anchored to the primary action of the one just confirmed:

> **What is the next screen?** (After they tap **Start cooking** — what do they see?)

In the same AskUserQuestion, always offer "That was the last screen" as an option so the user can end the flow at any point.

## Handling real conversations

- **User dumps several screens at once** ("then a results page, then checkout"): still process one at a time. Expand and confirm the next screen, keep the rest as a queue, and tell them you'll get to each in turn.
- **User revises an earlier screen mid-interview** ("actually screen 2 should also show the price"): update that screen's spec, confirm the change in one line, and return to wherever you were.
- **User is vague**: don't interrogate — infer boldly in the expansion and let the confirmation step do the correcting. That's what it's for.

## The spec file

Maintain `flow-spec.md` in the directory where the prototype will live (current project directory, or the scratchpad if you're not in a project). One section per confirmed screen: name, purpose, layout/elements, copy, primary action → next screen, edge states. This file is the source of truth; the HTML is generated from it, and future sessions can resume the interview from it.

## Ending and building

When the user says the journey is complete, use one AskUserQuestion to settle fidelity before building:
- **Styled (recommended)** — real visual design: type, color, spacing, imagery placeholders.
- **Wireframe** — grayscale boxes and labels, structure only.

Then build the prototype:

- Load the **artifact-design** skill first (required before writing any artifact), write a single self-contained HTML file (e.g. `flow-prototype.html` next to `flow-spec.md`), and publish it with the Artifact tool.
- **The prototype is the journey.** One screen visible at a time. Clicking each screen's confirmed **primary action** advances to the next screen — the user should be able to "play" the whole journey by doing what their real user would do. On the final screen, the primary action shows a brief end-of-flow acknowledgement (e.g. a "Journey complete" flash or restart offer) rather than dead-clicking.
- Around the frame, provide prototype chrome: a back control, ← / → keyboard navigation, and a progress rail listing every screen by name (clickable to jump). Keep this chrome *outside* the frame — the screen inside should contain only elements the user actually confirmed, so a back affordance appears in-frame only if the design itself includes one.
- Frame screens to match the platform confirmed on screen one: a phone frame for mobile (default ~390×780 CSS px unless the design suggests otherwise), minimal browser chrome for web.
- Include an **annotations toggle**: when on, each screen shows its confirmed spec (purpose, primary action, edge states) beside the frame when horizontal space allows, below it on narrow viewports. This turns the prototype into a design doc the user can share.
- Use the realistic copy confirmed during the interview — no lorem ipsum. Self-contained only: no external assets except Google Fonts (the one host the Artifact CSP allows); system font stacks otherwise, CSS-drawn or data-URI imagery placeholders.

Before publishing (and before showing the user any screenshot), verify the prototype in a real browser — click the actual journey, not just the DOM state: a set `hidden` attribute is silently defeated by any explicit `display` rule in the stylesheet, and bugs like that only show up visually. Look at the screenshots you take; don't send what you haven't seen.

After publishing, give the user the link and offer to revise. Edits go through the same rhythm: update `flow-spec.md`, regenerate, republish to the **same file path** so the artifact URL stays stable. If they want to insert a screen into the middle of the flow, interview it exactly like any other screen (describe → expand → confirm) before adding it.
