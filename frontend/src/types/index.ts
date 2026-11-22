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
  output_language?: string;
  recommendation_style?: string;
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
  output_language?: string;
  recommendation_style?: string;
  default_output_language?: string;
  available_output_languages?: string[];
  available_recommendation_styles?: string[];
}

export interface CustomizeRecommendationRequest {
  scan_id?: string;
  text?: string;
  language: string;
  style: string;
  classification?: string;
  risk_score?: number;
  risk_level?: RiskLevel;
  categories?: string[];
  target_type?: string;
  custom_recommendations?: string[];
  detected_language_code?: string;
}

export interface CustomizeRecommendationResponse {
  scan_id?: string;
  output_language: string;
  output_language_label: string;
  recommendation_style: string;
  explanation: string;
  recommended_actions: string[];
  classification: string;
  risk_score: number;
  risk_level: RiskLevel;
  immutability_verified: boolean;
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

export interface FailedTestCase {
  id: string;
  text_preview: string;
  language: string;
  ground_truth: string;
  predicted: string;
  error_type: string;
  risk_score: number;
  threat_categories: string[];
}

export interface EvaluationDataset {
  id: string;
  name: string;
  description: string;
  sample_count: number;
}

export interface EvaluationMetrics {
  dataset_name?: string;
  dataset_file?: string;
  clean_pass_rate?: number;
  uncertain_samples?: number;
  failed_cases?: FailedTestCase[];
  available_datasets?: string[];
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

export interface UserProfile {
  id: string;
  username: string;
  role: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}
