import { useMemo } from 'react';

function mulberry32(seed: number) {
  return () => {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function NightSky({ dim = false }: { dim?: boolean }) {
  const stars = useMemo(() => {
    const rand = mulberry32(20260915);
    return Array.from({ length: 90 }, (_, i) => ({
      id: i,
      x: rand() * 100,
      y: rand() * 62,
      r: rand() * 1.15 + 0.18,
      o: rand() * 0.55 + 0.18,
      delay: rand() * 7,
    }));
  }, []);

  return (
    <div className={`sky ${dim ? 'is-dim' : ''}`} aria-hidden="true">
      <svg className="sky-svg" viewBox="0 0 1440 900" preserveAspectRatio="xMidYMid slice">
        <defs>
          <linearGradient id="sky-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#071018" />
            <stop offset="55%" stopColor="#101a2c" />
            <stop offset="100%" stopColor="#1c2436" />
          </linearGradient>
          <radialGradient id="moon-glow" cx="42%" cy="58%" r="28%">
            <stop offset="0%" stopColor="#e8d4a8" stopOpacity="0.22" />
            <stop offset="70%" stopColor="#e8d4a8" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="mist" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#b7c0d4" stopOpacity="0" />
            <stop offset="100%" stopColor="#c5b8a4" stopOpacity="0.18" />
          </linearGradient>
        </defs>
        <rect width="1440" height="900" fill="url(#sky-fill)" />
        <ellipse cx="610" cy="530" rx="420" ry="180" fill="url(#moon-glow)" />
        {stars.map((s) => (
          <circle
            key={s.id}
            className="star"
            cx={(s.x / 100) * 1440}
            cy={(s.y / 100) * 900}
            r={s.r}
            fill="#f3ead8"
            opacity={s.o}
            style={{ animationDelay: `${s.delay}s` }}
          />
        ))}
        <g className="crescent" transform="translate(610 520)">
          <circle r="28" fill="#f6e7c6" />
          <circle cx="11" cy="-6" r="24" fill="#101a2c" />
        </g>
        <path d="M0 620 C 180 560, 280 600, 420 575 C 560 550, 640 610, 820 590 C 1000 570, 1120 630, 1440 580 L 1440 900 L 0 900 Z" fill="#141c2c" opacity="0.95" />
        <path d="M0 680 C 220 640, 360 700, 540 665 C 740 625, 900 710, 1440 650 L 1440 900 L 0 900 Z" fill="#0e1624" />
        <path d="M0 740 C 260 710, 480 780, 760 740 C 1040 700, 1240 770, 1440 730 L 1440 900 L 0 900 Z" fill="#0a101c" />
        <rect width="1440" height="900" fill="url(#mist)" />
      </svg>
    </div>
  );
}

export function QuietRoom({ warm = 0 }: { warm?: number }) {
  return (
    <div className="room" style={{ ['--warm' as string]: String(warm) }} aria-hidden="true">
      <div className="room-wash" />
      <div className="window">
        <div className="window-light" />
        <div className="mullion v" />
        <div className="mullion v two" />
        <div className="mullion h" />
      </div>
      <div className="lamp" />
      <div className="floor" />
    </div>
  );
}

export function Grain() {
  return <div className="grain" aria-hidden="true" />;
}

export function ClosedMac({ running = false }: { running?: boolean }) {
  return (
    <svg className="closed-mac" viewBox="0 0 420 96" aria-hidden="true">
      <rect x="24" y="10" width="372" height="58" rx="10" fill="#141c2c" stroke="rgba(232,212,168,0.38)" />
      <rect x="36" y="20" width="348" height="38" rx="4" fill="#0c1424" />
      <g transform="translate(210 39)">
        <circle r="11" fill="#f6e7c6" />
        <circle cx="5" cy="-3" r="9.5" fill="#0c1424" />
      </g>
      {running ? <circle className="mac-led" cx="360" cy="39" r="3.2" fill="#d4b483" /> : null}
      <rect x="16" y="68" width="388" height="12" rx="3" fill="#2a3344" />
      <rect x="16" y="78" width="388" height="7" rx="2" fill="#c9bda6" opacity="0.45" />
    </svg>
  );
}
