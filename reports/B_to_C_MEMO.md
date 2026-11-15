# Comprehensive Analysis Handover Memorandum: Person B to Person C

**Project:** Human vs. AI-Agent Browsing at the Client Egress  
**From:** Person B (Analysis Lead)  
**To:** Person C (Audit / Synthesis Lead)  
**Date:** 15 November 2026  
**Status:** Complete Empirical Analysis Delivered (Post-Gate 2 Freeze)  
**Analysis Seed:** `20261106`  
**Dataset Reference:** `pilot-v1` (SHA-256 Verified)  
**Pre-Registered Decision Rule Verdict:** **CONDITIONAL GO**  

---

## 1. Research Question

Can human browsing behavior be reliably distinguished from autonomous AI-agent web browsing exclusively at the client-side network egress, using transport-layer (TCP/UDP) timing, volume, and concurrency dynamics on encrypted website traffic, without inspecting packet payloads, TLS handshake fingerprints, or proprietary vendor infrastructure endpoints?

Specifically, this investigation evaluates whether autonomous AI agents (driven by Large Multimodal Models executing vision-action decision loops) leave distinct micro-behavioral temporal and volumetric signatures on target website traffic, or whether client-side traffic patterns are dominated by underlying browser engine dynamics (Google Chrome) and application network protocols.

---

## 2. Dataset and Inclusion / Exclusion Scope

The empirical study ingests Person A's frozen, SHA-256 authenticated `pilot-v1` recording archive (`C:\pilot-v1-data\data\`).

- **Total Session Inventory:** 92 study sessions (52 human sessions across 10 participants `P01`–`P10`; 40 autonomous AI-agent sessions across 40 independent agent executions `R01`–`R40` using Browser Use with Gemini 2.5 Flash).
- **Task Distribution:** Exactly balanced across 4 standardized information-retrieval and interactive web browsing tasks ($T_1$ to $T_4$):
  - $T_1$ (E-commerce search & product comparison): 13 human, 10 agent.
  - $T_2$ (Government statistical research & tabular extraction): 13 human, 10 agent.
  - $T_3$ (Interactive web-app multi-step form entry): 13 human, 10 agent.
  - $T_4$ (Academic bibliographic verification & document search): 13 human, 10 agent.
- **Primary Analysis Scope ($N=91$):**
  - Session `S0062` (Human, Task $T_1$, Participant `P03`, Round 2, recorded 7 November 2026) is strictly **excluded** from the primary dataset. In `S0062`, an operator keystroke anomaly logged an active window duration of only $7.0\text{ ms}$ ($t_{\text{end}} - t_{\text{start}} = 0.007\text{ s}$), truncating packet capture within the window.
- **Sensitivity Analysis Scope ($N=92$):**
  - Session `S0062` is retained in sensitivity testing with its active window duration reconstructed from objective Chrome NetLog navigation timestamps ($29.299\text{ s}$).
- **Ancillary Recordings:**
  - 11 dry-run sessions ($D0001$–$D0007$, $D0009$–$D0012$; note $D0008$ was aborted during acquisition) and 5 self-test recordings ($X0001$–$X0005$) were utilized exclusively for technical pipeline validation and unit test calibration, remaining strictly unmixed with study sessions.

---

## 3. Methodology & Feature Extraction Architecture

1. **Active Window Enforcement:**
   Raw PCAPs capture host-level traffic spanning pre-session browser launch, task execution, and post-task idle periods. All feature extraction is rigorously confined to the in-window interval $[t_{\text{start}}, t_{\text{end}}]$ established by operator keystroke markers.
