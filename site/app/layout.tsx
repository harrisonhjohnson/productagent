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
    default: 'productagent · an open-source product development agent, built on Claude Code',
    template: '%s · productagent',
  },
  description:
    'productagent does the product work as well as the code: user research, design, prototypes and fixes. Loops keep it going overnight, on a budget, on the Claude subscription you already pay for. Open source, or set up for you by the agency.',
  icons: { icon: '/favicon.svg' },
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
