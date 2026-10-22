import 'server-only';
import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkGfm from 'remark-gfm';
import remarkRehype from 'remark-rehype';
import rehypeSlug from 'rehype-slug';
import rehypeShiki from '@shikijs/rehype';
import rehypeStringify from 'rehype-stringify';
import { codeToHtml } from 'shiki';

const THEMES = { light: 'vitesse-light', dark: 'vitesse-dark' };

export async function renderMarkdown(md: string): Promise<string> {
  const file = await unified()
    .use(remarkParse)
    .use(remarkGfm)
    .use(remarkRehype)
    .use(rehypeSlug)
    .use(rehypeShiki, { themes: THEMES, fallbackLanguage: 'text' })
    .use(rehypeStringify)
    .process(md);
  return String(file);
}

export async function renderCode(src: string, lang: string): Promise<string> {
  try {
    return await codeToHtml(src, { lang, themes: THEMES });
  } catch {
    return await codeToHtml(src, { lang: 'text', themes: THEMES });
  }
}

export type Heading = { text: string; line: number };

export function extractHeadings(md: string, max = 5): Heading[] {
  const lines = md.split('\n');
  const found: Heading[] = [];
  let inFence = false;
  lines.forEach((l, i) => {
    if (/^\s*```/.test(l)) inFence = !inFence;
    if (inFence) return;
    const m = /^##\s+(.+?)\s*#*\s*$/.exec(l);
    if (m) found.push({ text: m[1].replace(/[`*_]/g, ''), line: i });
  });
  if (found.length <= max) return found;
  const step = (found.length - 1) / (max - 1);
  return Array.from({ length: max }, (_, i) => found[Math.round(i * step)]);
}
