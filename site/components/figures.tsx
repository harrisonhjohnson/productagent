import Link from 'next/link';
import type { ReactNode } from 'react';
import { FigureToggle } from '@/components/figure-toggle';
import { MODEL_BADGE_OFFSET, MODEL_LABEL_T, MODEL_LAYOUT, type Fig, type FigNode, type St } from '@/lib/figures';
import { ATTRIBUTION_WORD, type Attribution, type Break, type Machine } from '@/lib/machine';

const W0 = 440, H0 = 236;
const tw = (s: string, px: number) => s.length * px * 0.52;
const WORDS = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'];
const word = (n: number) => WORDS[n] ?? String(n);
const cap = (s: string) => s[0].toUpperCase() + s.slice(1);
const BADGE_KIND: Record<Attribution, string> = { machine: 'm', agent: 'a', shared: 's', design: 'd' };

type Placed = FigNode & { w: number; h: number; isBad: boolean };

function place(n: FigNode, st: St): Placed | null {
  if (n.only && n.only !== st) return null;
  const o = { ...n, ...(n[st] || {}) };
  const isMine = st === 'f' && n.fmine === 0 ? 0 : o.mine;
  return { ...o, mine: isMine, w: n.w || 108, h: n.h || (o.s ? 38 : 28), isBad: n.bad === st || n.bad === true };
}

function clip(u: { x: number; y: number }, n: Placed) {
  return Math.min(u.x ? n.w / 2 / Math.abs(u.x) : 1e9, u.y ? n.h / 2 / Math.abs(u.y) : 1e9);
}

