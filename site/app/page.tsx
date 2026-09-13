import { Explorer } from '@/components/explorer';
import { DescentPanel } from '@/components/descent-panel';
import { Shell } from '@/components/shell';
import { GITHUB, countAll, getTree } from '@/lib/content';

export default function Home() {
  const tree = getTree();
  const counts = countAll();
  const marks = tree.map((n) => n.name.slice(0, 12));

  return (
    <Shell path="/">
      <section className="tree-panel" aria-labelledby="tree-heading">
        <div className="tree-header">
          <div>
            <p>INDEX OF</p>
            <h1 id="tree-heading">/harnesses</h1>
          </div>
          <div className="tree-header-meta">
            <span>{counts.harnesses} harnesses · {counts.files} files</span>
          </div>
        </div>

        <div className="intro">
          <p>
            The Claude Code harnesses I actually run, scrubbed so you can adopt them: a design interview that ends
            in a clickable prototype, a strategy agent that argues back, an unattended night lane with a budget
            fence and a morning judge, and a TODO list that follows me to my phone. They sit alongside{' '}
            <a href={GITHUB} target="_blank" rel="noreferrer">productagent</a>, four agents for the four questions
            a PM's day runs on.
          </p>
        </div>

        <Explorer tree={tree} trackScroll label="productagent repository" />
      </section>

      <DescentPanel label="INDEX" marks={marks} readout={{ kind: 'percent' }} />
    </Shell>
  );
}
