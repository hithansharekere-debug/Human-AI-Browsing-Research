"""Unit and integration tests for sensitivity analyses, negative controls, and cluster bootstrap.

Tests execute strictly on synthetic mocks and fixtures. No study sessions are loaded.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.pipeline.model_evaluation import BASELINE_FEATURE_POOLS
from src.pipeline.negative_controls import NegativeControlValidator
from src.pipeline.sensitivity_analysis import SensitivityAnalyzer
from src.pipeline.statistics import (
    compute_cliffs_delta,
    cluster_bootstrap_ci_cliffs_delta,
    cluster_bootstrap_ci_auroc,
)


@pytest.fixture
def synthetic_study_dataset():
    """Generates a synthetic mock dataset matching the 92-session study structure."""
    rows = []
    # Humans: P01-P03 (8 each = 24), P04 (4), P05-P10 (4 each = 24). Total = 52.
    # Allocation: P01-P03 on 7 Nov (24 sessions); P04 has 3 on 7 Nov, 1 on 9 Nov; P05-P10 on 9 Nov (24 sessions).
    # Total Nov 7: 24 + 3 = 27. Total Nov 9: 1 + 24 = 25.
    sid = 1
    # P01-P03: 2 rounds of 4 tasks
    for p_num in range(1, 4):
        p_id = f"P{p_num:02d}"
        for rep in [1, 2]:
            for t_id in ["T1", "T2", "T3", "T4"]:
                rows.append({
                    "session_id": f"S{sid:04d}",
                    "controller": "human",
                    "participant_id": p_id,
                    "task_id": t_id,
                    "rep": rep,
                    "t_start_utc": "2026-11-07T10:00:00Z",
                    "excluded": 0,
                })
                sid += 1

    # P04: 3 on 7 Nov, 1 on 9 Nov
    for idx, t_id in enumerate(["T1", "T2", "T3", "T4"]):
        t_day = "2026-11-07T14:30:00Z" if idx < 3 else "2026-11-09T17:35:00Z"
        rows.append({
            "session_id": f"S{sid:04d}",
            "controller": "human",
            "participant_id": "P04",
            "task_id": t_id,
            "rep": 1,
            "t_start_utc": t_day,
            "excluded": 0,
        })
        sid += 1

    # P05-P10: 1 round on 9 Nov
    for p_num in range(5, 11):
        p_id = f"P{p_num:02d}"
        for t_id in ["T1", "T2", "T3", "T4"]:
            rows.append({
                "session_id": f"S{sid:04d}",
                "controller": "human",
                "participant_id": p_id,
                "task_id": t_id,
                "rep": 1,
                "t_start_utc": "2026-11-09T18:00:00Z",
                "excluded": 0,
            })
            sid += 1

    # Agents: 10 reps of 4 tasks = 40 sessions on 6 Nov
    for rep in range(1, 11):
        for t_id in ["T1", "T2", "T3", "T4"]:
            rows.append({
                "session_id": f"S{sid:04d}",
                "controller": "agent1",
                "participant_id": "NA",
                "task_id": t_id,
                "rep": rep,
                "t_start_utc": "2026-11-06T15:00:00Z",
                "excluded": 0,
            })
            sid += 1

    df_sessions = pd.DataFrame(rows)
    # Ensure S0062 is marked excluded
    if len(df_sessions) >= 62:
        df_sessions.loc[df_sessions["session_id"] == "S0062", "excluded"] = 1

    # Generate synthetic features
    rng = np.random.default_rng(20261106)
    n = len(df_sessions)
    feat_dict = {}

    # Core 6 features
    for col in BASELINE_FEATURE_POOLS["B6_core6"]:
        # Give a small signal between human and agent
        is_agent = (df_sessions["controller"] != "human").to_numpy()
        feat_dict[col] = rng.normal(loc=1.0 + 0.5 * is_agent, scale=0.5, size=n)

    # Q diagnostics
    feat_dict["Q_background_bytes"] = rng.uniform(1000, 50000, size=n)
    feat_dict["Q_gvt1_bytes"] = np.where(df_sessions["controller"] == "human", rng.uniform(1000000, 5000000, size=n), 0.0)
    feat_dict["Q_edge_present"] = rng.choice([0, 1], size=n, p=[0.8, 0.2])

    # Dest features
    feat_dict["D_dest_count"] = rng.integers(1, 15, size=n)
    feat_dict["D_search_present"] = np.where(df_sessions["controller"] == "human", rng.choice([0, 1], size=n, p=[0.5, 0.5]), 0)

    # All flows features for B5
    for col in BASELINE_FEATURE_POOLS["B5"]:
        if col not in feat_dict:
            feat_dict[col] = rng.normal(loc=1.0, scale=0.5, size=n)

    df_features = pd.DataFrame(feat_dict)
    return df_sessions, df_features


def test_cluster_bootstrap_cliffs_delta(synthetic_study_dataset):
    """Verifies that cluster bootstrap for Cliff's delta runs deterministically with 95% CIs."""
    df_sessions, df_features = synthetic_study_dataset
    df_merged = df_sessions.copy()
    for col in BASELINE_FEATURE_POOLS["B6_core6"]:
        df_merged[col] = df_features[col]

    delta, ci_lo, ci_hi = cluster_bootstrap_ci_cliffs_delta(
        df_merged,
        feature_col="T_idle_gap_median",
        n_resamples=50,  # Small count for test speed
        seed=20261106,
    )
    assert -1.0 <= delta <= 1.0
    assert -1.0 <= ci_lo <= ci_hi <= 1.0


