'use client';

import Image from 'next/image';
import { useScrollProgress } from './use-scroll-progress';

export type Readout =
  | { kind: 'percent' }
  | { kind: 'lines'; total: number }
  | { kind: 'items'; total: number };

type Props = {
  label: string;
  marks: string[];
  readout: Readout;
};

export function DescentPanel({ label, marks, readout }: Props) {
  const progress = useScrollProgress();
  const percent = Math.round(progress * 100);

  let value: string;
  if (readout.kind === 'lines') {
    value = `LINE ${String(Math.max(1, Math.round(progress * readout.total))).padStart(3, '0')} / ${readout.total}`;
  } else if (readout.kind === 'items') {
    value = `${String(Math.max(1, Math.round(progress * readout.total))).padStart(2, '0')} / ${readout.total}`;
  } else {
    value = `${String(percent).padStart(3, '0')}%`;
  }

  return (
    <aside className="descent-panel" aria-label="Scroll-controlled rappelling illustration">
      <div className="panel-grid" aria-hidden="true" />
      <div className="panel-heading">
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
      <div className="anchor" aria-hidden="true"><span /><span /><span /></div>
      <div className="rope" aria-hidden="true" />
      <div className="depth-scale" aria-hidden="true">
        {marks.map((mark, i) => <span key={`${i}-${mark}`}>{mark}</span>)}
      </div>
      <div className="rappeller" style={{ '--descent': progress } as React.CSSProperties} aria-hidden="true">
        <Image
          src="/rappeller-sketch.png"
          alt=""
          width={512}
          height={768}
          priority
          sizes="(max-width: 640px) 84px, 126px"
        />
      </div>
      <p className="descent-note">scroll depth / rope position</p>
    </aside>
  );
}