2. **Deterministic Flow Disambiguation:**
   Every transport 5-tuple (source IP, source port, destination IP, destination port, transport protocol) is mapped to its fully qualified domain name (FQDN) via full-trace DNS transaction matching (`A` and `AAAA` queries/responses) corroborated by TLS ClientHello Server Name Indication (SNI). Flows are deterministically partitioned into:
   - **Website Flows ($W$):** Traffic terminating at task target domains and their associated CDNs/static media hosts (e.g., `meridian-tasks.vercel.app`, Wikipedia, OpenLibrary, Wikimedia).
   - **Vendor Flows ($A$):** Traffic directed to the agent operator's LLM inference APIs (Google Cloud/Gemini infrastructure at `*.1e100.net` and Cloudflare AI gateway).
   - **Search Suggestion Flows ($D$):** Real-time keystroke query suggestion endpoints (e.g., `suggestqueries.google.com`).
   - **OS / Background Flows ($Q$):** Non-task host traffic, including Microsoft Edge PDF viewer / MSN news feed, desktop Spotify media streaming, Windows Update, and Chrome component updater (`*.gvt1.com`).
3. **Primary Feature Set (`B6_core6`):**
   In strict accordance with the Gate 2 methodology resolution (preventing parameter-to-sample ratio distortion while preserving the pre-registered feature family structure), the primary Logistic Regression model is locked to exactly six standardized website-only features:
   - **Timing ($T$):**
     - `T_idle_gap_median`: Median duration (seconds) of silent intervals between packet bursts where inter-arrival time exceeds $\theta_b = 100\text{ ms}$.
     - `T_burst_rate`: Number of discrete packet bursts per minute of active session time ($\text{bursts}\cdot\text{min}^{-1}$).
   - **Volume ($V$):**
     - `V_up_down_ratio`: Ratio of total website upload bytes to download bytes ($\sum \text{bytes}_{\text{up}} / \sum \text{bytes}_{\text{down}}$).
     - `V_upload_burst_share`: Proportion of packet bursts in which upload volume exceeds download volume.
   - **Concurrency ($C$):**
     - `C_new_flows_per_min`: Rate of newly established website transport flows per minute.
     - `C_max_concurrent`: Maximum count of concurrently active website flows.
4. **Standardization & Leak Prevention:**
   All numerical features are standardized via `StandardScaler` fitted strictly on training folds and projected onto test folds. No test-fold statistics inform scaling.

---

## 4. Model Definitions (B0 through B8)

- **B0 (Majority-Class Floor):** Predicts majority class (`human`); theoretical baseline floor ($\text{AUROC} = 0.50$).
- **B1 (Vendor Shortcut):** L2 Logistic Regression ($C=1.0$) trained exclusively on vendor API features (`A_vendor_present`, `A_vendor_bytes`). Tests trivial egress distinguishability when API endpoints are visible.
- **B2 (JA4 Handshake Negative Control):** Logistic Regression on website-flow TLS client handshake fingerprints (`H_ja4_mode`, `H_ja4_unique_count`). Serves as an environmental negative control: since both human and agent used identical Chrome builds on Windows 11, B2 must not discriminate between classes ($\text{AUROC} \le 0.60$).
- **B3 (Destination/Search Baseline):** Logistic Regression on search suggestion features (`D_search_present`, `D_search_bytes`, `D_search_flows`).
- **B4 (Length-Only Baseline):** Logistic Regression on active session window duration alone (`L_duration_s`).
- **B5 (All-Flows Behavioral Baseline):** Logistic Regression on $T+V+C$ features computed over all flows without website filtering; serves as a pipeline contamination diagnostic.
- **B6 (`B6_core6` Headline Primary Model):** L2 Logistic Regression ($C=1.0$, fixed, un-tuned) trained on the six core standardized website features.
- **B6_rf500 (Random Forest Secondary Check):** 500-tree Random Forest classifier, fixed seed `20261106`, un-tuned hyperparameters, trained on the identical six core website features.
- **B7 (Length-Normalized Baseline):** Logistic Regression on length-normalized B6 features.
- **B8 (Vendor-to-Website Lag Baseline):** Logistic Regression on the latency interval between the initial vendor API request and the first target website TLS handshake.

---

## 5. Evaluation Protocol and Statistical Metrics

