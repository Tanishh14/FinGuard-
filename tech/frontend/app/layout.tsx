import type { Metadata } from 'next';
import Navbar from './components/Navbar';
import './globals.css';

export const metadata: Metadata = {
  title: 'FinGuard AI - FinTech Dashboard',
  description: 'AI-powered fraud detection and analysis platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 min-h-screen">
        <Navbar />
        <main className="container mx-auto px-6 py-6">{children}</main>
        <footer className="mt-16 py-8 text-center border-t border-gray-200 bg-white">
          <p className="text-2xl font-bold text-gray-800">FinTech</p>
        </footer>
      </body>
    </html>
  );
}
