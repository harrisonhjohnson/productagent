import fs from 'node:fs';
import path from 'node:path';
import { ImageResponse } from 'next/og';

export const alt = 'Eleven Claude Code asks, written as specs';
export const size = { width: 1200, height: 630 };
export const contentType = 'image/png';

export default function AsksImage() {
  const md = fs.readFileSync(path.resolve(process.cwd(), '..', 'essays', 'asks.md'), 'utf8');
  const asks = [...md.matchAll(/^## (\d+)\. (.+)$/gm)].map((m) => [m[1], m[2]]);
  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          padding: '52px 72px',
          background: '#e9e3d4',
          color: '#18382f',
          fontFamily: 'Menlo, Courier New, monospace',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 22, letterSpacing: 4 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div style={{ width: 14, height: 14, borderRadius: 999, background: '#d85d34' }} />
            <span>PRODUCTAGENT · SPECS</span>
          </div>
          <span style={{ color: '#6e776d' }}>productagent.dev/asks</span>
        </div>
        <div style={{ fontSize: 50, fontWeight: 700, letterSpacing: -2, lineHeight: 1.1 }}>
          Eleven Claude Code asks, written as specs
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', borderTop: '2px solid #18382f', paddingTop: 18, rowGap: 8 }}>
          {asks.map(([n, name]) => (
            <div key={n} style={{ display: 'flex', width: '50%', fontSize: 21, gap: 12 }}>
              <span style={{ color: '#6f4b00', width: 34 }}>{n.padStart(2, '0')}</span>
              <span>{name}</span>
            </div>
          ))}
        </div>
      </div>
    ),
    size,
  );
}
