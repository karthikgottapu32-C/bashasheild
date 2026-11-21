/**
 * BhashaShield TypeScript SDK
 * Production-grade multilingual AI prompt injection defense and guardrail integration.
 */

export type PolicyDecision = 'ALLOW' | 'REVIEW' | 'BLOCK';
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | 'UNCERTAIN';
export type TargetType = 'AI_SYSTEM' | 'HUMAN_USER' | 'BOTH' | 'NONE';

export interface GuardDecisionResponse {
  decision: PolicyDecision;
  risk_score: number;
  risk_level: RiskLevel;
  primary_threat?: string | null;
  target_type: TargetType;
  reason: string;
  action_required: string;
  latency_ms: number;
  scan_id: string;
  model_status: string;
}

export interface AnalyzeResponse {
  scan_id: string;
  timestamp: string;
  text_preview: string;
  detected_language: string;
  detected_script: string;
  language_code: string;
  threat_categories: string[];
  primary_threat?: string | null;
  target_type: TargetType;
  risk_score: number;
  risk_level: RiskLevel;
  highlighted_spans: Array<{
    start: number;
    end: number;
    text: string;
    category: string;
    severity: string;
    rule_id: string;
    description: string;
  }>;
  matching_evidence: string[];
  confidence: number;
  model_status: string;
  recommended_actions: string[];
  explanation: string;
}

export class BhashaShieldSecurityError extends Error {
  public decision: GuardDecisionResponse;
  constructor(decision: GuardDecisionResponse) {
    super(
      `Prompt blocked by BhashaShield: ${decision.reason} (Threat: ${decision.primary_threat || 'Unknown'}, Score: ${decision.risk_score})`
    );
    this.name = 'BhashaShieldSecurityError';
    this.decision = decision;
  }
}

export class BhashaShieldClient {
  private baseUrl: string;
  private apiKey?: string;

  constructor(options?: { baseUrl?: string; apiKey?: string }) {
    this.baseUrl = (options?.baseUrl || 'http://127.0.0.1:8000').replace(/\/$/, '');
    this.apiKey = options?.apiKey;
  }

  private async request<T>(path: string, payload: unknown): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'User-Agent': 'BhashaShield-TS-SDK/1.0',
    };
    if (this.apiKey) {
      headers['X-API-Key'] = this.apiKey;
    }

    const res = await fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`BhashaShield API error ${res.status}: ${errText}`);
    }

    return (await res.json()) as T;
  }

  /**
   * Fast guardrail evaluation for incoming prompts and RAG contexts.
   */
  public async guard(
    prompt: string,
    context?: string,
    channel: string = 'General Text'
  ): Promise<GuardDecisionResponse> {
    return this.request<GuardDecisionResponse>('/v1/decision', {
      prompt,
      context,
      channel,
    });
  }

  /**
   * Full threat analysis returning granular spans, token offsets, and multi-label threats.
   */
  public async analyze(
    text: string,
    channel: string = 'General Text',
    saveToHistory: boolean = false
  ): Promise<AnalyzeResponse> {
    return this.request<AnalyzeResponse>('/v1/analyze', {
      text,
      channel,
      save_to_history: saveToHistory,
    });
  }

  /**
   * Wraps an LLM API call: verifies prompt safety and executes only if ALLOW or REVIEW.
   */
  public async wrapLLMCall<T>(
    prompt: string,
    callable: (safePrompt: string) => Promise<T>,
    context?: string
  ): Promise<T> {
    const decision = await this.guard(prompt, context);
    if (decision.decision === 'BLOCK') {
      throw new BhashaShieldSecurityError(decision);
    }
    return callable(prompt);
  }
}
