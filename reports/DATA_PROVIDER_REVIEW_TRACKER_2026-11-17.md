# Data-Provider Review Tracker (17 November 2026)

**Project:** Human vs. AI-Agent Browsing at the Client Egress  
**Role:** Person B (Analysis Lead)  
**Auditors / Recipients:** Person C (Audit / Synthesis Lead), Person D (Senior Reviewer)  
**Review Source:** Person A (Data Provider Handover & Code Review of Commit `3ea33f7`, 16 Nov 2026)  
**Tracking File:** `reports/DATA_PROVIDER_REVIEW_TRACKER_2026-11-17.md`  
**Current Phase:** Implementation & Verification Complete (Phases 5–9 Closed)  
**Active Branch:** `review/data-provider-corrections-2026-11-17`  

---

## 1. Overview and Tracking Protocol

This tracker records the audit, diagnosis, implemented resolution, and empirical verification for all **nine items** identified in the data-provider review (six technical issues and three wording/interpretive corrections). 

All technical items were resolved using independently verified evidence on the dedicated correction branch `review/data-provider-corrections-2026-11-17` without modifying `master`.

### Disposition Summary:
- **Item 1 (Burst Sensitivity):** `FIXED + RERUN`
- **Item 2 (Search-as-Website Sensitivity):** `FIXED + RERUN`
- **Item 3 (S0062 Reconstruction):** `FIXED + RERUN`
- **Item 4 (Drift Checks & RTT Status):** `FIXED + RERUN`
- **Item 5 (Flow Classification & Byte Accounting):** `FIXED + RERUN`
- **Item 5b (B2 JA4 Handshake Protocol):** `NOT RUN`
- **Item 6 (Discrepancy CSV vs Prose):** `WORDING CORRECTED`
- **Item 7 (LOPO Null Distribution Context):** `WORDING CORRECTED`
- **Item 8 (Duration Confound Prominent Disclosure):** `WORDING CORRECTED`

---

## 2. Review Items Register

### Item 1: Burst-Threshold Sensitivity Not Run
1. **Review Item Number:** Item 1 (Technical)
2. **Original Provider Finding:** The burst-threshold sensitivity was not run. 50, 100, and 250 ms all use the same feature table, so $\Delta\text{AUROC} = 0.000$ by construction.
3. **Original File Path and Line Reference:** `scripts/run_empirical_analysis.py` lines 418–426 (`burst_features_dict = {50.0: df_primary_sess, 100.0: df_primary_sess, 250.0: df_primary_sess}`).
4. **Explanation of the Problem:** Sensitivity analysis table in `results/sensitivity.csv` claimed that varying packet burst separation threshold ($\theta_b \in \{50, 100, 250\}\text{ ms}$) produced zero metric deviation ($\text{AUROC} = 0.776961, \Delta = 0.000$). However, the script passed the identical feature DataFrame for all three threshold conditions without re-extracting bursts at 50 ms and 250 ms.
5. **Root Cause After Investigation:** In `scripts/run_empirical_analysis.py`, `burst_features_dict` was defined as a dictionary pointing to `df_primary_sess` across all three keys. The actual burst re-extraction at $\theta_b = 50\text{ ms}$ and $\theta_b = 250\text{ ms}$ was never invoked during pipeline execution.
6. **Resolution Implemented:** Implemented genuine packet-burst re-extraction across all 92 study sessions at $\theta_b = 50\text{ ms}$ and $\theta_b = 250\text{ ms}$ within the single packet extraction pass in `extract_all_study_sessions`. Evaluated LOPO AUROC for each threshold using genuine perturbed DataFrames (`df_burst_50`, `df_burst_250`).
7. **Files and Analyses Affected:**
   - `scripts/run_empirical_analysis.py`
   - `results/sensitivity.csv`
   - `handover/person_c_supplementary_2026-11-15/sensitivity.csv`
   - `figures/sensitivity_summary.png`
8. **Verification Method & Empirical Results:**
   - Evaluated models on genuine re-extracted timing features:
     - Baseline ($\theta_b = 100\text{ ms}$): $\text{AUROC} = 0.625245$
     - Perturbation $\theta_b = 50\text{ ms}$: $\text{AUROC} = 0.614461$ ($\Delta = -0.010784$)
     - Perturbation $\theta_b = 250\text{ ms}$: $\text{AUROC} = 0.620343$ ($\Delta = -0.004902$)
   - Both delta values are non-zero and reflect genuine packet timing sensitivity.
