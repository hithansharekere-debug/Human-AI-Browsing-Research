# Preregistration Plan (analysis/PREREG.md)

**Title:** Statistical Comparison of Human vs. AI-Agent Browsing at Client Egress  
**Lead Analyst:** Person B (Analysis Lead)  
**Downstream Reviewers:** Person C, Person D  
**Status:** Pre-Gate 2 Specification (Reconciled with Authoritative Handover & Blueprint)  
**Dataset Scope:** 92 Sessions (52 Human across 10 participants, 40 Agent across 4 matched tasks)  
**Primary Analysis Population:** 91 sessions (excluding $S0062$ due to premature marker defect; retained for sensitivity analysis)

---

## 1. Study Design & Data Collection Summary

- **Apparatus:** Single test laptop, Windows 11 (build 26200), dedicated user account `StudyPC`, Google Chrome 157.0.8103.38 with identical DevTools port (`--remote-debugging-port=9222`), fresh copy of golden profile per session, MediaTek MT7921 Wi-Fi adapter on `lab-wifi`.
- **Controllers:**
  - Human ($n = 52$): 10 adult volunteers ($P01–P10$). $P01–P03$ completed 2 rounds (8 sessions each); $P04–P10$ completed 1 round (4 sessions each).
  - AI Agent ($n = 40$): Browser Use 0.13.14 driving Chrome via CDP using Google `gemini-3.5-flash-lite`. 10 repetitions per task. Interventions = 0.
- **Tasks:** Four checkable browsing tasks:
  - T1: Book catalogue lookup & category browsing (`meridian-tasks.vercel.app/books`)
  - T2: Wikipedia 3-hop navigation (`en.wikipedia.org`)
  - T3: Shop product comparison (`meridian-tasks.vercel.app/shop`)
  - T4: Form filling & submission with synthetic data (`meridian-tasks.vercel.app/form`)
- **Analysis Window:** Precise interval between hardware-timed START and END UDP marker packets to `192.0.2.1:9`. Markers and setup/shutdown traffic are excluded.
- **Unit of Analysis:** The session is the unit. Splitting, training, or testing by individual flow or packet is strictly prohibited.

---

## 2. Facts Known Before Analysis (Handover Part 5 & Blueprint §6.5)

The following empirical findings were established during pre-analysis data hygiene checks and are preregistered as prior knowledge:

### F1. Chrome Component Updater Day Confound
- **Evidence:** Fresh profiles downloaded ~5.3 MB from `edgedl.me.gvt1.com` (`*.gvt1.com`, IPv6 `2600:1900:4110:86f::`) in every human session on 7 and 9 Nov (in-window in 33 of 52 sessions), and in 0 agent sessions on 6 Nov.
- **Effect:** If unclassified, $gvt1$ massively contaminates volume and timing features, making human and agent sessions trivially separable due to Chrome component updating rather than browsing behavior.
- **Handling:** Classified as `os_background` in `flow_rules.yaml`. Excluded entirely from website flows for headline model $B6$. Volume tracked in diagnostic column `Q_gvt1_bytes`. $B4$ and $B5$ reported with and without $gvt1$ to quantify impact.

### F2. Google Search Suggestions in Human Sessions
- **Evidence:** `www.google.com` / `suggestqueries.google.com` appeared in 27 human sessions (T1: 8, T2: 7, T3: 3, T4: 9) and 0 agent sessions.
- **Effect:** Humans naturally typed search queries into Chrome's omnibox, whereas the automated agent navigated directly by clicking or passing full URLs.
- **Handling:** `www.google.com` and `*.google.com` assigned dedicated class `search` (Family D). Excluded from website-flow features for $B6$. Evaluated in shortcut baseline $B3$. Reported descriptively as a human behavioural phenomenon ("humans use the omnibox"), not as a primary traffic detector.

### F3. Almost All Traffic is IPv6
- **Evidence:** About 98% of the bytes inside the window are IPv6, for both classes.
- **Effect:** Filtering on `ip.*` only would silently drop almost everything.
- **Handling:** Use `ip` and `ipv6` in every filter and field list; verify that NFStream keeps IPv6 flows (default behavior). Marker packets are IPv4 (`ip.dst==192.0.2.1`).

### F4. Corrected Idle-Baseline Numbers
- **Evidence:** Handover measurements showed that typical background of 100–170 KB/min was only true for 6 Nov; subsequent days exhibited distinct background traffic:

