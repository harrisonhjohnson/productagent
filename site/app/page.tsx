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
import './geo.css';

export default function Home() {
  const tree = getTree();
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
          <h1 id="page-heading" className="lead-h1">Claude writes the code at night.<br />You review it in the morning.</h1>
          <div className="lead-stats">
            {stats.map(([big, label]) => (
              <div key={label} className="lead-stat"><b>{big}</b><span>{label}</span></div>
            ))}
          </div>
          <p className="lead-kicker">THE ESSAY · 8 MIN READ</p>
          <h2 className="lead-title">
            <Link href="/33-nights">33 nights of unattended Claude Code, and what I&apos;d ship as its PM</Link>
          </h2>
          <p className="lead-sub">From the run record, {range}. Three of the asks, each from a night it went wrong:</p>
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
          <p className="lead-byline">
            Built and run by <a href={AUTHOR_LINKEDIN} target="_blank" rel="noreferrer">Harrison Johnson</a>, a product manager, with Claude Code. Claude wrote most of the code; the calls are mine.
          </p>
        </section>

        <div className="part-break">
          <p className="part-break-kicker">PART TWO</p>
          <h2 className="part-break-title">The thing I built to run these nights</h2>
          <p className="part-break-lede">
            Loops is free and open source. You give it a goal, a budget, a cadence and a model; it works one bounded
            run at a time while you sleep and leaves you four lines in the morning.
          </p>
        </div>

        <Morning />

        <section className="usecases" aria-labelledby="usecases-heading">
          <p className="section-label" id="usecases-heading">WHAT A LOOP LOOKS LIKE</p>
          <StickyNotes />
        </section>

        <InstallLine />
        <Onboarding />

        <p className="section-label">OR BROWSE THE FOLDERS</p>
        <Explorer tree={tree} label="harnesses" collapsed />
      </section>

      <DescentPanel label="HOME" marks={marks} readout={{ kind: 'items', total: 3 }} />
    </Shell>
  );
}
