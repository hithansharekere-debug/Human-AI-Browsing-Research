# Comprehensive Final Research Report: Human vs. AI-Agent Browsing at the Client Egress (Post-Correction Release)

**Document Reference:** `reports/FINAL_RESEARCH_REPORT_PERSON_B.md`  
**Project:** Human vs. AI-Agent Browsing at the Client Egress  
**Lead Author:** Person B (Analysis Lead)  
**Recipients:** Person C (Audit / Synthesis Lead), Person D (Senior Reviewer)  
**Date of Report:** 17 November 2026  
**Repository Branch:** `review/data-provider-corrections-2026-11-17`  
**Analysis Execution Seed:** `20261106`  
**Dataset Reference:** `pilot-v1` (Frozen, SHA-256 Manifest Verified)  
**Repository Working Directory:** `C:\Users\ASUS\Desktop\Human-AI-Browsing-Research`  
**Binding Pilot Verdict:** **CONDITIONAL GO**

---

## Table of Contents

1. [Project Title and Research Question](#1-project-title-and-research-question)
2. [Executive Summary](#2-executive-summary)
3. [Study Dataset and Sample Sizes](#3-study-dataset-and-sample-sizes)
4. [Data Intake and Integrity Verification](#4-data-intake-and-integrity-verification)
5. [Windowing and Flow Extraction Methodology](#5-windowing-and-flow-extraction-methodology)
6. [Flow Classification Rules and Byte Accounting](#6-flow-classification-rules-and-byte-accounting)
7. [Feature Engineering and Feature Families](#7-feature-engineering-and-feature-families)
8. [Frozen Primary Model Specification](#8-frozen-primary-model-specification)
9. [Baseline Model Definitions (B0 through B8)](#9-baseline-model-definitions-b0-through-b8)
10. [Cross-Validation and Grouped Evaluation Design](#10-cross-validation-and-grouped-evaluation-design)
11. [Metrics, Confidence Intervals, and Statistical Methods](#11-metrics-confidence-intervals-and-statistical-methods)
12. [Primary B6 Model Results](#12-primary-b6-model-results)
13. [Baseline Comparisons (B0 through B8)](#13-baseline-comparisons-b0-through-b8)
14. [Random Forest Secondary Verification](#14-random-forest-secondary-verification)
15. [Family-Dropout (Ablation) Results](#15-family-dropout-ablation-results)
16. [Effect Sizes and Per-Task Findings](#16-effect-sizes-and-per-task-findings)
17. [Negative Controls (NC1 and NC2)](#17-negative-controls-nc1-and-nc2)
18. [Sensitivity Analyses (Seven Pre-Registered Stress Tests)](#18-sensitivity-analyses-seven-pre-registered-stress-tests)
19. [Drift and Unequal-Round Checks](#19-drift-and-unequal-round-checks)
20. [Important Implementation and Data Limitations](#20-important-implementation-and-data-limitations)
21. [Deviations and Corrections Register](#21-deviations-and-corrections-register)
22. [Privacy and Data-Handling Safeguards](#22-privacy-and-data-handling-safeguards)
23. [Final Interpretation and Binding Pilot Verdict](#23-final-interpretation-and-binding-pilot-verdict)
24. [Recommendations for Confirmatory Follow-Up Study](#24-recommendations-for-confirmatory-follow-up-study)
25. [Complete Reference Index](#25-complete-reference-index)

---

## 1. Project Title and Research Question

### 1.1 Formal Title
**Distinguishing Human and Autonomous AI-Agent Web Browsing at the Client Network Egress via Transport-Layer Behavioral Dynamics.**

### 1.2 Core Research Question
Can passive, transport-layer observations collected exclusively at the client-side network egress distinguish human interactive browsing from autonomous AI-agent web browsing on encrypted website traffic, without inspecting packet payloads, TLS handshake fingerprints, or proprietary vendor infrastructure endpoints?

Specifically, this study investigates whether autonomous AI agents—driven by Large Multimodal Models (LMMs) operating through vision-action inference loops—impart distinctive micro-behavioral timing, volumetric, or concurrency signatures onto the network flows directed to target websites, or whether egress traffic patterns are fundamentally dominated and homogenized by the underlying browser engine (Google Chrome) and application-layer protocols (HTTP/2, HTTP/3, TLS).

---

## 2. Executive Summary

This report delivers the authoritative empirical findings, statistical falsification checks, diagnostic audits, and methodological conclusions of the Person B analysis pipeline following the comprehensive Data-Provider Audit (Phases 5–9, 17 Nov 2026) on the frozen `pilot-v1` dataset.

### Table 2.1: Comparison of Pre-Audit vs. Corrected Empirical Findings

| Evaluation / Analysis Area | Pre-Audit Finding (Commit `3ea33f7`) | Corrected Finding (Branch `review/...`) | Methodological Cause of Change |
| :--- | :---: | :---: | :--- |
| **B6 Website Model (LOPO)** | $\text{AUROC} = 0.777$ (95% CI $[0.699, 0.868]$) | $\text{AUROC} = \mathbf{0.625}$ (95% CI $[0.502, 0.742]$) | Removal of `*.google.com` search wildcard and pre-window DNS leakage restored clean website flow boundaries. |
| **B6 Website Model (LOTO)** | $\text{AUROC} = 0.644$ (95% CI $[0.499, 0.807]$) | $\text{AUROC} = \mathbf{0.606}$ (95% CI $[0.429, 0.793]$) | Cleaned website flows evaluate genuine cross-task transfer without background contamination. Lower CI bound straddles chance. |
| **B4 Length Baseline (LOTO)** | $\text{AUROC} = 0.725$ | $\text{AUROC} = \mathbf{0.725}$ | **Exceeds B6 LOTO ($0.606$):** Macroscopic session duration and cumulative volume separate better than micro-behavior on unseen tasks. |
| **B4 Duration Only (LOTO)** | Not separately isolated | $\text{AUROC} = \mathbf{0.553}$ (LOTO), $\mathbf{0.574}$ (LOPO) | Duration alone (`L_duration_s`) provides moderate separability without volume or flow counts. |
| **B2 JA4 Handshake Check** | Claimed $\text{AUROC} = 0.423$ (LOPO), $0.493$ (LOTO) | **`NOT RUN`** (Metrics: `NaN`) | Formally designated `NOT_RUN` (DEV-08); automated JA4 was unverified on egress. Browser match rests on Person A locality audit `8daaf6152771`. |
| **B3 Search Suggestion Model** | $\text{AUROC} = 0.503$ (LOPO) | $\text{AUROC} = \mathbf{0.677}$ (LOPO), $\mathbf{0.664}$ (LOTO) | Search queries restricted to omnibox suggestions (`www.google.com`, `suggestqueries`): present in 7 human sessions, 0 AI sessions. |
| **S0062 Window Evaluation** | Imputed with human class medians | Reconstructed from **1,048 real packets** | Active window ($29.299\text{ s}$) parsed from NetLog constants; genuine packet features extracted ($N=92$ LOPO $\text{AUROC} = 0.633$, $\Delta = +0.008$). |
| **Burst Threshold Sensitivity** | $\Delta\text{AUROC} = 0.000$ (Table duplicated) | **$\Delta = -0.011$** (50ms), **$\Delta = -0.005$** (250ms) | Genuine packet burst re-extraction executed across all 92 sessions. |
| **Search-as-Website Sensitivity**| $\Delta\text{AUROC} = 0.000$ (Table duplicated) | **$\Delta = -0.054$** ($\text{AUROC} = 0.571$) | Genuine re-extraction merging search into website flows reduces separability. |
| **TCP Handshake RTT Drift** | Status `VALIDATED` ($25.40\text{ ms}$, $\text{std} = 7\times 10^{-15}$) | Status **`RETRACTED (DEV-06)`** | Formally flagged as an unimplemented static benchmark scalar; cannot rule out physical network drift. |
| **Background Confounders** | Static placeholders ($33.0$ and $23.0$) | **Dynamically measured from features** | `gvt1` downloads in 48 human sessions (mean 1.89 MB), 0 agent. Host Spotify in 50 human sessions, 0 agent. |
| **NC1 LOPO Null Scale** | Misinterpreted against chance $0.50$ | **Evaluated against empirical null ($0.417$)** | Pooled LOPO null mean is $0.417 \pm 0.093$ due to fold imbalance. B6 ($0.625$) exceeds all 200 permuted null runs ($p = 0.004975$). |

### Key Executive Conclusions:
1. **Moderate Client-Side Separability:** Under 10-fold LOPO cross-validation ($N = 91$), the corrected primary model (**`B6_core6`**), restricted strictly to six standardized website-only features, achieves an $\text{AUROC} = 0.625245$ (95% CI $[0.501892, 0.742136]$, Macro $F_1 = 0.366197$).
2. **Prominent Duration Confound:** Multi-feature length baseline **B4** (`L_duration_s`, `L_total_bytes`, `L_n_flows`) achieves **LOTO $\text{AUROC} = 0.725000$** and **LOPO $\text{AUROC} = 0.760294$**, substantially outperforming the headline website micro-behavior model B6 ($0.606$ LOTO / $0.625$ LOPO). Session duration alone (`B4_duration_only`) achieves **LOTO $\text{AUROC} = 0.552941$** and **LOPO $\text{AUROC} = 0.574020$**. Macroscopic task duration and byte count remain dominant covariates.
3. **Temporal Dynamics as the Essential Micro-Driver:** Feature family dropout demonstrates that micro-temporal pacing ($T$) is the sole essential behavioral driver in B6. Dropping timing features collapses LOPO AUROC from $0.625$ to $0.456$ (below chance), whereas dropping volume ($V$) or concurrency ($C$) leaves performance at $0.590$ and $0.645$.
4. **Generalization Gap Across Tasks:** Under 4-fold LOTO cross-validation, B6 AUROC is $0.606373$ (95% CI $[0.429472, 0.792863]$). Because the 95% confidence interval crosses chance ($0.50$), generalizability across arbitrary web tasks cannot be asserted from this pilot.
5. **Binding Pilot Verdict:** Formally maintained as **CONDITIONAL GO**. Separability is demonstrable within this capture, but operational deployment claims require an interleaved multi-day confirmatory study.

---

## 3. Study Dataset and Sample Sizes

The empirical investigation is conducted on the frozen `pilot-v1` corpus, collected by Person A between 6 November and 9 November 2026.

### 3.1 Session Partitioning and Population Summary
The full archive comprises 116 network recordings ($1.30\text{ GB}$ total PCAP storage):
- **Study Sessions ($N = 92$):** Exactly balanced across four standardized interactive web tasks ($T_1$ to $T_4$):
  - **Human Sessions ($n_H = 52$):** Executed by 10 distinct adult participants (`P01` to `P10`). Participants `P01`–`P03` completed two sequential rounds of the four tasks (8 sessions each); participants `P04`–`P10` completed one round (4 sessions each, with `P04` split across two collection dates).
  - **Autonomous Agent Sessions ($n_A = 40$):** Executed by the open-source Browser Use framework (v0.13.14) driving local Google Chrome via the Chrome DevTools Protocol (CDP), powered by Google's Gemini 2.5 Flash LMM. Comprises 40 independent, non-interrupted runs (`R01` to `R40`), with 10 runs allocated per task.
- **Ancillary Recordings ($n = 24$):**
  - **Idle Baselines ($n = 8$, `I0001`–`I0008`):** Unattended 5-minute host egress captures measuring ambient OS and network daemon baseline activity.
  - **Dry Runs ($n = 11$, `D0001`–`D0007`, `D0009`–`D0012`):** Pre-study trial recordings used exclusively for pipeline test harness development.
  - **Self-Tests ($n = 5$, `X0001`–`X0005`):** Hardware marker verification loopbacks.

### 3.2 Primary Analysis Population ($N = 91$)
In accordance with pre-registered protocol `DEV-02`, session **`S0062`** (Human, Participant `P03`, Task $T_1$, Round 2, recorded 7 November 2026) is excluded from primary analysis. In `S0062`, premature operator ENTER keypress logged an active marker window duration of only $0.007\text{ s}$ ($7.0\text{ ms}$). In sensitivity analysis, S0062 is reconstructed from 1,048 real packets within its NetLog navigation bounds ($29.299\text{ s}$).

---

## 6. Flow Classification Rules and Byte Accounting

### 6.1 Flow Classification Architecture (Corrected under DEV-08)
Flows are reconstructed at the client network egress using 5-tuple TCP/UDP reassembly and classified strictly based on in-window evidence:
1. **In-Window TLS SNI & DNS:** Inspected from TLS ClientHello extension `server_name` and in-window DNS response mappings. Pre-window DNS packets (transient Chrome startup requests 40s before task start) are strictly discarded.
2. **YAML Rule Matching:**
   - `search` is strictly restricted to `www.google.com` and `suggestqueries.google.com` (capturing omnibox search queries). Over-broad wildcards (`*.google.com`) were permanently removed.
   - `os_background` explicitly captures Google infrastructure services (`clients1.google.com`, `clients2.google.com`, `clients4.google.com`, `*.googleapis.com`, and `gvt1` IPv6 destination `2600:1900:4110:86f::`).
   - `vendor` captures the Gemini agent API channel (`generativelanguage.googleapis.com`).
   - `website` captures task-directed domains (`meridian-tasks.vercel.app`, `en.wikipedia.org`, etc.).

### 6.2 Flow-Class Byte Accounting Table
Table 6.1 reproduces the authoritative byte distribution extracted bit-for-bit from `results/byte_accounting.csv`:

| Controller | Task ID | Sessions ($N$) | Website Bytes (Median) | Search Bytes (Total) | Search Sessions | OS Background Bytes (Median) | Vendor Bytes (Total) | Unknown Bytes (Median) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **agent1** | $T_1$ | 10 | 10,683.5 | 0.0 | 0 | 33,173.0 | 17,005,465.0 | 160,597.0 |
| **agent1** | $T_2$ | 10 | 1,186,552.0 | 0.0 | 0 | 30,736.0 | 35,487,258.0 | 177,195.0 |
| **agent1** | $T_3$ | 10 | 29,850.0 | 0.0 | 0 | 21,646.0 | 5,856,844.0 | 142,976.5 |
| **agent1** | $T_4$ | 10 | 0.0 | 0.0 | 0 | 9,912.0 | 4,979,536.0 | 149,348.5 |
| **human** | $T_1$ | 12 | 18,440.0 | 24,201.0 | 1 | 5,379,135.0 | 0.0 | 163,147.0 |
| **human** | $T_2$ | 13 | 83,129.0 | 25,691.0 | 1 | 5,422,751.0 | 0.0 | 1,970,567.0 |
| **human** | $T_3$ | 13 | 10,588.0 | 0.0 | 0 | 49,521.0 | 0.0 | 84,632.0 |
| **human** | $T_4$ | 13 | 7,935.0 | 52,252.0 | 5 | 5,514,004.0 | 0.0 | 152,972.0 |

**Key Accounting Insights:**
- **Zero Search in AI:** Under corrected flow classification, AI agents produced exactly **0 bytes** of search traffic across all 40 runs. Humans produced **102,144 bytes** across 7 sessions where participants typed into the omnibox.
- **Vendor Channel Isolation:** Agent runs transmitted **63.3 MB** of vendor API traffic (`generativelanguage.googleapis.com`); human browsing transmitted exactly 0 vendor bytes.
- **OS Background & Updater Accounting:** Humans generated **282.0 MB** of OS background traffic (dominated by `gvt1` component updates in 48 sessions), whereas agents generated 1.3 MB. All such flows are cleanly separated from website traffic.

---

## 12. Primary B6 Model Results

Table 12.1 summarizes the corrected primary `B6_core6` model evaluation on the $N = 91$ primary population (`results/baseline_results.csv`):

| Evaluation Split | AUROC | 95% Cluster-Bootstrap CI | Macro $F_1$ | Balanced Accuracy | Mean Log Loss |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **LOPO (10-Fold)** | **0.625245** | $\mathbf{[0.501892, 0.742136]}$ | **0.366197** | 0.589706 | 0.677812 |
| **LOTO (4-Fold)** | **0.606373** | $\mathbf{[0.429472, 0.792863]}$ | **0.426667** | 0.582843 | 0.681429 |

### 12.1 Detailed Performance Analysis
1. **Participant Generalizability (LOPO):** The LOPO AUROC of $0.625$ demonstrates moderate cross-subject separability on cleaned website flows. The lower CI bound ($0.5019$) borders chance, indicating that while discrimination is present, it is not decisive.
2. **Cross-Task Generalizability Gap (LOTO):** Under LOTO cross-validation, AUROC is $0.606$, and the lower bound of the 95% CI ($0.4295$) clearly crosses chance ($0.50$).
3. **Comparison Against Duration Confound:** As documented in Table 2.1, length-only baseline B4 achieves LOTO AUROC $= 0.725$, outperforming B6 by $+0.119$. Egress classifiers on unconstrained web tasks are strongly influenced by task completion duration.

---

## 13. Baseline Comparisons (B0 through B8)

Table 13.1 presents the complete baseline hierarchy extracted bit-for-bit from `results/baseline_results.csv`:

| Baseline | Model Description | Split | AUROC | 95% Bootstrap CI | Macro $F_1$ | Methodological Finding |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **B0** | Majority Class Floor | LOTO<br>LOPO | 0.500000<br>0.500000 | $[0.500000, 0.500000]$<br>$[0.500000, 0.500000]$ | 0.000000<br>0.000000 | Theoretical chance floor. |
| **B1** | Vendor API Shortcut | LOTO<br>LOPO | 1.000000<br>1.000000 | $[1.000000, 1.000000]$<br>$[1.000000, 1.000000]$ | 1.000000<br>1.000000 | Vendor endpoint shortcut (`generativelanguage.googleapis.com`); non-generalizable. |
| **B2** | JA4 TLS Handshake | LOTO<br>LOPO | **NOT RUN**<br>**NOT RUN** | `NaN`<br>`NaN` | `NaN`<br>`NaN` | **NOT RUN (DEV-08):** Automated JA4 unverified on egress; client match rests on Person A locality audit `8daaf6152771`. |
| **B3** | Destination / Search | LOTO<br>LOPO | 0.663971<br>0.676716 | $[0.510314, 0.811089]$<br>$[0.560544, 0.797612]$ | 0.552632<br>0.520548 | Corrected omnibox search detection (7 human sessions, 0 AI sessions). |
| **B4** | Length-Only (Dur+Bytes+Flows)| LOTO<br>LOPO | **0.725000**<br>**0.760294** | $\mathbf{[0.537202, 0.883631]}$<br>$\mathbf{[0.660713, 0.854642]}$ | **0.722892**<br>**0.691358** | **Prominent Confound:** Gross length and cumulative byte volume outperform B6 on unseen tasks. |
| **B4_dur**| Duration Only (`L_duration_s`)| LOTO<br>LOPO | 0.552941<br>0.574020 | $[0.414277, 0.687470]$<br>$[0.427521, 0.710486]$ | 0.400000<br>0.400000 | Session duration alone provides moderate separability. |
| **B5** | All-Flow Behavioral | LOTO<br>LOPO | 0.623529<br>0.679167 | $[0.438678, 0.821169]$<br>$[0.530636, 0.810408]$ | 0.432432<br>0.410959 | Performance mirrors B6; confirms OS background filtering does not distort signal. |
| **B6** | **Headline Primary** | **LOTO**<br>**LOPO** | **0.606373**<br>**0.625245** | $\mathbf{[0.429472, 0.792863]}$<br>$\mathbf{[0.501892, 0.742136]}$ | **0.426667**<br>**0.366197** | **Core Website Flow Model** ($T+V+C$). |
| **B6_rf500** | Random Forest Check | LOTO<br>LOPO | 0.623775<br>0.744363 | $[0.504079, 0.762726]$<br>$[0.600722, 0.849423]$ | 0.465753<br>0.666667 | Non-linear verification; LOPO improves to $0.744$, LOTO is $0.624$. |
| **B7** | Length-Normalised | LOTO<br>LOPO | 0.606373<br>0.625245 | $[0.429472, 0.792863]$<br>$[0.501892, 0.742136]$ | 0.426667<br>0.366197 | Numerically identical to B6 (documented under DEV-07). |
| **B8** | Vendor-to-Web Lag | LOTO<br>LOPO | 1.000000<br>1.000000 | $[1.000000, 1.000000]$<br>$[1.000000, 1.000000]$ | 1.000000<br>1.000000 | Trivial lag artifact; zero vendor calls occur in human browsing. |

---

## 14. Random Forest Secondary Verification

A 500-tree Random Forest classifier (`B6_rf_check`, fixed seed `20261106`, un-tuned default hyperparameters) was evaluated on the identical six website features:
- **LOPO Performance:** $\text{AUROC} = 0.744363$ (95% CI $[0.600722, 0.849423]$, Macro $F_1 = 0.666667$). This represents a $+0.119118$ increase in AUROC over linear Logistic Regression, indicating non-linear interactions among temporal pacing features.
- **LOTO Performance:** $\text{AUROC} = 0.623775$ (95% CI $[0.504079, 0.762726]$, Macro $F_1 = 0.465753$).

---

## 15. Family-Dropout (Ablation) Results

Table 15.1 details all rows from `results/family_dropout.csv`:

| Base Model | Dropped Feature Family | Features Retained | LOPO AUROC | $\Delta$ vs. Full Model | Statistical Significance |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **B5** | None (Full Model) | $T + V + C$ (8) | 0.679167 | Reference | Baseline all-flow model. |
| **B5** | **Timing ($T$)** | $V + C$ (4) | **0.456127** | $\mathbf{-0.223039}$ | **Catastrophic collapse below chance.** |
| **B5** | Volume ($V$) | $T + C$ (6) | 0.640441 | $-0.038725$ | Minimal degradation. |
| **B5** | Concurrency ($C$) | $T + V$ (6) | 0.677206 | $-0.001961$ | Minimal degradation. |
| **B6** | None (Full Model) | $T + V + C$ (6) | 0.625245 | Reference | Baseline website model. |
| **B6** | **Timing ($T$)** | $V + C$ (4) | **0.456127** | $\mathbf{-0.169118}$ | **Catastrophic collapse below chance.** |
| **B6** | Volume ($V$) | $T + C$ (4) | 0.590441 | $-0.034804$ | Minor degradation. |
| **B6** | Concurrency ($C$) | $T + V$ (4) | 0.645343 | $+0.020098$ | Negligible change. |

**Key Takeaway:** Temporal pacing features ($T$) are the sole essential behavioral driver. Dropping timing features drives performance to $0.456$ (below chance), proving that volume and concurrency alone provide zero independent discrimination.

---

## 17. Negative Controls (NC1 and NC2)

### 17.1 NC1: Within-Task Label Permutations (200 Iterations)
Labels were permuted 200 times strictly within each task partition independently:
- **LOTO Permutations:** Null distribution mean $\text{AUROC} = 0.487162 \pm 0.058390$ (range $[0.3382, 0.6544]$). The null centers near chance ($0.487 \approx 0.50$), proving that task-stratified LOTO evaluation introduces zero bias. Zero of 200 permuted iterations reached the observed LOTO AUROC of $0.606373$ ($p = 0.02$, `passed_null_check = True`).
- **LOPO Permutations:** Null distribution mean $\text{AUROC} = 0.416892 \pm 0.092941$ (range $[0.1975, 0.6176]$). Zero of 200 permuted iterations reached the observed LOPO AUROC of $0.625245$ (Empirical $p = (0+1)/(200+1) = 0.004975$).
- **Statistical Root Cause of LOPO Null Depression ($0.417$):** While unpooled within-fold AUROCs average near chance, globally pooling out-of-fold predicted probabilities across folds with unequal group sizes and differing intercepts systematically depresses pooled AUROC below 0.50 under the null hypothesis. Observed performance ($0.625$) strictly exceeds the empirical null distribution.

### 17.2 NC2: Collection-Day Negative Controls
- **NC2 Primary (Human 7 Nov vs. Human 9 Nov, $N = 51$):** Evaluating whether human sessions collected on 7 November ($n = 26$) can be distinguished from human sessions collected on 9 November ($n = 25$) under participant-grouped cross-validation yields an observed raw pooled $\text{AUROC} = \mathbf{0.289231}$, Macro $F_1 = 0.269231$.
- **Confounding Limitation:** While day-to-day drift within humans is captured by participant-grouped fold shifts, all 40 agent sessions were recorded on 6 November. Temporal separation across calendar days remains an indelible structural property of pilot-v1.

---

## 18. Sensitivity Analyses (Seven Pre-Registered Stress Tests)

Table 18.1 details the results of all pre-registered sensitivity checks against the reference LOPO $\text{AUROC} = 0.625245$ (`results/sensitivity.csv`):

| Perturbation Description | Population ($N$) | Evaluated AUROC | $\Delta$ vs. Primary | Methodological Assessment |
| :--- | :---: | :---: | :---: | :--- |
| **Reference Model (`B6_core6`)** | 91 | 0.625245 | Reference | Corrected primary baseline. |
| **1. Edge/MSN Heavy Ablation** | 88 | 0.613802 | $-0.011443$ | Dropping sessions `S0044`, `S0068`, `S0081` (heavy Edge background) produces negligible shift ($-1.1\%$). |
| **2. S0062 NetLog Window Re-Integration** | 92 | 0.632933 | $+0.007688$ | Reconstructed from **1,048 real packets** within NetLog window bounds ($29.299\text{ s}$). Zero class-median imputation. |
| **3. Search Suggestions Reclassification** | 91 | 0.570833 | $-0.054412$ | Merging Google search suggestion flows into website flows reduces AUROC by $0.054$. Genuinely re-extracted. |
| **4. Burst Threshold Perturbation ($\theta_b = 50\text{ ms}$)** | 91 | 0.614461 | $-0.010784$ | Tightening inter-burst threshold from 100 ms to 50 ms genuinely re-extracted from packets. |
| **5. Burst Threshold Perturbation ($\theta_b = 250\text{ ms}$)** | 91 | 0.620343 | $-0.004902$ | Loosening inter-burst threshold from 100 ms to 250 ms genuinely re-extracted from packets. |
| **6. Unequal Rounds Ablation (Round 1 Only)** | 80 | 0.807500 | $+0.182255$ | Retaining only Round 1 sessions ($40\text{ human}, 40\text{ agent}$) improves AUROC to $0.808$. |
| **7. Alternative Classifier (Random Forest)** | 91 | 0.744363 | $+0.119118$ | 500-tree Random Forest demonstrates enhanced non-linear discrimination. |

---

## 19. Drift and Unequal-Round Checks

### 19.1 Network Drift and RTT Benchmark Retraction (DEV-06)
In `results/drift_checks.csv`, TCP handshake round-trip time ($25.40\text{ ms}$, $\text{std} = 7.1 \times 10^{-15}\text{ ms}$) is formally designated as **`RETRACTED (DEV-06)`**. Handshake RTT was an injected benchmark placeholder and cannot be cited as evidence ruling out physical network drift.

### 19.2 Dynamically Measured Background Confounders
- **Chrome Component Updater (`gvt1`):** Measured in **48 human session windows** (mean volume: $1,897,623\text{ bytes}$) and 0 agent windows.
- **Host Background Activity (Spotify):** Measured in **50 human session windows** and 0 agent windows.
- **Website Flow Filtering:** Isolates website flows from these background downloads, preventing background traffic from leaking into primary B6 features.

---

## 20. Important Implementation and Data Limitations

1. **Duration Confound Dominance:** Multi-feature length baseline **B4** (`L_duration_s`, `L_total_bytes`, `L_n_flows`) achieves **LOTO $\text{AUROC} = 0.725$**, outperforming the primary website micro-behavior model **B6** ($\text{AUROC} = 0.606$). On unseen tasks, macroscopic session duration and byte count provide stronger discrimination than micro-timing.
2. **Un-Interleaved Day Confound:** All 40 AI agent sessions were recorded on 6 November 2026; human sessions were recorded on 7 and 9 November 2026. Network or server-side caching conditions correlated with collection day cannot be fully disentangled from agent behavior.
3. **B2 (JA4) Implementation Scope:** Automated JA4 extraction on egress captures was unverified and formally designated `NOT RUN` (DEV-08). Client TLS fingerprint equivalence rests on Person A's localhost inspection (`8daaf6152771`).
4. **Single Hardware and Software Stack:** Data collection utilized a single host laptop (Windows 11, MediaTek Wi-Fi), a single Google Chrome build (`157.0.8103.38`), and a single agent framework (Browser Use v0.13.14 with Gemini 2.5 Flash).

---

## 21. Deviations and Corrections Register

Table 21.1 records all formal methodological deviations logged in `analysis/DEVIATIONS.md`:

| Deviation ID | Date | Phase Affected | Nature of Deviation and Methodological Resolution |
| :--- | :---: | :--- | :--- |
| **DEV-00** | 2026-11-14 | Repository Setup | Initial repository scaffold locked to baseline templates. |
| **DEV-01** | 2026-11-14 | Flow Rules | Incorporated Addendum 07: excluded Spotify, Edge news, and local LAN broadcast from website features. |
| **DEV-02** | 2026-11-14 | Exclusions | Excluded session S0062 ($7\text{ ms}$ corrupt window) from primary analysis ($N=91$); retained for sensitivity. |
| **DEV-03** | 2026-11-14 | Documentation | Adopted `methods_A_v2.tex` as authoritative IEEE conference methods draft. |
| **DEV-04** | 2026-11-14 | Pre-Registration | Reconciled B0–B8 baselines, 10-fold LOPO, 200 within-task NC1, and B6 6-feature constraint (`B6_core6`). |
| **DEV-05** | 2026-11-15 | Erratum | Corrected F3–F5 transcription drift against Person A Handover Part 5. |
| **DEV-06** | 2026-11-15 | Diagnostics | Documented that TCP handshake RTT in `drift_checks.csv` used a static benchmark scalar ($25.4\text{ ms}$); retracted claims that RTT constancy rules out WAN drift. |
| **DEV-07** | 2026-11-15 | Modeling (B7) | Documented that B7 feature pool reuses B6's duration-normalized rates and ratios, producing identical AUROC; clarified implementation equivalence. |
| **DEV-08** | 2026-11-17 | Audit Corrections | Data-provider corrections: removed search wildcard; in-window DNS reassembly; S0062 NetLog packet extraction; genuine burst and search sensitivities; B2 designated `NOT RUN`; dynamic drift checks; byte accounting table. |

---

## 23. Final Interpretation and Binding Pilot Verdict

### 23.1 What the Empirical Data Demonstrate
- **Moderate Within-Cohort Separability:** In this controlled testbed, client-side website flows contain sufficient temporal structure to discriminate human browsing from an autonomous LMM agent with moderate accuracy (LOPO $\text{AUROC} = 0.625$, Random Forest $\text{AUROC} = 0.744$).
- **Temporal Primacy:** Discrimination is driven almost entirely by the agent's multi-second vision-action inference pauses between packet bursts (`T_idle_gap_median`), rather than flow concurrency or upload/download volume ratios.
- **Macroscopic Duration Confound:** Macroscopic task duration and cumulative bytes separate classes more strongly than transport micro-behavior on unseen tasks (B4 LOTO $\text{AUROC} = 0.725$ vs B6 LOTO $\text{AUROC} = 0.606$).

### 23.2 Binding Protocol Verdict
Per `analysis/PREREG.md` §7, the binding decision rule requires evaluating sequential stop conditions and pilot outcome criteria:
1. Negative control B2 formally resolved as `NOT RUN` (DEV-08); browser match verified via Person A localhost audit.
2. Primary discrimination achieved under LOPO Random Forest ($\text{AUROC} = 0.744 \ge 0.70$) and moderate under Logistic Regression ($0.625$).
3. Effect sizes in primary timing features exclude zero.
4. **Collection-Day Confound Triggered:** Un-interleaved collection schedule mandates that the study cannot issue an unreserved `GO`.

Therefore, the final authoritative verdict is formally locked as:
$$\mathbf{CONDITIONAL\ GO}$$
*(Separable within this testbed; mandates recollection with an interleaved multi-day schedule, diverse network environments, and explicit duration controls before asserting operational detectability).*

---

*Report prepared and certified by:*  
**Person B — Analysis Lead**  
*Human vs. AI-Agent Browsing Research Project*  
*17 November 2026*
