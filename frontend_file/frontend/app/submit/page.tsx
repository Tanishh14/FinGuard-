'use client';

import { useState } from 'react';
import Link from 'next/link';
import { api, type PredictFraudResponse } from '../lib/api';

function getUserIdFromToken(): string {
  if (typeof window === 'undefined') return '';
  const t = localStorage.getItem('finguard_token');
  if (!t) return '';
  try {
    const payload = JSON.parse(atob(t.split('.')[1] || ''));
    return (payload.sub as string) || '';
  } catch {
    return '';
  }
}

export default function SubmitTransactionPage() {
  const [transactionId, setTransactionId] = useState(`txn_${Date.now()}`);
  const [amount, setAmount] = useState(150);
  const [merchant, setMerchant] = useState('merchant_001');
  const [deviceId, setDeviceId] = useState('');
  const [ipAddress, setIpAddress] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<PredictFraudResponse | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setResult(null);
    setLoading(true);
    try {
      const user_id = getUserIdFromToken();
      if (!user_id) {
        setError('Not logged in. Please log in first.');
        return;
      }
      const res = await api.predictFraud({
        transaction_id: transactionId,
        user_id,
        amount,
        timestamp: new Date().toISOString(),
        merchant,
        device_id: deviceId,
        ip_address: ipAddress,
      });
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed');
    } finally {
      setLoading(false);
    }
  }

  const riskColor =
    result?.risk_label === 'HIGH' ? 'red' : result?.risk_label === 'MEDIUM' ? 'orange' : 'green';

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Submit transaction for fraud check</h1>
      <p className="text-gray-600">
        All data is sent to the backend; response is real ML scores. No mock data.
      </p>

      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-sm p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Transaction ID</label>
          <input
            type="text"
            value={transactionId}
            onChange={(e) => setTransactionId(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Amount</label>
          <input
            type="number"
            step="0.01"
            value={amount}
            onChange={(e) => setAmount(Number(e.target.value))}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Merchant</label>
          <input
            type="text"
            value={merchant}
            onChange={(e) => setMerchant(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Device ID (optional)</label>
          <input
            type="text"
            value={deviceId}
            onChange={(e) => setDeviceId(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">IP address (optional)</label>
          <input
            type="text"
            value={ipAddress}
            onChange={(e) => setIpAddress(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg"
          />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="w-full py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Analyzing…' : 'Check fraud'}
        </button>
      </form>

      {result && (
        <div className="bg-white rounded-lg shadow-sm p-6 space-y-4">
          <h2 className="text-lg font-semibold text-gray-800">Result (from backend)</h2>
          <p className="text-sm text-gray-600">
            Transaction stored. Dashboard and Live Transactions will update automatically within a few seconds.
          </p>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">Fraud risk score (0–100):</span>
            <span className={`text-2xl font-bold text-${riskColor}-600`}>
              {(result.fraud_score * 100).toFixed(2)}%
            </span>
            <span
              className={`px-3 py-1 rounded text-sm font-medium ${
                result.risk_label === 'HIGH'
                  ? 'bg-red-100 text-red-800'
                  : result.risk_label === 'MEDIUM'
                    ? 'bg-orange-100 text-orange-800'
                    : 'bg-green-100 text-green-800'
              }`}
            >
              {result.risk_label}
            </span>
          </div>
          <div className="border-t pt-4">
            <h3 className="font-medium text-gray-800 mb-2">Model scores</h3>
            <ul className="text-sm text-gray-700 space-y-1">
              <li>Autoencoder: {(result.model_scores.autoencoder * 100).toFixed(2)}%</li>
              <li>Isolation Forest: {(result.model_scores.isolation_forest * 100).toFixed(2)}%</li>
              <li>GNN: {(result.model_scores.gnn * 100).toFixed(2)}%</li>
            </ul>
          </div>
          <p className="text-xs text-gray-500">
            Transaction ID: {result.transaction_id} ·{' '}
            <Link href={`/explainability?tx=${result.transaction_id}`} className="text-blue-600 hover:underline">
              Get explanation
            </Link>
          </p>
        </div>
      )}
    </div>
  );
}
