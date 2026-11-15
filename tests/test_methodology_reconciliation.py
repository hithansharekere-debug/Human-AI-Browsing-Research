"""Unit and integration tests verifying methodology reconciliation.

Tests:
1. Exact B0-B8 baseline definitions and features.
2. 10-fold LOPO cross-validation with zero grouping leakage.
3. 4-fold LOTO cross-validation.
4. NC1 with exactly 200 within-task label permutations.
5. Primary NC2 (Human 7 Nov vs Human 9 Nov) with participant-grouped folds.
6. Separation of primary vs supplementary day diagnostics.
7. Coverage of all 7 pre-registered sensitivity analyses.
8. Complete audit of Addendum 07 domains and verification of no unsupported DHCP/NTP exclusions.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest
import yaml

from src.pipeline.model_evaluation import (
    BASELINE_DESCRIPTIONS,
    BASELINE_FEATURE_POOLS,
    generate_lopo_folds,
    generate_loto_folds,
)
from src.pipeline.negative_controls import NegativeControlValidator
from src.pipeline.sensitivity_analysis import SensitivityAnalyzer
from src.pipeline.flow_classification import FlowClassifier


# ==============================================================================
# 1. BASELINE DEFINITIONS (B0 - B8)
# ==============================================================================

def test_exact_baseline_definitions_b0_b8():
    """Verifies that baselines B0-B8 match the authoritative blueprint and handover specifications."""
    expected_baselines = {"B0", "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8"}
    assert set(BASELINE_DESCRIPTIONS.keys()) == expected_baselines

    # Verify B0: Majority class floor
    assert "Majority class" in BASELINE_DESCRIPTIONS["B0"]

    # Verify B1: Vendor shortcut using A features
    assert "Vendor shortcut" in BASELINE_DESCRIPTIONS["B1"]
    assert "A_vendor_present" in BASELINE_FEATURE_POOLS["B1"]
    assert "A_vendor_bytes" in BASELINE_FEATURE_POOLS["B1"]

    # Verify B2: JA4 TLS handshake on website flows (H features)
    assert "JA4" in BASELINE_DESCRIPTIONS["B2"]
    assert "H_ja4_mode" in BASELINE_FEATURE_POOLS["B2"]

    # Verify B3: Destination / search baseline using D features
    assert "Destination/search" in BASELINE_DESCRIPTIONS["B3"]
    assert "D_dest_count" in BASELINE_FEATURE_POOLS["B3"]
    assert "D_search_present" in BASELINE_FEATURE_POOLS["B3"]

    # Verify B4: Length-only baseline using L features
    assert "Length-only" in BASELINE_DESCRIPTIONS["B4"]
    assert "L_duration_s" in BASELINE_FEATURE_POOLS["B4"]

    # Verify B5: T+V+C using all flows (diagnostic)
    assert "all flows" in BASELINE_DESCRIPTIONS["B5"]

    # Verify B6: Headline model (T+V+C on website flows only)
    assert "HEADLINE" in BASELINE_DESCRIPTIONS["B6"]
    # Check that candidate B6 features do NOT contain A, H, D, L, or Q features
    for col in BASELINE_FEATURE_POOLS["B6_core6"]:
        assert col[:2] in {"T_", "V_", "C_"}

    # B6 primary model is FROZEN to exactly these six standardized features
    assert BASELINE_FEATURE_POOLS["B6"] == [
        "T_idle_gap_median", "T_burst_rate",
        "V_up_down_ratio", "V_upload_burst_share",
        "C_new_flows_per_min", "C_max_concurrent",
    ]
    # Random Forest check uses the EXACT SAME six core features
    assert BASELINE_FEATURE_POOLS["B6_rf_check"] == BASELINE_FEATURE_POOLS["B6"]

    # Verify B7: B6 length-normalised features
    assert "length-normalised" in BASELINE_DESCRIPTIONS["B7"]

    # Verify B8: Vendor-to-website cross-flow lag only
    assert "Vendor-to-website" in BASELINE_DESCRIPTIONS["B8"]
    assert "T_vendor_to_website_lag_s" in BASELINE_FEATURE_POOLS["B8"]

    # Verify that burst-only, full behavioural, or oracle models are NOT primary baselines
    for non_baseline in ["burst_only", "full_behavioural", "oracle"]:
        assert non_baseline not in BASELINE_DESCRIPTIONS


# ==============================================================================
# 2. 10-FOLD LOPO DESIGN AND ZERO GROUPING LEAKAGE
# ==============================================================================

def test_ten_lopo_folds_and_zero_grouping_leakage():
    """Validates 10-fold LOPO with human participants P01-P10 and agent reps 1-10."""
    # Construct synthetic mock sessions DataFrame matching study structure (92 sessions)
    rows = []
    # 52 Human sessions: P01-P03 (8 each = 24), P04-P10 (4 each = 28)
    for p_num in range(1, 11):
        p_id = f"P{p_num:02d}"
        n_rounds = 2 if p_num <= 3 else 1
        for rnd in range(1, n_rounds + 1):
            for t_num in range(1, 5):
                rows.append({
                    "session_id": f"H_{p_id}_T{t_num}_r{rnd}",
                    "controller": "human",
                    "participant_id": p_id,
                    "task_id": f"T{t_num}",
                    "rep": rnd,
                })
    # 40 Agent sessions: reps 1-10 across 4 tasks
    for rep in range(1, 11):
        for t_num in range(1, 5):
            rows.append({
                "session_id": f"A_rep{rep}_T{t_num}",
                "controller": "agent1",
                "participant_id": None,
                "task_id": f"T{t_num}",
                "rep": rep,
            })

    mock_df = pd.DataFrame(rows)
    assert len(mock_df) == 92  # 52 human + 40 agent

    folds = generate_lopo_folds(mock_df, n_folds=10)
    assert len(folds) == 10, "Must produce exactly 10 folds for LOPO"

    tested_session_indices = set()

    for k, (train_idx, test_idx) in enumerate(folds, start=1):
        target_p = f"P{k:02d}"
        target_rep = k

        test_sessions = mock_df.iloc[test_idx]
        train_sessions = mock_df.iloc[train_idx]

        # 1. No index overlap between train and test
        assert len(set(train_idx).intersection(set(test_idx))) == 0

        # 2. Test fold human sessions must ONLY be participant Pk
        test_humans = test_sessions[test_sessions["controller"] == "human"]
        assert (test_humans["participant_id"] == target_p).all()

        # 3. Test fold agent sessions must ONLY be rep k
        test_agents = test_sessions[test_sessions["controller"] != "human"]
        assert (test_agents["rep"] == target_rep).all()
        assert len(test_agents) == 4  # Exactly one session per task

        # 4. Zero participant leakage: Pk must NEVER appear in train_sessions
        train_humans = train_sessions[train_sessions["controller"] == "human"]
        assert target_p not in train_humans["participant_id"].values

        # 5. Zero agent rep leakage: rep k must NEVER appear in train_sessions
        train_agents = train_sessions[train_sessions["controller"] != "human"]
        assert target_rep not in train_agents["rep"].values

        # 6. Both classes present in test fold
        assert len(test_humans) > 0
        assert len(test_agents) > 0

        # Track session indices to verify all 92 are tested exactly once
        for idx in test_idx:
            assert idx not in tested_session_indices, f"Session {idx} tested more than once"
            tested_session_indices.add(idx)

    assert len(tested_session_indices) == 92, "Every study session must be tested exactly once in LOPO"


def test_four_loto_folds():
    """Validates 4-fold Leave-One-Task-Out (LOTO) splits."""
    rows = []
    for t_num in range(1, 5):
        for s_idx in range(10):
            rows.append({
                "session_id": f"S_T{t_num}_{s_idx}",
                "task_id": f"T{t_num}",
                "controller": "human" if s_idx < 5 else "agent",
            })
    mock_df = pd.DataFrame(rows)
    folds = generate_loto_folds(mock_df)

    assert len(folds) == 4
    for j, (train_idx, test_idx) in enumerate(folds, start=1):
        target_task = f"T{j}"
        test_df = mock_df.iloc[test_idx]
        train_df = mock_df.iloc[train_idx]
        assert (test_df["task_id"] == target_task).all()
        assert target_task not in train_df["task_id"].values


# ==============================================================================
# 3. NEGATIVE CONTROLS (NC1 & NC2)
# ==============================================================================

def test_nc1_permutation_count_and_within_task_shuffling():
    """Verifies that NC1 uses exactly 200 within-task label permutations."""
    validator = NegativeControlValidator(n_permutations=200, random_seed=20261106)
    assert validator.n_permutations == 200

    # Test within-task shuffling preserves task-level class counts
    mock_sessions = pd.DataFrame([
        {"session_id": f"S{i:03d}", "task_id": "T1", "controller": "human" if i < 6 else "agent1"}
        for i in range(10)
    ] + [
        {"session_id": f"S{i+10:03d}", "task_id": "T2", "controller": "human" if i < 4 else "agent1"}
        for i in range(10)
    ])

    rng = np.random.default_rng(20261106)
    permuted_labels = validator.permute_labels_within_tasks(mock_sessions, rng)

    # Within T1, exactly 6 human (0) and 4 agent (1) must remain
    t1_mask = (mock_sessions["task_id"] == "T1").values
    assert np.sum(permuted_labels[t1_mask] == 0) == 6
    assert np.sum(permuted_labels[t1_mask] == 1) == 4

    # Within T2, exactly 4 human (0) and 6 agent (1) must remain
    t2_mask = (mock_sessions["task_id"] == "T2").values
    assert np.sum(permuted_labels[t2_mask] == 0) == 4
    assert np.sum(permuted_labels[t2_mask] == 1) == 6


def test_nc1_runs_both_loto_and_lopo_with_model_evaluations():
    """Confirms that NC1 executes B6 model evaluations under both LOTO and LOPO."""
    mock_sessions = pd.DataFrame([
        {"session_id": f"H_P01_T1", "controller": "human", "participant_id": "P01", "task_id": "T1", "rep": 1},
        {"session_id": f"H_P01_T2", "controller": "human", "participant_id": "P01", "task_id": "T2", "rep": 1},
        {"session_id": f"H_P02_T1", "controller": "human", "participant_id": "P02", "task_id": "T1", "rep": 1},
        {"session_id": f"H_P02_T2", "controller": "human", "participant_id": "P02", "task_id": "T2", "rep": 1},
        {"session_id": f"A_rep1_T1", "controller": "agent1", "participant_id": None, "task_id": "T1", "rep": 1},
        {"session_id": f"A_rep1_T2", "controller": "agent1", "participant_id": None, "task_id": "T2", "rep": 1},
        {"session_id": f"A_rep2_T1", "controller": "agent1", "participant_id": None, "task_id": "T1", "rep": 2},
        {"session_id": f"A_rep2_T2", "controller": "agent1", "participant_id": None, "task_id": "T2", "rep": 2},
    ])
    X_mock = np.random.randn(8, 6)

    # Use 5 permutations for quick unit test execution
    validator = NegativeControlValidator(n_permutations=5, random_seed=20261106)
    results = validator.run_nc1_both_splits(mock_sessions, X_mock)

    assert "loto" in results
    assert "lopo" in results
    assert len(results["loto"].permuted_aurocs) == 5
    assert len(results["lopo"].permuted_aurocs) == 5
    assert results["loto"].null_mean_auroc == pytest.approx(float(np.mean(results["loto"].permuted_aurocs)), abs=1e-5)
    assert results["lopo"].null_mean_auroc == pytest.approx(float(np.mean(results["lopo"].permuted_aurocs)), abs=1e-5)


def test_nc2_human_day_control_and_supplementary():
    """Verifies NC2 human-vs-human day labels and participant-grouped folds."""
    mock_human_sessions = pd.DataFrame([
        # 7 Nov sessions (label 0) - P01, P02, P03
        {"session_id": "H01", "participant_id": "P01", "t_start_utc": "2026-11-07T10:00:00Z"},
        {"session_id": "H02", "participant_id": "P01", "t_start_utc": "2026-11-07T10:15:00Z"},
        {"session_id": "H03", "participant_id": "P02", "t_start_utc": "2026-11-07T11:00:00Z"},
        {"session_id": "H04", "participant_id": "P03", "t_start_utc": "2026-11-07T12:00:00Z"},
        # 9 Nov sessions (label 1) - P05, P06, P07, P08
        {"session_id": "H05", "participant_id": "P05", "t_start_utc": "2026-11-09T17:00:00Z"},
        {"session_id": "H06", "participant_id": "P06", "t_start_utc": "2026-11-09T17:30:00Z"},
        {"session_id": "H07", "participant_id": "P07", "t_start_utc": "2026-11-09T18:00:00Z"},
        {"session_id": "H08", "participant_id": "P08", "t_start_utc": "2026-11-09T18:30:00Z"},
    ])

    X_mock = np.random.randn(8, 6)
    validator = NegativeControlValidator()
    result = validator.run_nc2_human_day_control(mock_human_sessions, X_mock)

    assert result.is_primary_control is True
    assert result.n_nov7_sessions == 4
    assert result.n_nov9_sessions == 4
    assert 0.0 <= result.auroc <= 1.0

    # Verify supplementary AI day diagnostic
    supp_result = validator.run_nc2_supp_ai_day_diagnostic(mock_human_sessions, X_mock)
    assert supp_result.is_supplementary is True
    assert "supplementary" in supp_result.comparison_name.lower() or supp_result.is_supplementary


# ==============================================================================
# 4. SENSITIVITY ANALYSES COVERAGE
# ==============================================================================

def test_sensitivity_analyses_coverage():
    """Verifies all 7 pre-registered sensitivity analyses are implemented."""
    analyzer = SensitivityAnalyzer()

    # 1. Day confound & RTT drift
    df_drift = analyzer.evaluate_day_confound_and_drift(pd.DataFrame(), {"S0001": 25.4, "S0002": 26.1})
    assert len(df_drift) >= 2
    assert "time_of_day_overlap" in df_drift["check"].values
    assert "tcp_handshake_rtt_drift" in df_drift["check"].values

    # 2. Unequal rounds
    df_rounds = analyzer.evaluate_unequal_rounds(pd.DataFrame())
    assert len(df_rounds) == 2
    assert "unequal_rounds_p01_p03" in df_rounds["check"].values
    assert "b6_drop_round2" in df_rounds["check"].values

    # 3. Edge sessions
    edge_res = analyzer.evaluate_edge_sessions_sensitivity(pd.DataFrame())
    assert set(edge_res["edge_sessions"]) == {"S0044", "S0068", "S0081"}

    # 4. S0062 inclusion
    s0062_res = analyzer.evaluate_s0062_reconstructed_window(pd.DataFrame())
    assert s0062_res["target_session"] == "S0062"
    assert s0062_res["reconstruction_source"] == "chrome_netlog_request_boundaries"

    # 5. Search class handling
    search_res = analyzer.evaluate_search_class_handling(pd.DataFrame())
    assert "search_as_destination_D" in search_res["condition_1"]
    assert "search_as_website_flow" in search_res["condition_2"]

    # 6. Burst thresholds 50, 100, 250 ms
    burst_res = analyzer.evaluate_burst_thresholds()
    assert burst_res["thresholds_ms"] == [50.0, 100.0, 250.0]

    # 7. Family dropout for B5 and B6
    df_dropout = analyzer.evaluate_family_dropout()
    assert set(df_dropout["model"].unique()) == {"B5", "B6"}
    assert set(df_dropout["dropped_family"].unique()) == {"none", "T", "V", "C"}


# ==============================================================================
# 5. COMPLETE ADDENDUM DOMAIN AUDIT & NO UNSUPPORTED EXCLUSIONS
# ==============================================================================

def test_addendum_07_explicit_domains_and_no_dhcp_ntp():
    """Verifies all explicit domains from Addendum 07 and confirms no unsupported DHCP/NTP exclusions."""
    rules_path = Path("features/flow_rules.yaml")
    assert rules_path.exists()
    classifier = FlowClassifier(rules_path=rules_path)

    # Explicit domains listed in Task 7
    explicit_domains = [
        "sectigo.com",
        "usertrust.com",
        "sfx.ms",
        "azureedge.net",
        "nvidiagrid.net",
        "hpgamestream.com",
        "falais.com",
        "pypi.org",
    ]
    for domain in explicit_domains:
        cls = classifier.classify_domain(domain)
        assert cls == "os_background", f"Expected os_background for {domain}, got {cls}"

    # Verify LAN exclusions
    assert classifier.classify_domain("Android.local") == "excluded"
    assert classifier.classify_domain("wpad.domain.name") == "excluded"
    assert classifier.classify_domain("Cal") == "excluded"

    # Verify unresolved domains fall through to unknown
    assert classifier.classify_domain("fastly-edge.com") == "unknown"
    assert classifier.classify_domain("cloudflare-ech.com") == "unknown"

    # Verify that DHCP (ports 67, 68) and NTP (port 123) are NOT in excluded_ports
    with open(rules_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    lan_ports = cfg.get("lan_traffic_exclusions", {}).get("excluded_ports", [])
    excluded_port_numbers = set()
    for item in lan_ports:
        if "port" in item:
            excluded_port_numbers.add(item["port"])
        if "ports" in item:
            excluded_port_numbers.update(item["ports"])

    assert 67 not in excluded_port_numbers, "DHCP port 67 must not be excluded without document justification"
    assert 68 not in excluded_port_numbers, "DHCP port 68 must not be excluded without document justification"
    assert 123 not in excluded_port_numbers, "NTP port 123 must not be excluded without document justification"