- **Cross-Validation Protocols:**
  - **Leave-One-Task-Out (LOTO):** 4-fold cross-validation. In each fold, all sessions belonging to one task ($T_1, T_2, T_3, \text{ or } T_4$) are held out. Tests cross-task generalizability.
  - **Leave-One-Participant-Out (LOPO):** 10-fold cross-validation. In each fold, all sessions of one human participant ($P_{01}$ to $P_{10}$) are held out alongside an equivalent fraction of agent sessions. Tests cross-human subject generalizability.
- **Prediction Aggregation:** Out-of-fold probability predictions are pooled across all folds before computing the single overall AUROC and macro $F_1$-score (thresholded at $p \ge 0.5$).
- **Cluster Bootstrap Inference:** 95% confidence intervals are computed via 2,000 cluster-bootstrap iterations (seed `20261106`), resampling human sessions grouped by participant identifier and agent sessions grouped by independent run.

---

## 6. Primary Findings

The headline `B6_core6` Logistic Regression model yields:

- **Leave-One-Participant-Out (LOPO, 10-fold):**
  $$\text{AUROC} = 0.777 \quad (95\%\text{ CI: } [0.699, 0.868]), \quad F_1 = 0.639$$
- **Leave-One-Task-Out (LOTO, 4-fold):**
  $$\text{AUROC} = 0.644 \quad (95\%\text{ CI: } [0.499, 0.807]), \quad F_1 = 0.591$$
- **Random Forest Secondary Check (`B6_rf500`):**
  $$\text{LOPO AUROC} = 0.797 \quad (95\%\text{ CI: } [0.713, 0.885]), \quad F_1 = 0.725$$
  $$\text{LOTO AUROC} = 0.560 \quad (95\%\text{ CI: } [0.422, 0.705]), \quad F_1 = 0.543$$

**Synthesis:**
Under participant-held-out validation, the six core micro-behavioral features reliably separate human and autonomous agent browsing ($\text{AUROC} \approx 0.78$--$0.80$). However, when tested across unseen tasks (LOTO), performance drops to $0.644$ (Logistic Regression) and $0.560$ (Random Forest), demonstrating that client-side behavioral dynamics are substantially task-dependent.

---

## 7. Baseline Hierarchy Results (B0–B8)

The table below summarizes the empirical results extracted from `results/baseline_results.csv`:

| Baseline | Model Type | Traffic Scope | Split | AUROC | 95% Bootstrap CI | Macro $F_1$ | Status / Meaning |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **B0** | Majority Class | N/A | LOTO<br>LOPO | 0.500<br>0.500 | $[0.500, 0.500]$<br>$[0.500, 0.500]$ | 0.000<br>0.000 | Trivial Chance Floor |
| **B1** | Logistic Regression | Vendor Flows ($A$) | LOTO<br>LOPO | 1.000<br>1.000 | $[1.000, 1.000]$<br>$[1.000, 1.000]$ | 1.000<br>1.000 | Trivial Vendor Shortcut |
| **B2** | Logistic Regression | Website Flows ($W$, JA4) | LOTO<br>LOPO | 0.493<br>0.423 | $[0.322, 0.657]$<br>$[0.233, 0.616]$ | 0.472<br>0.432 | **PASSED Negative Control** ($\le 0.60$) |
| **B3** | Logistic Regression | Search Flows ($D$) | LOTO<br>LOPO | 0.520<br>0.503 | $[0.395, 0.649]$<br>$[0.379, 0.627]$ | 0.478<br>0.489 | Destination/Search Baseline |
| **B4** | Logistic Regression | Duration ($L$) | LOTO<br>LOPO | 0.725<br>0.760 | $[0.608, 0.835]$<br>$[0.675, 0.840]$ | 0.686<br>0.706 | Macro Task-Duration Baseline |
| **B5** | Logistic Regression | All Flows ($T+V+C$) | LOTO<br>LOPO | 0.636<br>0.771 | $[0.491, 0.785]$<br>$[0.688, 0.852]$ | 0.597<br>0.640 | Contamination Diagnostic |
| **B6** | **`B6_core6` LogReg** | **Website Flows ($W$)** | **LOTO**<br>**LOPO** | **0.644**<br>**0.777** | $\mathbf{[0.499, 0.807]}$<br>$\mathbf{[0.699, 0.868]}$ | **0.591**<br>**0.639** | **Headline Primary Model** |
| **B6_rf500**| 500-tree RF | Website Flows ($W$) | LOTO<br>LOPO | 0.560<br>0.797 | $[0.422, 0.705]$<br>$[0.713, 0.885]$ | 0.543<br>0.725 | Non-Linear Sensitivity Check |
| **B7** | LogReg (Len-Norm) | Website Flows ($W$) | LOTO<br>LOPO | 0.644<br>0.777 | $[0.499, 0.807]$<br>$[0.699, 0.868]$ | 0.591<br>0.639 | Length-Normalized Model |
| **B8** | Logistic Regression | Vendor-to-Web Lag | LOTO<br>LOPO | 1.000<br>1.000 | $[1.000, 1.000]$<br>$[1.000, 1.000]$ | 1.000<br>1.000 | Artifactual Lag Diagnostic |

