import { Explorer } from '@/components/explorer';
import { InstallLine } from '@/components/install-line';
import { Onboarding } from '@/components/onboarding';
import { Shell } from '@/components/shell';
import { AUTHOR_LINKEDIN, GITHUB, getTree } from '@/lib/content';
import Link from 'next/link';
import { getEvidence } from '@/lib/evidence';
import './geo.css';

const RAILS = [
  'A goal, not a prompt. Every loop has a definition of done and a review date.',
  'A night branch and an OS sandbox. It never pushes or deploys.',
  'A time limit per run. Spending caps per week and month.',
  'Parks itself after two stuck nights, and tells you which calls are yours.',
];

const FAQ: [string, string][] = [
  ['What does it cost?', 'Nothing extra. It runs on the Claude or ChatGPT plan you already pay for, under caps you set.'],
  ['Does my laptop stay on?', 'Plugged in, lid open or shut. It runs in the first window your Mac is awake and on power.'],
  ['How do I know the report is true?', 'One command in the morning has a second model check the report against the actual diff.'],
  ['Can it be shut down or acquired?', 'It’s MIT-licensed files in your repo. There’s nothing to shut down.'],
  ['Only code?', 'Any goal that ends in files: research, docs, HTML prototypes, fixes.'],
  ['Windows or Linux?', 'Not yet. macOS only.'],
];

