'use client';

import RiskScoreCard from './components/RiskScoreCard';
import RiskTrendChart from './components/RiskTrendChart';
import FraudMap from './components/FraudMap';
import AlertTable from './components/AlertTable';
import { useEffect, useState } from 'react';
import { api, type DashboardMetrics, type TransactionStats, type FraudAlertResponse } from './lib/api';

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [stats, setStats] = useState<TransactionStats | null>(null);
  const [alerts, setAlerts] = useState<FraudAlertResponse[] | null>(null);
  const [trends, setTrends] = useState<Array<{ date: string; total_transactions: number; avg_risk_score: number; fraudulent_transactions: number }> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const POLL_INTERVAL_MS = 5000;

  useEffect(() => {
    let cancelled = false;
    let isFirst = true;
    async function load() {
      if (isFirst) {
        setLoading(true);
        setError(null);
        isFirst = false;
      }
      try {
        const [metricsRes, statsRes, alertsRes, trendsRes] = await Promise.all([
          api.getDashboardMetrics(),
          api.getDashboardStats(),
          api.getAlertsRecent(20),
          api.getRiskTrends(7),
        ]);
        if (!cancelled) {
          setMetrics(metricsRes);
          setStats(statsRes);
          setAlerts(alertsRes);
          setTrends(trendsRes);
        }
      } catch (e) {
        const message = e instanceof Error ? e.message : 'Backend unavailable';
        if (!cancelled) setError(message);
        if (!cancelled && message === 'Authentication required') {
          setMetrics(null);
          setStats(null);
          setAlerts(null);
          setTrends(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    const interval = setInterval(load, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <p className="text-gray-600">Loading dashboard from backend…</p>
      </div>
    );
  }

  const isAuthRequired = error === 'Authentication required';
  if (error && !isAuthRequired) {
    return (
      <div className="space-y-6">
        <div className="bg-red-50 border-l-4 border-red-500 rounded-lg p-4">
          <p className="font-semibold text-red-800">Backend error</p>
          <p className="text-sm text-red-700">{error}</p>
          <p className="text-sm text-gray-600 mt-2">
            Ensure the backend is running (e.g. <code className="bg-gray-100 px-1">uvicorn app.main:app --host 0.0.0.0 --port 8000</code> in the backend folder)
            and <code className="bg-gray-100 px-1">NEXT_PUBLIC_API_URL</code> points to it. No mock data.
          </p>
        </div>
      </div>
    );
  }

  const dist = stats?.risk_score_distribution ?? {};
  const low = dist.low ?? 0;
  const medium = dist.medium ?? 0;
  const high = (dist.high ?? 0) + (dist.critical ?? 0);
  const totalDist = low + medium + high || 1;

  return (
    <div className="space-y-6">
      {isAuthRequired && (
        <div className="bg-amber-50 border-l-4 border-amber-500 rounded-lg p-3">
          <p className="font-medium text-amber-800">Authentication required</p>
          <p className="text-sm text-amber-700">Log in for personalized data. Showing dashboard with limited data.</p>
        </div>
      )}
      {alerts && alerts.length > 0 && (
        <div className="bg-red-50 border-l-4 border-red-500 rounded-lg p-4 flex items-center space-x-3">
          <span className="text-2xl">⚠️</span>
          <div>
            <p className="font-semibold text-gray-800">
              {alerts.length} high-risk alert{alerts.length !== 1 ? 's' : ''} (from backend)
            </p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <RiskScoreCard
          title="TOTAL TRANSACTIONS"
          value={metrics != null ? String(metrics.total_transactions) : '—'}
          subtitle={stats ? `Today: ${stats.today_transactions}` : '—'}
          color="red"
        />
        <RiskScoreCard
          title="FLAGGED TRANSACTIONS"
          value={metrics != null ? String(metrics.flagged_transactions) : '—'}
          subtitle={metrics != null ? `${metrics.high_risk_percentage.toFixed(1)}% high risk` : '—'}
          color="orange"
        />
        <RiskScoreCard
          title="HIGH RISK %"
          value={metrics != null ? `${metrics.high_risk_percentage.toFixed(1)}%` : '—'}
          subtitle={stats ? `Avg score: ${stats.avg_risk_score?.toFixed(1) ?? '0'}%` : '—'}
          color="green"
        />
        <RiskScoreCard
          title="TOTAL AMOUNT"
          value={stats != null ? String(stats.total_amount?.toFixed(2) ?? '0') : '—'}
          subtitle="Processed"
          color="blue"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RiskTrendChart
          data={
            trends?.map((t) => ({
              time: t.date,
              fraudAttempts: t.fraudulent_transactions,
              legitimateTransactions: t.total_transactions - t.fraudulent_transactions,
            })) ?? []
          }
        />
        <FraudMap
          data={{
            lowRisk: (low / totalDist) * 100,
            mediumRisk: (medium / totalDist) * 100,
            highRisk: (high / totalDist) * 100,
          }}
        />
      </div>

      <AlertTable alerts={alerts ?? []} />
    </div>
  );
}
