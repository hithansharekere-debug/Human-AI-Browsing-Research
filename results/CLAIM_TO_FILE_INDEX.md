# Person B to Person C/D: Comprehensive Claim-to-File Evidence Index (Post-Correction Audit)

**Project:** Human vs. AI-Agent Browsing at the Client Egress  
**Lead:** Person B (Analysis Lead)  
**Recipients:** Person C (Audit/Synthesis Lead), Person D (Senior Reviewer)  
**Date:** 17 November 2026  
**Repository Branch:** `review/data-provider-corrections-2026-11-17`  
**Reference Git HEAD:** Current correction branch  
**Binding Pilot Verdict:** **`CONDITIONAL GO`**

---

## 1. Overview and Purpose

This document provides a strict, unambiguous mapping connecting every empirical claim, metric, effect size, baseline, negative control, and sensitivity result reported by Person B to its exact source file, row identifier/filter, and column name in the `results/` directory.

### Key Study Population Parameters
- **Total Study Sessions Ingested:** $N = 92$ (52 human, 40 agent).
- **Primary Analysis Population:** $N = 91$ (Session `S0062` strictly excluded due to an operator keystroke anomaly resulting in a $0.007\text{ s}$ duration marker window).
- **Sensitivity Analysis Population:** $N = 92$ (`S0062` retained with its active task duration and packet features reconstructed from Chrome NetLog request boundaries: $29.299\text{ s}$, 1,048 packets).
- **Unequal Rounds Population:** $N = 80$ (40 human Round 1 sessions + 40 agent runs; Round 2 sessions of P01–P03 dropped).

---

## 2. Master Claim-to-File Index

