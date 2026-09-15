import fs from 'node:fs';
import path from 'node:path';

export const dynamic = 'force-static';

// Serves harnesses/loops/install.sh at productagent.dev/install.sh so the one-liner is short.
export function GET() {
  const file = path.resolve(process.cwd(), '..', 'harnesses', 'loops', 'install.sh');
  return new Response(fs.readFileSync(file, 'utf8'), {
    headers: { 'content-type': 'text/plain; charset=utf-8', 'cache-control': 'public, max-age=300' },
  });
}
