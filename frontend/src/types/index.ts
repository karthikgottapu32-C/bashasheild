export type InputChannel = "UPI Remark" | "SMS" | "WhatsApp" | "Email" | "General Text";

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | "UNCERTAIN";

export interface HighlightedSpan {
  start: int_or_number;
  end: int_or_number;
  text: string;
  category: string;
  severity: string;
  rule_id: string;
  description: string;
}

type int_or_number = number;

export interface RuleFinding {
  rule_id: string;
  rule_name: string;
  category: string;
  target_type: string;
  severity: string;
  matched_text: string;
  evidence: string;
  span: { start: number; end: number };
}

export interface ModelFinding {
  predicted_class: string;
  probability: number;
  is_malicious: boolean;
  model_name: string;
  probabilities_by_class?: Record<string, number>;
}

export interface AnalyzeRequest {
  text: string;
  language_hint?: string;
  channel?: InputChannel;
  save_to_history?: boolean;
}

export interface AnalyzeResponse {
  scan_id: string;
  timestamp: string;
  text_preview: string;
  detected_language: string;
  detected_script: string;
  language_code: string;
  script_confidence: number;
  threat_categories: string[];
  primary_threat?: string;
  target_type: string;
  risk_score: number;
  risk_level: RiskLevel;
  highlighted_spans: HighlightedSpan[];
  matching_evidence: string[];
  rule_findings: RuleFinding[];
  model_findings?: ModelFinding;
  confidence: number;
  uncertainty: number;
  classification?: 'BENIGN' | 'MALICIOUS' | 'UNCERTAIN';
  model_status: string;
  recommended_actions: string[];
  explanation: string;
  channel: string;
}

export interface ScanRecord {
  id: string;
  timestamp: string;
  channel: string;
  language: string;
  script: string;
  risk_score: number;
  risk_level: string;
  primary_threat?: string;
  threat_categories: string[];
  target_type: string;
  text_preview: string;
  is_saved: boolean;
}

export interface DashboardStats {
  total_scans: number;
  threat_count: number;
  prompt_injection_count: number;
  high_risk_count: number;
  clean_count: number;
  risk_distribution: Record<string, number>;
  language_distribution: Record<string, number>;
  threat_distribution: Record<string, number>;
  channel_distribution: Record<string, number>;
  target_distribution: Record<string, number>;
  recent_scans: ScanRecord[];
}

export interface MetricSlice {
  precision: number;
  recall: number;
  f1_score: number;
  false_positive_rate: number;
  samples?: number;
}

export interface EvaluationMetrics {
  precision: number;
  recall: number;
  f1_score: number;
  false_positive_rate: number;
  prompt_injection_precision: number;
  prompt_injection_recall: number;
  prompt_injection_f1: number;
  total_samples: number;
  confusion_matrix: {
    true_positives: number;
    false_positives: number;
    false_negatives: number;
    true_negatives: number;
  };
  per_language: Record<string, MetricSlice>;
  per_script: Record<string, MetricSlice>;
  per_category: Record<string, MetricSlice>;
  per_channel: Record<string, MetricSlice>;
  evaluated_at: string;
  model_evaluated: string;
  is_synthetic: boolean;
  disclaimer: string;
}
