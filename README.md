# Human vs. AI-Agent Browsing at the Client Egress

**Analysis Lead:** Person B  
**Dataset Provider:** Person A (Frozen Egress Network Dataset)  
**Deliverable Recipient:** Person C (Final Synthesis & Independent Audit)  

---

## 1. Executive Overview

This repository hosts the reproducible, modular data science and statistical analysis pipeline for the study: **"Human vs. AI-Agent Browsing at the Client Egress"**.

The goal of this research package is to ingest Person A's frozen, verified egress network traces, perform rigorous session windowing, flow extraction, feature engineering, hypothesis testing, model evaluation, negative controls, and sensitivity analyses, and output an auditable evidence package for Person C.

```
+------------------+         +-------------------------------+         +------------------+
| Person A         |         | Person B (This Repository)    |         | Person C         |
| Frozen Dataset   | ------> | Pipeline & Statistical Study  | ------> | Synthesis &      |
| (Read-Only Ext.) |         | Verification -> Results -> QA |         | Audit Evaluation |
+------------------+         +-------------------------------+         +------------------+
```

---

## 2. Data Security & Ethical Boundaries

Strict data governance policies are enforced across this repository:
1. **External Raw Dataset**: Raw `.pcap`, packet archives, and sensitive raw traces are strictly hosted **outside** this repository directory tree. No `raw_data/` folder exists inside version control.
2. **Zero PII & Network Egress Shielding**: Logs, reports, and exported figures must never display raw IP addresses, MAC addresses, participant identifiers, or raw packet payloads. All entities must be keyed via blinded session/flow identifiers.
3. **No Intermediate Secret or Credential Leakage**: No API keys, credentials, or host-specific paths are tracked in git. All paths are parameterized via YAML configuration files or environment variables.
4. **Reproducible Frozen State**: Analysis must only operate on explicitly verified and checksum-validated datasets.

---

## 3. Repository Architecture

```
Human-AI-Browsing-Research/
├── .gitignore                    # Exclusion rules for pcaps, caches, secrets & output data
├── pyproject.toml                # Project metadata & build tool configuration
├── requirements.txt              # Pinned core dependencies
├── README.md                     # High-level project architecture & execution guide
├── config/                       # Pipeline run configurations
│   └── pilot_v1.yaml             # Pilot configuration template & parameter constraints
├── docs/                         # Governance & methodological specifications
│   ├── project_overview.md       # High-level research context and objectives
│   ├── data_handling_security.md # Ingestion rules, anonymization and integrity checks
│   ├── workflow.md               # End-to-end execution workflow (B -> C handover)
│   └── final_deliverables.md     # Package checklist for Person C
├── features/                     # Feature specifications & flow parsing definitions
│   ├── SPEC.md                   # Formal definitions of extracted features
│   └── flow_rules.yaml           # Layer-4/7 flow aggregation and protocol filter rules
├── analysis/                     # Preregistration and audit documents
│   ├── PREREG.md                 # Preregistered hypotheses, tests, and thresholds
│   └── DEVIATIONS.md             # Formal deviation log tracking any methodological changes
├── src/                          # Modular Python source library
│   ├── __init__.py
│   ├── utils/                    # Common utilities (logging, path validation, hashing)
│   │   ├── __init__.py
│   │   ├── logging_config.py     # Secure, sanitized logging handler
│   │   └── paths.py              # Pathlib-based path resolver
│   └── pipeline/                 # Core sequential pipeline components
│       ├── __init__.py
│       ├── dataset_verification.py  # Checksum validation & frozen state verification
│       ├── window_extraction.py     # Session window segmentation
│       ├── flow_extraction.py       # Bidirectional flow parsing (via nfstream)
│       ├── flow_classification.py   # Flow protocol/traffic typing & classification
│       ├── feature_engineering.py   # Statistical & temporal feature extraction
│       ├── statistics.py            # Parametric / non-parametric hypothesis testing
│       ├── model_evaluation.py      # Classifier evaluation & calibration
│       ├── negative_controls.py     # Permutation & label-shuffle negative controls
│       ├── sensitivity_analysis.py  # Window length & threshold perturbation tests
│       ├── reproducibility.py       # Environment capture & hash artifact generator
│       └── runner.py                # Pipeline orchestrator
├── scripts/                      # Executable CLI entry points
│   ├── verify_environment.py     # Sanity check for environment and dependencies
│   └── run_pipeline.py           # Pipeline runner entrypoint
├── tests/                        # Comprehensive unit & integration tests
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_imports.py
│   └── test_verification.py
├── reports/                      # Academic outputs and stakeholder communications
│   ├── methods_section.tex       # LaTeX draft of the methods section
│   ├── B_to_C_MEMO.md            # Handover memo from Person B to Person C
│   └── report_outline.md         # Comprehensive outline for the final report
├── results/                      # Generated tables, metrics and summary statistics
├── figures/                      # High-resolution generated charts and diagrams
└── output/                       # Audit logs, run manifests, and checksum bundles
```

---

## 4. Setup & Installation

### Prerequisites
- Python 3.10+ (Recommended: Python 3.11 or 3.12)
- Virtual environment tool (`venv`)
- External path to Person A's frozen dataset directory

### Environment Setup (Windows PowerShell)

```powershell
# 1. Create a dedicated virtual environment
python -m venv venv

# 2. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 3. Upgrade pip, setuptools, and wheel
python -m pip install --upgrade pip setuptools wheel

# 4. Install dependencies
pip install -r requirements.txt

# 5. Install project in editable mode
pip install -e .

# 6. Verify environment and modules
python scripts/verify_environment.py
```

---

## 5. Execution Model

The pipeline is staged in sequential, decoupled phases:

```
[External Dataset]
       │
       ▼
[Phase 1: Verification] ──> Checksum & schema confirmation
       │
       ▼
[Phase 2: Windowing & Flows] ──> Temporal slices & bidirectional flows (nfstream)
       │
       ▼
[Phase 3: Features] ──> Egress temporal, volumetric & burst statistics
       │
       ▼
[Phase 4: Statistical Testing] ──> Preregistered hypothesis evaluation
       │
       ▼
[Phase 5: Negative Controls & Sensitivity] ──> Null validation & threshold robustness
       │
       ▼
[Phase 6: Artifact Handover] ──> Reproducibility bundle for Person C
```

Run verification and pipeline testing:
```powershell
# Run automated tests
pytest -v

# Run verification pipeline with a target config
python scripts/run_pipeline.py --config config/pilot_v1.yaml --dry-run
```

---

## 6. Research Governance Reminder

> **CRITICAL DIRECTIVE**:
> In accordance with research protocol, feature calculation and empirical analysis of the 92 study sessions are deferred until Person A's frozen dataset manifest has completed verification and Person C has approved the preregistered plan (`analysis/PREREG.md`).
