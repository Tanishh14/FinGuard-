'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface RiskTrendChartProps {
  // API placeholder
  data?: Array<{
    time: string;
    fraudAttempts: number;
    legitimateTransactions: number;
  }>;
}

export default function RiskTrendChart({ data }: RiskTrendChartProps) {
  // Mock data - replace with API call
  const chartData = data || [
    { time: '00:00', fraudAttempts: 50, legitimateTransactions: 250 },
    { time: '04:00', fraudAttempts: 45, legitimateTransactions: 200 },
    { time: '08:00', fraudAttempts: 60, legitimateTransactions: 300 },
    { time: '12:00', fraudAttempts: 55, legitimateTransactions: 450 },
    { time: '16:00', fraudAttempts: 70, legitimateTransactions: 600 },
    { time: '20:00', fraudAttempts: 65, legitimateTransactions: 750 },
  ];

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">
        Real-time Fraud Dashboard
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="time" stroke="#6b7280" />
          <YAxis stroke="#6b7280" domain={[0, 800]} />
          <Tooltip />
          <Legend />
          <Line
            type="monotone"
            dataKey="fraudAttempts"
            stroke="#ef4444"
            strokeWidth={2}
            name="Fraud Attempts"
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="legitimateTransactions"
            stroke="#10b981"
            strokeWidth={2}
            name="Legitimate Transactions"
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
