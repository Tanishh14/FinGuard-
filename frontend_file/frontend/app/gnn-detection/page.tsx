'use client';

import { useEffect, useState } from 'react';
import { api, type GnnClustersResponse } from '../lib/api';

export default function GnnDetectionPage() {
  const [data, setData] = useState<GnnClustersResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await api.getGnnClusters();
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
        <h1 className="text-2xl font-bold text-gray-800">Graph Neural Network Detection</h1>
        <p className="text-gray-600">Loading data from API…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-800">Graph Neural Network Detection</h1>
        <div className="bg-red-50 border-l-4 border-red-500 rounded-lg p-4">
          <p className="font-semibold text-red-800">GNN API unavailable</p>
          <p className="text-sm text-red-700">{error}</p>
          <p className="text-sm text-gray-600 mt-2">
            Log in first. Then ensure the backend is running so /api/v1/gnn/clusters is available.
          </p>
        </div>
      </div>
    );
  }

  const clusters = data?.clusters ?? [];
  const nodes = data?.nodes ?? [];
  const edges = data?.edges ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-2 mb-6">
        <span className="text-2xl">🕸️</span>
        <h1 className="text-2xl font-bold text-gray-800">Graph Neural Network Detection</h1>
      </div>
      <p className="text-sm text-gray-600 mb-6">
        Graph built from real transactions (nodes: users, devices, merchants). Data from /api/v1/gnn/clusters.
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Graph (nodes & edges from API)</h2>
          <div className="bg-gray-50 rounded-lg p-8 border-2 border-dashed border-gray-300 min-h-[400px] flex items-center justify-center">
            <div className="text-center text-sm text-gray-600">
              <p>Nodes: {nodes.length} (users, devices, merchants)</p>
              <p>Edges: {edges.length}</p>
              <p>Data from GET /api/v1/gnn/clusters</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Suspicious clusters</h2>
          {clusters.length === 0 ? (
            <p className="text-gray-500">No clusters (no shared devices/merchants with 2+ transactions).</p>
          ) : (
            <div className="space-y-4">
              {clusters.map((cluster) => (
                <div
                  key={cluster.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <span className="text-xl">{cluster.type === 'merchant-ring' ? '🛒' : '👥'}</span>
                    <div>
                      <p className="font-medium text-gray-800">
                        {cluster.type === 'merchant-ring'
                          ? `Merchant Ring: ${cluster.merchants ?? 0} merchants (${cluster.location})`
                          : `Cluster ${cluster.id}: ${cluster.users ?? 0} users, ${cluster.devices ?? 0} devices (${cluster.location})`}
                      </p>
                    </div>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${
                      cluster.risk >= 80 ? 'bg-red-100 text-red-800' : cluster.risk >= 60 ? 'bg-orange-100 text-orange-800' : 'bg-yellow-100 text-yellow-800'
                    }`}
                  >
                    Risk: {cluster.risk}%
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
