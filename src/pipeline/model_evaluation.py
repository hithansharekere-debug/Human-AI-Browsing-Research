"""Model Evaluation & Cross-Validation Module.

Role: Person B (Analysis Lead)
Implements exact baseline definitions B0-B8, grouped cross-validation splits
(10-fold LOPO and 4-fold LOTO), and evaluation metrics according to PREREG.md.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, f1_score
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger("human_ai_egress.model_evaluation")


# ==============================================================================
# BASELINE FEATURE DEFINITIONS (B0 - B8)
# ==============================================================================
# Exactly restores the original authoritative definitions:
# B0: Majority-class baseline (AUROC 0.5 expected)
# B1: Vendor shortcut using A features
# B2: JA4-only website-flow baseline using H features (Design check: stop if > 0.6)
# B3: Destination/search baseline using D features
# B4: Length-only baseline using L features
# B5: T+V+C using all flows, retained as a shortcut/contamination diagnostic
# B6: T+V+C using website flows only (HEADLINE MODEL)
# B7: B6 with length-normalised features (Is B6 just B4 in disguise?)
# B8: Vendor-to-website lag only (Cross-flow timing)

BASELINE_DESCRIPTIONS: Dict[str, str] = {
    "B0": "Majority class baseline (floor, expected AUROC ~0.50)",
    "B1": "Vendor shortcut using A features (A_vendor_present, A_vendor_bytes)",
    "B2": "JA4 TLS handshake on website flows using H features (Design check: stop if > 0.60)",
    "B3": "Destination/search baseline using D features (D_dest_count, D_search_present)",
    "B4": "Length-only baseline using L features (L_duration_s, L_total_bytes, L_n_flows)",
    "B5": "T+V+C using all flows (diagnostic for F1 gvt1 and F2 search contamination)",
    "B6": "T+V+C using website flows only (HEADLINE MODEL; A, H, D, L, Q removed)",
    "B7": "B6 with length-normalised features (tests if B6 is driven by session duration)",
    "B8": "Vendor-to-website cross-flow lag only (cross-flow timing condition)",
}

# Exact authoritative feature pools by baseline
BASELINE_FEATURE_POOLS: Dict[str, List[str]] = {
    "B0": [],
    "B1": ["A_vendor_present", "A_vendor_bytes"],
    "B2": ["H_ja4_mode", "H_ja4_n_distinct"],
    "B3": ["D_dest_count", "D_search_present"],
    "B4": ["L_duration_s", "L_total_bytes", "L_n_flows"],
    "B4_duration_only": ["L_duration_s"],
    "B4_gvt1_diag": ["L_duration_s", "L_total_bytes_with_gvt1", "L_n_flows_with_gvt1"],
    "B5": [
        # All flows T+V+C (unfiltered diagnostic showing F1 gvt1 and F2 search contamination)
        "T_idle_gap_median_all", "T_idle_gap_cv_all", "T_idle_gap_entropy_all", "T_burst_rate_all",
        "V_up_down_ratio_all", "V_upload_burst_share_all",
        "C_new_flows_per_min_all", "C_max_concurrent_all",
    ],
    # B6 / B6_core6: PRIMARY HEADLINE MODEL (strictly 6 standardized features)
    # Explicit resolution of the <= 6 feature requirement for L2 Logistic Regression (C=1.0)
    "B6": [
        "T_idle_gap_median", "T_burst_rate",
        "V_up_down_ratio", "V_upload_burst_share",
        "C_new_flows_per_min", "C_max_concurrent",
    ],
    "B6_core6": [
        "T_idle_gap_median", "T_burst_rate",
        "V_up_down_ratio", "V_upload_burst_share",
        "C_new_flows_per_min", "C_max_concurrent",
    ],
    # Random Forest check uses the EXACT SAME 6 core features (secondary check only)
    "B6_rf_check": [
        "T_idle_gap_median", "T_burst_rate",
        "V_up_down_ratio", "V_upload_burst_share",
        "C_new_flows_per_min", "C_max_concurrent",
    ],
    "B7": [
        # Length-normalized T+V+C features (rate per second or duration-adjusted)
        "T_burst_rate", "T_idle_gap_median",
        "V_up_down_ratio", "V_upload_burst_share",
        "C_new_flows_per_min", "C_max_concurrent",
    ],
    "B8": ["T_vendor_to_website_lag_s"],
}


# ==============================================================================
# GROUPED SPLIT GENERATORS (LOPO & LOTO)
# ==============================================================================

def generate_lopo_folds(
    df: pd.DataFrame,
    n_folds: int = 10,
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """Generates the authoritative 10-fold Leave-One-Participant-Out (LOPO) splits.

    According to Handover Step 8:
    - Fold k tests on all sessions of human participant Pk (P01 for k=1 .. P10 for k=10)
      plus agent sessions with rep == k (4 sessions, one per task).
    - Trains on all other human participants and agent reps.
    - Zero leakage: No participant and no agent rep is ever in both train and test.

    Args:
        df: DataFrame containing metadata columns 'controller', 'participant_id', and 'rep'.
        n_folds: Number of folds (fixed at 10 for pilot-v1).

    Returns:
        List of 10 (train_indices, test_indices) tuples.
    """
    indices = np.arange(len(df))
    folds: List[Tuple[np.ndarray, np.ndarray]] = []

    controllers = df["controller"].values
    participants = df["participant_id"].fillna("").astype(str).values
    reps = df["rep"].fillna(-1).astype(int).values

    for k in range(1, n_folds + 1):
        target_p = f"P{k:02d}"
        target_rep = k

        # Test condition: Human participant Pk OR Agent repetition k
        test_mask = (
            ((controllers == "human") & (participants == target_p))
            | ((controllers != "human") & (reps == target_rep))
        )

        test_idx = indices[test_mask]
        train_idx = indices[~test_mask]

        if len(test_idx) == 0:
            logger.warning("LOPO fold %d has 0 test sessions (target_p=%s, target_rep=%d)", k, target_p, target_rep)

        folds.append((train_idx, test_idx))

    return folds


def generate_loto_folds(
    df: pd.DataFrame,
    tasks: Sequence[str] = ("T1", "T2", "T3", "T4"),
) -> List[Tuple[np.ndarray, np.ndarray]]:
    """Generates the authoritative 4-fold Leave-One-Task-Out (LOTO) splits.

    According to Handover Step 8:
    - The test fold holds every session of one task, human and agent.
    - Trains on all sessions of the remaining 3 tasks.

    Args:
        df: DataFrame containing metadata column 'task_id'.
        tasks: Sequence of task IDs (T1, T2, T3, T4).

    Returns:
        List of 4 (train_indices, test_indices) tuples.
    """
    indices = np.arange(len(df))
    folds: List[Tuple[np.ndarray, np.ndarray]] = []
    task_ids = df["task_id"].values

    for task in tasks:
        test_mask = (task_ids == task)
        test_idx = indices[test_mask]
        train_idx = indices[~test_mask]
        folds.append((train_idx, test_idx))

    return folds


# ==============================================================================
# MODEL EVALUATOR
# ==============================================================================

@dataclass(frozen=True)
class ModelPerformanceMetrics:
    """Evaluation metrics for a trained classifier (legacy dataclass preserved for compatibility)."""
    model_name: str
    roc_auc: float
    pr_auc: float = 0.0
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    brier_score: float = 0.0
    cv_splits: int = 5


@dataclass(frozen=True)
class BaselineEvaluationResult:
    """Record of a baseline evaluation under a specific cross-validation split."""
    baseline: str
    split_name: str
    model_name: str
    auroc: float
    f1: float
    n_sessions: int
    n_features: int
    features_used: List[str]


class ModelEvaluator:
    """Evaluates egress baseline classifiers under strict grouped CV protocols."""

    def __init__(self, random_seed: int = 20261106) -> None:
        self.seed = random_seed

    def evaluate_folds(
        self,
        X: np.ndarray,
        y: np.ndarray,
        folds: List[Tuple[np.ndarray, np.ndarray]],
        model_type: str = "logistic_regression",
    ) -> Tuple[float, float, np.ndarray, np.ndarray]:
        """Evaluates a classifier across pre-computed cross-validation folds.

        Args:
            X: Feature matrix (N samples x D features).
            y: Binary target labels (0 = Human, 1 = AI).
            folds: List of (train_idx, test_idx) tuples.
            model_type: 'logistic_regression' (primary, L2 C=1.0) or 'random_forest' (check).

        Returns:
            Tuple of (pooled_auroc, pooled_f1, pooled_y_true, pooled_y_prob).
        """
        y_true_all: List[int] = []
        y_prob_all: List[float] = []

        for train_idx, test_idx in folds:
            if len(test_idx) == 0:
                continue

            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]

            # Standardize features within training fold to prevent leakage
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)

            if model_type == "logistic_regression":
                clf = LogisticRegression(
                    C=1.0,
                    solver="lbfgs",
                    max_iter=1000,
                    random_state=self.seed,
                )
            elif model_type == "random_forest":
                clf = RandomForestClassifier(
                    n_estimators=500,
                    max_features="sqrt",
                    random_state=self.seed,
                )
            else:
                raise ValueError(f"Unsupported model_type: {model_type}")

            clf.fit(X_train_scaled, y_train)
            probs = clf.predict_proba(X_test_scaled)[:, 1]

            y_true_all.extend(y_test)
            y_prob_all.extend(probs)

        y_true_arr = np.array(y_true_all)
        y_prob_arr = np.array(y_prob_all)

        # Handle edge cases (e.g. single class in pooled predictions)
        if len(np.unique(y_true_arr)) < 2:
            auroc = 0.50
        else:
            auroc = float(roc_auc_score(y_true_arr, y_prob_arr))

        y_pred_arr = (y_prob_arr >= 0.5).astype(int)
        f1 = float(f1_score(y_true_arr, y_pred_arr, zero_division=0))

        return auroc, f1, y_true_arr, y_prob_arr
