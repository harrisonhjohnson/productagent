import type { Metadata } from 'next';
import Link from 'next/link';
import { DescentPanel } from '@/components/descent-panel';
import { Shell } from '@/components/shell';
import { AUTHOR_LINKEDIN } from '@/lib/content';

export const metadata: Metadata = {
  title: 'the morning, as a Claude Code feature',
  description:
    'A design sketch: what the morning review of unattended Claude Code runs would look like as a feature, built from what 33 nights taught. Sorted by the cost of waiting, one keystroke per Decision, facts from the runner, and a way to reach zero interventions without hiding them.',
};

const k = (s: string) => <span className="tui-key">{s}</span>;
const dim = (s: string) => <span className="tui-dim">{s}</span>;
const ok = <span className="tui-ok">✓</span>;

const lines: React.ReactNode[] = [
  <><b>Morning · Wed Oct 14</b>   3 loops ran · 22 min · $9.41 · <span className="tui-ok">0 escapes</span></>,
  '',
  <><span className="tui-h">NEEDS YOU · 3</span>                       {dim('sorted by what waiting costs')}</>,
  <span className="tui-sel">▸ 1  Merge     Fan-site update    blocks tonight’s run · 3 files · screenshot ✓ </span>,
  <>         {k('m')} merge   {k('d')} diff   {k('v')} view page</>,
  '  2  Decision  Permit research    count rows per permit or per building?',
  <>         {k('a')} per permit {dim('(run recommends)')}   {k('b')} per building</>,
  '  3  Login     Permit research    state portal needs you; the fence denied it',
  <>         {k('o')} open portal   {k('s')} skip it tonight</>,
  '',
  <span className="tui-h">DONE, NOTHING TO DO · 2</span>,
  <>  {ok}  Changelog watch    no changes on 3 sites       {k('↵')} evidence</>,
  <>  {ok}  Launch checklist   14 of 14 boxes match repo   {k('↵')} evidence</>,
  '',
  <span className="tui-h">FROM THE RUNNER, NOT THE AGENT</span>,
  '  refused calls 2, both expected (git push) · tasks left running 0',
  '  quota used last night 6% of the week · login good for 23 days',
  '',
  <span className="tui-rule">You answered “per permit” 3 times. Make it a standing Decision?  {k('y')} yes  {k('n')} keep asking</span>,
  '',
  dim('tab next · ↵ evidence · q done · 1 of 3 cleared in 0m 40s'),
];

export default function MorningPage() {
  return (
    <Shell path="/morning">
      <section className="tree-panel read" aria-labelledby="morning-heading">
        <nav className="crumbs" aria-label="Breadcrumb"><Link href="/">harnesses</Link><span>/</span><span aria-current="page">morning</span></nav>
        <div className="why-header">
          <p className="hero-eyebrow why-eyebrow">A DESIGN SKETCH · FROM <Link href="/33-nights">33 NIGHTS</Link></p>
          <h1 id="morning-heading">The morning, as a Claude Code feature.</h1>
          <p className="why-lede">
            Over 33 nights the machine was rarely the bottleneck. I was. A night took 8 minutes of machine time; the
            morning took as long as I let it, and when I skipped it the next night had nothing to do. Today my morning is
            a markdown file. This is what I would build so it takes five minutes.
          </p>
          <p className="why-rule">A sketch, not a shipped feature. Every line in it comes from a real morning.</p>
        </div>

        <div className="tui-wrap">
          <div className="term tui" role="figure" aria-label="Sketch of a morning review screen in the terminal">
            <div className="term-bar"><span /><span /><span /><em>~/loops · claude morning</em></div>
            <pre>
              {lines.map((l, i) => <span key={i}>{l}{'\n'}</span>)}
            </pre>
          </div>
        </div>

        <article className="doc">
          <h2 id="principles">Five choices, each from a night it went wrong</h2>
          <p>
            <b>1. Sort by what waiting costs, not by loop.</b> A weekly fan-site update sat on an unmerged branch for
            eight days, and one project collected 19 unmerged night branches. A branch that blocks tonight&apos;s run goes
            to the top, above a question that can wait a week.
          </p>
          <p>
            <b>2. One keystroke per Decision.</b> 37 Decisions queued over the run; 12 were still open at the end. A
            run that hands back a Decision has to write the options, and its own recommendation, so answering is a key
            press and not a paragraph.
          </p>
          <p>
            <b>3. Facts come from the runner, in their own panel.</b> One report said a run took &ldquo;~33 minutes&rdquo;;
            it took 6. Another said &ldquo;Blocked by the fence: none&rdquo; on a night with 34 refused calls. Time, cost,
            refusals and quota are printed by the runner, never summarized by the agent.
          </p>
          <p>
            <b>4. Done means evidence.</b> One loop ran 63 identical rechecks and called each one progress. Every
            &ldquo;done&rdquo; row opens the diff, the file or the page that proves it, and a row with nothing to open
            is not done.
          </p>
          <p>
            <b>5. Get to zero without hiding anything.</b> My first counted morning had 13 interventions; the next 12
            averaged 2.9. The cheap way to zero is to stop asking, which is how a system quietly takes decisions away from
            the person. Instead, when I answer the same Decision the same way three times, the screen offers to make it
            standing. I approve the rule once, it is listed and revocable, and approving it counts as an intervention
            that day. The count falls because the work got easier, not because it got hidden.
          </p>

          <h2 id="measure">How I would know it worked</h2>
          <ul>
            <li><b>Time to clear the morning</b>, median under five minutes. This is the number that matters most.</li>
            <li><b>Decisions waiting more than a day</b>: zero.</li>
            <li><b>Mornings skipped</b>, and whether the next night still had work to do.</li>
            <li><b>Standing Decisions revoked</b> within a week, as the check that rule-making is not too eager.</li>
          </ul>

          <h2 id="not-doing">Not doing</h2>
          <ul>
            <li><b>Auto-merge.</b> Only a person merges. The screen makes merging fast, not automatic.</li>
            <li><b>Pings at 3am.</b> Nothing reaches me before the morning unless a run is stuck and spending.</li>
            <li><b>A hosted dashboard.</b> The review lives in the terminal, next to the code it is about.</li>
          </ul>

          <p>
            The numbers here come from <Link href="/33-nights">the essay</Link> and <Link href="/evidence">the receipts</Link>.
            The pieces Claude Code would need underneath, such as refusals in the output, no exit with work pending,
            and a readable quota, are in <Link href="/asks">the asks</Link>.
          </p>
          <p>
            <i>Claude helped draft this sketch from the run record. The calls are mine. —{' '}
            <a href={AUTHOR_LINKEDIN} target="_blank" rel="noreferrer">Harrison Johnson</a></i>
          </p>
        </article>
      </section>
      <DescentPanel label="MORNING" marks={['SKETCH', 'CHOICES', 'MEASURE']} readout={{ kind: 'items', total: 5 }} />
    </Shell>
  );
}
