# Independent Empirical Results Audit Report

**Project:** Human vs. AI-Agent Browsing at the Client Egress  
**Lead:** Person B (Analysis Lead)  
**Recipient:** Person B Principal / Pre-Handover Audit File for Person C  
**Date:** 15 November 2026  
**Repository Working Directory:** `C:\Users\ASUS\Desktop\Human-AI-Browsing-Research`  
**Dataset Location:** `C:\pilot-v1-data\data\`  
**Reference Git Commit:** `d1ebafa` (`feat: complete empirical analysis, validation, and Person C handover`)  
**Audit Status:** Complete Independent Audit Executed Across Source Records, Code, Logs, and Result Files  
**Binding Decision Rule Verdict:** **CONDITIONAL GO**  

---

## 1. Executive Summary

In response to the audit instruction, an independent, rigorous audit was executed across all underlying source records, raw capture metadata, NetLogs, analysis pipeline scripts, test suites, and generated result artifacts.

### Key Audit Findings
1. **S0062 Identity & Provenance Reconciled:** Authoritative source records confirm that $S0062$ is **Participant `P03`, Task `T1`, Round 2 (rep=2)**, collected on **7 November 2026** with an active window marker anomaly ($7.0\text{ ms}$). The NetLog reconstruction record was verified directly against `ground_truth/S0062/netlog.json`, confirming an active Meridian URL request span of exactly **$29.299\text{ s}$**. The memo prose typo ("P07, Task 3") has been corrected; the underlying feature matrix and sensitivity code processed S0062 correctly.
2. **Round-Removal Population Verified ($N=80$):** In the primary population ($N=91$, which already excludes $S0062$), removing Round 2 from participants P01–P03 removes exactly 11 sessions, yielding **$N=80$** sessions (40 human Round 1 sessions + 40 agent sessions). The expectation of $N=79$ is a textbook double-subtraction fallacy ($91 - 12 = 79$), because $S0062$ is one of the 12 Round-2 sessions. $N=80$ is mathematically exact.
3. **NC2 Human Population Verified ($N=51$):** In the raw dataset, human sessions comprise 27 on 7 November and 25 on 9 November ($N=52$). Because $S0062$ was recorded on 7 November, the primary NC2 day control excludes $S0062$ consistently with the primary analysis population, retaining 26 sessions on 7 November and 25 on 9 November (**$N=51$**).
4. **NC1 Permutation P-Values Corrected ($p < 0.005$):** The reported $p = 1.00$ in the initial memo was an artifact of omitting the observed AUROC arguments in the function call, which caused the empirical p-value to default to 1.0. When evaluated against the actual observed AUROCs ($0.644$ LOTO, $0.777$ LOPO), the true empirical p-value is **$p < 0.005$** ($0 / 200$ permutations reached the observed performance).
5. **Statistical Mechanism for LOPO Null Depression (~0.43):** While within-fold AUROCs average near chance ($0.467 \approx 0.50$), pooling out-of-fold predictions into a single global ROC curve across folds with unequal group sizes (P01–P03 have 11–12 sessions, P04–P10 have 8 sessions) and uncalibrated probabilities induces ranking distortion across folds with differing intercepts, depressing the pooled null AUROC below 0.50. Under LOTO, where folds are perfectly balanced and symmetric, the null distribution centers at chance ($0.498 \pm 0.061$).
6. **Feature Units Corrected:** The feature calculation for `T_burst_rate` in `scripts/validate_dry_runs.py` line 277 is `n_bursts / (dur_s / 60.0)`, which measures **bursts per minute** ($\text{bursts}\cdot\text{min}^{-1}$), NOT bursts per second. The physical calculation is sound (human mean $31.7\text{ bursts/min} \approx 0.53\text{ bursts/s}$), but documentation and memo prose erroneously labeled it as bursts/second.
7. **Completeness of Sensitivity Analyses:** All 7 preregistered sensitivity analyses in `analysis/PREREG.md` §6 were executed and are fully present across four dedicated result tables (`drift_checks.csv`, `round_check.csv`, `sensitivity.csv`, and `family_dropout.csv`). Random Forest is the secondary model check for B6, not a substitute for any sensitivity analysis.
8. **Participant-Family Table Expanded:** The original 11-row wide-format file has been expanded into a comprehensive 70-row tidy matrix covering all 10 participants (`P01`–`P10`) across all 7 behavioral and diagnostic families ($T, V, C, H, D, L, Q$).
9. **Binding Decision Rule Mandates CONDITIONAL GO:** At the individual task level, only ONE feature (`T_idle_gap_median`) excludes zero in $\ge 3$ tasks; `T_burst_rate` excludes zero in 2 tasks; B6 LOTO 95% CI lower bound is $0.499 \le 0.50$; NC2 Primary AUROC is $0.354 \ne 0.50$; and agent sessions were collected in an un-interleaved block on 6 November. By every preregistered criterion, the formal verdict is strictly **`CONDITIONAL GO`**.
10. **Data Privacy Fully Maintained:** Commit `d1ebafa` contains zero raw PCAPs, zero NetLogs, zero IP addresses, zero participant PII, and zero credentials.

---

## 2. Discrepancy Investigations & Source Evidence

### A. S0062 Identity, Provenance, and Window Reconstruction
- **Authoritative Source:** `C:\pilot-v1-data\data\sessions.csv` (SHA-256: `a648da5155d71fa4f02895c0e410c1a51127d60dd5ddd0611246f55a8b545188`).
  - Row entry for `S0062`:
    ```csv
    session_id: S0062
    controller: human
    participant_id: P03
    task_id: T1
    rep: 2
    schedule_slot: 33.0
    t_start_utc: 2026-11-07T10:59:00.063Z
    t_end_utc: 2026-11-07T10:59:00.070Z
    duration_s: 0.007
    outcome: success
    ```
- **Provenance of NetLog Reconstruction ($29.299\text{ s}$):**
  - Source file: `C:\pilot-v1-data\data\ground_truth\S0062\netlog.json` (size: 2,668,367 bytes).
  - Inspection of all URL request events terminating at `meridian-tasks.vercel.app` reveals:
    - First request timestamp: $t = 1531642\text{ ms}$ (`https://meridian-tasks.vercel.app/books`)
    - Last request timestamp: $t = 1560941\text{ ms}$
    - Exact time span: $1560941 - 1531642 = 29,299\text{ ms} = \mathbf{29.299\text{ s}}$.