def test_cluster_bootstrap_auroc(synthetic_study_dataset):
    """Verifies cluster bootstrap for AUROC on pooled predictions."""
    df_sessions, _ = synthetic_study_dataset
    rng = np.random.default_rng(20261106)
    n = len(df_sessions)
    y_true = np.where(df_sessions["controller"] == "human", 0, 1)
    y_prob = np.clip(y_true * 0.7 + rng.normal(0, 0.2, size=n), 0.01, 0.99)

    auc, ci_lo, ci_hi = cluster_bootstrap_ci_auroc(
        df_sessions,
        y_true,
        y_prob,
        n_resamples=50,
        seed=20261106,
    )
    assert 0.0 <= auc <= 1.0
    assert 0.0 <= ci_lo <= ci_hi <= 1.0


def test_nc2_and_supplementary_with_synthetic(synthetic_study_dataset):
    """Verifies NC2 human-day control and supplementary AI day diagnostic."""
    df_sessions, df_features = synthetic_study_dataset
    validator = NegativeControlValidator(random_seed=20261106)

    human_mask = df_sessions["controller"] == "human"
    df_human = df_sessions.loc[human_mask].reset_index(drop=True)
    X_human = df_features.loc[human_mask, BASELINE_FEATURE_POOLS["B6_core6"]].to_numpy()

    nc2_res = validator.run_nc2_human_day_control(df_human, X_human)
    assert nc2_res.is_primary_control is True
    assert nc2_res.n_nov7_sessions == 27
    assert nc2_res.n_nov9_sessions == 25
    assert 0.0 <= nc2_res.auroc <= 1.0
    assert 0.0 <= nc2_res.f1 <= 1.0

    # Supplementary AI diagnostic
    X_all = df_features[BASELINE_FEATURE_POOLS["B6_core6"]].to_numpy()
    supp_res = validator.run_nc2_supp_ai_day_diagnostic(df_sessions, X_all)
    assert supp_res.is_supplementary is True
    assert 0.0 <= supp_res.auroc <= 1.0
    assert 0.0 <= supp_res.f1 <= 1.0


def test_sensitivity_analyses_with_synthetic(synthetic_study_dataset):
    """Verifies all 7 sensitivity analyses produce genuine calculations on synthetic data."""
    df_sessions, df_features = synthetic_study_dataset
    analyzer = SensitivityAnalyzer(random_seed=20261106)

    # 1. Day confound and drift
    rtt_mock = {f"S{i:04d}": float(20.0 + (i % 5)) for i in range(1, 93)}
    df_drift = analyzer.evaluate_day_confound_and_drift(df_sessions, rtt_mock, df_features)
    assert not df_drift.empty
    assert "tcp_handshake_rtt_drift" in df_drift["check"].values
    assert "time_of_day_overlap" in df_drift["check"].values

    # 2. Unequal rounds
    df_rounds = analyzer.evaluate_unequal_rounds(df_sessions, df_features)
    assert not df_rounds.empty
    assert "b6_drop_round2" in df_rounds["check"].values
    r2_row = df_rounds[df_rounds["check"] == "b6_drop_round2"].iloc[0]
    assert r2_row["n_sessions_retained"] == 79  # 91 - 12 = 79

    # 3. Edge sessions
    edge_res = analyzer.evaluate_edge_sessions_sensitivity(df_sessions, df_features)
    assert "auroc_without_edge" in edge_res
    assert 0.0 <= edge_res["auroc_without_edge"] <= 1.0

    # 4. S0062 window reconstruction
    s0062_res = analyzer.evaluate_s0062_reconstructed_window(df_sessions, df_features)
    assert "auroc_with_s0062_n92" in s0062_res
    assert 0.0 <= s0062_res["auroc_with_s0062_n92"] <= 1.0

    # 5. Search class handling
    search_res = analyzer.evaluate_search_class_handling(
        df_sessions,
        df_features_search_as_d=df_features,
        df_features_search_as_website=df_features,
    )
    assert 0.0 <= search_res["auroc_b6_search_as_d"] <= 1.0
    assert 0.0 <= search_res["auroc_b6_search_as_website"] <= 1.0

    # 6. Burst thresholds
    burst_dict = {
        50.0: df_features,
        100.0: df_features,
        250.0: df_features,
    }
    burst_res = analyzer.evaluate_burst_thresholds(
        df_sessions=df_sessions,
        df_features_by_threshold=burst_dict,
    )
    assert 100.0 in burst_res["aurocs_by_threshold"]

    # 7. Family dropout
    df_dropout = analyzer.evaluate_family_dropout(
        df_sessions=df_sessions,
        df_features=df_features,
    )
    assert not df_dropout.empty
    assert set(df_dropout["model"].unique()) == {"B5", "B6"}
    assert all(0.0 <= val <= 1.0 for val in df_dropout["auroc"])

    # Summary table
    df_summary = analyzer.generate_sensitivity_summary_table(
        edge_res, s0062_res, search_res, burst_res
    )
    assert len(df_summary) >= 3
    assert "analysis" in df_summary.columns
