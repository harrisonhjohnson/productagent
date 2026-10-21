import type { NextConfig } from 'next';
import path from 'node:path';

const nextConfig: NextConfig = {
  reactStrictMode: true,
  outputFileTracingRoot: path.join(import.meta.dirname, '..'),
  serverExternalPackages: ['shiki'],
  async redirects() {
    return [{ source: '/boring', destination: '/', permanent: true }];
  },
};

export default nextConfig;
