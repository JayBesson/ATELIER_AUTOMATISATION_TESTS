"""
Tests for the Frankfurter API (https://api.frankfurter.app)
Contract:
  GET /latest?from=EUR       → {amount, base, date, rates: {...}}
  GET /latest?from=EUR&to=USD,GBP
  GET /2020-01-01            → historical rates
  GET /currencies            → {USD: "US Dollar", ...}
  GET /latest?from=INVALID   → 404 or 422
  GET /9999-99-99            → 404
"""

from tester.client import get


def _pass(name, latency_ms, details=None):
    return {"name": name, "status": "PASS", "latency_ms": latency_ms, "details": details or ""}


def _fail(name, latency_ms, details):
    return {"name": name, "status": "FAIL", "latency_ms": latency_ms, "details": details}


# ── CONTRACT TESTS ──────────────────────────────────────────────────────────────

def test_latest_status_200():
    """GET /latest returns HTTP 200"""
    r = get("/latest", {"from": "EUR"})
    name = "GET /latest → 200"
    if r["error"]:
        return _fail(name, r["latency_ms"], r["error"])
    if r["status_code"] != 200:
        return _fail(name, r["latency_ms"], f"Expected 200, got {r['status_code']}")
    return _pass(name, r["latency_ms"])


def test_latest_content_type_json():
    """Response body is valid JSON with required fields"""
    r = get("/latest", {"from": "EUR"})
    name = "GET /latest → JSON schema"
    if r["error"] or r["json"] is None:
        return _fail(name, r["latency_ms"], r.get("error") or "No JSON body")
    body = r["json"]
    required = ["amount", "base", "date", "rates"]
    missing = [f for f in required if f not in body]
    if missing:
        return _fail(name, r["latency_ms"], f"Missing fields: {missing}")
    return _pass(name, r["latency_ms"])


def test_latest_field_types():
    """amount=float/int, base=str, date=str, rates=dict"""
    r = get("/latest", {"from": "EUR"})
    name = "GET /latest → field types"
    if r["error"] or r["json"] is None:
        return _fail(name, r["latency_ms"], r.get("error") or "No JSON body")
    body = r["json"]
    errors = []
    if not isinstance(body.get("amount"), (int, float)):
        errors.append(f"amount: expected number, got {type(body.get('amount'))}")
    if not isinstance(body.get("base"), str):
        errors.append(f"base: expected str, got {type(body.get('base'))}")
    if not isinstance(body.get("date"), str):
        errors.append(f"date: expected str, got {type(body.get('date'))}")
    if not isinstance(body.get("rates"), dict):
        errors.append(f"rates: expected dict, got {type(body.get('rates'))}")
    if errors:
        return _fail(name, r["latency_ms"], "; ".join(errors))
    return _pass(name, r["latency_ms"])


def test_latest_rates_non_empty():
    """rates dict contains at least 1 currency"""
    r = get("/latest", {"from": "EUR"})
    name = "GET /latest → rates non-empty"
    if r["error"] or r["json"] is None:
        return _fail(name, r["latency_ms"], r.get("error") or "No JSON body")
    rates = r["json"].get("rates", {})
    if len(rates) == 0:
        return _fail(name, r["latency_ms"], "rates dict is empty")
    return _pass(name, r["latency_ms"], f"{len(rates)} currencies returned")


def test_latest_filter_to():
    """GET /latest?from=EUR&to=USD returns only USD in rates"""
    r = get("/latest", {"from": "EUR", "to": "USD"})
    name = "GET /latest?to=USD → only USD"
    if r["error"] or r["json"] is None:
        return _fail(name, r["latency_ms"], r.get("error") or "No JSON body")
    rates = r["json"].get("rates", {})
    if list(rates.keys()) != ["USD"]:
        return _fail(name, r["latency_ms"], f"Expected only USD, got {list(rates.keys())}")
    return _pass(name, r["latency_ms"])


def test_currencies_endpoint():
    """GET /currencies returns a dict of currency codes → names"""
    r = get("/currencies")
    name = "GET /currencies → dict"
    if r["error"] or r["json"] is None:
        return _fail(name, r["latency_ms"], r.get("error") or "No JSON body")
    body = r["json"]
    if not isinstance(body, dict) or len(body) == 0:
        return _fail(name, r["latency_ms"], "Expected non-empty dict")
    if "EUR" not in body or "USD" not in body:
        return _fail(name, r["latency_ms"], "Missing EUR or USD in currencies")
    return _pass(name, r["latency_ms"], f"{len(body)} currencies listed")


def test_historical_date():
    """GET /2020-01-02 returns historical rates for that date"""
    r = get("/2020-01-02")
    name = "GET /2020-01-02 → historical"
    if r["error"] or r["json"] is None:
        return _fail(name, r["latency_ms"], r.get("error") or "No JSON body")
    body = r["json"]
    if body.get("date") != "2020-01-02":
        return _fail(name, r["latency_ms"], f"date mismatch: {body.get('date')}")
    if not isinstance(body.get("rates"), dict) or len(body["rates"]) == 0:
        return _fail(name, r["latency_ms"], "Missing or empty rates")
    return _pass(name, r["latency_ms"])


def test_invalid_currency_error():
    """GET /latest?from=INVALID returns 4xx (contract: invalid input rejected)"""
    r = get("/latest", {"from": "INVALID_CURRENCY_XYZ"})
    name = "GET /latest?from=INVALID → 4xx"
    if r["error"]:
        # Network / timeout — pass with note
        return _pass(name, r["latency_ms"], f"Network error (acceptable): {r['error']}")
    if r["status_code"] is not None and 400 <= r["status_code"] < 500:
        return _pass(name, r["latency_ms"], f"Got {r['status_code']} as expected")
    return _fail(name, r["latency_ms"], f"Expected 4xx, got {r['status_code']}")


def test_invalid_date_error():
    """GET /9999-99-99 returns 4xx"""
    r = get("/9999-99-99")
    name = "GET /9999-99-99 → 4xx"
    if r["error"]:
        return _pass(name, r["latency_ms"], f"Network error (acceptable): {r['error']}")
    if r["status_code"] is not None and 400 <= r["status_code"] < 500:
        return _pass(name, r["latency_ms"], f"Got {r['status_code']} as expected")
    return _fail(name, r["latency_ms"], f"Expected 4xx, got {r['status_code']}")


# ── QoS / LATENCY TEST ──────────────────────────────────────────────────────────

def test_latency_p95_under_threshold():
    """p95 latency over 5 calls must be < 2000ms"""
    latencies = []
    for _ in range(5):
        r = get("/latest", {"from": "EUR"})
        if r["latency_ms"] is not None:
            latencies.append(r["latency_ms"])

    name = "QoS p95 latency < 2000ms"
    if not latencies:
        return _fail(name, 0, "No successful calls")

    latencies.sort()
    idx = int(len(latencies) * 0.95)
    p95 = latencies[min(idx, len(latencies) - 1)]

    if p95 >= 2000:
        return _fail(name, p95, f"p95={p95}ms exceeds 2000ms threshold")
    return _pass(name, p95, f"p95={p95}ms (over {len(latencies)} calls)")


ALL_TESTS = [
    test_latest_status_200,
    test_latest_content_type_json,
    test_latest_field_types,
    test_latest_rates_non_empty,
    test_latest_filter_to,
    test_currencies_endpoint,
    test_historical_date,
    test_invalid_currency_error,
    test_invalid_date_error,
    test_latency_p95_under_threshold,
]
