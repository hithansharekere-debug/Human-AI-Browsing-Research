# Dry-Run and Non-Study Capture Validation Report

**Project:** Human vs. AI-Agent Browsing at the Client Egress  
**Role:** Person B (Analysis Lead)  
**Date:** 15 November 2026  
**Scope:** Permitted Dry-Run ($D0001$–$D0012$, excluding $D0008$) and Self-Test ($X0001$–$X0005$) Captures  
**Status:** VALIDATED — Stage 3 Complete

---

## 1. Inventory Reconciliation & Trace Identification

The inventory discrepancy identified in the readiness audit has been reconciled against the authoritative collection logs (`00_READ_ME_FIRST_PersonB_Handover.pdf` Part 2.7 & 3.1) and `C:\pilot-v1-data\data\SHA256SUMS.txt`:

- **Permitted Dry-Run Captures:** Exactly **11 captures** (`D0001.pcapng` through `D0012.pcapng`).
- **Explanation for Absent Capture ($D0008$):** As documented in Person A's Handover Part 2.7, capture $D0008$ was aborted during collection due to an agent execution error and moved out of the primary dataset to `data/_aborted_dry_runs/`. The primary dataset holds 11 dry runs, not 12.
- **Permitted Self-Test Captures:** Exactly **5 captures** (`X0001.pcapng` through `X0005.pcapng`).
- **Checksum Verification:** All 16 permitted non-study captures were verified bit-for-bit against `SHA256SUMS.txt`. All 16 passed ($16/16$).
- **Strict Isolation:** Zero study session traces ($S0001$–$S0092$) were accessed or processed during this stage.

---

## 2. Technical Validation Outcomes

| Verification Item | Specification / Requirement | Validation Result | Notes |
|---|---|---|---|
| **START/END Marker Detection** | Hardware UDP marker packets to `192.0.2.1:9` | **PASSED** | Marker bounds extracted cleanly matching logged `duration_s` within milliseconds ($D0001$: 54.997 s). |
| **Window Clipping** | Retain only packets strictly within $(t_{\text{start}}, t_{\text{end}})$ | **PASSED** | Pre-window (settle/quiet) and post-window (quiet/shutdown) packets strictly dropped ($D0001$: 6,661 in-window out of 10,022 total). |
| **Marker Exclusion** | Drop `ip.dst == 192.0.2.1` | **PASSED** | Both START and END marker packets excluded from flow extraction. |
| **Dual-Stack Accounting** | Dual IPv4 and IPv6 support | **PASSED** | Both IPv4 and IPv6 packet streams processed. Confirmed empirical Finding F3 ($95.6\%\text{--}97.7\%$ IPv6 bytes in dry runs). |
| **LAN Traffic Exclusion** | Drop broadcast, mDNS (5353), SSDP (1900), LLMNR (5355), NetBIOS (137–139), SMB (445), `*.local` | **PASSED** | LAN discovery packets dropped before flow reassembly ($36\text{--}54$ LAN packets dropped per dry run). |
| **Flow Classification Precedence** | $\text{LAN} \rightarrow \text{vendor} \rightarrow \text{search} \rightarrow \text{os\_background} \rightarrow \text{website} \rightarrow \text{unknown}$ | **PASSED** | Correctly resolved Gemini API (`generativelanguage.googleapis.com`) as `vendor`, Datadog telemetry (`http-intake.logs.us5.datadoghq.com`) as `vendor`, and `cloudflare-ech.com` as `unknown`. |
| **Flow Reassembly Engine** | 5-tuple bidirectional flows with $30\text{ s}$ idle timeout | **PASSED** | Bidirectional flow assembly completed without libpcap dependency using pure-binary Scapy fallback. |
| **Feature Schema Compliance** | 6 standardized primary B6 features ($2T + 2V + 2C$) | **PASSED** | All features (`T_idle_gap_median`, `T_burst_rate`, `V_up_down_ratio`, `V_upload_burst_share`, `C_new_flows_per_min`, `C_max_concurrent`) produced finite, valid numerical outputs. |
| **Unknown Traffic Monitoring** | Retain unknown traffic and report byte share | **PASSED** | Unknown bytes tracked without corrupting website flow metrics. |
| **Output Privacy** | Zero raw packet payloads, IP addresses, NetLog strings, or participant PII in derived feature outputs | **PASSED** | Verified: derived feature schema contains exclusively aggregate statistical metrics and approved identifiers. |
| **Reproducibility** | Two consecutive extraction passes produce identical results | **PASSED** | 100% byte-identical feature dictionaries across repeated extraction runs. |

---

## 3. Summary & Gate 3 Readiness

Stage 3 (Permitted Dry-Run Validation) has passed all verification requirements. The extraction and feature engineering engine is fully operational, verified against empirical network captures, and ready for Stage 4 execution.
