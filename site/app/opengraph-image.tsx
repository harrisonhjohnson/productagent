import { ImageResponse } from 'next/og';

export const alt = 'productagent.dev: Claude writes the code at night. You review it in the morning.';
export const size = { width: 1200, height: 630 };
export const contentType = 'image/png';

export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          padding: '64px 72px',
          background: '#e9e3d4',
          color: '#18382f',
          fontFamily: 'Menlo, Courier New, monospace',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 22, letterSpacing: 4 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div style={{ width: 14, height: 14, borderRadius: 999, background: '#d85d34' }} />
            <span>PRODUCTAGENT</span>
          </div>
          <span style={{ color: '#6e776d' }}>harrisonhjohnson/productagent</span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          <div style={{ fontSize: 26, color: '#d85d34', letterSpacing: 8 }}>PRODUCTAGENT</div>
          <div style={{ fontSize: 64, fontWeight: 700, letterSpacing: -2, lineHeight: 1.1 }}>Claude writes the code at night. You review it in the morning.</div>
          <div style={{ fontSize: 28, color: '#18382f', maxWidth: 980, lineHeight: 1.35 }}>
            Loops: one goal per loop, a fence the agent works inside, and a short report every morning. 33 nights on the record.
          </div>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 22, color: '#6e776d', letterSpacing: 3 }}>
          <span>productagent.dev</span>
          <span>Claude Code harnesses for product managers</span>
        </div>
      </div>
    ),
    size,
  );
}