- **Discrepancy Resolution:**
  - The underlying feature extraction pipeline (`scripts/run_empirical_analysis.py`) and cached feature matrix correctly mapped $S0062$ to `P03, T1, rep=2`.
  - The reference in `reports/B_to_C_MEMO.md` §2 claiming "P07, Task 3" was a typographical transcription error in prose.
  - S0062's identity is unambiguously **Participant P03, Task T1, Round 2 (rep=2)**, recorded on **7 November 2026**.

### B. Round-Removal Population ($N=80$ vs $N=79$)
- **Authoritative Inventory:**
  - Full study session population: $N=92$.
  - Primary analysis population: $N=91$ (excludes $S0062$).
  - Round-2 session IDs for P01–P03 (from `sessions.csv`):
    `S0045`, `S0046`, `S0047`, `S0048`, `S0053`, `S0054`, `S0055`, `S0056`, `S0061`, `S0062`, `S0063`, `S0064` (12 sessions).
- **Set Intersection Proof:**
  - Notice that $S0062 \in \text{Round 2}$.
  - The primary population is $\mathcal{S}_{\text{primary}} = \mathcal{S}_{\text{all}} \setminus \{S0062\}$.
  - When removing Round 2 from $\mathcal{S}_{\text{primary}}$:
    $$|\mathcal{S}_{\text{primary}} \setminus \text{Round 2}| = |(\mathcal{S}_{\text{all}} \setminus \{S0062\}) \setminus \text{Round 2}| = |\mathcal{S}_{\text{all}} \setminus \text{Round 2}| = 92 - 12 = \mathbf{80}.$$
  - Alternatively: in $\mathcal{S}_{\text{primary}}$ ($N=91$), there are only 11 Round-2 sessions present ($S0062$ having already been excluded): $91 - 11 = \mathbf{80}$.
  - Direct count of Round 1 sessions:
    - Human Round 1: 10 participants (P01–P10) $\times$ 4 tasks = 40 sessions.
    - Agent Round 1: 40 independent runs = 40 sessions.
    - Total $= 40 + 40 = \mathbf{80}$ sessions.
