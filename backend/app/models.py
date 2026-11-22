from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class BaseModelConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

class InputChannel(str, Enum):
    UPI_REMARK = "UPI Remark"
    SMS = "SMS"
    WHATSAPP = "WhatsApp"
    EMAIL = "Email"
    GENERAL_TEXT = "General Text"

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNCERTAIN = "UNCERTAIN"

class ThreatCategory(str, Enum):
    PROMPT_INJECTION = "PROMPT_INJECTION"
    JAILBREAK = "JAILBREAK"
    INSTRUCTION_OVERRIDE = "INSTRUCTION_OVERRIDE"
    PRIVILEGE_ESCALATION = "PRIVILEGE_ESCALATION"
    DATA_EXFILTRATION = "DATA_EXFILTRATION"
    SENSITIVE_INFO_EXPOSURE = "SENSITIVE_INFO_EXPOSURE"
    SOCIAL_ENGINEERING = "SOCIAL_ENGINEERING"
    PHISHING = "PHISHING"
    FINANCIAL_MANIPULATION = "FINANCIAL_MANIPULATION"
    CREDENTIAL_THEFT = "CREDENTIAL_THEFT"
    MALICIOUS_URL = "MALICIOUS_URL"
    MALICIOUS_CODE_INSTRUCTION = "MALICIOUS_CODE_INSTRUCTION"
    BENIGN = "BENIGN"
    UNKNOWN = "UNKNOWN"

class TargetType(str, Enum):
    AI_SYSTEM = "AI_SYSTEM"
    HUMAN_USER = "HUMAN_USER"
    BOTH = "BOTH"
    NONE = "NONE"

class HighlightedSpan(BaseModelConfig):
    start: int = Field(..., description="0-indexed start character offset in original text")
    end: int = Field(..., description="0-indexed end character offset in original text")
    text: str = Field(..., description="Exact matched substring")
    category: str = Field(..., description="Threat category for this span")
    severity: str = Field(..., description="Severity level")
    rule_id: str = Field(..., description="Rule ID that triggered this span")
    description: str = Field(..., description="Human-readable rule explanation")

class RuleFinding(BaseModelConfig):
    rule_id: str
    rule_name: str
    category: str
    target_type: str
    severity: str
    matched_text: str
    evidence: str
    span: Dict[str, int]

class ModelFinding(BaseModelConfig):
    predicted_class: str
    probability: float
    is_malicious: bool
    model_name: str
    probabilities_by_class: Optional[Dict[str, float]] = None
    margin: Optional[float] = Field(None, description="Difference between top probability and second highest probability")
    entropy: Optional[float] = Field(None, description="Normalized prediction entropy (uncertainty)")
    is_ambiguous: Optional[bool] = Field(False, description="True if margin is narrow or entropy is high")
    is_ood: Optional[bool] = Field(False, description="True if input has very low feature norm (out-of-distribution)")

class AnalyzeRequest(BaseModelConfig):
    text: str = Field(..., min_length=1, max_length=10000, description="Input text to scan for security threats")
    language_hint: Optional[str] = Field("auto", description="Optional language hint (auto, te, hi, en, te-Latn, hi-Latn)")
    channel: Optional[InputChannel] = Field(InputChannel.GENERAL_TEXT, description="Input delivery channel")
    save_to_history: Optional[bool] = Field(True, description="Privacy toggle: if false, scan text and findings are not persisted")
    output_language: Optional[str] = Field("auto", description="Desired presentation language: auto, en, te, hi, te-Latn, hi-Latn")
    recommendation_style: Optional[str] = Field("actionable", description="Desired recommendation style: actionable, simple, detailed, technical")

class AnalyzeResponse(BaseModelConfig):
    scan_id: str
    timestamp: str
    text_preview: str
    detected_language: str
    detected_script: str
    language_code: str
    script_confidence: float
    threat_categories: List[str]
    primary_threat: Optional[str] = None
    target_type: str
    risk_score: float = Field(..., ge=0.0, le=100.0)
    risk_level: RiskLevel
    highlighted_spans: List[HighlightedSpan]
    matching_evidence: List[str]
    rule_findings: List[RuleFinding]
    model_findings: Optional[ModelFinding] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    uncertainty: float = Field(..., ge=0.0, le=1.0)
    classification: str = Field("BENIGN", description="Three-state security classification: BENIGN, MALICIOUS, or UNCERTAIN")
    model_status: str
    recommended_actions: List[str]
    explanation: str
    channel: str
    output_language: str = Field("en", description="Output language used for explanation and recommendations")
    recommendation_style: str = Field("actionable", description="Style applied to recommendations")
    default_output_language: str = Field("en", description="Natural matching language for input")
    available_output_languages: List[str] = Field(default_factory=lambda: ["auto", "en", "te", "hi", "te-Latn", "hi-Latn"])
    available_recommendation_styles: List[str] = Field(default_factory=lambda: ["actionable", "simple", "detailed", "technical"])

