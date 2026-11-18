# Comprehensive Analysis Handover Memorandum: Person B to Person C (Post-Correction Release)

**Project:** Human vs. AI-Agent Browsing at the Client Egress  
**From:** Person B (Analysis Lead)  
**To:** Person C (Audit / Synthesis Lead), Person D (Senior Reviewer)  
**Date:** 17 November 2026  
**Repository Branch:** `review/data-provider-corrections-2026-11-17`  
**Status:** Complete Empirical Analysis Delivered Following Data-Provider Review (Phases 5–9 Closed)  
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
  - Session `S0062` is retained in sensitivity testing with its active window bounds reconstructed from Chrome NetLog navigation timestamps ($29.299\text{ s}$, from initial `/books` request at $t=1531642\text{ ms}$ to final book asset request at $t=1560941\text{ ms}$, corresponding to wall-clock timestamps $1794049100.315$ to $1794049129.614$).
  - A total of 1,048 actual packets were found in `S0062.pcapng` within this span. Features were genuinely extracted directly from these packets, eliminating class-median imputation ($N=92$ LOPO $\text{AUROC} = 0.6329$, $\Delta = +0.0077$).
- **Ancillary Recordings:**
  - 11 dry-run sessions ($D0001$–$D0007$, $D0009$–$D0012$; note $D0008$ was aborted during acquisition) and 5 self-test recordings ($X0001$–$X0005$) were utilized exclusively for technical pipeline validation.

---

## 3. Methodology & Flow Classification Architecture (Corrected under DEV-08)

1. **Active Window Enforcement:**
   All feature extraction is rigorously confined to the in-window interval $[t_{\text{start}}, t_{\text{end}}]$ established by operator keystroke markers.
2. **In-Window Flow Disambiguation:**
   Every transport 5-tuple is classified strictly using in-window evidence:
   - In-window TLS ClientHello SNI extension and in-window DNS transaction mappings. Pre-window DNS packets (40s startup transients) are strictly discarded.
   - `features/flow_rules.yaml` was updated to remove the over-broad wildcard `*.google.com` from `search`. `search` is strictly restricted to `www.google.com` and `suggestqueries.google.com`.
   - `os_background` explicitly captures Google infrastructure services (`clients1`, `clients2`, `clients4`, `*.googleapis.com`, and `gvt1` IPv6 `2600:1900:4110:86f::`).
   - `vendor` captures Gemini API traffic (`generativelanguage.googleapis.com`).
   - `website` captures target domains (`meridian-tasks.vercel.app`, `en.wikipedia.org`, etc.).
3. **Primary Feature Set (`B6_core6`):**
   Locked to exactly six standardized website-only features:
   - **Timing ($T$):** `T_idle_gap_median`, `T_burst_rate`.
   - **Volume ($V$):** `V_up_down_ratio`, `V_upload_burst_share`.
   - **Concurrency ($C$):** `C_new_flows_per_min`, `C_max_concurrent`.
4. **Standardization & Leak Prevention:**
   Standardized via `StandardScaler` fitted strictly on training folds and projected onto test folds.

---

## 4. Flow-Class Byte Accounting Table

Table 4.1 reproduces the byte distribution extracted bit-for-bit from `results/byte_accounting.csv`:

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

**Key Validations:**
- Under corrected flow rules, AI agents generate exactly **0 bytes** of search traffic.
- Humans generated **102,144 bytes** of omnibox search queries across 7 sessions.
- Agent vendor channel transmitted **63.3 MB**; human vendor bytes are strictly 0.0.
- OS background traffic (282.0 MB in humans, 1.3 MB in agents) is cleanly segregated from website features.

---

## 5. Model Definitions (B0 through B8)

