import type { NextConfig } from 'next';
import path from 'node:path';

const nextConfig: NextConfig = {
  reactStrictMode: true,
  outputFileTracingRoot: path.join(import.meta.dirname, '..'),
  serverExternalPackages: ['shiki'],
};

export default nextConfig;
