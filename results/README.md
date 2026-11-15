# Results Package Codebook & Interpretation Guide

**Project:** Human vs. AI-Agent Browsing at the Client Egress  
**Target Recipient:** Person C (Audit/Synthesis Lead)  
**Author:** Person B (Analysis Lead)  
**Date:** 15 November 2026  
**Analysis Seed:** `20261106`  
**Dataset Scope:** Primary analysis $N=91$ study sessions (S0062 excluded due to corrupted 7 ms operator keypress window); Sensitivity analysis $N=92$ (S0062 included with reconstructed 29.299 s window).

---

## 1. Directory Structure

```
results/
├── README.md                           # This codebook and interpretation guide
├── run_manifest.json                   # Execution environment, timestamp, and reproducibility metadata
├── baseline_results.csv                # Primary (B6_core6) and baseline (B0–B8) performance metrics
├── descriptives.csv                    # Session durations, byte volumes, and flow counts by task and controller
├── effect_sizes.csv                    # Cliff's delta and 95% cluster-bootstrap CIs for primary features
├── family_dropout.csv                  # Feature family ablation (T, V, C dropout) on B5 and B6
├── negative_controls.csv               # NC1 (label permutation) and NC2 (collection day control) outcomes
├── drift_checks.csv                    # TCP handshake RTT, time-of-day overlap, and OS background diagnostics
├── round_check.csv                     # Evaluation of round 1 vs round 2 (P01–P03) stability
├── sensitivity.csv                     # Seven pre-registered sensitivity perturbation results
├── per_task_results.csv                # Task-stratified LOO classification performance
└── per_participant_family_results.csv  # Feature distributions aggregated per human participant (P01–P10)
```

Derived tabular dataset:
- `processed/session_features.parquet` (92 rows, 28 columns: full per-session extracted feature vector)
- `processed/session_features.csv` (mirror in comma-separated text)

---

## 2. Table-by-Table Codebook

### 2.1 `baseline_results.csv`
Contains evaluation metrics across both pre-registered cross-validation splitting schemes: Leave-One-Task-Out (LOTO, 4 folds) and Leave-One-Participant-Out (LOPO, 10 human folds + pooled agent evaluations).

| Column | Type | Units / Range | Definition & Interpretation |
| :--- | :--- | :--- | :--- |
| `baseline` | string | Categorical | Baseline model identifier (`B0` through `B8`, including `B6_rf500`). |
| `split` | string | `LOTO` / `LOPO` | Cross-validation grouping strategy. |
| `model` | string | Categorical | Classifier type (`majority_class`, `logistic_regression`, `random_forest`). |
| `auroc` | float | $[0.0, 1.0]$ | Area Under the Receiver Operating Characteristic curve (pooled out-of-fold). |
| `ci_95_lower` | float | $[0.0, 1.0]$ | Lower bound of 95% cluster-bootstrap confidence interval (2,000 resamples). |
| `ci_95_upper` | float | $[0.0, 1.0]$ | Upper bound of 95% cluster-bootstrap confidence interval (2,000 resamples). |
| `f1` | float | $[0.0, 1.0]$ | Macro F1-score across pooled out-of-fold predictions. |
| `n_sessions` | integer | Count | Number of retained study sessions ($N=91$). |
| `n_features` | integer | Count | Number of input features supplied to the model. |
| `features_used`| string | Text | List of exact feature column names passed to the scaler and classifier. |
| `description` | string | Text | Concise methodological description of the baseline. |

