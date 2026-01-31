'use client';

interface FraudMapProps {
  data: {
    lowRisk: number;
    mediumRisk: number;
    highRisk: number;
  };
}

export default function FraudMap({ data }: FraudMapProps) {
  const total = data.lowRisk + data.mediumRisk + data.highRisk;
  const lowRiskPercent = total > 0 ? (data.lowRisk / total) * 100 : 0;
  const mediumRiskPercent = total > 0 ? (data.mediumRisk / total) * 100 : 0;
  const highRiskPercent = total > 0 ? (data.highRisk / total) * 100 : 0;

  const circumference = 2 * Math.PI * 90;
  const lowRiskOffset = circumference - (lowRiskPercent / 100) * circumference;
  const mediumRiskOffset =
    circumference - ((lowRiskPercent + mediumRiskPercent) / 100) * circumference;
  const highRiskOffset = circumference - ((highRiskPercent / 100) * circumference);

  const isEmpty = total === 0;

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">Risk distribution (from backend)</h3>
      {isEmpty ? (
        <p className="text-sm text-gray-500 py-8">No distribution data. Data comes from backend only.</p>
      ) : (
        <>
          <div className="flex items-center justify-center">
            <div className="relative w-64 h-64">
              <svg className="transform -rotate-90" width="256" height="256">
                <circle
                  cx="128"
                  cy="128"
                  r="90"
                  fill="none"
                  stroke="#10b981"
                  strokeWidth="40"
                  strokeDasharray={circumference}
                  strokeDashoffset={lowRiskOffset}
                />
                <circle
                  cx="128"
                  cy="128"
                  r="90"
                  fill="none"
                  stroke="#f97316"
                  strokeWidth="40"
                  strokeDasharray={circumference}
                  strokeDashoffset={mediumRiskOffset}
                />
                <circle
                  cx="128"
                  cy="128"
                  r="90"
                  fill="none"
                  stroke="#ef4444"
                  strokeWidth="40"
                  strokeDasharray={circumference}
                  strokeDashoffset={highRiskOffset}
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <p className="text-3xl font-bold text-gray-800">{total.toFixed(0)}%</p>
                  <p className="text-sm text-gray-600">Total</p>
                </div>
              </div>
            </div>
          </div>
          <div className="mt-6 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 bg-green-600 rounded" />
                <span className="text-sm text-gray-700">Low</span>
              </div>
              <span className="text-sm font-medium text-gray-800">{lowRiskPercent.toFixed(1)}%</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 bg-orange-500 rounded" />
                <span className="text-sm text-gray-700">Medium</span>
              </div>
              <span className="text-sm font-medium text-gray-800">{mediumRiskPercent.toFixed(1)}%</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 bg-red-600 rounded" />
                <span className="text-sm text-gray-700">High</span>
              </div>
              <span className="text-sm font-medium text-gray-800">{highRiskPercent.toFixed(1)}%</span>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
