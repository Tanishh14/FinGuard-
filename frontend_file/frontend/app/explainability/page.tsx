'use client';

import ExplainPanel from '../components/ExplainPanel';
import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { api } from '../lib/api';

export default function ExplainabilityPage() {
  const searchParams = useSearchParams();
  const txId = searchParams.get('tx');
  const [loading, setLoading] = useState(!!txId);
  const [error, setError] = useState('');
  const [transactionId, setTransactionId] = useState<string | undefined>();
  const [summary, setSummary] = useState<string | undefined>();
  const [confidence, setConfidence] = useState<number | undefined>();

  const REFRESH_INTERVAL_MS = 30000;

  useEffect(() => {
    if (!txId) {
      setLoading(false);
      return;
    }
    let isFirst = true;
    function fetchExplanation() {
      if (isFirst) setLoading(true);
      setError('');
      api.getExplanation(txId!)
        .then((res) => {
          setTransactionId(res.transaction_id);
          setSummary(res.summary);
          setConfidence(res.confidence);
        })
        .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load explanation'))
        .finally(() => {
          setLoading(false);
          isFirst = false;
        });
    }
    fetchExplanation();
    const interval = setInterval(fetchExplanation, REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [txId]);

  return (
    <div className="space-y-6">
      {txId && !loading && !error && (
        <p className="text-sm text-gray-600">
          Explanation for transaction: <strong>{txId}</strong> (from backend)
        </p>
      )}
      {!txId && (
        <p className="text-sm text-gray-600">
          Add <code className="bg-gray-100 px-1">?tx=TRANSACTION_ID</code> to the URL or use the link from a submitted transaction. No mock data.
        </p>
      )}
      <ExplainPanel
        transactionId={transactionId}
        explanation={summary}
        confidence={confidence}
        loading={loading}
        error={error || undefined}
      />
    </div>
  );
}
