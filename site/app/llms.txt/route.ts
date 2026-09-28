import { INSTALL_COMMAND } from '@/lib/install';
import { GITHUB, getTree } from '@/lib/content';

export const dynamic = 'force-static';

const SITE = 'https://productagent.dev';

export function GET() {
  const harnesses = getTree().filter((n) => n.kind === 'folder' || n.kind === 'link');
  const list = harnesses
    .map((n) => `- [${n.name}](${n.href.startsWith('http') ? n.href : SITE + n.href}): ${n.summary ?? ''}`)
    .join('\n');
  const body = `# productagent.dev

> productagent.dev is a free, public library of ${harnesses.length} Claude Code harnesses for product managers and operators: skills, agents, shell scripts on a schedule, a permissions fence and a Telegram bot. The flagship, Loops, lets an agent keep working while you sleep: each loop has a goal, a budget, a cadence and a model, runs on your own Mac and Claude or ChatGPT plan inside a fence, and leaves four plain lines per loop in the morning. Free, no paid tier, nothing phones home.

Install Loops (macOS): \`${INSTALL_COMMAND}\`
Install one skill: copy its folder into ~/.claude/skills/ (agents go in ~/.claude/agents/), then restart Claude Code.

## Start here

- [About](${SITE}/about): what productagent.dev is, who it is for, how to install, FAQ
- [Loops concept page](${SITE}/harnesses/loops/README.md): the four knobs, five states and the morning report
- [Loops machine](${SITE}/harnesses/loops/MACHINE.md): the runner, the fence and the morning judge
- [Why loops](${SITE}/why): sourced quotes from the people building Claude Code

## Harnesses

${list}

## Source

- [GitHub repository](${GITHUB}): the site builds from this repo; every harness has a harness.json manifest
- [Sitemap](${SITE}/sitemap.xml)
`;
  return new Response(body, {
    headers: { 'content-type': 'text/plain; charset=utf-8', 'cache-control': 'public, max-age=300' },
  });
}
