---
name: launch-business
description: Run the daily venture-launch pipeline for the umbrella company — validate an idea, branch by type (content site / digital product / micro-SaaS), build and deploy the minimum, instrument it, and log it to the registry. Use when launching a new venture, running "today's business", or turning an idea into a live experiment.
---

# launch-business

The engine of the umbrella company (#001). Turns one idea into a live, measured experiment in a
day. Always read `../../CLAUDE.md` (doctrine) and `../../REGISTRY.md` (portfolio) first.

## Steps

1. **Intake** — assign the next ID, capture the idea in one line, pick the type. Add an `idea`
   row to REGISTRY.md immediately so nothing is untracked.

2. **Validate (the gate)** — run the cheap demand test for that type (see doctrine). Report the
   signal honestly. **If it fails the gate, mark `killed` and stop.** Most ideas die here — that
   is the system working, not failing.

3. **Build the minimum** — only if the gate passed. First pull a brand kit from the `brand` skill so
   the venture ships on-brand from day one (it writes a `## Brand kit` into the venture's BRIEF). Then
   branch by type:
   - Content / niche → pages + analytics.
   - Digital product → storefront + the asset.
   - Micro-SaaS → scaffold from the default stack + Stripe + auth.
   Smallest thing that can capture demand. No gold-plating.

4. **Deploy** — ship to a live URL (Replit / Vercel).

5. **Instrument** — analytics + a demand-capture mechanism (signup or payment), wired and verified.

6. **Log** — update the registry row to `launched` with its URL. Record what to watch and the
   kill date. Then hand the venture to the `growth` skill — it owns the post-launch
   `launched → growing` loop (measure the honest signal, maintain, experiment).

## Principles
- **Validation-first:** never build before the gate passes.
- **One source of truth:** the registry is updated at every step, never skipped.
- **Bias to kill:** when unsure, kill it and move to the next idea.
