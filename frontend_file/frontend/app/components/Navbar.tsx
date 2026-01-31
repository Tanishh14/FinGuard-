'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { getToken, clearToken } from '../lib/api';

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [token, setTokenState] = useState<string | null>(null);

  useEffect(() => {
    setTokenState(getToken());
  }, [pathname]);

  const navItems = [
    { href: '/', label: 'Dashboard', icon: '📊' },
    { href: '/submit', label: 'Submit transaction', icon: '📤' },
    { href: '/gnn-detection', label: 'GNN Fraud Rings', icon: '🕸️' },
    { href: '/anomaly-detection', label: 'Anomaly Detection', icon: '📈' },
    { href: '/explainability', label: 'Explainability', icon: '🤖' },
    { href: '/live-transactions', label: 'Live Transactions', icon: '⚡' },
  ];

  function logout() {
    clearToken();
    setTokenState(null);
    router.push('/login');
    router.refresh();
  }

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
          {token ? (
            <button
              onClick={logout}
              className="px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100 rounded-lg"
            >
              Logout
            </button>
          ) : (
            <Link
              href="/login"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700"
            >
              Login
            </Link>
          )}
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium text-gray-700">LIVE</span>
          </div>
        </div>
      </div>
    </nav>
  );
}
