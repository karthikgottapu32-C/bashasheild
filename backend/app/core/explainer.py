from typing import List, Dict, Any, Optional, Tuple
import os
import requests
from app.models import ThreatCategory, TargetType, RiskLevel, RuleFinding, ModelFinding
from app.config import settings

def generate_explanation_and_actions(
    text: str,
    language: str,
    script: str,
    risk_level: RiskLevel,
    risk_score: float,
    categories: List[str],
    target_type: TargetType,
    rule_findings: List[RuleFinding],
    model_findings: Optional[ModelFinding] = None
) -> Tuple[str, List[str]]:
    # If no threats found:
    if risk_level == RiskLevel.LOW or not categories or categories == ["BENIGN"]:
        explanation = (
            f"No malicious prompt injections, exfiltration patterns, or social engineering tactics "
            f"were identified in this {language} ({script} script) input. The text appears benign and safe for AI processing."
        )
        recommendations = [
            "Proceed with normal AI assistant execution.",
            "Maintain standard input sandboxing and token length limits."
        ]
        return explanation, recommendations

    # Formulate deterministic deep explanation
    primary_threat = categories[0] if categories else "PROMPT_INJECTION"
    target_desc = {
        TargetType.AI_SYSTEM: "AI Assistant (Instruction Hijacking / Exfiltration)",
        TargetType.HUMAN_USER: "Human End-User (Phishing / Financial Scam)",
        TargetType.BOTH: "Hybrid Target (Both AI System and Human User)",
        TargetType.NONE: "Unknown / Low Risk"
    }.get(target_type, "AI System")

    matched_rules_summary = ", ".join([f"'{rf.rule_name}'" for rf in rule_findings[:3]])
    
    explanation_parts = [
        f"Critical security alert: Threat detected in {language} text using {script} script.",
        f"Target Type: {target_desc}.",
        f"Attack Vector: The input exhibits characteristic signatures of {primary_threat.replace('_', ' ').title()}.",
    ]

    if rule_findings:
        explanation_parts.append(f"Deterministic evidence triggered {len(rule_findings)} detection rule(s): {matched_rules_summary}.")

    if target_type in (TargetType.AI_SYSTEM, TargetType.BOTH):
        explanation_parts.append(
            "This pattern attempts to override system boundaries, ignore developer system directives, "
            "or manipulate model output contexts across language representations."
        )
    elif target_type == TargetType.HUMAN_USER:
        explanation_parts.append(
            "This pattern attempts to deceive or coerce the recipient into performing unauthorized financial transfers, "
            "entering secret PINs, or divulging credentials."
        )

    explanation = " ".join(explanation_parts)

    # Formulate prioritized actionable recommendations
    recommendations: List[str] = []

    if target_type in (TargetType.AI_SYSTEM, TargetType.BOTH):
        recommendations.append("CRITICAL: Drop or quarantine input; do NOT pass directly to downstream LLM reasoning contexts.")
        recommendations.append("Apply BhashaShield sanitizer to strip instruction override directives and reset context framing.")
        recommendations.append("Enforce strict role separation: preserve system prompt immutability in system message blocks.")
    
    if target_type in (TargetType.HUMAN_USER, TargetType.BOTH):
        recommendations.append("Alert recipient with high-visibility warning: Never enter UPI PIN to receive money or refunds.")
        recommendations.append("Flag sender account and transaction remark for security compliance inspection.")
        recommendations.append("Block embedded URLs and verify sender channel authenticity.")

    if any("EXFILTRATION" in c for c in categories):
        recommendations.append("Audit system prompt for sensitive API keys, database URLs, and environment variables.")

    # Check if Gemini API is available for supplementary advisory text
    if settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 5:
        try:
            # We only use Gemini to complement explanation text, never changing classification
            gemini_exp = _call_gemini_advisory(text, language, categories, rule_findings)
            if gemini_exp:
                explanation += f"\n\n[AI Security Advisory Analysis]: {gemini_exp}"
        except Exception:
            pass # Graceful degradation: never fails if Gemini unreachable

    return explanation, recommendations

def _call_gemini_advisory(text: str, language: str, categories: List[str], rule_findings: List[RuleFinding]) -> Optional[str]:
    # Non-blocking, best-effort enrichment
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
    prompt = (
        f"You are a cybersecurity analyst assistant. Briefly (in 2 sentences) explain the risk of this {language} input "
        f"which was flagged for {categories}: '{text[:200]}'."
    )
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    res = requests.post(url, json=payload, timeout=3)
    if res.status_code == 200:
        data = res.json()
        candidates = data.get("candidates", [])
        if candidates:
            return candidates[0]["content"]["parts"][0]["text"].strip()
    return None
