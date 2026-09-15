const STROKE = { fill: 'none', stroke: 'currentColor', strokeWidth: 1.6, strokeLinecap: 'round', strokeLinejoin: 'round' } as const;

export function LoopGlyph() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" {...STROKE}>
      <path d="M19 12a7 7 0 1 1-2.1-5" />
      <path d="M17 3v4h-4" />
    </svg>
  );
}
export function RunGlyph() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" {...STROKE}>
      <path d="M4 12h13" />
      <path d="M13 7l5 5-5 5" />
    </svg>
  );
}
export function OrderGlyph() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" {...STROKE}>
      <path d="M6 4h12v16H6z" />
      <path d="M9 9h6M9 13h6M9 17h3" />
      <circle cx="12" cy="4" r="1.6" fill="currentColor" stroke="none" />
    </svg>
  );
}
export function DecisionGlyph() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" {...STROKE}>
      <path d="M12 20V11" />
      <path d="M12 11L6 5M12 11l6-6" />
      <circle cx="6" cy="5" r="1.4" fill="currentColor" stroke="none" />
      <circle cx="18" cy="5" r="1.4" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function PlugGlyph() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" {...STROKE}>
      <path d="M9 3v5M15 3v5" />
      <path d="M6 8h12v3a6 6 0 0 1-12 0z" />
      <path d="M12 17v4" />
    </svg>
  );
}
export function LidGlyph({ open }: { open: boolean }) {
  return open ? (
    <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" {...STROKE}>
      <path d="M3 18h18" />
      <path d="M6 18V7l12-3v14" />
    </svg>
  ) : (
    <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" {...STROKE}>
      <path d="M3 17h18" />
      <path d="M5 17v-2h14v2" />
    </svg>
  );
}
export function MoonZGlyph() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" {...STROKE}>
      <path d="M9 4a8 8 0 1 0 9 12A7 7 0 0 1 9 4z" />
      <path d="M15 3h4l-4 4h4" />
    </svg>
  );
}

const WORDS = [
  { word: 'Loop', glyph: <LoopGlyph />, gloss: 'a goal that keeps renewing' },
  { word: 'Run', glyph: <RunGlyph />, gloss: 'one pass at it, tonight' },
  { word: 'Order', glyph: <OrderGlyph />, gloss: 'a one-off note for tonight' },
  { word: 'Decision', glyph: <DecisionGlyph />, gloss: 'what only you can settle' },
];

/** One picture of the whole thing: you write a goal by day, the agent runs at night, you read four lines and decide. */
function LoopCycle() {
  return (
    <svg className="cycle" viewBox="0 0 640 300" role="img" aria-labelledby="cycle-title">
      <title id="cycle-title">The loop: you set a goal, the agent runs at night under a budget, you read four lines in the morning, you decide, and the goal renews.</title>
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M0 0L10 5L0 10z" fill="currentColor" />
        </marker>
      </defs>

      {/* day / night halves */}
      <text x="320" y="22" textAnchor="middle" className="cycle-band">DAY · YOU</text>
      <text x="320" y="292" textAnchor="middle" className="cycle-band">NIGHT · THE AGENT</text>
      <line x1="40" y1="150" x2="600" y2="150" className="cycle-horizon" />

      {/* arrows: goal → run → four lines → decide → goal */}
      <g className="cycle-arrows" markerEnd="url(#arrow)">
        <path d="M112 108 V 192" markerEnd="url(#arrow)" />
        <path d="M206 232 H 434" markerEnd="url(#arrow)" />
        <path d="M528 192 V 108" markerEnd="url(#arrow)" />
        <path d="M434 68 H 206" markerEnd="url(#arrow)" />
      </g>

      {/* four stations */}
      <g className="station" transform="translate(112 68)">
        <rect x="-94" y="-34" width="188" height="68" rx="3" />
        <text y="-8" textAnchor="middle" className="station-title">1 · Write a goal</text>
        <text y="12" textAnchor="middle" className="station-sub">one sentence + four knobs</text>
      </g>
      <g className="station" transform="translate(528 68)">
        <rect x="-94" y="-34" width="188" height="68" rx="3" />
        <text y="-8" textAnchor="middle" className="station-title">4 · Decide</text>
        <text y="12" textAnchor="middle" className="station-sub">merge, park, or change a knob</text>
      </g>
      <g className="station station-night" transform="translate(112 232)">
        <rect x="-94" y="-34" width="188" height="68" rx="3" />
        <text y="-8" textAnchor="middle" className="station-title">2 · One run</text>
        <text y="12" textAnchor="middle" className="station-sub">inside the fence, under budget</text>
      </g>
      <g className="station station-night" transform="translate(528 232)">
        <rect x="-94" y="-34" width="188" height="68" rx="3" />
        <text y="-8" textAnchor="middle" className="station-title">3 · Four lines</text>
        <text y="12" textAnchor="middle" className="station-sub">trying · did · decided · need</text>
      </g>

      {/* sun and moon */}
      <g className="cycle-sky" transform="translate(320 100)">
        <circle r="9" />
        <path d="M0-16v3M0 13v3M-16 0h3M13 0h3M-11-11l2 2M9 9l2 2M11-11l-2 2M-9 9l-2 2" />
      </g>
      <g className="cycle-sky" transform="translate(320 200)">
        <path d="M4-11a11 11 0 1 0 8 15A9 9 0 0 1 4-11z" />
      </g>
    </svg>
  );
}