class CustomizeRecommendationRequest(BaseModelConfig):
    scan_id: Optional[str] = Field(None, description="Optional scan ID to update")
    text: Optional[str] = Field(None, description="Optional original prompt text")
    language: str = Field("auto", description="Target presentation language (auto, en, te, hi, te-Latn, hi-Latn)")
    style: str = Field("actionable", description="Target style (actionable, simple, detailed, technical)")
    classification: Optional[str] = Field(None, description="Immutable classification")
    risk_score: Optional[float] = Field(None, description="Immutable risk score")
    risk_level: Optional[RiskLevel] = Field(None, description="Immutable risk level")
    categories: Optional[List[str]] = Field(None, description="Threat categories")
    target_type: Optional[TargetType] = Field(None, description="Target type")
    custom_recommendations: Optional[List[str]] = Field(None, description="User-edited custom recommendations")
    detected_language_code: Optional[str] = Field("en", description="Detected input language code")

class CustomizeRecommendationResponse(BaseModelConfig):
    scan_id: Optional[str] = None
    output_language: str
    output_language_label: str
    recommendation_style: str
    explanation: str
    recommended_actions: List[str]
    classification: str
    risk_score: float
    risk_level: RiskLevel
    immutability_verified: bool = True

class ScanRecord(BaseModelConfig):
    id: str
    timestamp: str
    channel: str
    language: str
    script: str
    risk_score: float
    risk_level: str
    primary_threat: Optional[str]
    threat_categories: List[str]
    target_type: str
    text_preview: str
    is_saved: bool
    user_id: Optional[str] = "anonymous"

class UserRegisterRequest(BaseModelConfig):
    username: str = Field(..., min_length=3, max_length=64, description="Alphanumeric username")
    email: Optional[str] = Field(None, description="Optional user email address")
    password: str = Field(..., min_length=8, max_length=128, description="User password (min 8 characters)")

class UserLoginRequest(BaseModelConfig):
    username: str = Field(..., description="Username or email address")
    password: str = Field(..., description="User password")

class UserResponse(BaseModelConfig):
    id: str
    username: str
    email: str
    role: str
    created_at: str

class AuthResponse(BaseModelConfig):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class DashboardStats(BaseModelConfig):
    total_scans: int
    threat_count: int
    prompt_injection_count: int
    high_risk_count: int
    clean_count: int
    risk_distribution: Dict[str, int]
    language_distribution: Dict[str, int]
    threat_distribution: Dict[str, int]
    channel_distribution: Dict[str, int]
    target_distribution: Dict[str, int]
    recent_scans: List[ScanRecord]

class EvaluationMetrics(BaseModelConfig):
    precision: float
    recall: float
    f1_score: float
    false_positive_rate: float
    prompt_injection_precision: float
    prompt_injection_recall: float
    prompt_injection_f1: float
    total_samples: int
    per_language: Dict[str, Dict[str, float]]
    per_category: Dict[str, Dict[str, float]]
    per_script: Dict[str, Dict[str, float]]
    per_channel: Dict[str, Dict[str, float]]
    confusion_matrix: Dict[str, int]
    evaluated_at: str
    model_evaluated: str
    is_synthetic: bool = True
    disclaimer: str = "Results are measured on a synthetic evaluation dataset and do not establish real-world detection performance."

class PolicyDecision(str, Enum):
    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"

class GuardDecisionRequest(BaseModelConfig):
    prompt: str = Field(..., min_length=1, max_length=10000, description="Input text or prompt to guard")
    context: Optional[str] = Field(None, description="Optional RAG context or document content")
    session_id: Optional[str] = Field(None, description="Optional session or user identifier")
    channel: Optional[InputChannel] = Field(InputChannel.GENERAL_TEXT, description="Input channel")

class GuardDecisionResponse(BaseModelConfig):
    decision: PolicyDecision
    risk_score: float = Field(..., ge=0.0, le=100.0)
    risk_level: RiskLevel
    primary_threat: Optional[str] = None
    target_type: str
    reason: str
    action_required: str
    latency_ms: float
    scan_id: str
    model_status: str

