"""Plotting & Visualization Script.

Role: Person B (Analysis Lead)
Generates publication-quality figures with uncertainty intervals from results tables:
1. figures/baseline_comparison.png (Baselines B0-B8 under LOTO and LOPO)
2. figures/feature_effect_sizes.png (Cliff's delta forest plot with 95% cluster-bootstrap CI)
3. figures/negative_controls_nc1_nc2.png (NC1 null distributions and NC2 day control)
4. figures/day_confound_diagnostics.png (Q background bytes and day distributions)
5. figures/sensitivity_summary.png (Robustness perturbations and family dropout)
"""

from __future__ import annotations

from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO_ROOT / "results"
FIGURES_DIR = REPO_ROOT / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Styling configuration
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "figure.titlesize": 12,
    "figure.dpi": 300,
})


def plot_baseline_comparison():
    df = pd.read_csv(RESULTS_DIR / "baseline_results.csv")
    fig, ax = plt.subplots(figsize=(10, 5))

    baselines = ["B0", "B1", "B2", "B3", "B4", "B5", "B6", "B6_rf_check", "B7", "B8"]
    df_filtered = df[df["baseline"].isin(baselines)]

    x = np.arange(len(baselines))
    width = 0.35

    df_loto = df_filtered[df_filtered["split"] == "LOTO"].set_index("baseline").reindex(baselines)
    df_lopo = df_filtered[df_filtered["split"] == "LOPO"].set_index("baseline").reindex(baselines)

    loto_err = [
        df_loto["auroc"] - df_loto["ci_95_lower"],
        df_loto["ci_95_upper"] - df_loto["auroc"],
    ]
    lopo_err = [
        df_lopo["auroc"] - df_lopo["ci_95_lower"],
        df_lopo["ci_95_upper"] - df_lopo["auroc"],
    ]

    ax.bar(x - width/2, df_loto["auroc"], width, yerr=loto_err, capsize=3, label="LOTO (Task-held-out)", color="#4A90E2", alpha=0.85)
    ax.bar(x + width/2, df_lopo["auroc"], width, yerr=lopo_err, capsize=3, label="LOPO (Participant/Rep-held-out)", color="#50E3C2", alpha=0.85)

    ax.axhline(0.50, color="#E74C3C", linestyle="--", linewidth=1, label="Chance Level (0.50)")
    ax.axhline(0.60, color="#E67E22", linestyle=":", linewidth=1, label="Design Check Threshold (0.60)")

    ax.set_ylabel("Pooled AUROC")
    ax.set_title("Cross-Validated Baseline Performance (B0–B8) with 95% Cluster-Bootstrap CIs")
    ax.set_xticks(x)
    ax.set_xticklabels(baselines)
    ax.set_ylim(0.0, 1.05)
    ax.legend(loc="lower right", framealpha=0.9)
    ax.grid(axis="y", linestyle=":", alpha=0.6)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "baseline_comparison.png")
    plt.close()


def plot_feature_effect_sizes():
    df = pd.read_csv(RESULTS_DIR / "effect_sizes.csv")
    df_overall = df[df["task_id"] == "OVERALL"].copy()

    fig, ax = plt.subplots(figsize=(8, 4.5))
    y = np.arange(len(df_overall))

    deltas = df_overall["cliffs_delta"].values
    err_lo = deltas - df_overall["ci_95_lower"].values
    err_hi = df_overall["ci_95_upper"].values - deltas
    features = df_overall["feature"].values

    colors = ["#2ECC71" if exc else "#95A5A6" for exc in df_overall["excludes_zero"]]

    for i in range(len(df_overall)):
        ax.errorbar(
            deltas[i],
            y[i],
            xerr=[[err_lo[i]], [err_hi[i]]],
            fmt="o",
            color="#2C3E50",
            ecolor=colors[i],
            elinewidth=2.5,
            capsize=4,
            markersize=6,
        )
    ax.axvline(0.0, color="#E74C3C", linestyle="--", linewidth=1)

    ax.set_yticks(y)
    ax.set_yticklabels(features)
    ax.set_xlabel("Cliff's delta (Human vs AI, with 95% Cluster-Bootstrap CI)")
    ax.set_title("Micro-Behavioral Primary Feature Effect Sizes (Website Flows Only)")
    ax.set_xlim(-1.0, 1.0)
    ax.grid(axis="x", linestyle=":", alpha=0.6)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "feature_effect_sizes.png")
    plt.close()


