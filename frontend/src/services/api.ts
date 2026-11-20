import { AnalyzeRequest, AnalyzeResponse, DashboardStats, ScanRecord, EvaluationMetrics } from '../types';

export function getApiBaseUrl(): string {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL.replace(/\/$/, '');
  }

  if (typeof window !== 'undefined') {
    const port = window.location.port;
    // Standard reverse proxy ports (80, 443, empty) or Vite dev/preview (5173, 4173) proxy to backend
    if (port === '5173' || port === '4173' || port === '80' || port === '443' || port === '') {
      return '';
    }
    // If running on other localhost ports (e.g. 3000, 5000, 5500) without a reverse proxy
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
      return 'http://127.0.0.1:8000';
    }
  }

  return '';
}

function getAdminHeaders(): Record<string, string> {
  const headers: Record<string, string> = {};
  if (typeof window !== 'undefined') {
    const key = localStorage.getItem('bhashashield_admin_key') || sessionStorage.getItem('bhashashield_admin_key');
    if (key) {
      headers['X-Admin-Key'] = key;
    }
  }
  return headers;
}

async function requestJson<T>(path: string, options?: RequestInit): Promise<T> {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}${path}`;
  let response: Response;

  try {
    response = await fetch(url, options);
  } catch (err: any) {
    throw new Error(
      `Failed to connect to BhashaShield API at ${url}. Please ensure the backend server is running on http://127.0.0.1:8000.`
    );
  }

  if (!response.ok) {
    const errBody = await response.json().catch(() => ({ detail: null }));
    const message = errBody.detail || `Server error (${response.status}: ${response.statusText})`;
    throw new Error(message);
  }

  return response.json();
}

export async function analyzeText(request: AnalyzeRequest): Promise<AnalyzeResponse> {
  return requestJson<AnalyzeResponse>('/analyze', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });
}

export async function getStats(): Promise<DashboardStats> {
  return requestJson<DashboardStats>('/stats');
}

export async function getScans(limit = 50, offset = 0): Promise<ScanRecord[]> {
  return requestJson<ScanRecord[]>(`/scans?limit=${limit}&offset=${offset}`);
}

export async function clearScans(): Promise<{ status: string; cleared_records: number }> {
  return requestJson<{ status: string; cleared_records: number }>('/scans', {
    method: 'DELETE',
    headers: getAdminHeaders(),
  });
}

export async function getEvaluationReport(): Promise<EvaluationMetrics> {
  return requestJson<EvaluationMetrics>('/evaluation/report');
}

export async function triggerEvaluation(): Promise<{ status: string; report: EvaluationMetrics }> {
  return requestJson<{ status: string; report: EvaluationMetrics }>('/evaluation/run', {
    method: 'POST',
    headers: getAdminHeaders(),
  });
}

export async function checkHealth(): Promise<{ status: string; model_status: string }> {
  return requestJson<{ status: string; model_status: string }>('/health');
}