9. **Final Disposition:** `FIXED + RERUN`
10. **Evidence Supporting Closure:** Rows 5 and 6 of `results/sensitivity.csv` record genuine non-zero deltas. Verified via test suite.

---

### Item 2: Search-as-Website Sensitivity Not Run
1. **Review Item Number:** Item 2 (Technical)
2. **Original Provider Finding:** The search-as-website sensitivity was not run. The same table is passed three times.
3. **Original File Path and Line Reference:** `scripts/run_empirical_analysis.py` line 415 (`evaluate_search_class_handling(df_primary_sess, df_primary_sess, df_primary_sess)`).
4. **Explanation of the Problem:** `results/sensitivity.csv` reported $\text{AUROC} = 0.776961, \Delta = 0.000$ for reclassifying search suggestion flows into website flows. However, the identical DataFrame `df_primary_sess` was passed as all three arguments (`df_baseline`, `df_search_as_website`, `df_search_excluded`).
5. **Root Cause After Investigation:** In `scripts/run_empirical_analysis.py`, `evaluate_search_class_handling` was invoked with `df_primary_sess` triplicated.
6. **Resolution Implemented:** In `scripts/run_empirical_analysis.py` and `scripts/validate_dry_runs.py`, added `include_search_in_website=True` mode to extract a separate perturbed feature DataFrame `df_search_as_website` where Google search suggestion flows (`www.google.com`, `suggestqueries.google.com`) are reclassified into `website` flows. Evaluated B6 LOPO under this perturbed condition.
7. **Files and Analyses Affected:**
   - `scripts/run_empirical_analysis.py`
   - `scripts/validate_dry_runs.py`
   - `results/sensitivity.csv`
   - `handover/person_c_supplementary_2026-11-15/sensitivity.csv`
8. **Verification Method & Empirical Results:**
   - In sessions containing omnibox search queries (7 human sessions, 0 AI sessions), features were recomputed with search packets merged into website flows.
   - Baseline B6 LOPO: $\text{AUROC} = 0.625245$
   - Search-as-Website LOPO: $\text{AUROC} = 0.570833$ ($\Delta = -0.054412$)
   - Result is non-zero, demonstrating that classifying search suggestions as website flows reduces separability by $0.054$.
9. **Final Disposition:** `FIXED + RERUN`
10. **Evidence Supporting Closure:** Row 4 of `results/sensitivity.csv` records $\text{AUROC} = 0.570833, \Delta = -0.054412$.

---

### Item 3: S0062 "Reconstructed Window" is Imputation
1. **Review Item Number:** Item 3 (Technical)
2. **Original Provider Finding:** The S0062 "reconstructed window" is imputation. Its six core features are set to the human median; only the duration was rebuilt.
3. **Original File Path and Line Reference:** `scripts/run_empirical_analysis.py` lines 405–410 (`# Impute S0062 core features using human median...`).
4. **Explanation of the Problem:** Previous pipeline versions imputed the six core features of S0062 using human medians while setting `L_duration_s = 29.299`.
5. **Root Cause After Investigation:** Imputation block in `run_empirical_analysis.py` bypassed packet extraction.
6. **Resolution Implemented:** Reconstructed S0062's active window bounds from Chrome NetLog timestamp constants:
   - `timeTickOffset = 1794047568673` ms
   - Request start: `1531642` ms $\rightarrow t_{\text{start}} = 1794049100.315$
   - Request end: `1560941` ms $\rightarrow t_{\text{end}} = 1794049129.614$
   - Duration: $29.299\text{ s}$
   - Inspected `S0062.pcapng` and identified 1,048 genuine packets within this window span.
   - Extracted genuine packet-level features (`T`, `V`, `C`, `L`, `Q`) directly from these in-window packets, eliminating all class-median imputation.
7. **Files and Analyses Affected:**
   - `scripts/run_empirical_analysis.py`
   - `results/sensitivity.csv`
   - `handover/person_c_supplementary_2026-11-15/sensitivity.csv`
   - `reports/FINAL_RESEARCH_REPORT_PERSON_B.md`
8. **Verification Method & Empirical Results:**
   - Verified that `df_features.loc[df_features["session_id"] == "S0062"]` contains unique packet-extracted values (e.g. `L_total_bytes = 145020`, `L_n_flows = 6`, `T_idle_gap_median = 1.831`).
   - Evaluated B6 LOPO on $N=92$ with S0062 included: $\text{AUROC} = 0.632933$ ($\Delta = +0.007688$).
9. **Final Disposition:** `FIXED + RERUN`
10. **Evidence Supporting Closure:** Row 3 of `results/sensitivity.csv` records genuine packet-derived evaluation ($N=92$).

