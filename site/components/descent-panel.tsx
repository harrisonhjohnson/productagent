'use client';

import Image from 'next/image';
import { useCallback, useRef, useState } from 'react';
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

// The rappeller starts 30px below the panel top and travels (panel height - 209px); see .rappeller in globals.css.
const TRACK_TOP = 30;
const TRACK_INSET = 209;

export function DescentPanel({ label, marks, readout }: Props) {
  const progress = useScrollProgress();
  const percent = Math.round(progress * 100);
  const panelRef = useRef<HTMLElement>(null);
  const [dragging, setDragging] = useState(false);

  const scrollToPointer = useCallback((clientY: number) => {
    const el = panelRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const travel = Math.max(1, rect.height - TRACK_INSET);
    const p = Math.min(1, Math.max(0, (clientY - rect.top - TRACK_TOP) / travel));
    const max = document.documentElement.scrollHeight - window.innerHeight;
    window.scrollTo({ top: p * max, behavior: 'auto' });
  }, []);

  const onPointerDown = useCallback((e: React.PointerEvent<HTMLElement>) => {
    if (e.button !== 0 && e.pointerType === 'mouse') return;
    e.preventDefault();
    e.currentTarget.setPointerCapture(e.pointerId);
    setDragging(true);
    scrollToPointer(e.clientY);
  }, [scrollToPointer]);

  const onPointerMove = useCallback((e: React.PointerEvent<HTMLElement>) => {
    if (!dragging) return;
    e.preventDefault();
    scrollToPointer(e.clientY);
  }, [dragging, scrollToPointer]);

  const endDrag = useCallback((e: React.PointerEvent<HTMLElement>) => {
    if (!dragging) return;
    setDragging(false);
    if (e.currentTarget.hasPointerCapture(e.pointerId)) e.currentTarget.releasePointerCapture(e.pointerId);
  }, [dragging]);

  const onKeyDown = useCallback((e: React.KeyboardEvent<HTMLElement>) => {
    const step = window.innerHeight * 0.8;
    const jump: Record<string, number> = { ArrowDown: step, PageDown: step, ArrowUp: -step, PageUp: -step };
    if (e.key in jump) { e.preventDefault(); window.scrollBy({ top: jump[e.key], behavior: 'smooth' }); }
    if (e.key === 'Home') { e.preventDefault(); window.scrollTo({ top: 0 }); }
    if (e.key === 'End') { e.preventDefault(); window.scrollTo({ top: document.documentElement.scrollHeight }); }
  }, []);

  let value: string;
  if (readout.kind === 'lines') {
    value = `LINE ${String(Math.max(1, Math.round(progress * readout.total))).padStart(3, '0')} / ${readout.total}`;
  } else if (readout.kind === 'items') {
    value = `${String(Math.max(1, Math.round(progress * readout.total))).padStart(2, '0')} / ${readout.total}`;
  } else {
    value = `${String(percent).padStart(3, '0')}%`;
  }

  return (
    <aside
      ref={panelRef}
      className={`descent-panel${dragging ? ' is-dragging' : ''}`}
      role="slider"
      tabIndex={0}
      aria-label="Page position. Drag to scroll."
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={percent}
      aria-orientation="vertical"
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={endDrag}
      onPointerCancel={endDrag}
      onKeyDown={onKeyDown}
    >
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
          draggable={false}
          sizes="(max-width: 640px) 56px, 100px"
        />
      </div>
      <p className="descent-note">drag to scroll</p>
    </aside>
  );
}