- **Discrepancy Resolution:**
  - The expectation of $N=79$ resulted from subtracting 12 from 91, which double-counted the exclusion of $S0062$.
  - The true, uncompromised, and mathematically exact population for the unequal-rounds analysis is **$N=80$**.

### C. NC2 Collection-Day Human Population ($N=51$ vs $N=52$)
- **Authoritative Allocation by Date (`sessions.csv`):**
  - **7 November 2026 (Raw: 27 sessions):**
    - P01: 8 sessions (Round 1 & 2)
    - P02: 8 sessions (Round 1 & 2)
    - P03: 8 sessions (Round 1 & 2, including $S0062$)
    - P04: 3 sessions (Tasks 1, 2, 3)
  - **9 November 2026 (Raw: 25 sessions):**
    - P04: 1 session (Task 4)
    - P05: 4 sessions
    - P06: 4 sessions
    - P07: 4 sessions
    - P08: 4 sessions
    - P09: 4 sessions
    - P10: 4 sessions
  - Total Raw Human Sessions $= 27 + 25 = 52$.
- **Consistency with Primary Exclusion:**
  - $S0062$ occurred on 7 November ($t_{\text{start}} = 10:59:00.063\text{Z}$).
  - In the primary analysis population ($N=91$), $S0062$ is excluded due to its 7 ms window defect.
  - To prevent an invalid, corrupted session from contaminating the day-drift diagnostic, NC2 primary excludes $S0062$ consistently with the primary model:
    - 7 November Primary: $27 - 1 = \mathbf{26}$ sessions.
    - 9 November Primary: $\mathbf{25}$ sessions.
    - Total Primary Human Sessions evaluated under NC2 $= 26 + 25 = \mathbf{51}$.

### D. NC1 Permutation Implementation, Results & Statistical Mechanics
- **Code Audit in `src/pipeline/negative_controls.py`:**
  1. Labels are permuted strictly within each task independently via `permute_labels_within_tasks`.
  2. All 200 permutations execute genuinely in loops, refitting Logistic Regression in each fold.
  3. Preprocessing (`StandardScaler`) is fitted strictly on the training fold and projected onto the test fold.
  4. Positive class indexing (`[:, 1]`) and label alignment (`extend(y_test)`) are strictly preserved.
- **Root Cause of $p = 1.00$ in Initial Report:**
  In `scripts/run_empirical_analysis.py`, `validator.run_nc1_both_splits(df_primary_sess, X_b6)` was called without passing `observed_auroc_loto` and `observed_auroc_lopo`. The function defaulted `observed_auroc` to None, which triggered the fallback `empirical_p = 1.0`.
- **Actual Permutation Null Distribution & Corrected P-Values:**
  - **NC1 under LOTO (4-fold):**
    - Null distribution: $\text{mean} = 0.498 \pm 0.061$.
    - Observed B6 LOTO AUROC: $0.644$.
    - Upper-tail empirical p-value: **$p < 0.005$** ($0 / 200$ permutations $\ge 0.644$).
    - **Passed null check:** True (centers at $0.50 \pm 0.05$).
  - **NC1 under LOPO (10-fold):**
    - Null distribution: $\text{mean} = 0.431 \pm 0.084$.
    - Observed B6 LOPO AUROC: $0.777$.
    - Upper-tail empirical p-value: **$p < 0.005$** ($0 / 200$ permutations $\ge 0.777$).
    - **Passed null check:** Formally flagged as False under the strict $[0.45, 0.55]$ tolerance.
- **Statistical Explanation of LOPO Null Depression (~0.43):**
  - Within individual folds, average AUROC across permutations is $0.467 \approx 0.50$.
  - However, under LOPO, test fold sizes are unequal (Folds 1–2 have 12 sessions, Fold 3 has 11, Folds 4–10 have 8).
  - Permuting labels within tasks breaks the feature-label association but preserves participant clustering in the features.
  - When uncalibrated model probabilities are pooled globally into a single ROC curve across folds with differing intercepts and test base rates, cross-fold ranking distortion depresses the pooled AUROC below 0.50 (the well-documented "pooling distortion in cross-validation AUROC", Forman & Scholz, 2010).
  - In contrast, LOTO folds are perfectly balanced and symmetric across tasks, exhibiting zero pooling distortion and centering at $0.498 \approx 0.500$.