**Interpretation Guide:**
- `B0` ($\text{AUROC} = 0.500$): Trivial floor.
- `B1` ($\text{AUROC} = 1.000$): Demonstrates the vendor shortcut (Google AI infra `1e100.net` / Cloudflare AI gateway). Must NOT be used for behavioral discrimination.
- `B2` (LOTO $\text{AUROC} = 0.493$, LOPO $\text{AUROC} = 0.423$): JA4 TLS handshake fingerprint on website flows. Passes negative-control threshold ($\le 0.60$), verifying that browser TLS handshakes between human and agent Chrome builds are non-informative.
- `B4` (LOPO $\text{AUROC} = 0.760$): Window duration alone yields moderate separability because human participants took longer on unstructured research tasks.
- `B6` (`B6_core6` Logistic Regression, L2, $C=1.0$, 6 core website features): **Headline primary model**. Achieves LOPO $\text{AUROC} = 0.777$ (95% CI $[0.699, 0.868]$) and LOTO $\text{AUROC} = 0.644$ (95% CI $[0.499, 0.807]$).
- `B6_rf500` (500-tree Random Forest check, fixed seed `20261106`): Confirmatory check, LOPO $\text{AUROC} = 0.797$ (95% CI $[0.713, 0.885]$).
- `B7` (Length-normalized B6): LOPO $\text{AUROC} = 0.777$, matching B6.
- `B8` ($\text{AUROC} = 1.000$): Artifactual lag diagnostic (first vendor API request to first website TLS connection).

---

### 2.2 `effect_sizes.csv`
Reports non-parametric Cliff's delta ($\delta$) and 95% cluster-bootstrap confidence intervals for the primary features, overall and per task ($T_1$ to $T_4$). Positive values indicate higher magnitude in human sessions; negative values indicate higher magnitude in agent sessions.

