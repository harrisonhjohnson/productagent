import type { Metadata } from 'next';
import Link from 'next/link';
import { DescentPanel } from '@/components/descent-panel';
import { Shell } from '@/components/shell';
import { GITHUB } from '@/lib/content';
import { SCORERS, SCORER_MEANING, getEvidence, lastNight, type NightRow } from '@/lib/evidence';

export const metadata: Metadata = {
  title: 'evidence',
  description:
    'Every unattended run of Loops on the author’s machine, as the runner and the health desk recorded it: nights, cost, trajectory scores, fence refusals, judge grades, interventions. Numbers only, exported from the same files the morning reads.',
};

const pct = (a: number, b: number) => (b ? `${Math.round((100 * a) / b)}%` : '–');
const usd = (n: number) => `$${n.toFixed(2)}`;
const mins = (s: number) => `${Math.round(s / 60)}m`;

function Stat({ big, label, note }: { big: string; label: string; note?: string }) {
  return (
    <div className="ev-stat">
      <div className="ev-stat-big">{big}</div>
      <div className="ev-stat-label">{label}</div>
      {note && <div className="ev-stat-note">{note}</div>}
    </div>
  );
}

function statusWord(s: string) {
  return s === 'ok' ? 'ok' : s;
}

function trajCell(n: NightRow) {
  if (!n.sessions_scored) return <span className="ev-muted">not scored</span>;
  const bad = SCORERS.filter((k) => n.trajectory[k] !== undefined && (n.trajectory[k] as number) < 1);
  if (!bad.length) return <span>clean</span>;
  return <span className="ev-warn">{bad.join(', ')}</span>;
}

