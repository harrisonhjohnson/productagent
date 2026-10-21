import Image from 'next/image';
import { Explorer } from '@/components/explorer';
import { DescentPanel } from '@/components/descent-panel';
import { InstallLine } from '@/components/install-line';
import { Onboarding } from '@/components/onboarding';
import { StickyNotes } from '@/components/loop-usecases';
import { Morning } from '@/components/morning';
import { Shell } from '@/components/shell';
import { countAll, getTree } from '@/lib/content';
import Link from 'next/link';
import { getEvidence } from '@/lib/evidence';
import './geo.css';

export default function Home() {
  const tree = getTree();
  const counts = countAll();
  const marks = ['I', 'II', 'III'];
  const t = getEvidence()?.totals;
  const short = (d?: string | null) =>
    d ? new Date(`${d}T12:00:00Z`).toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' }).toUpperCase() : '';
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
        <a className="to-1999" href="/1999">✦ 1999 mode ✦</a>
        <div className="hero">
          <Image src="/loops-retro.png" alt="" fill priority sizes="(max-width: 780px) 100vw, 94vw" className="hero-img" />
          <div className="hero-copy">
            <p className="hero-eyebrow">PRODUCTAGENT</p>
            <h1 id="page-heading">Let an agent run a loop<br />while you sleep.</h1>
            <p className="hero-meta">claude code · codex · your mac · your plan · {counts.harnesses} harnesses</p>
          </div>
        </div>

        <section className="lead" aria-labelledby="lead-heading">
          <p className="section-label">ESSAY · FROM THE RUN RECORD, {range}</p>
          <h2 id="lead-heading" className="lead-title">
            <Link href="/33-nights">33 nights of unattended Claude Code, and what I&apos;d ship as its PM</Link>
          </h2>
          <div className="lead-stats">
            {stats.map(([big, label]) => (
              <div key={label} className="lead-stat"><b>{big}</b><span>{label}</span></div>
            ))}
          </div>
          <p className="lead-sub">Three of the asks, each from a night it went wrong:</p>
          <ol className="lead-asks">
            <li><b>Refusals in the record.</b> One report said &ldquo;blocked by the fence: none&rdquo; on a night with 34 refused calls.</li>
            <li><b>Sandbox on by default for headless runs.</b> Rules alone let one line of <code>python3 -c</code> escape five ways out of five.</li>
            <li><b>No exit with work pending.</b> Four nights ended on &ldquo;waiting on the task notification&rdquo; with no report.</li>
          </ol>
          <p className="lead-links">
            <Link href="/33-nights">Read the essay →</Link>
            <Link href="/evidence">See the receipts →</Link>
          </p>
          <p className="lead-byline">
            Built and run by Harrison Johnson, a product manager, with Claude Code. Claude wrote most of the code; the calls are mine.
          </p>
        </section>

        <InstallLine />
        <Onboarding />

        <section className="usecases" aria-labelledby="usecases-heading">
          <p className="section-label" id="usecases-heading">WHAT A LOOP LOOKS LIKE</p>
          <StickyNotes />
        </section>

        <Morning />

        <p className="section-label">OR BROWSE THE FOLDERS</p>
        <Explorer tree={tree} label="harnesses" />
      </section>

      <DescentPanel label="HOME" marks={marks} readout={{ kind: 'items', total: 3 }} />
    </Shell>
  );
}
