import Image from 'next/image';
import { Explorer } from '@/components/explorer';
import { DescentPanel } from '@/components/descent-panel';
import { InstallLine } from '@/components/install-line';
import { Stations } from '@/components/stations';
import { Onboarding } from '@/components/onboarding';
import { Where } from '@/components/where';
import { Closing } from '@/components/closing';
import { Lid } from '@/components/lid';
import { Shell } from '@/components/shell';
import { GITHUB, countAll, getTree } from '@/lib/content';

export default function Home() {
  const tree = getTree();
  const counts = countAll();
  const marks = ['1', '2', '3', '4'];

  return (
    <Shell path="/">
      <section className="tree-panel" aria-labelledby="page-heading">
        <div className="hero">
          <Image src="/nighttime.png" alt="" fill priority sizes="(max-width: 780px) 100vw, 94vw" className="hero-img" />
          <Lid hero />
          <div className="hero-copy">
            <p className="hero-eyebrow">PRODUCTAGENT</p>
            <h1 id="page-heading">Let an agent run a loop<br />while you sleep.</h1>
            <p className="hero-meta">claude code · codex · your mac · your plan · {counts.harnesses} harnesses</p>
          </div>
        </div>

        <InstallLine />
        <Onboarding />

        <Stations />

        <Where />

        <Closing />

        <p className="section-label">OR BROWSE THE FOLDERS</p>
        <Explorer tree={tree} label="harnesses" />
      </section>

      <DescentPanel label="STATION" marks={marks} readout={{ kind: 'items', total: 4 }} />
    </Shell>
  );
}
