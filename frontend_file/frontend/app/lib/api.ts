/**
 * Backend-only API client. All UI data comes from these calls.
 * JWT in memory + localStorage; Authorization header on every request.
 * In browser we use same-origin (/api/v1) so Next.js rewrites proxy to backend; avoids CORS.
 */

const getBase = (): string => {
  if (typeof window !== 'undefined') {
    return ''; // browser: use same-origin so Next.js rewrites proxy to backend
  }
  return (
    (typeof process !== 'undefined' && process.env?.NEXT_PUBLIC_API_URL) ||
    (typeof process !== 'undefined' && process.env?.VITE_API_BASE_URL) ||
    'http://localhost:8000'
  );
};
const BASE = getBase();
const API_V1 = BASE ? `${BASE}/api/v1` : '/api/v1';

let token: string | null =
  typeof window !== 'undefined' ? localStorage.getItem('finguard_token') : null;

export function setToken(t: string) {
  token = t;
  if (typeof window !== 'undefined') localStorage.setItem('finguard_token', t);
}

export function getToken() {
  if (typeof window !== 'undefined' && !token) token = localStorage.getItem('finguard_token');
  return token;
}

export function clearToken() {
  token = null;
  if (typeof window !== 'undefined') localStorage.removeItem('finguard_token');
}

async function request<T>(
  path: string,
  options: RequestInit & { skipAuth?: boolean } = {}
): Promise<T> {
  const { skipAuth, ...init } = options;
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(init.headers as Record<string, string>),
  };
  const t = getToken();
  if (!skipAuth && t) headers['Authorization'] = `Bearer ${t}`;

  const url = path.startsWith('http') ? path : `${API_V1}${path}`;
  let res: Response;
  try {
    res = await fetch(url, { ...init, headers });
  } catch (e) {
    const msg = e instanceof Error ? e.message : 'Network error';
    if (msg === 'Failed to fetch' || msg.includes('NetworkError') || msg.includes('Load failed')) {
      throw new Error(
        'Backend unreachable. Ensure the backend is running (e.g. uvicorn on port 8000) and NEXT_PUBLIC_API_URL is correct.'
      );
    }
    throw e;
  }
  if (res.status === 401) clearToken();
  if (!res.ok) {
    if (res.status === 502 || res.status === 503 || res.status === 504) {
      throw new Error(
        'Backend unreachable. Ensure the backend is running (e.g. uvicorn on port 8000) and NEXT_PUBLIC_API_URL is correct.'
      );
    }
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const message =
      res.status === 401 ? 'Authentication required' : ((err as { detail?: string }).detail || res.statusText);
    throw new Error(message);
  }
  return res.json() as Promise<T>;
}

export interface PredictFraudRequest {
  transaction_id: string;
  user_id: string;
  amount: number;
  timestamp: string;
  merchant: string;
  device_id: string;
  ip_address: string;
}

export interface ModelScores {
  autoencoder: number;
  isolation_forest: number;
  gnn: number;
}

export interface PredictFraudResponse {
  transaction_id: string;
  fraud_score: number;
  risk_label: 'LOW' | 'MEDIUM' | 'HIGH';
  model_scores: ModelScores;
}

export interface ExplanationResponse {
  transaction_id: string;
  summary: string;
  reasons: { reason: string; severity: string; impact_score?: number }[];
  suggested_actions: { action: string; priority: string; description?: string }[];
  confidence: number;
  model_used?: string;
}

export interface TransactionItem {
  transaction_id: string;
  amount: number;
  currency: string;
  merchant_id: string;
  transaction_time: string;
  risk_score: number;
  risk_level: string;
  is_fraudulent: boolean;
}

export interface TransactionListResponse {
  items: TransactionItem[];
  total: number;
  page: number;
  pages: number;
  has_more: boolean;
}

export interface TransactionStats {
  total_transactions: number;
  today_transactions: number;
  fraudulent_transactions: number;
  high_risk_transactions: number;
  total_amount: number;
  fraud_amount: number;
  avg_risk_score: number;
  risk_score_distribution: Record<string, number>;
}

export interface FraudAlertResponse {
  alert_id: string;
  transaction_id: string;
  amount: number;
  merchant_id: string;
  risk_score: number;
  risk_level: string;
  alert_type: string;
  severity: string;
  message: string;
  created_at: string;
  status: string;
}

export interface DashboardMetrics {
  total_transactions: number;
  flagged_transactions: number;
  high_risk_percentage: number;
}

export interface AnomalySummary {
  chart_data: { user: string; score: number }[];
  scores: { user: string; score: number; pattern?: string; status?: string }[];
  alert: { message: string };
}

export interface GnnClustersResponse {
  nodes: { id: string; type: string; label: string }[];
  edges: { source: string; target: string }[];
  clusters: { id: string; type: string; users?: number; devices?: number; merchants?: number; location: string; risk: number }[];
}

export const api = {
  health: () => request<{ status: string; service?: string }>('/health', { skipAuth: true }),

  login: (username: string, password: string) =>
    request<{ access_token: string; token_type: string; expires_in_minutes: number }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
      skipAuth: true,
    }),

  predictFraud: (body: PredictFraudRequest) =>
    request<PredictFraudResponse>('/predict/fraud', { method: 'POST', body: JSON.stringify(body) }),

  getExplanation: (transactionId: string) =>
    request<ExplanationResponse>(`/explain/${encodeURIComponent(transactionId)}`),

  listTransactions: (params?: { skip?: number; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.skip != null) q.set('skip', String(params.skip));
    if (params?.limit != null) q.set('limit', String(params.limit));
    return request<TransactionListResponse>(`/transactions?${q}`);
  },

  getDashboardStats: () => request<TransactionStats>('/transactions/stats/dashboard'),

  getAlertsRecent: (limit?: number) => {
    const q = limit != null ? `?limit=${limit}` : '';
    return request<FraudAlertResponse[]>(`/transactions/alerts/recent${q}`);
  },

  getRiskTrends: (days?: number) => {
    const q = days != null ? `?days=${days}` : '';
    return request<{ date: string; total_transactions: number; avg_risk_score: number; fraudulent_transactions: number }[]>(`/transactions/trends/risk${q}`);
  },

  getDashboardMetrics: () => request<DashboardMetrics>('/dashboard/metrics'),

  getAnomalySummary: () => request<AnomalySummary>('/anomaly/summary'),

  getGnnClusters: () => request<GnnClustersResponse>('/gnn/clusters'),
};