| ID | Day | KB/min in window | What dominates | Use as baseline? |
|---|---|---|---|---|
| I0001 | 6 Nov | 1,164 | Chrome download on first idle run, plus NVIDIA and HP software | No (outlier) |
| I0002 | 6 Nov | 127 | msn, Chrome client services, Office | Yes (matches agent day) |
| I0003 | 6 Nov | 57 | Same | Yes (matches agent day) |
| I0004 | 7 Nov | 12,910 | Windows Update / Delivery Optimization (`14.102.231.202`) | No (outlier) |
| I0005 | 7 Nov | 1,206 | The gvt1 component download (5.3 MB, F1) | Yes, as a "human-day" baseline |
| I0006 | 9 Nov | 1,259 | The gvt1 component download (F1) | Yes, as a "human-day" baseline |
| I0007 | 9 Nov | 25,616 | Windows Update / Delivery Optimization (`14.102.231.203`, `*.delivery.mp.microsoft.com`) | No (outlier) |
| I0008 | 9 Nov | 1,209 | The gvt1 component download (F1) | Yes, as a "human-day" baseline |

- **Effect:** Demonstrates that unmanaged OS and component update traffic creates apparent day differences if not filtered.
- **Handling:** Once the `gvt1` flow is removed, 7 and 9 Nov idles fall to about 150–190 KB/min, close to 6 Nov (~127 KB/min). This serves as evidence that the background filter makes days comparable. Do not use outliers (I0001, I0004, I0007) to set thresholds.

### F5. Ten Known Collection Issues from 9 Nov Report
The ten known issues from Person A's 9 Nov collection report remain in effect and are addressed as follows:
1. **Issue 1 (Day Confound):** Agent and human sessions are on different days (agents 6 Nov 14:35–16:41 IST; humans 7 Nov 09:56–16:40 IST and 9 Nov 17:31–18:33 IST). The schedule was not followed. *Action:* Negative control NC2, time-of-day overlap analysis, TCP handshake RTT drift check, and background bytes by day.
2. **Issue 2 (Unequal Rounds):** P01–P03 completed 2 rounds; P04–P10 completed 1 round. *Action:* Participant-clustered bootstrap and 10-fold LOPO; compare round 1 vs. round 2 for P01–P03.
3. **Issue 3 (S0062 Window Duration):** S0062 (P03, T1, round 2) has a window of 0.007 s due to premature ENTER keypress. *Action:* Exclude from primary analysis via `label_corrections.csv`; sensitivity analysis recomputes window from NetLog first/last Meridian request.
4. **Issue 4 (Edge, Bing, MSN Background):** Heavy in S0044 (P01 T4), S0068 (P04 T3), S0081 (P08 T4) (guide PDF open in Edge); lighter in 16 more sessions. *Action:* Classify `bing.com`, `msn.com`, `edge.microsoft.com`, `microsoftonline.com` as `os_background`; report B6 with and without the 3 heavy sessions.
5. **Issue 5 (Idle Outliers):** I0001, I0004, I0007. *Action:* Do not use them to set thresholds.
6. **Issue 6 (Upstream Validation):** Upstream validation not done (`upstream/` is empty). *Action:* Acknowledged as a limitation for Person C and Person D.
7. **Issue 7 (Datadog in Dry-Run):** Unexplained connection to `http-intake.logs.us5.datadoghq.com` in one dry-run agent capture. *Action:* Label as `vendor` (Family A) if seen; record presence in agent sessions (0 in study sessions).
8. **Issue 8 (100% Task Success):** 100% success on both sides. *Action:* No outcome stratification possible; note as limitation ("tasks may be easy").
9. **Issue 9 (S0010 DuckDuckGo Navigation):** S0010 (agent, T2) used DuckDuckGo search during task. *Action:* Destinations differ (Family D); retain and note in analysis.
10. **Issue 10 (Gemini Quota Errors):** HTTP 429/503 errors occurred in early test runs only, none in study sessions. *Action:* None required.

---

## 3. Preregistered Baselines (B0–B8)

Exactly restores the authoritative baseline definitions from Blueprint §6.3 and Handover Step 8:

