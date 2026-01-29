'use client';

import { useEffect, useState } from 'react';

interface Transaction {
  id: string;
  user: string;
  amount: string;
  merchant: string;
  riskScore: number;
  decision: 'Approved' | 'Blocked' | 'Flagged';
}

export default function LiveTransactionsPage() {
  // API placeholders - replace with actual API calls
  const [transactions, setTransactions] = useState<Transaction[] | null>(null);

  useEffect(() => {
    // TODO: Replace with actual API calls
    // Example:
    // fetch('/api/transactions/live').then(res => res.json()).then(setTransactions);
  }, []);

  // Mock data - replace with API data
  const transactionData: Transaction[] = transactions || [
    {
      id: 'TX-9481',
      user: 'Vikram Patel',
      amount: '₹3117',
      merchant: 'BigBasket',
      riskScore: 26,
      decision: 'Approved',
    },
    {
      id: 'TX-7197',
      user: 'Arun Joshi',
      amount: '₹2090',
      merchant: 'Amazon India',
      riskScore: 12,
      decision: 'Approved',
    },
    {
      id: 'TX-4821',
      user: 'Sneha Reddy',
      amount: '₹1433986',
      merchant: 'Crypto Exchange IN',
      riskScore: 90,
      decision: 'Blocked',
    },
    {
      id: 'TX-3847',
      user: 'Rajesh Kumar',
      amount: '₹950000',
      merchant: 'Fake GST Merchant',
      riskScore: 96,
      decision: 'Blocked',
    },
    {
      id: 'TX-5623',
      user: 'Priya Sharma',
      amount: '₹4500',
      merchant: 'Flipkart',
      riskScore: 21,
      decision: 'Approved',
    },
    {
      id: 'TX-8921',
      user: 'Amit Singh',
      amount: '₹12500',
      merchant: 'Suspicious Merchant',
      riskScore: 87,
      decision: 'Flagged',
    },
    {
      id: 'TX-3456',
      user: 'Kavita Mehta',
      amount: '₹3200',
      merchant: 'Zomato',
      riskScore: 29,
      decision: 'Approved',
    },
    {
      id: 'TX-7890',
      user: 'Rohit Verma',
      amount: '₹85000',
      merchant: 'Unknown Merchant',
      riskScore: 81,
      decision: 'Blocked',
    },
    {
      id: 'TX-2345',
      user: 'Anjali Desai',
      amount: '₹2100',
      merchant: 'Swiggy',
      riskScore: 15,
      decision: 'Approved',
    },
    {
      id: 'TX-6789',
      user: 'Suresh Iyer',
      amount: '₹650000',
      merchant: 'Fraudulent Merchant',
      riskScore: 94,
      decision: 'Blocked',
    },
  ];

  const getRiskColor = (score: number) => {
    if (score >= 80) return 'bg-red-500';
    if (score >= 60) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getDecisionBadge = (decision: string) => {
    switch (decision) {
      case 'Approved':
        return 'bg-green-100 text-green-800';
      case 'Blocked':
        return 'bg-red-100 text-red-800';
      case 'Flagged':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center space-x-2 mb-2">
          <span className="text-2xl">⚡</span>
          <h1 className="text-3xl font-bold text-gray-800">
            Live Transaction Monitoring
          </h1>
        </div>
        <p className="text-gray-600">
          Real-time fraud scoring and alerts
        </p>
      </div>

      {/* Transaction Table */}
      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                  Transaction ID
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                  Amount
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                  Merchant
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                  Risk Score
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                  AI Decision
                </th>
                <th className="px-6 py-4 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {transactionData.map((tx, index) => (
                <tr
                  key={tx.id}
                  className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}
                >
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {tx.id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-800">
                    {tx.user}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-800">
                    {tx.amount}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-800">
                    {tx.merchant}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-medium text-gray-800">
                        {tx.riskScore}%
                      </span>
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${getRiskColor(
                            tx.riskScore
                          )}`}
                          style={{ width: `${tx.riskScore}%` }}
                        ></div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-medium ${getDecisionBadge(
                        tx.decision
                      )}`}
                    >
                      {tx.decision}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <button className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded">
                      🔍
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Simulation Buttons */}
      <div className="flex justify-center space-x-4">
        <button className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg flex items-center space-x-2">
          <span>✓</span>
          <span>Simulate Normal TX</span>
        </button>
        <button className="bg-red-600 hover:bg-red-700 text-white font-semibold py-3 px-6 rounded-lg flex items-center space-x-2">
          <span>☠️</span>
          <span>Simulate Fraud TX</span>
        </button>
      </div>
    </div>
  );
}
