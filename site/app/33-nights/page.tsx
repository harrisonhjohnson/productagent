import fs from 'node:fs';
import path from 'node:path';
import type { Metadata } from 'next';
import Link from 'next/link';
import { DescentPanel } from '@/components/descent-panel';
import { EssayChart } from '@/components/essay-charts';
import { Shell } from '@/components/shell';
import { AUTHOR_GITHUB, AUTHOR_LINKEDIN } from '@/lib/content';
import { getEvidence } from '@/lib/evidence';
import { extractHeadings, renderMarkdown } from '@/lib/render';

const FILE = path.resolve(process.cwd(), '..', 'essays', '33-nights.md');
const CHART = /^<!-- chart:(\w+) -->$/m;

export const metadata: Metadata = {
  title: '33 nights',
  description:
    '33 nights of unattended Claude Code at $6.13 a night: ten things that broke, what each taught me about running an agent overnight, and every Claude Code problem I hit with what I would ship as its PM.',
};

export default async function Essay() {
  const md = fs.readFileSync(/*turbopackIgnore: true*/ FILE, 'utf8');
  const title = md.match(/^# (.+)$/m)?.[1] ?? '33 nights';
  const body = md.replace(/^# .+\n+/, '');
  const ev = getEvidence();
  const parts = body.split(CHART);
  const html = await Promise.all(parts.map((p, i) => (i % 2 ? Promise.resolve(p) : renderMarkdown(p))));
  const marks = extractHeadings(body, 3).map((h) => h.text.slice(0, 12));
  const words = body.replace(new RegExp(CHART.source, 'gm'), '').split(/\s+/).filter(Boolean).length;

  return (
    <Shell path="/33-nights">
      <section className="tree-panel read" aria-labelledby="essay-heading">
        <nav className="crumbs" aria-label="Breadcrumb"><Link href="/">harnesses</Link><span>/</span><span aria-current="page">33 nights</span></nav>
        <div className="why-header">
          <p className="hero-eyebrow why-eyebrow">ESSAY · {Math.round(words / 230)} MIN READ</p>
          <h1 id="essay-heading">{title}</h1>
          <p className="why-rule">
            Every number comes from the run record, frozen at October 16. <Link href="/evidence">Check the receipts →</Link>
          </p>
        </div>
        <article className="doc essay">
          {html.map((h, i) =>
            i % 2 ? (ev ? <EssayChart key={i} name={h} ev={ev} /> : null) : <div key={i} dangerouslySetInnerHTML={{ __html: h }} />,
          )}
          <aside className="author">
            <p>
              <b>Harrison Johnson</b> is a product manager in New York. He has spent a decade building marketplaces and
              B2B software, as employee number one, as a co-founder, and as a product lead, and now runs his own projects
              with Claude Code day and night. The machine behind this essay is open source:{' '}
              <Link href="/harnesses/loops">Loops</Link>.
            </p>
            <p className="author-links">
              <a href={AUTHOR_LINKEDIN} target="_blank" rel="noreferrer">LinkedIn ↗</a>
              <a href={AUTHOR_GITHUB} target="_blank" rel="noreferrer">GitHub ↗</a>
              <Link href="/evidence">The receipts →</Link>
            </p>
          </aside>
        </article>
      </section>
      <DescentPanel label="33 NIGHTS" marks={marks} readout={{ kind: 'items', total: marks.length }} />
    </Shell>
  );
}
