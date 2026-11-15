# Handover Memorandum: Person B (Analysis Lead) to Person C (Downstream Recipient)

**Date:** 2026-11-14  
**From:** Person B (Analysis Lead)  
**To:** Person C (Project Co-Lead / External Evaluator & Decision Maker)  
**Subject:** Delivery of Verified Analysis Architecture & Reproducible Research Package  
**Status:** Foundation & Pipeline Scaffold Complete (Awaiting Frozen Dataset Ingestion & Preregistration Sign-off)

---

## 1. Executive Summary

As Person B (Analysis Lead), I have constructed the end-to-end, reproducible analysis foundation for our study **"Human vs. AI-Agent Browsing at the Client Egress"**. 

This package is designed to ingest Person A's frozen network traces, verify bit-for-bit integrity, perform standardized windowing and flow extraction, execute preregistered statistical tests, conduct negative controls, and output verified evidence tables and figures for your independent review.

In compliance with our research protocol:
- **No data fabrication or premature feature extraction on the 92 sessions has been performed.**
- The repository structure, secure isolation boundaries, configuration schemas, unit test suite, and LaTeX methods documentation are completely initialized and operational.

---

## 2. Package Architecture and Component Status

| Component | Repository Path | Functional Purpose | Status |
|---|---|---|---|
| **Pipeline Core** | `src/pipeline/` | 10 modular Python stages from verification to reproducibility | Implemented & Unit-Tested |
| **Specifications** | `features/SPEC.md`, `flow_rules.yaml` | Mathematical feature definitions and Layer-4/7 filter rules | Locked |
| **Preregistration** | `analysis/PREREG.md`, `DEVIATIONS.md` | Formal hypotheses, test thresholds, and deviation tracking | Awaiting Person C Approval |
| **Configuration** | `config/pilot_v1.yaml` | Experiment parameters, window settings, and random seeds | Ready |
| **Methods Section**| `reports/methods_section.tex` | Standalone publication-grade LaTeX methods draft | Ready |
| **Output Buffers** | `results/`, `figures/`, `output/` | Version-controlled directories with `.gitkeep` placeholders | Secured & Clean |

---

## 3. Data Protection and Zero-Leakage Assurances

1. **Strictly External Raw Data:** Person A's packet captures will remain exclusively on external, write-protected storage. The repository `.gitignore` guarantees that no `.pcap`, raw archive, or raw trace can be committed.
2. **Sanitized Pipeline:** Source IPs, destination IPs, and participant IDs are blinded and excluded from all feature matrices, logs, and visualization routines.
3. **Reproducibility Guarantee:** All statistical tests, cross-validation splits, and bootstrap iterations are anchored to deterministic random seeds (`seed = 42`). An automated reproducibility manifest (`output/reproducibility_manifest.json`) locks environment parameters and output hashes.

---

## 4. Immediate Action Items for Person C

To proceed to Phase 1 (Ingestion & Verification of the 92 study sessions), please review and sign off on:
1. **Preregistered Hypotheses (`analysis/PREREG.md`):** Confirm hypotheses H1, H2, and H3, multiple-comparison corrections (Benjamini-Hochberg FDR at $q=0.05$), and negative control thresholds.
2. **Feature Schema (`features/SPEC.md`):** Confirm that the volumetric, temporal, concurrency, and burst features align with your target theoretical distinctions.
3. **External Dataset Path:** Coordinate with Person A to provide the read-only external storage path and matching `manifest.sha256`.

---

*Signed,*  
**Person B**  
*Senior Research Engineer & Analysis Lead*
