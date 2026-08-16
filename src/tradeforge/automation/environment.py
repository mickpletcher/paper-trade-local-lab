from __future__ import annotations

import hashlib
import json
from importlib.metadata import distributions
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

IGNORED_INSTALLED_PACKAGES = {"pip", "setuptools", "tradeforge", "wheel"}


def inspect_environment(lock_path: Path = Path("requirements.lock")) -> dict[str, object]:
    expected = _read_locked_versions(lock_path)
    installed: dict[str, str] = {}
    for distribution in distributions():
        try:
            name = distribution.metadata["Name"]
        except KeyError:
            continue
        if name:
            installed[str(canonicalize_name(name))] = distribution.version
    missing = sorted(name for name in expected if name not in installed)
    mismatched = [
        {"package": name, "expected": expected[name], "installed": installed[name]}
        for name in sorted(expected.keys() & installed.keys())
        if installed[name] != expected[name]
    ]
    undeclared = sorted(name for name in installed.keys() - expected.keys() - IGNORED_INSTALLED_PACKAGES)
    return {
        "status": "healthy" if not missing and not mismatched and not undeclared else "drifted",
        "missing": missing,
        "mismatched": mismatched,
        "undeclared": undeclared,
        "locked_count": len(expected),
        "installed_count": len(installed),
    }


def verify_lock_provenance(lock_path: Path, metadata_path: Path) -> dict[str, object]:
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    digest = hashlib.sha256(lock_path.read_bytes()).hexdigest()
    if metadata.get("sha256") != digest:
        raise ValueError("Dependency lock digest does not match provenance metadata.")
    source = metadata.get("source_index")
    if source != "https://pypi.org/simple":
        raise ValueError("Dependency provenance must use the approved PyPI source index.")
    if metadata.get("attestation") != "github-oidc-sigstore":
        raise ValueError("Dependency lock metadata must declare GitHub OIDC signing.")
    if metadata.get("attestation_workflow") != ".github/workflows/ci.yml":
        raise ValueError("Dependency lock attestation workflow is not approved.")
    command = metadata.get("generation_command")
    if not isinstance(command, str) or "--universal" not in command or "--python-version 3.11" not in command:
        raise ValueError("Dependency provenance generation command is incomplete.")
    return {"status": "verified", "sha256": digest, "source_index": source}


def _read_locked_versions(lock_path: Path) -> dict[str, str]:
    expected: dict[str, str] = {}
    for line in lock_path.read_text(encoding="utf-8").splitlines():
        if not line or line[0].isspace() or line.startswith("#") or "==" not in line:
            continue
        requirement = Requirement(line)
        if requirement.marker is not None and not requirement.marker.evaluate():
            continue
        versions = [specifier.version for specifier in requirement.specifier if specifier.operator == "=="]
        if len(versions) != 1:
            raise ValueError(f"Locked requirement must contain one exact version: {line}")
        expected[str(canonicalize_name(requirement.name))] = versions[0]
    return expected
