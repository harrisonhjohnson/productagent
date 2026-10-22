import type { Metadata } from 'next';
import Link from 'next/link';
import { DescentPanel } from '@/components/descent-panel';
import { InstallLine } from '@/components/install-line';
import { INSTALL_COMMAND } from '@/lib/install';
import { Shell } from '@/components/shell';
import { AUTHOR_GITHUB, AUTHOR_LINKEDIN, GITHUB, getTree } from '@/lib/content';

const SITE = 'https://productagent.dev';

const TITLE = 'About productagent.dev: free Claude Code harnesses for product managers';
const DESCRIPTION =
  'productagent.dev is a free, public library of Claude Code harnesses for product managers: skills, agents, scripts and a Telegram bot. The flagship, Loops, runs an agent overnight on your Mac under a budget and a fence, and leaves four plain lines per loop in the morning.';

export const metadata: Metadata = {
  title: { absolute: TITLE },
  description: DESCRIPTION,
  alternates: { canonical: '/about' },
  openGraph: { title: TITLE, description: DESCRIPTION, url: '/about', type: 'website', siteName: 'productagent', images: ['/opengraph-image'] },
  twitter: { card: 'summary_large_image', title: TITLE, description: DESCRIPTION, images: ['/twitter-image'] },
};

const FAQ: { q: string; a: string }[] = [
  {
    q: 'What is a Claude Code harness?',
    a: 'A harness is anything written down that tells Claude Code how to do a repeated job: a skill (a SKILL.md folder), an agent definition, a slash command, a permissions fence, a set of shell scripts on a schedule, or a whole bot. productagent.dev publishes the harnesses one product manager runs every day, as the folders they are.',
  },
  {
    q: 'Is productagent.dev free?',
    a: 'Yes. Every harness is a public folder on GitHub. Loops runs on the Claude or ChatGPT plan you already pay for. productagent.dev sells nothing and has no paid tier.',
  },
  {
    q: 'How do I install a harness?',
    a: `Loops installs with one line in the macOS Terminal: ${INSTALL_COMMAND}. For a single skill or agent, copy its folder into ~/.claude/skills (skills) or its file into ~/.claude/agents (agents), then restart Claude Code.`,
  },
  {
    q: 'What is Loops?',
    a: 'Loops lets an agent keep working on a goal while you sleep. You set four knobs per loop: a goal, a budget, a cadence and a model. Each night the runner does one bounded run per loop inside a fence, then writes four lines per loop: what it was trying to do, what it did, what it decided, and what it needs from you.',
  },
  {
    q: 'Is it safe to let an agent run unattended?',
    a: 'Loops is built around that question. Each run has a dollar budget and a timeout. A fence of Claude Code permissions allows a short list of actions and blocks git push, rm, shells and edits to the loops file, and the OS sandbox underneath stops what text rules miss, such as a one-line python3 -c. The runner keeps its own list of every blocked call and prints the list under the morning report, so the agent cannot hide what it tried. Nothing runs until you write a loop, and running the installer again with --off stops the schedule.',
  },
  {
    q: 'Does it work with Codex or ChatGPT?',
    a: 'Loops runs Claude Code or Codex on your own Mac, on your own subscription. The skills and agents target Claude Code.',
  },
  {
    q: 'Does anything leave my machine?',
    a: 'No. Loops runs locally, writes its reports to local files and sends no telemetry.',
  },
];

function jsonLd(value: unknown) {
  return JSON.stringify(value).replace(/</g, '\\u003c');
}

