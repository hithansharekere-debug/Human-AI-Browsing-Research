# Supplementary Person B → Person C/D Results Handover Package

**Project:** Human vs. AI-Agent Browsing at the Client Egress  
**Author:** Person B (Analysis Lead)  
**Recipients:** Person C (Audit/Synthesis Lead), Person D (Senior Reviewer)  
**Date:** 15 November 2026  
**Repository Working Directory:** `C:\Users\ASUS\Desktop\Human-AI-Browsing-Research`  
**Reference Git HEAD:** `48cda7c`  
**Binding Pilot Verdict:** **`CONDITIONAL GO`**

---

## 1. Package Contents and Structure

This supplementary package provides derived-only tabular outputs and indexing documentation requested by Person C and Person D to facilitate the final synthesis and audit of the empirical findings.

The package contains exclusively derived, aggregated tabular results. It contains **zero** raw packet captures (`.pcap`), Chrome NetLogs, participant PII, credentials, or IP addresses.

### Inventory of Files

1. `family_dropout.csv`:
   - Contains the pre-registered feature family dropout analysis for models **B5** (all flows) and **B6** (website flows only).
   - Evaluates the effect of dropping timing ($T$), volume ($V$), and concurrency ($C$) families independently.
   - Evaluated on the 10-fold Leave-One-Participant-Out (LOPO) split ($N = 91$).
2. `sensitivity.csv`:
   - Contains the pre-registered model perturbation and sensitivity analyses against the reference B6 LOPO AUROC ($0.776961$):
     - Heavy Edge/MSN news feed session ablation (excluding S0044, S0068, S0081; $N=88$, $\text{AUROC} = 0.765625$).
     - Session S0062 inclusion via NetLog-reconstructed window ($N=92$, $\text{AUROC} = 0.778365$).
     - Search suggestion flow classification handling ($\Delta = 0.000$).
     - Packet burst separation threshold perturbation ($\theta_b \in \{50, 100, 250\}\text{ ms}$, $\Delta = 0.000$).
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
  - Primary Generalization Split: **4-fold LOTO** ($\text{AUROC} = 0.644$, 95% CI $[0.499, 0.807]$).
  - Primary Separability Split: **10-fold LOPO** ($\text{AUROC} = 0.777$, 95% CI $[0.699, 0.868]$).
- **Secondary Model Check:**
  - Pre-registered un-tuned 500-tree Random Forest check on the identical 6 features (LOPO $\text{AUROC} = 0.797$; LOTO $\text{AUROC} = 0.560$).
- **Diagnostic / Sensitivity Results:**
  - Family dropout (identifies temporal dynamics $T$ as the sole essential driver of separability).
  - Sensitivity checks (Edge ablation, S0062 window reconstruction, search classification, burst thresholds).
  - Negative controls NC1 and NC2.
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
- **Interpreting B6 LOPO CI $[0.699, 0.868]$:** Strictly excludes 0.50 (chance) and the lower bound is $\ge 0.699 \approx 0.70$, confirming substantial separability across human participants within this dataset.
- **Interpreting B6 LOTO CI $[0.499, 0.807]$:** The lower bound ($0.4988$) straddles chance ($0.50$). This indicates that while average discrimination across tasks is $0.644$, performance on an unseen task can drop toward chance (e.g., Task $T_4$ LOO AUROC is $0.554$). Generalization to arbitrary web applications is not proven.

---

## 5. Session S0062 Inclusion and Exclusion Protocol

- **Primary Analysis Scope ($N=91$):**
  - Session `S0062` is strictly **excluded** from the primary dataset and all primary baselines.
  - In `S0062` (Human, Task $T_1$, Participant `P03`, Round 2, recorded 7 November 2026), an operator keystroke error logged an active window duration of only $7.0\text{ ms}$ ($0.007\text{ s}$), truncating packet capture within the window.
- **Sensitivity Analysis Scope ($N=92$):**
  - Session `S0062` is retained in sensitivity analysis with its active task duration reconstructed from objective Chrome NetLog request boundaries ($29.299\text{ s}$, from initial `/books` request at $t=1531642\text{ ms}$ to final book asset request at $t=1560941\text{ ms}$).
  - Including reconstructed `S0062` yields B6 LOPO $\text{AUROC} = 0.778365$ ($\Delta = +0.001405$). The primary exclusion has negligible impact on study conclusions.

---

## 6. Critical Methodological Caveats

### A. Calendar Day and Controller Confound
- All 40 autonomous agent sessions were captured in a single continuous block on **6 November 2026**.
- Human sessions were captured across **7 November** (26 primary sessions) and **9 November** (25 primary sessions).
- Although physical network latency checks confirm standard base RTTs (17–27 ms) and B2 JA4 TLS handshakes show zero cryptographic leakage ($\text{AUROC} \le 0.493$), the un-interleaved schedule means that day-associated network or host environmental shifts cannot be completely disentangled from human-vs-agent controller differences.

### B. NC2 Human Day Control and the 0.2537 Permutation Null
- The primary NC2 control (Human 7 Nov vs Human 9 Nov, $N=51$) yielded an observed raw pooled $\text{AUROC} = 0.353846$ (participant-clustered 95% CI $[0.2438, 0.4860]$).
- A 500-permutation simulation of participant-level day assignment yielded a permuted null mean of **$0.2537 \pm 0.1208$** ($p = 0.7860$).
- **Mathematical Root Cause:** In participant-grouped cross-validation across days, each test fold contains only one class. Holding out a Class 0 participant increases the training base rate, shifting the model intercept upward and artificially inflating predicted probabilities for the held-out Class 0 sessions. When raw uncalibrated probabilities are pooled globally into a single ROC curve, Class 0 sessions systematically receive higher probabilities than Class 1 sessions, inverting the ranking and driving the pooled AUROC far below 0.50.
- **Prior-Calibrated Diagnostic:** When out-of-fold logits are calibrated by the training prior, the observed NC2 AUROC shifts from $0.354$ to **$0.513846$** (pure chance), and the permutation null centers at **$0.4570 \approx 0.50$**.
- This proves that client egress features do **not** genuinely separate between 7 Nov and 9 Nov once fold-intercept distortion is removed.

---

## 7. Binding Pilot Verdict

In strict accordance with the pre-registered decision rule (`analysis/PREREG.md` §7):
$$\mathbf{CONDITIONAL\ GO}$$
*(Egress timing features separate classes in this dataset [LOPO AUROC 0.777], but operational detectability cannot be asserted without re-collecting with an interleaved human-agent schedule across multi-day blocks).*

---

*Handover Package Prepared & Certified,*  
**Person B**  
*Analysis Lead*
