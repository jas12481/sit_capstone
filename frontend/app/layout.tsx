import type { Metadata } from 'next';
import './globals.css';
import Sidebar from '@/components/Sidebar';
import SessionProviderWrapper from '@/components/SessionProviderWrapper';

export const metadata: Metadata = {
  title: 'AIA Claims AI',
  description: 'AI-governed insurance claims operations platform',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <SessionProviderWrapper>
          <div className="flex h-screen overflow-hidden">
            <Sidebar />
            <main className="ml-56 flex-1 overflow-y-auto">
              {children}
            </main>
          </div>
        </SessionProviderWrapper>
      </body>
    </html>
  );
}
