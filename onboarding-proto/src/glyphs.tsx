const STROKE = {
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.6,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
};

export function LoopGlyph() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" {...STROKE}>
      <path d="M19 12a7 7 0 1 1-2.1-5" />
      <path d="M17 3v4h-4" />
    </svg>
  );
}

export function RunGlyph() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" {...STROKE}>
      <path d="M4 12h13" />
      <path d="M13 7l5 5-5 5" />
    </svg>
  );
}

export function OrderGlyph() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" {...STROKE}>
      <path d="M6 4h12v16H6z" />
      <path d="M9 9h6M9 13h6M9 17h3" />
      <circle cx="12" cy="4" r="1.6" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function DecisionGlyph() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" {...STROKE}>
      <path d="M12 20V11" />
      <path d="M12 11L6 5M12 11l6-6" />
      <circle cx="6" cy="5" r="1.4" fill="currentColor" stroke="none" />
      <circle cx="18" cy="5" r="1.4" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function PlugGlyph() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" {...STROKE}>
      <path d="M9 3v5M15 3v5" />
      <path d="M6 8h12v3a6 6 0 0 1-12 0z" />
      <path d="M12 17v4" />
    </svg>
  );
}

export function LidGlyph({ open }: { open: boolean }) {
  return open ? (
    <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" {...STROKE}>
      <path d="M3 18h18" />
      <path d="M6 18V7l12-3v14" />
    </svg>
  ) : (
    <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" {...STROKE}>
      <path d="M3 17h18" />
      <path d="M5 17v-2h14v2" />
    </svg>
  );
}

export function MoonZGlyph() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" {...STROKE}>
      <path d="M9 4a8 8 0 1 0 9 12A7 7 0 0 1 9 4z" />
      <path d="M15 3h4l-4 4h4" />
    </svg>
  );
}

export function PhoneGlyph() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" {...STROKE}>
      <rect x="7" y="2" width="10" height="20" rx="2" />
      <path d="M10 19h4" />
    </svg>
  );
}

export function GraphGlyph() {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true" {...STROKE}>
      <circle cx="6" cy="12" r="2.2" />
      <circle cx="12" cy="6" r="2.2" />
      <circle cx="18" cy="10" r="2.2" />
      <circle cx="14" cy="18" r="2.2" />
      <path d="M8 11.2l2.4-3.6M13.8 7.6l2.4 1.6M16.4 12.2l-1.6 4.2M12.2 8.2l1.2 7.4M8 13.4l4.2 3.4" />
    </svg>
  );
}

export const NOUN_GLYPH = {
  Loop: LoopGlyph,
  Run: RunGlyph,
  Order: OrderGlyph,
  Decision: DecisionGlyph,
} as const;
