import type { ReactNode } from 'react';
import { BEATS } from './data';
import type { BeatId } from './types';

export function Shell({
  beat,
  onJump,
  helpOpen,
  children,
  hint,
  title,
  kicker,
}: {
  beat: BeatId;
  onJump: (id: BeatId) => void;
  helpOpen: boolean;
  children: ReactNode;
  hint: string;
  title: string;
  kicker: string;
}) {
  return (
    <div className="shell" data-beat={beat} data-help={helpOpen ? 'open' : 'closed'}>
      <header className="chrome-top">
        <div className="brand">
          <span className="dot" />
          <span>PRODUCTAGENT</span>
          <span className="sep">·</span>
          <span className="muted">DEMO</span>
          <span className="sep">·</span>
          <span className="muted">POST-INSTALL</span>
        </div>
        <nav className="rail" aria-label="Beats">
          {BEATS.map((b) => (
            <button
              key={b.id}
              type="button"
              className={b.id === beat ? 'tick is-now' : b.id < beat ? 'tick is-done' : 'tick'}
              onClick={() => onJump(b.id as BeatId)}
              title={`${b.code} · ${b.name}`}
              aria-current={b.id === beat ? 'step' : undefined}
            >
              <span className="tick-code">{b.code}</span>
            </button>
          ))}
        </nav>
        <p className="demo-note">Demo only · no install · no network</p>
      </header>

      <main className="stage" tabIndex={-1} aria-labelledby="beat-title">
        <p className="kicker" id="beat-kicker">
          {kicker}
        </p>
        <h1 id="beat-title" className="sr-only">
          {title}
        </h1>
        {children}
      </main>

      <footer className="chrome-bot">
        <p className="hint">
          <kbd>Enter</kbd> {hint}
          <span className="hint-gap" />
          <kbd>?</kbd> keys
          <span className="hint-gap" />
          <kbd>⌫</kbd> back
        </p>
        <p className="beat-name">
          {BEATS[beat].code} · {BEATS[beat].name}
        </p>
      </footer>
    </div>
  );
}

export function HelpOverlay({ onClose }: { onClose: () => void }) {
  return (
    <div className="help" role="dialog" aria-labelledby="help-title">
      <div className="help-card">
        <p className="kicker" id="help-title">
          Keyboard
        </p>
        <ul>
          <li>
            <kbd>Enter</kbd> <kbd>Space</kbd> continue / confirm
          </li>
          <li>
            <kbd>⌫</kbd> <kbd>←</kbd> previous beat
          </li>
          <li>
            <kbd>1</kbd>–<kbd>4</kbd> arm Loop, Run, Order, Decision
          </li>
          <li>
            <kbd>1</kbd>–<kbd>6</kbd> pick a starter Loop on B3
          </li>
          <li>
            <kbd>Tab</kbd> knobs · <kbd>←</kbd> <kbd>→</kbd> change
          </li>
          <li>
            <kbd>Esc</kbd> skip a cinematic · close this
          </li>
          <li>
            <kbd>R</kbd> replay from cold boot
          </li>
        </ul>
        <p className="help-foot">Click the B0–B8 ticks to jump. This is a demo. Nothing is installed.</p>
        <button type="button" className="text-btn" onClick={onClose}>
          Close
        </button>
      </div>
    </div>
  );
}
