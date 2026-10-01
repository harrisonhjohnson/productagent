# Summary

A self-contained Vite + React + TypeScript prototype of ProductAgent’s post-install
onboarding, living in `onboarding-proto/` so the loops machine and `install.sh` stay
untouched.

## What it is

Nine beats, B0–B8, that teach the four nouns and sell the lid-shut fantasy:

Cold boot → lid promise → four-noun loadout → first Loop → overnight time-lapse →
morning report → Karma tease → phone tease → you’re live.

It is a demo. It does not install into `~/loops`, does not call a network, and does
not copy operator data. Starter Loops and morning reports are synthetic, matching
the examples on productagent.dev.

## How to run

```bash
cd onboarding-proto
npm install
npm run dev
```

Keyboard: Enter to continue, 1–4 to arm the nouns, 1–6 to pick a starter, ? for the
map, R to replay. Click B0–B8 to jump.

## Design

Navy and cream, IBM Plex Mono, one Fraunces line for the sleep promise. Crescent
sky and a quiet window. No Tron grid. `prefers-reduced-motion` flattens the boot
typewriter and the overnight clock.

## What was not changed

`harnesses/loops/**`, `site/**`, and the installer are untouched except a short
pointer in the root README.
