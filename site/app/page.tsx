import Image from 'next/image';
import { Explorer } from '@/components/explorer';
import { DescentPanel } from '@/components/descent-panel';
import { InstallLine } from '@/components/install-line';
import { Onboarding } from '@/components/onboarding';
import { StickyNotes } from '@/components/loop-usecases';
import { Morning } from '@/components/morning';
import { Shell } from '@/components/shell';
import { countAll, getTree } from '@/lib/content';
import Link from 'next/link';
import './geo.css';

export default function Home() {
  const tree = getTree();
  const counts = countAll();
  const marks = ['I', 'II', 'III'];

  return (
    <Shell path="/">
      <section className="tree-panel" aria-labelledby="page-heading">
        <a className="to-1999" href="/1999">✦ 1999 mode ✦</a>
        <div className="hero">
          <Image src="/loops-retro.png" alt="" fill priority sizes="(max-width: 780px) 100vw, 94vw" className="hero-img" />
          <div className="hero-copy">
            <p className="hero-eyebrow">PRODUCTAGENT</p>
            <h1 id="page-heading">Let an agent run a loop<br />while you sleep.</h1>
            <p className="hero-meta">claude code · codex · your mac · your plan · {counts.harnesses} harnesses</p>
          </div>
        </div>

        <p className="byline">
          Built and run by Harrison Johnson, a product manager, with Claude Code: 33 nights of unattended runs, every
          one on the record. <Link href="/evidence">Read the receipts →</Link>
        </p>

        <InstallLine />
        <Onboarding />

        <section className="usecases" aria-labelledby="usecases-heading">
          <p className="section-label" id="usecases-heading">WHAT A LOOP LOOKS LIKE</p>
          <StickyNotes />
        </section>

        <Morning />

        <p className="section-label">OR BROWSE THE FOLDERS</p>
        <Explorer tree={tree} label="harnesses" />
      </section>

      <DescentPanel label="HOME" marks={marks} readout={{ kind: 'items', total: 3 }} />
    </Shell>
  );
}
