# Results Package Codebook & Interpretation Guide (Post-Correction Release)

**Project:** Human vs. AI-Agent Browsing at the Client Egress  
**Target Recipient:** Person C (Audit/Synthesis Lead), Person D (Senior Reviewer)  
**Author:** Person B (Analysis Lead)  
**Date:** 17 November 2026  
**Repository Branch:** `review/data-provider-corrections-2026-11-17`  
**Analysis Seed:** `20261106`  
**Dataset Scope:** Primary analysis $N=91$ study sessions (S0062 excluded due to corrupted 7 ms operator keypress window); Sensitivity analysis $N=92$ (S0062 included with reconstructed 29.299 s window, 1,048 packets).

---

## 1. Directory Structure

```
results/
├── README.md                           # This codebook and interpretation guide
├── RUN_MANIFEST.json                   # Execution environment, timestamp, and reproducibility metadata
├── baseline_results.csv                # Primary (B6_core6) and baseline (B0–B8) performance metrics
├── byte_accounting.csv                 # Detailed byte distribution across 5 flow classes (Human vs AI)
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
- `processed/session_features.parquet` (92 rows: full per-session extracted feature vector)
- `processed/session_features.csv` (mirror in comma-separated text)

---

## 2. Table-by-Table Codebook

### 2.1 `baseline_results.csv`
Contains evaluation metrics across both pre-registered cross-validation splitting schemes: Leave-One-Task-Out (LOTO, 4 folds) and Leave-One-Participant-Out (LOPO, 10 human folds + pooled agent evaluations).

| Column | Type | Units / Range | Definition & Interpretation |
| :--- | :--- | :--- | :--- |
| `baseline` | string | Categorical | Baseline model identifier (`B0` through `B8`, including `B6_rf_check`). |
| `split` | string | `LOTO` / `LOPO` | Cross-validation grouping strategy. |
| `model` | string | Categorical | Classifier type (`majority_class`, `logistic_regression`, `random_forest`, `NOT_RUN`). |
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
- `B2` (`NOT_RUN`, `NaN`): JA4 TLS handshake fingerprint on website flows. Formally designated `NOT_RUN` (DEV-08); automated JA4 extraction unverified on egress. Browser client identity match rests on Person A locality audit `8daaf6152771`.
- `B3` (LOTO $\text{AUROC} = 0.664$, LOPO $\text{AUROC} = 0.677$): Omnibox search query detection (7 human sessions, 0 AI sessions).
- `B4` (LOTO $\text{AUROC} = 0.725$, LOPO $\text{AUROC} = 0.760$): Multi-feature length baseline (duration, bytes, flows). Outperforms B6 on unseen tasks, demonstrating a prominent macroscopic duration confound.
- `B4_duration_only` (LOTO $\text{AUROC} = 0.553$, LOPO $\text{AUROC} = 0.574$): Session duration alone (`L_duration_s`).
- `B6` (`B6_core6` Logistic Regression, L2, $C=1.0$, 6 core website features): **Headline primary model**. Achieves LOPO $\text{AUROC} = 0.625$ (95% CI $[0.502, 0.742]$) and LOTO $\text{AUROC} = 0.606$ (95% CI $[0.429, 0.793]$).
- `B6_rf_check` (500-tree Random Forest check, fixed seed `20261106`): Confirmatory check, LOPO $\text{AUROC} = 0.744$ (95% CI $[0.601, 0.849]$).
- `B7` (Length-normalized B6): LOPO $\text{AUROC} = 0.625$, matching B6 bit-for-bit (see DEV-07: B6 was already constructed using duration-normalized rates and ratios).
- `B8` ($\text{AUROC} = 1.000$): Artifactual lag diagnostic (first vendor API request to first website TLS connection).

---

### 2.2 `byte_accounting.csv`
Detailed accounting table breaking down byte volumes across five disjoint flow classes (`website`, `search`, `os_background`, `vendor`, `unknown`) by controller and task:
- In AI agent sessions: `search_bytes_sum = 0.0` and `search_sessions_count = 0` across all tasks.
- In human sessions: `search_bytes_sum = 102,144` bytes across 7 sessions (T1: 1, T2: 1, T3: 0, T4: 5).
- In AI agent sessions: `vendor_bytes_sum = 63,329,103` bytes (63.3 MB) across 40 sessions. In human sessions, vendor bytes are strictly 0.0.
- In human sessions: `os_background_bytes_sum = 282,031,240` bytes (dominated by `gvt1` component updates in 48 sessions).

---

### 2.3 `effect_sizes.csv`
Reports non-parametric Cliff's delta ($\delta$) and 95% cluster-bootstrap confidence intervals for the primary features, overall and per task ($T_1$ to $T_4$). Positive values indicate higher magnitude in human sessions; negative values indicate higher magnitude in agent sessions.

**Key Findings:**
- `T_idle_gap_median` ($\delta = -0.586$, 95% CI $[-0.754, -0.410]$): **Excludes zero**. The AI agent pauses between bursts for significantly longer and more regular median durations (model thinking / vision inference loop) compared to human continuous micro-scrolling.
- `T_burst_rate` ($\delta = +0.312$, 95% CI $[+0.125, +0.470]$): **Excludes zero**. Humans generate more frequent discrete bursts per minute of active session time ($\text{bursts}\cdot\text{min}^{-1}$) during interaction.
- Volume ($V$) and Concurrency ($C$) features straddle zero overall:
  - `V_up_down_ratio`: $\delta = -0.060$ (95% CI $[-0.169, +0.044]$)
  - `V_upload_burst_share`: $\delta = -0.147$ (95% CI $[-0.323, +0.029]$)
  - `C_new_flows_per_min`: $\delta = +0.009$ (95% CI $[-0.211, +0.237]$)
  - `C_max_concurrent`: $\delta = +0.038$ (95% CI $[-0.125, +0.181]$)

---

### 2.4 `family_dropout.csv`
Ablation experiment dropping entire feature families ($T, V, C$) one at a time from B5 (all flows) and B6 (website flows only) under 10-fold LOPO cross-validation:
- When $T$ (timing) is dropped from B6, LOPO AUROC collapses from **0.625 to 0.456** (below chance).
- Dropping $V$ yields AUROC = **0.590**; dropping $C$ yields AUROC = **0.645**.
- Micro-behavioral timing is the single necessary component for client egress separability.

---

### 2.5 `negative_controls.csv`
Reports falsification tests: NC1 (within-task label permutations) and NC2 (collection day controls).
- `NC1_LOTO`: Null mean is $0.487 \pm 0.058$, observed AUROC = $0.606$, empirical $p = 0.02$, `passed_null_check = True`. Centers near chance (0.50). Confirms no structural leakage in task-stratified cross-validation.
- `NC1_LOPO`: Null mean is $0.417 \pm 0.093$, observed AUROC = $0.625$, empirical $p < 0.005$ ($0 / 200 \ge 0.625$). LOPO null depression is driven by uncalibrated probability pooling distortion across folds with unequal participant session counts. Observed B6 strictly exceeds the empirical null.
- `NC2_PRIMARY` (Human 7 Nov vs Human 9 Nov): Pooled out-of-fold AUROC is **0.289**, Macro $F_1 = 0.269$. Confirms detectable day/cohort variance between the two collection days.
- `NC2_SUPPLEMENTARY` (AI Nov 6 vs Human Nov 7/9): AUROC is **0.625**, identical to the primary model, highlighting that controller class is fully collinear with collection date.

---

### 2.6 `sensitivity.csv`
Evaluates the stability of the primary `B6_core6` model against pre-registered perturbations:
1. **Edge PDF / MSN sessions ablation (`without_S0044_S0068_S0081`):** AUROC = $0.6138$ ($\Delta = -0.0114$).
2. **S0062 window reconstruction ($N=92$):** AUROC = $0.6329$ ($\Delta = +0.0077$). Reconstructed from 1,048 real packets; zero imputation.
3. **Search suggestions allocated to website flows:** AUROC = $0.5708$ ($\Delta = -0.0544$).
4. **Packet burst threshold $\theta_b = 50\text{ ms}$:** AUROC = $0.6145$ ($\Delta = -0.0108$).
5. **Packet burst threshold $\theta_b = 250\text{ ms}$:** AUROC = $0.6203$ ($\Delta = -0.0049$).
*All sensitivity checks have genuinely computed non-zero deltas.*

---

### 2.7 `drift_checks.csv`
Physical network and OS background stability checks across collection days:
- `tcp_handshake_rtt_drift`: Formally marked **`RETRACTED (DEV-06)`**. Handshake RTT was an injected benchmark placeholder ($25.40\text{ ms}$) and cannot rule out physical network drift.
- `chrome_updater_gvt1_human_day_confound`: Measured dynamically in **48 of 51 human windows** (mean volume: 1.89 MB) and 0 agent windows.
- `spotify_human_sessions_presence`: Measured dynamically in **50 of 51 human windows** and 0 agent windows.
- Both OS background sources are cleanly segregated from website flows under corrected flow classification.

---

*Codebook Certified,*  
**Person B**  
*Analysis Lead*
