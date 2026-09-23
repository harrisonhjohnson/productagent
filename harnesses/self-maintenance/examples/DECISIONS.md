# Decisions — what only you can settle

One row per ask. Settle a row with `loopctl.py apply D-NNN` (runs its `apply:` or
`patch:` and ticks it) or `loopctl.py park-decision D-NNN` (ticks it `~`, nothing runs).
A row without `apply:`/`patch:` is a judgment call; tick it by hand after deciding.
The night appends; it never edits or removes rows.

- [x] D-001 · ops · 2026-09-20 · Ratify the self-maintenance lane in the charter (loopctl, DECISIONS.md, patches, pod issues).
      patch: pm/nights/patches/2026-09-20-self-maintenance-lane.patch
- [~] D-002 · site · 2026-09-21 · Permit watch: run an attended catch-up on the unread mid-month feed-diff backlog, or accept the gap as likely covered elsewhere? — settled 2026-09-22: accept the gap
- [ ] D-004 · site · 2026-09-22 · Weekly read: approve a certificate-fixed fetch for the state portal on the night lane, or leave it attended-only?
- [ ] D-005 · site · 2026-09-22 · Round-up: the script's global four-failure circuit breaker let one rate-limited source starve seven others — loosen the backoff or retry per source?
- [ ] D-009 · ops · 2026-09-22 · Noise 1 of 4: tell every lane's session how the shell behaves (one command per call, scratch path, no retry of a refused call). Apply first.
      patch: pm/nights/patches/2026-09-22-shell-facts.patch
- [ ] D-013 · site · 2026-09-23 · Move the permit-watch loop from the default model to a cheaper one? The floor is met.
      apply: LOOPCTL_ATTENDED=1 python3 00-ops/night/loopctl.py model L-10 claude-sonnet-5