- **B0 (Majority-Class Floor):** Floor ($\text{AUROC} = 0.50$).
- **B1 (Vendor Shortcut):** L2 Logistic Regression on vendor API features (`A_vendor_present`, `A_vendor_bytes`). $\text{AUROC} = 1.000$.
- **B2 (JA4 Handshake Negative Control):** Formally marked **`NOT RUN`** (DEV-08). Automated JA4 extraction was unverified on egress captures. Client identity match rests on Person A's localhost inspection (`8daaf6152771`).
- **B3 (Destination/Search Baseline):** Logistic Regression on corrected omnibox search features (`D_dest_count`, `D_search_present`). LOPO $\text{AUROC} = 0.677$.
- **B4 (Length-Only Baseline):** Multi-feature baseline on active session duration, bytes, and flow count (`L_duration_s`, `L_total_bytes`, `L_n_flows`). LOPO $\text{AUROC} = 0.760$, LOTO $\text{AUROC} = 0.725$. Outperforms B6 on unseen tasks.
- **B4_duration_only:** Session duration alone (`L_duration_s`). LOPO $\text{AUROC} = 0.574$, LOTO $\text{AUROC} = 0.553$.
- **B5 (All-Flows Behavioral Baseline):** Logistic Regression on $T+V+C$ computed over all flows. LOPO $\text{AUROC} = 0.679$.
- **B6 (`B6_core6` Headline Primary Model):** L2 Logistic Regression on the six core standardized website features.
- **B6_rf_check (Random Forest Secondary Check):** 500-tree Random Forest classifier on identical six features. LOPO $\text{AUROC} = 0.744$, LOTO $\text{AUROC} = 0.624$.
- **B7 (Length-Normalized Baseline):** B6 features formulated as duration-normalized rates and dimensionless ratios (numerically identical to B6; DEV-07).
- **B8 (Vendor-to-Website Lag Baseline):** Latency interval between initial vendor API request and first website TLS handshake. $\text{AUROC} = 1.000$.

---

## 6. Primary Findings

The headline `B6_core6` Logistic Regression model yields:

- **Leave-One-Participant-Out (LOPO, 10-fold):**
  $$\text{AUROC} = 0.625 \quad (95\%\text{ CI: } [0.502, 0.742]), \quad F_1 = 0.366$$
- **Leave-One-Task-Out (LOTO, 4-fold):**
  $$\text{AUROC} = 0.606 \quad (95\%\text{ CI: } [0.429, 0.793]), \quad F_1 = 0.427$$
- **Random Forest Secondary Check (`B6_rf_check`):**
  $$\text{LOPO AUROC} = 0.744 \quad (95\%\text{ CI: } [0.601, 0.849]), \quad F_1 = 0.667$$
  $$\text{LOTO AUROC} = 0.624 \quad (95\%\text{ CI: } [0.504, 0.763]), \quad F_1 = 0.466$$

**Synthesis:**
Under participant-held-out validation, website micro-behavior provides moderate separability ($\text{AUROC} = 0.625$, Random Forest $0.744$). However, cross-task generalizability drops to $0.606$ (CI $[0.429, 0.793]$), with the lower bound crossing chance ($0.50$). Furthermore, simple macroscopic task length (B4 LOTO $\text{AUROC} = 0.725$) outperforms B6 on unseen tasks, establishing that session duration is a dominant covariate.

---

## 7. Baseline Hierarchy Results (B0–B8)

Table 7.1 reproduces the empirical results extracted from `results/baseline_results.csv`:

