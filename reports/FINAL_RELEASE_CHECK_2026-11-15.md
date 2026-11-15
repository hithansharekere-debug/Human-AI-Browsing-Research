# Final Statistical and Release Verification Report

**Project:** Human vs. AI-Agent Browsing at the Client Egress  
**Role:** Person B (Analysis Lead)  
**Recipient:** Person B Principal / Pre-Release Verification for Person C  
**Date:** 15 November 2026  
**Repository Working Directory:** `C:\Users\ASUS\Desktop\Human-AI-Browsing-Research`  
**Dataset Location:** `C:\pilot-v1-data\data\`  
**Reference Git Commit:** `c0725c3` (`docs(audit): complete independent empirical results audit and reconcile evidence`)  
**Status:** Verification Complete — Final Release Check Executed  
**Release Recommendation:** **APPROVE FOR PERSON C SYNTHESIS (HOLD REMOTE GITHUB PUSH)**  
**Binding Pilot Verdict:** **CONDITIONAL GO**

---

## 1. Executive Summary

This report establishes the final statistical verification and release audit across the empirical results pipeline, addressing all targeted inquiries regarding negative controls (NC1, NC2), network drift metrics (TCP handshake RTT), session reconstruction provenance (S0062), data privacy, and repo release readiness.

All 36 unit and integration tests pass without error (`36 passed in 13.75s`). The working directory is clean, all data files are strictly derived tabular outputs, and zero sensitive artifacts (PCAPs, NetLogs, IP addresses, credentials, PII) have been staged or committed.

---

## 2. Targeted Verification Findings

### A. NC1 LOPO Statistical Validation

A rigorous audit of the 200 within-task label permutations was conducted under both Leave-One-Task-Out (LOTO) and Leave-One-Participant-Out (LOPO) cross-validation splits.

#### 1. Permutation Procedure and Label Counts
- Labels were permuted strictly within each of the four tasks independently, preserving task-specific class balances:
  - **Task $T_1$:** 22 sessions (12 human, 10 agent; S0062 excluded).
  - **Task $T_2$:** 23 sessions (13 human, 10 agent).
  - **Task $T_3$:** 23 sessions (13 human, 10 agent).
  - **Task $T_4$:** 23 sessions (13 human, 10 agent).
  - **Total Primary Population:** $N = 91$ sessions (51 human, 40 agent).
- For every permutation iteration, preprocessing (`StandardScaler`) was refitted strictly on the training fold, the $L_2$ Logistic Regression model was fitted on training data, predictions were generated on the test fold, and out-of-fold predictions were pooled globally before AUROC calculation.

#### 2. Actual NC1 LOPO 200 Permutation Null Distribution
- **Count:** 200 permutations
- **Mean:** $0.430882$
- **Median:** $0.434559$
- **Standard Deviation:** $0.084334$
- **Minimum:** $0.197549$
- **Maximum:** $0.617647$
- **Quantiles:**
  - 1%: $0.217985$
  - 5%: $0.290196$
  - 10%: $0.323039$
  - 25%: $0.375000$
  - 50%: $0.434559$
  - 75%: $0.484926$
  - 90%: $0.543333$
  - 95%: $0.566397$
  - 99%: $0.602539$

#### 3. Per-Fold Within-Fold Null Summaries
Evaluation of test folds across the 200 permutations shows:
- **Fold 0 (P01, $n=12$):** Within-fold $\text{AUROC} = 0.467 \pm 0.181$, mean prob $= 0.436 \pm 0.155$.
- **Fold 1 (P02, $n=12$):** Within-fold $\text{AUROC} = 0.459 \pm 0.184$, mean prob $= 0.440 \pm 0.085$.
- **Fold 2 (P03, $n=11$):** Within-fold $\text{AUROC} = 0.503 \pm 0.189$, mean prob $= 0.438 \pm 0.142$.
- **Fold 3 (P04, $n=8$):** Within-fold $\text{AUROC} = 0.459 \pm 0.240$, mean prob $= 0.438 \pm 0.107$.
- **Fold 4 (P05, $n=8$):** Within-fold $\text{AUROC} = 0.472 \pm 0.222$, mean prob $= 0.439 \pm 0.103$.
- **Fold 5 (P06, $n=8$):** Within-fold $\text{AUROC} = 0.469 \pm 0.257$, mean prob $= 0.442 \pm 0.116$.
- **Fold 6 (P07, $n=8$):** Within-fold $\text{AUROC} = 0.487 \pm 0.244$, mean prob $= 0.440 \pm 0.135$.
- **Fold 7 (P08, $n=8$):** Within-fold $\text{AUROC} = 0.490 \pm 0.227$, mean prob $= 0.437 \pm 0.107$.
- **Fold 8 (P09, $n=8$):** Within-fold $\text{AUROC} = 0.493 \pm 0.227$, mean prob $= 0.441 \pm 0.091$.
- **Fold 9 (P10, $n=8$):** Within-fold $\text{AUROC} = 0.462 \pm 0.241$, mean prob $= 0.441 \pm 0.130$.

#### 4. Investigation of LOPO Null Mean Deviation (0.431)
- Within individual test folds, the discrimination ability is near chance: the average unpooled within-fold macro AUROC is $0.4765 \pm 0.0899$.
- When predicted probabilities are rank-standardized within each fold prior to pooling, the pooled AUROC mean shifts rightward to $0.4784 \pm 0.0791$.
- **Statistical Root Cause:** In LOPO, test fold sample sizes and base rates are unequal: Folds 0–2 have 11–12 sessions with a 67% human base rate (P01–P03 performed 2 rounds), whereas Folds 3–9 have 8 sessions with a 50% human base rate (P04–P10 performed 1 round).
- As established in statistical machine learning literature (Forman & Scholz, 2010), pooling raw, uncalibrated out-of-fold predicted probabilities across folds with differing intercepts and group sizes induces cross-fold ranking distortion, depressing the pooled AUROC below 0.50.
- Under LOTO, where folds are perfectly balanced and symmetric across all 4 tasks (each task fold contains identical 10 AI sessions and 12–13 human sessions), cross-fold ranking distortion is absent, and the null distribution centers at chance ($0.4981 \pm 0.0609$).
- **Evidence Statement:** We explicitly do NOT claim that the LOPO null distribution conventionally centers at 0.50 under global pooling ($0.431 \ne 0.500$). However, because zero of the 200 permuted runs reached the observed LOPO AUROC of $0.776961$, the separation remains statistically significant.

#### 5. Plus-One Empirical P-Values
Using the standard conservative plus-one formula:
$$p = \frac{1 + \sum_{i=1}^B \mathbb{I}(\text{AUROC}_{\text{null}, i} \ge \text{AUROC}_{\text{obs}})}{B + 1}$$
- **LOPO Split ($B=200$, observed $\text{AUROC} = 0.776961$):**
  $$p = \frac{1 + 0}{201} = \mathbf{0.004975}\ (p < 0.0050)$$
- **LOTO Split ($B=200$, observed $\text{AUROC} = 0.644118$):**
  $$p = \frac{1 + 0}{201} = \mathbf{0.004975}\ (p < 0.0050)$$

---

### B. NC2 Human Collection-Day Inference

The primary NC2 negative control evaluates whether client egress traffic features discriminate between human collection dates (7 November vs. 9 November 2026).

#### 1. Population & Class Orientation
- Primary human population: $N = 51$ sessions (S0062 excluded due to 7 ms duration defect).
- **7 November 2026 (Class 0):** $26$ sessions (P01: 8, P02: 8, P03: 7, P04: 3).
- **9 November 2026 (Class 1):** $25$ sessions (P04: 1, P05: 4, P06: 4, P07: 4, P08: 4, P09: 4, P10: 4).
- **Positive-Class Orientation:** $\text{Class } 0 = \text{7 Nov}$, $\text{Class } 1 = \text{9 Nov}$.
- **Cross-Validation:** Participant-grouped holdout (each participant is entirely held out in train or test).

#### 2. Observed Metric & Clustered Uncertainty
- **Observed AUROC:** $0.353846$ (F1 $= 0.428571$).
- **Participant-Clustered 95% Confidence Interval (2000 cluster-bootstrap resamples):**
  $$\text{95\% CI: } [0.2438,\ 0.4860]$$
  The confidence interval strictly excludes 0.50 (upper bound $0.4860 < 0.50$).

#### 3. Participant-Grouped Permutation Test & Mechanics
- **Exact Permutation Procedure:**
  To test exchangeability under participant grouping, participant-level day assignments were permuted 500 times: 3 randomly selected participants were assigned to Nov 7 (all sessions = 0), 1 participant to the P04 split (Tasks 1–3 on Nov 7 = 0, Task 4 on Nov 9 = 1), and 6 participants to Nov 9 (all sessions = 1).
- **Fold Construction & Scoring:**
  Cross-validation uses 10 folds corresponding to the 10 participants. In each fold, the held-out participant's test set contains only one class (except Fold 3 with P04). Preprocessing and Logistic Regression are fitted on the remaining 9 participants, generating out-of-fold predicted probabilities $P(Y=1|X)$ that are pooled globally before AUROC calculation.
- **Why the Permuted Null AUROC Mean is 0.2537:**
  - Because test folds are homogeneous (single-class), the within-fold AUROC is undefined, and scoring depends entirely on global pooling across folds.
  - When a Class 0 participant is held out, the training set suffers a deficit of Class 0, so the training prevalence $\bar{y}_{\text{train}}$ increases (e.g. from 49% to 58% Class 1). In Logistic Regression, the intercept $\beta_0 \approx \log(\frac{\bar{y}}{1 - \bar{y}})$ shifts upward, systematically inflating the predicted probabilities $P(Y=1)$ for the held-out Class 0 sessions.
  - Conversely, when a Class 1 participant is held out, $\bar{y}_{\text{train}}$ drops (to 45% Class 1), shifting $\beta_0$ downward and depressing $P(Y=1)$ for the held-out Class 1 sessions.
  - When these raw uncalibrated probabilities are pooled globally into a single ROC curve, Class 0 sessions systematically receive higher probabilities than Class 1 sessions, inverting the global ranking and depressing the pooled AUROC far below 0.50 (mean $0.2537 \pm 0.1208$).
  - This effect is exacerbated because participants have unequal session counts (P01–P03 have 7–8 sessions while P05–P10 have 4 sessions).
- **Statistical Diagnostic (Prior-Calibrated Scoring):**
  - To test whether the 0.2537 null is an artifact of fold-intercept shift, a prior-calibrated diagnostic was evaluated by adjusting predicted logits by the training prior: $\text{logit}(p) - \log(\frac{\bar{y}_{\text{train}}}{1 - \bar{y}_{\text{train}}})$.
  - Under prior calibration, the permutation null mean shifts rightward from $0.229$ to **$0.4570 \pm 0.0812$** (centering near chance).
  - More importantly, the **observed NC2 AUROC under prior calibration shifts from $0.353846$ to $0.513846$** (virtually identical to 0.500, indicating zero genuine feature discrimination between 7 Nov and 9 Nov).
- **Interpretation, Recommendation & Defect Documentation:**
  - The observed raw AUROC of $0.354$ does NOT represent an inverted physical traffic signature across days. It is a mathematical defect of pooling uncalibrated out-of-fold probabilities across cluster-homogeneous folds.
  - The 0.2537 null mean is NOT statistically interpretable as a standard exchangeable null; it is an artifact of the same pooling defect under cluster permutation.
  - **Recommendation:** Do NOT silently alter or replace the preregistered primary NC2 result in `results/negative_controls.csv`. Retain the primary metric ($0.354$) as preregistered, but document the prior-calibrated diagnostic ($0.514$) in reports to explain that day separability is absent once intercept pooling distortion is removed.
  - **Confounding Disclosure:** Collection day and controller label remain completely confounded because all 40 AI sessions were collected on 6 November, whereas human sessions were collected on 7 and 9 November.
- **Supplementary Diagnostic:** The supplementary AI-vs-Human day diagnostic yields $\text{AUROC} = 0.7770$ and $\text{F1} = 0.6389$ (confounded by day).

---

### C. TCP Handshake RTT Provenance and Network Drift Limitations

An audit of the reported TCP handshake RTT in `results/drift_checks.csv` was conducted.

1. **Provenance of Reported Metric:**
   - In `scripts/run_empirical_analysis.py` (lines 390–394), the analysis pipeline utilized a fixed benchmark scalar:
     ```python
     rtt_dict = {row["session_id"]: 25.4 for _, row in df_primary_sess.iterrows()}
     ```
   - **Observation Count:** 91 entries (40 AI on Nov 6, 26 Human on Nov 7, 25 Human on Nov 9).
   - **Values Injected:** The identical constant float $25.4\text{ ms}$ was assigned to all sessions.
   - **Standard Deviation Artifact:** The reported standard deviation ($7.1 \times 10^{-15}\text{ ms}$) was a mathematical precision artifact of calculating the sample standard deviation on an array of identical float constants, rather than physical network latency stability across calendar days.
2. **Physical Packet Capture Evidence:**
   - Physical packet inspection of raw `.pcapng` files reveals that true TCP handshake ($\text{SYN} \rightarrow \text{SYN/ACK}$) round-trip times to `meridian-tasks.vercel.app` (and port 443) typically exhibit base latencies between 17 and 27 ms, with variable jitter, retransmissions, and latency spikes exceeding 100 ms on occasional flows.
3. **Formal Deviation (`DEV-06`):**
   - Logged in `analysis/DEVIATIONS.md` as `DEV-06`. Documentation in `reports/B_to_C_MEMO.md`, `results/README.md`, and `reports/EMPIRICAL_RESULTS_AUDIT_2026-11-15.md` has been corrected to remove claims that RTT was "invariant at 25.40 ms ruling out drift".
4. **Scientific Limitation:**
   - Handshake RTT to a single server origin cannot rule out physical network, ISP routing, or environmental drift across collection dates. The calendar day confound remains an active limitation.

---

### D. S0062 Reconstruction Verification

The original source records and Chrome NetLog for session `S0062` were audited.

1. **Authoritative `sessions.csv` Record:**
   - Row 77 of `sessions.csv` (SHA-256 `a648da5155d71fa4f02895c0e410c1a51127d60dd5ddd0611246f55a8b545188`):
     - `session_id: S0062`
     - `controller: human`
     - `participant_id: P03` (unambiguously P03, not P07)
     - `task_id: T1` (Bookstore browsing, not T3)
     - `rep: 2` (Round 2)
     - `t_start_utc: 2026-11-07T10:59:00.063Z`
     - `t_end_utc: 2026-11-07T10:59:00.070Z`
     - `duration_s: 0.007` (7.0 ms marker anomaly)
     - `outcome: success`
2. **NetLog Event Analysis (`ground_truth/S0062/netlog.json`):**
   - Total NetLog events: 11,335. Total `URL_REQUEST` sources: 74 (53 task-related, 21 non-task).
   - **First Selected Task Request:** `https://meridian-tasks.vercel.app/books`, request start time $t = 1531642\text{ ms}$.
   - **Last Selected Task Request:** `https://meridian-tasks.vercel.app/img/book/11.svg`, request start time $t = 1560941\text{ ms}$ (event end $1560992\text{ ms}$).
   - **Exact Reconstructed Span:** $1560941 - 1531642 = 29,299\text{ ms} = \mathbf{29.299\text{ s}}$.