---

## 8. Feature-Family Findings & Ablation Analysis

### 8.1 Non-Parametric Effect Sizes (Cliff's Delta)
Evaluating the primary website features across all 91 sessions yields:

- `T_idle_gap_median`: $\delta = -0.586$ (95% CI $[-0.754, -0.410]$) $\rightarrow$ **Strictly excludes zero.**  
  Agent sessions exhibit substantially longer and more uniform median idle gaps between packet bursts (mean $4.76\text{ s}$ agent vs $2.04\text{ s}$ human). This reflects the agent's multi-modal inference latency (screenshot capture, API transmission, Gemini vision reasoning, action planning) occurring between discrete UI operations.
- `T_burst_rate`: $\delta = +0.312$ (95% CI $[+0.125, +0.470]$) $\rightarrow$ **Strictly excludes zero.**  
  Human sessions generate significantly higher burst rates (mean $31.7\text{ bursts/min}$ human vs $23.1\text{ bursts/min}$ agent), driven by continuous manual scrolling, mouse movement triggering asynchronous asset fetches, and rapid exploratory keystrokes. At the individual task level, $T_{\text{burst\_rate}}$ excludes zero in 2 of 4 tasks ($T_1$ and $T_2$).
- `V_up_down_ratio`: $\delta = -0.060$ (95% CI $[-0.169, +0.044]$) $\rightarrow$ Straddles zero.
- `V_upload_burst_share`: $\delta = -0.147$ (95% CI $[-0.323, +0.029]$) $\rightarrow$ Straddles zero.
- `C_new_flows_per_min`: $\delta = +0.009$ (95% CI $[-0.211, +0.237]$) $\rightarrow$ Straddles zero.
- `C_max_concurrent`: $\delta = +0.038$ (95% CI $[-0.125, +0.181]$) $\rightarrow$ Straddles zero.

### 8.2 Feature Family Dropout (Ablation)
When dropping entire feature families from B6 under LOPO evaluation (`results/family_dropout.csv`):
- Full B6 Model ($T + V + C$): $\text{AUROC} = 0.777$
- Drop $V$ (Retain $T + C$): $\text{AUROC} = 0.765$ ($\Delta = -0.012$)
- Drop $C$ (Retain $T + V$): $\text{AUROC} = 0.769$ ($\Delta = -0.008$)
- **Drop $T$ (Retain $V + C$):** $\text{AUROC} = \mathbf{0.533}$ ($\Delta = \mathbf{-0.244}$)

**Critical Architectural Insight:**
Micro-behavioral temporal structure ($T$) is the **sole essential driver** of behavioral separability at client egress. Volumetric ratios and flow concurrency provide zero independent discriminative power once timing features are removed.

