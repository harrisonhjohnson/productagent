import type { Metadata } from 'next';
import Link from 'next/link';
import { DescentPanel } from '@/components/descent-panel';
import { QuoteCard } from '@/components/in-their-words';
import { InstallLine } from '@/components/install-line';
import { Shell } from '@/components/shell';
import { QUOTES } from '@/lib/quotes';

export const metadata: Metadata = {
  title: 'why',
  description:
    'The case for loops and graphs, in Anthropic’s own words. Verbatim, sourced and dated quotes from the people building Claude Code, and what each one turned into in the loops folder.',
};

export default function Why() {
  const loops = QUOTES.filter((q) => q.part === 'loops');
  const graphs = QUOTES.filter((q) => q.part === 'graphs');
  return (
    <Shell path="/why">
      <section className="tree-panel" aria-labelledby="why-heading">
        <nav className="crumbs" aria-label="Breadcrumb"><Link href="/">harnesses</Link><span>/</span><span>why</span></nav>
        <div className="why-header">
          <p className="hero-eyebrow why-eyebrow">WHY LOOPS, WHY GRAPHS</p>
          <h1 id="why-heading">In their own words.</h1>
          <p className="why-lede">
            I did not start running agents overnight because of a benchmark. I started because the people building
            Claude Code kept saying the same two things in public: the next step is loops, and long-running work
            needs memory outside the context window. This page is those quotes, verbatim and linked, with one line
            each on what it became in the folder. If a quote is wrong, the source is one click away.
          </p>
          <p className="why-rule">Rule: nothing paraphrased, nothing undated, nothing without a link. Updated by hand.</p>
        </div>

        <h2 className="why-part"><span>I</span> Loops</h2>
        <p className="why-part-lede">
          The work is a loop, the loop has stopping conditions, and the person&apos;s job moves from prompting to
          writing loops.
        </p>
        <div className="quote-list">{loops.map((q) => <QuoteCard key={q.id} q={q} />)}</div>

        <h2 className="why-part"><span>II</span> Graphs</h2>
        <p className="why-part-lede">
          Every session forgets. Notes persisted outside the context window are how work survives, and a pile of
          notes only answers questions when the facts are connected.
        </p>
        <div className="quote-list">{graphs.map((q) => <QuoteCard key={q.id} q={q} />)}</div>

        <div className="why-close">
          <p className="section-label">THE FOLDER THOSE QUOTES BECAME</p>
          <InstallLine />
        </div>
      </section>
      <DescentPanel label="WHY" marks={['I', 'II']} readout={{ kind: 'items', total: QUOTES.length }} />
    </Shell>
  );
}
