'use client';

import { useScrollProgress } from './use-scroll-progress';

export function TopbarReadout() {
  const percent = Math.round(useScrollProgress() * 100);
  return (
    <div className="scroll-readout" aria-label={`${percent}% through page`}>
      <span className="status-dot" />
      <span>{String(percent).padStart(3, '0')}%</span>
    </div>
  );
}
