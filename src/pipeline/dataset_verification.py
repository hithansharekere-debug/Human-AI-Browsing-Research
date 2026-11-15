"""Dataset Verification Module.

Role: Person B (Analysis Lead)
Verifies integrity, completeness, and cryptographic hashes of Person A's
frozen egress network dataset before allowing downstream processing.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("human_ai_egress.dataset_verification")


@dataclass(frozen=True)
class SessionVerificationRecord:
    """Record of cryptographic verification for a single session file."""
    session_id: str
    file_path: Path
    expected_sha256: str
    calculated_sha256: str
    is_valid: bool
    file_size_bytes: int
    error_message: Optional[str] = None


@dataclass
class DatasetVerificationReport:
    """Summary report across all verified sessions."""
    total_expected: int
    total_found: int
    total_valid: int
    is_dataset_complete: bool
    records: List[SessionVerificationRecord] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "total_expected": self.total_expected,
            "total_found": self.total_found,
            "total_valid": self.total_valid,
            "is_dataset_complete": self.is_dataset_complete,
            "records": [
                {
                    "session_id": r.session_id,
                    "expected_sha256": r.expected_sha256,
                    "calculated_sha256": r.calculated_sha256,
                    "is_valid": r.is_valid,
                    "file_size_bytes": r.file_size_bytes,
                    "error_message": r.error_message,
                }
                for r in self.records
            ],
        }


def compute_sha256(file_path: Path, chunk_size: int = 65536) -> str:
    """Computes SHA-256 digest of a target file.

    Args:
        file_path: Path to target file.
        chunk_size: Block size in bytes for reading.

    Returns:
        Hexadecimal SHA-256 hash string.

    Raises:
        FileNotFoundError: If target file does not exist.
        PermissionError: If file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for hash calculation: {file_path}")

    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def parse_manifest_file(manifest_path: Path) -> Dict[str, str]:
    """Parses a standard SHA256 manifest file formatted as '<hash>  <filename>'.

    Args:
        manifest_path: Path to the external manifest.sha256 file.

    Returns:
        Mapping of filename/session_id to expected SHA-256 string.
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    manifest_map: Dict[str, str] = {}
    with open(manifest_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(maxsplit=1)
            if len(parts) == 2:
                sha_hash, filename = parts[0].strip(), parts[1].strip()
                manifest_map[filename] = sha_hash
    return manifest_map


def verify_dataset(
    manifest_path: Path,
    dataset_dir: Path,
    expected_session_count: int = 92,
) -> DatasetVerificationReport:
    """Verifies Person A's external frozen dataset against the provided manifest.

    Args:
        manifest_path: Path to manifest.sha256.
        dataset_dir: Path to directory holding frozen pcap/session archives.
        expected_session_count: Expected number of study sessions (default: 92).

    Returns:
        DatasetVerificationReport detailing verification outcome.
    """
    logger.info("Initiating dataset verification gate...")
    logger.info("Verifying against external directory: %s", dataset_dir)

    if not dataset_dir.exists():
        logger.warning("External dataset directory does not exist yet: %s", dataset_dir)
        return DatasetVerificationReport(
            total_expected=expected_session_count,
            total_found=0,
            total_valid=0,
            is_dataset_complete=False,
            records=[],
        )

    manifest_entries = parse_manifest_file(manifest_path)
    records: List[SessionVerificationRecord] = []
    valid_count = 0

    for filename, expected_hash in manifest_entries.items():
        session_file = dataset_dir / filename
        session_id = session_file.stem

        if not session_file.exists():
            records.append(
                SessionVerificationRecord(
                    session_id=session_id,
                    file_path=session_file,
                    expected_sha256=expected_hash,
                    calculated_sha256="",
                    is_valid=False,
                    file_size_bytes=0,
                    error_message="File missing from dataset directory",
                )
            )
            continue

        try:
            calc_hash = compute_sha256(session_file)
            is_valid = calc_hash.lower() == expected_hash.lower()
            if is_valid:
                valid_count += 1
            else:
                logger.error("Hash mismatch for session: %s", session_id)

            records.append(
                SessionVerificationRecord(
                    session_id=session_id,
                    file_path=session_file,
                    expected_sha256=expected_hash,
                    calculated_sha256=calc_hash,
                    is_valid=is_valid,
                    file_size_bytes=session_file.stat().st_size,
                    error_message=None if is_valid else "SHA-256 hash mismatch",
                )
            )
        except Exception as exc:
            logger.exception("Error verifying session file %s: %s", session_id, exc)
            records.append(
                SessionVerificationRecord(
                    session_id=session_id,
                    file_path=session_file,
                    expected_sha256=expected_hash,
                    calculated_sha256="",
                    is_valid=False,
                    file_size_bytes=0,
                    error_message=str(exc),
                )
            )

    is_complete = (valid_count == expected_session_count) and (len(manifest_entries) == expected_session_count)
    logger.info(
        "Verification complete. Valid: %d/%d (Complete: %s)",
        valid_count,
        expected_session_count,
        is_complete,
    )

    return DatasetVerificationReport(
        total_expected=expected_session_count,
        total_found=len(records),
        total_valid=valid_count,
        is_dataset_complete=is_complete,
        records=records,
    )


def save_verification_report(report: DatasetVerificationReport, output_path: Path) -> None:
    """Saves the verification report to JSON format."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2)
    logger.info("Verification report saved to: %s", output_path)
