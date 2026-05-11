export type RiskTier = 'Healthy' | 'Watch' | 'At Risk' | 'Critical';

export type ActionStatus =
  | 'Monitor only'
  | 'Generate reminder draft'
  | 'Recommend follow-up'
  | 'Create follow-up task'
  | 'Escalate to loan officer';

export interface PortfolioHealthItem {
  loan_id: string;
  client_id: string;
  client_name: string | null;
  risk_score: number;
  risk_tier: RiskTier;
  recommended_action: ActionStatus;
  policy_decision: string;
  explanation: string;
  autonomy_level: number;
}

export interface DecisionDetail extends PortfolioHealthItem {
  evidence: Record<string, unknown>;
  model_name: string;
  created_at?: string;
  timestamp?: string;
}

export interface DecisionFeedbackRequest {
  feedback: 'approve' | 'reject';
  comment?: string | null;
  reviewer?: string | null;
}

export interface DecisionFeedbackResponse {
  loan_id: string;
  feedback: 'approve' | 'reject';
  comment: string | null;
  reviewer: string | null;
  stored: boolean;
}

export interface PortfolioHealthSummary {
  total_loans: number;
  healthy_loans: number;
  watch_loans: number;
  at_risk_loans: number;
  critical_loans: number;
}

export interface PortfolioHealthResponse {
  summary: PortfolioHealthSummary;
  items: PortfolioHealthItem[];
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}