"""Reproducibility & Package Manifest Module.

Role: Person B (Analysis Lead)
Captures execution environment metadata, software dependencies, random seeds,
and generates SHA-256 digests for all generated deliverables for Person C.
"""

from __future__ import annotations

import hashlib
import json
import logging
import platform
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("human_ai_egress.reproducibility")


@dataclass
class ReproducibilityManifest:
    """Complete manifest locking all parameters, environment state, and output hashes."""
    project_name: str
    timestamp_utc: str
    python_version: str
    operating_system: str
    architecture: str
    git_commit_sha: Optional[str]
    random_seed: int
    installed_packages: Dict[str, str]
    output_checksums: Dict[str, str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "timestamp_utc": self.timestamp_utc,
            "environment": {
                "python_version": self.python_version,
                "operating_system": self.operating_system,
                "architecture": self.architecture,
                "git_commit_sha": self.git_commit_sha,
                "random_seed": self.random_seed,
            },
            "installed_packages": self.installed_packages,
            "output_checksums": self.output_checksums,
        }


def get_git_commit_sha(repo_root: Path) -> Optional[str]:
    """Attempts to retrieve the current git commit SHA if repository is under git."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return None


def get_installed_package_versions() -> Dict[str, str]:
    """Retrieves pinned versions of installed scientific libraries."""
    packages = [
        "numpy",
        "pandas",
        "scipy",
        "scikit-learn",
        "pyarrow",
        "pyyaml",
        "matplotlib",
        "pytest",
        "nfstream",
    ]
    versions: Dict[str, str] = {}
    for pkg in packages:
        try:
            mod = __import__(pkg.replace("-", "_"))
            versions[pkg] = getattr(mod, "__version__", "unknown")
        except ImportError:
            versions[pkg] = "not_installed"
    return versions


def hash_output_files(directories: List[Path]) -> Dict[str, str]:
    """Computes SHA-256 digests for all generated non-empty files in output directories."""
    checksums: Dict[str, str] = {}
    for d in directories:
        if not d.exists():
            continue
        for file_path in d.rglob("*"):
            if file_path.is_file() and not file_path.name.endswith(".gitkeep"):
                hasher = hashlib.sha256()
                with open(file_path, "rb") as f:
                    while chunk := f.read(65536):
                        hasher.update(chunk)
                checksums[str(file_path.name)] = hasher.hexdigest()
    return checksums


def generate_reproducibility_manifest(
    project_name: str,
    random_seed: int,
    repo_root: Path,
    output_directories: List[Path],
    destination_file: Path,
) -> ReproducibilityManifest:
    """Generates and writes a comprehensive reproducibility manifest."""
    manifest = ReproducibilityManifest(
        project_name=project_name,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
        python_version=sys.version,
        operating_system=f"{platform.system()} {platform.release()}",
        architecture=platform.machine(),
        git_commit_sha=get_git_commit_sha(repo_root),
        random_seed=random_seed,
        installed_packages=get_installed_package_versions(),
        output_checksums=hash_output_files(output_directories),
    )

    destination_file.parent.mkdir(parents=True, exist_ok=True)
    with open(destination_file, "w", encoding="utf-8") as f:
        json.dump(manifest.to_dict(), f, indent=2)

    logger.info("Reproducibility manifest successfully written to: %s", destination_file)
    return manifest
