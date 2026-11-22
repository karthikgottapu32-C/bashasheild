import { AnalyzeRequest, AnalyzeResponse, DashboardStats, ScanRecord, EvaluationMetrics } from '../types';

export function getApiBaseUrl(): string {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL.replace(/\/$/, '');
  }

  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    const port = window.location.port;

    // Local development: use Vite proxy on 5173/4173, or direct local backend on 8000
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      if (port === '5173' || port === '4173') {
        return '';
      }
      return 'http://127.0.0.1:8000';
    }

    // When served from the cloud backend (Render) or any custom domain:
    // Relative requests stay on the same origin and eliminate cross-device localhost failures
    if (hostname === 'bhashashield-api.onrender.com' || !hostname.includes('.')) {
      return '';
    }

    // External static frontend hosts (e.g. Vercel, Netlify): target public production API
    if (hostname.endsWith('.vercel.app') || hostname.endsWith('.netlify.app') || hostname.endsWith('.pages.dev')) {
      return 'https://bhashashield-api.onrender.com';
    }

    // Fallback: stay relative to current host
    return '';
  }

  return 'https://bhashashield-api.onrender.com';
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
      `Failed to connect to BhashaShield API at ${url}. Please verify network connectivity and backend service status.`
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

export async function getScans(
  limit = 50,
  offset = 0,
  query?: string,
  riskLevel?: string
): Promise<ScanRecord[]> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  if (query) params.set('query', query);
  if (riskLevel && riskLevel !== 'ALL') params.set('risk_level', riskLevel);
  return requestJson<ScanRecord[]>(`/scans?${params.toString()}`);
}

export async function deleteScan(scanId: string): Promise<{ status: string; message: string }> {
  return requestJson<{ status: string; message: string }>(`/scans/${scanId}`, {
    method: 'DELETE',
    headers: getAdminHeaders(),
  });
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
