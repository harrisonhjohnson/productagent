import fs from 'node:fs';
import path from 'node:path';
import type { Metadata } from 'next';
import Link from 'next/link';
import { DescentPanel } from '@/components/descent-panel';
import { Shell } from '@/components/shell';
import { extractHeadings, renderMarkdown } from '@/lib/render';

const FILE = path.resolve(process.cwd(), '..', 'essays', '33-nights.md');

export const metadata: Metadata = {
  title: '33 nights',
  description:
    '33 nights of unattended Claude Code at $6.13 a night: ten things that broke, what each taught me about running an agent overnight, and every Claude Code problem I hit with what I would ship as its PM.',
};

export default async function Essay() {
  const md = fs.readFileSync(/*turbopackIgnore: true*/ FILE, 'utf8');
  const title = md.match(/^# (.+)$/m)?.[1] ?? '33 nights';
  const body = md.replace(/^# .+\n+/, '');
  const html = await renderMarkdown(body);
  const marks = extractHeadings(body, 3).map((h) => h.text.slice(0, 12));
  const words = body.split(/\s+/).filter(Boolean).length;

  return (
    <Shell path="/33-nights">
      <section className="tree-panel" aria-labelledby="essay-heading">
        <nav className="crumbs" aria-label="Breadcrumb"><Link href="/">harnesses</Link><span>/</span><span aria-current="page">33 nights</span></nav>
        <div className="why-header">
          <p className="hero-eyebrow why-eyebrow">ESSAY · {Math.round(words / 230)} MIN READ</p>
          <h1 id="essay-heading">{title}</h1>
          <p className="why-rule">
            Every number comes from the run record, frozen at October 16. <Link href="/evidence">Check the receipts →</Link>
          </p>
        </div>
        <article className="doc essay" dangerouslySetInnerHTML={{ __html: html }} />
      </section>
      <DescentPanel label="33 NIGHTS" marks={marks} readout={{ kind: 'items', total: marks.length }} />
    </Shell>
  );
}
