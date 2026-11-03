import fs from 'node:fs';
import path from 'node:path';

export const dynamic = 'force-static';

export function GET() {
  const body = fs.readFileSync(/*turbopackIgnore: true*/ path.resolve(process.cwd(), '..', 'evidence', 'machine.schema.json'), 'utf8');
  return new Response(body, { headers: { 'content-type': 'application/json; charset=utf-8' } });
}
