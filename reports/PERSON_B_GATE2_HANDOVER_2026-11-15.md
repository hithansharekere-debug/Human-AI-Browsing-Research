# Person B — Gate 2 Completion and Analysis Handover Report

**Project:** Human vs. AI-Agent Browsing at the Client Egress  
**Role:** Person B — Analysis Lead  
**Report date:** 15 November 2026  
**Recipient:** Person C — Audit/Synthesis Lead  
**Status:** Gate 2 documentation committed; empirical analysis not yet started

---

## 1. Executive Summary

Gate 2 methodology reconciliation and documentation have been completed and committed locally.

The original Gate 2 freeze was committed, followed by a separate documentation erratum correcting the transcription of findings F3–F5 against Person A's authoritative handover and 9 November collection report.

The final verification run completed successfully:

- **32 tests passed** in 12.04 seconds.
- The working tree is clean.
- Both commits are preserved in Git history.
- No remote is configured and nothing has been pushed.
- No study sessions (S0001–S0092) have been processed.
- No study feature extraction or empirical analysis has started.

The project is therefore at a documented and locally committed methodology stage. It is not yet at the empirical-results or final handover stage.

## 2. Git and Verification Status

Repository:

`C:\Users\ASUS\Desktop\Human-AI-Browsing-Research`

Branch: `master`

### Commit history

| Commit | Message |
|---|---|
| `e3fa7128951a19cecb682254e3a2dd58a8b4b967` | Gate 2: SPEC + PREREG frozen |
| `459a26c57ce6a0a347b776e9350924690b6132cd` | Gate 2 erratum: restore F3-F5 from handover |

The second commit is a separate correction. The original freeze commit was not amended or rewritten.

### Final verification

| Check | Result |
|---|---|
| Pytest suite | 32 passed |
| Test execution time | 12.04 seconds |
| Working tree | Clean |
| Erratum files changed | 3 |
| Git remote | None |
| External push | None |
| Study sessions processed | 0 |

The erratum changed only:

- `analysis/PREREG.md`
- `docs/GATE2_REVIEW.md`
- `analysis/DEVIATIONS.md`

The tests used dry-run, self-test, and synthetic fixtures. Passing these tests confirms the tested functionality and methodology checks; it does not establish that the full real-data analysis is correct.

## 3. F3–F5 Documentation Erratum

The transcription error in the earlier committed preregistration was corrected using:

- Person A's `00_READ_ME_FIRST_PersonB_Handover.pdf`, Part 5.
- Person A's 9 November collection report.

The corrections are recorded in `DEV-05`.

### F3 — IPv6 traffic dominance

Approximately 98% of in-window bytes are IPv6 across both controller classes.

The pipeline must therefore account for both IPv4 and IPv6 in filters and field extraction. IPv4-only filtering could silently discard most of the observed traffic.

### F4 — Corrected idle-baseline measurements

The corrected idle measurements for I0001–I0008 have been restored, including their original KB/min values.

The measurements show that:

- 6 November included idle measurements of 127 and 57 KB/min, alongside an initial Chrome/NVIDIA/HP software outlier.
- 7 and 9 November included substantial `gvt1` component downloads.
- I0004 and I0007 were exceptional Windows Update/Delivery Optimization outliers.
- Removing `gvt1` brings the 7 and 9 November idle levels to approximately 150–190 KB/min, compared with approximately 127 KB/min for the 6 November reference measurement.

The documented outliers must not be used to establish background thresholds.

### F5 — Ten known collection issues

The ten collection issues from Person A's 9 November report are restored:

1. Collection-day and schedule confounding.
2. Unequal participant rounds.
3. S0062's defective 0.007-second window.
4. Edge/Bing/MSN background traffic in S0044, S0068, S0081, and 16 additional sessions.
5. Idle-baseline outliers.
6. Missing upstream validation.
7. Datadog traffic in one dry-run agent capture.
8. 100% task success on both sides.
9. DuckDuckGo navigation in agent session S0010.
10. Gemini quota errors in early test runs.

The corresponding handling and limitations are documented in the preregistration and Gate 2 review.

## 4. Frozen Methodology

The following major methodology decisions are documented in the committed specification and preregistration.

### Flow processing

- Session windows are defined by START and END markers.
- Marker packets are excluded from feature extraction.
- Both IPv4 and IPv6 traffic are supported.
- LAN traffic is excluded before flow aggregation.
- Flows are clipped to the session window.
- NFStream uses bidirectional five-tuple flow identification, with the specified idle and active timeouts.
- A tshark packet-table fallback is specified.

### Flow classification

The precedence is:

`LAN exclusion → vendor → search → os_background → website → unknown`

The background-domain addendum and the documented special cases are included in the flow-classification specification.

### Primary model

The primary model is B6_core6, using website-only timing, volume, and connection-structure features:

- `T_idle_gap_median`
- `T_burst_rate`
- `V_up_down_ratio`
- `V_upload_burst_share`
- `C_new_flows_per_min`
- `C_max_concurrent`

The primary Logistic Regression uses standardization, L2 regularization, C=1.0, and no hyperparameter tuning.

