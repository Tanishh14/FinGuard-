'use client';

interface FraudMapProps {
  // API placeholder
  data?: {
    lowRisk: number;
    mediumRisk: number;
    highRisk: number;
  };
}

export default function FraudMap({ data }: FraudMapProps) {
  // Mock data - replace with API call
  const riskData = data || {
    lowRisk: 65,
    mediumRisk: 22,
    highRisk: 13,
  };

  const total = riskData.lowRisk + riskData.mediumRisk + riskData.highRisk;
  const lowRiskPercent = (riskData.lowRisk / total) * 100;
  const mediumRiskPercent = (riskData.mediumRisk / total) * 100;
  const highRiskPercent = (riskData.highRisk / total) * 100;

  // Calculate angles for donut chart
  const circumference = 2 * Math.PI * 90; // radius = 90
  const lowRiskOffset = circumference - (lowRiskPercent / 100) * circumference;
  const mediumRiskOffset =
    circumference -
    ((lowRiskPercent + mediumRiskPercent) / 100) * circumference;
  const highRiskOffset = circumference - ((highRiskPercent / 100) * circumference);

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-4">
        Risk Distribution
      </h3>
      <div className="flex items-center justify-center">
        <div className="relative w-64 h-64">
          <svg className="transform -rotate-90" width="256" height="256">
            {/* Low Risk - Green */}
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
            {/* Medium Risk - Orange */}
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
            {/* High Risk - Red */}
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
              <p className="text-3xl font-bold text-gray-800">{total}%</p>
              <p className="text-sm text-gray-600">Total Risk</p>
            </div>
          </div>
        </div>
      </div>
      <div className="mt-6 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-green-600 rounded"></div>
            <span className="text-sm text-gray-700">Low Risk</span>
          </div>
          <span className="text-sm font-medium text-gray-800">
            {lowRiskPercent.toFixed(1)}%
          </span>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-orange-500 rounded"></div>
            <span className="text-sm text-gray-700">Medium Risk</span>
          </div>
          <span className="text-sm font-medium text-gray-800">
            {mediumRiskPercent.toFixed(1)}%
          </span>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-red-600 rounded"></div>
            <span className="text-sm text-gray-700">High Risk</span>
          </div>
          <span className="text-sm font-medium text-gray-800">
            {highRiskPercent.toFixed(1)}%
          </span>
        </div>
      </div>
    </div>
  );
}