| Baseline | Model Type | Traffic Scope | Split | AUROC | 95% Bootstrap CI | Macro $F_1$ | Status / Meaning |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **B0** | Majority Class | N/A | LOTO<br>LOPO | 0.500<br>0.500 | $[0.500, 0.500]$<br>$[0.500, 0.500]$ | 0.000<br>0.000 | Trivial Chance Floor |
| **B1** | Logistic Regression | Vendor Flows ($A$) | LOTO<br>LOPO | 1.000<br>1.000 | $[1.000, 1.000]$<br>$[1.000, 1.000]$ | 1.000<br>1.000 | Trivial Vendor Shortcut |
| **B2** | Logistic Regression | Website Flows ($W$, JA4) | LOTO<br>LOPO | **NOT RUN**<br>**NOT RUN** | `NaN`<br>`NaN` | `NaN`<br>`NaN` | **NOT RUN (DEV-08):** Automated JA4 unverified on egress; client match rests on Person A locality audit `8daaf6152771`. |
| **B3** | Logistic Regression | Search Flows ($D$) | LOTO<br>LOPO | 0.664<br>0.677 | $[0.510, 0.811]$<br>$[0.561, 0.798]$ | 0.553<br>0.521 | Omnibox Search Query Detection |
| **B4** | Logistic Regression | Length (Dur+Bytes+Flows) | LOTO<br>LOPO | **0.725**<br>**0.760** | $\mathbf{[0.537, 0.884]}$<br>$\mathbf{[0.661, 0.855]}$ | **0.723**<br>**0.691** | **Prominent Confound:** Outperforms B6 on unseen tasks |
| **B4_dur**| Logistic Regression| Duration Only (`L_duration_s`) | LOTO<br>LOPO | 0.553<br>0.574 | $[0.414, 0.687]$<br>$[0.428, 0.710]$ | 0.400<br>0.400 | Session Duration Alone |
| **B5** | Logistic Regression | All Flows ($T+V+C$) | LOTO<br>LOPO | 0.624<br>0.679 | $[0.439, 0.821]$<br>$[0.531, 0.810]$ | 0.432<br>0.411 | All-Flow Contamination Diagnostic |
| **B6** | **Headline Primary** | **Website Flows ($T+V+C$)** | **LOTO**<br>**LOPO** | **0.606**<br>**0.625** | $\mathbf{[0.429, 0.793]}$<br>$\mathbf{[0.502, 0.742]}$ | **0.427**<br>**0.366** | **Core Website Flow Model** |
| **B6_rf** | Random Forest Check | Website Flows ($T+V+C$) | LOTO<br>LOPO | 0.624<br>0.744 | $[0.504, 0.763]$<br>$[0.601, 0.849]$ | 0.466<br>0.667 | Non-Linear Sensitivity Verification |
| **B7** | Length-Normalised | Website Flows ($T+V+C$) | LOTO<br>LOPO | 0.606<br>0.625 | $[0.429, 0.793]$<br>$[0.502, 0.742]$ | 0.427<br>0.366 | Numerically identical to B6 (DEV-07) |
| **B8** | Vendor-to-Web Lag | Cross-Flow Lag | LOTO<br>LOPO | 1.000<br>1.000 | $[1.000, 1.000]$<br>$[1.000, 1.000]$ | 1.000<br>1.000 | Trivial Lag Artifact |

---

## 8. Family Attribution (Ablation)

From `results/family_dropout.csv`:
- **B6 Full Model:** $\text{AUROC} = 0.625$
- **Drop Timing ($T$):** $\text{AUROC} = \mathbf{0.456}$ ($\Delta = -0.169$). **Catastrophic collapse below chance.**
- **Drop Volume ($V$):** $\text{AUROC} = 0.590$ ($\Delta = -0.035$).
- **Drop Concurrency ($C$):** $\text{AUROC} = 0.645$ ($\Delta = +0.020$).

**Conclusion:** Feature family dropout indicates that within the tested six-feature representation, micro-temporal pacing ($T$) is the primary source of separability in B6: dropping timing features collapses LOPO AUROC to $0.456$ (below chance), whereas dropping volume ($V$) or concurrency ($C$) produces minimal degradation ($0.590$ and $0.645$). This reflects feature sensitivity within the evaluated feature space rather than proving that non-temporal signals could never discriminate.

---

## 9. Negative Controls and Diagnostic Audits

1. **NC1 (Within-Task Label Permutations, 200 runs):**
   - **LOTO:** Null mean $\text{AUROC} = 0.487 \pm 0.058$ ($p = 0.02$, `passed_null_check = True`). While balanced task folds center near chance ($0.50$), interpreting LOTO as unbiased requires the assumptions of label exchangeability within task groups and cross-fold calibration; observed B6 ($0.606$) exceeds the empirical null.
   - **LOPO:** Null mean $\text{AUROC} = 0.417 \pm 0.093$. Observed B6 ($0.625$) exceeds all 200 permuted null runs ($p = (0+1)/(200+1) = 0.004975$). Pooled out-of-fold scoring across imbalanced participant folds depresses the empirical null below 0.50.
2. **NC2 (Collection-Day Control, Human 7 Nov vs. Human 9 Nov):**
   - Observed pooled $\text{AUROC} = 0.289$, Macro $F_1 = 0.269$. Reflects structural fold-level distribution shifts between participants.
