import { InstallLine } from '@/components/install-line';
import { Onboarding } from '@/components/onboarding';
import { Shell } from '@/components/shell';
import { AUTHOR_LINKEDIN, GITHUB } from '@/lib/content';
import Link from 'next/link';
import { getEvidence } from '@/lib/evidence';
import './geo.css';

const RAILS = [
  'A goal, not a prompt. Every loop has a definition of done and a review date.',
  'A night branch and an OS sandbox. It never pushes or deploys.',
  'A time limit per run. Spending caps per week and month.',
  'Parks itself after two stuck nights, and tells you which calls are yours.',
];

const FEATURES: [string, string, string][] = [
  ['bh-circle', 'Loops', 'Give it a goal, a cadence and a model. It works overnight on a night branch and leaves a four-line report with the calls that are yours.'],
  ['bh-square', 'Budget', 'It runs on the Claude subscription you already pay for. You set a time limit per run and spending caps per week and month. Every report says what the night cost.'],
  ['bh-tri', 'Skills', 'A library for the product work around the code: user research, design, prototypes, strategy. Each skill is a folder you can read before you run it.'],
];

const SKILLS: [string, [string, string, string][]][] = [
  ['User research', [['rootcause', '/harnesses/rootcause', 'Groups interview notes, support quotes and metrics by root cause, and drafts the questions to ask next.']]],
  ['Design', [
    ['flow-design', '/harnesses/flow-design', 'A design interview, one question per screen, that ends in a clickable prototype.'],
    ['prototype-swarm', '/harnesses/prototype-swarm', 'Fills in every missing screen of a prototype until each click goes somewhere.'],
    ['show-dont-tell', '/harnesses/show-dont-tell', 'Turns a wall of text into diagrams and charts drawn in code.'],
  ]],
  ['Strategy', [['pm-strategist', '/harnesses/pm-strategist', 'A strategy advisor that pressure-tests an idea instead of cheering for it.']]],
  ['Running the day', [['todo', '/harnesses/todo', 'One TODO file you can reach from Claude Code and from your phone.']]],
];

const WHO: [string, string][] = [
  ['Founders validating a business', 'You have an idea and no team yet. It does the research and the prototype while you talk to customers.'],
  ['Solo builders', 'You are the PM, the designer and the engineer. It keeps the work moving on the nights you can’t.'],
  ['Small teams', 'A product you plan to run for years. Loops keep the recurring work going and the budget stays inside the plan you have.'],
];

const REPORT: [string, string][] = [
  ['Trying to', 'read the second of five county permit files.'],
  ['Did', 'read all four documents. The permit says 96 units; the agency page says 98. Flagged it, didn’t guess.'],
  ['Decided', 'one row per permit, not per building.'],
  ['Need from you', 'check the renewal on the state portal. It needs a login the fence denies.'],
];

const FAQ: [string, string][] = [
  ['What does it cost?', 'Nothing extra. It runs on the Claude or ChatGPT plan you already pay for, under caps you set.'],
  ['Does my laptop stay on?', 'Plugged in, lid open or shut. It runs in the first window your Mac is awake and on power.'],
  ['How do I know the report is true?', 'One command in the morning has a second model check the report against the actual diff.'],
  ['Can it be shut down or acquired?', 'It’s MIT-licensed files in your repo. There’s nothing to shut down.'],
  ['Only code?', 'No. Any goal that ends in files: research, docs, HTML prototypes, fixes.'],
  ['Windows or Linux?', 'Not yet. macOS only.'],
];

