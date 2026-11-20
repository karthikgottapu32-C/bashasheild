# BhashaShield — API Security & Guardrail Validation

**Document Version:** 1.0.0  
**Verification Status:** Verified via Automated Test Suite (`backend/app/tests/test_security_and_sdk.py`)  
**Auditor:** Application Security Team  

---

## 1. Security Architecture Overview

BhashaShield provides two tiers of API interaction:
1. **Public/Inference Endpoints** (`POST /v1/decision`, `POST /v1/analyze`, `POST /analyze`): Designed for low-latency guardrail integration in production LLM applications.
2. **Administrative/Destructive Endpoints** (`DELETE /scans`, `DELETE /v1/scans`, `POST /evaluation/run`): Operations that mutate system state or run intensive computations.

---

## 2. Implemented Defense Controls

### 2.1 Defense-in-Depth HTTP Headers
Every outgoing HTTP response from the FastAPI application is processed by `SecurityHeadersMiddleware`, injecting the following mandatory headers:

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

*Verification Test:* `backend/app/tests/test_security_and_sdk.py::test_security_headers_present` (**PASSED**).

---

### 2.2 Input Boundaries & Payload Caps
- **Max Input Length:** Inputs longer than `settings.MAX_INPUT_LENGTH` (10,000 characters) are rejected immediately with `HTTP 400 Bad Request`.
- **Max Request Body Size:** Incoming payloads with `Content-Length > 1,048,576` bytes (1MB) are rejected with `HTTP 413 Payload Too Large` before deserialization.
- **Empty / Whitespace-Only Validation:** Inputs consisting solely of whitespace are rejected with `HTTP 400 Bad Request`.

*Verification Test:* `backend/app/tests/test_security_and_sdk.py::test_payload_size_enforcement` (**PASSED**).

---

### 2.3 Denial-of-Service Rate Limiting
- **Mechanism:** In-memory sliding-window IP rate limiter (`RateLimitMiddleware`).
- **Policy:** Enforces a configurable cap (`RATE_LIMIT_PER_MINUTE = 120` by default) on `/v1/analyze`, `/v1/decision`, and `/analyze`.
- **Response:** Requests exceeding threshold receive `HTTP 429 Too Many Requests` with a `Retry-After: 60` header and structured error body:
  ```json
  {
    "detail": "Rate limit exceeded. Maximum 120 requests per minute.",
    "error_code": "RATE_LIMIT_EXCEEDED"
  }
  ```

---

### 2.4 Administrative Authorization (`X-Admin-Key`)
Destructive and compute-heavy endpoints are protected via the `verify_admin_key` dependency:
- `DELETE /scans` (History clearance)
- `DELETE /v1/scans` (Versioned history clearance alias)
- `POST /evaluation/run` (840-sample benchmark suite execution)

When `ADMIN_API_KEY` is configured in the environment:
- Requests lacking a valid `X-Admin-Key` header are rejected with `HTTP 401 Unauthorized`.
- Only requests presenting the exact pre-shared administrative key are granted execution.

*Verification Test:* `backend/app/tests/test_security_and_sdk.py::test_admin_authorization_enforcement` (**PASSED**).

---

### 2.5 Information Leakage Prevention
A global exception handler intercepts unhandled runtime exceptions:
```python
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred.", "error_code": "INTERNAL_SERVER_ERROR"}
    )
```
This guarantees that internal server tracebacks, directory paths, and runtime environments are never exposed to API consumers.

---

## 3. SDK Integration Security

### 3.1 Python SDK (`sdk/python/bhashashield.py`)
- **Zero External Dependencies:** Built entirely with Python standard library (`urllib.request`, `json`).
- **Guardrail Wrapper Pattern:** `BhashaShieldClient.wrap_llm_call()` automatically inspects the prompt before dispatching to any model callback. If BhashaShield returns `decision == "BLOCK"`, execution is halted immediately with a `BhashaShieldSecurityException`, preventing unauthorized model execution.

*Verification Test:* `backend/app/tests/test_security_and_sdk.py::test_python_sdk_wrapper_exception` (**PASSED**).

### 3.2 TypeScript SDK (`sdk/typescript/bhashashield.ts`)
- **Native Fetch Implementation:** Operates seamlessly in modern Node.js 18+ and edge browser environments without extra packages.
- **Type-Safe Contract:** Defines strict TypeScript interfaces for `GuardDecisionResponse`, `AnalyzeResponse`, and `PolicyDecision`.
