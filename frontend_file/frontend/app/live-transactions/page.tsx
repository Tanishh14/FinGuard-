'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, type TransactionItem } from '../lib/api';

export default function LiveTransactionsPage() {
  const [transactions, setTransactions] = useState<TransactionItem[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  const POLL_INTERVAL_MS = 5000;

  useEffect(() => {
    let cancelled = false;
    let isFirst = true;
    let es: EventSource | null = null;

    async function load() {
      if (isFirst) {
        setLoading(true);
        setError(null);
        isFirst = false;
      }
      try {
        const res = await api.listTransactions({ skip: 0, limit: 100 });
        if (!cancelled) setTransactions(res.items);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Backend unavailable');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();

    // Real-time via Server-Sent Events
    try {
      es = new EventSource('/api/v1/stream');
      es.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data);
          if (data?.type === 'transaction') {
            setTransactions((prev) => {
              if (!prev) return [data as any];
              // Prepend new transaction and keep unique by transaction_id
              const dedup = [data as any, ...prev.filter((t) => t.transaction_id !== data.transaction_id)];
              return dedup.slice(0, 100);
            });
          }
        } catch (err) {
          // ignore parse errors
        }
      };
      es.onerror = () => {
        // Attempt to reconnect by closing and letting browser reconnect
        if (es) es.close();
        setTimeout(() => {
          // trigger reload attempt
          setRetryCount((c) => c + 1);
        }, 2000);
      };
    } catch (err) {
      // If SSE is not supported, fallback to polling (already running)
    }

    return () => {
      cancelled = true;
      if (es) es.close();
    };
  }, [retryCount]);

  const getRiskColor = (score: number) => {
    if (score >= 80) return 'bg-red-500';
    if (score >= 60) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getDecisionBadge = (isFraudulent: boolean, riskLevel: string) => {
    if (isFraudulent || riskLevel === 'high' || riskLevel === 'critical') return 'bg-red-100 text-red-800';
    if (riskLevel === 'medium') return 'bg-yellow-100 text-yellow-800';
    return 'bg-green-100 text-green-800';
  };

  const getDecision = (isFraudulent: boolean, riskLevel: string) => {
    if (isFraudulent || riskLevel === 'high' || riskLevel === 'critical') return 'Blocked';
    if (riskLevel === 'medium') return 'Flagged';
    return 'Approved';
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <p className="text-gray-600">Loading transactions from backend…</p>
      </div>
    );
  }

  if (error) {
    const isUnreachable = error.includes('Backend unreachable') || error.includes('unavailable');
    const isAuthError = error.includes('Authentication required') || error.toLowerCase().includes('auth') || error.toLowerCase().includes('login');
    const backendUrl =
      (typeof process !== 'undefined' && process.env?.NEXT_PUBLIC_API_URL) || 'http://localhost:8000';
    const healthUrl = `${backendUrl.replace(/\/$/, '')}/health`;
    return (
      <div className="space-y-6">
        <div className="bg-red-50 border-l-4 border-red-500 rounded-lg p-4">
          <p className="font-semibold text-red-800">Backend error</p>
          <p className="text-sm text-red-700 mt-1">{error}</p>
          {isUnreachable ? (
            <>
              <p className="text-sm text-gray-700 mt-3 font-medium">Quick checks:</p>
              <ul className="text-sm text-gray-700 mt-1 list-disc list-inside space-y-1">
                <li>Start the backend: <code className="bg-gray-100 px-1 rounded">cd backend && uvicorn main:app --host 0.0.0.0 --port 8000</code> (or <code className="bg-gray-100 px-1 rounded">uvicorn app.main:app</code>)</li>
                <li>In <code className="bg-gray-100 px-1 rounded">frontend_file/frontend/.env.local</code> set <code className="bg-gray-100 px-1 rounded">NEXT_PUBLIC_API_URL={backendUrl}</code></li>
                <li>Restart the Next.js dev server after changing env.</li>
                <li>Log in; Live Transactions requires an authenticated user.</li>
              </ul>
              <p className="text-sm text-gray-600 mt-2">
                <a
                  href={healthUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline font-medium"
                >
                  Open backend health in new tab →
                </a>
                {' '}(if it loads, backend is up and the issue may be proxy or login)
              </p>
            </>
          ) : isAuthError ? (
            <>
              <p className="text-sm text-gray-700 mt-3 font-medium">Authentication required</p>
              <p className="text-sm text-gray-600 mt-2">This page requires a logged-in user. Please sign in with the demo account to view live transactions.</p>
              <div className="mt-3 flex space-x-2">
                <Link href="/login" className="px-3 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium">Open login</Link>
                <button
                  type="button"
                  onClick={() => { localStorage.removeItem('finguard_token'); window.location.href = '/login'; }}
                  className="px-3 py-2 bg-gray-100 text-gray-800 rounded-lg text-sm"
                >
                  Clear token & go
                </button>
              </div>
            </>
          ) : (
            <p className="text-sm text-gray-600 mt-2">No mock data. Ensure backend is running and you are logged in.</p>
          )}
          <button
            type="button"
            onClick={() => { setError(null); setLoading(true); setRetryCount((c) => c + 1); }}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm font-medium"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-3xl font-bold text-gray-800">Live Transaction Monitoring</h1>
          <span className="inline-flex items-center px-3 py-1 rounded-full bg-green-50 text-green-800 text-sm font-medium">LIVE</span>
        </div>
        <p className="text-gray-600">Real-time transactions from the backend. No mock data.</p>
      </div>

      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                  Transaction ID
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                  Amount
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                  Merchant
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                  Risk Score
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                  Decision
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {transactions && transactions.length > 0 ? (
                transactions.map((tx) => (
                  <tr key={tx.transaction_id} className="bg-white">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {tx.transaction_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-800">
                      {tx.currency} {tx.amount.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-800">
                      {tx.merchant_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium text-gray-800">{tx.risk_score.toFixed(0)}%</span>
                        <div className="w-24 bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${getRiskColor(tx.risk_score)}`}
                            style={{ width: `${Math.min(100, tx.risk_score)}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-medium ${getDecisionBadge(
                          tx.is_fraudulent,
                          tx.risk_level
                        )}`}
                      >
                        {getDecision(tx.is_fraudulent, tx.risk_level)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Link
                        href={`/explainability?tx=${tx.transaction_id}`}
                        className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded text-sm"
                      >
                        Explain
                      </Link>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                    No transactions. Submit a transaction to see data from backend.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
