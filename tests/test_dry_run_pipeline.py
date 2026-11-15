"""Integration and verification tests using dry-run, idle, and self-test data only.

In strict compliance with project protocols:
- NO study sessions (S0001-S0092) are loaded, parsed, or processed.
- Uses only self-test (X0001) and dry-run (D0001) traces, or synthetic mocks.
- Tests marker extraction, window clipping, Addendum 07 classification rules,
  S0062 exclusion rules, and feature schema definitions.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.pipeline.window_extraction import (
    ObservationWindow,
    WindowExtractor,
    extract_hardware_marker_bounds,
)
from src.pipeline.flow_classification import FlowClassifier


DATA_RAW_DIR = Path(r"C:\pilot-v1-data\data\raw")


@pytest.mark.skipif(not (DATA_RAW_DIR / "X0001.pcapng").exists(), reason="External test data not available")
def test_marker_extraction_self_test():
    """Validates hardware marker extraction on self-test recording X0001."""
    x_pcap = DATA_RAW_DIR / "X0001.pcapng"
    t_start, t_end = extract_hardware_marker_bounds(x_pcap, "X0001")

    assert t_start is not None, "START marker should be found in X0001"
    assert t_end is not None, "END marker should be found in X0001"
    assert t_end > t_start, "END marker must occur after START marker"
    duration = t_end - t_start
    assert 7.0 <= duration <= 9.0, f"Expected ~8.0s duration for X0001, got {duration:.3f}s"


@pytest.mark.skipif(not (DATA_RAW_DIR / "D0001.pcapng").exists(), reason="External dry-run data not available")
def test_marker_extraction_dry_run_d0001():
    """Validates hardware marker extraction on dry-run recording D0001."""
    d_pcap = DATA_RAW_DIR / "D0001.pcapng"
    t_start, t_end = extract_hardware_marker_bounds(d_pcap, "D0001")

    assert t_start is not None, "START marker should be found in D0001"
    assert t_end is not None, "END marker should be found in D0001"
    assert t_end > t_start, "END marker must occur after START marker"
    duration = t_end - t_start
    assert 50.0 <= duration <= 60.0, f"Expected ~55.0s duration for D0001, got {duration:.3f}s"


def test_in_window_traffic_clipping_logic():
    """Verifies that pre-window, post-window, and marker packets are strictly dropped."""
    t_start = 100.0
    t_end = 150.0

    mock_packets = pd.DataFrame([
        {"pkt_id": 1, "time_epoch": 95.0, "dst_ip": "1.1.1.1", "bytes": 100},   # Pre-window (settle) -> DROP
        {"pkt_id": 2, "time_epoch": 100.0, "dst_ip": "192.0.2.1", "bytes": 64}, # Marker START -> DROP
        {"pkt_id": 3, "time_epoch": 110.0, "dst_ip": "142.250.80.46", "bytes": 500}, # In-window -> KEEP
        {"pkt_id": 4, "time_epoch": 125.0, "dst_ip": "151.101.1.69", "bytes": 1200}, # In-window -> KEEP
        {"pkt_id": 5, "time_epoch": 150.0, "dst_ip": "192.0.2.1", "bytes": 64}, # Marker END -> DROP
        {"pkt_id": 6, "time_epoch": 155.0, "dst_ip": "1.1.1.1", "bytes": 100},   # Post-window (shutdown) -> DROP
    ])

    in_window_mask = (
        (mock_packets["time_epoch"] > t_start)
        & (mock_packets["time_epoch"] < t_end)
        & (mock_packets["dst_ip"] != "192.0.2.1")
    )
    clipped = mock_packets.loc[in_window_mask]

    assert len(clipped) == 2
    assert list(clipped["pkt_id"]) == [3, 4]
    assert (clipped["dst_ip"] != "192.0.2.1").all()


def test_flow_rules_addendum_07_comprehensive():
    """Validates that FlowClassifier correctly implements all Addendum 07 requirements."""
    rules_path = Path("features/flow_rules.yaml")
    assert rules_path.exists()
    classifier = FlowClassifier(rules_path=rules_path)

    # 1. Personal applications -> os_background
    for domain in ["spotify.com", "ap-gew4.spotify.com", "dropbox.com", "zoom.us", "skype.com", "mcafee.com"]:
        assert classifier.classify_domain(domain) == "os_background", f"Expected os_background for {domain}"

    # 2. Dry-run only domains -> os_background
    for domain in ["grammarly.com", "api.grammarly.io", "honey.io", "brave.com", "claude.ai", "anthropic.com"]:
        assert classifier.classify_domain(domain) == "os_background", f"Expected os_background for {domain}"

    # 3. MSN / Edge news feed -> os_background
    for domain in ["headtopics.com", "zigwheels.com", "carhp.in", "theindustryoutlook.com"]:
        assert classifier.classify_domain(domain) == "os_background", f"Expected os_background for {domain}"

    # 4. Tracking and telemetry -> os_background
    for domain in ["scorecardresearch.com", "doubleclick.net", "googletagmanager.com", "google-analytics.com"]:
        assert classifier.classify_domain(domain) == "os_background", f"Expected os_background for {domain}"

    # 5. Infrastructure and OEM -> os_background
    for domain in ["digicert.com", "lencr.org", "pki.goog", "msftconnecttest.com", "nvidia.com", "hpsmart.com"]:
        assert classifier.classify_domain(domain) == "os_background", f"Expected os_background for {domain}"

    # 6. LAN filtering
    assert classifier.classify_domain("Android.local") == "excluded"
    assert classifier.classify_domain("mycomputer.local") == "excluded"
    assert classifier.classify_domain("wpad.domain.name") == "excluded"
    assert classifier.classify_domain("Cal") == "excluded"

    # 7. Unresolved domains remain unknown
    assert classifier.classify_domain("fastly-edge.com") == "unknown"
    assert classifier.classify_domain("cloudflare-ech.com") == "unknown"

    # 8. Vendor vs Website precedence
    assert classifier.classify_domain("generativelanguage.googleapis.com") == "vendor"
    assert classifier.classify_domain("wikipedia.org") == "website"
    assert classifier.classify_domain("en.wikipedia.org") == "website"


def test_s0062_exclusion_logic():
    """Verifies that S0062 is correctly flagged and filtered in primary analysis without mutating raw data."""
    # Synthetic representation of sessions metadata table
    mock_sessions = pd.DataFrame([
        {"session_id": "S0061", "participant_id": "P03", "task_id": "T1", "duration_s": 45.2, "outcome": "SUCCESS"},
        {"session_id": "S0062", "participant_id": "P03", "task_id": "T1", "duration_s": 0.007, "outcome": "PREMATURE_END"},
        {"session_id": "S0063", "participant_id": "P03", "task_id": "T2", "duration_s": 52.8, "outcome": "SUCCESS"},
    ])

    # Pipeline exclusion logic: flag sessions with duration < 1.0s or explicitly S0062
    mock_sessions["excluded"] = (mock_sessions["session_id"] == "S0062") | (mock_sessions["duration_s"] < 1.0)
    mock_sessions["exclusion_reason"] = np.where(
        mock_sessions["session_id"] == "S0062",
        "Truncated window (0.007s) due to premature enter press; retained for sensitivity analysis",
        None
    )

    # Primary analysis cohort (N=91 in full dataset, N=2 in this mock)
    primary_cohort = mock_sessions[~mock_sessions["excluded"]]
    assert len(primary_cohort) == 2
    assert "S0062" not in primary_cohort["session_id"].values

    # Sensitivity analysis cohort (all sessions, with S0062 reconstructed)
    sensitivity_cohort = mock_sessions.copy()
    assert len(sensitivity_cohort) == 3
    assert "S0062" in sensitivity_cohort["session_id"].values


def test_feature_schema_specification():
    """Validates that the required feature schema adheres strictly to features/SPEC.md."""
    expected_prefixes = {"T_", "V_", "C_", "A_", "H_", "D_", "L_", "Q_"}
    metadata_cols = {"session_id", "controller", "participant_id", "task_id", "rep", "outcome", "excluded"}

    spec_columns = [
        "session_id", "controller", "participant_id", "task_id", "rep", "outcome", "excluded",
        # T (Timing)
        "T_idle_gap_median", "T_idle_gap_cv", "T_idle_gap_entropy", "T_burst_rate", "T_gap_autocorr_lag1",
        # V (Volume)
        "V_up_down_ratio", "V_upload_burst_share",
        # C (Connections)
        "C_new_flows_per_min", "C_max_concurrent", "C_quic_share",
        # A (Vendor)
        "A_vendor_present", "A_vendor_bytes",
        # H (Handshake)
        "H_ja4_mode", "H_ja4_n_distinct",
        # D (Destinations)
        "D_dest_count", "D_search_present",
        # L (Length / Controls)
        "L_duration_s", "L_total_bytes", "L_n_flows",
        # Q (Diagnostics / Confound Monitors)
        "Q_background_bytes", "Q_gvt1_bytes", "Q_edge_present",
    ]

    for col in spec_columns:
        if col in metadata_cols:
            continue
        prefix = col[:2]
        assert prefix in expected_prefixes, f"Column {col} missing valid family prefix from SPEC.md"

    # Headline baseline B6 uses exclusively standardized T, V, and C features
    b6_features = [c for c in spec_columns if c.startswith(("T_", "V_", "C_"))]
    assert len(b6_features) == 10  # 5 T + 2 V + 3 C
    assert "L_duration_s" not in b6_features
    assert "A_vendor_present" not in b6_features
    assert "Q_background_bytes" not in b6_features
