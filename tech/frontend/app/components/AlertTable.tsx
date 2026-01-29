'use client';

interface Alert {
  id: string;
  type: 'high-risk' | 'new-pattern' | 'model-update';
  title: string;
  description: string;
  icon: string;
}

interface AlertTableProps {
  // API placeholder
  alerts?: Alert[];
}

export default function AlertTable({ alerts }: AlertTableProps) {
  // Mock data - replace with API call
  const alertData: Alert[] =
    alerts || [
      {
        id: '1',
        type: 'high-risk',
        title: 'High-risk transaction blocked',
        description:
          'TX-4892: ₹9,50,000 flagged by GNN fraud ring detection',
        icon: '⚠️',
      },
      {
        id: '2',
        type: 'new-pattern',
        title: 'New fraud pattern detected',
        description:
          'Autoencoder identified new merchant collusion pattern in Gujarat',
        icon: '🔍',
      },
      {
        id: '3',
        type: 'model-update',
        title: 'Model retrained successfully',
        description:
          'Adaptive learning loop updated with 312 new fraud cases from Indian banks',
        icon: '✅',
      },
    ];

  const getIconColor = (type: string) => {
    switch (type) {
      case 'high-risk':
        return 'bg-red-100 text-red-600';
      case 'new-pattern':
        return 'bg-yellow-100 text-yellow-600';
      case 'model-update':
        return 'bg-green-100 text-green-600';
      default:
        return 'bg-gray-100 text-gray-600';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex items-center space-x-2 mb-6">
        <span className="text-2xl">🔔</span>
        <h3 className="text-xl font-bold text-gray-800">Recent Alerts</h3>
      </div>
      <div className="space-y-4">
        {alertData.map((alert, index) => (
          <div key={alert.id}>
            <div className="flex items-start space-x-4 py-3">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center ${getIconColor(
                  alert.type
                )}`}
              >
                <span className="text-lg">{alert.icon}</span>
              </div>
              <div className="flex-1">
                <h4 className="font-bold text-gray-800 mb-1">{alert.title}</h4>
                <p className="text-sm text-gray-600">{alert.description}</p>
              </div>
            </div>
            {index < alertData.length - 1 && (
              <div className="border-b border-gray-200"></div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