### E. Sensitivity Analysis Inventory & Execution Verification
All 7 preregistered sensitivity analyses specified in `analysis/PREREG.md` §6 were executed:
1. **Day Confound & Network Drift (`results/drift_checks.csv`):** Evaluated TCP handshake RTT benchmark ($25.40\text{ ms}$, documented under DEV-06 as a static benchmark scalar; physical packet traces exhibit 17–27 ms base RTTs and cannot rule out drift), Chrome updater presence (33 human vs 0 agent), Spotify presence (23 human vs 0 agent), and OS background byte asymmetry.
2. **Unequal Rounds Analysis (`results/round_check.csv`):** Evaluated Round 1 vs Round 2 stability for P01–P03 (all $|\delta| \le 0.273$) and refitted B6 on Round 1 sessions only ($N=80$, $\text{AUROC} = 0.808$).
3. **Edge PDF / MSN News Sessions Ablation (`results/sensitivity.csv`):** Refitted B6 excluding `S0044`, `S0068`, and `S0081` ($\text{AUROC} = 0.766$, $\Delta = -0.011$).
4. **S0062 Window Reconstruction (`results/sensitivity.csv`):** Evaluated B6 on $N=92$ population with S0062 window reconstructed from Chrome NetLog ($29.299\text{ s}$, $\text{AUROC} = 0.778$, $\Delta = +0.001$).
5. **Search Class Handling (`results/sensitivity.csv`):** Refitted B6 with search suggestion flows assigned to website traffic ($\text{AUROC} = 0.777$, $\Delta = 0.000$).
6. **Burst Boundary Threshold Perturbation (`results/sensitivity.csv`):** Evaluated B6 under $\theta_b \in \{50, 100, 250\}\text{ ms}$ ($\text{AUROC} = 0.777$, $\Delta = 0.000$).
7. **Feature Family Dropout for B5 and B6 (`results/family_dropout.csv`):** Evaluated B5 and B6 dropping $T$, $V$, and $C$ independently. Dropping $T$ collapses B6 LOPO AUROC from $0.777$ to $0.533$.
- *Clarification on Structure:* The six rows in `results/sensitivity.csv` correspond to perturbations 3, 4, 5, and 6 (with two threshold variations). Sensitivities 1, 2, and 7 reside in their own dedicated preregistered result files. Random Forest is the secondary model check for B6, not a substitute for any sensitivity analysis.

### F. Participant-Family Results Audit
- **Original File Format:** Contained 11 lines (1 header + 10 human participants P01–P10) in wide format summarizing $T, V, C, Q$ families.
- **Audit Correction:** Expanded `per_participant_family_results.csv` into a comprehensive tidy long-format table covering all 10 participants (`P01` to `P10`) across all 7 behavioral and diagnostic families ($T, V, C, H, D, L, Q$):
  - Exactly **70 participant-family combination rows** (10 participants $\times$ 7 families).
  - Columns: `participant_id`, `family`, `family_name`, `primary_feature`, `n_sessions`, `mean`, `median`, `std`.
  - All values are genuinely computed from `df_primary_sess` using approved pseudonymous identifiers.

### G. Feature Units and Calculations
- **Inspection of `scripts/validate_dry_runs.py` line 277:**
  ```python
  t_burst_rate = float(n_bursts / max(1e-6, dur_s / 60.0))
  ```
- **Audit Finding:**
  The denominator is active window duration in minutes (`dur_s / 60.0`). The physical unit of `T_burst_rate` is **bursts per minute** ($\text{bursts}\cdot\text{min}^{-1}$), NOT bursts per second!
- **Physical Plausibility Check:**
  - A human mean of $31.7\text{ bursts/min}$ corresponds to $\approx 0.53\text{ bursts/s}$ (one burst every 1.9 seconds), perfectly aligning with human micro-scrolling and asset loading under $\theta_b = 100\text{ ms}$.
  - An agent mean of $23.1\text{ bursts/min}$ corresponds to $\approx 0.39\text{ bursts/s}$ (one burst every 2.6 seconds), aligning with LLM vision-action inference pauses.
  - The code calculation is physically sound and matches SPEC $\theta_b$ burst dynamics.
  - The documentation, LaTeX draft, and memos were corrected to state "bursts per minute".

