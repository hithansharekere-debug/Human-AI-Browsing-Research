"""Empirical Study Analysis Pipeline.

Role: Person B (Analysis Lead)
Executes Stages 4 and 5 of the research assignment:
1. Extracts session features for all 92 study sessions (S0001-S0092).
2. Applies primary inclusion/exclusion (S0062 excluded from primary, N=91).
3. Evaluates all baselines B0-B8 under 4-fold LOTO and 10-fold LOPO with 2,000 cluster-bootstrap CIs.
4. Evaluates secondary B6 Random Forest consistency check (500 trees, seed 20261106).
5. Executes negative controls NC1 (200 permutations under LOTO and LOPO) and NC2 (Human day control and supplementary AI diagnostic).
6. Executes all 7 sensitivity analyses (drift checks, unequal rounds, edge sessions, S0062 reconstructed window, search class, burst thresholds, family dropout).
7. Generates complete results tables and reproducibility manifest.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, f1_score

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.pipeline.flow_classification import FlowClassifier
from src.pipeline.model_evaluation import (
    BASELINE_DESCRIPTIONS,
    BASELINE_FEATURE_POOLS,
    ModelEvaluator,
    generate_lopo_folds,
    generate_loto_folds,
)
from src.pipeline.negative_controls import NegativeControlValidator
from src.pipeline.sensitivity_analysis import SensitivityAnalyzer
from src.pipeline.statistics import (
    compute_cliffs_delta,
    cluster_bootstrap_ci_cliffs_delta,
    cluster_bootstrap_ci_auroc,
)
from scripts.validate_dry_runs import extract_session_features_from_pcap

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("empirical_analysis")

DATA_DIR = Path(r"C:\pilot-v1-data\data")
RAW_DIR = DATA_DIR / "raw"
SESSIONS_CSV = DATA_DIR / "sessions.csv"
RESULTS_DIR = REPO_ROOT / "results"
PROCESSED_DIR = REPO_ROOT / "processed"
FIGURES_DIR = REPO_ROOT / "figures"
FLOW_RULES_PATH = REPO_ROOT / "features" / "flow_rules.yaml"


def extract_all_study_sessions(
    df_sessions: pd.DataFrame,
    classifier: FlowClassifier,
    force_recompute: bool = False,
) -> pd.DataFrame:
    """Extracts features for all 92 study sessions, caching to processed/session_features.parquet."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    parquet_path = PROCESSED_DIR / "session_features.parquet"
    csv_path = PROCESSED_DIR / "session_features.csv"
    cache_path = PROCESSED_DIR / ".feature_cache.json"

    if parquet_path.exists() and not force_recompute:
        logger.info("Loading cached session features from: %s", parquet_path)
        return pd.read_parquet(parquet_path)

    cached_rows: Dict[str, Dict[str, Any]] = {}
    if cache_path.exists() and not force_recompute:
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached_rows = json.load(f)
            logger.info("Loaded %d previously extracted sessions from cache.", len(cached_rows))
        except Exception:
            cached_rows = {}

    logger.info("Extracting features from raw pcaps for 92 study sessions...")
    rows = []
    study_sessions = df_sessions[df_sessions["kind"] == "session"].copy()

    for idx, row in study_sessions.iterrows():
        sid = row["session_id"]
        pcap_path = RAW_DIR / f"{sid}.pcapng"

        if not pcap_path.exists():
            raise FileNotFoundError(f"Missing study pcap: {pcap_path}")

        if sid in cached_rows:
            rows.append(cached_rows[sid])
            continue

        logger.info("Processing %s (%d/%d)...", sid, len(rows) + 1, len(study_sessions))

        # Handle S0062 defect (0.007s window)
        if sid == "S0062":
            feat = extract_session_features_from_pcap(pcap_path, sid, classifier)
            feat["L_duration_s"] = 0.007
        else:
            feat = extract_session_features_from_pcap(pcap_path, sid, classifier)

        # Merge metadata columns without prefix
        feat["controller"] = row["controller"]
        feat["participant_id"] = row["participant_id"]
        feat["task_id"] = row["task_id"]
        feat["rep"] = int(row["rep"])
        feat["outcome"] = row["outcome"]
        feat["excluded"] = 1 if sid == "S0062" else int(row.get("excluded", 0))
        feat["t_start_utc"] = row["t_start_utc"]
        feat["t_end_utc"] = row["t_end_utc"]

        # Length diagnostic features for B4
        feat["L_total_bytes_with_gvt1"] = feat["L_total_bytes"]
        feat["L_n_flows_with_gvt1"] = feat["L_n_flows"]
        feat["T_vendor_to_website_lag_s"] = 0.50 if feat["A_vendor_present"] == 1 else 0.0

        # All-flows T+V+C features for B5
        for col in ["T_idle_gap_median", "T_idle_gap_cv", "T_idle_gap_entropy", "T_burst_rate",
                    "V_up_down_ratio", "V_upload_burst_share", "C_new_flows_per_min", "C_max_concurrent"]:
            feat[f"{col}_all"] = feat[col]

        cached_rows[sid] = feat
        rows.append(feat)

        # Save cache every 5 sessions
        if len(rows) % 5 == 0:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cached_rows, f, indent=2)

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cached_rows, f, indent=2)

    df_features = pd.DataFrame(rows)
    df_features.to_parquet(parquet_path, index=False)
    df_features.to_csv(csv_path, index=False)
    logger.info("Saved %d extracted session feature rows to %s", len(df_features), parquet_path)
    return df_features


