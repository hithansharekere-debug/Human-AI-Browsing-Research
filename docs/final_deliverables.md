# Final Deliverables Checklist: Person B to Person C

This checklist enumerates all artifacts and documentation required for a complete, reproducible handover from **Person B (Analysis Lead)** to **Person C (Downstream Recipient & Reviewer)**.

---

## Deliverables Matrix

| Item # | Artifact Description | Location / Path | Status | Verification Criteria |
|---|---|---|---|---|
| **D1** | **Dataset Integrity & Verification Report** | `output/verification_report.json` | Pending Data | Checksum match for all 92 sessions; zero corruption flags. |
| **D2** | **Feature Specification Matrix** | `features/SPEC.md` | Defined | Formal mathematical definitions and measurement units for all features. |
| **D3** | **Flow Parsing & Filtering Rules** | `features/flow_rules.yaml` | Defined | Explicit Layer-4/Layer-7 filtering and background traffic isolation. |
| **D4** | **Preregistered Statistical Analysis** | `results/preregistered_results.csv` | Template Ready | All hypotheses evaluated with point estimates, CI, and adjusted p-values. |
| **D5** | **Exploratory & Secondary Statistics** | `results/exploratory_results.csv` | Template Ready | Explicitly segregated from confirmatory findings. |
| **D6** | **Model Performance & Calibration Report**| `results/model_metrics.json` | Template Ready | Stratified CV metrics: ROC-AUC, PR-AUC, F1, Brier score, feature importances. |
| **D7** | **Negative Controls & Sanity Validations**| `results/negative_controls.json` | Template Ready | Label permutation, session shuffling, and synthetic Poisson baseline results. |
| **D8** | **Sensitivity & Robustness Analysis** | `results/sensitivity_analysis.json` | Template Ready | Invariance checks across window sizes (5s-60s) and idle threshold perturbations. |
| **D9** | **Publication-Ready Figures** | `figures/*.png`, `figures/*.pdf` | Scaffolded | DPI>=300, vector PDF copies, anonymized legends, zero raw IP tags. |
| **D10**| **Formal Deviation Log** | `analysis/DEVIATIONS.md` | Template Ready | Full chronology of any divergence from `PREREG.md`. |
| **D11**| **Academic Methods Section Draft** | `reports/methods_section.tex` | Template Ready | Standalone LaTeX document detailing data provenance, pipeline, and stats. |
| **D12**| **Synthesis & Handover Memo** | `reports/B_to_C_MEMO.md` | Template Ready | Comprehensive briefing summarizing conclusions, limitations, and caveats. |
| **D13**| **Reproducibility Manifest** | `output/reproducibility_manifest.json` | Template Ready | Pinned OS details, Python environment lock, git commit SHA, output SHA-256 hashes. |

---

## Sign-off Criteria for Person C Handover

Before delivering the archive to Person C, Person B must confirm:
- [ ] Pipeline runs fully end-to-end via `python scripts/run_pipeline.py --config config/pilot_v1.yaml` with exit code 0.
- [ ] All unit tests pass cleanly via `pytest`.
- [ ] No raw IP addresses, participant identifiers, or raw packet payloads are present in `results/`, `reports/`, or `output/`.
- [ ] The reproducibility manifest verifies bit-for-bit consistency on a clean virtual environment.
