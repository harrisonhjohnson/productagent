import Link from 'next/link';
import { Explorer } from '@/components/explorer';
import { DescentPanel } from '@/components/descent-panel';
import { Shell } from '@/components/shell';
import { GITHUB, countAll, getTree } from '@/lib/content';

type Job = {
  n: string;
  job: string;
  how: string;
  links: { label: string; href: string; external?: boolean }[];
};

const JOBS: Job[] = [
  {
    n: '01',
    job: 'Keep one TODO list that follows you from the terminal to your phone.',
    how: 'One markdown file. A Claude Code skill and a Telegram bot both read and write it, so capture, triage, and "what\'s due" work from wherever you are. Hand an item to an agent that asks before it acts.',
    links: [
      { label: 'read the guide', href: '/harnesses/todo/README.md' },
      { label: 'the skill', href: '/harnesses/todo/skill/SKILL.md' },
      { label: 'the bot', href: '/harnesses/todo/bot/BOT.md' },
    ],
  },
  {
    n: '02',
    job: 'Turn a conversation about a flow into a clickable prototype.',
    how: 'A screen-by-screen interview: one question at a time, ending in an HTML prototype of the journey. Then let a swarm fill in every screen the prototype links to but doesn\'t have yet.',
    links: [
      { label: 'flow-design', href: '/harnesses/flow-design/SKILL.md' },
      { label: 'prototype-swarm', href: '/harnesses/prototype-swarm/SKILL.md' },
    ],
  },
  {
    n: '03',
    job: 'Pressure-test a strategy before you present it.',
    how: 'An advisor agent with three lenses: build taste and latent demand, business structure and moats, and PM execution. It argues back instead of cheering.',
    links: [{ label: 'pm-strategist', href: '/harnesses/pm-strategist/pm-strategist.md' }],
  },
  {
    n: '04',
    job: 'Let an agent work overnight without letting it spend, push, or wander.',
    how: 'A permissions fence, a charter with budget dials, self-renewing standing orders, and a morning judge that grades the night against the diff rather than the report.',
    links: [
      { label: 'read the guide', href: '/harnesses/night-orders/README.md' },
      { label: 'the fence', href: '/harnesses/night-orders/settings.json' },
      { label: 'the runner', href: '/harnesses/night-orders/ops/night/run-night.sh' },
    ],
  },
  {
    n: '05',
    job: 'Turn a list of companies into the people you should talk to.',
    how: 'Point the AI subscriptions you already pay for at a CSV of target accounts. Open source, MIT.',
    links: [{ label: 'rev-intel-harness', href: 'https://github.com/harrisonhjohnson/rev-intel-harness', external: true }],
  },
];

export default function Home() {
  const tree = getTree();
  const counts = countAll();
  const marks = JOBS.map((j) => j.n);

  return (
    <Shell path="/">
      <section className="tree-panel" aria-labelledby="page-heading">
        <div className="tree-header">
          <div>
            <p>PRODUCTAGENT</p>
            <h1 id="page-heading">What do you need to get done?</h1>
          </div>
          <div className="tree-header-meta">
            <span>{JOBS.length} jobs · {counts.harnesses} harnesses</span>
          </div>
        </div>

        <div className="intro">
          <p>
            Working tools for product managers who run their day with Claude Code, published as the folders they
            actually are. Each job below is answered by a harness: a skill, an agent, a fence, or a bot you can copy
            into your own setup. They sit alongside{' '}
            <a href={GITHUB} target="_blank" rel="noreferrer">productagent</a>, four agents for the four questions
            a PM's day runs on.
          </p>
        </div>

        <ol className="jobs" aria-label="Jobs to be done">
          {JOBS.map((j) => (
            <li className="job" key={j.n} id={`job-${j.n}`}>
              <span className="job-n" aria-hidden="true">{j.n}</span>
              <div>
                <h2>{j.job}</h2>
                <p>{j.how}</p>
                <div className="job-links">
                  {j.links.map((l) =>
                    l.external ? (
                      <a key={l.href} href={l.href} target="_blank" rel="noreferrer">{l.label} ↗</a>
                    ) : (
                      <Link key={l.href} href={l.href}>{l.label}</Link>
                    ),
                  )}
                </div>
              </div>
            </li>
          ))}
        </ol>

        <p className="section-label">OR BROWSE THE FOLDERS</p>
        <Explorer tree={tree} label="harnesses" />
      </section>

      <DescentPanel label="JOB" marks={marks} readout={{ kind: 'items', total: JOBS.length }} />
    </Shell>
  );
}
