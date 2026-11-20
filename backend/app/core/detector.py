import uuid
from datetime import datetime
from typing import List, Optional
from app.models import (
    AnalyzeRequest,
    AnalyzeResponse,
    RiskLevel,
    ThreatCategory,
    TargetType,
    HighlightedSpan
)
from app.core.language_detector import detect_language
from app.core.rule_engine import evaluate_rules
from app.core.model_service import model_service
from app.core.explainer import generate_explanation_and_actions
from app.database import save_scan

def analyze_text(request: AnalyzeRequest) -> AnalyzeResponse:
    text = request.text
    scan_id = f"BS-{uuid.uuid4().hex[:10].upper()}"
    timestamp = datetime.utcnow().isoformat() + "Z"
    text_preview = text[:80] + ("..." if len(text) > 80 else "")

    # 1. Detect language and script
    lang_info = detect_language(text, request.language_hint or "auto")
    detected_language = lang_info["language"]
    detected_script = lang_info["script"]
    language_code = lang_info["language_code"]
    script_confidence = lang_info["confidence"]

    # 2. Evaluate Rule Engine
    rule_findings, highlighted_spans, rule_risk_score, categories, target_type = evaluate_rules(text)

    # 3. Evaluate ML Model
    model_finding = model_service.predict(text)
    model_status = model_service.status

    # 4. Synthesize Risk Score & Risk Level
    combined_score = rule_risk_score
    if model_finding and model_finding.is_malicious:
        # If model detects threat, blend model probability
        model_contribution = model_finding.probability * 40.0
        combined_score = min(100.0, max(combined_score, 50.0 + (model_finding.probability * 45.0)))
    elif model_finding and not model_finding.is_malicious and combined_score < 30.0:
        combined_score = min(combined_score, 15.0)

    # Risk level thresholding
    if combined_score >= 75.0:
        risk_level = RiskLevel.CRITICAL
    elif combined_score >= 50.0:
        risk_level = RiskLevel.HIGH
    elif combined_score >= 25.0:
        risk_level = RiskLevel.MEDIUM
    else:
        risk_level = RiskLevel.LOW

    # Set threat categories
    cat_names = [c.value if hasattr(c, "value") else str(c) for c in categories]
    if not cat_names:
        if risk_level != RiskLevel.LOW:
            cat_names = [ThreatCategory.PROMPT_INJECTION.value]
        else:
            cat_names = [ThreatCategory.BENIGN.value]

    primary_threat = cat_names[0] if cat_names else None

    # Matching evidence collection
    matching_evidence: List[str] = []
    for rf in rule_findings:
        evidence_str = f"[{rf.rule_id}] {rf.rule_name} matched substring '{rf.matched_text}' (Severity: {rf.severity})"
        if evidence_str not in matching_evidence:
            matching_evidence.append(evidence_str)

    if model_finding:
        matching_evidence.append(
            f"[{model_finding.model_name}] Inference classified as {model_finding.predicted_class} (Confidence: {model_finding.probability:.2f})"
        )

    # Confidence and uncertainty estimation
    if rule_findings and model_finding and model_finding.is_malicious:
        confidence = 0.96
        uncertainty = 0.04
    elif rule_findings:
        confidence = 0.92
        uncertainty = 0.08
    elif model_finding:
        confidence = round(model_finding.probability, 2)
        uncertainty = round(1.0 - confidence, 2)
    else:
        confidence = 0.88
        uncertainty = 0.12

    # 5. Generate human-understandable explanation and actionable recommendations
    explanation, recommended_actions = generate_explanation_and_actions(
        text=text,
        language=detected_language,
        script=detected_script,
        risk_level=risk_level,
        risk_score=combined_score,
        categories=cat_names,
        target_type=target_type,
        rule_findings=rule_findings,
        model_findings=model_finding
    )

    # 6. Privacy & Persistence
    save_to_hist = request.save_to_history if request.save_to_history is not None else True
    save_scan(
        scan_id=scan_id,
        channel=request.channel.value if hasattr(request.channel, "value") else str(request.channel),
        language=detected_language,
        script=detected_script,
        risk_score=combined_score,
        risk_level=risk_level.value,
        primary_threat=primary_threat,
        threat_categories=cat_names,
        target_type=target_type.value,
        text_preview=text_preview,
        full_text=text if save_to_hist else None,
        save_to_history=save_to_hist
    )

    return AnalyzeResponse(
        scan_id=scan_id,
        timestamp=timestamp,
        text_preview=text_preview,
        detected_language=detected_language,
        detected_script=detected_script,
        language_code=language_code,
        script_confidence=script_confidence,
        threat_categories=cat_names,
        primary_threat=primary_threat,
        target_type=target_type.value,
        risk_score=combined_score,
        risk_level=risk_level,
        highlighted_spans=highlighted_spans,
        matching_evidence=matching_evidence,
        rule_findings=rule_findings,
        model_findings=model_finding,
        confidence=confidence,
        uncertainty=uncertainty,
        model_status=model_status,
        recommended_actions=recommended_actions,
        explanation=explanation,
        channel=request.channel.value if hasattr(request.channel, "value") else str(request.channel)
    )