export default function EvidencePage() {
  const ev = getEvidence();
  if (!ev) {
    return (
      <Shell path="/evidence">
        <section className="tree-panel">
          <div className="why-header"><h1>No evidence file yet.</h1></div>
        </section>
      </Shell>
    );
  }
  const t = ev.totals;
  const nights = ev.nights.filter((n) => n.lane === 'night').slice().reverse();
  const last = lastNight(ev);
  const statusLine = Object.entries(t.night_status)
    .sort((a, b) => b[1] - a[1])
    .map(([k, v]) => `${v} ${statusWord(k)}`)
    .join(' · ');
  const unclean = (k: (typeof SCORERS)[number]) => t.trajectory_clean[k].scored - t.trajectory_clean[k].clean;
  const gitBad = unclean('git_readonly');
  const reportBad = unclean('report_written');
  const judgeLine =['A', 'B', 'C', 'D', 'E'].filter((c) => t.judge[c]).map((c) => `${c}×${t.judge[c]}`).join(' · ') || 'none';

  return (
    <Shell path="/evidence">
      <section className="tree-panel read read-wide" aria-labelledby="ev-heading">
        <nav className="crumbs" aria-label="Breadcrumb"><Link href="/">harnesses</Link><span>/</span><span aria-current="page">evidence</span></nav>
        <div className="why-header">
          <p className="hero-eyebrow why-eyebrow">THE NUMBERS BEHIND <Link href="/33-nights">33 NIGHTS</Link></p>
          <h1 id="ev-heading">The receipts.</h1>
          <p className="why-lede">
            For 33 nights Claude Code worked unattended on my Mac. This page is every one of those nights, as the
            records saw them: the cost ledger the runner writes, seven automatic checks the health desk runs over each
            transcript, the refused calls the runner lists under each report, an LLM judge’s grade of each report
            against the actual diff, and how many things I had to do by hand the next morning. Nothing here is
            written by the agent about itself. The story is in <Link href="/33-nights">the essay</Link>; what I’d
            change in Claude Code is in <Link href="/asks">the asks</Link>.
          </p>
          <p className="why-lede">
            Read it with its limits. These are runs on one person’s Mac, on one person’s side projects. The work was chores:
            ship a fix, read a feed, write candidate rows. It is not a benchmark of product judgment, and the judge has
            run three times. What it does show is whether the machine stays inside its fence, what a night costs, and
            whether the morning is getting shorter.
          </p>
          <p className="why-rule">
            {ev.through ? `Frozen at ${ev.through}` : `Generated ${ev.generated.slice(0, 16).replace('T', ' ')}`} · {t.first_night} to {t.last_night} · export script in the loops harness
          </p>
        </div>

        <h2 className="why-part"><span>I</span> Totals</h2>
        <div className="ev-stats">
          <Stat big={String(t.nights)} label="nights run" note={statusLine} />
          <Stat big={usd(t.night_cost_usd)} label="night spend, API-equivalent" note={`${usd(t.all_lanes_cost_usd)} across ${t.runs_all_lanes} runs, day and night`} />
          <Stat big={String(t.sessions_scored)} label="sessions scored" note="transcripts graded by the health desk" />
          <Stat big={String(t.refused_calls_total)} label="calls the fence refused" note={`over ${t.nights_with_fence_record} nights with a runner-written fence section`} />
          <Stat big={judgeLine} label="judge grades, report vs diff" note={`${t.judge_rows} rows · A = every claim supported`} />
          <Stat
            big={t.interventions.latest === null ? '–' : String(t.interventions.latest)}
            label="interventions, last night on record"
            note={`mean ${t.interventions.mean ?? '–'} over ${t.interventions.nights} nights · baseline ${t.interventions.baseline_2026_09_18} on 2026-09-18`}
          />
        </div>

        <h2 className="why-part"><span>II</span> Trajectory scorers</h2>
        <p className="why-part-lede">
          Seven deterministic checks the health desk runs over every unattended session’s transcript. The share that scored clean, out of the
          sessions where the check applied.
        </p>
        <table className="ev-table ev-scorers">
          <thead><tr><th>scorer</th><th>means</th><th>clean</th><th>share</th></tr></thead>
          <tbody>
            {SCORERS.map((k) => {
              const c = t.trajectory_clean[k];
              return (
                <tr key={k}>
                  <td><code>{k}</code></td>
                  <td>{SCORER_MEANING[k]}</td>
                  <td>{c.clean} / {c.scored}</td>
                  <td className={c.clean < c.scored ? 'ev-warn' : undefined}>{pct(c.clean, c.scored)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <p className="why-part-lede ev-foot">
          The ones that are not clean are real. {gitBad} sessions ran a git command only the runner may run; most predate the rule
          that promoted it from a prompt line to a scorer. {reportBad} sessions ended without a report, which is the
          failure the rule that every run ends in a report exists to catch. The git scorer also has false positives: on 2026-09-28 and 2026-10-16 it
          flagged a note the agent wrote, <code>git merge-base</code> (a read), and a decision that quoted a command for the human to run.
          The scorer is fixed for future runs; the numbers above stay as recorded.
        </p>

        <h2 className="why-part"><span>III</span> Nights</h2>
        <p className="why-part-lede">
          One row per night, newest first. Status and cost come from the runner’s own record. Refused calls are the
          runner’s count, not the agent’s. Interventions are how many times the morning had to act.
        </p>
        <div className="ev-scroll">
          <table className="ev-table">
            <thead>
              <tr><th>night</th><th>status</th><th>cost</th><th>time</th><th>tool calls</th><th>trajectory</th><th>refused</th><th>judge</th><th>interventions</th></tr>
            </thead>
            <tbody>
              {nights.map((n) => (
                <tr key={n.date}>
                  <td>{n.date}</td>
                  <td className={n.status === 'ok' ? undefined : 'ev-warn'}>{statusWord(n.status)}{n.runs > 1 ? ` ×${n.runs}` : ''}</td>
                  <td>{usd(n.cost_usd)}{n.cost_is_estimate ? '*' : ''}</td>
                  <td>{mins(n.secs)}</td>
                  <td>{n.sessions_scored ? `${n.tool_calls}${n.tool_errors ? ` (${n.tool_errors} err)` : ''}` : <span className="ev-muted">–</span>}</td>
                  <td>{trajCell(n)}</td>
                  <td>{n.refused_calls === null ? <span className="ev-muted">–</span> : n.refused_calls}</td>
                  <td>{n.judge ?? <span className="ev-muted">–</span>}</td>
                  <td>{n.interventions ?? <span className="ev-muted">–</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="why-part-lede ev-foot">
          A dash means the record did not exist yet that night: the fence section was added on 2026-09-22, the
          interventions line the same week, the health desk on 2026-09-04. Older nights have only the ledger.
          On 2026-09-22 itself, the health desk counted 34 refused calls in the night’s transcript while the
          agent’s report said “Blocked by the fence: none.” That gap is why the runner writes the list now.
          {last && last.sessions_scored === 0 ? ' The newest night has not been through the health desk yet.' : ''}
        </p>

        <h2 className="why-part"><span>IV</span> The loops, at the freeze</h2>
        <div className="ev-stats">
          <Stat big={String(t.loops.active ?? 0)} label="loops active" note={Object.entries(t.loops).map(([k, v]) => `${v} ${k}`).join(' · ')} />
          <Stat big={String(t.decisions.open ?? 0)} label="decisions open" note={`${t.decisions.applied ?? 0} applied · ${t.decisions.parked ?? 0} parked`} />
        </div>

        <div className="why-close">
          <p className="section-label">WHERE THIS COMES FROM</p>
          <p className="why-lede">
            <Link href="/harnesses/loops/ops/health/fleet-health.py">fleet-health.py</Link> writes the scores,{' '}
            <Link href="/harnesses/loops/ops/health/judge-night.sh">judge-night.sh</Link> the grades,{' '}
            <Link href="/harnesses/loops/ops/night/run-night.sh">run-night.sh</Link> the ledger and the fence section, and{' '}
            <Link href="/harnesses/self-maintenance">loopctl</Link> the interventions line. The export is one more script
            beside them, and the JSON it writes is{' '}
            <a href={`${GITHUB}/blob/main/evidence/evidence.json`} target="_blank" rel="noreferrer">in the repo</a>.
          </p>
        </div>
      </section>
      <DescentPanel label="EVIDENCE" marks={['I', 'II', 'III', 'IV']} readout={{ kind: 'items', total: nights.length }} />
    </Shell>
  );
}
