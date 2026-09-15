import { useEffect, useMemo, useState } from 'react';
import { BOOT_LINES, CADENCES, MODELS, NOUNS, STARTERS, formatKnobs, loopMarkdown } from './data';
import { DecisionGlyph, GraphGlyph, LidGlyph, MoonZGlyph, NOUN_GLYPH, PhoneGlyph, PlugGlyph } from './glyphs';
import { useReducedMotion, useTypedLines } from './hooks';
import { Laptop } from './scenes';
import type { BeatId, Cadence, Draft, Model, Noun, StarterId } from './types';

export function B0ColdBoot({
  active,
  complete,
  onReady,
}: {
  active: boolean;
  complete: boolean;
  onReady: (ready: boolean) => void;
}) {
  const reduced = useReducedMotion();
  const { visible, done, skip } = useTypedLines(BOOT_LINES, reduced, active, 380);
  const finished = complete || done;

  useEffect(() => {
    if (finished) onReady(true);
  }, [finished, onReady]);

  useEffect(() => {
    if (!active) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') skip();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [active, skip]);

  return (
    <section className="beat beat-boot">
      <div className="boot-panel">
        <p className="path">~/loops</p>
        <ol className="boot-log" aria-live="polite">
          {(finished ? BOOT_LINES : visible).map((line, i) => (
            <li key={line} className={i === (finished ? BOOT_LINES : visible).length - 1 && !finished ? 'is-live' : undefined}>
              <span className="prompt">›</span> {line}
            </li>
          ))}
        </ol>
        {finished ? (
          <p className="boot-wait">
            Installed. <span className="caret" />
          </p>
        ) : (
          <p className="boot-skip">Esc skips the boot</p>
        )}
      </div>
    </section>
  );
}

export function B1LidPromise() {
  return (
    <section className="beat beat-promise">
      <div className="promise-copy">
        <p className="eyebrow">THE PROMISE</p>
        <h2 className="display">
          Let an agent run a loop
          <br />
          while you sleep.
        </h2>
        <p className="lede">Lid shut. Same Mac. Same Claude plan. No server to rent, and nothing phones home.</p>
      </div>
      <div className="promise-mac">
        <Laptop open={0.14} screen="sky" />
      </div>
      <ul className="facts">
        <li>
          <span className="fact-glyph">
            <MoonZGlyph />
          </span>
          <div>
            <strong>Eight free hours a night.</strong>
            <p>The hours you are asleep become the hours the agent works.</p>
          </div>
        </li>
        <li>
          <span className="fact-glyph">
            <LidGlyph open={false} />
          </span>
          <div>
            <strong>Lid shut, laptop in the bag.</strong>
            <p>A Mac naps when you close it. The machine keeps a Run alive under a closed lid, then lets it sleep.</p>
          </div>
        </li>
        <li>
          <span className="fact-glyph">
            <PlugGlyph />
          </span>
          <div>
            <strong>What you already pay for.</strong>
            <p>Your Mac, your Claude plan. By default it waits for power and never runs under thirty percent battery.</p>
          </div>
        </li>
      </ul>
    </section>
  );
}

export function B2Loadout({
  armed,
  focused,
  onArm,
  onFocus,
}: {
  armed: Record<Noun, boolean>;
  focused: Noun;
  onArm: (word: Noun) => void;
  onFocus: (word: Noun) => void;
}) {
  const all = NOUNS.every((n) => armed[n.word]);
  return (
    <section className="beat beat-loadout">
      <header className="beat-head">
        <p className="eyebrow">LOADOUT</p>
        <h2>Four words. That’s the whole system.</h2>
        <p className="lede">Arm each one. {all ? 'Loaded. Continue.' : 'Press 1–4, or click.'}</p>
      </header>
      <ul className="nouns">
        {NOUNS.map((n) => {
          const Glyph = NOUN_GLYPH[n.word];
          const isOn = armed[n.word];
          const isFocus = focused === n.word;
          return (
            <li key={n.word}>
              <button
                type="button"
                className={`noun ${isOn ? 'is-armed' : ''} ${isFocus ? 'is-focus' : ''}`}
                onClick={() => onArm(n.word)}
                onMouseEnter={() => onFocus(n.word)}
                onFocus={() => onFocus(n.word)}
              >
                <span className="noun-key">{n.key}</span>
                <span className="noun-glyph">
                  <Glyph />
                </span>
                <span className="noun-word">{n.word}</span>
                <span className="noun-gloss">{n.gloss}</span>
                <span className="noun-body">{n.body}</span>
                <span className="noun-state">{isOn ? 'armed' : 'arm'}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

export function B3CreateLoop({
  draft,
  onPick,
  onPatch,
}: {
  draft: Draft;
  onPick: (id: StarterId) => void;
  onPatch: (patch: Partial<Draft>) => void;
}) {
  return (
    <section className="beat beat-create">
      <header className="beat-head">
        <p className="eyebrow">L-01 · DRAFT</p>
        <h2>Write one Loop. The agent never can.</h2>
        <p className="lede">
          Write the goal the way you would say it to a new hire on their first day. Then set four knobs. First three
          Runs you review.
        </p>
      </header>
      <div className="create-grid">
        <ul className="starters" aria-label="Starter loops">
          {STARTERS.map((s, i) => (
            <li key={s.id}>
              <button
                type="button"
                className={draft.starterId === s.id ? 'starter is-on' : 'starter'}
                onClick={() => onPick(s.id)}
              >
                <span className="starter-n">{i + 1}</span>
                <span className="starter-name">{s.name}</span>
                <span className="starter-goal">{s.goal}</span>
                <span className="starter-knobs">{formatKnobs(s.budget, s.cadence, s.model)}</span>
              </button>
            </li>
          ))}
        </ul>
        <div className="charter">
          <label className="field">
            <span>Goal</span>
            <textarea
              rows={3}
              value={draft.goal}
              onChange={(e) => onPatch({ goal: e.target.value })}
            />
          </label>
          <div className="knob-row">
            <label className="field">
              <span>Budget / run</span>
              <div className="stepper">
                <button type="button" onClick={() => onPatch({ budget: Math.max(1, draft.budget - 1) })}>
                  −
                </button>
                <strong>${draft.budget}</strong>
                <button type="button" onClick={() => onPatch({ budget: Math.min(12, draft.budget + 1) })}>
                  +
                </button>
              </div>
            </label>
            <label className="field">
              <span>Cadence</span>
              <select
                value={draft.cadence}
                onChange={(e) => onPatch({ cadence: e.target.value as Cadence })}
              >
                {CADENCES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>Model</span>
              <select value={draft.model} onChange={(e) => onPatch({ model: e.target.value as Model })}>
                {MODELS.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <pre className="md">{loopMarkdown(draft)}</pre>
          <p className="charter-foot">Lives in pm/LOOPS.md. You edit that file. The agent never can.</p>
        </div>
      </div>
    </section>
  );
}

export function B4Timelapse({
  active,
  complete,
  draft,
  onReady,
}: {
  active: boolean;
  complete: boolean;
  draft: Draft;
  onReady: (ready: boolean) => void;
}) {
  const reduced = useReducedMotion();
  const [t, setT] = useState(reduced || complete ? 1 : 0);

  useEffect(() => {
    if (!active) return;
    if (reduced) {
      setT(1);
      onReady(true);
      return;
    }
    setT(0);
    let raf = 0;
    const start = performance.now();
    const dur = 11000;
    const tick = (now: number) => {
      const p = Math.min(1, (now - start) / dur);
      setT(p);
      if (p < 1) raf = requestAnimationFrame(tick);
      else onReady(true);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [active, reduced, onReady]);

  useEffect(() => {
    if (!active) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setT(1);
        onReady(true);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [active, onReady]);

  const p = complete ? 1 : t;
  const minutes = Math.floor(p * (7 * 60 + 40)); // 23:12 → 06:52
  const clock = formatNightClock(23, 12, minutes);
  const open = p < 0.12 ? 1 - p / 0.12 : 0;
  const logs = nightLog(draft, p);

  return (
    <section className="beat beat-night">
      <header className="beat-head">
        <p className="eyebrow">ONE RUN · LID SHUT</p>
        <h2>While you sleep, literally.</h2>
        <p className="lede">
          Plugged in. Battery above thirty. Fence on. {draft.name} gets one bounded pass, then the machine sleeps.
        </p>
      </header>
      <div className="night-stage">
        <Laptop open={open} clock={clock} screen="sky" />
        <ol className="night-log" aria-live="polite">
          <li className="clock-line">{clock}</li>
          {logs.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ol>
      </div>
      {p >= 1 ? <p className="night-done">Four lines written. Continue.</p> : <p className="boot-skip">Esc skips the night</p>}
    </section>
  );
}

function formatNightClock(h: number, m: number, add: number) {
  const total = h * 60 + m + add;
  const hh = Math.floor(total / 60) % 24;
  const mm = total % 60;
  return `${String(hh).padStart(2, '0')}:${String(mm).padStart(2, '0')}`;
}

function nightLog(draft: Draft, t: number): string[] {
  const lines = [
    { at: 0.08, text: '23:14  plugged in · 94% · battery floor 30%' },
    { at: 0.16, text: `23:15  L-01 run · ${draft.model} · $${draft.budget}` },
    { at: 0.28, text: '23:16  fence: spend, push, merge — denied' },
    { at: 0.42, text: `01:02  ${workVerb(draft.starterId)}` },
    { at: 0.62, text: '03:41  still inside the fence' },
    { at: 0.82, text: '06:47  four lines written' },
    { at: 0.94, text: '06:48  lid shut · sleeping' },
  ];
  return lines.filter((l) => t >= l.at).map((l) => l.text);
}

function workVerb(id: StarterId): string {
  switch (id) {
    case 'changelogs':
      return 'reading public changelogs';
    case 'backlog':
      return 'shipping one backlog item';
    case 'tickets':
      return 'clustering yesterday’s tickets';
    case 'launch':
      return 'checking the launch checklist against the repo';
    case 'weekly':
      return 'drafting the weekly update';
    case 'icp':
      return 'finding ten companies that look like the customer';
  }
}

export function B5Morning({
  draft,
  settled,
  onSettle,
}: {
  draft: Draft;
  settled: boolean;
  onSettle: () => void;
}) {
  const starter = STARTERS.find((s) => s.id === draft.starterId) ?? STARTERS[0];
  const r = starter.report;
  return (
    <section className="beat beat-morning">
      <header className="beat-head">
        <p className="eyebrow">MORNING · FOUR LINES</p>
        <h2>If the four lines are missing, the run is not done.</h2>
        <p className="lede">
          One Loop. One Run. Four plain sentences. The last one is a Decision — settle it, or leave it for later.
        </p>
      </header>
      <article className="report">
        <p className="report-id">## L-01</p>
        <p>
          <span>Trying to:</span> {r.trying}
        </p>
        <p>
          <span>Did:</span> {r.did}
        </p>
        <p>
          <span>Decided:</span> {r.decided}
        </p>
        <p className="need">
          <span>Need from you:</span> {r.need}
        </p>
        <p className="where">Where to look: {r.where}</p>
      </article>
      <button type="button" className={settled ? 'settle is-on' : 'settle'} onClick={onSettle}>
        <DecisionGlyph />
        {settled ? 'Decision noted. Continue.' : 'This is yours. Mark it seen.'}
      </button>
    </section>
  );
}

const KARMA_NODES = [
  { id: 'l01', x: 50, y: 48, label: 'L-01 report' },
  { id: 'linear', x: 22, y: 28, label: 'Linear changelog' },
  { id: 'notion', x: 38, y: 18, label: 'Notion changelog' },
  { id: 'amp', x: 70, y: 22, label: 'Amplitude changelog' },
  { id: 'dec', x: 78, y: 58, label: 'Decision: threat or noise' },
  { id: 'brief', x: 28, y: 68, label: 'one-page brief' },
  { id: 'week', x: 58, y: 78, label: 'weekly draft' },
];

const KARMA_EDGES: [string, string][] = [
  ['l01', 'linear'],
  ['l01', 'notion'],
  ['l01', 'amp'],
  ['l01', 'dec'],
  ['l01', 'brief'],
  ['brief', 'week'],
  ['dec', 'amp'],
];

export function B6Karma() {
  const [hot, setHot] = useState('l01');
  const linked = useMemo(() => {
    const set = new Set<string>([hot]);
    for (const [a, b] of KARMA_EDGES) {
      if (a === hot) set.add(b);
      if (b === hot) set.add(a);
    }
    return set;
  }, [hot]);

  return (
    <section className="beat beat-karma">
      <header className="beat-head">
        <p className="eyebrow">
          <GraphGlyph /> KARMA · OPTIONAL
        </p>
        <h2>A month of reports stays searchable.</h2>
        <p className="lede">
          Every report the Loops write becomes a node. The graph finds the relationships, so last month’s Decision is
          one query away. Open source. After a month of mornings.
        </p>
      </header>
      <div className="constellation" onMouseLeave={() => setHot('l01')}>
        <svg viewBox="0 0 100 100" className="graph" role="img" aria-label="A small graph of reports and a Decision">
          {KARMA_EDGES.map(([a, b]) => {
            const na = KARMA_NODES.find((n) => n.id === a)!;
            const nb = KARMA_NODES.find((n) => n.id === b)!;
            const on = linked.has(a) && linked.has(b);
            return (
              <line
                key={`${a}-${b}`}
                x1={na.x}
                y1={na.y}
                x2={nb.x}
                y2={nb.y}
                className={on ? 'edge is-on' : 'edge'}
              />
            );
          })}
          {KARMA_NODES.map((n) => (
            <g
              key={n.id}
              className={linked.has(n.id) ? 'node is-on' : 'node'}
              onMouseEnter={() => setHot(n.id)}
            >
              <circle cx={n.x} cy={n.y} r={hot === n.id ? 2.6 : 1.8} />
              <text x={n.x} y={n.y - 3.6} textAnchor="middle">
                {n.label}
              </text>
            </g>
          ))}
        </svg>
      </div>
    </section>
  );
}

const CHAT_LINES = [
  'you:/loops',
  'bot:L-01  draft · weekly · sonnet · $2',
  'you:/loop L-01 budget 5',
  'bot:budget is 5. Dated. Marked as yours.',
  'you:this morning',
  'bot:## L-01\nTrying to: watch three competitors’ changelogs.\nNeed from you: threat, or noise?',
];

export function B7Phone({ active }: { active: boolean }) {
  const reduced = useReducedMotion();
  const { visible, done } = useTypedLines(CHAT_LINES, reduced, active, 520);

  return (
    <section className="beat beat-phone">
      <header className="beat-head">
        <p className="eyebrow">
          <PhoneGlyph /> FROM YOUR PHONE
        </p>
        <h2>The same four lines, in your pocket.</h2>
        <p className="lede">
          One markdown list, two doors: the terminal you already use, and Telegram. Change a budget. Pause a Loop. Read
          this morning’s four lines. Every edit lands in pm/LOOPS.md, dated and marked as yours.
        </p>
      </header>
      <div className="phone-wrap">
        <div className="phone">
          <div className="phone-bar">
            <span>09:14</span>
            <span>loops</span>
          </div>
          <ol className="chat">
            {visible.map((raw) => {
              const who = raw.startsWith('you:') ? 'you' : 'bot';
              const text = raw.slice(who.length + 1);
              return (
                <li key={raw} className={who}>
                  {text}
                </li>
              );
            })}
          </ol>
          <p className="composer">{done ? 'Message' : '…'}</p>
        </div>
      </div>
    </section>
  );
}

export function B8Live({ draft, onReplay }: { draft: Draft; onReplay: () => void }) {
  return (
    <section className="beat beat-live">
      <header className="beat-head">
        <p className="eyebrow">YOU’RE LIVE</p>
        <h2>Plug the laptop in tonight.</h2>
        <p className="lede">
          L-01 is written. Status: draft. The fence is on. Close the lid. In the morning, four sentences. Then you make
          the Decision only you can make.
        </p>
      </header>
      <ul className="checklist">
        <li>
          <strong>Loop</strong> {draft.name} · {formatKnobs(draft.budget, draft.cadence, draft.model)}
        </li>
        <li>
          <strong>Run</strong> one bounded pass, under the budget, inside the fence
        </li>
        <li>
          <strong>Order</strong> none tonight — Loops fill the slots
        </li>
        <li>
          <strong>Decision</strong> waiting for you in the morning
        </li>
      </ul>
      <div className="live-actions">
        <button type="button" className="primary" onClick={onReplay}>
          Replay from cold boot
        </button>
        <p className="fine">
          Fine print: waits until the Mac is plugged in; never runs under thirty percent battery. To skip a night, tell
          the bot: pause. Nothing phones home.
        </p>
      </div>
    </section>
  );
}

export function beatMeta(id: BeatId): { title: string; kicker: string; hint: string } {
  switch (id) {
    case 0:
      return { title: 'Cold boot', kicker: 'B0 · COLD BOOT', hint: 'begin' };
    case 1:
      return { title: 'Lid promise', kicker: 'B1 · LID SHUT', hint: 'continue' };
    case 2:
      return { title: 'Four words', kicker: 'B2 · LOADOUT', hint: 'after all four are armed' };
    case 3:
      return { title: 'First Loop', kicker: 'B3 · WRITE A LOOP', hint: 'confirm L-01' };
    case 4:
      return { title: 'Overnight', kicker: 'B4 · ONE RUN', hint: 'after the night, or Esc' };
    case 5:
      return { title: 'Morning', kicker: 'B5 · FOUR LINES', hint: 'mark the Decision seen' };
    case 6:
      return { title: 'Karma', kicker: 'B6 · OPTIONAL', hint: 'continue' };
    case 7:
      return { title: 'Phone', kicker: 'B7 · TELEGRAM', hint: 'continue' };
    case 8:
      return { title: 'You’re live', kicker: 'B8 · TONIGHT', hint: 'or R to replay' };
  }
}
