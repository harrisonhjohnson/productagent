import { SCORERS, SCORER_MEANING, type Evidence } from '@/lib/evidence';

const CAP = 14;
const md = (d: string) => `${Number(d.slice(5, 7))}/${Number(d.slice(8, 10))}`;

function NightsChart({ ev }: { ev: Evidence }) {
  const nights = ev.nights.filter((n) => n.lane === 'night');
  return (
    <figure className="chart">
      <figcaption>Cost of each night at API prices. Gold nights did not finish clean.</figcaption>
      <div className="chart-bars" role="img" aria-label={`${nights.length} nights, one bar each, cost in dollars`}>
        {nights.map((n) => (
          <div
            key={n.date}
            className={`chart-bar${n.status === 'ok' ? '' : ' warn'}${n.cost_usd > CAP ? ' over' : ''}`}
            style={{ height: `${(Math.min(n.cost_usd, CAP) / CAP) * 100}%` }}
            title={`${md(n.date)} · ${n.status} · $${n.cost_usd.toFixed(2)}`}
          >
            {n.cost_usd > CAP && <span>${n.cost_usd.toFixed(0)}</span>}
          </div>
        ))}
      </div>
      <div className="chart-axis"><span>{md(nights[0].date)}</span><span>{md(nights[nights.length - 1].date)}</span></div>
    </figure>
  );
}

function InterventionsChart({ ev }: { ev: Evidence }) {
  const base = ev.totals.interventions.baseline_2026_09_18;
  const rows = [
    { date: '2026-09-18', v: base, base: true },
    ...ev.nights.filter((n) => n.lane === 'night' && n.interventions != null).map((n) => ({ date: n.date, v: n.interventions as number, base: false })),
  ];
  return (
    <figure className="chart">
      <figcaption>Things I did by hand the next morning. First bar is the baseline; the line is my target of one.</figcaption>
      <div className="chart-bars chart-iv" role="img" aria-label={`Interventions per morning: baseline ${base}, then ${rows.slice(1).map((r) => r.v).join(', ')}`}>
        <div className="chart-target" style={{ bottom: `${(1 / base) * 100}%` }} />
        {rows.map((r) => (
          <div key={r.date} className={`chart-bar${r.base ? ' base' : ''}`} style={{ height: `${Math.max(r.v / base, 0.012) * 100}%` }}>
            <span>{r.v}</span>
          </div>
        ))}
      </div>
      <div className="chart-axis"><span>{md(rows[0].date)}</span><span>{md(rows[rows.length - 1].date)}</span></div>
    </figure>
  );
}

function ChecksChart({ ev }: { ev: Evidence }) {
  const t = ev.totals.trajectory_clean;
  return (
    <figure className="chart">
      <figcaption>Seven checks run on every scored session, read from the transcripts, not the reports.</figcaption>
      <div className="checks">
        {SCORERS.map((s) => {
          const { clean, scored } = t[s];
          return (
            <div key={s} className="check">
              <span className="check-name">{SCORER_MEANING[s]}</span>
              <span className="check-meter"><span style={{ width: `${(100 * clean) / scored}%` }} className={clean === scored ? '' : 'warn'} /></span>
              <span className="check-n">{clean}/{scored}</span>
            </div>
          );
        })}
      </div>
    </figure>
  );
}

export function EssayChart({ name, ev }: { name: string; ev: Evidence }) {
  if (name === 'nights') return <NightsChart ev={ev} />;
  if (name === 'interventions') return <InterventionsChart ev={ev} />;
  if (name === 'checks') return <ChecksChart ev={ev} />;
  return null;
}
