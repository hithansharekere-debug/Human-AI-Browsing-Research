# Analysis Deviations Log (analysis/DEVIATIONS.md)

**Project:** Human vs. AI-Agent Browsing at the Client Egress  
**Maintainer:** Person B (Analysis Lead)  
**Auditors / Recipients:** Person C, Person D  
**Status:** Pre-Gate 2 Log (Locked before Study Session Processing)

---

## Protocol on Deviations

Any change, adjustment, unexpected data anomaly, or post-hoc analysis divergence from the preregistered protocol (`analysis/PREREG.md`) must be documented here in real time.

Every log entry requires:
1. **Timestamp (UTC)**
2. **Phase Affected**
3. **Reason for Deviation**
4. **Original Preregistered Specification**
5. **Modified Specification & Rationale**
6. **Expected Impact on Statistical Power or Bias**
7. **Sign-off Status**

---

## Deviation Register

| ID | Date | Phase | Original Specification | Action / Deviation Taken | Justification & Evidence | Impact Assessment | Status |
|---|---|---|---|---|---|---|---|
| **DEV-00** | 2026-11-14 | Setup | Starter repository scaffold | Baseline repository initialization | Initial project setup from starter templates | None (Pre-execution) | Baseline Locked |
| **DEV-01** | 2026-11-14 | Flow Classification | Initial port-based flow rules (`flow_rules.yaml` v1.0) | Incorporated Person A Addendum 07 (`flow_rules.yaml` v1.1): added personal apps (Spotify in 23 human sessions), Edge news feed, and LAN traffic exclusions | Person A's 13 Nov egress audit revealed non-study background traffic correlated with collection dates (Spotify, Dropbox, Skype, McAfee, Edge news) and LAN broadcast (`Android.local`) | Prevents class-confound leakage into primary B6 website features. Drops LAN packets before flow reassembly. Unresolved domains (`fastly-edge.com`, `cloudflare-ech.com`) remain `unknown`. | Pre-Gate 2 Staged |
| **DEV-02** | 2026-11-14 | Session Exclusions | All 92 study sessions included in primary analysis | S0062 (P03, T1, rep 2) excluded from primary analysis ($N=91$); retained for sensitivity analysis with NetLog-reconstructed window | Marker analysis revealed S0062 has a window duration of $0.007\text{ s}$ due to premature ENTER keypress at capture launch; task execution took place after END marker | Primary analysis avoids severe outlier with 0 task flows. Sensitivity analysis evaluates robustness with reconstructed window. Zero impact on raw `sessions.csv`. | Pre-Gate 2 Staged |
| **DEV-03** | 2026-11-14 | Methods Documentation | Methods Section v1 draft | Adopted `methods_A_v2.tex` as authoritative source for paper Section III | Person A received Person D's review corrections: replaced "balanced" wording, documented P04 schedule split across two days, isolated Datadog to dry runs, and noted day-correlated background | Harmonizes analysis documentation with upstream collection paper text. Subsection III-H remains placeholder for Person B. | Pre-Gate 2 Staged |
| **DEV-04** | 2026-11-14 | Pre-Registration & Methodology | Temporary baseline nomenclature, 1000-perm NC1, and 4-fold LOPO | Restored authoritative B0–B8 baselines, 10-fold LOPO pairing agents by rep, 200 within-task perm NC1, primary Human 7 vs 9 Nov NC2, all 7 sensitivity analyses, and documented B6 <= 6 feature constraint | Pre-Gate 2 reconciliation against authoritative Blueprint §6.3 and Handover Step 8/9; resolved feature count conflict by defining B6_core6 (2T+2V+2C) for Logistic Regression | Eliminates methodology discrepancies; guarantees zero grouping leakage in 10 LOPO folds; aligns negative controls with frozen preregistration plan. | Pre-Gate 2 Staged |

---

## Exploratory vs. Confirmatory Segregation

- All findings generated from deviations or un-preregistered models must be flagged with `[EXPLORATORY]` in all reports and summaries delivered to Person C and Person D.
- Confirmatory hypotheses retain strict priority in manuscript reporting.