export default function About() {
  const harnesses = getTree().filter((n) => n.kind === 'folder' || n.kind === 'link');
  const count = harnesses.length;
  const abs = (href: string) => (href.startsWith('http') ? href : SITE + href);

  const graph = {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'WebSite',
        '@id': `${SITE}/#website`,
        url: SITE,
        name: 'productagent',
        description: DESCRIPTION,
        publisher: { '@id': `${SITE}/#person` },
      },
      {
        '@type': 'Person',
        '@id': `${SITE}/#person`,
        name: 'Harrison Johnson',
        jobTitle: 'Product manager',
        url: `${SITE}/about`,
        sameAs: [AUTHOR_GITHUB, AUTHOR_LINKEDIN],
      },
      {
        '@type': 'AboutPage',
        '@id': `${SITE}/about#page`,
        url: `${SITE}/about`,
        name: TITLE,
        description: DESCRIPTION,
        isPartOf: { '@id': `${SITE}/#website` },
        about: { '@id': `${SITE}/#loops` },
        author: { '@id': `${SITE}/#person` },
        mainEntity: { '@id': `${SITE}/about#harnesses` },
      },
      {
        '@type': 'SoftwareApplication',
        '@id': `${SITE}/#loops`,
        name: 'Loops',
        url: `${SITE}/harnesses/loops`,
        applicationCategory: 'DeveloperApplication',
        operatingSystem: 'macOS',
        description: harnesses.find((n) => n.name === 'loops')?.summary,
        installUrl: `${SITE}/install.sh`,
        codeRepository: `${GITHUB}/tree/main/harnesses/loops`,
        isAccessibleForFree: true,
        author: { '@id': `${SITE}/#person` },
      },
      {
        '@type': 'ItemList',
        '@id': `${SITE}/about#harnesses`,
        name: 'productagent harnesses',
        numberOfItems: count,
        itemListElement: harnesses.map((n, i) => ({
          '@type': 'ListItem',
          position: i + 1,
          item: {
            '@type': 'SoftwareSourceCode',
            name: n.name,
            description: n.summary,
            url: abs(n.href),
            codeRepository: n.githubUrl,
          },
        })),
      },
      {
        '@type': 'FAQPage',
        '@id': `${SITE}/about#faq`,
        mainEntity: FAQ.map((f) => ({
          '@type': 'Question',
          name: f.q,
          acceptedAnswer: { '@type': 'Answer', text: f.a },
        })),
      },
    ],
  };

  return (
    <Shell path="/about">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLd(graph) }} />
      <section className="tree-panel read" aria-labelledby="about-heading">
        <nav className="crumbs" aria-label="Breadcrumb"><Link href="/">harnesses</Link><span>/</span><span aria-current="page">about</span></nav>
        <div className="why-header">
          <p className="hero-eyebrow why-eyebrow">ABOUT PRODUCTAGENT.DEV</p>
          <h1 id="about-heading">Claude Code harnesses for product managers, free to read and run on your own Mac.</h1>
          <p className="why-lede">
            productagent.dev is a free, public library of {count} Claude Code harnesses for product managers and
            operators: skills, agents, shell scripts on a schedule, a permissions fence and a Telegram bot. The
            flagship, Loops, lets Claude keep working overnight and hands the decisions back to you in the morning. You give each loop a goal, a budget, a cadence
            and a model. Loops runs on your Mac and the Claude or ChatGPT plan you already pay for, works inside a fence
            (permission rules with the OS sandbox underneath), and leaves four plain lines per loop in the morning.
          </p>
          <pre className="about-install"><code>{INSTALL_COMMAND}</code></pre>
        </div>

        <article className="doc">
          <h2 id="author">Who made this</h2>
          <p>
            Harrison Johnson, a product manager in New York. He has spent a decade building marketplaces and B2B
            software, as employee number one, as a co-founder, and as a product lead. He built productagent.dev with
            Claude Code and runs Loops on his own projects every night. Three pages come out of that work:
          </p>
          <ul>
            <li><Link href="/33-nights"><b>33 nights of unattended Claude Code</b></Link>: ten things that broke, what each taught, and why the morning review is the product.</li>
            <li><Link href="/asks"><b>Eleven Claude Code asks</b></Link>: every problem from those nights, written as a spec with evidence, a way to measure it, and what to leave out.</li>
            <li><Link href="/evidence"><b>The receipts</b></Link>: the run record behind both, numbers only.</li>
          </ul>
          <p>
            <a href={AUTHOR_LINKEDIN} target="_blank" rel="noreferrer">LinkedIn ↗</a>
            {' · '}
            <a href={AUTHOR_GITHUB} target="_blank" rel="noreferrer">GitHub ↗</a>
          </p>

          <h2 id="who">Who productagent.dev is for</h2>
          <ul>
            <li>Product managers who already run part of the day in Claude Code or Codex.</li>
            <li>Founders and operators with more projects than evenings.</li>
            <li>Anyone who wants an agent to keep working overnight without handing it the keys.</li>
          </ul>

          <h2 id="harnesses">What you get: {count} harnesses</h2>
          <p>Each harness is a folder you can read before you run it. Open one to see every file.</p>
          <ul>
            {harnesses.map((n) => (
              <li key={n.href}>
                {n.kind === 'link' ? (
                  <a href={n.href} target="_blank" rel="noreferrer"><b>{n.name}</b> ↗</a>
                ) : (
                  <Link href={n.href}><b>{n.name}</b></Link>
                )}
                {' '}({n.tier}): {n.summary}
              </li>
            ))}
          </ul>

          <h2 id="morning">What Loops leaves you in the morning</h2>
          <pre><code>{`## L-03 · Ship one fix
- Trying to: ship the "sort permits by county" backlog item.
- Did: added the county filter; the page renders in a headless browser.
- Decided: left the mobile layout alone; separate backlog item.
- Need from you: merge branch night/2026-09-14 if the screenshot looks right.`}</code></pre>
          <p>
            Four words run the whole system. A <b>Loop</b> is work with a goal that renews itself. A <b>Run</b> is one
            bounded pass at a loop. An <b>Order</b> is a one-off instruction for tonight. A <b>Decision</b> is anything a
            run could not settle; the run hands the decision back to you instead of guessing. Read the full concept
            page at <Link href="/harnesses/loops/README.md">harnesses/loops/README.md</Link>, and the runner and fence
            at <Link href="/harnesses/loops/MACHINE.md">MACHINE.md</Link>.
          </p>
        </article>

        <div id="install"><InstallLine /></div>
        <article className="doc">
          <p>
            Want one skill, not the whole machine? Copy a skill folder (for example{' '}
            <Link href="/harnesses/flow-design">flow-design</Link>) into <code>~/.claude/skills/</code>, or an agent
            file (for example <Link href="/harnesses/pm-strategist">pm-strategist</Link>) into{' '}
            <code>~/.claude/agents/</code>. Restart Claude Code and the skill or agent shows up.
          </p>

          <h2 id="made">How productagent.dev is made</h2>
          <p>
            Harrison Johnson, a product manager, runs these harnesses on real projects every day and night. Each
            harness gets copied off Harrison&apos;s machine, scrubbed of personal paths, budgets and client names, and
            published here as a folder. Claude Code wrote most of the code and much of the prose; Harrison makes the calls on what
            ships and what the rules are. Every example on the site is synthetic. The one exception is{' '}
            <Link href="/evidence">the receipts</Link>: the real run record, numbers only, frozen at a cutoff date. <Link href="/33-nights">The essay</Link> walks through what those nights taught.
          </p>
          <p>
            The site reads the <a href={GITHUB} target="_blank" rel="noreferrer">GitHub repository</a> at build time, so
            productagent.dev and the repo always match. Want the case for loops in the words of the people building
            Claude Code? Read <Link href="/why">why</Link>.
          </p>

          <h2 id="faq">Questions people ask</h2>
          {FAQ.map((f) => (
            <section key={f.q}>
              <h3>{f.q}</h3>
              <p>{f.a}</p>
            </section>
          ))}

          <h2 id="follow">Follow along</h2>
          <ul>
            <li><a href={GITHUB} target="_blank" rel="noreferrer">Star harrisonhjohnson/productagent on GitHub</a> to get new harnesses as they ship.</li>
            <li><a href={AUTHOR_GITHUB} target="_blank" rel="noreferrer">Follow Harrison on GitHub</a>.</li>
            <li><a href={AUTHOR_LINKEDIN} target="_blank" rel="noreferrer">Connect with Harrison on LinkedIn</a>.</li>
            <li>Found a bug or want a harness? <a href={`${GITHUB}/issues`} target="_blank" rel="noreferrer">Open an issue</a>.</li>
            <li>Agents and crawlers: read <a href="/llms.txt">/llms.txt</a> for a plain-text map of the site.</li>
          </ul>
        </article>
      </section>
      <DescentPanel label="ABOUT" marks={['AUTHOR', 'WHAT', 'INSTALL', 'FAQ']} readout={{ kind: 'items', total: count }} />
    </Shell>
  );
}
