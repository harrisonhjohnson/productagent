import type { Metadata } from 'next';
import { Geist_Mono } from 'next/font/google';
import { Analytics } from '@vercel/analytics/next';
import './globals.css';

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

const siteUrl =
  process.env.NEXT_PUBLIC_SITE_URL ??
  (process.env.VERCEL_PROJECT_PRODUCTION_URL
    ? `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}`
    : 'http://localhost:3000');

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: 'productagent — tools for PMs who run their day with Claude Code',
    template: '%s — productagent',
  },
  description:
    'A TODO list that follows you to your phone, a design interview that ends in a prototype, a strategy agent that argues back, and an agent that works overnight on a leash. Copy what you need.',
  openGraph: {
    siteName: 'productagent',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={geistMono.variable}>
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  );
}
