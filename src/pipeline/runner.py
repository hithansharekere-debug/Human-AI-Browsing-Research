"""Pipeline Orchestrator & Runner Module.

Role: Person B (Analysis Lead)
Coordinates the sequential execution of dataset verification, windowing,
feature extraction, statistical testing, modeling, negative controls, and
reproducibility bundling.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from src.utils.logging_config import configure_logging
from src.utils.paths import get_repo_root, load_yaml_config, resolve_project_paths
from src.pipeline.dataset_verification import (
    verify_dataset,
    save_verification_report,
)
from src.pipeline.reproducibility import generate_reproducibility_manifest

logger = logging.getLogger("human_ai_egress.runner")


class PipelineOrchestrator:
    """Manages the full end-to-end analysis lifecycle."""

    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path
        self.config: Dict[str, Any] = load_yaml_config(config_path)
        self.paths = resolve_project_paths(self.config)
        self.random_seed = self.config.get("project", {}).get("random_seed", 42)
        self.project_name = self.config.get("project", {}).get("name", "Human-AI-Egress")

    def run_verification_phase(self) -> bool:
        """Phase 1: Validates external raw dataset against manifest."""
        logger.info("================== PHASE 1: DATASET VERIFICATION ==================")
        data_cfg = self.config.get("data_source", {})
        manifest_path = Path(data_cfg.get("external_manifest_path", ""))
        dataset_dir = Path(data_cfg.get("external_dataset_dir", ""))
        expected_count = self.config.get("project", {}).get("session_count_expected", 92)

        report = verify_dataset(
            manifest_path=manifest_path,
            dataset_dir=dataset_dir,
            expected_session_count=expected_count,
        )

        out_report = self.paths["output"] / "verification_report.json"
        save_verification_report(report, out_report)

        if not report.is_dataset_complete:
            logger.warning(
                "Dataset verification: Dataset is not yet fully populated or verified (%d/%d valid).",
                report.total_valid,
                report.total_expected,
            )
            return False

        logger.info("Phase 1 verified successfully. All %d sessions validated.", report.total_valid)
        return True

    def run_reproducibility_phase(self) -> None:
        """Phase 6: Generates reproducibility manifest locking deliverables."""
        logger.info("================== PHASE 6: REPRODUCIBILITY LOCK ==================")
        manifest_dest = self.paths["output"] / "reproducibility_manifest.json"
        generate_reproducibility_manifest(
            project_name=self.project_name,
            random_seed=self.random_seed,
            repo_root=get_repo_root(),
            output_directories=[self.paths["results"], self.paths["figures"], self.paths["output"]],
            destination_file=manifest_dest,
        )
        logger.info("Reproducibility lock generated.")

    def execute(self, dry_run: bool = False) -> None:
        """Executes the pipeline up to permissible boundary."""
        logger.info("Starting pipeline execution for: %s", self.project_name)
        logger.info("Dry-run mode: %s", dry_run)

        # Always run verification
        is_verified = self.run_verification_phase()

        if dry_run:
            logger.info("Dry-run complete: Pipeline structure, paths, and config validated.")
            self.run_reproducibility_phase()
            return

        if not is_verified:
            logger.warning(
                "Halting pipeline before feature extraction: External frozen dataset is pending or incomplete."
            )
            self.run_reproducibility_phase()
            return

        logger.info(
            "External dataset verified. Ready for feature extraction and statistical analysis "
            "upon Person C approval."
        )
        self.run_reproducibility_phase()
