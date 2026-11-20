import { AnalyzeRequest, AnalyzeResponse, DashboardStats, ScanRecord, EvaluationMetrics } from '../types';

const BASE_URL = import.meta.env.VITE_API_URL || '';

export async function analyzeText(request: AnalyzeRequest): Promise<AnalyzeResponse> {
  const response = await fetch(`${BASE_URL}/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Failed to analyze text' }));
    throw new Error(err.detail || `Server error (${response.status})`);
  }

  return response.json();
}

export async function getStats(): Promise<DashboardStats> {
  const response = await fetch(`${BASE_URL}/stats`);
  if (!response.ok) {
    throw new Error('Failed to fetch dashboard statistics');
  }
  return response.json();
}

export async function getScans(limit = 50, offset = 0): Promise<ScanRecord[]> {
  const response = await fetch(`${BASE_URL}/scans?limit=${limit}&offset=${offset}`);
  if (!response.ok) {
    throw new Error('Failed to fetch scan history');
  }
  return response.json();
}

export async function clearScans(): Promise<{ status: string; cleared_records: number }> {
  const response = await fetch(`${BASE_URL}/scans`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to clear scan history');
  }
  return response.json();
}

export async function getEvaluationReport(): Promise<EvaluationMetrics> {
  const response = await fetch(`${BASE_URL}/evaluation/report`);
  if (!response.ok) {
    throw new Error('Failed to fetch evaluation report');
  }
  return response.json();
}

export async function triggerEvaluation(): Promise<{ status: string; report: EvaluationMetrics }> {
  const response = await fetch(`${BASE_URL}/evaluation/run`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error('Failed to execute evaluation pipeline');
  }
  return response.json();
}

export async function checkHealth(): Promise<{ status: string; model_status: string }> {
  const response = await fetch(`${BASE_URL}/health`);
  if (!response.ok) {
    throw new Error('Health check failed');
  }
  return response.json();
}
