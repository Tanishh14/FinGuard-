'use client';

import { useEffect, useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { api, type AnomalySummary } from '../lib/api';

export default function AnomalyDetectionPage() {
  const [data, setData] = useState<AnomalySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await api.getAnomalySummary();
        if (!cancelled) setData(res);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load data');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-gray-800">Deep Anomaly Detection</h1>
        <p className="text-gray-600">Loading data from API…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-gray-800">Deep Anomaly Detection</h1>
        <div className="bg-red-50 border-l-4 border-red-500 rounded-lg p-4">
          <p className="font-semibold text-red-800">Data unavailable</p>
          <p className="text-sm text-red-700">{error}</p>
          <p className="text-sm text-gray-600 mt-2">
            Log in first. Then ensure the backend is running so /api/v1/anomaly/summary is available.
          </p>
        </div>
      </div>
    );
  }

  const chartData = data?.chart_data ?? [];
  const scores = data?.scores ?? [];
  const alertMessage = data?.alert?.message ?? '';

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-2 mb-6">
        <span className="text-2xl">📈</span>
        <h1 className="text-3xl font-bold text-gray-800">Deep Anomaly Detection</h1>
      </div>
      <p className="text-gray-600 mb-6">Anomaly scores from GET /api/v1/anomaly/summary (real DB data).</p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Anomaly score by transaction</h3>
          {chartData.length === 0 ? (
            <p className="text-gray-500 py-8">No anomaly data yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="user" stroke="#6b7280" angle={-45} textAnchor="end" height={80} />
                <YAxis stroke="#6b7280" domain={[0, 100]} />
                <Tooltip />
                <Bar dataKey="score" fill="#6366f1" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
        <div className="space-y-6">
          {alertMessage && (
            <div className="bg-blue-50 border-l-4 border-blue-500 rounded-lg p-4">
              <h4 className="font-bold text-gray-800 mb-1">Anomaly Detection Alert</h4>
              <p className="text-sm text-gray-700">{alertMessage}</p>
            </div>
          )}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Anomaly scores (from API)</h3>
            {scores.length === 0 ? (
              <p className="text-gray-500">No scores.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-2 px-2 font-medium text-gray-700">User</th>
                      <th className="text-left py-2 px-2 font-medium text-gray-700">Score</th>
                      <th className="text-left py-2 px-2 font-medium text-gray-700">Pattern</th>
                      <th className="text-left py-2 px-2 font-medium text-gray-700">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {scores.map((row, i) => (
                      <tr key={i} className="border-b border-gray-100">
                        <td className="py-2 px-2 text-gray-800">{row.user}</td>
                        <td className="py-2 px-2">{row.score}%</td>
                        <td className="py-2 px-2 text-gray-700">{row.pattern ?? '—'}</td>
                        <td className="py-2 px-2">{row.status ?? '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
