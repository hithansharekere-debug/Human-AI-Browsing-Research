# Dataset Intake & Cryptographic Verification Report

**Date:** 2026-11-14  
**Project:** Human vs. AI-Agent Browsing at the Client Egress  
**Role:** Person B (Analysis Lead)  
**Dataset Tag:** `pilot-v1` (Frozen 2026-11-09 13:23:11 UTC by Person A)  
**Status:** **ALL INTAKE STAGES (A, B, C, D, E) COMPLETE & 100% VERIFIED**  

---

## 1. Executive Summary

Safe onboarding and cryptographic verification of Person A's dataset (`pilot-v1`) has been successfully completed in full compliance with research protocol and data-security directives:
- **Zero Ingestion Contamination:** Raw packet captures and ground truth traces reside strictly **outside** the Git repository in `C:\pilot-v1-data\data\`.
- **Desktop Source Preserved:** The original download `C:\Users\ASUS\Desktop\TO_PERSON_B.zip` is preserved unmodified.
- **`sessions.csv` Unmodified:** The frozen session ledger matches its SHA-256 hash bit-for-bit.
- **Zero Password Exposure:** The authorized 7z password was entered interactively into a local terminal session without being echoed, logged, hardcoded, or transmitted.
- **Payload Privacy:** No packet payloads were inspected.
- **No Premature Analysis:** No feature calculation or statistical analysis of the 92 study sessions has been performed.

---

## 2. Cryptographic Checksum Verifications

| Checkpoint | Target Path | Expected Hash / Prefix | Calculated SHA-256 Digest | Status |
|---|---|---|---|---|
| **Outer Archive** | `incoming/TO_PERSON_B.zip` | `9A91BB019312AF93499B407CF26A4855C19F59A3515357AF843A4196AA9F8750` | `9A91BB019312AF93499B407CF26A4855C19F59A3515357AF843A4196AA9F8750` | **PASS (Confirmed by Person A)** |
| **Inner Raw Archive** | `staging/.../02_pilot-v1_RAW_ENCRYPTED.7z` | Prefix `2f4c5790b603df3e` | `2F4C5790B603DF3EE6B18C4536C29E1E9C06A92CA50E4581DF36D12E4578930D` | **PASS (Prefix Confirmed)** |
| **Internal Manifest** | `data/SHA256SUMS.txt` | `dd39bf130ed33adb6e5723fcae0a583fb1fe3ab2c7bcb93e31166ea2d9e309fd` | `dd39bf130ed33adb6e5723fcae0a583fb1fe3ab2c7bcb93e31166ea2d9e309fd` | **PASS** |
| **Sessions Ledger** | `data/sessions.csv` | `a648da5155d71fa4f02895c0e410c1a51127d60dd5ddd0611246f55a8b545188` | `a648da5155d71fa4f02895c0e410c1a51127d60dd5ddd0611246f55a8b545188` | **PASS** |

---

## 3. Comprehensive Manifest Verification (Stage C Audit)

Following interactive decryption into `C:\pilot-v1-data\data\`, every file listed in `SHA256SUMS.txt` was validated against its cryptographic digest:

- **Total Manifest Entries Checked:** `491`
- **Passed:** `491` (100.0%)
- **Failed / Mismatched:** `0`
- **Missing Files:** `0`
- **Unindexed / Extra Files:** `0`

### Inventory Breakdown
- **116 Packet Captures (`raw/*.pcapng`):**
  - 92 Study Sessions (52 Human, 40 Agent)
  - 8 Idle Baselines (`I0001`–`I0008`)
  - 11 Dry Runs (`D0001`–`D0012`, excluding aborted `D0008`)
  - 5 System Self-Tests (`X0001`–`X0005`)
- **374 Ground Truth Artifacts (`ground_truth/<id>/`):**
  - 116 `meta.json` files
  - 116 Chrome `netlog.json` files
  - Agent runtime logs (`agent_history.json`, `agent_result.json`, `agent_stdout.log`)
- **1 Master Session Ledger (`sessions.csv`)**

---

## 4. Correction File Validation (`label_corrections.csv`)

Validated the newly received correction file from Person A (`SEND_TO_B_14Nov.zip`):
- **Preservation:** The received file is preserved intact at `C:\pilot-v1-data\incoming\updates_14Nov\label_corrections.csv`.
- **Row Count:** Exactly **13 correction rows**.
- **Columns Affected:** All 13 rows modify `answer_given` exclusively.
- **Outcome Invariance:** Zero outcome modifications (`outcome` remains `success` for all 92 study sessions).
- **Summary:** Corrects shortened operator summary strings with verbatim answers from `agent_result.json` (ratings "1 star", weights "607 g") and NetLog lookups ("The Iron Tide").
- **Separate S0062 Exclusion Row:** Formatted for separate ingestion without modifying `sessions.csv`:
  ```csv
  S0062,excluded,0,1,"Premature END marker (duration_s=0.007s). Task occurred outside analysis window. Excluded from primary analysis per PREREG; retained for sensitivity analysis.",PB,2026-11-14
  ```

---

## 5. Methods Section Version 2 (`methods_A_v2.tex`)

- **Preservation:** Preserved at `reports/methods_A_v2.tex` and staged as the primary working draft in `reports/methods_section.tex`.
- **Modifications from v1:** Includes Person D's feedback (avoids "balanced" terminology, specifies "recorded as successful", documents participant P04 schedule split across two days, records Datadog isolation to dry runs, and documents day-correlated background traffic F1/Spotify).
- **Placeholder:** Subsection III-H (`Feature Extraction and Classification`) remains untouched as `[To be written by the analysis lead.]`.

---

## 6. Blockers & Gate 2 Readiness

- **Current Blockers:** **NONE.** All checksums have passed, dataset integrity is verified, and documentation is up to date.
- **Next Stage:** Gate 2 freeze (committing `features/SPEC.md`, `features/flow_rules.yaml`, `analysis/PREREG.md`) before initiating feature extraction on dry runs and study sessions.
- **Protocol Reminder:** SPEC and PREREG must be frozen with a dated Git commit before computing any features on the 92 study sessions.
