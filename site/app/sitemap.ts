import type { MetadataRoute } from 'next';
import { getAllNodes } from '@/lib/content';

const SITE = 'https://productagent.dev';

export default function sitemap(): MetadataRoute.Sitemap {
  const pages: MetadataRoute.Sitemap = [
    { url: SITE, changeFrequency: 'weekly', priority: 1 },
    { url: `${SITE}/about`, changeFrequency: 'monthly', priority: 0.9 },
    { url: `${SITE}/why`, changeFrequency: 'monthly', priority: 0.7 },
    { url: `${SITE}/boring`, changeFrequency: 'weekly', priority: 0.6 },
  ];
  const harnesses = getAllNodes()
    .filter((n) => n.kind === 'folder' || n.kind === 'text')
    .map((n) => ({ url: SITE + n.href, changeFrequency: 'weekly' as const, priority: n.slug.length === 2 ? 0.8 : 0.5 }));
  return [...pages, ...harnesses];
}