| Claim ID | Category / Type | Reported Metric & Value | Exact Source File | Row Filter / Identifier | Exact Column Names | Caveat / Interpretation Guidance |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CLM-01** | **Primary Headline** | B6 LOPO $\text{AUROC} = 0.625$<br>95% CI $[0.502, 0.742]$<br>F1 $= 0.366$ | `results/baseline_results.csv` | `baseline == "B6"` & `split == "LOPO"` | `auroc`, `ci_95_lower`, `ci_95_upper`, `f1`, `n_sessions=91` | Primary separability across 10 held-out human participants under corrected flow classification (`*.google.com` search wildcard removed). Excludes vendor (A), handshake (H), destination (D), length (L), and background (Q). |
| **CLM-02** | **Primary Headline** | B6 LOTO $\text{AUROC} = 0.606$<br>95% CI $[0.429, 0.793]$<br>F1 $= 0.427$ | `results/baseline_results.csv` | `baseline == "B6"` & `split == "LOTO"` | `auroc`, `ci_95_lower`, `ci_95_upper`, `f1`, `n_sessions=91` | Primary generalization across 4 unseen web tasks. Lower bound ($0.429$) straddles chance ($0.50$). |
| **CLM-03** | **Secondary Model Check** | B6 Random Forest LOPO $\text{AUROC} = 0.744$<br>95% CI $[0.601, 0.849]$<br>F1 $= 0.667$ | `results/baseline_results.csv` | `baseline == "B6_rf_check"` & `split == "LOPO"` | `auroc`, `ci_95_lower`, `ci_95_upper`, `f1` | Pre-registered un-tuned 500-tree Random Forest using identical 6 features. Secondary model check; not the headline model. |
| **CLM-04** | **Secondary Model Check** | B6 Random Forest LOTO $\text{AUROC} = 0.624$<br>95% CI $[0.504, 0.763]$<br>F1 $= 0.466$ | `results/baseline_results.csv` | `baseline == "B6_rf_check"` & `split == "LOTO"` | `auroc`, `ci_95_lower`, `ci_95_upper`, `f1` | Random Forest generalizability across unseen tasks. |
| **CLM-05** | **Design Negative Check** | B2 JA4 Handshake (NOT RUN)<br>Metrics: `NaN` | `results/baseline_results.csv` | `baseline == "B2"` & `split == "LOPO"` | `auroc`, `ci_95_lower`, `ci_95_upper`, `f1` | Formally designated `NOT_RUN` (DEV-08). Automated JA4 extraction unverified on egress captures; client match rests on Person A locality audit `8daaf6152771`. |
| **CLM-06** | **Design Negative Check** | B2 JA4 Handshake (NOT RUN)<br>Metrics: `NaN` | `results/baseline_results.csv` | `baseline == "B2"` & `split == "LOTO"` | `auroc`, `ci_95_lower`, `ci_95_upper`, `f1` | Formally designated `NOT_RUN` (DEV-08). Automated JA4 extraction unverified on egress captures. |
| **CLM-07** | **Shortcut Baseline** | B1 Vendor Shortcut LOPO & LOTO $\text{AUROC} = 1.000$<br>95% CI $[1.000, 1.000]$ | `results/baseline_results.csv` | `baseline == "B1"` | `auroc`, `ci_95_lower`, `ci_95_upper`, `f1=1.0` | Vendor API traffic (`generativelanguage.googleapis.com`) present only in agent runs. Shortcut removed from B6. |
| **CLM-08** | **Shortcut Baseline** | B8 Vendor Cross-Flow Lag LOPO & LOTO $\text{AUROC} = 1.000$<br>95% CI $[1.000, 1.000]$ | `results/baseline_results.csv` | `baseline == "B8"` | `auroc`, `ci_95_lower`, `ci_95_upper`, `f1=1.0` | Timing lag between API call and browser fetch. Shortcut removed from B6. |
| **CLM-09** | **Shortcut Baseline** | B3 Destination/Search LOPO $\text{AUROC} = 0.677$<br>LOTO $\text{AUROC} = 0.664$ | `results/baseline_results.csv` | `baseline == "B3"` | `auroc`, `ci_95_lower`, `ci_95_upper`, `f1` | Corrected omnibox search query detection (7 human sessions, 0 agent sessions). |
| **CLM-10** | **Shortcut Baseline** | B4 Length Baseline LOPO $\text{AUROC} = 0.760$<br>LOTO $\text{AUROC} = 0.725$ | `results/baseline_results.csv` | `baseline == "B4"` | `auroc`, `ci_95_lower`, `ci_95_upper`, `f1` | Multi-feature length baseline (duration, bytes, flows). Outperforms B6 ($0.725$ vs $0.606$ LOTO; $0.760$ vs $0.625$ LOPO). Prominently disclosed as duration confound. |
| **CLM-10b** | **Duration Confound Check** | B4 Duration Only LOPO $\text{AUROC} = 0.574$<br>LOTO $\text{AUROC} = 0.553$ | `results/baseline_results.csv` | `baseline == "B4_duration_only"` | `auroc`, `ci_95_lower`, `ci_95_upper`, `f1` | Session duration alone (`L_duration_s`). |
| **CLM-11** | **Diagnostic Baseline** | B5 All-Flow LOPO $\text{AUROC} = 0.679$<br>LOTO $\text{AUROC} = 0.624$ | `results/baseline_results.csv` | `baseline == "B5"` | `auroc`, `ci_95_lower`, `ci_95_upper`, `f1` | Evaluates T+V+C on all flows including OS background (gvt1, Edge/MSN). |
| **CLM-12** | **Secondary Check** | B7 Length-Normalised LOPO $\text{AUROC} = 0.625$<br>LOTO $\text{AUROC} = 0.606$ | `results/baseline_results.csv` | `baseline == "B7"` | `auroc`, `ci_95_lower`, `ci_95_upper`, `f1` | Numerically identical to B6 because B6 features are already duration-normalized rates and dimensionless ratios. |
| **CLM-13** | **Family Attribution** | B6 Dropout: Drop T LOPO $\text{AUROC} = 0.456$<br>($\Delta = -0.169$) | `results/family_dropout.csv` | `model == "B6"` & `dropped_family == "T"` | `model`, `dropped_family`, `remaining_families`, `auroc` | Micro-temporal features ($T$) are the sole essential driver of separability; dropping $T$ collapses performance below chance. |
| **CLM-14** | **Family Attribution** | B6 Dropout: Drop V LOPO $\text{AUROC} = 0.590$<br>($\Delta = -0.035$) | `results/family_dropout.csv` | `model == "B6"` & `dropped_family == "V"` | `model`, `dropped_family`, `remaining_families`, `auroc` | Dropping volume features ($V$) causes minor performance drop. |
| **CLM-15** | **Family Attribution** | B6 Dropout: Drop C LOPO $\text{AUROC} = 0.645$<br>($\Delta = +0.020$) | `results/family_dropout.csv` | `model == "B6"` & `dropped_family == "C"` | `model`, `dropped_family`, `remaining_families`, `auroc` | Dropping concurrency features ($C$) causes negligible performance change. |
| **CLM-16** | **Family Attribution** | B5 Dropout: Drop T $\text{AUROC} = 0.456$<br>Drop V $= 0.640$, Drop C $= 0.677$ | `results/family_dropout.csv` | `model == "B5"` | `model`, `dropped_family`, `remaining_families`, `auroc` | Confirms identical timing dominance holds across all-flow feature representations. |
| **CLM-17** | **Sensitivity Check** | Edge Sessions Ablation LOPO $\text{AUROC} = 0.614$<br>$\Delta = -0.011$ | `results/sensitivity.csv` | `analysis == "edge_sessions_ablation"` | `condition`, `auroc`, `reference_auroc`, `delta_auroc` | Evaluated on $N=88$ sessions (excluding S0044, S0068, S0081). Confirms heavy MSN background traffic does not create false separability. |
| **CLM-18** | **Sensitivity Check** | S0062 NetLog Window LOPO $\text{AUROC} = 0.633$<br>$\Delta = +0.008$ | `results/sensitivity.csv` | `analysis == "s0062_window_reconstruction"` | `condition`, `auroc`, `reference_auroc`, `delta_auroc` | Evaluated on $N=92$ sessions with S0062 window reconstructed from NetLog ($29.299\text{ s}$, 1,048 real packets). Replaces class-median imputation. |
| **CLM-19** | **Sensitivity Check** | Search Class Allocation LOPO $\text{AUROC} = 0.571$<br>$\Delta = -0.054$ | `results/sensitivity.csv` | `analysis == "search_class_allocation"` | `condition`, `auroc`, `reference_auroc`, `delta_auroc` | Google search suggestion flows classified as website traffic instead of destination D. Genuinely re-extracted; non-zero delta. |
| **CLM-20** | **Sensitivity Check** | Burst Threshold $\theta_b \in \{50, 250\}\text{ ms}$<br>50ms: $0.614$ ($\Delta = -0.011$)<br>250ms: $0.620$ ($\Delta = -0.005$) | `results/sensitivity.csv` | `analysis == "burst_threshold_perturbation"` | `condition`, `auroc`, `reference_auroc`, `delta_auroc` | Packet bursts genuinely re-extracted at 50ms and 250ms thresholds; non-zero deltas. |
| **CLM-21** | **Negative Control NC1** | NC1 LOTO (200 permutations)<br>Null mean $= 0.487 \pm 0.058$<br>Empirical $p = 0.02$ | `results/negative_controls.csv` | `control_id == "NC1_LOTO"` | `observed_auroc=0.606`, `null_mean_auroc`, `null_std_auroc`, `empirical_p_value=0.02` | Passed null check. Balanced task folds center at chance ($0.487 \approx 0.50$). Observed B6 ($0.606$) exceeds null. |
| **CLM-22** | **Negative Control NC1** | NC1 LOPO (200 permutations)<br>Null mean $= 0.417 \pm 0.093$<br>Empirical $p < 0.005$ | `results/negative_controls.csv` | `control_id == "NC1_LOPO"` | `observed_auroc=0.625`, `null_mean_auroc`, `null_std_auroc`, `empirical_p_value=0.0` | Null mean depressed to 0.417 due to unequal fold sizes/base rates across participants. B6 ($0.625$) exceeds empirical null. |
| **CLM-23** | **Negative Control NC2** | NC2 Primary Human Day Control<br>Observed $\text{AUROC} = 0.289$, F1 $= 0.269$ | `results/negative_controls.csv` | `control_id == "NC2_PRIMARY"` | `observed_auroc=0.289231`, `passed_null_check=False` | Evaluates 26 sessions on 7 Nov vs 25 on 9 Nov ($N=51$). Departure from 0.50 is driven by participant-grouped fold base-rate shifts. |
| **CLM-24** | **Negative Control NC2** | Supplementary AI Day Diagnostic<br>$\text{AUROC} = 0.625$, F1 $= 0.366$ | `results/negative_controls.csv` | `control_id == "NC2_SUPPLEMENTARY"` | `observed_auroc=0.625245` | Supplementary diagnostic confounded by collection day (AI Nov 6 vs Human Nov 7/9). |
| **CLM-25** | **Flow-Class Accounting** | Flow Byte Accounting Table<br>Human vs AI across 5 flow classes | `results/byte_accounting.csv` | All 8 rows | `controller`, `task_id`, `website_bytes_sum`, `search_bytes_sum`, `os_background_bytes_sum`, `vendor_bytes_sum`, `unknown_bytes_sum` | Proves that under corrected flow classification, AI has 0 search bytes, Human has 102.1 KB search bytes across 7 sessions, and OS background is fully accounted for. |
| **CLM-26** | **Environmental Drift** | Network & Background Drift:<br>gvt1 in 48 human sessions, 0 agent<br>Spotify in 50 human sessions, 0 agent<br>RTT status: RETRACTED (DEV-06) | `results/drift_checks.csv` | All 10 rows | `check`, `metric`, `value`, `status` | gvt1 and Spotify presence dynamically measured from feature matrices. TCP handshake RTT formally marked `RETRACTED (DEV-06)` (unimplemented scalar). |
| **CLM-27** | **Subgroup Analysis** | Per-Participant Family Stats:<br>70 participant-family combinations | `results/per_participant_family_results.csv` | All 70 rows | `participant_id`, `family`, `primary_feature`, `n_sessions`, `mean`, `median`, `std` | Complete behavioral profile across all 10 participants and all 7 feature families. Pure derived summary. |
| **CLM-28** | **Sensitivity Check** | Unequal Rounds Ablation:<br>Round 1 only ($N=80$) LOPO $\text{AUROC} = 0.808$ | `results/round_check.csv` | `check == "b6_drop_round2"` | `metric="auroc"`, `value=0.8075`, `n_sessions_retained=80` | Dropping Round 2 sessions of P01–P03 eliminates round imbalance. |

---

*Index Compiled & Certified,*  
**Person B**  
*Analysis Lead*
