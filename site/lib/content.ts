import 'server-only';
import fs from 'node:fs';
import path from 'node:path';
import matter from 'gray-matter';

export const GITHUB = 'https://github.com/harrisonhjohnson/productagent';
const REF = 'main';
const REPO_ROOT = path.resolve(process.cwd(), '..');

const SKIP = new Set(['node_modules', '__pycache__', 'harness.json', '.DS_Store']);

export type NodeKind = 'folder' | 'text' | 'code' | 'file' | 'link';

export type Harness = {
  name: string;
  slug: string;
  tier: string;
  summary: string;
  source: string;
  entry: string | null;
  order: number;
  kind: 'files' | 'link';
  url: string | null;
};

export type TreeNode = {
  name: string;
  slug: string[];
  kind: NodeKind;
  meta: string;
  href: string;
  githubUrl: string;
  summary?: string;
  tier?: string;
  children?: TreeNode[];
};

const CODE_EXT = new Set(['.sh', '.py', '.ts', '.tsx', '.js', '.mjs', '.json', '.yaml', '.yml', '.plist', '.txt', '.example', '.toml', '.css']);
const LANG: Record<string, string> = {
  '.sh': 'bash', '.py': 'python', '.md': 'markdown', '.ts': 'typescript', '.tsx': 'tsx',
  '.js': 'javascript', '.mjs': 'javascript', '.json': 'json', '.yaml': 'yaml', '.yml': 'yaml',
  '.plist': 'xml', '.txt': 'text', '.example': 'ini', '.toml': 'toml', '.css': 'css',
};

function kindOf(name: string): NodeKind {
  const ext = path.extname(name).toLowerCase();
  if (ext === '.md') return 'text';
  if (CODE_EXT.has(ext)) return 'code';
  if (!ext && /^(Dockerfile|Makefile|LICENSE)$/i.test(name)) return 'code';
  return 'file';
}

export function langOf(name: string): string {
  return LANG[path.extname(name).toLowerCase()] ?? 'text';
}

function abs(slug: string[]) {
  return path.join(/*turbopackIgnore: true*/ REPO_ROOT, ...slug);
}

function readHarness(dir: string): Harness | null {
  const p = path.join(dir, 'harness.json');
  if (!fs.existsSync(p)) return null;
  return JSON.parse(fs.readFileSync(p, 'utf8')) as Harness;
}

function countLines(file: string) {
  const text = fs.readFileSync(file, 'utf8');
  return text.split('\n').length - (text.endsWith('\n') ? 1 : 0);
}

function fileNode(slug: string[]): TreeNode {
  const name = slug[slug.length - 1];
  return {
    name,
    slug,
    kind: kindOf(name),
    meta: `${countLines(abs(slug))} lines`,
    href: '/' + slug.join('/'),
    githubUrl: `${GITHUB}/blob/${REF}/${slug.join('/')}`,
  };
}

function folderNode(slug: string[]): TreeNode {
  const dir = abs(slug);
  const name = slug[slug.length - 1];
  const harness = readHarness(dir);

  if (harness?.kind === 'link' && harness.url) {
    return {
      name: harness.slug,
      slug,
      kind: 'link',
      meta: 'external',
      href: harness.url,
      githubUrl: harness.url,
      summary: harness.summary,
      tier: harness.tier,
    };
  }

  const entries = fs
    .readdirSync(dir, { withFileTypes: true })
    .filter((e) => !e.name.startsWith('.') && !SKIP.has(e.name));

  const children = entries.map((e) =>
    e.isDirectory() ? folderNode([...slug, e.name]) : fileNode([...slug, e.name]),
  );

  const order = (n: TreeNode) => {
    const h = n.kind === 'folder' || n.kind === 'link' ? readHarness(abs(n.slug)) : null;
    return h?.order ?? 1000;
  };
  children.sort((a, b) => {
    const ao = order(a), bo = order(b);
    if (ao !== bo) return ao - bo;
    const af = a.kind === 'folder' || a.kind === 'link' ? 0 : 1;
    const bf = b.kind === 'folder' || b.kind === 'link' ? 0 : 1;
    if (af !== bf) return af - bf;
    if (a.name.toLowerCase() === 'readme.md') return -1;
    if (b.name.toLowerCase() === 'readme.md') return 1;
    return a.name.localeCompare(b.name);
  });

  return {
    name,
    slug,
    kind: 'folder',
    meta: harness ? harness.tier : `${String(children.length).padStart(2, '0')} items`,
    href: '/' + slug.join('/'),
    githubUrl: `${GITHUB}/tree/${REF}/${slug.join('/')}`,
    summary: harness?.summary,
    tier: harness?.tier,
    children,
  };
}

let cachedTree: TreeNode[] | null = null;

export function getTree(): TreeNode[] {
  if (cachedTree) return cachedTree;
  cachedTree = folderNode(['harnesses']).children ?? [];
  return cachedTree;
}

function walk(nodes: TreeNode[], out: TreeNode[] = []) {
  for (const n of nodes) {
    out.push(n);
    if (n.children) walk(n.children, out);
  }
  return out;
}

export function getAllNodes() {
  return walk(getTree());
}

export function getAllSlugs(): string[][] {
  return getAllNodes()
    .filter((n) => n.kind !== 'link')
    .map((n) => n.slug);
}

export function getNode(slug: string[]): TreeNode | undefined {
  const key = slug.join('/');
  return getAllNodes().find((n) => n.slug.join('/') === key);
}

export function getHarness(slug: string[]): Harness | null {
  return readHarness(abs(slug));
}

export function readFile(slug: string[]) {
  const raw = fs.readFileSync(abs(slug), 'utf8');
  const name = slug[slug.length - 1];
  if (path.extname(name).toLowerCase() === '.md') {
    const { content, data } = matter(raw);
    return { content, frontmatter: data as Record<string, unknown>, lang: 'markdown', lines: countLines(abs(slug)) };
  }
  return { content: raw, frontmatter: {}, lang: langOf(name), lines: countLines(abs(slug)) };
}

export function countAll() {
  const all = getAllNodes();
  return {
    files: all.filter((n) => n.kind !== 'folder' && n.kind !== 'link').length,
    folders: all.filter((n) => n.kind === 'folder').length,
    harnesses: getTree().filter((n) => n.kind === 'folder' || n.kind === 'link').length,
  };
}
