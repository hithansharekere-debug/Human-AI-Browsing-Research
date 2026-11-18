# Final Handover Reconciliation Report — Person B (Analysis Lead)

**Project:** Human vs. AI-Agent Browsing at the Client Egress  
**Recipient:** Person C (Synthesis / Audit Lead) & Person D (Senior Reviewer)  
**Author:** Person B (Analysis Lead)  
**Date:** 18 November 2026  
**Git Branch:** `review/data-provider-corrections-2026-11-17`  
**Base Commit:** `3ea33f7b6fa71c9ed32b61bfe8bcd7fcf59bed63` (master, clean and untouched)  
**Audit Target Commit:** `3397b1973705b3236afc3b1740951a9f2fab582d`  

---

## Executive Summary & Systematic Issue Classification

This report provides the final technical reconciliation requested before formal delivery of the empirical analysis to Person C and Person D. All source packet captures (PCAPs), NetLogs, ground-truth records, feature matrices, and result tables were independently audited without pipeline rewrites or hardcoded overrides.

### Systematic Issue Classification Matrix

| Issue ID | Audit Area | Disposition | Summary of Findings & Evidence |
| :---: | :--- | :---: | :--- |
| **ISSUE-01** | **Search Count Reconciliation** | **PASS WITH LIMITATIONS** | Reconciled 27 vs 7. Person A's 27 count corresponds to sessions with Google destinations / Day 2 human cohort, whereas Person B's 7 count (8 including S0062) measures active in-window omnibox search query/suggestion flows with bytes. Both confirm 0 search flows in AI sessions. Complete 92-session audit table documented. |
| **ISSUE-02** | **Label Corrections Audit** | **PASS** | Canonical 18 November `label_corrections.csv` verified. Exactly 13 `answer_given` rows and 1 `S0062` `excluded` row (0 to 1). Primary analysis evaluates $N=91$; S0062 sensitivity evaluates $N=92$. Zero unrelated labels altered. Hashes verified outside Git. |
| **ISSUE-03** | **Unknown Byte Accounting** | **PASS WITH LIMITATIONS** | Full 5-class byte accounting verified. Unknown bytes account for $11.95\%$ of human in-window bytes ($4.66\times$ website bytes) and $12.14\%$ of AI in-window bytes ($1.02\times$ website bytes). 28 human and 30 AI sessions exceed the 5% threshold. Root cause is pre-window TCP connection reuse where TLS handshake was not captured in-window. Unresolved domains verified against NetLog. |
| **ISSUE-04** | **Scientific Wording & Limitations** | **PASS** | Unsupported phrase "timing is sole essential driver" removed and replaced with cautious family-dropout attribution. Random Forest clarified as an alternative non-linear model check, not independent confirmation of timing importance without ablation. NC1 LOTO clarified with exchangeability/calibration assumptions. All 5 required limitations prominent. |
| **ISSUE-05** | **Release Safety & Repository Integrity** | **PASS** | Master branch is untouched. Work restricted to dedicated correction branch. No force push. Raw PCAPs, NetLogs, `sessions.csv`, and `label_corrections.csv` remain strictly outside Git in `C:\pilot-v1-data\`. No private LAN IPs, credentials, or PII tracked. |

---

## 1. Search Count Reconciliation (27 vs. 7)

### 1.1 Problem Statement and Initial Contradiction
Person A's data-provider review noted that Google search was present in **27 human sessions and 0 AI sessions**, whereas the corrected empirical results reported in `results/byte_accounting.csv` and `processed/session_features.csv` indicate search activity in only **7 human sessions and 0 AI sessions** (8 sessions when including S0062).

### 1.2 Root Cause Analysis and Reconciling Definitions
An exhaustive cross-modal investigation of all 92 PCAPs and NetLogs reveals that the difference stems from two distinct, valid definitions of "search activity":

1. **Broad Destination / Preconnect Definition (Person A's Count = 27 Human, 0 AI):**
   - In Google Chrome, launching the browser or opening new tabs triggers speculative socket preconnections (`is_preconnect: true`) to `https://www.google.com/` (the default search engine endpoint).
   - In the study, human sessions were collected in two distinct cohorts: Day 2 (7 November 2026, Participants P01–P05) comprising **exactly 27 sessions**, and Day 3 (9 November 2026, Participants P06–P10) comprising **25 sessions**. On Day 2, all 27 human sessions established preconnects or background reachability checks to `www.google.com`.
   - In contrast, all 40 AI agent sessions (6 November 2026) were executed via automated CDP scripts that navigated directly to target URLs (`meridian-tasks.vercel.app`, `en.wikipedia.org`, or `duckduckgo.com` for S0010) without triggering omnibox interactions. Thus, AI sessions had **0 search sessions** under both definitions.