type Note = { goal: string; knobs: string; tilt: number };

const NOTES: Note[] = [
  { goal: 'Watch three competitors’ changelogs. Tell me what changed and whether it matters.', knobs: 'weekly · sonnet · $2 a run', tilt: -1.6 },
  { goal: 'Ship one small fix from the backlog. Verify it renders before you report it.', knobs: 'nightly · opus · $6 a run', tilt: 1.1 },
  { goal: 'Read yesterday’s support tickets. Cluster them. Name the top three themes.', knobs: 'nightly · sonnet · $3 a run', tilt: -0.7 },
  { goal: 'Check every box on the launch checklist against the repo. Flag the ones that lie.', knobs: 'every 2nd night · sonnet · $2 a run', tilt: 1.8 },
  { goal: 'Draft the weekly update from this week’s reports. I edit. I send.', knobs: 'weekly · opus · $4 a run', tilt: -1.2 },
  { goal: 'Find ten companies that look like our best customer. Say why, with links.', knobs: 'every 3rd night · sonnet · $3 a run', tilt: 0.9 },
];

export function LoopUseCases() {
  return (
    <section className="usecases" aria-labelledby="usecases-heading">
      <p className="section-label">THE WHOLE THING IN ONE PICTURE</p>
      <div className="cycle-wrap">
        <LoopCycle />
      </div>

      <ul className="words" aria-label="The four words">
        {WORDS.map((w) => (
          <li key={w.word}>
            <span className="word-glyph">{w.glyph}</span>
            <span className="word-name">{w.word}</span>
            <span className="word-gloss">{w.gloss}</span>
          </li>
        ))}
      </ul>


      <p className="section-label">WHILE YOU SLEEP, LITERALLY</p>
      <div className="sleep">
        <p className="sleep-lede">
          Close the laptop at night. Open it in the morning to work that got done: the fix shipped and checked, the
          tickets sorted, the update drafted. Same Mac, same Claude plan, no server to rent.
        </p>
        <ul className="sleep-rules" aria-label="Why it matters">
          <li>
            <span className="sleep-glyph"><MoonZGlyph /></span>
            <div>
              <strong>Eight free hours a night.</strong>
              <p>The hours you are asleep become the hours the agent works. A goal you would never get to by day gets a run every night.</p>
            </div>
          </li>
          <li>
            <span className="sleep-glyph"><LidGlyph open={false} /></span>
            <div>
              <strong>Lid shut, laptop in the bag.</strong>
              <p>A Mac naps the second you close it. The folder carries the settings that keep it working under a closed lid, then let it sleep again.</p>
            </div>
          </li>
          <li>
            <span className="sleep-glyph"><PlugGlyph /></span>
            <div>
              <strong>Runs on what you already pay for.</strong>
              <p>Your own laptop, your own Claude subscription. No cloud minutes, no second machine, nothing phones home.</p>
            </div>
          </li>
        </ul>
        <p className="sleep-foot">
          Fine print: by default it waits until the Mac is plugged in and never runs under thirty percent battery, so
          you do not wake up to a dead laptop. Both are settings. To skip a night, tell the bot: pause.
        </p>
      </div>

      <p className="section-label" id="usecases-heading">WHAT WOULD YOU LOOP?</p>
      <p className="usecases-lede">
        A loop is a sticky note with a budget. Write the goal the way you would say it to a new hire on their first
        day, then pick a cadence, a model and a price. These are examples, not live loops.
      </p>
      <ul className="notes" aria-label="Example loops">
        {NOTES.map((n, i) => (
          <li className="note" key={i} style={{ ['--tilt' as string]: `${n.tilt}deg` }}>
            <span className="note-pin" aria-hidden="true" />
            <p className="note-goal">{n.goal}</p>
            <p className="note-knobs">{n.knobs}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