export function Diagram({ fig, st, label }: { fig: Fig; st: St; label: string }) {
  const W = fig.W || W0, H = fig.H || H0;
  const nodes: Record<string, Placed> = {};
  for (const n of fig.nodes) {
    const p = place(n, st);
    if (p) nodes[n.id] = p;
  }
  const edges: ReactNode[] = [], labels: ReactNode[] = [], top: ReactNode[] = [], extra: ReactNode[] = [];

  fig.edges.forEach((e, i) => {
    if (e.only && e.only !== st) return;
    const a = nodes[e.a], b = nodes[e.b];
    if (!a || !b) return;
    const p = { x: a.x, y: a.y + (e.ay || 0) }, q = { x: b.x, y: b.y + (e.by || 0) };
    const len = Math.hypot(q.x - p.x, q.y - p.y), u = { x: (q.x - p.x) / len, y: (q.y - p.y) / len };
    const ta = clip(u, a) + 2, tb = clip(u, b) + 6;
    const s = { x: p.x + u.x * ta, y: p.y + u.y * ta };
    let end = { x: q.x - u.x * tb, y: q.y - u.y * tb };
    const bad = !!e.bad;
    const cls = `ed${bad ? ' bad' : ''}${e.dash ? ' dash' : ''}`;
    if (e.cut) {
      const span = Math.hypot(end.x - s.x, end.y - s.y), stop = bad ? span * 0.72 : span - 6;
      end = { x: s.x + u.x * stop, y: s.y + u.y * stop };
      edges.push(<path key={`e${i}`} d={`M${s.x},${s.y}L${end.x},${end.y}`} className={cls} />);
      const nx = -u.y * 7, ny = u.x * 7;
      if (bad) top.push(<path key={`x${i}`} className="x" d={`M${end.x - 5},${end.y - 5}L${end.x + 5},${end.y + 5}M${end.x + 5},${end.y - 5}L${end.x - 5},${end.y + 5}`} />);
      else edges.push(<path key={`t${i}`} className="ed stop" d={`M${end.x + nx},${end.y + ny}L${end.x - nx},${end.y - ny}`} />);
    } else {
      edges.push(<path key={`e${i}`} d={`M${s.x},${s.y}L${end.x},${end.y}`} className={cls} />);
      const ax = end.x + u.x * 6, ay = end.y + u.y * 6, nx = -u.y * 3.6, ny = u.x * 3.6;
      edges.push(<path key={`a${i}`} className={`ah${bad ? ' bad' : ''}`} d={`M${ax},${ay}L${end.x + nx},${end.y + ny}L${end.x - nx},${end.y - ny}Z`} />);
    }
    if (e.l) {
      const t = e.t ?? 0.5, mx = s.x + (end.x - s.x) * t, w = tw(e.l, 9.5) + 8;
      let my = s.y + (end.y - s.y) * t;
      if (Math.abs(u.y) < 0.2 && w > Math.abs(end.x - s.x) * 0.9) my -= 10;
      labels.push(
        <g key={`l${i}`} className={`lb${bad ? ' bad' : ''}`}>
          <rect x={mx - w / 2} y={my - 7} width={w} height={13} rx={2} />
          <text x={mx} y={my + 3.3} textAnchor="middle">{e.l}</text>
        </g>,
      );
    }
  });

  if (fig.table) {
    const rows = [['', 'agent said', 'log said'], ['time', '~33 min', '6 min'], ['refusals', 'none', '34'], ['cost', '$0', '$0.602']];
    const x0 = 70, y0 = 160;
    rows.forEach((r, i) => {
      const y = y0 + i * 16;
      extra.push(<text key={`r${i}a`} x={x0} y={y} className="tx">{r[0]}</text>);
      extra.push(<text key={`r${i}b`} x={x0 + 110} y={y} className={i && st === 'b' ? 'tx bad' : 'tx'}>{r[1]}</text>);
      extra.push(<text key={`r${i}c`} x={x0 + 220} y={y} className={i && st === 'f' ? 'tx big' : 'tx'}>{r[2]}</text>);
      if (i && st === 'b') extra.push(<path key={`r${i}x`} className="x thin" d={`M${x0 + 106},${y - 3.5}L${x0 + 170},${y - 3.5}`} />);
    });
  }

  if (fig.units) {
    const cols = 21, sz = 9, gap = 2.2, x0 = 152, y0 = 22;
    for (let i = 0; i < fig.units; i++) {
      const c = i % cols, r = Math.floor(i / cols);
      extra.push(<rect key={`u${i}`} x={x0 + c * (sz + gap)} y={y0 + r * (sz + gap)} width={sz} height={sz} rx={1.5} className={st === 'b' ? 'u' : 'u ok'} />);
    }
    extra.push(
      <text key="ut" x={x0} y={y0 + 3 * (sz + gap) + 12} className={st === 'b' ? 'tx bad' : 'tx'}>
        {st === 'b' ? '63 identical rechecks, each marked progress' : '63 rechecks, 0 changed files, 0 progress'}
      </text>,
    );
    edges.push(<path key="ue" className="ed" d={`M${118},${36}L${x0 - 6},${36}`} />);
    extra.push(<text key="ul" x={(118 + x0) / 2} y={31} textAnchor="middle" className="tx">runs</text>);
  }

  for (const bd of fig.badges || []) {
    let x: number, y: number;
    if (bd.node) {
      const n = nodes[bd.node];
      x = n.x + n.w / 2 - 2;
      y = n.y - n.h / 2 - 1;
    } else {
      const a = nodes[bd.a!], b = nodes[bd.b!], t = bd.t ?? 0.5;
      x = a.x + (b.x - a.x) * t + (bd.dx || 0);
      y = a.y + (b.y - a.y) * t + (bd.dy || 0);
    }
    top.push(
      <a key={`b${bd.n}`} href={`${fig.badgeBase ?? ''}#fig-break-${bd.n}`} className={`bd ${bd.k}`} aria-label={`Break ${bd.n}`}>
        <circle cx={x} cy={y} r={9} />
        <text x={x} y={y + 3.6} textAnchor="middle">{bd.n}</text>
      </a>,
    );
  }

  return (
    <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={label} className="fig-svg">
      <g>{edges}</g>
      <g>{labels}</g>
      <g>
        {Object.values(nodes).map((n) => (
          <g key={n.id} className={`nd${n.isBad ? ' bad' : ''}${n.mine ? ' mine' : ''}`}>
            <rect x={n.x - n.w / 2} y={n.y - n.h / 2} width={n.w} height={n.h} rx={3} />
            <text x={n.x} y={n.s ? n.y - 2 : n.y + 4} textAnchor="middle" className="l">{n.l}</text>
            {n.s && <text x={n.x} y={n.y + 11} textAnchor="middle" className="s">{n.s}</text>}
          </g>
        ))}
        {extra}
      </g>
      <g>{top}</g>
    </svg>
  );
}

export function attributionCounts(m: Machine) {
  const c: Record<Attribution, number> = { machine: 0, agent: 0, shared: 0, design: 0 };
  for (const b of m.breaks) c[b.attribution]++;
  return c;
}

