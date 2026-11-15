"""Tests dataset verification and cryptographic hashing logic."""

import hashlib
from pathlib import Path
import pytest
from src.pipeline.dataset_verification import (
    compute_sha256,
    parse_manifest_file,
    verify_dataset,
)


def test_compute_sha256(tmp_path: Path):
    test_file = tmp_path / "sample.bin"
    test_content = b"Egress Network Traces Test Sample Content"
    test_file.write_bytes(test_content)

    expected_hash = hashlib.sha256(test_content).hexdigest()
    computed_hash = compute_sha256(test_file)

    assert computed_hash == expected_hash


def test_parse_manifest_and_verify(tmp_path: Path):
    data_dir = tmp_path / "frozen_pcaps"
    data_dir.mkdir()

    file1 = data_dir / "session_001.bin"
    file1.write_bytes(b"session 1 raw payload simulation")
    hash1 = hashlib.sha256(b"session 1 raw payload simulation").hexdigest()

    file2 = data_dir / "session_002.bin"
    file2.write_bytes(b"session 2 raw payload simulation")
    hash2 = hashlib.sha256(b"session 2 raw payload simulation").hexdigest()

    manifest_file = tmp_path / "manifest.sha256"
    manifest_file.write_text(f"{hash1}  session_001.bin\n{hash2}  session_002.bin\n", encoding="utf-8")

    parsed = parse_manifest_file(manifest_file)
    assert len(parsed) == 2
    assert parsed["session_001.bin"] == hash1

    report = verify_dataset(
        manifest_path=manifest_file,
        dataset_dir=data_dir,
        expected_session_count=2,
    )
    assert report.total_expected == 2
    assert report.total_found == 2
    assert report.total_valid == 2
    assert report.is_dataset_complete is True
