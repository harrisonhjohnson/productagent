'use client';

import { useState, type ReactNode } from 'react';

export function FigureToggle({ labels, broke, fixed }: { labels: [string, string]; broke: ReactNode; fixed: ReactNode }) {
  const [view, setView] = useState<'b' | 'f'>('b');
  return (
    <>
      <div className="fig-seg" role="group" aria-label="Diagram state">
        {(['b', 'f'] as const).map((v, i) => (
          <button key={v} type="button" aria-pressed={view === v} onClick={() => setView(v)}>
            {labels[i]}
          </button>
        ))}
      </div>
      <div hidden={view !== 'b'}>{broke}</div>
      <div hidden={view !== 'f'}>{fixed}</div>
    </>
  );
}
