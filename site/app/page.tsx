import { Explorer } from '@/components/explorer';
import { DescentPanel } from '@/components/descent-panel';
import { Shell } from '@/components/shell';
import { GITHUB, countAll, getTree } from '@/lib/content';

export default function Home() {
  const tree = getTree();
  const counts = countAll();
  const marks = tree.map((n) => n.name.replace(/\.md$/, '').slice(0, 10));

  return (
    <Shell path="/">
      <section className="tree-panel" aria-labelledby="tree-heading">
        <div className="tree-header">
          <div>
            <p>INDEX OF</p>
            <h1 id="tree-heading">/productagent</h1>
          </div>
          <div className="tree-header-meta">
            <span>{counts.harnesses} harnesses · {counts.files} files</span>
            <span>click a name to open · chevron to collapse</span>
          </div>
        </div>

        <div className="intro">
          <p>
            An AI operating system for product managers, and the harnesses around it. Four agents answer the four
            questions a PM's day runs on (who owns this, what's the status, where's the data, when is it due).
            The <code>harnesses/</code> folder holds the Claude Code skills, agents, fences, and bots I actually run:
            a design interview that ends in a clickable prototype, an unattended night lane with a budget fence and
            a morning judge, and a Telegram bridge so the terminal follows me to my phone.
          </p>
          <p>
            Browse here, or go straight to <a href={GITHUB} target="_blank" rel="noreferrer">the git</a>. Every
            file page has a link to the same path on GitHub. Built by Harrison Johnson with Claude; the judgment is
            mine, the legwork was the agents'.
          </p>
        </div>

        <Explorer tree={tree} trackScroll label="productagent repository" />
      </section>

      <DescentPanel label="INDEX" marks={marks} readout={{ kind: 'percent' }} />
    </Shell>
  );
}
