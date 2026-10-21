import fs from 'node:fs';
import path from 'node:path';
import type { Metadata } from 'next';
import Link from 'next/link';
import { DescentPanel } from '@/components/descent-panel';
import { Shell } from '@/components/shell';
import { AUTHOR_GITHUB, AUTHOR_LINKEDIN } from '@/lib/content';
import { renderMarkdown } from '@/lib/render';

const FILE = path.resolve(process.cwd(), '..', 'essays', 'asks.md');

export const metadata: Metadata = {
  title: 'eleven Claude Code asks',
  description:
    'Eleven Claude Code problems from 33 nights of unattended runs, each written as a spec: problem, dated evidence, what to ship, how to measure it, and what to leave out.',
};

const slug = (s: string) => s.toLowerCase().replace(/[^a-z0-9 -]/g, '').trim().replace(/ /g, '-');

export default async function Asks() {
  const md = fs.readFileSync(/*turbopackIgnore: true*/ FILE, 'utf8');
  const title = md.match(/^# (.+)$/m)?.[1] ?? 'Eleven Claude Code asks';
  const body = md.replace(/^# .+\n+/, '');
  const asks = [...body.matchAll(/^## (\d+)\. (.+)$/gm)].map((m) => ({ n: m[1], name: m[2], id: slug(`${m[1]}. ${m[2]}`) }));
  const html = await renderMarkdown(body);

  return (
    <Shell path="/asks">
      <section className="tree-panel" aria-labelledby="asks-heading">
        <nav className="crumbs" aria-label="Breadcrumb"><Link href="/">harnesses</Link><span>/</span><span aria-current="page">asks</span></nav>
        <div className="why-header">
          <p className="hero-eyebrow why-eyebrow">SPECS · FROM <Link href="/33-nights">33 NIGHTS</Link></p>
          <h1 id="asks-heading">{title}</h1>
          <p className="why-rule">Problem · Evidence · Ship · Measure · Not doing. Ranked by what each would have saved me.</p>
        </div>
        <nav className="asks-index" aria-label="The eleven asks">
          <ol>
            {asks.map((a) => <li key={a.id}><a href={`#${a.id}`}>{a.name}</a></li>)}
          </ol>
        </nav>
        <article className="doc essay asks" dangerouslySetInnerHTML={{ __html: html }} />
        <aside className="author author-wide">
          <p>
            <b>Harrison Johnson</b> is a product manager in New York who runs his own projects with Claude Code day and
            night. Read the <Link href="/33-nights">essay</Link> these came from, or check <Link href="/evidence">the receipts</Link>.
          </p>
          <p className="author-links">
            <a href={AUTHOR_LINKEDIN} target="_blank" rel="noreferrer">LinkedIn ↗</a>
            <a href={AUTHOR_GITHUB} target="_blank" rel="noreferrer">GitHub ↗</a>
          </p>
        </aside>
      </section>
      <DescentPanel label="ASKS" marks={['1', '4', '8', '11']} readout={{ kind: 'items', total: asks.length }} />
    </Shell>
  );
}
