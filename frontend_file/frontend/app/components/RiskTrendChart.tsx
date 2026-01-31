'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface RiskTrendChartProps {
  data: Array<{
    time: string;
    fraudAttempts: number;
    legitimateTransactions: number;
  }>;
}

export default function RiskTrendChart({ data }: RiskTrendChartProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">Risk trend (from backend)</h3>
      {data.length === 0 ? (
        <p className="text-sm text-gray-500 py-8">No trend data. Data comes from backend only.</p>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="time" stroke="#6b7280" />
            <YAxis stroke="#6b7280" domain={[0, 'auto']} />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="fraudAttempts"
              stroke="#ef4444"
              strokeWidth={2}
              name="Fraud"
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="legitimateTransactions"
              stroke="#10b981"
              strokeWidth={2}
              name="Legitimate"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
