import Link from 'next/link';
import { TerminalSquare } from 'lucide-react';
import { GITHUB } from '@/lib/content';
import { TopbarReadout } from './topbar-readout';

export function Shell({ path, children }: { path: string; children: React.ReactNode }) {
  return (
    <main className="site-shell">
      <header className="topbar">
        <nav className="brand-lockup" aria-label="Site">
          <Link className="brand-lockup" href="/" style={{ color: 'inherit', textDecoration: 'none' }}>
            <TerminalSquare aria-hidden="true" size={17} strokeWidth={1.5} />
            <span>PRODUCTAGENT</span>
          </Link>
          <Link className="topbar-link" href="/about">ABOUT</Link>
        </nav>
        <a className="topbar-path" href={GITHUB} target="_blank" rel="noreferrer" aria-label="Repository on GitHub" style={{ textDecoration: 'none' }}>
          harrisonhjohnson/productagent · {path}
        </a>
        <TopbarReadout />
      </header>
      <div className="page-grid">{children}</div>
    </main>
  );
}
