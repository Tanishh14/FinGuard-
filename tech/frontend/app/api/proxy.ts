// API Proxy - Replace with actual backend endpoints
// This file serves as a placeholder for API integration

export const API_ENDPOINTS = {
  // Dashboard endpoints
  dashboard: {
    kpi: '/api/dashboard/kpi',
    chart: '/api/dashboard/chart',
    risk: '/api/dashboard/risk',
    alerts: '/api/dashboard/alerts',
  },
  // Anomaly Detection endpoints
  anomaly: {
    chart: '/api/anomaly/chart',
    scores: '/api/anomaly/scores',
    alert: '/api/anomaly/alert',
  },
  // GNN Detection endpoints
  gnn: {
    graph: '/api/gnn/graph',
    results: '/api/gnn/results',
    features: '/api/gnn/features',
  },
  // Explainability endpoints
  explainability: {
    transactions: '/api/explainability/transactions',
    explanation: '/api/explainability/explanation',
    rag: '/api/explainability/rag',
    notification: '/api/explainability/notification',
  },
  // Live Transactions endpoints
  transactions: {
    live: '/api/transactions/live',
    simulateNormal: '/api/transactions/simulate/normal',
    simulateFraud: '/api/transactions/simulate/fraud',
  },
};

// Example API call function
export async function fetchAPI(endpoint: string, options?: RequestInit) {
  // TODO: Replace with actual backend URL
  const baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  
  try {
    const response = await fetch(`${baseURL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });
    
    if (!response.ok) {
      throw new Error(`API call failed: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}