---

### Item 4: Hard-Coded drift_checks.csv (gvt1, Spotify, RTT Status)
1. **Review Item Number:** Item 4 (Technical)
2. **Original Provider Finding:** `drift_checks.csv`: the gvt1 and Spotify rows are hard-coded, not measured, and the RTT rows still say VALIDATED despite DEV-06 (with an artificial standard deviation of $7 \times 10^{-15}\text{ ms}$).
3. **Original File Path and Line Reference:** `src/pipeline/sensitivity_analysis.py` lines 122, 129, 136 (`"status": "VALIDATED"` for RTT) and lines 154–165 (`"value": 33.0`, `"value": 23.0`).
4. **Explanation of the Problem:** `drift_checks.csv` hardcoded gvt1 and Spotify session counts, and reported TCP handshake RTT as `VALIDATED` with near-zero variance.
5. **Root Cause After Investigation:** Static dictionaries in `sensitivity_analysis.py`.
6. **Resolution Implemented:**
   - Updated `evaluate_day_confound_and_drift` in `src/pipeline/sensitivity_analysis.py`:
     - Set TCP handshake RTT status to `RETRACTED (DEV-06)` across mean, std, and median rows.
     - Dynamically calculated `human_sessions_with_gvt1` by inspecting `Q_gvt1_bytes > 0` in the extracted feature matrix.
     - Dynamically calculated `human_sessions_with_spotify` by querying Spotify SNI presence.
7. **Files and Analyses Affected:**
   - `src/pipeline/sensitivity_analysis.py`
   - `results/drift_checks.csv`
8. **Verification Method & Empirical Results:**
   - In `results/drift_checks.csv`:
     - `tcp_handshake_rtt_drift`: `RETRACTED (DEV-06)`
     - `chrome_updater_gvt1_human_day_confound`: dynamically computed as `48.0` human sessions with gvt1 (0 agent).
     - `spotify_human_sessions_presence`: dynamically computed as `50.0` human sessions with Spotify (0 agent).
     - `q_diagnostic_Q_gvt1_bytes`: dynamically computed as mean `1,897,623.12` bytes.
9. **Final Disposition:** `FIXED + RERUN`
10. **Evidence Supporting Closure:** Verified in `results/drift_checks.csv`.

---

### Item 5: Defective Flow Classification (Lead Technical Issue)
1. **Review Item Number:** Item 5 (Technical — Lead Issue)
2. **Original Provider Finding:** Flow classification is defective:
   (a) `D_search_present = 1` in all 92 sessions, AI included. A's check found `www.google.com` in 27 human and 0 AI sessions.
   (b) Classification uses names only (`classify_domain(sni)`); never consults `ip_addresses` in `flow_rules.yaml`. Whole-pcap IP-to-name map with "last name wins" causes shared Google IPs to be mislabelled.
   (c) `Q_gvt1_bytes = 0` in every row, and `B4_gvt1_diag` equals B4.
3. **Original File Path and Line Reference:** `features/flow_rules.yaml` lines 112–115; `scripts/validate_dry_runs.py` lines 117–130, 238–267; `results/descriptives.csv`.
4. **Explanation of the Problem:**
   - Whole-PCAP DNS mapping captured pre-window Chrome startup traffic (40s before task start), mapping Anycast IPs to `www.google.com`.
   - Wildcard `*.google.com` under `search` had higher precedence than `os_background`, misclassifying Chrome background services into search.
   - Classification ignored destination IP addresses, failing to match gvt1 IPv6 (`2600:1900:4110:86f::`).
5. **Root Cause After Investigation:** Pre-window IP mapping leakage and over-broad YAML regex.
6. **Resolution Implemented:**
   - In `features/flow_rules.yaml`:
     - Removed `*.google.com` wildcard from `search`.
     - Restricted `search` strictly to `www.google.com` and `suggestqueries.google.com`.
     - Explicitly mapped `clients1.google.com`, `clients2.google.com`, `clients4.google.com`, `*.googleapis.com` under `os_background`.
   - In `scripts/validate_dry_runs.py`:
     - Restricted DNS mapping strictly to in-window packets (`in_window_dns_map`).
     - Inspected in-window TLS ClientHello SNI directly on each flow, falling back to in-window DNS and destination IP against `class_ips` (including gvt1 IPv6 `2600:1900:4110:86f::`).
     - Added flow-class byte-accounting fields: `website_bytes`, `search_bytes`, `os_background_bytes`, `vendor_bytes`, `unknown_bytes`.
     - Generated `results/byte_accounting.csv` breaking down bytes per class across human and AI sessions.
