# Post-install onboarding prototype

Interactive, demo-only prototype of the first minutes after
`curl -fsSL https://productagent.dev/install.sh | bash` lays the machine down in
`~/loops`. Nothing here installs, phones home, or talks to a network.

Promise it sells: **Let an agent run a loop while you sleep.** Lid shut, same Mac,
same Claude plan.

Four words it teaches: **Loop**, **Run**, **Order**, **Decision**.

## Run

```bash
cd onboarding-proto
npm install
npm run dev
```

Opens on `http://localhost:5173`. Designed for **1280×800** and up. Keyboard-first.

```bash
npm run build    # typecheck + production bundle
npm run preview  # serve the bundle
```

## Keyboard

| Key | Action |
|---|---|
| `Enter` / `Space` | Continue. Skips a cinematic if it is still playing. |
| `⌫` / `←` | Previous beat |
| `1`–`4` | Arm Loop, Run, Order, Decision (B2) |
| `1`–`6` | Pick a starter Loop (B3) |
| `Tab` then `←` `→` | Knobs on B3 |
| `Esc` | Skip boot / overnight · close the keymap |
| `?` | Keymap |
| `R` | Replay from cold boot |
| Click `B0`–`B8` | Jump (demo chrome) |

If the OS asks for reduced motion, typewriters and the overnight time-lapse collapse to a still.

## Beat map

| Beat | Name | What you learn |
|---|---|---|
| **B0** | Cold boot | The machine is in `~/loops`. Fence on. Battery floor 30%. AC gate. Nothing runs until you write a Loop. |
| **B1** | Lid promise | Lid shut, same Mac, same Claude plan. Eight free hours. Plug in. |
| **B2** | Four-noun loadout | Arm Loop, Run, Order, Decision. That is the whole system. |
| **B3** | First Loop | Pick a starter, set goal / budget / cadence / model. Preview of `pm/LOOPS.md`. Status: draft. First three Runs you review. |
| **B4** | Overnight time-lapse | One Run under a closed lid. Clock 23:12 → 06:48. Fence holds. Machine sleeps. |
| **B5** | Morning report | Four plain sentences: Trying to / Did / Decided / Need from you. The last is a Decision. |
| **B6** | Karma tease | A month of reports stays searchable. Optional. After a month of mornings. |
| **B7** | Phone tease | Telegram door: `/loops`, `/loop L-01 budget 5`, this morning’s four lines. |
| **B8** | You’re live | L-01 is written. Plug the laptop in tonight. |

A clean run (arm all four, pick a Loop, watch the night) is about **60–90 seconds**.

## Starter Loops

The six starters are the same examples as the site, and they are synthetic:

1. Competitors’ changelogs
2. Backlog fix
3. Support ticket themes
4. Launch checklist
5. Weekly update
6. ICP companies

## Mood

Deep navy, cream monospace (IBM Plex Mono), one serif line for the sleep promise (Fraunces).
Crescent night + quiet window light. No neon grid.

This folder does not touch `harnesses/loops/install.sh` or the loops machine.
