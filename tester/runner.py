import datetime
from tester.tests import ALL_TESTS


def run_all_tests() -> dict:
    """Run all tests and return a structured run result."""
    results = []
    for test_fn in ALL_TESTS:
        try:
            result = test_fn()
        except Exception as e:
            result = {
                "name": test_fn.__name__,
                "status": "ERROR",
                "latency_ms": 0,
                "details": str(e),
            }
        results.append(result)

    passed = sum(1 for t in results if t["status"] == "PASS")
    failed = len(results) - passed
    total = len(results)

    latencies = [t["latency_ms"] for t in results if t.get("latency_ms")]
    avg_latency = int(sum(latencies) / len(latencies)) if latencies else 0

    sorted_lat = sorted(latencies)
    p95_idx = int(len(sorted_lat) * 0.95)
    p95_latency = sorted_lat[min(p95_idx, len(sorted_lat) - 1)] if sorted_lat else 0

    return {
        "api": "Frankfurter",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "summary": {
            "passed": passed,
            "failed": failed,
            "total": total,
            "error_rate": round(failed / total, 3) if total else 0,
            "latency_ms_avg": avg_latency,
            "latency_ms_p95": p95_latency,
        },
        "tests": results,
    }