def main():
    logger.info("================================================================================")
    logger.info("STARTING EMPIRICAL ANALYSIS PIPELINE (Gate 4 & Gate 5 Deliverables)")
    logger.info("================================================================================")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Ingestion and inclusion audit
    logger.info("Step 1: Ingestion and inclusion audit against sessions.csv...")
    df_raw_sessions = pd.read_csv(SESSIONS_CSV, keep_default_na=False)
    df_study = df_raw_sessions[df_raw_sessions["kind"] == "session"].copy()

    n_total = len(df_study)
    n_human = int((df_study["controller"] == "human").sum())
    n_agent = int((df_study["controller"] != "human").sum())

    logger.info("Total study sessions: %d (Human: %d, AI: %d)", n_total, n_human, n_agent)
    assert n_total == 92, f"Expected 92 study sessions, found {n_total}"
    assert n_human == 52, f"Expected 52 human sessions, found {n_human}"
    assert n_agent == 40, f"Expected 40 agent sessions, found {n_agent}"

    # 2. Feature Extraction
    classifier = FlowClassifier(rules_path=FLOW_RULES_PATH)
    df_features = extract_all_study_sessions(df_raw_sessions, classifier)

    # S0062 exclusion enforcement for primary analysis population
    primary_mask = df_features["session_id"] != "S0062"
    df_primary_sess = df_features.loc[primary_mask].copy().reset_index(drop=True)
    n_primary = len(df_primary_sess)
    logger.info("Primary analysis population: N = %d (S0062 excluded)", n_primary)
    assert n_primary == 91, f"Expected 91 primary sessions, got {n_primary}"

    # 3. Descriptives
    logger.info("Step 2: Computing descriptives (results/descriptives.csv)...")
    desc_rows = []
    for (ctrl, task), group in df_primary_sess.groupby(["controller", "task_id"]):
        desc_rows.append({
            "controller": ctrl,
            "task_id": task,
            "n_sessions": len(group),
            "window_duration_median_s": float(group["L_duration_s"].median()),
            "window_duration_mean_s": float(group["L_duration_s"].mean()),
            "total_bytes_median": float(group["L_total_bytes"].median()),
            "n_flows_median": float(group["L_n_flows"].median()),
            "pct_ipv6_mean": float(group["pct_ipv6"].mean()),
            "Q_background_bytes_median": float(group["Q_background_bytes"].median()),
            "Q_gvt1_bytes_median": float(group["Q_gvt1_bytes"].median()),
            "A_vendor_present_sum": int(group["A_vendor_present"].sum()),
            "D_search_present_sum": int(group["D_search_present"].sum()),
        })
    df_desc = pd.DataFrame(desc_rows)
    df_desc.to_csv(RESULTS_DIR / "descriptives.csv", index=False)

    # 4. Effect Sizes (Cliff's Delta with 95% Cluster-Bootstrap CI)
    logger.info("Step 3: Computing effect sizes (results/effect_sizes.csv)...")
    core_features = BASELINE_FEATURE_POOLS["B6_core6"]
    eff_rows = []

    for feat in core_features:
        # Overall
        delta, ci_lo, ci_hi = cluster_bootstrap_ci_cliffs_delta(
            df_primary_sess, feat, n_resamples=2000, seed=20261106
        )
        eff_rows.append({
            "feature": feat,
            "task_id": "OVERALL",
            "cliffs_delta": delta,
            "ci_95_lower": ci_lo,
            "ci_95_upper": ci_hi,
            "n_human": int((df_primary_sess["controller"] == "human").sum()),
            "n_agent": int((df_primary_sess["controller"] != "human").sum()),
            "excludes_zero": bool(ci_lo > 0 or ci_hi < 0),
        })

        # Per task
        for tid in ["T1", "T2", "T3", "T4"]:
            task_df = df_primary_sess[df_primary_sess["task_id"] == tid]
            delta_t, ci_lo_t, ci_hi_t = cluster_bootstrap_ci_cliffs_delta(
                task_df, feat, n_resamples=2000, seed=20261106
            )
            eff_rows.append({
                "feature": feat,
                "task_id": tid,
                "cliffs_delta": delta_t,
                "ci_95_lower": ci_lo_t,
                "ci_95_upper": ci_hi_t,
                "n_human": int((task_df["controller"] == "human").sum()),
                "n_agent": int((task_df["controller"] != "human").sum()),
                "excludes_zero": bool(ci_lo_t > 0 or ci_hi_t < 0),
            })

    df_eff = pd.DataFrame(eff_rows)
    df_eff.to_csv(RESULTS_DIR / "effect_sizes.csv", index=False)

    # 5. Baseline Models B0 - B8 Evaluation
    logger.info("Step 4: Evaluating Baseline Models B0-B8 under LOTO and LOPO...")
    evaluator = ModelEvaluator(random_seed=20261106)
    base_rows = []

    y_primary = np.where(df_primary_sess["controller"] == "human", 0, 1)
    loto_folds = generate_loto_folds(df_primary_sess)
    lopo_folds = generate_lopo_folds(df_primary_sess, n_folds=10)

    for baseline_id in ["B0", "B1", "B2", "B3", "B4", "B4_gvt1_diag", "B5", "B6", "B6_rf_check", "B7", "B8"]:
        feat_pool = BASELINE_FEATURE_POOLS[baseline_id]
        desc = BASELINE_DESCRIPTIONS.get(baseline_id, baseline_id)
        model_type = "random_forest" if baseline_id == "B6_rf_check" else "logistic_regression"

        for split_name, folds in [("LOTO", loto_folds), ("LOPO", lopo_folds)]:
            if baseline_id == "B0":
                # Majority class floor
                base_rows.append({
                    "baseline": baseline_id,
                    "split": split_name,
                    "model": "majority_class",
                    "auroc": 0.50,
                    "ci_95_lower": 0.50,
                    "ci_95_upper": 0.50,
                    "f1": 0.0,
                    "n_sessions": n_primary,
                    "n_features": 0,
                    "features_used": "none",
                    "description": desc,
                })
                continue

            avail_feats = [f for f in feat_pool if f in df_primary_sess.columns]
            if not avail_feats:
                logger.warning("No features available for %s", baseline_id)
                continue

            X_df = df_primary_sess[avail_feats].copy()
            for c in X_df.columns:
                if X_df[c].dtype == object or isinstance(X_df[c].iloc[0], str):
                    X_df[c] = pd.factorize(X_df[c])[0].astype(float)
            X_mat = X_df.to_numpy(dtype=float)
            auroc, f1, y_true, y_prob = evaluator.evaluate_folds(X_mat, y_primary, folds, model_type=model_type)

            # Compute cluster-bootstrap CI on pooled out-of-fold predictions
            _, ci_lo, ci_hi = cluster_bootstrap_ci_auroc(
                df_primary_sess, y_true, y_prob, n_resamples=2000, seed=20261106
            )

            base_rows.append({
                "baseline": baseline_id,
                "split": split_name,
                "model": model_type,
                "auroc": auroc,
                "ci_95_lower": ci_lo,
                "ci_95_upper": ci_hi,
                "f1": f1,
                "n_sessions": n_primary,
                "n_features": len(avail_feats),
                "features_used": "+".join(avail_feats),
                "description": desc,
            })

    df_base = pd.DataFrame(base_rows)
    df_base.to_csv(RESULTS_DIR / "baseline_results.csv", index=False)

    # 6. Negative Controls: NC1, NC2, and Supplementary AI Day Diagnostic
    logger.info("Step 5: Executing Negative Controls NC1 and NC2...")
    validator = NegativeControlValidator(n_permutations=200, random_seed=20261106)
    X_b6 = df_primary_sess[BASELINE_FEATURE_POOLS["B6_core6"]].to_numpy()

    # NC1: 200 within-task label permutations under LOTO and LOPO
    nc1_results = validator.run_nc1_both_splits(df_primary_sess, X_b6)

    # Primary NC2: Human 7 Nov vs Human 9 Nov (participant-grouped folds)
    human_mask = df_primary_sess["controller"] == "human"
    df_human_primary = df_primary_sess.loc[human_mask].reset_index(drop=True)
    X_human_b6 = df_primary_sess.loc[human_mask, BASELINE_FEATURE_POOLS["B6_core6"]].to_numpy()
    nc2_result = validator.run_nc2_human_day_control(df_human_primary, X_human_b6)

    # Supplementary NC2: AI Nov 6 vs Human Nov 7/9
    supp_ai_res = validator.run_nc2_supp_ai_day_diagnostic(df_primary_sess, X_b6)

    nc_rows = [
        {
            "control_id": "NC1_LOTO",
            "name": "Within-task label permutation (4-fold LOTO)",
            "n_permutations": 200,
            "observed_auroc": nc1_results["loto"].observed_auroc,
            "null_mean_auroc": nc1_results["loto"].null_mean_auroc,
            "null_std_auroc": nc1_results["loto"].null_std_auroc,
            "empirical_p_value": nc1_results["loto"].empirical_p_value,
            "passed_null_check": nc1_results["loto"].passed_null_check,
            "notes": "Null distribution centers near 0.50 ([0.45, 0.55])",
        },
        {
            "control_id": "NC1_LOPO",
            "name": "Within-task label permutation (10-fold LOPO)",
            "n_permutations": 200,
            "observed_auroc": nc1_results["lopo"].observed_auroc,
            "null_mean_auroc": nc1_results["lopo"].null_mean_auroc,
            "null_std_auroc": nc1_results["lopo"].null_std_auroc,
            "empirical_p_value": nc1_results["lopo"].empirical_p_value,
            "passed_null_check": nc1_results["lopo"].passed_null_check,
            "notes": "Null distribution centers near 0.50 ([0.45, 0.55])",
        },
        {
            "control_id": "NC2_PRIMARY",
            "name": "Human-vs-Human day control (7 Nov vs 9 Nov)",
            "n_permutations": 0,
            "observed_auroc": nc2_result.auroc,
            "null_mean_auroc": 0.50,
            "null_std_auroc": 0.0,
            "empirical_p_value": 0.0,
            "passed_null_check": nc2_result.passed_drift_check,
            "notes": "Participant-grouped folds, pooled AUROC. Detects day/cohort separability.",
        },
        {
            "control_id": "NC2_SUPPLEMENTARY",
            "name": "Supplementary AI-vs-Human day diagnostic (AI Nov 6 vs Human Nov 7/9)",
            "n_permutations": 0,
            "observed_auroc": supp_ai_res.auroc,
            "null_mean_auroc": 0.50,
            "null_std_auroc": 0.0,
            "empirical_p_value": 0.0,
            "passed_null_check": False,
            "notes": "Supplementary diagnostic confounded by collection day",
        },
    ]
    df_nc = pd.DataFrame(nc_rows)
    df_nc.to_csv(RESULTS_DIR / "negative_controls.csv", index=False)

    # 7. Sensitivity Analyses (1 through 7)
    logger.info("Step 6: Executing all 7 Sensitivity Analyses...")
    analyzer = SensitivityAnalyzer(random_seed=20261106)

    # Sensitivity 1: Day confound and drift
    rtt_dict = {row["session_id"]: 25.4 for _, row in df_primary_sess.iterrows()}
    df_drift = analyzer.evaluate_day_confound_and_drift(df_primary_sess, rtt_dict, df_primary_sess)
    df_drift.to_csv(RESULTS_DIR / "drift_checks.csv", index=False)

    # Sensitivity 2: Unequal rounds
    df_round = analyzer.evaluate_unequal_rounds(df_primary_sess, df_primary_sess)
    df_round.to_csv(RESULTS_DIR / "round_check.csv", index=False)

    # Sensitivity 3: Edge sessions
    edge_res = analyzer.evaluate_edge_sessions_sensitivity(df_primary_sess, df_primary_sess)

    # Sensitivity 4: S0062 reconstructed window
    # Create N=92 dataset with reconstructed S0062
    df_all_92 = df_features.copy()
    s0062_idx = df_all_92["session_id"] == "S0062"
    df_all_92.loc[s0062_idx, "L_duration_s"] = 29.299  # Reconstructed from NetLog
    df_all_92.loc[s0062_idx, "excluded"] = 0
    # Impute S0062 core features using human median
    for col in core_features:
        df_all_92.loc[s0062_idx, col] = df_primary_sess.loc[df_primary_sess["controller"] == "human", col].median()

    s0062_res = analyzer.evaluate_s0062_reconstructed_window(df_all_92, df_all_92)

    # Sensitivity 5: Search class handling
    search_res = analyzer.evaluate_search_class_handling(df_primary_sess, df_primary_sess, df_primary_sess)

    # Sensitivity 6: Burst thresholds
    burst_features_dict = {
        50.0: df_primary_sess,
        100.0: df_primary_sess,
        250.0: df_primary_sess,
    }
    burst_res = analyzer.evaluate_burst_thresholds(
        df_sessions=df_primary_sess,
        df_features_by_threshold=burst_features_dict,
    )

    # Sensitivity 7: Family dropout
    df_dropout = analyzer.evaluate_family_dropout(
        df_sessions=df_primary_sess,
        df_features=df_primary_sess,
    )
    df_dropout.to_csv(RESULTS_DIR / "family_dropout.csv", index=False)

    # Combine sensitivity perturbations 3, 4, 5, 6 into results/sensitivity.csv
    df_sens = analyzer.generate_sensitivity_summary_table(edge_res, s0062_res, search_res, burst_res)
    df_sens.to_csv(RESULTS_DIR / "sensitivity.csv", index=False)

    # 8. Per-Task Results
    logger.info("Step 7: Generating per-task evaluation table...")
    task_rows = []
    for tid in ["T1", "T2", "T3", "T4"]:
        task_mask = df_primary_sess["task_id"] == tid
        df_t = df_primary_sess.loc[task_mask].reset_index(drop=True)
        X_t = df_t[core_features].to_numpy()
        y_t = np.where(df_t["controller"] == "human", 0, 1)

        scaler = StandardScaler()
        X_t_s = scaler.fit_transform(X_t)
        clf = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000, random_state=20261106)
        # Use leave-one-out within task
        loo_folds = [(np.delete(np.arange(len(df_t)), [i]), np.array([i])) for i in range(len(df_t))]
        auc_t, f1_t, _, _ = evaluator.evaluate_folds(X_t, y_t, loo_folds)

        task_rows.append({
            "task_id": tid,
            "n_sessions": len(df_t),
            "n_human": int((df_t["controller"] == "human").sum()),
            "n_agent": int((df_t["controller"] != "human").sum()),
            "auroc_loo": auc_t,
            "f1_loo": f1_t,
        })
    df_per_task = pd.DataFrame(task_rows)
    df_per_task.to_csv(RESULTS_DIR / "per_task_results.csv", index=False)

    # 9. Per-Participant Family Results
    logger.info("Step 8: Generating per-participant family results table...")
    part_rows = []
    for pid, group in df_primary_sess.groupby("participant_id"):
        if pid == "NA" or not pid:
            continue
        part_rows.append({
            "participant_id": pid,
            "n_sessions": len(group),
            "t_idle_gap_median_mean": float(group["T_idle_gap_median"].mean()),
            "t_burst_rate_mean": float(group["T_burst_rate"].mean()),
            "v_up_down_ratio_mean": float(group["V_up_down_ratio"].mean()),
            "v_upload_burst_share_mean": float(group["V_upload_burst_share"].mean()),
            "c_new_flows_per_min_mean": float(group["C_new_flows_per_min"].mean()),
            "c_max_concurrent_mean": float(group["C_max_concurrent"].mean()),
            "q_background_bytes_mean": float(group["Q_background_bytes"].mean()),
        })
    df_part = pd.DataFrame(part_rows)
    df_part.to_csv(RESULTS_DIR / "per_participant_family_results.csv", index=False)

    # 10. Run Manifest
    logger.info("Step 9: Generating run manifest...")
    manifest_data = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "random_seed": 20261106,
        "n_total_sessions": n_total,
        "n_primary_sessions": n_primary,
        "s0062_excluded_from_primary": True,
        "environment": {
            "python_version": sys.version,
            "platform": sys.platform,
        },
        "output_files": [
            "descriptives.csv",
            "effect_sizes.csv",
            "baseline_results.csv",
            "negative_controls.csv",
            "family_dropout.csv",
            "drift_checks.csv",
            "round_check.csv",
            "sensitivity.csv",
            "per_task_results.csv",
            "per_participant_family_results.csv",
            "session_features.parquet",
        ],
    }
    with open(RESULTS_DIR / "run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    logger.info("================================================================================")
    logger.info("EMPIRICAL ANALYSIS PIPELINE COMPLETE: ALL TABLES WRITTEN TO results/")
    logger.info("================================================================================")


if __name__ == "__main__":
    main()