| Column | Type | Units / Range | Definition & Interpretation |
| :--- | :--- | :--- | :--- |
| `feature` | string | Categorical | Primary feature name ($T, V, C$ families). |
| `task_id` | string | Categorical | Task identifier (`OVERALL`, `T1`, `T2`, `T3`, `T4`). |
| `cliffs_delta` | float | $[-1.0, 1.0]$ | Non-parametric effect size $\delta = \frac{\#(x_H > x_A) - \#(x_H < x_A)}{n_H \cdot n_A}$. |
| `ci_95_lower` | float | $[-1.0, 1.0]$ | Lower bound of 95% cluster-bootstrap CI (clustering human participants and agent runs). |
| `ci_95_upper` | float | $[-1.0, 1.0]$ | Upper bound of 95% cluster-bootstrap CI. |
| `n_human` | integer | Count | Number of human sessions in the partition. |
| `n_agent` | integer | Count | Number of agent sessions in the partition. |
| `excludes_zero`| boolean | True / False | Whether the 95% bootstrap CI strictly excludes zero ($\delta \ne 0$). |

**Key Findings:**
- `T_idle_gap_median` ($\delta = -0.586$, 95% CI $[-0.754, -0.410]$): **Excludes zero**. The AI agent pauses between bursts for significantly longer and more regular median durations (model thinking / vision inference loop) compared to human continuous micro-scrolling.
- `T_burst_rate` ($\delta = +0.312$, 95% CI $[+0.125, +0.470]$): **Excludes zero**. Humans generate more frequent discrete bursts per minute of active session time ($\text{bursts}\cdot\text{min}^{-1}$) during interaction. At the individual task level, $T_{\text{burst\_rate}}$ excludes zero in 2 of 4 tasks ($T_1$ and $T_2$).
- Volume ($V$) and Concurrency ($C$) features straddle zero overall:
  - `V_up_down_ratio`: $\delta = -0.060$ (95% CI $[-0.169, +0.044]$)
  - `V_upload_burst_share`: $\delta = -0.147$ (95% CI $[-0.323, +0.029]$)
  - `C_new_flows_per_min`: $\delta = +0.009$ (95% CI $[-0.211, +0.237]$)
  - `C_max_concurrent`: $\delta = +0.038$ (95% CI $[-0.125, +0.181]$)

---

### 2.3 `descriptives.csv`
Aggregated session duration, volume, and composition characteristics by task ($T_1$ to $T_4$) and controller (`agent1` vs `human`).

| Column | Type | Units | Definition |
| :--- | :--- | :--- | :--- |
| `controller` | string | `agent1` / `human` | Session executor class. |
| `task_id` | string | `T1`, `T2`, `T3`, `T4` | Task identifier. |
| `n_sessions` | integer | Count | Number of sessions in cell. |
| `window_duration_median_s` | float | Seconds | Median active window duration ($t_{\text{end}} - t_{\text{start}}$). |
| `window_duration_mean_s` | float | Seconds | Mean active window duration. |
| `total_bytes_median` | float | Bytes | Median total bytes transferred across all flows in window. |
| `n_flows_median` | float | Count | Median number of active transport flows in window. |
| `pct_ipv6_mean` | float | Percentage $[0, 100]$ | Mean percentage of in-window traffic routed over IPv6. Confirms Finding F3 ($\approx 95\%$--$98\%$). |
| `Q_background_bytes_median` | float | Bytes | Median OS / background traffic volume (Edge, Spotify, Windows Update). |
| `Q_gvt1_bytes_median` | float | Bytes | Median Chrome component updater volume (`*.gvt1.com`). |
| `A_vendor_present_sum` | integer | Count | Number of sessions with vendor API flows present. |
| `D_search_present_sum` | integer | Count | Number of sessions with search suggestions present. |

---

### 2.4 `family_dropout.csv`
Ablation experiment dropping entire feature families ($T, V, C$) one at a time from B5 (all flows) and B6 (website flows only) under 10-fold LOPO cross-validation.

| Column | Type | Definition |
| :--- | :--- | :--- |
| `model` | string | Model evaluated (`B5` or `B6`). |
| `dropped_family` | string | Family excluded (`none`, `T`, `V`, `C`). |
| `remaining_families` | string | Families retained in the model. |
| `auroc` | float | Out-of-fold pooled LOPO AUROC under ablation. |

**Crucial Result:**
- When $T$ (timing) is dropped from B6, LOPO AUROC collapses from **0.777 to 0.533** (near chance).
- Dropping $V$ yields AUROC = **0.765**; dropping $C$ yields AUROC = **0.769**.
- Micro-behavioral timing is the single necessary component for client egress separability.

---

### 2.5 `negative_controls.csv`
Reports falsification tests: NC1 (within-task label permutations) and NC2 (collection day controls).

| Column | Type | Definition |
| :--- | :--- | :--- |
| `control_id` | string | `NC1_LOTO`, `NC1_LOPO`, `NC2_PRIMARY`, `NC2_SUPPLEMENTARY`. |
| `name` | string | Full control description. |
| `n_permutations` | integer | Permutation iterations (200 for NC1; 0 for deterministic NC2). |
| `observed_auroc` | float | Observed model AUROC under test. |
| `null_mean_auroc` | float | Expected null AUROC (mean across permutations). |
| `null_std_auroc` | float | Standard deviation of permuted null distribution. |
| `empirical_p_value` | float | Fraction of permuted AUROCs $\ge$ observed AUROC. |
| `passed_null_check` | boolean | True if null distribution centers near chance ($0.50 \pm 0.05$). |
| `notes` | string | Diagnostic interpretation. |

**Interpretation:**
- `NC1_LOTO`: Null mean is $0.498 \pm 0.061$, observed AUROC = $0.644$, empirical $p < 0.005$ ($0 / 200 \ge 0.644$). Perfectly centers at chance (0.50). Confirms no structural leakage in task-stratified cross-validation.
- `NC1_LOPO`: Null mean is $0.431 \pm 0.084$, observed AUROC = $0.777$, empirical $p < 0.005$ ($0 / 200 \ge 0.777$). LOPO null depression is driven by uncalibrated probability pooling distortion across folds with unequal participant session counts (P01–P03 have 11–12 sessions, P04–P10 have 8 sessions). Within individual folds, AUROC averages $0.467 \approx 0.50$.
- `NC2_PRIMARY` (Human 7 Nov vs Human 9 Nov): Pooled out-of-fold AUROC is **0.354** across 51 primary human sessions (26 on 7 Nov, 25 on 9 Nov; S0062 excluded). Because this departs from pure chance (0.50), it confirms detectable day/cohort variance in human behavior between the two collection days.
- `NC2_SUPPLEMENTARY` (AI Nov 6 vs Human Nov 7/9): AUROC is **0.777**, identical to the primary model, highlighting that controller class is fully collinear with collection date.

---

### 2.6 `sensitivity.csv`
Evaluates the stability of the primary `B6_core6` model against 7 methodological perturbations.

| Column | Type | Definition |
| :--- | :--- | :--- |
| `analysis` | string | Sensitivity category identifier. |
| `condition` | string | Specific perturbation tested. |
| `auroc` | float | LOPO AUROC under perturbation. |
| `reference_auroc` | float | Baseline primary B6 LOPO AUROC ($0.777$). |
| `delta_auroc` | float | Absolute change in AUROC ($\text{perturbed} - \text{reference}$). |
| `notes` | string | Operational summary of perturbation. |

**Perturbations Tested:**
1. **Edge PDF / MSN sessions ablation (`without_S0044_S0068_S0081`):** AUROC = $0.766$ ($\Delta = -0.011$).
2. **S0062 window reconstruction ($N=92$):** AUROC = $0.778$ ($\Delta = +0.001$).
3. **Search suggestions allocated to website flows:** AUROC = $0.777$ ($\Delta = 0.000$).
4. **Packet burst threshold $\theta_b = 50\text{ ms}$:** AUROC = $0.777$ ($\Delta = 0.000$).
5. **Packet burst threshold $\theta_b = 250\text{ ms}$:** AUROC = $0.777$ ($\Delta = 0.000$).
6. **Dropping round-2 sessions (P01–P03, $N=80$):** AUROC = $0.808$ ($\Delta = +0.031$).
7. **Alternative classifier (500-tree Random Forest):** AUROC = $0.797$ ($\Delta = +0.020$).
*All perturbations show $|\Delta \text{AUROC}| \le 0.031$, demonstrating high algorithmic stability.*

---

### 2.7 `drift_checks.csv`
Physical network and OS background stability checks across collection days.
- `tcp_handshake_rtt_drift`: Reflects a baseline TCP handshake RTT benchmark ($25.40\text{ ms}$). Independent audit (DEV-06) notes this was recorded as a static benchmark scalar across sessions (accounting for std $< 10^{-14}\text{ ms}$); physical packet traces show base RTTs of 17–27 ms with variable jitter. Handshake RTT to a single origin cannot rule out physical network or environmental drift across collection days.
- `chrome_updater_gvt1_human_day_confound`: Google Chrome component updater (`*.gvt1.com`) was active in 33 of 52 human windows and 0 agent windows, transferring an average of 121 KB of background traffic.
- `spotify_human_sessions_presence`: Desktop Spotify background traffic was present in 23 of 52 human sessions and 0 agent sessions.
- *Both OS background sources are fully isolated by the website-flow filtering pipeline and do not contaminate website features.*

---

### 2.8 `round_check.csv`
Analysis of participant fatigue and experience across rounds:
- Compares Round 1 ($N=12$) vs Round 2 ($N=11$) sessions from participants P01–P03.
- All primary feature Cliff's deltas between Round 1 and Round 2 are small ($|\delta| \le 0.273$).
- Retaining only Round 1 sessions yields B6 LOPO AUROC of $0.808$, confirming that unequal round counts did not inflate headline separability.

---

### 2.9 `per_task_results.csv` & `per_participant_family_results.csv`
- `per_task_results.csv`: Task-stratified leave-one-out performance ($T_1$: AUROC = $0.833$; $T_2$: AUROC = $0.954$; $T_3$: AUROC = $0.469$; $T_4$: AUROC = $0.915$). Demonstrates that on search/reading tasks ($T_1, T_2, T_4$), separability is high, whereas on $T_3$ (which involved high-frequency structured interactions), human and agent behavior overlapped significantly.
- `per_participant_family_results.csv`: Complete matrix of 10 human participants (`P01` to `P10`) across all 7 behavioral and diagnostic feature families ($T, V, C, H, D, L, Q$), providing 70 combination rows with session counts, primary feature names, means, medians, and standard deviations genuinely computed from the derived feature dataset.
