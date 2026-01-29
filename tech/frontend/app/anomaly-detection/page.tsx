'use client';

import { useEffect, useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

export default function AnomalyDetectionPage() {
  // API placeholders - replace with actual API calls
  const [chartData, setChartData] = useState(null);
  const [anomalyScores, setAnomalyScores] = useState(null);
  const [alertData, setAlertData] = useState(null);

  useEffect(() => {
    // TODO: Replace with actual API calls
    // Example:
    // fetch('/api/anomaly/chart').then(res => res.json()).then(setChartData);
    // fetch('/api/anomaly/scores').then(res => res.json()).then(setAnomalyScores);
    // fetch('/api/anomaly/alert').then(res => res.json()).then(setAlertData);
  }, []);

  // Mock data - replace with API data
  const anomalyChartData = chartData || [
    { user: 'User A (Mumbai)', score: 92 },
    { user: 'User B (Delhi)', score: 87 },
    { user: 'User C (Bangalore)', score: 34 },
    { user: 'User D (Chennai)', score: 68 },
    { user: 'User E (Kolkata)', score: 91 },
  ];

  const scoresData = anomalyScores || [
    {
      user: 'U-4821 (Mumbai)',
      score: 92,
      pattern: 'Spending Spike',
      status: 'High Risk',
    },
    {
      user: 'U-4822 (Delhi)',
      score: 87,
      pattern: 'Time Anomaly',
      status: 'High Risk',
    },
    {
      user: 'U-4823 (Bangalore)',
      score: 34,
      pattern: 'Normal',
      status: 'Low Risk',
    },
    {
      user: 'U-4824 (Chennai)',
      score: 68,
      pattern: 'Location Jump',
      status: 'Medium Risk',
    },
    {
      user: 'U-4825 (Kolkata)',
      score: 91,
      pattern: 'Velocity',
      status: 'High Risk',
    },
  ];

  const alertInfo = alertData || {
    message:
      'Unusual Pattern Detected: User spending pattern deviates by 3.8σ from normal behavior',
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'High Risk':
        return 'bg-red-100 text-red-800';
      case 'Medium Risk':
        return 'bg-orange-100 text-orange-800';
      case 'Low Risk':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getBarColor = (score: number) => {
    if (score >= 80) return '#ef4444'; // red
    if (score >= 60) return '#f97316'; // orange
    return '#10b981'; // green
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-2 mb-6">
        <span className="text-2xl">📈</span>
        <h1 className="text-3xl font-bold text-gray-800">
          Deep Anomaly Detection
        </h1>
      </div>
      <p className="text-gray-600 mb-6">
        Autoencoder identifying zero-day fraud patterns
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Panel - Chart */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center space-x-2 mb-4">
            <div className="w-3 h-3 bg-red-500 rounded"></div>
            <h3 className="text-lg font-semibold text-gray-800">
              Anomaly Score
            </h3>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={anomalyChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="user"
                stroke="#6b7280"
                angle={-45}
                textAnchor="end"
                height={100}
              />
              <YAxis stroke="#6b7280" domain={[0, 100]} />
              <Tooltip />
              <Bar
                dataKey="score"
                fill={(entry: any) => getBarColor(entry.score)}
                radius={[8, 8, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Right Panel - Alert, Table, Button */}
        <div className="space-y-6">
          {/* Anomaly Alert */}
          <div className="bg-blue-50 border-l-4 border-blue-500 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <span className="text-2xl">⚠️</span>
              <div>
                <h4 className="font-bold text-gray-800 mb-1">
                  Anomaly Detection Alert
                </h4>
                <p className="text-sm text-gray-700">{alertInfo.message}</p>
              </div>
            </div>
          </div>

          {/* Anomaly Scores Table */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">
              Anomaly Scores
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">
                      User
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">
                      Anomaly Score
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">
                      Pattern
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-700">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {scoresData.map((item: any, index: number) => (
                    <tr
                      key={index}
                      className={`border-b border-gray-100 ${
                        index % 2 === 0 ? 'bg-white' : 'bg-gray-50'
                      }`}
                    >
                      <td className="py-3 px-4 text-sm text-gray-800">
                        {item.user}
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center space-x-2">
                          <span className="text-sm font-medium text-gray-800">
                            {item.score}%
                          </span>
                          <div className="flex-1 bg-gray-200 rounded-full h-2 max-w-24">
                            <div
                              className={`h-2 rounded-full ${
                                item.score >= 80
                                  ? 'bg-red-500'
                                  : item.score >= 60
                                  ? 'bg-orange-500'
                                  : 'bg-yellow-500'
                              }`}
                              style={{ width: `${item.score}%` }}
                            ></div>
                          </div>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-700">
                        {item.pattern}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(
                            item.status
                          )}`}
                        >
                          {item.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Run Anomaly Scan Button */}
          <button className="w-full bg-yellow-500 hover:bg-yellow-600 text-white font-semibold py-4 px-6 rounded-lg flex items-center justify-center space-x-2 transition-colors">
            <span>⚡</span>
            <span>Run Anomaly Scan</span>
          </button>
        </div>
      </div>
    </div>
  );
}