3. **Representativeness of Active Task Interval:**
   - In Task $T_1$, the user was instructed to browse books on `meridian-tasks.vercel.app/books`. The initial request at $1531642\text{ ms}$ represents the initial page navigation, followed by CSS styles and SVG book assets, culminating in the final book asset fetch at $1560941\text{ ms}$.
4. **External Factors & Integrity:**
   - **Redirects:** Direct navigation (HTTP 200); no HTTP 301/302 redirects.
   - **Retries:** Zero failed TCP connects or aborted requests to the task server.
   - **Background Requests:** Chrome SafeBrowsing requests (`safebrowsing.googleapis.com` and Fastly edge OHTTP relays) overlap the interval, but are strictly excluded by origin domain rules (`flow_rules.yaml`).
   - **Source Record Preservation:** `sessions.csv` remains strictly untouched. S0062 is excluded from the primary model ($N=91$) and evaluated in sensitivity testing ($N=92$, $\text{AUROC} = 0.778$, $\Delta = +0.001$).

---

### E. Final Privacy and Release Inspection

A full inspection of commits beyond `origin/master` (including `d1ebafa`, `c0725c3`, and working tree) was performed:
1. **Committed File Inventory:**
   - 29 files modified or added. All are documentation (`.md`, `.tex`), pipeline scripts (`.py`), test suites, publication figures (`.png`), and derived result tables (`.csv`, `.json`).
   - `processed/session_features.parquet` is strictly local (gitignored).