export function ModelFigure({ m, num, home }: { m: Machine; num?: number; home?: boolean }) {
  const fig: Fig = {
    n: 0, t: 'The night machine', W: 860, H: 500, badgeBase: home ? '/33-nights' : '',
    nodes: m.parts.map((p) => ({ id: p.id, x: MODEL_LAYOUT[p.id][0], y: MODEL_LAYOUT[p.id][1], l: p.label.replace("'", '’'), s: p.detail, mine: p.owner === 'mine' ? 1 : 0 })),
    edges: m.links.map((l) => ({ a: l.from, b: l.to, l: l.verb, t: MODEL_LABEL_T[`${l.from}>${l.to}`] })),
    badges: m.breaks.map((b) => {
      const k = BADGE_KIND[b.attribution];
      if ('part' in b.at) return { n: b.n, k, node: b.at.part };
      return { n: b.n, k, a: b.at.link[0], b: b.at.link[1], ...MODEL_BADGE_OFFSET[b.n] };
    }),
  };
  const c = attributionCounts(m);
  return (
    <figure className={`fig fig-model${home ? ' fig-home' : ''}`} id="fig-machine">
      <figcaption>
        {num ? <span className="fig-num">Figure {num}. </span> : null}{cap(word(c.machine))} of the {word(m.breaks.length)} breaks were in the
        machine around the agent. {cap(word(c.agent))} were the agent’s, {word(c.shared)} needed both, and {word(c.design)} was a
        rule working as designed. Each number links to its break{home ? ' in the essay' : ''}.
      </figcaption>
      <div className="fig-scroll">
        <Diagram fig={fig} st="b" label={`The parts of the night machine and how they connect, with the ${m.breaks.length} breaks pinned where they happened.`} />
      </div>
      <div className="fig-key">
        <span><i className="bd-key m" />Machine</span>
        <span><i className="bd-key a" />Agent</span>
        <span><i className="bd-key s" />Shared</span>
        <span><i className="bd-key d" />By design</span>
        <span><i className="box-key" />Parts I wrote</span>
        <span><Link href="/evidence/machine.json">machine.json</Link></span>
      </div>
    </figure>
  );
}

function Receipts({ b }: { b: Break }) {
  return (
    <p className="fig-receipts">
      <span className={`fig-tag ${BADGE_KIND[b.attribution]}`}>{ATTRIBUTION_WORD[b.attribution]}</span>
      <span className="fig-tag plain">{b.fix === 'shipped' ? 'Fix shipped' : 'Still open'}</span>
      {b.receipts.length ? (
        b.receipts.map((r) => <Link key={r.href + r.label} href={r.href}>{r.label} →</Link>)
      ) : (
        <span className="fig-muted">No row in the night table</span>
      )}
    </p>
  );
}

export function BreakFigure({ fig, b, num }: { fig: Fig; b: Break; num: number }) {
  return (
    <figure className="fig" id={`fig-break-${fig.n}`}>
      <figcaption><span className="fig-num">Figure {num}.</span> {fig.claim}</figcaption>
      <FigureToggle
        labels={['How it broke', b.fix === 'shipped' ? 'After the fix' : 'What it needs']}
        broke={<Diagram fig={fig} st="b" label={`${fig.t}. ${fig.nb}`} />}
        fixed={<><Diagram fig={fig} st="f" label={`${fig.t}. ${fig.nf}`} /><p className="fig-note">{fig.nf}</p></>}
      />
      <Receipts b={b} />
    </figure>
  );
}

export function AskFigure({ fig, num }: { fig: Fig; num: number }) {
  return (
    <figure className="fig" id={`fig-ask-${fig.id}`}>
      <figcaption><span className="fig-num">Figure {num}.</span> {fig.claim}</figcaption>
      <FigureToggle
        labels={['Today', 'Proposed']}
        broke={<Diagram fig={fig} st="b" label={`${fig.t}. ${fig.nb}`} />}
        fixed={<><Diagram fig={fig} st="f" label={`${fig.t}. ${fig.nf}`} /><p className="fig-note">{fig.nf}</p></>}
      />
    </figure>
  );
}

export function AskGrid({ m }: { m: Machine }) {
  const hit = new Set(m.asks.flatMap((a) => a.breaks));
  const notCC = m.breaks.filter((b) => !hit.has(b.n));
  return (
    <figure className="fig ask-grid">
      <figcaption>
        <span className="fig-num">Figure 1.</span> Each ask against the breaks from{' '}
        <Link href="/33-nights">33 nights</Link> it would have prevented. No ask covers breaks {notCC.map((b) => b.n).join(', ').replace(/, (\d+)$/, ' and $1')}. Those
        are fixed, or fixable, in my own setup.
      </figcaption>
      <div className="fig-scroll">
        <table>
          <thead>
            <tr>
              <th scope="col">Ask</th>
              {m.breaks.map((b) => (
                <th key={b.n} scope="col" title={b.title}>
                  <Link href={`/33-nights#fig-break-${b.n}`} className={`bd-key ${BADGE_KIND[b.attribution]} num`}>{b.n}</Link>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {m.asks.map((a) => (
              <tr key={a.id}>
                <th scope="row">{a.n}. {a.title}</th>
                {m.breaks.map((b) => (
                  <td key={b.n} aria-label={a.breaks.includes(b.n) ? `prevents break ${b.n}` : undefined}>{a.breaks.includes(b.n) ? '●' : ''}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="fig-note">Asks with an empty row came from friction outside the ten breaks: quota, cost, turn limits, skills, quiet defaults.</p>
    </figure>
  );
}

export function AskThumb({ fig, line }: { fig: Fig; line: ReactNode }) {
  return (
    <Link href={`/asks#fig-ask-${fig.id}`} className="ask-thumb">
      <Diagram fig={fig} st="b" label={`${fig.t}. ${fig.nb}`} />
      <b>{fig.t}</b>
      <span>{line}</span>
    </Link>
  );
}
