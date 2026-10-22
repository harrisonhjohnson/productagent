import Link from 'next/link';
import { TerminalSquare } from 'lucide-react';
import { GITHUB } from '@/lib/content';

export function Shell({ children }: { path: string; children: React.ReactNode }) {
  return (
    <main className="site-shell">
      <header className="topbar">
        <nav className="brand-lockup" aria-label="Site">
          <Link className="brand-lockup" href="/" style={{ color: 'inherit', textDecoration: 'none' }}>
            <TerminalSquare aria-hidden="true" size={17} strokeWidth={1.5} />
            <span>PRODUCTAGENT</span>
          </Link>
          <Link className="topbar-link" href="/about">ABOUT</Link>
          <Link className="topbar-link" href="/33-nights">ESSAY</Link>
          <Link className="topbar-link" href="/asks">ASKS</Link>
          <Link className="topbar-link" href="/evidence">RECEIPTS</Link>
        </nav>
        <a className="topbar-path" href={GITHUB} target="_blank" rel="noreferrer" style={{ textDecoration: 'none' }}>
          SOURCE ON GITHUB ↗
        </a>
      </header>
      <div className="page-grid">{children}</div>
    </main>
  );
}
