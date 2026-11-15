#!/usr/bin/env python3
"""Main Pipeline CLI Entrypoint.

Role: Person B (Analysis Lead)
Executes or dry-runs the client egress research pipeline.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.utils.logging_config import configure_logging
from src.pipeline.runner import PipelineOrchestrator


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Human vs. AI Client Egress Analysis Pipeline (Person B)"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/pilot_v1.yaml"),
        help="Path to YAML configuration file (default: config/pilot_v1.yaml)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration, paths, and reproducibility locks without processing full dataset",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose DEBUG logging",
    )

    args = parser.parse_args()

    import logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = configure_logging(log_level=log_level)

    try:
        orchestrator = PipelineOrchestrator(config_path=args.config)
        orchestrator.execute(dry_run=args.dry_run)
        return 0
    except Exception as exc:
        logger.exception("Pipeline execution failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
