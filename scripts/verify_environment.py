#!/usr/bin/env python3
"""Environment and Dependency Verification Script.

Role: Person B (Analysis Lead)
Verifies that the Python environment meets all dependency, version,
and project configuration requirements.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_PACKAGES = [
    ("numpy", "Core numeric array processing"),
    ("pandas", "Tabular feature processing"),
    ("scipy", "Statistical hypothesis testing & distributions"),
    ("sklearn", "Machine learning evaluation & cross-validation"),
    ("pyarrow", "Parquet serialization"),
    ("yaml", "Configuration loading (PyYAML)"),
    ("matplotlib", "Visualization and figure generation"),
    ("pytest", "Automated testing framework"),
]

OPTIONAL_PACKAGES = [
    ("nfstream", "Bidirectional egress flow parsing (required for raw pcap extraction)"),
]


def check_python_version() -> bool:
    """Ensures Python version is >= 3.10."""
    print(f"[*] Checking Python version: {sys.version.split()[0]}")
    if sys.version_info < (3, 10):
        print(f"[-] Python 3.10 or newer is required. Found: {sys.version}")
        return False
    print("  [OK] Python version satisfies requirements (>= 3.10)")
    return True


def check_dependencies() -> bool:
    """Verifies that all required packages can be imported."""
    all_ok = True
    print("\n[*] Checking required scientific libraries:")
    for pkg_name, description in REQUIRED_PACKAGES:
        try:
            mod = __import__(pkg_name)
            ver = getattr(mod, "__version__", "unknown")
            print(f"  [OK] {pkg_name:<12} (v{ver:<8}) - {description}")
        except ImportError:
            print(f"  [MISSING] {pkg_name:<12} - {description}")
            all_ok = False

    print("\n[*] Checking domain-specific packages:")
    for pkg_name, description in OPTIONAL_PACKAGES:
        try:
            mod = __import__(pkg_name)
            ver = getattr(mod, "__version__", "unknown")
            print(f"  [OK] {pkg_name:<12} (v{ver:<8}) - {description}")
        except ImportError:
            print(f"  [NOT INSTALLED] {pkg_name:<12} - {description} (Install via 'pip install nfstream')")

    return all_ok


def check_project_structure() -> bool:
    """Verifies expected repository folders and templates exist."""
    print("\n[*] Checking project folder structure and key files:")
    required_paths = [
        "docs/project_overview.md",
        "docs/data_handling_security.md",
        "docs/workflow.md",
        "docs/final_deliverables.md",
        "features/SPEC.md",
        "features/flow_rules.yaml",
        "analysis/PREREG.md",
        "analysis/DEVIATIONS.md",
        "config/pilot_v1.yaml",
        "reports/methods_section.tex",
        "reports/B_to_C_MEMO.md",
        "reports/report_outline.md",
        "src/pipeline/dataset_verification.py",
        "src/pipeline/window_extraction.py",
        "src/pipeline/flow_extraction.py",
        "src/pipeline/flow_classification.py",
        "src/pipeline/feature_engineering.py",
        "src/pipeline/statistics.py",
        "src/pipeline/model_evaluation.py",
        "src/pipeline/negative_controls.py",
        "src/pipeline/sensitivity_analysis.py",
        "src/pipeline/reproducibility.py",
        "src/pipeline/runner.py",
        "results",
        "figures",
        "output",
    ]
    missing = []
    for rel_path in required_paths:
        target = REPO_ROOT / rel_path
        if not target.exists():
            missing.append(rel_path)

    if missing:
        print(f"[-] Missing repository paths: {missing}")
        return False

    print(f"  [OK] All {len(required_paths)} required templates, modules, and directories verified.")
    return True


def main() -> int:
    print("=" * 65)
    print(" HUMAN VS. AI EGRESS RESEARCH - ENVIRONMENT VERIFICATION")
    print("=" * 65)
    py_ok = check_python_version()
    struct_ok = check_project_structure()
    deps_ok = check_dependencies()

    print("\n" + "=" * 65)
    if py_ok and struct_ok and deps_ok:
        print("STATUS: ALL DEPENDENCIES AND PROJECT STRUCTURE SATISFIED.")
        print("=" * 65)
        return 0
    elif py_ok and struct_ok and not deps_ok:
        print("STATUS: PROJECT STRUCTURE VERIFIED. PYTHON DEPENDENCIES NEEDED.")
        print("Install required packages via:")
        print("  pip install -r requirements.txt")
        print("=" * 65)
        return 2
    else:
        print("STATUS: VERIFICATION FAILED.")
        print("=" * 65)
        return 1


if __name__ == "__main__":
    sys.exit(main())

