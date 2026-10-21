# productagent

The repo behind productagent.dev: Claude Code harnesses for product managers, each a
folder under `harnesses/` with a `harness.json` manifest, plus the static Next.js site in
`site/` that renders those folders.

## Vocabulary

Loop, Run, Order, Decision. Keep every public sentence inside those four words plus plain
English. Do not reintroduce lane, envelope, wrapper, standup, seed or root on the site;
they are internal to the machine and belong in `harnesses/loops/MACHINE.md` only.

## Rules

- Everything published passes the scrub gate in `harnesses/README.md` (must print nothing).
- No live data from the operator's machine ever lands here. Examples on the site are synthetic.
  One exception (2026-10-20): `/evidence` renders `evidence/evidence.json`, the real run record frozen at a
  cutoff date (`export-evidence.py --through`). Numbers, dates and verdicts only; it passes the scrub gate.
- `harnesses/loops` is the flagship; its `README.md` is the concept page, `MACHINE.md` the engineering page.
- The site builds with `cd site && npm run build`. A push to `main` deploys.