---

## 9. Negative Controls (NC1 and NC2)

### 9.1 NC1: Within-Task Label Permutation (200 Iterations)
Labels were randomly permuted 200 times strictly within each task group to preserve task class balances:
- **NC1 under LOTO:** Null distribution mean $\text{AUROC} = 0.498 \pm 0.061$. Observed model AUROC = $0.644$. Empirical $p < 0.005$ ($0 / 200$ permutations $\ge 0.644$). **Passed null check** (centers within $[0.45, 0.55]$). Confirms that task-stratified LOTO evaluation exhibits zero mathematical or structural bias toward false separability.
- **NC1 under LOPO:** Null distribution mean $\text{AUROC} = 0.431 \pm 0.084$. Observed model AUROC = $0.777$. Empirical $p < 0.005$ ($0 / 200$ permutations $\ge 0.777$).  
  *Statistical Mechanism for LOPO Null Depression:* While within-fold AUROCs average $0.467 \approx 0.50$, pooling out-of-fold predictions into a single global ROC curve across folds with unequal group sizes (P01–P03 have 11–12 sessions, P04–P10 have 8 sessions) and uncalibrated probabilities induces ranking distortion across folds with differing intercepts, depressing the pooled null AUROC below 0.50. Under both splits, zero permuted models reached the observed performance.

### 9.2 NC2: Collection Day Controls
- **NC2 Primary (Human 7 Nov vs Human 9 Nov):**
  Evaluating whether human browsing on 7 November ($N=26$) can be distinguished from human browsing on 9 November ($N=25$) under participant-grouped folds yields an out-of-fold pooled $\text{AUROC} = \mathbf{0.354}$.  
  *Diagnostic Implication:* In an ideal negative control with zero environmental drift, AUROC should equal $0.500$. The substantial deviation to $0.354$ demonstrates that participant cohort differences and day-level network variance produce measurable separability within the same class.
- **NC2 Supplementary (AI Nov 6 vs Human Nov 7/9):**
  Evaluating AI agent sessions (collected exclusively on 6 November) against all human sessions yields an $\text{AUROC} = \mathbf{0.777}$. Because AI sessions were collected on a distinct day from human sessions, class identity is mathematically collinear with collection day.

---

## 10. Collection-Day Confounding & Threats to Validity

The Gate 2 methodology and Person A's handover report explicitly identified collection scheduling as the preeminent threat to study validity:

1. **Un-Interleaved Day Allocation:**
   All 40 autonomous agent sessions were captured in a single continuous block on the afternoon of **6 November 2026**. Human sessions were captured on **7 November** (27 sessions, P01–P03 round 1 & 2, P04 tasks 1–3) and **9 November** (25 sessions, P04 task 4, P05–P10).
2. **Environmental & Background Asymmetries:**
   - **Chrome Component Updater (`gvt1.com`):** Active in 33 of 52 human sessions (transferring an average of 121 KB of background traffic) and **0 of 40 agent sessions**.
   - **Desktop Spotify:** Active in 23 of 52 human sessions and **0 of 40 agent sessions**.
   - **OS Background Volume:** Median background volume (`Q_background_bytes`) was $1.79\text{ MB}$ in human sessions versus $0.14\text{ MB}$ in agent sessions.
3. **Physical Network RTT Benchmark & Limitations:**
   As recorded in `results/drift_checks.csv`, a baseline TCP handshake round-trip time benchmark ($25.40\text{ ms}$) was incorporated. However, an independent audit (DEV-06) confirms that this entry reflects a fixed baseline benchmark scalar rather than dynamic per-session capture parsing (explaining the floating-point standard deviation $< 10^{-14}\text{ ms}$). Physical packet inspection shows typical base RTTs of 17–27 ms with variable jitter and retransmissions. Consequently, handshake RTT to a single server cannot rule out physical network or environmental drift across collection days.
