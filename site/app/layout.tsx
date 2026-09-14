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
    'Loops: give an agent a goal, a budget, a cadence and a model, and read four plain sentences in the morning. Plus a TODO bot for your phone, a design interview that ends in a prototype, and a strategy agent that argues back. Copy what you need.',
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
