import Link from 'next/link';
import { CycleDiagram, DecisionGlyph, LoopGlyph, RunGlyph, SleepBlock, StickyNotes } from './loop-usecases';
import { Morning } from './morning';

function ReadGlyph() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 6h16M4 10h16M4 14h10M4 18h7" />
    </svg>
  );
}

type Harness = { label: string; href: string; external?: boolean; note: string };

type Station = {
  n: number;
  word: string;
  owns: string;
  glyph: React.ReactNode;
  claim: string;
  how: string;
  harnesses: Harness[];
  proof?: React.ReactNode;
};

const STATIONS: Station[] = [
  {
    n: 1,
    word: 'Decide',
    owns: 'a Decision is anything only you can settle',
    glyph: <DecisionGlyph />,
    claim: 'Make the call before you make the thing.',
    how: 'The agent never guesses at a decision. It hands it back. These are the tools for the part of the job that stays yours: pressure-testing a bet, drawing the flow before writing it, setting the dials once.',
    harnesses: [
      { label: 'pm-strategist', href: '/harnesses/pm-strategist/pm-strategist.md', note: 'three lenses that argue back' },
      { label: 'flow-design', href: '/harnesses/flow-design/SKILL.md', note: 'a screen-by-screen interview that ends in a prototype' },
      { label: 'prototype-swarm', href: '/harnesses/prototype-swarm/SKILL.md', note: 'fills every screen the prototype links to' },
      { label: 'the charter', href: '/harnesses/loops/pm/CHARTER.md', note: 'model, caps, floor, cadence, decided once' },
    ],
  },
  {
    n: 2,
    word: 'Delegate',
    owns: 'a Loop is a goal that renews; an Order is one-off for tonight',
    glyph: <LoopGlyph />,
    claim: 'Write it the way you would tell a new hire.',
    how: 'One sentence and four knobs: goal, budget, cadence, model. Standing orders renew themselves; one-offs go first. From the terminal, or from your phone.',
    harnesses: [
      { label: 'loops', href: '/harnesses/loops/README.md', note: 'the concept page' },
      { label: 'orders', href: '/harnesses/loops/pm/templates/ORDERS.md', note: 'one-offs for tonight' },
      { label: 'the phone bot', href: '/harnesses/todo/bot/BOT.md', note: 'add a loop, change a knob, pause, from Telegram' },
    ],
    proof: <StickyNotes />,
  },
  {
    n: 3,
    word: 'Run',
    owns: 'a Run is one bounded pass, unattended',
    glyph: <RunGlyph />,
    claim: 'Lid shut. Fenced. Under budget.',
    how: 'The machine takes the first window that fits: plugged in, enough battery, enough of your week left. One run, one branch, no pushes, a hard timeout. Claude Code or Codex.',
    harnesses: [
      { label: 'the machine', href: '/harnesses/loops/MACHINE.md', note: 'runner, checker, watchdog, judge' },
      { label: 'the fence', href: '/harnesses/loops/settings.json', note: 'every allow and deny line' },
      { label: 'the quota floor', href: '/harnesses/loops/ops/night/quota.py', note: 'never the last fifth of your week' },
    ],
    proof: <SleepBlock />,
  },
  {
    n: 4,
    word: 'Read',
    owns: 'four lines: trying, did, decided, need from you',
    glyph: <ReadGlyph />,
    claim: 'Four sentences, then back to Decide.',
    how: 'Every run ends with four plain lines per loop, each pointing at the file it came from. A judge checks the report against the diff. Reports become memory, so last month’s mistake is one query away.',
    harnesses: [
      { label: 'the morning judge', href: '/harnesses/loops/ops/health/judge-night.md', note: 'grades the report against what was actually written' },
      { label: 'the health desk', href: '/harnesses/loops/ops/health/fleet-health.py', note: 'ground truth from transcripts, not self-report' },
      { label: 'karma', href: 'https://github.com/harrisonhjohnson/karma', external: true, note: 'a personal knowledge graph of every report' },
    ],
    proof: <Morning />,
  },
];

export function Stations() {
  return (
    <section className="stations" aria-labelledby="stations-heading">
      <div className="stations-intro">
        <p className="section-label" id="stations-heading">THE WHOLE THING IN ONE PICTURE</p>
        <p className="stations-lede">
          Give an agent standing orders. Only ever do the parts only you can do. Four stations, and every folder on
          this site lives at exactly one of them.
        </p>
        <div className="cycle-wrap"><CycleDiagram /></div>
      </div>

      <ol className="station-list">
        {STATIONS.map((s) => (
          <li className="stn" key={s.word} id={`station-${s.word.toLowerCase()}`}>
            <div className="stn-rail" aria-hidden="true">
              <span className="stn-num">{s.n}</span>
              <span className="stn-line" />
            </div>
            <div className="stn-body">
              <header className="stn-head">
                <span className="stn-glyph">{s.glyph}</span>
                <div>
                  <h2>{s.word}</h2>
                  <p className="stn-owns">{s.owns}</p>
                </div>
              </header>
              <p className="stn-claim">{s.claim}</p>
              <p className="stn-how">{s.how}</p>
              <ul className="stn-harnesses" aria-label={`Folders for ${s.word}`}>
                {s.harnesses.map((h) => (
                  <li key={h.href}>
                    {h.external ? (
                      <a href={h.href} target="_blank" rel="noreferrer">{h.label} ↗</a>
                    ) : (
                      <Link href={h.href}>{h.label}</Link>
                    )}
                    <span>{h.note}</span>
                  </li>
                ))}
              </ul>
              {s.proof && <div className="stn-proof">{s.proof}</div>}
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
