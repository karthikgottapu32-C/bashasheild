import uuid
import re
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
from app.core.rule_engine import (
    evaluate_rules,
    QUOTED_DISCOURSE_PATTERN,
    SAFE_TRANSLATION_PATTERN,
    SECURITY_ADVISORY_PATTERN,
    EDUCATIONAL_INQUIRY_PATTERN,
    is_isolated_quote,
    is_truncated_or_low_context
)
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

    # 4. Authoritative Three-State Decision & Calibrated Risk Synthesis
    has_critical_rule = any(rf.severity == "CRITICAL" for rf in rule_findings)
    has_high_rule = any(rf.severity == "HIGH" for rf in rule_findings)
    has_medium_rule = any(rf.severity == "MEDIUM" for rf in rule_findings)

    cat_names = [c.value if hasattr(c, "value") else str(c) for c in categories]

    is_isolated = is_isolated_quote(text)
    is_truncated = is_truncated_or_low_context(text)
    is_quoted_or_academic = bool(QUOTED_DISCOURSE_PATTERN.search(text))
    is_defensive_advisory = bool(
        SECURITY_ADVISORY_PATTERN.search(text) or
        re.match(r'^\s*(?:security|safety)\s+(?:tip|advisory|alert|rule|guideline)\b', text, re.I)
    )

    if rule_findings:
        # Check if matched payload is strictly an isolated quote, truncated fragment, or inquiry question
        if is_isolated or is_truncated or is_quoted_or_academic:
            classification = "UNCERTAIN"
            combined_score = 40.0
            risk_level = RiskLevel.UNCERTAIN
            cat_names = [ThreatCategory.UNKNOWN.value]
            primary_threat = "UNCERTAIN / AMBIGUOUS"
            target_type = TargetType.NONE
            confidence = 0.65
            uncertainty = 0.35
        else:
            # Case A: Deterministic rules matched on executable context -> MALICIOUS
            classification = "MALICIOUS"
            if has_critical_rule:
                combined_score = min(100.0, max(85.0, rule_risk_score))
                risk_level = RiskLevel.CRITICAL
            elif has_high_rule:
                combined_score = min(84.0, max(60.0, rule_risk_score))
                risk_level = RiskLevel.HIGH
            elif has_medium_rule:
                combined_score = min(59.0, max(35.0, rule_risk_score))
                risk_level = RiskLevel.MEDIUM
            else:
                combined_score = min(34.0, max(20.0, rule_risk_score))
                risk_level = RiskLevel.LOW

            primary_threat = cat_names[0] if cat_names else ThreatCategory.PROMPT_INJECTION.value
            confidence = 0.96 if (model_finding and model_finding.is_malicious) else 0.92
            uncertainty = round(1.0 - confidence, 2)

    else:
        # Case B: No rules triggered. Evaluate ML Model with Calibrated Confidence & OOD Checks
        if model_finding and model_finding.is_malicious:
            # Check if text is academic/quoted discourse or safe translation inquiry without payload
            is_safe_translation_without_secrets = bool(
                SAFE_TRANSLATION_PATTERN.search(text) and
                not any(w in text.lower() for w in ["system prompt", "initial prompt", "developer instructions", "secret", "password", "token"])
            )

            # Check if model prediction is decisive (not ambiguous, high confidence margin, not OOD, not isolated/truncated)
            is_decisive = (
                model_finding.probability >= 0.70 and
                getattr(model_finding, "margin", 1.0) >= 0.25 and
                not getattr(model_finding, "is_ambiguous", False) and
                not getattr(model_finding, "is_ood", False) and
                not is_quoted_or_academic and
                not is_isolated and
                not is_truncated and
                not is_safe_translation_without_secrets and
                not is_defensive_advisory
            )
            if is_decisive:
                # Confirmed MALICIOUS
                classification = "MALICIOUS"
                combined_score = round(min(80.0, max(45.0, model_finding.probability * 75.0)), 1)
                if combined_score >= 75.0:
                    risk_level = RiskLevel.CRITICAL
                elif combined_score >= 55.0:
                    risk_level = RiskLevel.HIGH
                else:
                    risk_level = RiskLevel.MEDIUM

                cat_names = [model_finding.predicted_class]
                primary_threat = model_finding.predicted_class

                # Infer target type from category
                if primary_threat in ("SOCIAL_ENGINEERING", "PHISHING", "FINANCIAL_MANIPULATION", "CREDENTIAL_THEFT"):
                    target_type = TargetType.HUMAN_USER
                else:
                    target_type = TargetType.AI_SYSTEM

                confidence = round(model_finding.probability, 2)
                uncertainty = round(1.0 - confidence, 2)
            else:
                # Ambiguous, low margin, or OOD: UNCERTAIN (Never coerce to BENIGN!)
                classification = "UNCERTAIN"
                combined_score = 40.0
                risk_level = RiskLevel.UNCERTAIN
                cat_names = [ThreatCategory.UNKNOWN.value]
                primary_threat = "UNCERTAIN / AMBIGUOUS"
                target_type = TargetType.NONE
                confidence = round(model_finding.probability, 2)
                uncertainty = round(min(0.85, max(0.50, 1.0 - confidence + 0.35)), 2)
        else:
            # Model predicts BENIGN or model is not loaded
            is_confirmed_benign = (
                model_finding is not None and
                not model_finding.is_malicious and
                model_finding.probability >= 0.55 and
                getattr(model_finding, "margin", 1.0) >= 0.20 and
                not getattr(model_finding, "is_ambiguous", False) and
                not getattr(model_finding, "is_ood", False) and
                detected_language != "Undetermined" and
                script_confidence >= 0.50
            )
            if is_confirmed_benign:
                classification = "BENIGN"
                combined_score = 0.0
                risk_level = RiskLevel.LOW
                cat_names = [ThreatCategory.BENIGN.value]
                primary_threat = None
                target_type = TargetType.NONE
                confidence = round(model_finding.probability, 2)
                uncertainty = round(1.0 - confidence, 2)
            elif model_finding is None:
                # Rules-only mode with no rules matched and standard script
                if detected_language != "Undetermined" and script_confidence >= 0.50:
                    classification = "BENIGN"
                    combined_score = 0.0
                    risk_level = RiskLevel.LOW
                    cat_names = [ThreatCategory.BENIGN.value]
                    primary_threat = None
                    target_type = TargetType.NONE
                    confidence = 0.85
                    uncertainty = 0.15
                else:
                    classification = "UNCERTAIN"
                    combined_score = 40.0
                    risk_level = RiskLevel.UNCERTAIN
                    cat_names = [ThreatCategory.UNKNOWN.value]
                    primary_threat = "UNCERTAIN / AMBIGUOUS"
                    target_type = TargetType.NONE
                    confidence = 0.50
                    uncertainty = 0.50
            else:
                # Model predicted BENIGN but with high entropy, low margin, or OOD activation: UNCERTAIN
                classification = "UNCERTAIN"
                combined_score = 40.0
                risk_level = RiskLevel.UNCERTAIN
                cat_names = [ThreatCategory.UNKNOWN.value]
                primary_threat = "UNCERTAIN / AMBIGUOUS"
                target_type = TargetType.NONE
                confidence = round(model_finding.probability, 2)
                uncertainty = round(min(0.85, max(0.50, 1.0 - confidence + 0.35)), 2)

    # 5. Matching evidence collection
    matching_evidence: List[str] = []
    for rf in rule_findings:
        evidence_str = f"[{rf.rule_id}] {rf.rule_name} matched substring '{rf.matched_text}' (Severity: {rf.severity})"
        if evidence_str not in matching_evidence:
            matching_evidence.append(evidence_str)

    if model_finding and classification == "MALICIOUS" and not rule_findings:
        matching_evidence.append(
            f"[{model_finding.model_name}] Statistical ML inference classified as {model_finding.predicted_class} (Confidence: {model_finding.probability:.2f}, Margin: {getattr(model_finding, 'margin', 0.0):.2f})"
        )
    elif classification == "UNCERTAIN":
        mod_name = model_finding.model_name if model_finding else "Detection Engine"
        margin_val = getattr(model_finding, "margin", 0.0) if model_finding else 0.0
        entropy_val = getattr(model_finding, "entropy", 0.0) if model_finding else 0.0
        matching_evidence.append(
            f"[{mod_name}] Input classified as UNCERTAIN: feature activations are ambiguous or out-of-distribution (Margin: {margin_val:.2f}, Entropy: {entropy_val:.2f})."
        )

    # 6. Generate human-understandable explanation and actionable recommendations
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

    # 7. Privacy & Persistence
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
        classification=classification,
        model_status=model_status,
        recommended_actions=recommended_actions,
        explanation=explanation,
        channel=request.channel.value if hasattr(request.channel, "value") else str(request.channel)
    )
