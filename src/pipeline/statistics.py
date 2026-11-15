"""Statistical Testing & Hypothesis Evaluation Module.

Role: Person B (Analysis Lead)
Executes preregistered hypothesis testing, calculates parametric and
non-parametric effect sizes (Cliff's delta, Cohen's d), bootstrap confidence intervals,
and applies multiple comparison corrections (Benjamini-Hochberg FDR).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger("human_ai_egress.statistics")


@dataclass(frozen=True)
class HypothesisTestResult:
    """Standardized output container for a statistical hypothesis test."""
    hypothesis_id: str
    feature_name: str
    test_type: str
    statistic: float
    p_value: float
    adjusted_p_value: Optional[float]
    effect_size_name: str
    effect_size_val: float
    ci_lower: float
    ci_upper: float
    is_significant: bool
    notes: str = ""


def compute_cliffs_delta(x: np.ndarray, y: np.ndarray) -> float:
    """Calculates Cliff's delta non-parametric effect size.

    delta = #(x > y) - #(x < y) / (n_x * n_y)
    """
    x = np.asarray(x).ravel()
    y = np.asarray(y).ravel()
    n_x, n_y = len(x), len(y)
    if n_x == 0 or n_y == 0:
        return 0.0

    # Pairwise comparison matrix
    diff = x[:, None] - y[None, :]
    greater = np.sum(diff > 0)
    less = np.sum(diff < 0)
    return float((greater - less) / (n_x * n_y))


def bootstrap_ci(
    x: np.ndarray,
    y: np.ndarray,
    stat_func,
    n_resamples: int = 2000,
    ci_level: float = 0.95,
    seed: int = 42,
) -> Tuple[float, float]:
    """Computes percentile bootstrap confidence interval for a two-sample metric."""
    rng = np.random.default_rng(seed)
    n_x, n_y = len(x), len(y)
    resamples = np.zeros(n_resamples)

    for i in range(n_resamples):
        x_boot = rng.choice(x, size=n_x, replace=True)
        y_boot = rng.choice(y, size=n_y, replace=True)
        resamples[i] = stat_func(x_boot, y_boot)

    alpha_tail = (1.0 - ci_level) / 2.0
    lower = float(np.percentile(resamples, 100 * alpha_tail))
    upper = float(np.percentile(resamples, 100 * (1.0 - alpha_tail)))
    return lower, upper


def adjust_p_values_fdr_bh(p_values: List[float]) -> List[float]:
    """Applies Benjamini-Hochberg False Discovery Rate (FDR) adjustment."""
    p_arr = np.asarray(p_values)
    n = len(p_arr)
    if n == 0:
        return []

    order = np.argsort(p_arr)
    ranked_p = p_arr[order]
    q_vals = ranked_p * n / (np.arange(1, n + 1))

    # Enforce monotonicity in reverse
    for i in range(n - 2, -1, -1):
        q_vals[i] = min(q_vals[i], q_vals[i + 1])

    # Un-sort to restore original order
    adjusted = np.empty(n)
    adjusted[order] = np.clip(q_vals, 0.0, 1.0)
    return adjusted.tolist()


class StatisticalEvaluator:
    """Evaluates preregistered hypotheses comparing Human vs. AI cohorts."""

    def __init__(
        self,
        alpha: float = 0.05,
        bootstrap_iterations: int = 2000,
        random_seed: int = 42,
    ) -> None:
        self.alpha = alpha
        self.n_boot = bootstrap_iterations
        self.seed = random_seed

    def test_two_sample_difference(
        self,
        human_samples: np.ndarray,
        ai_samples: np.ndarray,
        hypothesis_id: str,
        feature_name: str,
        use_welch: bool = False,
    ) -> HypothesisTestResult:
        """Executes a two-sample hypothesis test with effect size and bootstrap CI."""
        h = np.asarray(human_samples, dtype=float).ravel()
        a = np.asarray(ai_samples, dtype=float).ravel()

        if len(h) < 3 or len(a) < 3:
            return HypothesisTestResult(
                hypothesis_id=hypothesis_id,
                feature_name=feature_name,
                test_type="Insufficient Samples",
                statistic=0.0,
                p_value=1.0,
                adjusted_p_value=1.0,
                effect_size_name="None",
                effect_size_val=0.0,
                ci_lower=0.0,
                ci_upper=0.0,
                is_significant=False,
                notes="Sample size too small to evaluate",
            )

        if use_welch:
            test_type = "Welch t-test"
            stat, p_val = stats.ttest_ind(h, a, equal_var=False)
            eff_name = "Cohen's d"
            pooled_std = np.sqrt(((np.var(h, ddof=1) + np.var(a, ddof=1)) / 2.0))
            eff_val = float((np.mean(h) - np.mean(a)) / max(1e-9, pooled_std))
            ci_low, ci_high = bootstrap_ci(
                h, a, lambda x, y: (np.mean(x) - np.mean(y)) / max(1e-9, pooled_std),
                n_resamples=self.n_boot, seed=self.seed
            )
        else:
            test_type = "Mann-Whitney U"
            res = stats.mannwhitneyu(h, a, alternative="two-sided")
            stat, p_val = float(res.statistic), float(res.pvalue)
            eff_name = "Cliff's delta"
            eff_val = compute_cliffs_delta(h, a)
            ci_low, ci_high = bootstrap_ci(
                h, a, compute_cliffs_delta,
                n_resamples=self.n_boot, seed=self.seed
            )

        return HypothesisTestResult(
            hypothesis_id=hypothesis_id,
            feature_name=feature_name,
            test_type=test_type,
            statistic=float(stat),
            p_value=float(p_val),
            adjusted_p_value=None,  # Populated via post-hoc FDR adjustment
            effect_size_name=eff_name,
            effect_size_val=float(eff_val),
            ci_lower=float(ci_low),
            ci_upper=float(ci_high),
            is_significant=bool(p_val < self.alpha),
            notes="",
        )

    def evaluate_preregistered_battery(
        self,
        df_sessions: pd.DataFrame,
        label_col: str = "cohort_label",
    ) -> List[HypothesisTestResult]:
        """Runs the battery of preregistered confirmatory hypothesis tests."""
        if df_sessions.empty or label_col not in df_sessions.columns:
            logger.warning("Empty or unlabelled session DataFrame. Returning empty test battery.")
            return []

        human_df = df_sessions[df_sessions[label_col].str.upper() == "HUMAN"]
        ai_df = df_sessions[df_sessions[label_col].str.upper() == "AI"]

        battery = [
            ("H1_IAT_SKEW", "iat_skew_out", False),
            ("H1_IDLE_PAUSE", "idle_duration_mean", False),
            ("H2_CONCURRENCY", "concurrency_peak", True),
            ("H2_BYTES_RATIO", "bytes_ratio_out_in", False),
        ]

        raw_results: List[HypothesisTestResult] = []
        for hyp_id, feat, use_welch in battery:
            if feat in human_df.columns and feat in ai_df.columns:
                h_vals = human_df[feat].dropna().to_numpy()
                a_vals = ai_df[feat].dropna().to_numpy()
                res = self.test_two_sample_difference(h_vals, a_vals, hyp_id, feat, use_welch)
                raw_results.append(res)

        # Apply FDR correction across all battery tests
        if raw_results:
            p_vals = [r.p_value for r in raw_results]
            adj_p = adjust_p_values_fdr_bh(p_vals)
            adjusted_results = []
            for r, q in zip(raw_results, adj_p):
                adjusted_results.append(
                    HypothesisTestResult(
                        hypothesis_id=r.hypothesis_id,
                        feature_name=r.feature_name,
                        test_type=r.test_type,
                        statistic=r.statistic,
                        p_value=r.p_value,
                        adjusted_p_value=float(q),
                        effect_size_name=r.effect_size_name,
                        effect_size_val=r.effect_size_val,
                        ci_lower=r.ci_lower,
                        ci_upper=r.ci_upper,
                        is_significant=bool(q < self.alpha),
                        notes=r.notes,
                    )
                )
            return adjusted_results

        return []