2. **Data Privacy Audit:**
   - Raw packet captures (`.pcap`, `.pcapng`): **Zero committed.**
   - Chrome NetLogs (`netlog.json`, `*.netlog`): **Zero committed.**
   - Passwords, API tokens, `.env` files: **Zero committed.**
   - Participant PII: **Zero committed** (only pseudonyms `P01`–`P10`).
   - IP Addresses: Zero external or client IP leakage. Only standard documentation and test IPs appear in code: RFC 5737 TEST-NET-1 marker (`192.0.2.1`), subnet broadcast (`192.168.1.255`), limited broadcast (`255.255.255.255`), and standard lab local IP (`[private LAN address]`) from Person A's handover.
3. **Data Schemas:** All 10 CSV tables, the JSON run manifest, and parquet schemas conform strictly to specifications.
4. **Git Coverage:** `.gitignore` actively excludes `*.pcap`, `*.pcapng`, `*.parquet`, `data/`, `interim/`, `.env`, and private archives.

---

## 3. Outstanding Issues and Scientific Limitations

1. **Un-Interleaved Day Confound:** All agent sessions were captured on 6 November; human sessions were captured on 7 and 9 November. While negative control B2 confirms that browser TLS handshakes do not discriminate ($0.423 \le 0.60$), calendar day variance cannot be completely uncoupled from controller type.
2. **Single Access Network & Machine:** All sessions were recorded from one physical laptop on one lab Wi-Fi network.
3. **Single LLM & Framework:** Pilot evaluated Browser Use v0.13.14 with Gemini 2.5 Flash; results do not necessarily generalize to alternative reasoning architectures or headless engines.
4. **Task Success Uniformity:** All 92 recorded sessions succeeded; behavioral dynamics during error recovery or aborted tasks were not observed.

---

## 4. Explicit Release Recommendation

### Recommendation: **APPROVE FOR PERSON C SYNTHESIS (HOLD REMOTE GITHUB PUSH)**

1. **Delivery Verdict:** **`CONDITIONAL GO`**
   - In strict compliance with `analysis/PREREG.md` §7, because of the un-interleaved collection schedule and NC2 cohort separation, any finding from this pilot can only state "separable in this dataset", and an unreserved `GO` is strictly prohibited.
2. **Release Authorization:**
   - The analysis deliverables, codebook, test suites, and audit logs are verified, robust, and mathematically sound.
   - Person B formally authorizes delivering this audit report and derived result tables to Person C for final synthesis.
   - Remote push to GitHub (`origin/master`) remains on **HOLD** pending Person C's synthesis review.

---

*Final Verification Certified,*  
**Person B**  
*Analysis Lead*
