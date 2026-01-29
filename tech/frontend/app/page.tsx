'use client';

import RiskScoreCard from './components/RiskScoreCard';
import RiskTrendChart from './components/RiskTrendChart';
import FraudMap from './components/FraudMap';
import AlertTable from './components/AlertTable';
import { useEffect, useState } from 'react';

export default function DashboardPage() {
  // API placeholders - replace with actual API calls
  const [kpiData, setKpiData] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [riskData, setRiskData] = useState(null);
  const [alerts, setAlerts] = useState(null);

  useEffect(() => {
    // TODO: Replace with actual API calls
    // Example:
    // fetch('/api/dashboard/kpi').then(res => res.json()).then(setKpiData);
    // fetch('/api/dashboard/chart').then(res => res.json()).then(setChartData);
    // fetch('/api/dashboard/risk').then(res => res.json()).then(setRiskData);
    // fetch('/api/dashboard/alerts').then(res => res.json()).then(setAlerts);
  }, []);

  return (
    <div className="space-y-6">
      {/* High-Risk Activity Alert Banner */}
      <div className="bg-gray-100 border-l-4 border-red-500 rounded-lg p-4 flex items-center space-x-3">
        <span className="text-2xl">⚠️</span>
        <div>
          <p className="font-semibold text-gray-800">
            High-Risk Activity Detected: Fraud ring detected in E-commerce
            sector
          </p>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <RiskScoreCard
          title="TOTAL TRANSACTIONS"
          value="42,857"
          subtitle="+2.3% fraud attempts"
          color="red"
          data={kpiData?.transactions}
        />
        <RiskScoreCard
          title="FRAUD DETECTED"
          value="₹1.2 Cr"
          subtitle="₹8.5 Cr saved today"
          color="orange"
          data={kpiData?.fraud}
        />
        <RiskScoreCard
          title="DETECTION ACCURACY"
          value="94.7%"
          subtitle="+8.2% vs industry avg"
          color="green"
          data={kpiData?.accuracy}
        />
        <RiskScoreCard
          title="AVG RESPONSE TIME"
          value="47ms"
          subtitle="Real-time analysis"
          color="blue"
          data={kpiData?.responseTime}
        />
      </div>

      {/* Fraud Alert Popup */}
      <div className="fixed top-24 right-6 bg-red-50 border-2 border-red-300 rounded-lg p-4 shadow-lg z-50 max-w-sm">
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3">
            <span className="text-2xl">⚠️</span>
            <div>
              <h4 className="font-bold text-red-800 mb-1">FRAUD DETECTED</h4>
              <p className="text-sm text-gray-700">
                Transaction TX-4674 from Rajesh Kumar in Jaipur blocked with
                96% risk score! RBI alert generated.
              </p>
            </div>
          </div>
          <button className="text-gray-400 hover:text-gray-600">✕</button>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RiskTrendChart data={chartData} />
        <FraudMap data={riskData} />
      </div>

      {/* Recent Alerts */}
      <AlertTable alerts={alerts} />
    </div>
  );
}
