'use client';

import type { FraudAlertResponse } from '../lib/api';

interface AlertTableProps {
  alerts: FraudAlertResponse[];
}

export default function AlertTable({ alerts }: AlertTableProps) {
  const getIconColor = (severity: string) => {
    if (severity === 'high' || severity === 'critical') return 'bg-red-100 text-red-600';
    if (severity === 'medium') return 'bg-yellow-100 text-yellow-600';
    return 'bg-gray-100 text-gray-600';
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex items-center space-x-2 mb-6">
        <span className="text-2xl">🔔</span>
        <h3 className="text-xl font-bold text-gray-800">Recent Alerts (from backend)</h3>
      </div>
      <div className="space-y-4">
        {alerts.length === 0 ? (
          <p className="text-sm text-gray-500">No alerts. Data comes from backend only.</p>
        ) : (
          alerts.map((alert, index) => (
            <div key={alert.alert_id}>
              <div className="flex items-start space-x-4 py-3">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center ${getIconColor(
                    alert.severity
                  )}`}
                >
                  <span className="text-lg">⚠️</span>
                </div>
                <div className="flex-1">
                  <h4 className="font-bold text-gray-800 mb-1">{alert.alert_type}</h4>
                  <p className="text-sm text-gray-600">{alert.message}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {alert.transaction_id} · {alert.merchant_id} · {alert.risk_score.toFixed(0)}% · {alert.created_at}
                  </p>
                </div>
              </div>
              {index < alerts.length - 1 && <div className="border-b border-gray-200" />}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
