"""Negative Controls Module.

Role: Person B (Analysis Lead)
Implements authoritative negative controls according to PREREG.md and Handover Step 9:
- NC1: Exactly 200 within-task label permutations of headline model B6 under LOTO and LOPO.
- NC2: Human-vs-Human day classification (7 Nov = 0, 9 Nov = 1) using participant-grouped folds and B6 website features.
- NC2_supp_ai_day_diagnostic: Supplementary AI-vs-human day diagnostic.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, f1_score
from sklearn.preprocessing import StandardScaler

from src.pipeline.model_evaluation import generate_loto_folds, generate_lopo_folds

logger = logging.getLogger("human_ai_egress.negative_controls")


@dataclass(frozen=True)
class PermutationTestResult:
    """Summary of label permutation negative control (compatibility alias)."""
    observed_roc_auc: float
    permuted_auc_mean: float
    permuted_auc_std: float
    p_value_empirical: float
    n_permutations: int
    passed_null_check: bool


@dataclass(frozen=True)
class NC1PermutationResult:
    """Summary of NC1 within-task label permutation negative control."""
    observed_auroc: float
    permuted_aurocs: List[float]
    null_mean_auroc: float
    null_std_auroc: float
    empirical_p_value: float
    n_permutations: int
    passed_null_check: bool  # True if permuted distribution centers near 0.50 (within 0.45 - 0.55)


@dataclass(frozen=True)
class NC2DayControlResult:
    """Summary of NC2 Human-vs-Human collection day negative control."""
    auroc: float
    f1: float
    n_sessions: int
    n_nov7_sessions: int
    n_nov9_sessions: int
    passed_drift_check: bool  # True if AUROC centers near 0.50 (within 0.40 - 0.60)
    is_primary_control: bool = True


@dataclass(frozen=True)
class NC2SupplementaryAIDayResult:
    """Summary of supplementary AI-vs-Human day diagnostic."""
    comparison_name: str
    auroc: float
    f1: float
    is_supplementary: bool = True


class NegativeControlValidator:
    """Executes negative controls to rule out spurious discrimination and environmental drift."""

    def __init__(
        self,
        n_permutations: int = 200,  # Authoritative: 200 within-task permutations
        random_seed: int = 20261106,
    ) -> None:
        self.n_permutations = n_permutations
        self.seed = random_seed

    def permute_labels_within_tasks(
        self,
        df_sessions: pd.DataFrame,
        rng: np.random.Generator,
    ) -> np.ndarray:
        """Shuffles controller labels within each task independently to preserve task-specific base rates."""
        permuted_labels = np.zeros(len(df_sessions), dtype=int)
        y_true = np.where(df_sessions["controller"] == "human", 0, 1)

        for task in df_sessions["task_id"].unique():
            mask = (df_sessions["task_id"] == task).values
            indices = np.where(mask)[0]
            labels = y_true[indices]
            shuffled = rng.permutation(labels)
            permuted_labels[indices] = shuffled

        return permuted_labels

    def run_nc1_label_permutation(
        self,
        df_sessions: pd.DataFrame,
        X_features: np.ndarray,
        split_type: str = "lopo",
        observed_auroc: Optional[float] = None,
    ) -> NC1PermutationResult:
        """Executes NC1: exactly 200 within-task label permutations of B6.

        Args:
            df_sessions: DataFrame containing session metadata (controller, task_id, participant_id, rep).
            X_features: Standardized B6 feature matrix.
            split_type: 'lopo' (10-fold LOPO) or 'loto' (4-fold LOTO).
            observed_auroc: The true model's unpermuted cross-validated AUROC.

        Returns:
            NC1PermutationResult.
        """
        rng = np.random.default_rng(self.seed)
        null_aurocs = np.zeros(self.n_permutations)

        logger.info("Executing NC1: %d within-task label permutations under %s...", self.n_permutations, split_type)

        # Precompute folds based on session grouping
        if split_type == "lopo":
            folds = generate_lopo_folds(df_sessions, n_folds=10)
        elif split_type == "loto":
            folds = generate_loto_folds(df_sessions)
        else:
            raise ValueError(f"Unsupported split_type for NC1: {split_type}")

        for i in range(self.n_permutations):
            y_perm = self.permute_labels_within_tasks(df_sessions, rng)
            y_true_perm: List[int] = []
            y_prob_perm: List[float] = []

            for train_idx, test_idx in folds:
                if len(test_idx) == 0:
                    continue

                X_train, X_test = X_features[train_idx], X_features[test_idx]
                y_train, y_test = y_perm[train_idx], y_perm[test_idx]

                scaler = StandardScaler()
                X_tr_s = scaler.fit_transform(X_train)
                X_te_s = scaler.transform(X_test)

                clf = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000, random_state=self.seed)
                clf.fit(X_tr_s, y_train)
                probs = clf.predict_proba(X_te_s)[:, 1]

                y_true_perm.extend(y_test)
                y_prob_perm.extend(probs)

            y_true_arr = np.array(y_true_perm)
            y_prob_arr = np.array(y_prob_perm)

            if len(np.unique(y_true_arr)) < 2:
                null_aurocs[i] = 0.50
            else:
                null_aurocs[i] = float(roc_auc_score(y_true_arr, y_prob_arr))

        mean_null = float(np.mean(null_aurocs))
        std_null = float(np.std(null_aurocs))

        if observed_auroc is not None:
            empirical_p = float(np.mean(null_aurocs >= observed_auroc))
        else:
            empirical_p = 1.0

        # Permutation test passes if null distribution centers near 0.50
        passed_null = bool(0.45 <= mean_null <= 0.55)

        logger.info(
            "NC1 Permutation test complete (%s): Null AUROC = %.3f (+/- %.3f), passed = %s",
            split_type,
            mean_null,
            std_null,
            passed_null,
        )

        return NC1PermutationResult(
            observed_auroc=observed_auroc if observed_auroc is not None else 0.50,
            permuted_aurocs=null_aurocs.tolist(),
            null_mean_auroc=mean_null,
            null_std_auroc=std_null,
            empirical_p_value=empirical_p,
            n_permutations=self.n_permutations,
            passed_null_check=passed_null,
        )

    def run_nc1_both_splits(
        self,
        df_sessions: pd.DataFrame,
        X_features: np.ndarray,
        observed_auroc_loto: Optional[float] = None,
        observed_auroc_lopo: Optional[float] = None,
    ) -> Dict[str, NC1PermutationResult]:
        """Executes NC1 across both LOTO and LOPO splits (200 permutations each)."""
        logger.info("Running NC1 across both LOTO and LOPO splits...")
        return {
            "loto": self.run_nc1_label_permutation(
                df_sessions, X_features, split_type="loto", observed_auroc=observed_auroc_loto
            ),
            "lopo": self.run_nc1_label_permutation(
                df_sessions, X_features, split_type="lopo", observed_auroc=observed_auroc_lopo
            ),
        }

    def run_nc2_human_day_control(
        self,
        df_human_sessions: pd.DataFrame,
        X_features: np.ndarray,
    ) -> NC2DayControlResult:
        """Executes Primary NC2: Human-vs-Human day classification.

        According to Handover Step 9:
        - Human sessions from 7 November: label 0 (P01-P03 + part of P04).
        - Human sessions from 9 November: label 1 (part of P04 + P05-P10).
        - Uses participant-grouped folds (ensuring each participant is entirely in train or test).
        - Uses specified B6 website-only features.
        - Pooled AUROC calculation: Predictions from all held-out folds are pooled
          BEFORE calculating the overall AUROC. Individual folds containing only one class
          do not compute a standalone AUROC.
        - IMPORTANT METHODOLOGICAL NOTE: Day is completely associated with participant cohort
          in this dataset (P01-P03 on Nov 7 vs P05-P10 on Nov 9). Consequently, NC2 detects
          day/cohort-associated separability and CANNOT independently attribute any observed
          effect to environmental drift vs between-participant behavioral variance.
        """
        # Determine day from t_start_utc or schedule_slot / session metadata
        # 7 Nov 2026 -> label 0, 9 Nov 2026 -> label 1
        t_starts = df_human_sessions["t_start_utc"].fillna("").astype(str)
        is_nov9 = t_starts.str.contains("2026-11-09")
        y_day = is_nov9.astype(int).values

        n_nov7 = int((~is_nov9).sum())
        n_nov9 = int(is_nov9.sum())

        logger.info("Executing Primary NC2: Human 7 Nov (n=%d) vs Human 9 Nov (n=%d)...", n_nov7, n_nov9)

        # Participant-grouped cross-validation folds
        participants = df_human_sessions["participant_id"].unique()
        folds: List[Tuple[np.ndarray, np.ndarray]] = []
        indices = np.arange(len(df_human_sessions))

        for p in participants:
            test_mask = (df_human_sessions["participant_id"] == p).values
            test_idx = indices[test_mask]
            train_idx = indices[~test_mask]
            folds.append((train_idx, test_idx))

        y_true_all: List[int] = []
        y_prob_all: List[float] = []

        for train_idx, test_idx in folds:
            if len(test_idx) == 0:
                continue

            X_train, X_test = X_features[train_idx], X_features[test_idx]
            y_train, y_test = y_day[train_idx], y_day[test_idx]

            # In participant-grouped split across days, a fold's train set might lack one class
            if len(np.unique(y_train)) < 2:
                # Fallback to majority probability for unrepresented class
                probs = np.full(len(test_idx), 0.5)
            else:
                scaler = StandardScaler()
                X_tr_s = scaler.fit_transform(X_train)
                X_te_s = scaler.transform(X_test)

                clf = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000, random_state=self.seed)
                clf.fit(X_tr_s, y_train)
                probs = clf.predict_proba(X_te_s)[:, 1]

            y_true_all.extend(y_test)
            y_prob_all.extend(probs)

        y_true_arr = np.array(y_true_all)
        y_prob_arr = np.array(y_prob_all)

        if len(np.unique(y_true_arr)) < 2:
            auroc = 0.50
            f1 = 0.0
        else:
            auroc = float(roc_auc_score(y_true_arr, y_prob_arr))
            y_pred_arr = (y_prob_arr >= 0.5).astype(int)
            f1 = float(f1_score(y_true_arr, y_pred_arr, zero_division=0))

        passed = bool(0.40 <= auroc <= 0.60)
        logger.info("Primary NC2 complete: AUROC = %.3f, F1 = %.3f, passed = %s", auroc, f1, passed)

        return NC2DayControlResult(
            auroc=auroc,
            f1=f1,
            n_sessions=len(df_human_sessions),
            n_nov7_sessions=n_nov7,
            n_nov9_sessions=n_nov9,
            passed_drift_check=passed,
            is_primary_control=True,
        )

    def run_nc2_supp_ai_day_diagnostic(
        self,
        df_sessions: pd.DataFrame,
        X_features: np.ndarray,
    ) -> NC2SupplementaryAIDayResult:
        """Executes supplementary AI-vs-Human day diagnostic.

        Separately named and treated as supplementary per methodology requirements.
        Evaluates cross-day classification (AI Nov 6 vs Human Nov 7/9) using LOPO grouped folds.
        """
        logger.info("Executing Supplementary AI-vs-Human Day Diagnostic...")
        if len(df_sessions) == 0 or len(X_features) == 0:
            return NC2SupplementaryAIDayResult(
                comparison_name="AI_Nov6_vs_Human_Nov7_and_Nov9_diagnostic",
                auroc=0.50,
                f1=0.0,
                is_supplementary=True,
            )

        # y_target: 1 for AI (recorded 6 Nov), 0 for Human (recorded 7/9 Nov)
        if "controller" in df_sessions.columns:
            y_target = np.where(df_sessions["controller"].astype(str).str.lower() == "human", 0, 1)
        else:
            # Fallback if only day timestamps exist (e.g. mock test DataFrame)
            t_starts = df_sessions.get("t_start_utc", pd.Series([""] * len(df_sessions))).fillna("").astype(str)
            is_nov9 = t_starts.str.contains("2026-11-09")
            y_target = is_nov9.astype(int).values

        # Use LOPO folds if metadata columns exist, else k-fold
        if "participant_id" in df_sessions.columns and "rep" in df_sessions.columns:
            folds = generate_lopo_folds(df_sessions, n_folds=10)
        else:
            indices = np.arange(len(df_sessions))
            folds = [(np.delete(indices, [i]), np.array([i])) for i in range(len(df_sessions))]

        y_true_all: List[int] = []
        y_prob_all: List[float] = []

        for train_idx, test_idx in folds:
            if len(test_idx) == 0:
                continue

            X_train, X_test = X_features[train_idx], X_features[test_idx]
            y_train, y_test = y_target[train_idx], y_target[test_idx]

            if len(np.unique(y_train)) < 2:
                probs = np.full(len(test_idx), 0.5)
            else:
                scaler = StandardScaler()
                X_tr_s = scaler.fit_transform(X_train)
                X_te_s = scaler.transform(X_test)

                clf = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000, random_state=self.seed)
                clf.fit(X_tr_s, y_train)
                probs = clf.predict_proba(X_te_s)[:, 1]

            y_true_all.extend(y_test)
            y_prob_all.extend(probs)

        y_true_arr = np.array(y_true_all)
        y_prob_arr = np.array(y_prob_all)

        if len(np.unique(y_true_arr)) < 2:
            auroc = 0.50
            f1 = 0.0
        else:
            auroc = float(roc_auc_score(y_true_arr, y_prob_arr))
            y_pred_arr = (y_prob_arr >= 0.5).astype(int)
            f1 = float(f1_score(y_true_arr, y_pred_arr, zero_division=0))

        logger.info("Supplementary AI Day Diagnostic complete: AUROC = %.3f, F1 = %.3f", auroc, f1)

        return NC2SupplementaryAIDayResult(
            comparison_name="AI_Nov6_vs_Human_Nov7_and_Nov9_diagnostic",
            auroc=auroc,
            f1=f1,
            is_supplementary=True,
        )
