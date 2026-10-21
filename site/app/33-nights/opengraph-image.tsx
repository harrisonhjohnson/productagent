import { ImageResponse } from 'next/og';
import { getEvidence } from '@/lib/evidence';

export const alt = '33 nights of unattended Claude Code, and what I’d ship as its PM';
export const size = { width: 1200, height: 630 };
export const contentType = 'image/png';

export default function EssayImage() {
  const t = getEvidence()?.totals;
  const nights = t?.nights ?? 33;
  const avg = t ? t.night_cost_usd / t.nights : 6.13;
  const stats: [string, string][] = [
    [String(nights), 'nights'],
    [`$${avg.toFixed(2)}`, 'average night'],
    ['10', 'things broke'],
    ['11', 'Claude Code asks'],
  ];
  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          padding: '60px 72px',
          background: '#e9e3d4',
          color: '#18382f',
          fontFamily: 'Menlo, Courier New, monospace',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 22, letterSpacing: 4 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div style={{ width: 14, height: 14, borderRadius: 999, background: '#d85d34' }} />
            <span>PRODUCTAGENT · ESSAY</span>
          </div>
          <span style={{ color: '#6e776d' }}>productagent.dev/33-nights</span>
        </div>
        <div style={{ fontSize: 58, fontWeight: 700, letterSpacing: -2, lineHeight: 1.1, maxWidth: 1040 }}>
          33 nights of unattended Claude Code, and what I’d ship as its PM
        </div>
        <div style={{ display: 'flex', borderTop: '2px solid #18382f' }}>
          {stats.map(([big, label]) => (
            <div key={label} style={{ display: 'flex', flexDirection: 'column', flex: 1, paddingTop: 20, gap: 6 }}>
              <span style={{ fontSize: 56, fontWeight: 700, letterSpacing: -2 }}>{big}</span>
              <span style={{ fontSize: 20, color: '#6e776d', letterSpacing: 3, textTransform: 'uppercase' }}>{label}</span>
            </div>
          ))}
        </div>
      </div>
    ),
    size,
  );
}
