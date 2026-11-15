# End-to-End Analysis Workflow

This document defines the strict sequential workflow executed by Person B (Analysis Lead) to process Person A's dataset and deliver the audited evidence package to Person C.

## Workflow Phases

```
+-----------------------------------------------------------------------------------------+
|                               PHASE 1: INGESTION & INTEGRITY                            |
|  - Ingest external read-only dataset path                                               |
|  - Validate SHA-256 manifest against raw files (src/pipeline/dataset_verification.py)   |
|  - Check completeness across all 92 expected sessions (Human vs. AI pairs)             |
+-----------------------------------------------------------------------------------------+
                                           │
                                           ▼
+-----------------------------------------------------------------------------------------+
|                               PHASE 2: PREPROCESSING & WINDOWING                        |
|  - Segment continuous capture into observation windows (src/pipeline/window_extraction) |
|  - Extract bidirectional flows using nfstream (src/pipeline/flow_extraction.py)         |
|  - Filter background OS telemetry & classify traffic (src/pipeline/flow_classification) |
+-----------------------------------------------------------------------------------------+
                                           │
                                           ▼
+-----------------------------------------------------------------------------------------+
|                               PHASE 3: FEATURE ENGINEERING                              |
|  - Extract transport & timing metrics according to features/SPEC.md                     |
|  - Generate tabular dataset (Parquet format) with anonymized schema                     |
|  - Verify zero-leakage constraints (no target leakage, no IP persistence)               |
+-----------------------------------------------------------------------------------------+
                                           │
                                           ▼
+-----------------------------------------------------------------------------------------+
|                               PHASE 4: STATISTICAL TESTING                              |
|  - Execute preregistered statistical tests (analysis/PREREG.md)                         |
|  - Calculate effect sizes (Cohen's d, Cliff's delta) and confidence intervals           |
|  - Apply FDR / Bonferroni correction for multiple hypothesis comparisons               |
+-----------------------------------------------------------------------------------------+
                                           │
                                           ▼
+-----------------------------------------------------------------------------------------+
|                               PHASE 5: MODEL EVALUATION & VALIDATION                    |
|  - Fit baseline classifiers (Logistic Regression, Random Forest) via cross-validation   |
|  - Compute ROC-AUC, PR-AUC, F1, calibration curves, and feature importances             |
|  - Run negative controls (label-shuffling, time-reversal, synthetic Poisson nulls)     |
|  - Perform sensitivity analysis across window sizes (e.g., 5s, 15s, 30s, 60s)           |
+-----------------------------------------------------------------------------------------+
                                           │
                                           ▼
+-----------------------------------------------------------------------------------------+
|                               PHASE 6: REPRODUCIBILITY & DELIVERABLE BUNDLING           |
|  - Package final metrics tables into results/                                           |
|  - Render high-resolution publication figures into figures/                             |
|  - Generate environment freeze, git commit hash, and artifact checksum manifest        |
|  - Draft Handover Memo (reports/B_to_C_MEMO.md) and Methods Section (reports/*.tex)     |
+-----------------------------------------------------------------------------------------+
```

## Protocol Enforcement

1. **Gatekeeping**: No phase can proceed if the upstream verification phase yields validation errors or missing checksums.
2. **Deviation Logging**: Any necessary alteration to the statistical test, parameter values, or filtering logic must be recorded in `analysis/DEVIATIONS.md` before finalizing deliverables for Person C.
