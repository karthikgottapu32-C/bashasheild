"""
BhashaShield Python SDK
Production-grade multilingual AI prompt injection defense and guardrail integration.
"""

import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, Callable

class BhashaShieldSecurityException(Exception):
    """Raised when an adversarial prompt injection or security threat is blocked by policy."""
    def __init__(self, decision: Dict[str, Any]):
        self.decision = decision
        super().__init__(
            f"Prompt blocked by BhashaShield: {decision.get('reason')} "
            f"(Threat: {decision.get('primary_threat')}, Score: {decision.get('risk_score')})"
        )

class BhashaShieldClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", api_key: Optional[str] = None, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "BhashaShield-Python-SDK/1.0"
        }
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            raise RuntimeError(f"BhashaShield API error HTTP {e.code}: {err_body}") from e
        except Exception as e:
            raise RuntimeError(f"Failed to communicate with BhashaShield at {url}: {e}") from e

    def guard(self, prompt: str, context: Optional[str] = None, channel: str = "General Text") -> Dict[str, Any]:
        """
        Fast guardrail check returning actionable decision (ALLOW, REVIEW, BLOCK).
        """
        return self._post("/v1/decision", {
            "prompt": prompt,
            "context": context,
            "channel": channel
        })

    def analyze(self, text: str, channel: str = "General Text", save_to_history: bool = False) -> Dict[str, Any]:
        """
        Comprehensive deep security scan returning spans, confidence, language detection, and target types.
        """
        return self._post("/v1/analyze", {
            "text": text,
            "channel": channel,
            "save_to_history": save_to_history
        })

    def wrap_llm_call(self, prompt: str, llm_callable: Callable[[str], Any], context: Optional[str] = None) -> Any:
        """
        Decorator / wrapper pattern: guards prompt before executing downstream LLM call.
        Raises BhashaShieldSecurityException if decision == 'BLOCK'.
        """
        decision = self.guard(prompt, context=context)
        if decision.get("decision") == "BLOCK":
            raise BhashaShieldSecurityException(decision)
        return llm_callable(prompt)
