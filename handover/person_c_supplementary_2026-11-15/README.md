# Supplementary Person B → Person C/D Results Handover Package (Post-Correction Release)

**Project:** Human vs. AI-Agent Browsing at the Client Egress  
**Author:** Person B (Analysis Lead)  
**Recipients:** Person C (Audit/Synthesis Lead), Person D (Senior Reviewer)  
**Date:** 17 November 2026  
**Repository Branch:** `review/data-provider-corrections-2026-11-17`  
**Reference Git HEAD:** Current correction branch  
**Binding Pilot Verdict:** **`CONDITIONAL GO`**

---

## 1. Package Contents and Structure

This supplementary package provides derived-only tabular outputs, byte accounting records, and indexing documentation requested by Person C and Person D to facilitate the final synthesis and audit of the empirical findings following the Data-Provider Review (Phases 5–9, 17 Nov 2026).

The package contains exclusively derived, aggregated tabular results. It contains **zero** raw packet captures (`.pcap`), Chrome NetLogs, participant PII, credentials, or IP addresses.

### Inventory of Files

1. `family_dropout.csv`:
   - Contains the pre-registered feature family dropout analysis for models **B5** (all flows) and **B6** (website flows only).
   - Evaluates the effect of dropping timing ($T$), volume ($V$), and concurrency ($C$) families independently.
   - Evaluated on the 10-fold Leave-One-Participant-Out (LOPO) split ($N = 91$).
   - Shows that dropping $T$ collapses B6 performance from $0.625$ to $0.456$ (below chance), proving temporal dynamics are the sole essential driver.
2. `sensitivity.csv`:
   - Contains genuine, newly re-extracted model perturbation and sensitivity analyses against the reference B6 LOPO AUROC ($0.625245$):
     - Heavy Edge/MSN news feed session ablation (excluding S0044, S0068, S0081; $N=88$, $\text{AUROC} = 0.6138$, $\Delta = -0.0114$).
     - Session S0062 inclusion via NetLog-reconstructed window ($N=92$, $\text{AUROC} = 0.6329$, $\Delta = +0.0077$, reconstructed from 1,048 real packets).
     - Search suggestion flow classification handling ($\text{AUROC} = 0.5708$, $\Delta = -0.0544$).
     - Packet burst separation threshold perturbation:
       - $\theta_b = 50\text{ ms}$: $\text{AUROC} = 0.6145$, $\Delta = -0.0108$.
       - $\theta_b = 250\text{ ms}$: $\text{AUROC} = 0.6203$, $\Delta = -0.0049$.
3. `b7_length_normalised_results.csv`:
   - Extracted baseline evaluation rows for **B7** (Length-Normalised website flow features) under both 4-fold Leave-One-Task-Out (LOTO) and 10-fold Leave-One-Participant-Out (LOPO) splits ($N = 91$).
   - Demonstrates that when features are defined as duration-normalized rates and dimensionless ratios (as done in the core 6 features of B6), the resulting performance is numerically identical to B6 (documented under DEV-07).
4. `per_participant_family_results.csv`:
   - Full 70-row tidy matrix containing summary statistics (mean, median, standard deviation) for all 10 human participants (`P01`–`P10`) across all 7 behavioral and diagnostic families ($T, V, C, H, D, L, Q$).
5. `CLAIM_TO_FILE_INDEX.md`:
   - Complete, exhaustive claim-to-file mapping table linking every reported result, baseline (B0–B8), negative control (NC1, NC2), effect size, and sensitivity metric to its exact source file, row, and column.
6. `README.md`:
   - This document.

---

## 2. Distinction Between Primary and Supplementary Results

To prevent misattribution or over-interpretation, Person B explicitly delineates the methodological status of each result:

- **Primary Headline Model:**
  - **`B6_core6`** (L2 Logistic Regression, $C=1.0$, strictly six standardized website-only features: $T_{\text{idle\_gap\_median}}$, $T_{\text{burst\_rate}}$, $V_{\text{up\_down\_ratio}}$, $V_{\text{upload\_burst\_share}}$, $C_{\text{new\_flows\_per\_min}}$, $C_{\text{max\_concurrent}}$).
  - Evaluated on primary population $N = 91$ (excluding S0062).
  - Primary Generalization Split: **4-fold LOTO** ($\text{AUROC} = 0.606$, 95% CI $[0.429, 0.793]$).
  - Primary Separability Split: **10-fold LOPO** ($\text{AUROC} = 0.625$, 95% CI $[0.502, 0.742]$).
- **Secondary Model Check:**
  - Pre-registered un-tuned 500-tree Random Forest check on the identical 6 features (LOPO $\text{AUROC} = 0.744$; LOTO $\text{AUROC} = 0.624$).
