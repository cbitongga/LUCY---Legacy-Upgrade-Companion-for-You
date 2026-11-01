"""Fail-closed acceptance; no blended confidence score."""
DIMENSIONS = ["functional", "required_tests", "data_integrity", "security", "performance", "memory", "soak", "cloud", "operations", "human_approval"]


def decide(gates):
    by_name = {gate["name"]: gate for gate in gates}
    if any(g.get("status") in {"failed", "blocked"} for g in gates):
        return "Blocked"
    if any(name not in by_name or by_name[name].get("status") != "passed" for name in DIMENSIONS if name != "human_approval"):
        return "Incomplete"
    if by_name.get("human_approval", {}).get("status") != "passed":
        return "Needs Review"
    return "Accepted"


def compare(baseline, candidate):
    old = {case["id"]: case for case in baseline["cases"]}
    new = {case["id"]: case for case in candidate["cases"]}
    return [{"case": key, "legacy": old.get(key), "candidate": new.get(key)} for key in sorted(old.keys() | new.keys()) if old.get(key) != new.get(key)]


def critic(baseline, candidate, author="implementation", reviewer="independent-checks"):
    if author == reviewer:
        raise ValueError("An implementation actor cannot certify its own remediation")
    findings = []
    mismatches = compare(baseline, candidate)
    if mismatches:
        findings.append({"kind": "functional", "severity": "critical", "title": "Observable invoice contract changed", "mismatches": mismatches})
    if candidate["memory"]["growth_bytes"] > 65536:
        findings.append({"kind": "memory", "severity": "critical", "title": "Retained allocations exceed approved 64 KiB growth budget", "growth_bytes": candidate["memory"]["growth_bytes"]})
    return {"reviewer": reviewer, "author": author, "findings": findings,
            "limitations": ["Deterministic checks, not an independent AI or human review", "Six scenarios; not exhaustive behavioral equivalence", "Short allocation probe; not soak, RSS, security, or cloud assurance"]}
