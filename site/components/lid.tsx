'use client';

import { useEffect, useRef, useState } from 'react';

// A laptop that closes as it scrolls into view. Progress 0 = open, evening; 1 = shut, morning.
export function Lid({ hero = false }: { hero?: boolean }) {
  const ref = useRef<HTMLDivElement>(null);
  const [p, setP] = useState(0);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduced) { setP(1); return; }
    let frame = 0;
    const update = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        let t: number;
        if (hero) {
          // in the hero: shut by the time the hero has scrolled two-thirds of the way out
          const h = el.parentElement?.getBoundingClientRect().height ?? window.innerHeight * 0.5;
          t = window.scrollY / (h * 0.66);
        } else {
          const r = el.getBoundingClientRect();
          const vh = window.innerHeight;
          const start = vh * 0.85, end = vh * 0.35;
          t = (start - r.top) / (start - end);
        }
        setP(Math.min(1, Math.max(0, t)));
      });
    };
    update();
    window.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
    return () => { cancelAnimationFrame(frame); window.removeEventListener('scroll', update); window.removeEventListener('resize', update); };
  }, [hero]);

  const angle = -(p * 88);                    // 0deg open (screen upright) → -88deg shut (folded onto the base)
  const morning = p > 0.85;
  const hh = morning ? '07' : '23', mm = morning ? '12' : '41';

  return (
    <div className={`lid${hero ? ' lid-hero' : ''}`} ref={ref} style={{ ['--p' as string]: p }} aria-hidden="true">
      <div className="lid-clock">
        <span>{hh}:{mm}</span>
        <em>{morning ? 'morning · four lines waiting' : 'night · lid open'}</em>
      </div>
      <div className="lid-scene">
        <div className="lid-laptop">
          <div className="lid-screen" style={{ transform: `rotateX(${angle}deg)` }}>
            <div className="lid-glow" />
          </div>
          <div className="lid-base" />
        </div>
      </div>
      <p className="lid-caption">{p < 0.5 ? 'close it.' : 'still working.'}</p>
    </div>
  );
}