export default function Home() {
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
            <p className="bh-label">Open source · built on Claude Code</p>
            <h1 id="page-heading" className="bh-h1">A product development <span className="bh-red">agent.</span></h1>
            <p className="bh-sub">
              productagent does the product work as well as the code: user research, design, prototypes and fixes. It
              keeps going overnight, on a budget, on the Claude subscription you already pay for.
            </p>
            <div className="bh-ctas">
              <a className="bh-btn" href="#install">Install it ↓</a>
              <a className="bh-text" href="#agency">Or work with the agency →</a>
            </div>
            <p className="bh-byline">
              Built and run by <a href={AUTHOR_LINKEDIN} target="_blank" rel="noreferrer">Harrison Johnson</a>, a product
              manager, with Claude Code. Claude wrote most of the code; the calls are mine.
            </p>
          </div>
          <figure className="bh-art">
            <div className="bh-moon" aria-hidden="true" /><div className="bh-bar" aria-hidden="true" /><div className="bh-sun" aria-hidden="true" />
            <div className="bh-report">
              <p className="bh-dim">pm/nights/2026-09-15.md</p>
              <p className="bh-k">## Permit research, iteration 2</p>
              <dl>
                {REPORT.map(([k, v]) => (
                  <div key={k}><dt className="bh-k">{k}</dt><dd>{v}</dd></div>
                ))}
              </dl>
              <p className="bh-dim">41 min · $3.80 of $6 · 0 pushes · progress: yes</p>
            </div>
            <figcaption>
              What a loop leaves you in the morning. An example, modeled on a real night.{' '}
              <Link href="/evidence">The record of 33 real ones →</Link>
            </figcaption>
          </figure>
        </header>

        <section className="bh-sec" aria-labelledby="what">
          <div className="bh-wrap">
            <p className="bh-label">01 / What&rsquo;s in it</p>
            <h2 id="what" className="bh-h2">Three parts.<br />One agent.</h2>
            <div className="bh-grid3">
              {FEATURES.map(([shape, name, text]) => (
                <div className="bh-card" key={name}><div className={`bh-shape ${shape}`} /><h3>{name}</h3><p>{text}</p></div>
              ))}
            </div>
          </div>
        </section>

        <section className="bh-sec" aria-labelledby="skills">
          <div className="bh-wrap">
            <p className="bh-label">02 / Skills</p>
            <h2 id="skills" className="bh-h2">Product work.<br />Written down.</h2>
            <div className="bh-skills">
              {SKILLS.map(([group, items]) => (
                <div className="bh-skillrow" key={group}>
                  <h3>{group}</h3>
                  <ul>
                    {items.map(([name, href, text]) => (
                      <li key={name}><Link href={href}>{name}</Link><span>{text}</span></li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
            <p className="bh-note">Copy any skill folder into <code>~/.claude/skills/</code>. <Link href="/about#harnesses">The full list →</Link></p>
          </div>
        </section>

        <section className="bh-sec" aria-labelledby="who">
          <div className="bh-wrap">
            <p className="bh-label">03 / Who it&rsquo;s for</p>
            <h2 id="who" className="bh-h2">Small teams.<br />Long projects.</h2>
            <div className="bh-grid3">
              {WHO.map(([name, text]) => (
                <div className="bh-card" key={name}><h3 style={{ marginTop: 0 }}>{name}</h3><p>{text}</p></div>
              ))}
            </div>
          </div>
        </section>

        <section className="bh-sec" aria-labelledby="rails">
          <div className="bh-wrap">
            <p className="bh-label">04 / Loops</p>
            <h2 id="rails" className="bh-h2">It works at night.<br />Inside a fence.</h2>
            <div className="bh-rails">
              {RAILS.map((r, i) => (
                <div className="bh-rail" key={r}><span className="bh-n">0{i + 1}</span><p>{r}</p></div>
              ))}
            </div>
          </div>
        </section>

        <section className="bh-sec" aria-labelledby="fit">
          <div className="bh-wrap">
            <p className="bh-label">05 / Where it fits</p>
            <h2 id="fit" className="bh-h2">Not another<br />agent sidebar.</h2>
            <div className="bh-tablewrap">
              <table className="bh-table">
                <thead>
                  <tr><th><span className="sr-only">Tool</span></th><th>What runs</th><th>When it stops to ask</th></tr>
                </thead>
                <tbody>
                  <tr><td><b>Conductor-style apps</b></td><td>Parallel agents on your Mac, while you watch</td><td>You decide live</td></tr>
                  <tr><td><b>Claude Code scheduled tasks</b></td><td>A prompt on a schedule or trigger, in the cloud or the Desktop app</td><td>Up to your prompt</td></tr>
                  <tr className="bh-us"><td>Loops</td><td>A product goal on your Mac, inside a fence, built on Claude Code</td><td>Built in: done checks, parking, &ldquo;Need from you&rdquo;</td></tr>
                </tbody>
              </table>
            </div>
            <p className="bh-note">Loops runs on Claude Code. It adds the management layer for unattended product work.</p>
          </div>
        </section>

        <section className="bh-sec" aria-labelledby="faq">
          <div className="bh-wrap">
            <p className="bh-label">06 / Straight answers</p>
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
            <p className="bh-label">07 / Install</p>
            <h2 className="bh-h2">One line.<br />Four questions.</h2>
          </div>
          <InstallLine />
          <Onboarding />
        </section>

        <section className="bh-sec" id="agency" aria-labelledby="agency-h">
          <div className="bh-wrap">
            <div className="bh-hire">
              <div>
                <p className="bh-label">08 / The agency</p>
                <h2 id="agency-h" className="bh-h2">Or have it set up for you.</h2>
                <p>I install productagent for your team and run the first two weeks with you. Past clients include{' '}
                  <a href="https://deepgreen.co" target="_blank" rel="noreferrer">deepgreen.co</a>.</p>
                <a className="bh-btn" href={AUTHOR_LINKEDIN} target="_blank" rel="noreferrer">Message me on LinkedIn ↗</a>
              </div>
              <div className="bh-hire-side">
                <p className="bh-label">Setup · two weeks</p>
                <ol>
                  <li>Install Loops on your repo, fenced for your team.</li>
                  <li>Write your first three loops together.</li>
                  <li>Pick the skills your team needs and tune the budget.</li>
                  <li>Review the first week of mornings with you.</li>
                </ol>
              </div>
            </div>
          </div>
        </section>

        <section className="bh-sec" aria-labelledby="record">
          <div className="bh-wrap">
            <p className="bh-label">09 / The record</p>
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

        <footer className="bh-foot">
          <div className="bh-wrap">
            <p className="bh-big">Goal → Branch.</p>
            <p>
              productagent.dev · Loops is free and open source, MIT ·{' '}
              <a href={GITHUB} target="_blank" rel="noreferrer">Source on GitHub</a> ·{' '}
              <Link href="/about#harnesses">Other harnesses</Link>
            </p>
          </div>
        </footer>
      </div>
    </Shell>
  );
}
