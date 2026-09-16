// A synthetic morning, modeled on real ones. The four lines are the whole contract.
export function Morning() {
  return (
    <section className="morning" aria-labelledby="morning-heading">
      <p className="section-label" id="morning-heading">WHAT YOU READ IN THE MORNING</p>
      <div className="term" role="figure" aria-label="Example of one loop's morning report">
        <div className="term-bar"><span /><span /><span /><em>pm/nights/2026-09-15.md</em></div>
        <pre>{`## L-04 — Permit research, iteration 2
- Trying to:   read the second of five county permit files and pull the generator count.
- Did:         read all four documents, every page. The permit says 96 units; the agency
               web page says 98. Recorded the gap as a discrepancy, did not reconcile it.
- Decided:     one row per permit, not per building. Flagging it, since it is your call.
- Need from you: check the renewal on the state portal; it needs a login the fence denies.
- Where to look: pm/nights/loops/L-04.md, data/ledger-2026-09-15.md

run: 41 min · $3.80 of $6 · 0 pushes · 0 denials · progress: yes`}</pre>
      </div>
      <p className="morning-note">
        If the four lines are missing, the run is not done. That rule is in every loop&apos;s definition of done, and the
        morning judge checks for it. This one is an example, modeled on a real night.
      </p>
    </section>
  );
}
