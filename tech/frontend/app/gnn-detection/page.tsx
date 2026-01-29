'use client';

import { useEffect, useState } from 'react';

export default function GnnDetectionPage() {
  // API placeholders - replace with actual API calls
  const [graphData, setGraphData] = useState(null);
  const [detectionResults, setDetectionResults] = useState(null);
  const [features, setFeatures] = useState(null);

  useEffect(() => {
    // TODO: Replace with actual API calls
    // Example:
    // fetch('/api/gnn/graph').then(res => res.json()).then(setGraphData);
    // fetch('/api/gnn/results').then(res => res.json()).then(setDetectionResults);
    // fetch('/api/gnn/features').then(res => res.json()).then(setFeatures);
  }, []);

  // Mock data - replace with API data
  const clusters = detectionResults || [
    {
      id: 'A',
      users: 8,
      devices: 3,
      location: 'Mumbai',
      risk: 92,
      type: 'user-cluster',
    },
    {
      id: 'B',
      users: 5,
      ips: 2,
      location: 'Delhi-NCR',
      risk: 68,
      type: 'user-cluster',
    },
    {
      id: 'C',
      merchants: 3,
      location: 'Bangalore',
      risk: 87,
      type: 'merchant-ring',
    },
  ];

  const keyFeatures = features || [
    {
      title: 'Graph Neural Networks',
      description: 'Detect coordinated fraud rings and complex networks',
      icon: '🕸️',
    },
    {
      title: 'Deep Anomaly Detection',
      description: 'Autoencoders for zero-day fraud pattern detection',
      icon: '🧠',
    },
    {
      title: 'LLM + RAG Explainability',
      description: 'Natural language explanations for every decision',
      icon: '🤖',
    },
    {
      title: 'Real-time Processing',
      description: '47ms average response time for live transactions',
      icon: '⚡',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Panel - Graph Visualization */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center space-x-2 mb-2">
            <span className="text-2xl">🕸️</span>
            <h2 className="text-xl font-bold text-gray-800">
              Graph Neural Network Detection
            </h2>
          </div>
          <p className="text-sm text-gray-600 mb-6">
            Detecting coordinated fraud rings across users, devices, and
            merchants
          </p>

          {/* Graph Visualization Placeholder */}
          <div className="bg-gray-50 rounded-lg p-8 border-2 border-dashed border-gray-300 min-h-[400px] flex items-center justify-center">
            <div className="text-center">
              <div className="text-4xl mb-4">🕸️</div>
              <p className="text-gray-600 mb-2">
                Graph Visualization (Interactive)
              </p>
              <p className="text-sm text-gray-500">
                {/* API placeholder for graph nodes and edges */}
                Nodes: Users (red), Merchants (blue), Devices (green), IPs
                (diamond)
                <br />
                Edges: Connections between entities
                <br />
                {/* TODO: Replace with actual graph visualization library like vis.js, cytoscape, or d3.js */}
                {/* Data structure: graphData.nodes, graphData.edges */}
              </p>
            </div>
          </div>
        </div>

        {/* Right Panel - Detection Results */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center space-x-2 mb-4">
            <span className="text-xl">🔍</span>
            <h2 className="text-xl font-bold text-gray-800">
              GNN Detection Results
            </h2>
          </div>

          {/* Highlighted Info Box */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <p className="text-sm text-gray-800">
              <strong>Fraud Ring Identified:</strong> Cluster of 8 users
              sharing 3 device IDs across 5 merchants
            </p>
          </div>

          {/* Suspicious Clusters */}
          <h3 className="text-lg font-semibold text-gray-800 mb-4">
            Suspicious Clusters Detected
          </h3>
          <div className="space-y-4 mb-6">
            {clusters.map((cluster: any) => (
              <div
                key={cluster.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  <span className="text-xl">
                    {cluster.type === 'merchant-ring' ? '🛒' : '👥'}
                  </span>
                  <div>
                    <p className="font-medium text-gray-800">
                      {cluster.type === 'merchant-ring'
                        ? `Merchant Ring: ${cluster.merchants} fake merchants (${cluster.location})`
                        : `Cluster ${cluster.id}: ${cluster.users} users, ${
                            cluster.devices || cluster.ips
                          } ${cluster.devices ? 'devices' : 'IPs'} (${
                            cluster.location
                          })`}
                    </p>
                  </div>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    cluster.risk >= 80
                      ? 'bg-red-100 text-red-800'
                      : cluster.risk >= 60
                      ? 'bg-orange-100 text-orange-800'
                      : 'bg-yellow-100 text-yellow-800'
                  }`}
                >
                  Risk: {cluster.risk}%
                </span>
              </div>
            ))}
          </div>

          {/* Run GNN Analysis Button */}
          <button className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg flex items-center justify-center space-x-2 transition-colors">
            <span>🔍</span>
            <span>Run GNN Analysis</span>
          </button>
        </div>
      </div>

      {/* Key Features Section */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center space-x-2 mb-6">
          <span className="text-xl">⭐</span>
          <h2 className="text-xl font-bold text-gray-800">Key Features</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {keyFeatures.map((feature: any, index: number) => (
            <div
              key={index}
              className="bg-gray-50 rounded-lg p-6 border border-gray-200"
            >
              <div className="text-3xl mb-3">{feature.icon}</div>
              <h3 className="font-semibold text-gray-800 mb-2">
                {feature.title}
              </h3>
              <p className="text-sm text-gray-600">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
