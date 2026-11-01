"""Fixed trusted fixture runner, invoked in a separate Python process.

Process separation is not a sandbox. Never route arbitrary repositories here.
"""
import gc
import importlib.util
import json
from pathlib import Path
import sys
import time
import tracemalloc

CASES = [
    {"id": "ordinary", "items": [{"price": "12.50", "quantity": 2}]},
    {"id": "round_half_up", "items": [{"price": "1.005", "quantity": 1}]},
    {"id": "empty", "items": []},
    {"id": "negative", "items": [{"price": "10", "quantity": -1}]},
    {"id": "zero", "items": [{"price": "0", "quantity": 0}]},
    {"id": "fractional", "items": [{"price": "0.10", "quantity": 3}, {"price": "0.20", "quantity": 1}]},
]


def measure(path):
    spec = importlib.util.spec_from_file_location("invoice_target", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    results = []
    for case in CASES:
        try:
            output = module.invoice(case["items"])
        except Exception as exc:
            output = {"exception": type(exc).__name__, "message": str(exc)}
        results.append({**case, "output": output})
    # Warm up before measuring, then collect garbage between equal workload batches.
    for _ in range(100):
        module.invoice(CASES[0]["items"])
    tracemalloc.start()
    samples = []
    start = time.monotonic()
    for batch in range(6):
        for _ in range(200):
            module.invoice(CASES[0]["items"])
        gc.collect()
        current, peak = tracemalloc.get_traced_memory()
        samples.append({"requests": (batch + 1) * 200, "retained_bytes": current, "peak_bytes": peak})
    tracemalloc.stop()
    return {"cases": results, "memory": {"samples": samples, "growth_bytes": samples[-1]["retained_bytes"] - samples[0]["retained_bytes"],
            "duration_seconds": time.monotonic() - start, "method": "Python traced allocations, six batches of 200 requests after warm-up and GC; excludes native memory and RSS"}, "python": sys.version}


if __name__ == "__main__":
    print(json.dumps(measure(Path(sys.argv[1]))))
