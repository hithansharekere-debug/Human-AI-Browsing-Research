"""Filesystem path utilities and project boundary management.

Ensures strict decoupling between the code repository and external datasets.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any
import yaml


def get_repo_root() -> Path:
    """Returns the absolute Path to the repository root directory."""
    return Path(__file__).resolve().parent.parent.parent


def load_yaml_config(config_path: Path) -> Dict[str, Any]:
    """Loads and validates a YAML configuration file.

    Args:
        config_path: Path to configuration file.

    Returns:
        Dictionary containing configuration parameters.

    Raises:
        FileNotFoundError: If configuration file does not exist.
        yaml.YAMLError: If YAML file is malformed.
    """
    resolved_path = config_path if config_path.is_absolute() else get_repo_root() / config_path
    if not resolved_path.exists():
        raise FileNotFoundError(f"Configuration file not found at: {resolved_path}")

    with open(resolved_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Configuration at {resolved_path} must be a dictionary.")

    return data


def resolve_project_paths(config: Dict[str, Any]) -> Dict[str, Path]:
    """Resolves standard output, results, figures, and reports directories.

    Args:
        config: Parsed configuration dictionary.

    Returns:
        Mapping of directory names to absolute Path objects.
    """
    root = get_repo_root()
    paths_cfg = config.get("paths", {})

    resolved = {
        "root": root,
        "results": root / paths_cfg.get("results_dir", "results"),
        "figures": root / paths_cfg.get("figures_dir", "figures"),
        "output": root / paths_cfg.get("output_dir", "output"),
        "reports": root / paths_cfg.get("reports_dir", "reports"),
    }

    # Ensure output directories exist
    for key in ["results", "figures", "output", "reports"]:
        resolved[key].mkdir(parents=True, exist_ok=True)

    return resolved
