'use client';

interface ExplainPanelProps {
  transactionId?: string;
  explanation?: string;
  confidence?: number;
  loading?: boolean;
  error?: string;
}

export default function ExplainPanel({
  transactionId,
  explanation,
  confidence,
  loading,
  error,
}: ExplainPanelProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-4">Explainability (from backend)</h3>
        <p className="text-gray-600">Loading explanation…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-4">Explainability (from backend)</h3>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 font-medium">Error</p>
          <p className="text-sm text-red-700">{error}</p>
          <p className="text-sm text-gray-600 mt-2">No mock data. Ensure backend and explainability service are running.</p>
        </div>
      </div>
    );
  }

  if (!transactionId && !explanation) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-4">Explainability (from backend)</h3>
        <p className="text-gray-600">
          Add <code className="bg-gray-100 px-1">?tx=TRANSACTION_ID</code> to the URL or open a transaction from Live Transactions to load explanation from backend.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex items-center space-x-2 mb-4">
        <span className="text-2xl">🤖</span>
        <h3 className="text-xl font-bold text-gray-800">Explainability (from backend)</h3>
      </div>
      <p className="text-sm text-gray-600 mb-6">Natural language explanation from backend API. No mock data.</p>

      {transactionId && (
        <p className="text-sm text-gray-700 mb-2">Transaction: <strong>{transactionId}</strong></p>
      )}

      <div className="mb-6">
        <h4 className="font-semibold text-gray-800 mb-2">AI Explanation</h4>
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans">
            {explanation || 'No explanation available for this transaction.'}
          </pre>
        </div>
      </div>

      {confidence != null && (
        <p className="text-sm text-gray-600">Confidence: {(confidence * 100).toFixed(0)}%</p>
      )}
    </div>
  );
}