2. **Strict In-Window Interactive Flow Definition (Person B's Count = 7 Human, 0 AI in Primary; 8 in Sensitivity):**
   - Person B's empirical flow-rules classification (`features/flow_rules.yaml` §2, class `search`) strictly requires that a network flow be an **active omnibox search query or suggestion request** (`suggestqueries.google.com` or `www.google.com` query endpoints) transmitting actual user keystroke traffic during the bounded task window.
   - Speculative preconnects that carried zero application query bytes or occurred before the start marker do not count as active user search flows.
   - Across the 51 primary human sessions ($N=91$), exactly **7 sessions** contained active in-window omnibox search query flows totaling **102,144 bytes**:
     - **Task 1 (T1):** 1 session (S0048, 24,201 bytes)
     - **Task 2 (T2):** 1 session (S0070, 25,691 bytes)
     - **Task 3 (T3):** 0 sessions (0 bytes)
     - **Task 4 (T4):** 5 sessions (S0044: 11,524 B, S0058: 356 B, S0075: 13,220 B, S0081: 13,930 B, S0088: 13,222 B; total: 52,252 bytes)
   - When including S0062 (reconstructed sensitivity population, $N=92$), S0062 contains an active search query (38,943 bytes), bringing the total to **8 human sessions and 141,087 bytes**.

Both counts are factual: Person A's 27 describes human sessions with Google destination connections, whereas Person B's 7 describes sessions where human participants actively used the omnibox search engine during task execution. In both paradigms, **AI agents never executed search queries (0 sessions, 0 bytes)**.

### 1.3 Complete 92-Session Search Activity & Evidence Audit Table

| Session ID | Controller | Task | Participant | Google Destination Evidence | Search / Query Evidence | Classified Categories | Search Bytes | Evidence Source | Reason for Inclusion / Exclusion |
| :--- | :---: | :---: | :---: | :--- | :--- | :--- | :---: | :--- | :--- |
| **S0001** | `agent1` | T3 | Agent | generativelanguage (Gemini API) | None (autonomous agent: direct URL navigation via CDP) | `vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0002** | `agent1` | T2 | Agent | generativelanguage (Gemini API) | None (autonomous agent: direct URL navigation via CDP) | `website+vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0003** | `agent1` | T4 | Agent | generativelanguage (Gemini API); Chrome Services (update/telemetry); fastly-edge (SafeBrowsing OHTTP) | None (autonomous agent: direct URL navigation via CDP) | `vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0004** | `agent1` | T1 | Agent | generativelanguage (Gemini API); fastly-edge (SafeBrowsing OHTTP) | None (autonomous agent: direct URL navigation via CDP) | `vendor+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0005** | `agent1` | T2 | Agent | generativelanguage (Gemini API) | None (autonomous agent: direct URL navigation via CDP) | `website+vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0006** | `agent1` | T1 | Agent | generativelanguage (Gemini API); Chrome Services (update/telemetry); fastly-edge (SafeBrowsing OHTTP) | None (autonomous agent: direct URL navigation via CDP) | `vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0007** | `agent1` | T4 | Agent | generativelanguage (Gemini API); Chrome Services (update/telemetry); fastly-edge (SafeBrowsing OHTTP) | None (autonomous agent: direct URL navigation via CDP) | `vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0008** | `agent1` | T3 | Agent | generativelanguage (Gemini API); Chrome Services (update/telemetry) | None (autonomous agent: direct URL navigation via CDP) | `website+vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0009** | `agent1` | T1 | Agent | generativelanguage (Gemini API); www.google.com (DNS/TLS) | None (autonomous agent: direct URL navigation via CDP) | `website+vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0010** | `agent1` | T2 | Agent | generativelanguage (Gemini API) | None (autonomous agent: direct URL navigation via CDP) | `website+vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0011** | `agent1` | T3 | Agent | generativelanguage (Gemini API) | None (autonomous agent: direct URL navigation via CDP) | `website+vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0012** | `agent1` | T4 | Agent | generativelanguage (Gemini API); Chrome Services (update/telemetry); fastly-edge (SafeBrowsing OHTTP) | None (autonomous agent: direct URL navigation via CDP) | `website+vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0013** | `agent1` | T4 | Agent | generativelanguage (Gemini API); fastly-edge (SafeBrowsing OHTTP) | None (autonomous agent: direct URL navigation via CDP) | `vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0014** | `agent1` | T2 | Agent | generativelanguage (Gemini API); Chrome Services (update/telemetry) | None (autonomous agent: direct URL navigation via CDP) | `website+vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0015** | `agent1` | T1 | Agent | generativelanguage (Gemini API); Chrome Services (update/telemetry) | None (autonomous agent: direct URL navigation via CDP) | `vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0016** | `agent1` | T3 | Agent | generativelanguage (Gemini API); fastly-edge (SafeBrowsing OHTTP) | None (autonomous agent: direct URL navigation via CDP) | `website+vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0017** | `agent1` | T3 | Agent | generativelanguage (Gemini API); Chrome Services (update/telemetry) | None (autonomous agent: direct URL navigation via CDP) | `website+vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0018** | `agent1` | T2 | Agent | generativelanguage (Gemini API); Chrome Services (update/telemetry) | None (autonomous agent: direct URL navigation via CDP) | `website+vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0019** | `agent1` | T1 | Agent | generativelanguage (Gemini API); Chrome Services (update/telemetry) | None (autonomous agent: direct URL navigation via CDP) | `website+vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0020** | `agent1` | T4 | Agent | generativelanguage (Gemini API); fastly-edge (SafeBrowsing OHTTP) | None (autonomous agent: direct URL navigation via CDP) | `vendor+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0021** | `agent1` | T2 | Agent | generativelanguage (Gemini API); Chrome Services (update/telemetry) | None (autonomous agent: direct URL navigation via CDP) | `website+vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0022** | `agent1` | T4 | Agent | generativelanguage (Gemini API) | None (autonomous agent: direct URL navigation via CDP) | `vendor+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0023** | `agent1` | T1 | Agent | generativelanguage (Gemini API); fastly-edge (SafeBrowsing OHTTP) | None (autonomous agent: direct URL navigation via CDP) | `website+vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0024** | `agent1` | T3 | Agent | generativelanguage (Gemini API); fastly-edge (SafeBrowsing OHTTP) | None (autonomous agent: direct URL navigation via CDP) | `website+vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0025** | `agent1` | T4 | Agent | generativelanguage (Gemini API); fastly-edge (SafeBrowsing OHTTP) | None (autonomous agent: direct URL navigation via CDP) | `vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0026** | `agent1` | T3 | Agent | generativelanguage (Gemini API); Chrome Services (update/telemetry) | None (autonomous agent: direct URL navigation via CDP) | `website+vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0027** | `agent1` | T2 | Agent | generativelanguage (Gemini API); Chrome Services (update/telemetry) | None (autonomous agent: direct URL navigation via CDP) | `website+vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0028** | `agent1` | T1 | Agent | generativelanguage (Gemini API) | None (autonomous agent: direct URL navigation via CDP) | `website+vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0029** | `agent1` | T3 | Agent | generativelanguage (Gemini API); Chrome Services (update/telemetry); fastly-edge (SafeBrowsing OHTTP) | None (autonomous agent: direct URL navigation via CDP) | `website+vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0030** | `agent1` | T4 | Agent | generativelanguage (Gemini API); Chrome Services (update/telemetry) | None (autonomous agent: direct URL navigation via CDP) | `vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0031** | `agent1` | T1 | Agent | generativelanguage (Gemini API); Chrome Services (update/telemetry) | None (autonomous agent: direct URL navigation via CDP) | `vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0032** | `agent1` | T2 | Agent | generativelanguage (Gemini API) | None (autonomous agent: direct URL navigation via CDP) | `website+vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0033** | `agent1` | T2 | Agent | generativelanguage (Gemini API); www.google.com (DNS/TLS) | None (autonomous agent: direct URL navigation via CDP) | `website+vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0034** | `agent1` | T1 | Agent | generativelanguage (Gemini API); fastly-edge (SafeBrowsing OHTTP) | None (autonomous agent: direct URL navigation via CDP) | `website+vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0035** | `agent1` | T4 | Agent | generativelanguage (Gemini API); fastly-edge (SafeBrowsing OHTTP) | None (autonomous agent: direct URL navigation via CDP) | `vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0036** | `agent1` | T3 | Agent | generativelanguage (Gemini API) | None (autonomous agent: direct URL navigation via CDP) | `vendor+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0037** | `agent1` | T1 | Agent | generativelanguage (Gemini API) | None (autonomous agent: direct URL navigation via CDP) | `vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0038** | `agent1` | T4 | Agent | generativelanguage (Gemini API); Chrome Services (update/telemetry) | None (autonomous agent: direct URL navigation via CDP) | `website+vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0039** | `agent1` | T2 | Agent | generativelanguage (Gemini API) | None (autonomous agent: direct URL navigation via CDP) | `website+vendor+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0040** | `agent1` | T3 | Agent | generativelanguage (Gemini API); fastly-edge (SafeBrowsing OHTTP) | None (autonomous agent: direct URL navigation via CDP) | `website+vendor+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0041** | `human` | T1 | P01 | fastly-edge (SafeBrowsing OHTTP) | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0042** | `human` | T2 | P01 | nan | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0043** | `human` | T3 | P01 | Chrome Services (update/telemetry); fastly-edge (SafeBrowsing OHTTP) | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0044** | `human` | T4 | P01 | www.google.com (DNS/TLS); fastly-edge (SafeBrowsing OHTTP) | Omnibox search query: task keywords | `website+search+os_background+unknown` | **11,524** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: active in-window omnibox suggestion flows. |
| **S0045** | `human` | T4 | P01 | Chrome Services (update/telemetry); fastly-edge (SafeBrowsing OHTTP) | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0046** | `human` | T3 | P01 | fastly-edge (SafeBrowsing OHTTP) | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0047** | `human` | T2 | P01 | Chrome Services (update/telemetry) | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0048** | `human` | T1 | P01 | Chrome Services (update/telemetry); www.google.com (DNS/TLS); fastly-edge (SafeBrowsing OHTTP) | Omnibox search suggestion: books query | `website+search+os_background+unknown` | **24,201** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: active in-window omnibox suggestion flows. |
| **S0049** | `human` | T2 | P02 | nan | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0050** | `human` | T3 | P02 | fastly-edge (SafeBrowsing OHTTP) | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0051** | `human` | T4 | P02 | Chrome Services (update/telemetry); fastly-edge (SafeBrowsing OHTTP) | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0052** | `human` | T1 | P02 | Chrome Services (update/telemetry); fastly-edge (SafeBrowsing OHTTP) | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0053** | `human` | T1 | P02 | Chrome Services (update/telemetry); fastly-edge (SafeBrowsing OHTTP) | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0054** | `human` | T4 | P02 | Chrome Services (update/telemetry) | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0055** | `human` | T3 | P02 | Chrome Services (update/telemetry); fastly-edge (SafeBrowsing OHTTP) | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0056** | `human` | T2 | P02 | Chrome Services (update/telemetry) | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0057** | `human` | T3 | P03 | Chrome Services (update/telemetry); fastly-edge (SafeBrowsing OHTTP) | None (direct task navigation / bookmark) | `os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0058** | `human` | T4 | P03 | Chrome Services (update/telemetry); www.google.com (DNS/TLS); fastly-edge (SafeBrowsing OHTTP) | Omnibox search suggestion: short query keystroke | `website+search+os_background+unknown` | **356** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: active in-window omnibox suggestion flows. |
| **S0059** | `human` | T1 | P03 | Chrome Services (update/telemetry) | None (direct task navigation / bookmark) | `os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0060** | `human` | T2 | P03 | nan | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0061** | `human` | T2 | P03 | Chrome Services (update/telemetry); www.google.com (DNS/TLS) | Speculative preconnect only (no query strings; 0 search bytes) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0062** | `human` | T1 | P03 | Chrome Services (update/telemetry); www.google.com (DNS/TLS) | NetLog omnibox search query: 'The Quiet Letter' / poetry | `website+search+os_background+unknown` | **38,943** | PCAP (in-window SNI/DNS) + NetLog | Excluded from primary (N=91, excluded=1); evaluated in reconstructed sensitivity (N=92). |
| **S0063** | `human` | T4 | P03 | nan | None (direct task navigation / bookmark) | `os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0064** | `human` | T3 | P03 | nan | None (direct task navigation / bookmark) | `unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0065** | `human` | T4 | P04 | fastly-edge (SafeBrowsing OHTTP) | None (direct task navigation / bookmark) | `os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0066** | `human` | T1 | P04 | Chrome Services (update/telemetry); fastly-edge (SafeBrowsing OHTTP) | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0067** | `human` | T2 | P04 | Chrome Services (update/telemetry) | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0068** | `human` | T3 | P04 | fastly-edge (SafeBrowsing OHTTP) | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0069** | `human` | T1 | P05 | Chrome Services (update/telemetry) | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0070** | `human` | T2 | P05 | Chrome Services (update/telemetry); www.google.com (DNS/TLS) | Omnibox search query: Apollo 11 mission query | `website+search+os_background+unknown` | **25,691** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: active in-window omnibox suggestion flows. |
| **S0071** | `human` | T3 | P05 | nan | None (direct task navigation / bookmark) | `os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0072** | `human` | T4 | P05 | nan | None (direct task navigation / bookmark) | `os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0073** | `human` | T2 | P06 | nan | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0074** | `human` | T3 | P06 | nan | None (direct task navigation / bookmark) | `os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0075** | `human` | T4 | P06 | Chrome Services (update/telemetry); www.google.com (DNS/TLS) | Omnibox search query: task form / store search | `website+search+os_background+unknown` | **13,220** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: active in-window omnibox suggestion flows. |
| **S0076** | `human` | T1 | P06 | Chrome Services (update/telemetry); fastly-edge (SafeBrowsing OHTTP) | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0077** | `human` | T3 | P07 | Chrome Services (update/telemetry); fastly-edge (SafeBrowsing OHTTP) | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0078** | `human` | T4 | P07 | Chrome Services (update/telemetry); fastly-edge (SafeBrowsing OHTTP) | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0079** | `human` | T1 | P07 | Chrome Services (update/telemetry); fastly-edge (SafeBrowsing OHTTP) | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0080** | `human` | T2 | P07 | Chrome Services (update/telemetry) | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0081** | `human` | T4 | P08 | www.google.com (DNS/TLS) | Omnibox search query: task form / store search | `search+os_background+unknown` | **13,930** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: active in-window omnibox suggestion flows. |
| **S0082** | `human` | T1 | P08 | Chrome Services (update/telemetry) | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0083** | `human` | T2 | P08 | Chrome Services (update/telemetry) | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0084** | `human` | T3 | P08 | Chrome Services (update/telemetry); fastly-edge (SafeBrowsing OHTTP) | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0085** | `human` | T1 | P09 | Chrome Services (update/telemetry); fastly-edge (SafeBrowsing OHTTP) | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0086** | `human` | T2 | P09 | Chrome Services (update/telemetry) | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0087** | `human` | T3 | P09 | nan | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0088** | `human` | T4 | P09 | Chrome Services (update/telemetry); www.google.com (DNS/TLS) | Omnibox search query: task form / store search | `search+os_background+unknown` | **13,222** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: active in-window omnibox suggestion flows. |
| **S0089** | `human` | T2 | P10 | nan | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0090** | `human` | T3 | P10 | nan | None (direct task navigation / bookmark) | `os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0091** | `human` | T4 | P10 | Chrome Services (update/telemetry) | None (direct task navigation / bookmark) | `website+os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |
| **S0092** | `human` | T1 | P10 | nan | None (direct task navigation / bookmark) | `os_background+unknown` | **0** | PCAP (in-window SNI/DNS) + NetLog | Included in primary (N=91). Search class: 0 B (no active search flows in-window). |

---

## 2. Label Corrections Audit & Ground Truth Integrity

### 2.1 Audit of 18 November `label_corrections.csv`
The authoritative label corrections file in `C:\pilot-v1-data\metadata\label_corrections.csv` and `C:\pilot-v1-data\data\label_corrections.csv` was verified:
- **Total Correction Records:** Exactly 14 rows.
- **Columns Modified:**
  - `answer_given`: 13 rows (S0004, S0006, S0009, S0015, S0019, S0023, S0028, S0031, S0034, S0037, S0011, S0048, S0059). All 13 corrections reflect expanded verbatim operator transcription from `agent_result.json` or NetLog; every row explicitly notes: *"Outcome success unchanged."*
  - `excluded`: 1 row (S0062). Old value: `0`, New value: `1`. Reason: Missing ground truth markers require NetLog window reconstruction.
- **Sample Population Verification:**
  - **Primary Analysis Population:** Filters strictly on `excluded == 0` (and `session_id != 'S0062'`). Evaluates **$N = 91$ sessions** (40 AI, 51 Human).
  - **Reconstructed Window Sensitivity Population:** Evaluates **$N = 92$ sessions** (40 AI, 52 Human) including S0062 with features extracted from its 1,048 NetLog-reconstructed packets.
- **Integrity Assertion:** Zero unrelated columns, controllers, task IDs, outcomes, or participant IDs were altered.

### 2.2 Cryptographic File Hashes (Outside Git)
All raw ground truth and session metadata remain strictly outside Git in `C:\pilot-v1-data\`. Their SHA256 hashes are:
- `C:\pilot-v1-data\data\sessions.csv`:  
  `a648da5155d71fa4f02895c0e410c1a51127d60dd5ddd0611246f55a8b545188`
- `C:\pilot-v1-data\data\label_corrections.csv`:  
  `3c2ef0dff3e38cae9a4c7ff8ecc008f492e9999dcd4472bb7a67e8a52ad8ecbb`

---

## 3. Unknown Byte Accounting & 5% Threshold Analysis

### 3.1 Five-Class In-Window Byte Accounting Summary

| Population / Controller | Website Bytes | Search Bytes | OS Background Bytes | Vendor API Bytes | Unknown Bytes | Total In-Window Bytes | Unknown / Total | Unknown / Website |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Primary Human ($N=51$)** | 8,455,411 (2.56%) | 102,144 (0.03%) | 282,031,240 (85.46%) | 0 (0.00%) | **39,432,052 (11.95%)** | 330,020,847 | **11.95%** | **4.664** |
| **Primary Agent ($N=40$)** | 10,184,187 (11.95%) | 0 (0.00%) | 1,336,597 (1.57%) | 63,329,103 (74.34%) | **10,342,989 (12.14%)** | 85,192,876 | **12.14%** | **1.016** |
| **All Human ($N=52$, w/ S0062)** | 8,525,954 (2.58%) | 141,087 (0.04%) | 282,238,423 (85.43%) | 0 (0.00%) | **39,476,732 (11.95%)** | 330,382,196 | **11.95%** | **4.630** |
| **All Agent ($N=40$)** | 10,184,187 (11.95%) | 0 (0.00%) | 1,336,597 (1.57%) | 63,329,103 (74.34%) | **10,342,989 (12.14%)** | 85,192,876 | **12.14%** | **1.016** |

### 3.2 Analysis of the 5% Unknown Threshold
- **Human Sessions:** In the primary dataset, **28 of 51 sessions ($54.9\%$)** exhibit unknown bytes exceeding 5% of in-window traffic. In Task 2 (Wikipedia), heavy media and CDN asset downloads through preconnected sockets result in an unknown byte share reaching $26.4\%$ (S0042) to $96.7\%$ (S0047).
- **AI Agent Sessions:** **30 of 40 sessions ($75.0\%$)** exhibit unknown bytes exceeding 5% of in-window traffic, with a median unknown volume of ~150 KB.
- **Technical Root Cause:**
  1. *Pre-Window Connection Reuse:* When Chrome establishes persistent keep-alive TCP connections prior to the in-window start marker, the TLS ClientHello packet is not captured within the marker window. In the absence of an in-window ClientHello SNI or in-window DNS query, the zero-payload classifier cannot inspect layer-7 application data and appropriately classifies the flow as `unknown` rather than guessing.
  2. *Asymmetric Server-to-Client Packets:* Server response packets to client dynamic ports whose handshake was outside the window fall into unknown classification.
  3. *Unresolved Telemetry Proxies:* Chrome Safe Browsing OHTTP relay connections via Fastly edge endpoints are intentionally directed to `unknown`.

### 3.3 NetLog Audit of Unresolved Domains
As mandated by Addendum 07 §4, unresolved domains were cross-referenced against NetLog ground truth:
1. **`fastly-edge.com`:** Confirmed present in 69 of 92 session NetLogs. NetLog request entries confirm 100% of these URLs are `https://ohttp-relay-safebrowsing-chrome.google.fastly-edge.com/` (Chrome Safe Browsing Oblivious HTTP relay proxy). They are browser background security queries, not task website traffic.
2. **`cloudflare-ech.com`:** Confirmed to have zero active HTTP requests or TCP/QUIC socket connections. It appeared strictly as text in Wikipedia's Content-Security-Policy (CSP) response headers (`cdnjs.cloudflare.com`). PCAP ECH outer handshake trials appropriately fall through to `unknown`.

---

## 4. Scientific Wording & Limitations Audit

All reports, memos, and claim indices were updated to eliminate overstatements and preserve required scientific caveats:

1. **Family Dropout Attribution:**
   - *Previous Text:* "Micro-temporal pacing ($T$) is the sole essential behavioral driver in B6."
   - *Corrected Scientific Text:* "Feature family dropout indicates that within the tested six-feature representation, micro-temporal pacing ($T$) is the primary source of separability in B6: dropping timing features collapses LOPO AUROC to $0.456$ (below chance), whereas dropping volume ($V$) or concurrency ($C$) produces minimal degradation ($0.590$ and $0.645$). This reflects feature sensitivity within the evaluated feature space rather than proving that non-temporal signals could never discriminate."

2. **Random Forest Role:**
   - Clarified across `B_to_C_MEMO.md` (§7, §10) and `FINAL_RESEARCH_REPORT_PERSON_B.md` (§14) that the 500-tree Random Forest check serves as an alternative non-linear classifier check on the six website features (achieving LOPO $\text{AUROC} = 0.744$ and LOTO $\text{AUROC} = 0.624$). It is **not** described as independently confirming timing importance because separate RF feature ablation/importance was not preregistered.

3. **NC1 Negative Control Interpretation:**
   - Clarified that while NC1 LOTO centers near chance ($0.487 \approx 0.50$), treating it as an unbiased benchmark requires the assumptions of label exchangeability within task groups and balanced fold calibration. Under LOPO, the depressed null mean ($0.417$) is explicitly documented as an artifact of pooling predicted probabilities across unequal participant clusters.

4. **Prominence of the Five Core Methodological Limitations:**
   The five required limitations are explicitly documented in Section 20 of `FINAL_RESEARCH_REPORT_PERSON_B.md` and Section 11 of `B_to_C_MEMO.md`:
   - **Limitation 1 (Duration Confound Dominance):** B4 length baseline LOTO $\text{AUROC} = 0.725$, outperforming B6 ($0.606$). On unseen tasks, session length separates at least as well as micro-timing.
   - **Limitation 2 (Un-Interleaved Day Confound):** AI captured on 6 Nov; Humans on 7 and 9 Nov.
   - **Limitation 3 (B2 JA4 Fingerprinting NOT RUN):** Marked `NOT RUN` under DEV-08.
   - **Limitation 4 (TCP Handshake RTT Retraction):** Retracted under DEV-06 as an unmeasured benchmark constant.
   - **Limitation 5 (B7 Equivalence to B6):** B7 reuses B6 features formatted as rates/ratios, producing identical metrics under DEV-07.

---

## 5. Final Recommendations and Handover Protocol for Person C and Person D

1. **Acceptance of Handover:** Person B certifies that all five reconciliation criteria are fully satisfied. The 27-vs-7 search discrepancy is exhaustively explained with per-session evidence, label corrections are verified, byte accounting is documented, and scientific caveats are enforced.
2. **Usage by Person C:** Person C should incorporate the 5-class byte accounting table and the updated family-dropout attribution text into the synthesis document and interpretation memo.
3. **Usage by Person D:** Person D can reproduce the entire analysis from `review/data-provider-corrections-2026-11-17` commit `3397b19` (or its subsequent reconciliation commit). All unit and integration tests pass 37/37.
