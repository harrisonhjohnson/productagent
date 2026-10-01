# productagent

Working tools for product managers who run their day with Claude Code, published as the
folders they actually are. Browse them at **[productagent.dev](https://productagent.dev)**
or start at [harnesses/README.md](harnesses/README.md).

The centre of it is **[Loops](harnesses/loops/README.md)**: give an agent a goal, a budget,
a cadence and a model. It works one bounded run at a time while you sleep, inside a fence
it cannot climb, and hands you four plain sentences in the morning. Around it:

- **[TODO](harnesses/todo/README.md)** — one markdown list shared between the terminal and a Telegram bot. The bot is also the phone-side write path for loops (`/loops`, `/loop L-03 budget 5`).
- **[flow-design](harnesses/flow-design/SKILL.md)** and **[prototype-swarm](harnesses/prototype-swarm/SKILL.md)** — a screen-by-screen interview that ends in a clickable prototype, and a swarm that fills in the screens it links to.
- **[pm-strategist](harnesses/pm-strategist/pm-strategist.md)** — an advisor agent that argues back.
- **[karma](https://github.com/harrisonhjohnson/karma)** — a knowledge graph over everything the loops write, so a month of reports stays searchable.
- **[rev-intel-harness](https://github.com/harrisonhjohnson/rev-intel-harness)** — companies in, people out.

Four words carry the whole system: a **Loop** is work with a goal that renews itself; a
**Run** is one bounded pass at it; an **Order** is a one-off instruction for tonight; a
**Decision** is anything the run could not settle and hands back to you.

## What's in this repo

```
harnesses/        # every harness as a folder with a harness.json manifest
  loops/          # the flagship: fence, charter, runner, morning judge, spec
  todo/           # the list + the Telegram bot
  flow-design/  prototype-swarm/  pm-strategist/
  karma/  rev-intel-harness/      # links to their own repos
site/             # productagent.dev (Next.js, reads harnesses/ at build time)
onboarding-proto/ # demo-only post-install onboarding (Vite). Does not install anything.
```

There is also an interactive **[post-install onboarding prototype](onboarding-proto/README.md)** —
nine beats that teach Loop, Run, Order and Decision and sell the lid-shut night. Demo
only; `cd onboarding-proto && npm install && npm run dev`.

## Getting started

Clone the repo, open the harness you want, and copy its folder into your own setup. Each
README says what to copy and what to edit first. Nothing here phones home, and nothing is
hosted: every harness runs on your machine, on your Claude Code subscription.

Built by Harrison Johnson with Claude. The agents did the copying and the first pass of
scrubbing; the judgment about what to publish is mine.
