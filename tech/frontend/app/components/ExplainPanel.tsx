'use client';

interface ExplainPanelProps {
  // API placeholder
  transactionData?: {
    id: string;
    amount: string;
    user: string;
  };
  explanation?: string;
  ragData?: {
    similarity: number;
    patternId: string;
    knowledgeBaseSize: number;
  };
}

export default function ExplainPanel({
  transactionData,
  explanation,
  ragData,
}: ExplainPanelProps) {
  // Mock data - replace with API call
  const selectedTransaction = transactionData || {
    id: 'TX-4892',
    amount: '₹9,50,000',
    user: 'Rajesh Kumar',
  };

  const aiExplanation =
    explanation ||
    `**High Risk - Fraud Ring Detected**

(1) Amount (₹9,50,000) is 8.2x user's 30-day average (₹1,15,000)
(2) Originates from IP address previously associated with 3 known fraudulent accounts in Delhi
(3) Transaction time (2:15 AM local) deviates from user's normal pattern (typically 9 AM-6 PM)
(4) Merchant 'Global Imports India' has 12 prior fraud incidents in our database.

**GNN Analysis**: User is part of a 5-account cluster sharing device fingerprints across Mumbai-Delhi corridor.

**RBI Compliance**: Requires SAR filing (over ₹10 lakhs suspicious).

**Recommendation**: Block immediately and flag all connected accounts.`;

  const ragInfo = ragData || {
    similarity: 92,
    patternId: 'RBI-382',
    knowledgeBaseSize: 5000,
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex items-center space-x-2 mb-4">
        <span className="text-2xl">🤖</span>
        <h3 className="text-xl font-bold text-gray-800">
          LLM + RAG Explainability Engine
        </h3>
      </div>
      <p className="text-sm text-gray-600 mb-6">
        Natural language explanations for every fraud decision
      </p>

      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select a transaction to analyze:
        </label>
        <select className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
          <option>
            {selectedTransaction.id}: {selectedTransaction.amount} - User:{' '}
            {selectedTransaction.user}
          </option>
        </select>
      </div>

      <div className="mb-6">
        <div className="flex items-center space-x-2 mb-3">
          <span className="text-lg">💬</span>
          <h4 className="font-semibold text-gray-800">AI Explanation</h4>
        </div>
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans">
            {aiExplanation}
          </pre>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex items-center space-x-2 mb-4">
          <span className="text-xl">📚</span>
          <h4 className="font-semibold text-gray-800">RAG Knowledge Base</h4>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          Retrieving from {ragInfo.knowledgeBaseSize}+ fraud patterns and RBI
          guidelines
        </p>
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-700">Similarity match:</span>
            <span className="text-sm font-medium text-gray-800">
              {ragInfo.similarity}% with RBI Fraud Pattern #{ragInfo.patternId}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full"
              style={{ width: `${ragInfo.similarity}%` }}
            ></div>
          </div>
        </div>
        <div className="mb-4">
          <p className="text-sm font-medium text-gray-700 mb-2">
            Query Examples:
          </p>
          <div className="space-y-2">
            <div className="px-3 py-2 bg-blue-50 border border-blue-200 rounded text-sm text-blue-700 cursor-pointer hover:bg-blue-100">
              Why was transaction {selectedTransaction.id} flagged?
            </div>
            <div className="px-3 py-2 bg-blue-50 border border-blue-200 rounded text-sm text-blue-700 cursor-pointer hover:bg-blue-100">
              Show me similar fraud patterns from last month
            </div>
            <div className="px-3 py-2 bg-blue-50 border border-blue-200 rounded text-sm text-blue-700 cursor-pointer hover:bg-blue-100">
              What RBI regulations apply to this case?
            </div>
          </div>
        </div>
        <div className="flex space-x-2">
          <input
            type="text"
            placeholder="Ask the AI fraud analyst..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center space-x-2">
            <span>🔍</span>
            <span>Q Ask AI Analyst</span>
          </button>
        </div>
      </div>
    </div>
  );
}
