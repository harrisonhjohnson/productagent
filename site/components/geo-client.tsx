'use client';

import { useEffect, useState } from 'react';

type Entry = { id: string; msg: string; verbs: [string, string][] };

const ENTRIES: Entry[] = [
  { id: 'D-014', msg: "Merge last nite's fix to the empty state?", verbs: [['Merge', 'MERGED'], ['Park', 'PARKED']] },
  { id: 'D-015', msg: 'Retry each source on its own instead of stopping everything?', verbs: [['Apply', 'APPLIED'], ['Park', 'PARKED']] },
  { id: 'D-016', msg: 'Keep the state portal as a by-hand check? Its certificate is broken.', verbs: [['Yes', 'YES'], ['Later', 'LATER']] },
];

export function Guestbook() {
  const [signed, setSigned] = useState<Record<string, string>>({});
  const left = ENTRIES.length - Object.keys(signed).length;
  return (
    <>
      <table className="gb">
        <thead>
          <tr><th>#</th><th>MESSAGE</th><th>SIGN</th></tr>
        </thead>
        <tbody>
          {ENTRIES.map((e) => (
            <tr key={e.id} className={signed[e.id] ? 'done' : undefined}>
              <td><b>{e.id}</b></td>
              <td className="msg">{e.msg}</td>
              <td>
                {signed[e.id] ? (
                  <span className="stamp">{signed[e.id]} ✓</span>
                ) : (
                  e.verbs.map(([label, stamp]) => (
                    <button key={label} type="button" onClick={() => setSigned((s) => ({ ...s, [e.id]: stamp }))}>{label}</button>
                  ))
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="tiny" aria-live="polite" style={{ marginTop: 6 }}>
        {left ? `${left} unsigned entr${left === 1 ? 'y' : 'ies'} (this is a demo, nothing is saved)` : 'all signed!!! go back 2 sleep'}
      </p>
    </>
  );
}

export function Webring({ sites }: { sites: string[] }) {
  const ring = ['productagent.dev', ...sites];
  const [at, setAt] = useState(0);
  const go = (i: number) => setAt((i + ring.length) % ring.length);
  return (
    <div className="webring">
      <div className="webring-title">★ The Night Shift Webring ★</div>
      <button type="button" onClick={() => go(at - 1)}>&lt;&lt; Prev</button>|
      <button type="button" onClick={() => go(Math.floor(Math.random() * ring.length))}>Random</button>|
      <button type="button" onClick={() => go(at + 1)}>Next &gt;&gt;</button>
      <div className="tiny" style={{ marginTop: 4 }} aria-live="polite">this site: {ring[at]}</div>
    </div>
  );
}

export function Sparkles() {
  useEffect(() => {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches || !matchMedia('(hover: hover)').matches) return;
    const stars = ['✦', '★', '✧', '·'];
    const colors = ['#ff0', '#0ff', '#f0f', '#fff'];
    let last = 0;
    const onMove = (e: MouseEvent) => {
      const now = Date.now();
      if (now - last < 45) return;
      last = now;
      const s = document.createElement('span');
      s.className = 'geo-sparkle';
      s.setAttribute('aria-hidden', 'true');
      s.textContent = stars[Math.floor(Math.random() * stars.length)];
      s.style.color = colors[Math.floor(Math.random() * colors.length)];
      s.style.left = `${e.clientX + 6}px`;
      s.style.top = `${e.clientY + 6}px`;
      document.body.appendChild(s);
      setTimeout(() => s.remove(), 900);
    };
    document.addEventListener('mousemove', onMove);
    return () => document.removeEventListener('mousemove', onMove);
  }, []);
  return null;
}