- **Duration Confound Disclosure:**
  - Multi-feature length baseline **B4** (`L_duration_s`, `L_total_bytes`, `L_n_flows`) achieves **LOTO $\text{AUROC} = 0.725$** and **LOPO $\text{AUROC} = 0.760$**, outperforming B6 ($0.606$ LOTO / $0.625$ LOPO).
  - Session duration alone (`B4_duration_only`) achieves **LOTO $\text{AUROC} = 0.553$** and **LOPO $\text{AUROC} = 0.574$**.
  - While B6 deliberately strips gross volume and flow counts to isolate micro-behavior, macroscopic task length and byte count remain highly predictive confounders at the client egress.
- **Formally Withdrawn / Not Run Baselines:**
  - **B2 (JA4 TLS Fingerprint Match):** Formally designated as `NOT_RUN` with metrics recorded as `NaN`. Automated JA4 extraction is not verified on egress captures in this environment; client identity match rests on Person A's localhost inspection (`8daaf6152771`).
  - **TCP Handshake RTT:** Formally designated as `RETRACTED (DEV-06)` in `results/drift_checks.csv`. Handshake RTT was an injected benchmark placeholder ($25.40\text{ ms}$) and does not represent an empirical measurement of network latency.
- **Shortcut Baselines (Not Generalisable Evidence):**
  - **B1** (Vendor API Presence/Bytes: $\text{AUROC} = 1.000$) and **B8** (Vendor-to-Website Cross-Flow Lag: $\text{AUROC} = 1.000$) reflect direct detection of the Gemini LLM API channel (`generativelanguage.googleapis.com`).
  - These are vendor shortcuts, present solely because the agent architecture sends screen captures to an external API endpoint. They do **not** represent generalizable client egress browsing behavior and are strictly stripped from B6.

---

## 3. Evaluation Splits and Cross-Validation Structure

All reported models were evaluated strictly under out-of-fold cross-validation without parameter tuning:

1. **4-fold Leave-One-Task-Out (LOTO):**
   - In each fold, all sessions of one web task ($T_1$, $T_2$, $T_3$, or $T_4$) are held out as the test set.
   - Evaluates whether behavioral differences learned on 3 web applications generalize to an unseen 4th application.
   - Test folds are balanced (each task has 10 agent runs and 12–13 human sessions).
2. **10-fold Leave-One-Participant-Out (LOPO):**
   - In each fold, all sessions of one human participant ($P_k$) plus agent runs with replication index $k$ are held out as the test set.
   - Evaluates whether separability holds across distinct human individuals.
   - Test folds have unequal sizes (Folds 0–2 for P01–P03 have 11–12 sessions; Folds 3–9 for P04–P10 have 8 sessions) due to unequal rounds in the original data collection.

---

## 4. Interpretation of Confidence Intervals

All 95% confidence intervals reported in `baseline_results.csv` and `effect_sizes.csv` were computed using **2,000 cluster-bootstrap resamples**, clustered at the independent session unit level (human participant ID for humans, independent run ID for agents).
- **Interpreting B6 LOPO CI $[0.502, 0.742]$:** The lower bound ($0.5019$) borders chance ($0.50$), reflecting moderate separability across human participants after eliminating flow-classification leaks.
- **Interpreting B6 LOTO CI $[0.429, 0.793]$:** The lower bound ($0.4295$) straddles chance ($0.50$), indicating that generalizability across completely unseen web applications cannot be guaranteed.

---

## 5. Session S0062 Reconstruction Protocol

- **Primary Analysis Scope ($N=91$):**
  - Session `S0062` is strictly **excluded** from the primary dataset and all primary baselines.
  - In `S0062` (Human, Task $T_1$, Participant `P03`, Round 2, recorded 7 November 2026), an operator keystroke error logged an active window duration of only $7.0\text{ ms}$ ($0.007\text{ s}$).
- **Sensitivity Analysis Scope ($N=92$):**
  - Session `S0062` was reconstructed from Chrome NetLog navigation request boundaries ($29.299\text{ s}$, from initial `/books` request at $t=1531642\text{ ms}$ to final book asset request at $t=1560941\text{ ms}$, corresponding to wall-clock timestamps $1794049100.315$ to $1794049129.614$).
  - A total of 1,048 actual packets were found within this window in `S0062.pcapng`. Features were genuinely extracted directly from these packets, replacing prior class-median imputation.
  - Retaining reconstructed `S0062` yields B6 LOPO $\text{AUROC} = 0.6329$ ($\Delta = +0.0077$).

---

## 6. Critical Methodological Caveats

### A. Calendar Day and Controller Confound
All 40 AI sessions were collected on 6 November 2026; all 52 human sessions were collected on 7 November (P01–P06) and 9 November (P07–P10).
- Negative control **NC2** (7 Nov vs 9 Nov within humans) yields $\text{AUROC} = 0.289$, reflecting structural fold-level distribution shifts between participants.
- In addition, Chrome component updater (`gvt1`) downloads were dynamically measured in 48 human session windows (mean 1.89 MB) and 0 agent windows. Background host activity (Spotify) was present in 50 human sessions and 0 agent sessions.
- While website-only filtering (B6) successfully removes `gvt1` and host background traffic from behavioral features, the temporal separation across calendar days remains an indelible structural property of pilot-v1.

---

*Handover Package Certified,*  
**Person B**  
*Analysis Lead*
