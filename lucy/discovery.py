"""Bounded metadata-only intake. Repository contents are never executed."""
from collections import Counter
from pathlib import Path
import os

EXCLUDED = {".git", ".lucy", ".env", "node_modules", ".venv", "vendor", "__pycache__"}
LANGUAGES = {".py": "Python", ".js": "JavaScript", ".ts": "TypeScript", ".java": "Java", ".go": "Go", ".rs": "Rust", ".cs": "C#"}


def inspect_repository(path, limit=5000):
    root = Path(path).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Repository must be a directory")
    counts, manifests, tests = Counter(), [], []
    total = 0
    truncated = False
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED and not d.startswith('.') and not (Path(directory) / d).is_symlink())
        for name in sorted(files):
            file = Path(directory) / name
            if file.is_symlink() or name.startswith('.'):
                continue
            total += 1
            if total > limit:
                truncated = True
                break
            counts[LANGUAGES.get(file.suffix, "Other")] += 1
            relative = str(file.relative_to(root))
            if name in {"package.json", "pyproject.toml", "requirements.txt", "go.mod", "Cargo.toml", "Dockerfile"}:
                manifests.append(relative)
            if name.startswith("test_") or ".test." in name or ".spec." in name:
                tests.append(relative)
        if truncated:
            break
    return {"version": 1, "verified": {"files_scanned": min(total, limit), "language_file_counts": dict(counts), "manifest_paths": manifests, "test_paths": tests},
            "inferred": ["Language labels are inferred from file extensions; test paths do not establish coverage."],
            "unknown": ["Runtime behavior", "Dependency versions and vulnerabilities", "Production topology", "Authentication", "Business contracts"],
            "truncated": truncated, "scope": "metadata only; no file contents retained or executed"}
