import type {
  DecisionDetail,
  DecisionFeedbackRequest,
  DecisionFeedbackResponse,
  HealthResponse,
  PortfolioHealthResponse,
} from './types';

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set('Content-Type', 'application/json');

  const response = await fetch(`${apiBaseUrl}${path}`, {
    headers,
    ...init,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health');
}

export function getPortfolioHealth(limit: number): Promise<PortfolioHealthResponse> {
  return request<PortfolioHealthResponse>(`/portfolio/health?limit=${limit}`);
}

export function getDecision(loanId: string): Promise<DecisionDetail> {
  return request<DecisionDetail>(`/decisions/${encodeURIComponent(loanId)}`);
}

export function submitDecisionFeedback(
  loanId: string,
  feedback: DecisionFeedbackRequest,
): Promise<DecisionFeedbackResponse> {
  return request<DecisionFeedbackResponse>(`/decisions/${encodeURIComponent(loanId)}/feedback`, {
    method: 'POST',
    body: JSON.stringify(feedback),
  });
}