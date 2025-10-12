import React from 'react';
import type { Metadata } from 'next';
import { ApiProvider } from '@/components/ApiProvider';

export const metadata: Metadata = {
  title: 'BioSTEAM Designer',
  description: 'Block-based designer for BioSTEAM front-end',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, fontFamily: 'system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, sans-serif' }}>
        <ApiProvider>
          {children}
        </ApiProvider>
      </body>
    </html>
  );
}