| ID | Feature Set Scope | Expected Outcome | Role & What It Tells You |
|---|---|---|---|
| **B0** | Majority class | $\text{AUROC} = 0.50$ | Floor baseline. |
| **B1** | Vendor shortcut ($A$ family only) | $\text{AUROC} \approx 1.0$ | The trivial shortcut. Reported to demonstrate awareness. |
| **B2** | JA4 TLS handshake on website flows ($H$ family only) | $\text{AUROC} \approx 0.50$ | **Design check.** If $\text{AUROC} > 0.60$, **STOP AND FIX** (browsers differ). |
| **B3** | Destination/search baseline ($D$ family only) | Task-dependent | Evaluates path differences and search suggestion presence ($F2$). |
| **B4** | Length-only baseline ($L$ family only) | High | Determines whether classification is driven simply by speed/duration. Reported clean and with a separately labeled diagnostic `B4_gvt1_diag` to quantify $F1$ updater impact. |
| **B5** | $T + V + C$ across all flows | Unconstrained | Retained as a shortcut/contamination diagnostic (shows distortion by $F1$ and $F2$). Separately labeled `B5_no_gvt1_diag` evaluates non-gvt1 background. |
| **B6** | **$T + V + C$ on website flows only** ($A, H, D, L, Q$ removed) | **Headline model** | **Primary confirmatory test of micro-behavioral egress separability.** Strictly excludes all background and shortcut flows. |
| **B7** | $B6$ with length-normalized features | Invariant | Tests: "Is $B6$ just $B4$ in disguise?" |
| **B8** | Vendor-to-website cross-flow lag only | Separate condition | Evaluates tool-call think time vs human hesitation (cross-flow timing). |

*Note on Q Features:* Features in family $Q$ (`Q_background_bytes`, `Q_gvt1_bytes`, `Q_edge_present`) are monitors/diagnostics only. They are **never** included in any predictive model ($B0\text{--}B8$).

---

## 4. Modeling, Cross-Validation & Metric Specifications

### Model Specification & Frozen B6 Feature Set
- **Primary Model (`B6_core6`):** $L_2$-regularized Logistic Regression ($C = 1.0$, `solver='lbfgs'`, no hyperparameter tuning) trained on **exactly six standardized primary features**:
  1. $T$: `T_idle_gap_median`
  2. $T$: `T_burst_rate`
  3. $V$: `V_up_down_ratio`
  4. $V$: `V_upload_burst_share`
  5. $C$: `C_new_flows_per_min`
  6. $C$: `C_max_concurrent`
- **Methodological Guarantees for B6:**
  - This is the explicit, frozen resolution of the original $\le 6$-feature constraint from Blueprint §6.2 and Handover Step 6.
  - Selected purely a priori on domain coverage and statistical stability, **without reference to study session outcomes or empirical performance**.
  - **No eight-feature Logistic Regression model will be fitted as a primary or secondary model.**
- **Check Model (Random Forest Check):**
  - Evaluated on the **exact same six core features** ($2T + 2V + 2C$).
  - Hyperparameters: 500 trees, `max_features='sqrt'`, fixed seed `20261106`, no tuning.
  - Serves as an algorithmic non-linear consistency check; **never the headline model**.
- **Role of Remaining T/V/C Candidates:**
  - Other candidate features (`T_idle_gap_cv`, `T_idle_gap_entropy`, `T_gap_autocorr_lag1`, `C_quic_share`) are reserved strictly for pre-specified family dropout and sensitivity analyses. They are never added to the primary model.

### Metrics & Resampling
- **Primary Metric:** Area Under the Receiver Operating Characteristic ($\text{AUROC}$) on pooled out-of-fold predictions.
- **Secondary Metric:** $F_1$ score (threshold = 0.50).
- **Confidence Intervals:** 95% cluster-bootstrap confidence intervals computed with **2,000 resamples** (random seed `20261106`).
  - Clusters: Resample the 10 human participants ($P01–P10$) with replacement and the 10 agent repetitions ($rep=1..10$) with replacement; retain all sessions belonging to each chosen cluster.
- **Effect Sizes:** Cliff's $\delta$ per primary feature (overall and per task) with 95% cluster-bootstrap CI.

### Cross-Validation Splits
1. **Random Session Split:** 5-fold stratified by label. Used exclusively as a leakage diagnostic; never reported as headline.
2. **Leave-One-Task-Out (LOTO):** 4 folds. Each test fold contains all sessions for one task (human and agent).
3. **Leave-One-Participant-Out (LOPO):** **10 folds.** Fold $k$ tests on all sessions of human participant $P_k$ plus agent sessions with $rep = k$ (4 sessions, one per task), and trains on the remaining 9 participants and 9 agent reps. No participant or agent rep ever appears in both train and test folds.

---

## 5. Negative Controls & Invariance Checks

1. **NC1 (Within-Task Label Permutation under LOTO and LOPO):**
   - Shuffle controller labels randomly *within each task* independently to preserve task base rates.
   - For all **200 permutations**, the primary $B6$ model is fully refitted and evaluated under both LOTO (4 folds) and LOPO (10 folds).
   - Predictions across folds are pooled to calculate the permutation's overall AUROC.
   - **Pass Criterion:** The empirical null AUROC distribution across the 200 actual model runs must center near $0.50$ (mean $\in [0.45, 0.55]$). If NC1 is far from 0.50, **STOP AT ONCE** (pipeline leakage).