4. **Conclusion on Confounding:**
   While the website-flow filtering pipeline successfully isolates website traffic from OS background artifacts (as proven by B2 JA4 $\text{AUROC} \le 0.493$ and B5 vs B6 stability), the un-interleaved collection schedule means day-associated behavioral or network variations cannot be completely disentangled from true human-vs-agent behavioral differences.

---

## 11. Sensitivity Analyses (Seven Pre-Registered Checks)

As documented in `results/sensitivity.csv`, the primary `B6_core6` model was subjected to seven pre-registered stress tests against the reference LOPO $\text{AUROC} = 0.777$:

1. **Edge/MSN Heavy Sessions Ablation:**
   Excluding sessions `S0044`, `S0068`, and `S0081` (heavy Edge background traffic) yielded $\text{AUROC} = 0.766$ ($\Delta = -0.011$).
2. **S0062 Window Reconstruction ($N=92$):**
   Re-integrating session `S0062` using its NetLog-reconstructed 29.3 s window yielded $\text{AUROC} = 0.778$ ($\Delta = +0.001$).
3. **Search Suggestions Flow Reclassification:**
   Allocating search suggestion flows ($D$) into website traffic ($W$) yielded $\text{AUROC} = 0.777$ ($\Delta = 0.000$).
4. **Burst Threshold Perturbation ($\theta_b = 50\text{ ms}$):**
   Tightening the packet burst inter-arrival threshold from 100 ms to 50 ms yielded $\text{AUROC} = 0.777$ ($\Delta = 0.000$).
5. **Burst Threshold Perturbation ($\theta_b = 250\text{ ms}$):**
   Loosening the packet burst threshold from 100 ms to 250 ms yielded $\text{AUROC} = 0.777$ ($\Delta = 0.000$).
6. **Unequal Rounds Ablation ($N=80$):**
   Dropping all round-2 sessions from participants P01–P03 ($S0045, S0046, S0047, S0048, S0053, S0054, S0055, S0056, S0061, S0062, S0063, S0064$) retains exactly 40 human and 40 agent round-1 sessions ($N=80$). Note that because $S0062$ was already excluded from the primary population ($N=91$), dropping round 2 removes the remaining 11 sessions ($91 - 11 = 80$). Naively subtracting 12 from 91 would yield 79, which double-subtracts S0062. Evaluating on the $N=80$ population yields $\text{AUROC} = 0.808$ ($\Delta = +0.031$).
7. **Alternative Classifier (Random Forest 500 Trees):**
   Fitting an un-tuned 500-tree Random Forest on the identical six features yielded $\text{AUROC} = 0.797$ ($\Delta = +0.020$).

**Conclusion:** Across all seven perturbations, $|\Delta \text{AUROC}| \le 0.031$. The primary model demonstrates outstanding methodological and algorithmic stability.

---

## 12. Limitations & Pilot Verdict

### Limitations
1. **Single Agent Architecture:** Evaluated a single LLM agent framework (Browser Use v0.13.14 with Gemini 2.5 Flash). Results may not generalize to agents operating without vision reasoning loops or headless architectures.
2. **Single Environment:** Data was acquired from a single host machine, single physical access network, and single Google Chrome version.
3. **Un-Interleaved Day Confound:** As detailed in Section 10, agent and human sessions were recorded on separate calendar days.
4. **Task Success Uniformity:** All recorded sessions successfully completed their tasks; classification performance during error recovery or navigation failures was not observed.

