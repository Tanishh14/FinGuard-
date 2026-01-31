/**
 * Backend API endpoints. Frontend ONLY talks to backend; no direct ML or DB.
 * Use app/lib/api.ts for authenticated requests (login, predict/fraud, explain).
 */

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_V1 = `${BASE}/api/v1`;

export const API_ENDPOINTS = {
  auth: { login: `${API_V1}/auth/login` },
  predict: { fraud: `${API_V1}/predict/fraud` },
  explain: (txId: string) => `${API_V1}/explain/${encodeURIComponent(txId)}`,
  health: `${BASE}/health`,
  transactions: `${API_V1}/transactions`,
  dashboard: { stats: `${API_V1}/transactions/stats/dashboard` },
  alerts: { recent: `${API_V1}/transactions/alerts/recent` },
};

export async function fetchAPI(endpoint: string, options?: RequestInit) {
  const token = typeof window !== 'undefined' ? localStorage.getItem('finguard_token') : null;
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string>),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(endpoint.startsWith('http') ? endpoint : `${BASE}${endpoint}`, {
    ...options,
    headers,
  });
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
  return res.json();
}
