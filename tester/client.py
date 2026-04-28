import time
import requests

BASE_URL = "https://api.frankfurter.app"
TIMEOUT = 3  # seconds
MAX_RETRIES = 1


def get(path: str, params: dict = None) -> dict:
    """
    Makes a GET request with timeout, 1 retry, and 429/5xx handling.
    Returns a dict with: status_code, json (or None), latency_ms, error (or None).
    """
    url = BASE_URL + path
    attempt = 0

    while attempt <= MAX_RETRIES:
        start = time.perf_counter()
        try:
            resp = requests.get(url, params=params, timeout=TIMEOUT)
            latency_ms = int((time.perf_counter() - start) * 1000)

            if resp.status_code == 429:
                # Rate limited — wait 2s and retry once
                if attempt < MAX_RETRIES:
                    time.sleep(2)
                    attempt += 1
                    continue
                return {
                    "status_code": 429,
                    "json": None,
                    "latency_ms": latency_ms,
                    "error": "Rate limited (429)",
                }

            try:
                body = resp.json()
            except Exception:
                body = None

            return {
                "status_code": resp.status_code,
                "json": body,
                "latency_ms": latency_ms,
                "error": None,
            }

        except requests.exceptions.Timeout:
            latency_ms = int((time.perf_counter() - start) * 1000)
            if attempt < MAX_RETRIES:
                attempt += 1
                continue
            return {
                "status_code": None,
                "json": None,
                "latency_ms": latency_ms,
                "error": "Timeout",
            }

        except requests.exceptions.RequestException as e:
            latency_ms = int((time.perf_counter() - start) * 1000)
            return {
                "status_code": None,
                "json": None,
                "latency_ms": latency_ms,
                "error": str(e),
            }

    # Should not reach here
    return {"status_code": None, "json": None, "latency_ms": 0, "error": "Unknown"}