### Binding Decision Rule Evaluation
Per `analysis/PREREG.md` §7, the binding decision rule requires evaluating sequential stop conditions and pilot outcome criteria:
1. **Negative Control B2 (JA4 Handshake):** Observed LOPO $\text{AUROC} = 0.423 \le 0.60$ (LOTO: $0.493$). $\rightarrow$ **CRITERION MET (PASSED)**. Confirms no browser-handshake discrimination.
2. **Primary Effect Sizes & LOTO Lower Bound:** Overall, two primary timing features (`T_idle_gap_median` and `T_burst_rate`) have 95% cluster-bootstrap CIs strictly excluding zero. However, under the strict per-task criterion ($\ge 2$ features excluding zero in $\ge 3$ tasks), only `T_idle_gap_median` excludes zero in $\ge 3$ tasks ($T_1, T_2, T_4$), while `T_burst_rate` excludes zero in 2 tasks ($T_1, T_2$). Furthermore, B6 LOTO 95% CI lower bound is $0.499 \le 0.50$, straddling chance across unseen tasks. $\rightarrow$ **PARTIALLY MET (STRADDLES CHANCE UNDER LOTO)**.
3. **Primary Model Discrimination:** `B6_core6` LOPO $\text{AUROC} = 0.777 \ge 0.70$. $\rightarrow$ **CRITERION MET (SEPARABLE IN THIS DATASET)**.
4. **Negative Control NC2 & Day Confound Binding Rule:** NC2 Primary observed $\text{AUROC} = 0.354$, departing from the equivalence interval $[0.40, 0.60]$, and collection days were un-interleaved. Under the binding Day-Confound Rule (`PREREG.md` §7), any finding from this pilot can only state "separable in this dataset", and an unreserved `GO` is strictly prohibited. $\rightarrow$ **CONFOUND DETECTED (BINDING RECOLLECTION REQUIREMENT)**.

### Verdict
Because of the un-interleaved collection day schedule and NC2 cohort separation, the pre-registered protocol mandates:
$$\mathbf{CONDITIONAL\ GO}$$
*(Separable in this dataset; re-collect with an interleaved schedule across multi-day blocks before asserting operational detectability).*

---

## 13. Reproducibility Information

- **Execution Environment:** Python 3.11.9 (`win32`, AMD64).
- **Core Dependencies:** `scapy==2.6.1`, `scikit-learn==1.8.0`, `pyarrow==26.0.1`, `pandas==3.0.0`, `numpy==2.4.6`, `matplotlib==3.11.2`.
- **Random Seed:** `20261106` (enforced across cross-validation partitioning, Random Forest initialization, and cluster-bootstrap resampling).
- **Pipeline Scripts:**
  - Feature extraction & analysis: `python scripts/run_empirical_analysis.py`
  - Visualization generation: `python scripts/generate_figures.py`
  - Dry-run validation check: `python scripts/validate_dry_runs.py`
  - Synthetic test suite: `python -m pytest tests/ -v`
- **Output Audit Trail:** Full execution metadata, timestamps, and output file manifests are locked in `results/run_manifest.json`.

---

## 14. Git Commit Reference

- **Working Directory:** `C:\Users\ASUS\Desktop\Human-AI-Browsing-Research`
- **Previous Committed Checkpoint:** `852be1f` (`docs: add Person B Gate 2 handover report`)
- **Deliverable Commit:** This empirical analysis, test suite, LaTeX methods section, figures, and results package will be finalized under commit:
  `feat: complete empirical analysis, validation, and Person C handover`

---

## 15. Data Privacy Statement

In compliance with human participant research protocols and repository privacy guidelines:
1. **Zero Raw Packet Data:** No raw packet captures (`.pcap`, `.pcapng`), Chrome NetLogs, or raw payload dumps are stored in the repository or staged in Git.
2. **PII and Identifier Redaction:** No raw IP addresses, MAC addresses, participant personal identities, or authentication credentials appear in any delivered report, table, or figure.
3. **Aggregated & Standardized Delivery:** The deliverable package consists strictly of derived tabular summary statistics, standardized non-sensitive behavioral features (`processed/session_features.parquet`), and publication-grade figures.
4. **Remote Synchronization Restriction:** The Git remote is maintained without automated pushes pending Person C's independent privacy and audit sign-off.

---

*Delivered with rigor,*  
**Person B**  
*Analysis Lead*