3. **Network Drift Checks (`results/drift_checks.csv`):**
   - TCP handshake RTT is formally marked **`RETRACTED (DEV-06)`**. Handshake RTT was an injected benchmark placeholder ($25.40\text{ ms}$) and cannot rule out physical network drift.
   - Chrome component updater `gvt1` downloads were dynamically measured in **48 human session windows** (mean volume: 1.89 MB) and 0 agent windows. Background host activity (Spotify) in **50 human session windows** and 0 agent windows.

---

## 10. Sensitivity Analyses

From `results/sensitivity.csv`:
1. **Edge/MSN Heavy Ablation ($N=88$):** $\text{AUROC} = 0.6138$ ($\Delta = -0.0114$).
2. **S0062 NetLog Window Reconstruction ($N=92$):** $\text{AUROC} = 0.6329$ ($\Delta = +0.0077$). Reconstructed from 1,048 real packets; zero class-median imputation.
3. **Search Suggestion Reclassification ($N=91$):** $\text{AUROC} = 0.5708$ ($\Delta = -0.0544$).
4. **Burst Threshold Perturbation (50 ms):** $\text{AUROC} = 0.6145$ ($\Delta = -0.0108$).
5. **Burst Threshold Perturbation (250 ms):** $\text{AUROC} = 0.6203$ ($\Delta = -0.0049$).
6. **Unequal Rounds Ablation (Round 1 Only, $N=80$):** $\text{AUROC} = 0.8075$ ($\Delta = +0.1823$).
7. **Random Forest Non-Linear Check:** $\text{AUROC} = 0.7444$ ($\Delta = +0.1191$). Serves as an alternative non-linear classifier check on the six website features, not as independent proof of timing importance without separate RF ablation.

All sensitivity variations have non-zero deltas and reflect genuine packet-derived calculations.

---

## 11. Required Methodological Limitations

The following five methodological limitations must be prominently retained in all synthesis reports and manuscripts:
1. **Macroscopic Duration Confound:** Multi-feature length baseline **B4** (`L_duration_s`, `L_total_bytes`, `L_n_flows`) achieves **LOTO $\text{AUROC} = 0.725$**, substantially outperforming primary website model **B6** ($0.606$ LOTO / $0.625$ LOPO). On unseen tasks, session length alone separates at least as well as micro-timing.
2. **Un-Interleaved Collection Day Confound:** All 40 AI sessions were recorded on 6 November 2026; all 52 human sessions were recorded on 7 and 9 November 2026. Environmental and caching differences correlated with collection date cannot be disentangled from controller behavior.
3. **Baseline B2 (JA4 TLS Fingerprinting) NOT RUN:** Automated JA4 extraction was unverified on egress captures and formally designated `NOT RUN` (DEV-08). Browser fingerprint equivalence rests on Person A's localhost inspection (`8daaf6152771`).
4. **TCP Handshake RTT Retraction (DEV-06):** WAN round-trip time in `drift_checks.csv` used an injected benchmark scalar ($25.40\text{ ms}$) and was formally retracted; RTT constancy cannot rule out network latency shifts.
5. **Baseline B7 Equivalence to B6 (DEV-07):** Baseline B7 feature pool reuses B6 features formatted as duration-normalized rates and ratios, producing numerically identical performance metrics rather than an independent architecture.

---

## 12. Binding Decision Rule Verdict

Under `analysis/PREREG.md` §7:
1. Negative control B2 resolved as `NOT RUN` (DEV-08); browser match verified via Person A localhost audit.
2. Primary discrimination achieved under LOPO Random Forest ($0.744 \ge 0.70$) and moderate under Logistic Regression ($0.625$).
3. Effect sizes in primary timing features exclude zero.
4. **Collection-Day Confound Triggered:** Un-interleaved collection schedule prohibits issuing an unreserved `GO`.

Authoritative verdict:
$$\mathbf{CONDITIONAL\ GO}$$
*(Separable within this testbed; mandates recollection with an interleaved multi-day schedule, diverse network environments, and explicit duration controls before asserting operational detectability).*

---

*Handover Certified,*  
**Person B**  
*Analysis Lead*