export default function Home() {
  const tree = getTree();
  const t = getEvidence()?.totals;
  const stats: [string, string][] = [
    [String(t?.nights ?? 33), 'unattended nights'],
    [t ? `$${(t.night_cost_usd / t.nights).toFixed(2)}` : '$6.13', 'average night'],
    ['10', 'things broke'],
    ['11', 'Claude Code asks'],
  ];

  return (
    <Shell path="/">
      <div className="bh">
        <header className="bh-hero">
          <div className="bh-hero-copy">
            <p className="bh-label">001 / Loops · open source</p>
            <h1 id="page-heading" className="bh-h1">Wake up to work that&rsquo;s <span className="bh-red">done.</span></h1>
            <p className="bh-sub">
              Loops gives Claude Code a product goal, a budget and a fence. It works on your Mac overnight and leaves
              you a four-line report with the calls that are yours to make.
            </p>
            <div className="bh-ctas">
              <a className="bh-btn" href="#install">Install Loops ↓</a>
              <Link className="bh-text" href="/33-nights">Read the 33-night essay →</Link>
            </div>
            <p className="bh-byline">
              Built and run by <a href={AUTHOR_LINKEDIN} target="_blank" rel="noreferrer">Harrison Johnson</a>, a product
              manager, with Claude Code. Claude wrote most of the code; the calls are mine.
            </p>
          </div>
          <div className="bh-art" aria-hidden="true">
            <div className="bh-moon" /><div className="bh-bar" /><div className="bh-sun" />
            <div className="bh-tag">Night → Morning</div>
          </div>
        </header>

        <section className="bh-sec" aria-labelledby="how">
          <div className="bh-wrap">
            <p className="bh-label">01 / How it works</p>
            <h2 id="how" className="bh-h2">Three steps.<br />One is sleeping.</h2>
            <div className="bh-grid3">
              <div className="bh-card"><div className="bh-shape bh-circle" /><h3>Write a goal</h3><p>Say it the way you would to a new hire. Pick a cadence, a model and a budget.</p></div>
              <div className="bh-card"><div className="bh-shape bh-square" /><h3>It runs at night</h3><p>Claude Code or Codex works on a night branch, inside a fence, on the plan you already pay for.</p></div>
              <div className="bh-card"><div className="bh-shape bh-tri" /><h3>You read four lines</h3><p>What it tried, what it did, what it decided, and what it needs from you. Then review the branch.</p></div>
            </div>
          </div>
        </section>

        <section className="bh-sec" aria-labelledby="morning">
          <div className="bh-wrap bh-split">
            <div>
              <p className="bh-label">02 / The morning</p>
              <h2 id="morning" className="bh-h2">Four lines.<br />Coffee&rsquo;s still hot.</h2>
              <p className="bh-lede">
                If the four lines are missing, the run isn&rsquo;t done. That rule is in every loop. This one is an
                example, modeled on a real night. <Link href="/morning">The morning, as a Claude Code feature →</Link>
              </p>
            </div>
            <pre className="bh-report">
<span className="bh-dim">pm/nights/2026-09-15.md</span>{'\n\n'}
<span className="bh-k">## Permit research, iteration 2</span>{'\n'}
<span className="bh-k">Trying to</span>{'      read the second of five county permit files.\n'}
<span className="bh-k">Did</span>{'            read all four documents. The permit says 96 units;\n               the agency page says 98. Flagged it, didn’t guess.\n'}
<span className="bh-k">Decided</span>{'        one row per permit, not per building.\n'}
<span className="bh-k">Need from you</span>{'  check the renewal on the state portal. It needs\n               a login the fence denies.\n\n'}
<span className="bh-dim">41 min · $3.80 of $6 · 0 pushes · progress: yes</span>
            </pre>
          </div>
        </section>

        <section className="bh-sec" aria-labelledby="rails">
          <div className="bh-wrap">
            <p className="bh-label">03 / Guardrails</p>
            <h2 id="rails" className="bh-h2">Built for product work.<br />Fenced like it.</h2>
            <div className="bh-rails">
              {RAILS.map((r, i) => (
                <div className="bh-rail" key={r}><span className="bh-n">0{i + 1}</span><p>{r}</p></div>
              ))}
            </div>
          </div>
        </section>

        <section className="bh-sec" aria-labelledby="fit">
          <div className="bh-wrap">
            <p className="bh-label">04 / Where it fits</p>
            <h2 id="fit" className="bh-h2">Not another<br />agent sidebar.</h2>
            <div className="bh-tablewrap">
              <table className="bh-table">
                <thead>
                  <tr><th><span className="sr-only">Tool</span></th><th>What runs</th><th>Who&rsquo;s watching</th><th>When it stops to ask</th></tr>
                </thead>
                <tbody>
                  <tr><td><b>Conductor-style apps</b></td><td>Parallel agents on your Mac</td><td>You are</td><td>You decide live</td></tr>
                  <tr><td><b>Claude Code scheduled tasks</b></td><td>A prompt on a schedule or trigger, in the cloud or the Desktop app</td><td>Nobody</td><td>Up to your prompt</td></tr>
                  <tr className="bh-us"><td>Loops</td><td>A product goal on your Mac, built on Claude Code</td><td>Nobody, inside a fence</td><td>Built in: done checks, parking, &ldquo;Need from you&rdquo;</td></tr>
                </tbody>
              </table>
            </div>
            <p className="bh-note">Loops runs on Claude Code. It adds the management layer for unattended product work.</p>
          </div>
        </section>

        <section className="bh-sec" aria-labelledby="faq">
          <div className="bh-wrap">
            <p className="bh-label">05 / Straight answers</p>
            <h2 id="faq" className="bh-h2">Short questions.<br />Short answers.</h2>
            <div className="bh-faq">
              {FAQ.map(([q, a]) => (
                <div key={q}><h3>{q}</h3><p>{a}</p></div>
              ))}
            </div>
          </div>
        </section>

        <section className="bh-sec bh-install" id="install" aria-label="Install Loops">
          <div className="bh-wrap">
            <p className="bh-label">06 / Install</p>
            <h2 className="bh-h2">One line.<br />Four questions.</h2>
          </div>
          <InstallLine />
          <Onboarding />
        </section>

        <section className="bh-sec" aria-labelledby="record">
          <div className="bh-wrap">
            <p className="bh-label">07 / The record</p>
            <h2 id="record" className="bh-h2">I ran it for 33 nights.<br />Here&rsquo;s what broke.</h2>
            <div className="bh-stats">
              {stats.map(([big, label]) => (
                <div className="bh-stat" key={label}><b>{big}</b><span>{label}</span></div>
              ))}
            </div>
            <div className="bh-ctas">
              <Link className="bh-btn bh-ghost" href="/33-nights">Read the essay →</Link>
              <Link className="bh-text" href="/asks">The eleven asks</Link>
              <Link className="bh-text" href="/evidence">The receipts</Link>
            </div>
          </div>
        </section>

        <section className="bh-sec" id="hire" aria-labelledby="hire-h">
          <div className="bh-wrap">
            <div className="bh-hire">
              <div>
                <p className="bh-label">08 / Work with me</p>
                <h2 id="hire-h" className="bh-h2">Hand your team&rsquo;s product work to Claude Code overnight.</h2>
                <p>I set up Loops for product teams and run the first two weeks with you.</p>
                <a className="bh-btn" href={AUTHOR_LINKEDIN} target="_blank" rel="noreferrer">Message me on LinkedIn ↗</a>
              </div>
              <div className="bh-hire-side">
                <p className="bh-label">Night shift setup · two weeks</p>
                <ol>
                  <li>Install Loops on your repo, fenced for your team.</li>
                  <li>Write your first three loops together.</li>
                  <li>Tune the caps, checks and fence.</li>
                  <li>Review the first week of mornings with you.</li>
                </ol>
              </div>
            </div>
          </div>
        </section>

        <section className="bh-sec" aria-label="Other harnesses">
          <div className="bh-wrap">
            <p className="bh-label">09 / Other harnesses</p>
          </div>
          <Explorer tree={tree} label="harnesses" collapsed />
        </section>

        <footer className="bh-foot">
          <div className="bh-wrap">
            <p className="bh-big">Goal → Branch.</p>
            <p>
              productagent.dev · Loops is free and open source, MIT ·{' '}
              <a href={GITHUB} target="_blank" rel="noreferrer">Source on GitHub</a>
            </p>
          </div>
        </footer>
      </div>
    </Shell>
  );
}