2. **Primary NC2 (Human vs. Human Day Classification):**
   - Human sessions from 7 Nov: label `0` ($n = 27$); Human sessions from 9 Nov: label `1` ($n = 25$).
   - Evaluated on standardized $B6$ website-only features.
   - **Fold Composition & Pooled AUROC:**
     - Evaluated across participant-grouped folds, keeping every participant entirely in either training or test.
     - Predictions are generated exclusively for held-out participants.
     - All held-out predictions are pooled across folds before computing the single overall AUROC. Standalone per-fold AUROCs are never calculated for folds containing only one day class.
   - **Methodological Scope & Caveat:**
     - In this dataset, collection day is completely associated with participant cohort ($P01\text{--}P03$ on 7 Nov vs $P05\text{--}P10$ on 9 Nov).
     - NC2 detects day/cohort-associated separability. It **cannot independently attribute** an observed difference to environmental drift versus between-subject behavioral variance.
   - **Pass Criterion:** Pooled AUROC must center near 0.50 ($[0.40, 0.60]$). If $\text{AUROC} > 0.60$, day/cohort drift is confirmed as an unresolvable confound.
3. **Supplementary NC2 (AI vs. Human Day Diagnostic):**
   - Diagnostic comparing AI on 6 Nov with human sessions across days; separately named and treated strictly as supplementary.

---

## 6. Sensitivity Analyses (Handover Step 11)

All 7 authoritative sensitivity analyses are pre-registered:

1. **Day Confound & Network Drift (`results/drift_checks.csv`):**
   - (a) NC2 evaluation.
   - (b) Time-of-day overlap: 8 human sessions on 7 Nov started after 14:00 IST (matching agent clock hours); report $B6$ effect directions for them vs. other humans.
   - (c) Network drift: TCP handshake RTT ($\text{SYN}\rightarrow\text{SYN/ACK}$) to `meridian-tasks.vercel.app` per session across collection days.
   - (d) Background volume distributions ($Q$ columns) by day.
2. **Unequal Rounds (`results/round_check.csv`):** Compare P01–P03 round 1 vs. round 2 (Cliff's $\delta$). Rerun $B6$ with round 2 sessions dropped.
3. **Edge News Sessions (`results/sensitivity.csv`):** Rerun $B6$ excluding heavy Edge sessions S0044, S0068, S0081.
4. **S0062 Inclusion (`results/sensitivity.csv`):** Rerun $B6$ with S0062 included using window rebuilt from Chrome NetLog.
5. **Search Class Handling (`results/sensitivity.csv`):** Rerun $B6$ and $B3$ with `search` assigned to `website`, then to $D$.
6. **Burst Threshold Perturbation (`results/sensitivity.csv`):** Rerun $B6$ across burst thresholds $\theta_b \in \{50, 100, 250\}\text{ ms}$.
7. **Family Dropout for B5 and B6 (`results/family_dropout.csv`):** Drop one feature family at a time ($T$, $V$, or $C$) from $B5$ and from $B6$ to quantify behavioural drivers.

---

## 7. Stop Conditions & Pilot Decision Rules

### Immediate Stop Conditions (Tell Person A and Person D the same day)
1. **$B2$ (JA4 on website flows) is above 0.60:** Indicates browsers differ.
2. **$NC1$ is far from 0.50:** Indicates pipeline information leakage.
3. **Data Leakage in Splits:** Any session, participant, or task crosses between train and test sets in grouped splits.
4. **Checksum Failure:** Any file fails hash verification against `SHA256SUMS.txt`.

### Pilot Outcome Criteria (Blueprint §6.7)
- **`GO to Full Study`:** Data valid, $B2 \approx 0.50$, $B6$ LOTO AUROC 95% CI lower bound $> 0.50$ (or $\ge 2$ primary features have $|\delta|$ CI excluding 0 in $\ge 3$ tasks), and literature novelty checks clean.
- **`CONDITIONAL GO`:** Data collection valid but CIs straddle chance (use effect sizes for power calculation), OR day confound / RTT drift detected $\rightarrow$ recommendation: *re-collect with interleaved scheduling*.
- **`REDESIGN / NO-GO`:** Prior art found, or $B6 \approx 0.50$ with tight CIs and clean NC1/NC2 (informative negative), or data invalid.

**Day-Confound Binding Rule:** Because of F1 and Spotify, a `GO` from this pilot can only state "separable in this dataset". If NC2 fails or drift checks show a day effect, the honest proposed outcome is **`CONDITIONAL GO`**.
