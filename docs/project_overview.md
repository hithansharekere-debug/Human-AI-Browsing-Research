# Project Overview: Human vs. AI-Agent Browsing at the Client Egress

## 1. Context and Problem Statement

The emergence of autonomous AI web agents (e.g., browser-use, agentic browsing assistants, automated web shoppers) represents a fundamental shift in client-side web interaction. Traditional human browsing is characterized by stochastic cognitive pauses, visual parsing delays, variable scroll intervals, and distinct multi-tab burst dynamics. In contrast, AI agents execute DOM actions, page transitions, and query dispatches according to programmatic control loops, tool-calling latencies, and machine comprehension speeds.

This study investigates whether and how **Human Browsing** and **AI-Agent Browsing** diverge when observed strictly at the **client egress** (the local network edge / outbound network interface before external NAT or ISP routing).

## 2. Research Roles & Division of Responsibilities

```
+---------------------------------------------------------------------------------+
|                                 RESEARCH TEAM                                   |
+------------------------+--------------------------------+-----------------------+
| Person A               | Person B (Current Role)        | Person C              |
| Data Acquisition Lead  | Analysis Lead                  | Reviewer / Recipient  |
+------------------------+--------------------------------+-----------------------+
| - Study execution (92  | - Frozen dataset verification  | - Independent review  |
|   browsing sessions)   | - Flow & window extraction     | - Methodological      |
| - Packet capture &     | - Feature engineering          |   audit & replication |
|   ground truth logging | - Preregistered statistics     | - Paper synthesis &   |
| - Dataset freezing &   | - Robustness & sensitivity     |   decision evaluation |
|   checksum generation  | - Reproducibility packaging    |                       |
+------------------------+--------------------------------+-----------------------+
```

## 3. Core Hypotheses (High-Level)

1. **H1 (Temporal Micro-Dynamics):** AI-agent browsing exhibits significantly lower inter-request jitter and different inter-burst idle distributions compared to human browsing under matched browsing objectives.
2. **H2 (Volumetric & Flow Concurrency):** AI-agent browsing generates distinct concurrent flow-arrival densities and request-pipelining structures at the transport layer due to rapid API calls and headless asset rendering patterns.
3. **H3 (Egress Detectability & Robustness):** Classifiers trained on egress flow summary features can discriminate human from AI sessions above chance, but performance degrades under simulated network jitter and window-truncation negative controls.

## 4. Scope and Guardrails

- **Zero Data Contamination:** The raw dataset collected by Person A remains untouched, write-protected, and strictly outside the git tree.
- **Hypothesis Separation:** Exploratory analyses must be explicitly partitioned from confirmatory tests documented in `analysis/PREREG.md`. Any divergence is logged in `analysis/DEVIATIONS.md`.
- **Pre-execution Phase:** No session processing or feature extraction is executed on the 92 study sessions until the foundational pipeline is fully reviewed and verified.
