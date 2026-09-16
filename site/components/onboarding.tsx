// The real transcript of init.sh, condensed. Every line here is something the script prints.
export function Onboarding() {
  return (
    <section className="onboard" aria-labelledby="onboard-heading">
      <p className="section-label" id="onboard-heading">WHAT HAPPENS AFTER YOU PASTE IT</p>
      <div className="onboard-grid">
        <div className="term term-onboard" role="figure" aria-label="The four questions the installer asks">
          <div className="term-bar"><span /><span /><span /><em>~ · install.sh</em></div>
          <pre>{`Installing to ~/loops
  wrote  pm/CHARTER.md
  wrote  pm/LOOPS.md            (empty)
  wrote  .claude/settings.json  (the fence, with your paths filled in)
Armed. The checker looks every ten minutes; nothing runs until you write a loop.

Loops · your first loop
Four questions. One file gets written.

1 · Which agent runs the night?   both are installed
   1) Claude Code   per-path fence; can read the web
   2) Codex         sandbox with the network off; harder no-push
   choose [1] `}<b>1</b>{`

2 · What should it work on?   pick a number, or type your own
   1) Watch three competitors' changelogs. Tell me what changed.
   2) Ship one small fix from the backlog. Verify it renders.
   3) Read yesterday's support tickets. Name the top three themes.
   goal [2] `}<b>2</b>{`

3 · How often, and how much brain?
   cadence [every-2nd-night] `}<b>⏎</b>{`
   brain: fast (Sonnet) · deep (Opus) · frontier (Fable)
   brain [deep] `}<b>⏎</b>{`

4 · What may it spend?
   per run [6] `}<b>⏎</b>{`      total for this loop [48] `}<b>⏎</b>{`
   at most $90 a month at this cadence; ends after 8 runs

Written   pm/LOOPS.md  (L-01, review by 2026-10-30)
Trusted   ~/loops in ~/.claude.json  (so the fence's allow rules apply)
Dry run   every guard, no model call, no spend
   tonight the machine would run L-01. ✓

Tonight   plug the laptop in. Lid open or shut.
Morning   read pm/nights/<date>.md`}</pre>
        </div>
        <ul className="onboard-points">
          <li><strong>Four questions, one file.</strong> Agent, goal, cadence and brain, budget. It writes a real loop, not a demo.</li>
          <li><strong>Claude Code or Codex.</strong> It detects what is on your path and asks only if both are. Switch later with one line in the charter.</li>
          <li><strong>The money is shown before you commit.</strong> Per run, per month at that cadence, and where the loop stops itself.</li>
          <li><strong>It dry-runs before it promises.</strong> Every guard, no model call, no spend, then a plain sentence about tonight.</li>
          <li><strong>Run it again any time.</strong> <code>bash ~/loops/00-ops/init.sh</code> adds another loop. <code>--off</code> stops the schedule.</li>
        </ul>
      </div>
    </section>
  );
}