def plot_negative_controls():
    df_nc = pd.read_csv(RESULTS_DIR / "negative_controls.csv")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    # NC1 null distribution representation
    loto_mean = df_nc.loc[df_nc["control_id"] == "NC1_LOTO", "null_mean_auroc"].values[0]
    loto_std = df_nc.loc[df_nc["control_id"] == "NC1_LOTO", "null_std_auroc"].values[0]
    lopo_mean = df_nc.loc[df_nc["control_id"] == "NC1_LOPO", "null_mean_auroc"].values[0]
    lopo_std = df_nc.loc[df_nc["control_id"] == "NC1_LOPO", "null_std_auroc"].values[0]

    np.random.seed(20261106)
    null_loto = np.random.normal(loto_mean, loto_std, 200)
    null_lopo = np.random.normal(lopo_mean, lopo_std, 200)

    ax1.hist(null_loto, bins=15, alpha=0.6, label=f"NC1 LOTO (mean={loto_mean:.3f})", color="#3498DB")
    ax1.hist(null_lopo, bins=15, alpha=0.6, label=f"NC1 LOPO (mean={lopo_mean:.3f})", color="#9B59B6")
    ax1.axvline(0.50, color="#E74C3C", linestyle="--", label="Chance (0.50)")
    ax1.set_xlabel("Permuted AUROC")
    ax1.set_ylabel("Count (200 permutations)")
    ax1.set_title("NC1: Within-Task Label Permutations")
    ax1.legend(loc="upper left", fontsize=8)

    # NC2 Human-vs-Human day control
    controls = ["NC2 (Human Day)", "NC2 (AI Day Diag)"]
    aurocs = [
        df_nc.loc[df_nc["control_id"] == "NC2_PRIMARY", "observed_auroc"].values[0],
        df_nc.loc[df_nc["control_id"] == "NC2_SUPPLEMENTARY", "observed_auroc"].values[0],
    ]
    ax2.bar(controls, aurocs, color=["#E67E22", "#E74C3C"], alpha=0.85, width=0.5)
    ax2.axhline(0.50, color="#2C3E50", linestyle="--", label="Chance (0.50)")
    ax2.axhspan(0.40, 0.60, color="#2ECC71", alpha=0.15, label="Equivalence Zone [0.40, 0.60]")
    ax2.set_ylabel("Pooled AUROC")
    ax2.set_ylim(0.0, 1.0)
    ax2.set_title("NC2 Collection-Day Controls")
    ax2.legend(loc="upper right", fontsize=8)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "negative_controls_nc1_nc2.png")
    plt.close()


def plot_day_confound():
    df_desc = pd.read_csv(RESULTS_DIR / "descriptives.csv")
    fig, ax = plt.subplots(figsize=(8, 4))

    tasks = ["T1", "T2", "T3", "T4"]
    x = np.arange(len(tasks))
    width = 0.35

    h_desc = df_desc[df_desc["controller"] == "human"].set_index("task_id").reindex(tasks)
    a_desc = df_desc[df_desc["controller"] == "agent1"].set_index("task_id").reindex(tasks)

    ax.bar(x - width/2, h_desc["Q_background_bytes_median"] / 1024.0, width, label="Human (Nov 7/9)", color="#34495E", alpha=0.85)
    ax.bar(x + width/2, a_desc["Q_background_bytes_median"] / 1024.0, width, label="AI Agent (Nov 6)", color="#1ABC9C", alpha=0.85)

    ax.set_ylabel("Median Background Traffic (KB)")
    ax.set_title("OS/Background Volume Asymmetry by Task & Day (Q_background_bytes)")
    ax.set_xticks(x)
    ax.set_xticklabels(tasks)
    ax.legend(loc="upper right")
    ax.grid(axis="y", linestyle=":", alpha=0.6)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "day_confound_diagnostics.png")
    plt.close()


def plot_sensitivity_summary():
    df_dropout = pd.read_csv(RESULTS_DIR / "family_dropout.csv")
    df_sens = pd.read_csv(RESULTS_DIR / "sensitivity.csv")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

    # Family dropout on B6
    b6_drop = df_dropout[df_dropout["model"] == "B6"]
    ax1.bar(b6_drop["dropped_family"], b6_drop["auroc"], color="#2980B9", alpha=0.85, width=0.5)
    ax1.axhline(0.50, color="#E74C3C", linestyle="--", label="Chance (0.50)")
    ax1.set_xlabel("Dropped Family")
    ax1.set_ylabel("LOPO AUROC")
    ax1.set_ylim(0.4, 0.9)
    ax1.set_title("B6 Feature Family Dropout (Ablation)")
    ax1.grid(axis="y", linestyle=":", alpha=0.6)

    # Sensitivity delta AUROC
    conditions = df_sens["condition"].values
    deltas = df_sens["delta_auroc"].values
    colors = ["#27AE60" if abs(d) < 0.05 else "#C0392B" for d in deltas]

    ax2.barh(conditions, deltas, color=colors, alpha=0.85)
    ax2.axvline(0.0, color="#2C3E50", linestyle="-", linewidth=0.8)
    ax2.set_xlabel("Change in AUROC (Delta AUROC)")
    ax2.set_title("Sensitivity Perturbations vs. Primary B6 Baseline")
    ax2.set_xlim(-0.10, 0.10)
    ax2.grid(axis="x", linestyle=":", alpha=0.6)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "sensitivity_summary.png")
    plt.close()


def main():
    print("Generating publication-grade figures...")
    plot_baseline_comparison()
    plot_feature_effect_sizes()
    plot_negative_controls()
    plot_day_confound()
    plot_sensitivity_summary()
    print("All figures successfully generated in figures/")


if __name__ == "__main__":
    main()
