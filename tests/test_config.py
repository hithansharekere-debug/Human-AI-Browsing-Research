"""Tests configuration validation and schema checks."""

from pathlib import Path
import pytest
from src.utils.paths import get_repo_root, load_yaml_config, resolve_project_paths


def test_pilot_v1_config_exists():
    root = get_repo_root()
    cfg_path = root / "config" / "pilot_v1.yaml"
    assert cfg_path.exists(), "config/pilot_v1.yaml must exist."


def test_pilot_v1_config_structure():
    root = get_repo_root()
    cfg = load_yaml_config(root / "config" / "pilot_v1.yaml")

    # Required top-level keys
    assert "project" in cfg
    assert "data_source" in cfg
    assert "windowing" in cfg
    assert "flow_extraction" in cfg
    assert "features" in cfg
    assert "statistics" in cfg
    assert "modeling" in cfg
    assert "paths" in cfg

    # Verify session count
    assert cfg["project"]["session_count_expected"] == 92


def test_resolve_project_paths():
    root = get_repo_root()
    cfg = load_yaml_config(root / "config" / "pilot_v1.yaml")
    paths = resolve_project_paths(cfg)

    for key in ["results", "figures", "output", "reports"]:
        assert key in paths
        assert paths[key].exists()
