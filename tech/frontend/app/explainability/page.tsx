'use client';

import ExplainPanel from '../components/ExplainPanel';
import { useEffect, useState } from 'react';

export default function ExplainabilityPage() {
  // API placeholders - replace with actual API calls
  const [transactionData, setTransactionData] = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [ragData, setRagData] = useState(null);
  const [notification, setNotification] = useState(null);

  useEffect(() => {
    // TODO: Replace with actual API calls
    // Example:
    // fetch('/api/explainability/transactions').then(res => res.json()).then(setTransactionData);
    // fetch('/api/explainability/explanation').then(res => res.json()).then(setExplanation);
    // fetch('/api/explainability/rag').then(res => res.json()).then(setRagData);
    // fetch('/api/explainability/notification').then(res => res.json()).then(setNotification);
  }, []);

  // Mock notification data
  const notificationData = notification || {
    transactionId: 'TX-9481',
    user: 'Vikram Patel',
    location: 'Delhi',
    riskScore: 26,
    decision: 'auto-approved',
  };

  return (
    <div className="space-y-6">
      {/* Floating Notification */}
      {notificationData && (
        <div className="fixed top-24 right-6 bg-green-50 border-2 border-green-300 rounded-lg p-4 shadow-lg z-50 max-w-sm">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-800">
                Transaction {notificationData.transactionId} from{' '}
                {notificationData.user} in {notificationData.location}{' '}
                {notificationData.decision} with {notificationData.riskScore}%
                risk score
              </p>
            </div>
            <button
              onClick={() => setNotification(null)}
              className="text-gray-400 hover:text-gray-600 ml-2"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Main Content */}
      <ExplainPanel
        transactionData={transactionData}
        explanation={explanation}
        ragData={ragData}
      />
    </div>
  );
}
