import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { Explorer } from '@/components/explorer';
import { DescentPanel } from '@/components/descent-panel';
import { Shell } from '@/components/shell';
import { getAllSlugs, getHarness, getNode, getTree, readFile } from '@/lib/content';
import { extractHeadings, renderCode, renderMarkdown } from '@/lib/render';

export const dynamicParams = false;

export function generateStaticParams() {
  return getAllSlugs().map((slug) => ({ slug }));
}

type Props = { params: Promise<{ slug: string[] }> };

function firstParagraph(md: string) {
  const body = md
    .split('\n')
    .filter((l) => l.trim() && !l.startsWith('#') && !l.startsWith('```') && !l.startsWith('|') && !l.startsWith('-'))
    .slice(0, 2)
    .join(' ')
    .replace(/[`*_>]/g, '');
  return body.length > 180 ? body.slice(0, 177) + '…' : body;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const node = getNode(slug);
  if (!node) return {};
  const harness = node.kind === 'folder' ? getHarness(slug) : null;
  const description = harness?.summary ?? (node.kind === 'text' ? firstParagraph(readFile(slug).content) : `${node.meta} · ${slug.join('/')}`);
  return { title: slug.join('/'), description };
}

function Crumbs({ slug }: { slug: string[] }) {
  return (
    <nav className="crumbs" aria-label="Breadcrumb">
      <Link href="/">productagent</Link>
      {slug.map((part, i) => {
        const last = i === slug.length - 1;
        const href = '/' + slug.slice(0, i + 1).join('/');
        return (
          <span key={href}>
            <span aria-hidden="true">/ </span>
            {last ? <span aria-current="page">{part}</span> : <Link href={href}>{part}</Link>}
          </span>
        );
      })}
    </nav>
  );
}

export default async function Page({ params }: Props) {
  const { slug } = await params;
  const node = getNode(slug);
  if (!node || node.kind === 'link') notFound();

  const tree = getTree();
  const pathLabel = '/' + slug.join('/');

  if (node.kind === 'folder') {
    const harness = getHarness(slug);
    const entry = harness?.entry ? node.children?.find((c) => c.name === harness.entry) : undefined;
    return (
      <Shell path={pathLabel}>
        <section className="tree-panel" aria-labelledby="doc-heading">
          <Crumbs slug={slug} />
          <div className="doc-header">
            <div>
              <h1 id="doc-heading">{harness?.name ?? node.name}/</h1>
              {harness && <p>{harness.tier} · from {harness.source}</p>}
            </div>
            <div className="doc-actions">
              <a href={node.githubUrl} target="_blank" rel="noreferrer">open on github ↗</a>
              {entry && <Link href={entry.href}>read {entry.name}</Link>}
            </div>
          </div>
          {harness?.summary && <p className="folder-summary">{harness.summary}</p>}
          <div className="folder-index">
            <Explorer tree={node.children ?? []} label={`${node.name} contents`} />
          </div>
          <p className="section-label">FULL INDEX</p>
          <Explorer tree={tree} activeSlug={slug} label="productagent repository" />
        </section>
        <DescentPanel
          label={node.name.toUpperCase().slice(0, 14)}
          marks={(node.children ?? []).slice(0, 5).map((c) => c.name.slice(0, 12))}
          readout={{ kind: 'items', total: node.children?.length ?? 0 }}
        />
      </Shell>
    );
  }

  const file = readFile(slug);
  const isMarkdown = file.lang === 'markdown';
  const html = isMarkdown ? await renderMarkdown(file.content) : await renderCode(file.content, file.lang);
  const headings = isMarkdown ? extractHeadings(file.content) : [];
  const marks = headings.length >= 2 ? headings.map((h) => h.text.slice(0, 12)) : ['0%', '25%', '50%', '75%', '100%'];
  const fm = file.frontmatter as { description?: string; name?: string };

  return (
    <Shell path={pathLabel}>
      <section className="tree-panel" aria-labelledby="doc-heading">
        <Crumbs slug={slug} />
        <div className="doc-header">
          <div>
            <h1 id="doc-heading">{node.name}</h1>
            {fm.description && <p>{fm.description}</p>}
          </div>
          <div className="doc-actions">
            <a href={node.githubUrl} target="_blank" rel="noreferrer">view on github ↗</a>
            <span>{file.lines} lines · {file.lang}</span>
          </div>
        </div>
        {isMarkdown ? (
          <article className="doc" dangerouslySetInnerHTML={{ __html: html }} />
        ) : (
          <div className="code-view" dangerouslySetInnerHTML={{ __html: html }} />
        )}
        <p className="section-label">FULL INDEX</p>
        <Explorer tree={tree} activeSlug={slug} label="productagent repository" />
      </section>
      <DescentPanel label={node.name.toUpperCase().slice(0, 14)} marks={marks} readout={{ kind: 'lines', total: file.lines }} />
    </Shell>
  );
}
