import Image from 'next/image';
import Link from 'next/link';
import { Explorer } from '@/components/explorer';
import { DescentPanel } from '@/components/descent-panel';
import { LoopUseCases } from '@/components/loop-usecases';
import { InstallLine } from '@/components/install-line';
import { Onboarding } from '@/components/onboarding';
import { InTheirWords } from '@/components/in-their-words';
import { Agents } from '@/components/agents';
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
    job: 'Give an agent a goal and let it work overnight without letting it spend, push, or wander.',
    how: 'A loop is work with a goal that renews itself. You set four knobs: goal, budget, cadence, model. It runs one bounded pass at a time inside a permissions fence, and every morning you read four plain sentences per loop: what it was trying to do, what it did, what it decided, what it needs from you.',
    links: [
      { label: 'what a loop is', href: '/harnesses/loops/README.md' },
      { label: 'the machine', href: '/harnesses/loops/MACHINE.md' },
      { label: 'the fence', href: '/harnesses/loops/settings.json' },
    ],
  },
  {
    n: '02',
    job: 'Run it from your phone.',
    how: 'One markdown TODO list shared between the terminal and a Telegram bot. The same bot lists your loops, changes a budget or a model with one message, pauses a loop, and reads back this morning\'s four lines.',
    links: [
      { label: 'read the guide', href: '/harnesses/todo/README.md' },
      { label: 'the bot', href: '/harnesses/todo/bot/BOT.md' },
    ],
  },
  {
    n: '03',
    job: 'Turn a conversation about a flow into a clickable prototype.',
    how: 'A screen-by-screen interview: one question at a time, ending in an HTML prototype of the journey. Then let a swarm fill in every screen the prototype links to but doesn\'t have yet.',
    links: [
      { label: 'flow-design', href: '/harnesses/flow-design/SKILL.md' },
      { label: 'prototype-swarm', href: '/harnesses/prototype-swarm/SKILL.md' },
    ],
  },
  {
    n: '04',
    job: 'Pressure-test a strategy before you present it.',
    how: 'An advisor agent with three lenses: build taste and latent demand, business structure and moats, and PM execution. It argues back instead of cheering.',
    links: [{ label: 'pm-strategist', href: '/harnesses/pm-strategist/pm-strategist.md' }],
  },
  {
    n: '05',
    job: 'Keep a month of agent reports searchable.',
    how: 'A personal knowledge graph. Every report the loops write becomes a seed; the graph finds the relationships, so last month\'s mistake is one query away. Open source, MIT.',
    links: [{ label: 'karma', href: 'https://github.com/harrisonhjohnson/karma', external: true }],
  },
  {
    n: '06',
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
        <div className="hero">
          <Image src="/loops-retro.png" alt="" fill priority sizes="(max-width: 780px) 100vw, 78vw" className="hero-img" />
          <div className="hero-copy">
            <p className="hero-eyebrow">PRODUCTAGENT</p>
            <h1 id="page-heading">Let an agent run a loop<br />while you sleep.</h1>
            <p className="hero-meta">claude code · codex · your mac · your plan · {counts.harnesses} harnesses</p>
          </div>
        </div>

        <InstallLine />
        <InTheirWords />
        <Onboarding />

        <div className="intro">
          <p>
            Working tools for product managers who run their day with Claude Code, published as the folders they
            actually are. Four words carry the system: a <strong>Loop</strong> is work with a goal that renews
            itself; a <strong>Run</strong> is one bounded pass at it; an <strong>Order</strong> is a one-off
            instruction for tonight; a <strong>Decision</strong> is anything the run could not settle and hands
            back to you. Everything below is a folder you can copy into your own setup. Nothing is hosted, and
            nothing phones home.
          </p>
        </div>

        <LoopUseCases />

        <Agents />

        <p className="section-label">SIX JOBS IT DOES</p>
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