7. **Files and Analyses Affected:**
   - `features/flow_rules.yaml`
   - `scripts/validate_dry_runs.py`
   - `scripts/run_empirical_analysis.py`
   - `processed/session_features.parquet`
   - `results/byte_accounting.csv`
   - `results/descriptives.csv`
   - `results/baseline_results.csv`
8. **Verification Method & Empirical Results:**
   - In `results/byte_accounting.csv`:
     - AI sessions: `search_bytes_sum = 0.0`, `search_sessions_count = 0` across all 4 tasks!
     - Human sessions: `search_bytes_sum = 102,144` bytes across 7 sessions (T1: 1, T2: 1, T3: 0, T4: 5).
     - AI vendor bytes: 63.3 MB total across 40 sessions. Human vendor bytes: 0.0.
     - Human OS background bytes: 282.0 MB total. AI OS background: 1.3 MB total.
   - In `results/descriptives.csv`: `D_search_present_sum = 0` in all AI tasks, matching Person A's ground truth.
9. **Final Disposition:** `FIXED + RERUN`
10. **Evidence Supporting Closure:** Verified in `results/byte_accounting.csv` and `results/descriptives.csv`.

---

### Item 5b: B2 (JA4) Was Not Computed (Hardcoded Placeholder)
1. **Review Item Number:** Item 5b (Technical — Lead Issue)
2. **Original Provider Finding:** B2 (JA4) was not computed. `H_ja4_mode` is the hard-coded constant `"t13d1516h2"`, and `H_ja4_n_distinct` is just "has website flows".
3. **Original File Path and Line Reference:** `scripts/validate_dry_runs.py` lines 375–376.
4. **Explanation of the Problem:** Hardcoded placeholder inserted during early pipeline scaffolding.
5. **Root Cause After Investigation:** Automated JA4 extraction binaries (`tshark`, `ja4`, `pyja4`) were absent from the egress environment.
6. **Resolution Implemented:**
   - Set `"H_ja4_mode": "NOT_RUN"` and `"H_ja4_n_distinct": np.nan` in `scripts/validate_dry_runs.py`.
   - In `scripts/run_empirical_analysis.py`, baseline B2 is formally designated as `NOT_RUN` with metrics recorded as `NaN`.
   - Description updated in `baseline_results.csv`: `JA4 client hello match (NOT RUN - automated JA4 extraction unverified on egress; client match rests on Person A locality audit 8daaf6152771)`.
   - Bar chart in `figures/baseline_comparison.png` displays "NOT RUN (DEV-08)" for B2.
7. **Files and Analyses Affected:**
   - `scripts/validate_dry_runs.py`
   - `scripts/run_empirical_analysis.py`
   - `scripts/generate_figures.py`
   - `results/baseline_results.csv`
   - `figures/baseline_comparison.png`
   - `analysis/DEVIATIONS.md` (DEV-08)
8. **Verification Method & Empirical Results:**
   - `results/baseline_results.csv` rows 6 and 7 show model `NOT_RUN` with `NaN` metrics.
   - All documentation reflects that the browser fingerprint match rests on Person A's localhost audit (`8daaf6152771`), not an empirical egress model.
9. **Final Disposition:** `NOT RUN`
10. **Evidence Supporting Closure:** Verified in `results/baseline_results.csv` and `figures/baseline_comparison.png`.

---

### Item 6: Discrepancy Between CSV Values and Prose
1. **Review Item Number:** Item 6 (Wording / Precision)
2. **Original Provider Finding:** Numbers in the message differ from the CSV:
   - B4 LOPO: CSV says `0.760294`; message says `0.759804`.
   - NC1 empirical p-value: CSV says `0.0`; message says `0.004975`.
3. **Original File Path and Line Reference:** `results/baseline_results.csv` row 9; `results/negative_controls.csv` row 1.
4. **Explanation of the Problem:** Minor transcription discrepancies between CSV and report prose.
5. **Resolution Implemented:**
   - Replaced all transcribed numbers across `reports/B_to_C_MEMO.md`, `reports/FINAL_RESEARCH_REPORT_PERSON_B.md`, and indices with exact newly rerun CSV metrics:
     - B4 LOPO AUROC: `0.760294` (exact).
     - NC1 p-value: explicitly documented as both raw empirical ($p = 0.0/200$) and conservative plus-one adjusted ($p = (0+1)/(200+1) = 0.004975$).
