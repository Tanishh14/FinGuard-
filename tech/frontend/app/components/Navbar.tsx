'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Navbar() {
  const pathname = usePathname();

  const navItems = [
    { href: '/', label: 'Dashboard', icon: '📊' },
    { href: '/gnn-detection', label: 'GNN Fraud Rings', icon: '🕸️' },
    { href: '/anomaly-detection', label: 'Anomaly Detection', icon: '📈' },
    { href: '/explainability', label: 'LLM + RAG Explainability', icon: '🤖' },
    { href: '/live-transactions', label: 'Live Transactions', icon: '⚡' },
  ];

  return (
    <nav className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-8">
          <div className="flex items-center space-x-2">
            <span className="text-2xl">🛡️</span>
            <span className="text-xl font-bold text-blue-900">FinGuard AI</span>
          </div>
          <div className="flex space-x-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <span className="mr-2">{item.icon}</span>
                  {item.label}
                </Link>
              );
            })}
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium text-gray-700">LIVE</span>
          </div>
          <div className="px-3 py-1 bg-blue-50 border border-blue-200 rounded text-xs font-medium text-blue-700">
            IN Made in India
          </div>
        </div>
      </div>
    </nav>
  );
}
