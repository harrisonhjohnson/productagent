import { Explorer } from '@/components/explorer';
import { DescentPanel } from '@/components/descent-panel';
import { InstallLine } from '@/components/install-line';
import { Onboarding } from '@/components/onboarding';
import { StickyNotes } from '@/components/loop-usecases';
import { Morning } from '@/components/morning';
import { Shell } from '@/components/shell';
import { AUTHOR_LINKEDIN, getTree } from '@/lib/content';
import Link from 'next/link';
import { getEvidence } from '@/lib/evidence';
import { ModelFigure } from '@/components/figures';
import { getMachine } from '@/lib/machine';
import './geo.css';

export default function Home() {
  const tree = getTree();
  const machine = getMachine();
  const marks = ['I', 'II', 'III'];
  const t = getEvidence()?.totals;
  const short = (d?: string | null) =>
    d ? new Date(`${d}T12:00:00Z`).toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' }) : '';
  const range = t ? `${short(t.first_night)} – ${short(t.last_night)}` : '';
  const stats: [string, string][] = [
    [String(t?.nights ?? 33), 'unattended nights'],
    [t ? `$${(t.night_cost_usd / t.nights).toFixed(2)}` : '$6.13', 'average night'],
    ['10', 'things broke'],
    ['11', 'Claude Code asks'],
  ];

  return (
    <Shell path="/">
      <section className="tree-panel" aria-labelledby="page-heading">
        <section className="lead" aria-labelledby="page-heading">
          <p className="section-label">PRODUCTAGENT · BY HARRISON JOHNSON</p>
          <h1 id="page-heading" className="lead-h1">Wake up to work that&apos;s already done.</h1>
          <p className="lead-sub">
            Loops runs Claude Code while you sleep, on the plan you already pay for. Give it one goal and a budget. In
            the morning you get a four-line report and a branch to review.
          </p>
          <div className="lead-cta">
            <a className="lead-primary" href="#install">Install Loops ↓</a>
            <p className="lead-links">
              <Link href="/33-nights">Or read what 33 nights of running it taught me →</Link>
            </p>
          </div>
          <p className="lead-byline">
            Built and run by <a href={AUTHOR_LINKEDIN} target="_blank" rel="noreferrer">Harrison Johnson</a>, a product manager, with Claude Code. Claude wrote most of the code; the calls are mine.
          </p>
        </section>

        <Morning />

        <p className="why-overnight">
          <b>Why overnight?</b> It isn&apos;t cheaper per task. It uses the hours your plan sits idle, and you review
          the work instead of watching it happen.
        </p>

        <section className="usecases" aria-labelledby="usecases-heading">
          <p className="section-label" id="usecases-heading">WHAT A LOOP LOOKS LIKE</p>
          <StickyNotes />
        </section>

        <div id="install" className="install-anchor">
          <InstallLine />
          <Onboarding />
        </div>

        <div className="part-break">
          <p className="part-break-kicker">PART TWO · THE ESSAY · 8 MIN READ</p>
          <h2 className="part-break-title">
            <Link href="/33-nights">33 nights of unattended Claude Code, and what I&apos;d ship as its PM</Link>
          </h2>
          <p className="part-break-lede">From the run record, {range}. Three of the asks, each from a night it went wrong:</p>
        </div>

        <section className="lead lead-proof" aria-label="What 33 nights showed">
          <div className="lead-stats">
            {stats.map(([big, label]) => (
              <div key={label} className="lead-stat"><b>{big}</b><span>{label}</span></div>
            ))}
          </div>
          <ol className="lead-asks">
            <li><b>Refusals in the record.</b> One report said &ldquo;blocked by the fence: none&rdquo; on a night with 34 refused calls.</li>
            <li><b>Sandbox on by default for headless runs.</b> Rules alone let one line of <code>python3 -c</code> escape five ways out of five.</li>
            <li><b>No exit with work pending.</b> Four nights ended on &ldquo;waiting on the task notification&rdquo; with no report.</li>
          </ol>
          <div className="lead-cta">
            <Link className="lead-primary" href="/33-nights">Read the essay →</Link>
            <p className="lead-links">
              <span>Then:</span>
              <Link href="/asks">all eleven asks as specs</Link>
              <Link href="/morning">the morning as a Claude Code feature</Link>
              <Link href="/evidence">the receipts</Link>
            </p>
          </div>
        </section>

        <section className="home-machine" aria-label="Where the ten breaks happened">
          <p className="section-label">WHERE THE TEN BREAKS HAPPENED</p>
          <ModelFigure m={machine} home />
        </section>

        <p className="section-label">OTHER HARNESSES</p>
        <Explorer tree={tree} label="harnesses" collapsed />
      </section>

      <DescentPanel label="HOME" marks={marks} readout={{ kind: 'items', total: 3 }} />
    </Shell>
  );
}
