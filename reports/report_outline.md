# Research Report Outline

**Study Title:** Human vs. AI-Agent Browsing at the Client Egress  
**Target Venue:** IEEE S&P / USENIX Security / ACM IMC  
**Primary Authors:** Person A, Person B, Person C  

---

## 1. Introduction
- Background: Proliferation of autonomous AI agents interacting with web services via browser automation.
- Problem: Can external or network edge observers distinguish human from agent browsing using client egress traffic alone?
- Threat model and practical significance (e.g., bot detection, fraud prevention, privacy leakage, automated web compliance).
- Summary of findings: Key temporal, burst, and concurrency differentials observed.

## 2. Experimental Setup and Data Provenance
- Acquisition protocol (Person A): Controlled collection environment, matched browsing tasks (search, e-commerce, multi-step navigation).
- Cohort description: 92 sessions ($n_H = 46$ Human, $n_A = 46$ Agent).
- Data integrity, hashing, and isolation protocol.

## 3. Analysis Pipeline & Egress Feature Architecture
- Client egress network boundary: Inbound vs. Outbound perspective.
- Temporal windowing ($T_w = 30\text{ s}$) and bidirectional flow reconstruction (nfstream).
- Feature domain formulation:
  - Volumetric asymmetry and packet count dynamics.
  - Temporal micro-jitter: IAT skewness, dispersion, and tail percentiles.
  - Concurrency profiles: Peak and average simultaneous active flows.
  - Burst-pause dynamics: Quantifying user think-time vs. agent processing latency.

## 4. Preregistered Statistical Results
- Confirmatory Hypothesis 1: Pause variability and outbound timing regularity (Mann-Whitney U, Cliff's delta).
- Confirmatory Hypothesis 2: Flow concurrency and burst arrival density (Welch's t-test).
- Multiple comparisons adjustment: Benjamini-Hochberg FDR control ($q = 0.05$).
- Summary tables and empirical CDFs.

## 5. Machine Learning Discrimination & Robustness
- Classifiers: Regularized Logistic Regression and Random Forests under Stratified Group K-Fold CV.
- ROC-AUC, Precision-Recall curves, and Brier calibration scores.
- Negative controls: Label permutation test ($B = 1,000$) and synthetic Poisson baseline verification.
- Sensitivity analysis: Window size sweep ($5\text{ s}$ to $60\text{ s}$) and pause threshold perturbation ($0.5\text{ s}$ to $5.0\text{ s}$).

## 6. Discussion and Practical Implications
- Fundamental limits of client egress observability.
- The role of network jitter, background OS traffic, and caching in obscuring behavioral signatures.
- Countermeasures: How agents can camouflage egress signatures (e.g., synthetic jitter injection, human pause simulation).

## 7. Threats to Validity & Limitations
- Task selection bias and browser headless mode idiosyncrasies.
- Dataset scale ($N = 92$) and external generalizability.
- Strict accounting of any deviations recorded in `analysis/DEVIATIONS.md`.

## 8. Conclusion & Reproducibility Statement
- Final summary of insights.
- Availability of reproducible pipeline, container environment, and verification manifests.