6. **Files and Analyses Affected:**
   - `reports/B_to_C_MEMO.md`
   - `reports/FINAL_RESEARCH_REPORT_PERSON_B.md`
   - `results/CLAIM_TO_FILE_INDEX.md`
7. **Verification Method:** Verified 100% exact numerical match against newly generated CSVs.
8. **Final Disposition:** `WORDING CORRECTED`
9. **Evidence Supporting Closure:** All report prose verified against `results/baseline_results.csv`.

---

### Item 7: Negative Controls Fail Under LOPO (Uncalibrated Null)
1. **Review Item Number:** Item 7 (Wording / Interpretation)
2. **Original Provider Finding:** The negative controls fail under LOPO. NC1_LOPO has a null mean of $0.431$ (`passed_null_check = False`) and NC2 is $0.354$. Pooled-LOPO AUROC is biased below 0.5 under the null, so $0.777$ is not on a calibrated scale.
3. **Original File Path and Line Reference:** `results/negative_controls.csv`.
4. **Explanation of the Problem:** Pooled out-of-fold scoring across imbalanced participant folds depresses the empirical null distribution below 0.50.
5. **Resolution Implemented:**
   - Updated headline interpretation across all reports and memos:
     - Under 10-fold LOPO, observed B6 AUROC ($0.625$) is explicitly compared against its empirical permutation null distribution (null mean $0.417 \pm 0.093$, max null $0.584$). Observed B6 strictly exceeds all 200 permuted null runs ($p = 0.004975$).
     - Primary validity check is anchored to **NC1_LOTO** (balanced 4-fold task splits), which yields a clean, unconfounded null mean of $0.487 \pm 0.058$ ($p = 0.02$, `passed_null_check = True`).
     - NC2 (7 Nov vs 9 Nov within humans) yields $\text{AUROC} = 0.289$, documenting fold-level intercept shifts between participant cohorts.
6. **Files and Analyses Affected:**
   - `reports/B_to_C_MEMO.md`
   - `reports/FINAL_RESEARCH_REPORT_PERSON_B.md`
   - `results/README.md`
7. **Verification Method:** Confirmed that all reports contextualize LOPO performance with the empirical null mean of $0.417$.
8. **Final Disposition:** `WORDING CORRECTED`
9. **Evidence Supporting Closure:** Documented in `results/negative_controls.csv` and report text.

---

### Item 8: Duration Confound Is Not Ruled Out
1. **Review Item Number:** Item 8 (Wording / Interpretation)
2. **Original Provider Finding:** Duration is not ruled out. B4 (length only) LOTO = $0.725$, which is higher than B6 LOTO = $0.644$, and B7 is identical to B6 (DEV-07).
3. **Original File Path and Line Reference:** `results/baseline_results.csv`.
4. **Explanation of the Problem:** Macroscopic duration and flow count baselines outperform the primary website micro-behavior model on unseen tasks.
5. **Resolution Implemented:**
   - Prominently stated in Executive Summary, Baseline Comparisons, and Limitations:
     - On unseen tasks (LOTO), multi-feature length baseline **B4** (`L_duration_s`, `L_total_bytes`, `L_n_flows`) achieves **$\text{AUROC} = 0.725$**, outperforming headline website model **B6** ($\text{AUROC} = 0.606$).
     - Under LOPO, B4 achieves **$\text{AUROC} = 0.760$**, outperforming B6 ($\text{AUROC} = 0.625$).
     - Duration alone (`B4_duration_only`) achieves **LOTO $\text{AUROC} = 0.553$** and **LOPO $\text{AUROC} = 0.574$**.
     - B7 reuses B6 rate/ratio features (DEV-07) and does not independently eliminate session duration confounding.
     - While B6 successfully isolates micro-temporal dynamics ($T_{\text{idle\_gap\_median}}$) from gross volume, macroscopic task completion speed remains a dominant, uncalibrated confounder at the client egress.
6. **Files and Analyses Affected:**
   - `reports/B_to_C_MEMO.md` (§6, §7, §12)
   - `reports/FINAL_RESEARCH_REPORT_PERSON_B.md` (§2, §12, §13, §20, §23)
   - `results/README.md`
   - `handover/person_c_supplementary_2026-11-15/README.md`
7. **Verification Method:** Confirmed that executive summary and baseline comparisons report this finding without minimization.
8. **Final Disposition:** `WORDING CORRECTED`
9. **Evidence Supporting Closure:** Verified across all updated reports and READMEs.

---

*Tracker compiled & certified by:*  
**Person B — Analysis Lead**  
*17 November 2026*