The Random Forest is specified as a secondary nonlinear consistency check, not the primary model.

### Evaluation

The methodology specifies:

- AUROC as the primary metric.
- F1 as a secondary metric.
- Cluster-bootstrap confidence intervals using 2,000 resamples.
- LOTO task-held-out evaluation.
- LOPO participant/agent-repetition-held-out evaluation.
- Within-task label-permutation negative control NC1.
- Human-vs-human collection-day negative control NC2.
- Pre-specified family-dropout and sensitivity analyses.

The exact decisions and implementation requirements are recorded in the committed project files.

## 5. Data Integrity and Handling

The study data remain outside the Git repository under:

`C:\pilot-v1-data\`

The intake verification previously reported:

- 491 checksum entries checked.
- 491 passed.
- 0 mismatches.
- 0 missing files.
- 0 unexpected extras.

The original `sessions.csv` and `label_corrections.csv` were preserved. Person A's authoritative `methods_A_v2.tex` was also preserved.

The Gate 2 and erratum commits contain documentation, source code, configuration, and tests, not raw packet captures or the study dataset.

**No raw data is being transferred to Person C in this report.**

## 6. Important Analysis Readiness Limitations

The current repository must not yet be treated as a completed empirical-analysis pipeline.

The latest implementation review identified placeholder functions in parts of:

- `src/pipeline/sensitivity_analysis.py`
- `src/pipeline/negative_controls.py`

Examples include fixed placeholder AUROCs and hard-coded round counts.

The existing tests establish that the relevant components are wired into the project and pass their current tests. They do not establish that every sensitivity analysis or supplementary negative control computes valid results from real study data.

Real dry-run flow validation has also not yet been completed.

Before processing the study sessions, these items must be addressed:

1. Replace placeholder analysis functions with genuine calculations.
2. Validate feature extraction on permitted dry-run data.
3. Verify IPv4/IPv6 handling and flow-classification behavior.
4. Confirm that primary analysis excludes S0062.
5. Verify that grouped splits do not leak participants or agent repetitions.
6. Validate the bootstrap and negative-control implementations.
7. Confirm that every requested sensitivity analysis produces actual computed results.
8. Verify that the output contains derived features and results only, with no raw traffic or identifying information.

No empirical performance claims should be made until these checks and the real-data analysis are complete.

## 7. Person C's Requested Empirical Deliverables

The following requirements have been recorded for the final derived-results package.

### A. Collection-day confounding

Evaluate whether collection day can predict the controller label, taking account of:

- AI-agent sessions collected on 6 November.
- Human sessions collected on 7 and 9 November.
- Chrome updater traffic in 33 of 52 human windows and zero AI windows.
- Spotify traffic in 23 human sessions and zero AI sessions.

The analysis must distinguish actual browsing behavior from collection-day and background-software effects.

### B. Sensitivity analyses

Report the primary results with and without:

- S0044
- S0068
- S0081

Also report the S0062 sensitivity analysis using the NetLog-reconstructed window, separately from the primary analysis that excludes S0062.

### C. Per-family results

Provide results and confidence intervals for:

1. Vendor
2. Handshake
3. Destination
4. Length
5. Timing
6. Volume
7. Connection structure

Results should use the agreed participant-grouped evaluation approach and provide enough detail for Person C to compare the findings with L1, L3, L6, and L9 and populate the Introduction result slot.

### D. Output and privacy boundary

The final package must contain derived results only.

Expected outputs include:

- Descriptive statistics.
- Effect sizes and confidence intervals.
- Baseline results.
- Family-dropout results.
- Negative-control results.
- Collection-day/drift diagnostics.
- Sensitivity results.
- Figures and plotting scripts.
- Run manifest and methodology/deviation records.
- Processed session features without IP addresses, participant names, or raw packet data.
- A README explaining the analysis and reproducibility steps.

No raw packet captures, raw session ledgers, NetLogs, or private ground-truth artifacts should be included in the Person C package.

## 8. Current Handover Status

| Deliverable | Status |
|---|---|
| Gate 2 methodology reconciliation | Completed |
| Gate 2 local freeze commit | Completed |
| F3–F5 source-verified erratum | Committed |
| DEV-05 deviation record | Committed |
| Test suite | 32 passed |
| Real dry-run feature validation | Pending |
| Placeholder sensitivity functions | Pending implementation |
| Full study feature extraction | Not started |
| Primary empirical analysis | Not started |
| Collection-day negative-control results | Not started |
| Per-family confidence intervals | Not started |
| Requested sensitivity results | Not started |
| Derived-results package for Person C | Pending |

## 9. Conclusion

Person B's Gate 2 documentation and methodology reconciliation are committed locally, and the latest verification run passed all 32 tests.

The F3–F5 transcription error has been corrected using Person A's authoritative source documents and registered as DEV-05.

However, the empirical analysis has not started. The remaining analysis functions and real-data validation must be completed before any findings are reported.

Person C's requested deliverables are understood and will be prepared as a separate derived-results package. No raw data will be transferred.

**Current status: Gate 2 documentation complete; empirical analysis pending.**