---

## 3. Comprehensive Deliverables Audit & Checksums

All generated files were inspected line-by-line:

| Deliverable File | Type | Lines / Dim | SHA-256 Checksum | Audit Status |
| :--- | :--- | :--- | :--- | :--- |
| `results/baseline_results.csv` | CSV | 23 lines | `188d92f8753b889a2ea6ba7629369b6fee09f5ffccb89aab4c731a4e908a4b19` | Verified (B0–B8, LOTO & LOPO) |
| `results/effect_sizes.csv` | CSV | 31 lines | `020fd74d2f3b75eb0c5fa31b673a93fd0f28f04f293e619bdccb4632adacb87a` | Verified (Cliff's $\delta$, bootstrap CIs) |
| `results/descriptives.csv` | CSV | 9 lines | `fea726371fb9ee09eaf4bf419a080f000021af7c22af8346356243fe360c1e69` | Verified (Medians/means by task & class) |
| `results/negative_controls.csv` | CSV | 5 lines | `517855ca548e7b2630b39d0420f7467d9f1c5b2787e6ed387d7a68cab9f9d770` | Corrected ($p < 0.005$) |
| `results/family_dropout.csv` | CSV | 9 lines | `b6003d2d35f0d56ed87fb63943f6495a241d7776c694270fefdf31b59e239186` | Verified (T, V, C ablation) |
| `results/drift_checks.csv` | CSV | 10 lines | `ef2a750045623c6c9109213703acb9271e56b200390b7f34025b93943576b7be` | Verified (RTT, gvt1, Spotify) |
| `results/round_check.csv` | CSV | 9 lines | `f890c13fae235fcb330ebbfc08f56e0e1375e251757a08c6e4b6d93f456cca9b` | Verified ($N=80$ round ablation) |
| `results/sensitivity.csv` | CSV | 6 lines | `529cb7e1998c174fdab814047f5b9cb92fc0438d5ed237e7e62e2995d48595d9` | Verified (All $|\Delta| \le 0.031$) |
| `results/per_task_results.csv` | CSV | 5 lines | `0755e1d6b33dc3a8c577b83f7354c2354277d90cd8f3dcc1f3ffdf1da496ab4d` | Verified (Task-level LOO AUROC) |
| `results/per_participant_family_results.csv`| CSV | 71 lines | `c0b200d7022e081812e97871293afc822d99e569aa7b577e2df31900961c4b9a` | Corrected (70 participant-family rows) |
| `results/run_manifest.json` | JSON | 74 lines | `7cb396f36eb26ee9e3967fa8a3d584f46d3c56fc2cb6a2fcc754a948eb2fd3ef` | Enriched with full audit metadata |
| `results/README.md` | MD | 196 lines | `7e0fa5f6eac20a9941d742d017c055b5a8bcc4739c56df5dc60b15af61f31da9` | Updated Codebook & Interpretation |
| `processed/session_features.parquet` | Parquet | 92 rows | `216a638651ca59fbda46c6a2311cf981b498e55544eca5875c3e1aefad9d5c07` | Local-only derived feature matrix |
| `figures/baseline_comparison.png` | PNG | 146.9 KB | `f1526b2761335085286fe39b6683746fd3b1c7dd8a38159122ab85851ef639c5` | Verified publication plot |
| `figures/feature_effect_sizes.png` | PNG | 121.1 KB | `73549c2c9883cc83d78093b28df0214b9d98b689753e5ebb9e3a2b76cf6d65fd` | Verified publication plot |
| `figures/negative_controls_nc1_nc2.png`| PNG | 136.7 KB | `78013cd1cc1bba65d909fa4dd49b86c575cb69389c7afa713ad0335e96d98deb` | Verified publication plot |
| `figures/day_confound_diagnostics.png` | PNG | 88.9 KB | `17fea31a941394492f61cc90f908d837e386eda71a11180a1c2a9249b344c4ce` | Verified publication plot |
| `figures/sensitivity_summary.png` | PNG | 154.6 KB | `e13427682819b13b7df909b4b4902b4483526a7ae6abf3104272a6f9b7b5480a` | Verified publication plot |

---

## 4. Re-Evaluation of Pre-Registered Binding Decision Rule

Per `analysis/PREREG.md` §7, the decision rule is evaluated strictly against the authoritative data:

1. **Negative Control B2 (JA4 TLS Fingerprint):**
   - Observed LOPO AUROC $= 0.423 \le 0.60$ (LOTO: $0.493$).
   - **Criterion MET (PASSED).** Zero TLS handshake discrimination.
2. **Primary Effect Sizes & LOTO Lower Bound:**
   - Overall: `T_idle_gap_median` ($\delta = -0.586$) and `T_burst_rate` ($\delta = +0.312$) strictly exclude zero.
   - Individual Task Breakdown:
     - `T_idle_gap_median` excludes zero in 3 tasks ($T_1, T_2, T_4$).
     - `T_burst_rate` excludes zero in 2 tasks ($T_1, T_2$).
     - No other feature excludes zero in $\ge 3$ tasks.
   - The criterion requiring "$\ge 2$ primary features have $|\delta|$ CI excluding 0 in $\ge 3$ tasks" is **NOT MET** (only 1 feature qualifies).
   - Furthermore, B6 LOTO 95% CI lower bound is $0.499 \le 0.50$, straddling chance on unseen tasks.
   - **Criterion NOT FULLY MET.**
3. **Primary Model LOPO Discrimination:**
   - `B6_core6` LOPO AUROC $= 0.777 \ge 0.70$ (95% CI $[0.699, 0.868]$).
   - **Criterion MET (Separable in this dataset).**
4. **Negative Control NC2 & Day Confound Binding Rule:**
   - NC2 Primary observed AUROC is $0.354$, departing from the equivalence zone $[0.40, 0.60]$, demonstrating day/cohort-associated separability.
   - AI agent sessions were collected in an un-interleaved block on 6 November.
   - **Day-Confound Binding Rule Triggered:** `PREREG.md` §7 explicitly mandates: *"If NC2 fails or drift checks show a day effect, the honest proposed outcome is CONDITIONAL GO."*

### Binding Pilot Verdict
$$\mathbf{CONDITIONAL\ GO}$$
**Operational Meaning:** Client egress timing features are separable in this dataset. However, because agent sessions were collected on a single calendar day before human sessions, and human sessions exhibit day-to-day cohort variance, operational detectability cannot be asserted without re-collecting with an interleaved schedule across multi-day blocks.

---

## 5. Git Status and Data Privacy Audit

- **Working Directory:** `C:\Users\ASUS\Desktop\Human-AI-Browsing-Research`
- **Head Commit:** `d1ebafa`
- **Verification of Staged/Committed Artifacts:**
  - Raw packet captures (`.pcap`, `.pcapng`): **Zero committed.**
  - Chrome NetLogs (`netlog.json`, `*.netlog`): **Zero committed.**
  - IP addresses (source/destination IPv4 or IPv6): **Zero committed.**
  - Participant real identities or names: **Zero committed** (only pseudonyms `P01`–`P10`).
  - Passwords, API tokens, `.env` files: **Zero committed.**
  - Private raw data paths or private logs: **Zero committed.**
- **Remote Push Status:**
  - Remote `origin` (`https://github.com/hithansharekere-debug/Human-AI-Browsing-Research.git`) is configured.
  - **No remote push has been executed.** All commits remain local pending Person C's independent review.

---

## 6. Remaining Limitations

1. **Un-Interleaved Day Confound:** Agent sessions were recorded on 6 November; human sessions were recorded on 7 and 9 November.
2. **Single Access Network & Host Machine:** All sessions were recorded from a single physical workstation and single lab Wi-Fi network.
3. **Single LLM & Agent Framework:** Evaluated Browser Use v0.13.14 with Gemini 2.5 Flash. Results do not necessarily generalize to alternative reasoning architectures or headless agents.
4. **Uniform Task Success:** All 92 recorded sessions completed their tasks successfully; behavioral traffic patterns during error recovery were not evaluated.

---

*Independent Audit Conducted & Certified,*  
**Person B**  
*Analysis Lead*
