# Feature Specification (features/SPEC.md)

**Project:** Human vs. AI-Agent Browsing at the Client Egress  
**Author:** Person B (Analysis Lead)  
**Status:** Pre-Gate 2 Specification (Reconciled with Authoritative Handover & Blueprint)  
**Target Output:** `processed/session_features.parquet` (one row per session, 92 rows)

---

## 1. Analysis Window Definition

The analysis window for each session is defined strictly by the **hardware-timed UDP marker packets** recorded within the packet capture (`.pcapng`):
- **Window Start ($t_{\text{start}}$):** Timestamp of the START marker packet (`ip.dst == 192.0.2.1 && udp.payload =~ "P1MARK START <session_id>"`).
- **Window End ($t_{\text{end}}$):** Timestamp of the END marker packet (`ip.dst == 192.0.2.1 && udp.payload =~ "P1MARK END <session_id>"`).
- **Marker Packet Handling:** The two marker packets themselves are strictly dropped before computing features (`flt = frame.time_epoch > s && frame.time_epoch < e && !(ip.dst == 192.0.2.1)`).
- **Traffic Outside Window:** Traffic preceding $t_{\text{start}}$ (Chrome profile launch, 30s settle, 10s quiet) and traffic succeeding $t_{\text{end}}$ (10s quiet, Chrome shutdown) are excluded from feature calculation.
- **Protocol Scope:** Both **IPv4** and **IPv6** packets are retained (IPv6 accounts for ~98% of in-window traffic).
- **Loopback Traffic:** Local loopback (`127.0.0.0/8`, `::1`) is excluded.
- **Arbitrary Windowing Prohibition:** Arbitrary fixed 30-second temporal windows are **not used** for session features. The session window is variable-length matching the actual task execution interval.

---

## 2. Flow Reassembly & Scoping

- **Reassembly Engine:** `NFStreamer` bidirectional 5-tuple (`source=window_pcap`, `idle_timeout=30`, `active_timeout=1800`, `statistical_analysis=True`, `splt_analysis=0`).
  - Fallback engine: Custom flow builder from `tshark` packet table (5-tuple, 30s idle timeout) if NFStream is unavailable on Windows host.
- **Window Clipping:** Any flow initiating before or active after the marker boundaries is clipped strictly to $[t_{\text{start}}, t_{\text{end}}]$. Only in-window packets and bytes are aggregated.
- **Flow Classes:** Flows are partitioned into 5 classes via `features/flow_rules.yaml` following strict precedence:
  1. `vendor` (Family A)
  2. `search` (Family D)
  3. `os_background`
  4. `website` (Primary analysis scope)
  5. `unknown` (Default for unclassified flows)
- **LAN Traffic Exclusion:** All local discovery protocols (mDNS, SSDP, LLMNR, NetBIOS/SMB), broadcast (`192.168.1.255`), and LAN hostnames (`*.local`, `Android.local`, `wpad.domain.name`, `Cal`) are dropped before flow reassembly. (DHCP and NTP are not excluded as neither is justified by authoritative documents).

---

## 3. Feature Schema & Family Definitions

Every feature column carries its family prefix. Identifier columns have no prefix:
`session_id`, `controller`, `participant_id`, `task_id`, `rep`, `outcome`, `excluded`.

### Primary Feature Families (Computed on `website` Flows Only)

The headline baseline **$B6$** is trained exclusively on standardized features from families $T$, $V$, and $C$.

| Family | Column Name | Type | Priority | Description & Mathematical Definition |
|---|---|---|---|---|
| **T (Timing)** | `T_idle_gap_median` | float | Primary | Median duration (seconds) of idle pauses $\ge \theta_i$ ($500\text{ ms}$) between active bursts ($\theta_b = 100\text{ ms}$) on website flows. |
| | `T_idle_gap_cv` | float | Primary | Coefficient of variation ($\sigma / \mu$) of idle pause durations. |
| | `T_idle_gap_entropy` | float | Primary | Shannon entropy computed across 12 $\log_{10}$-spaced bins of idle gaps from $0.5\text{ s}$ to $120\text{ s}$. |
| | `T_burst_rate` | float | Primary | Number of packet bursts per minute of active session time on website flows. |
| | `T_gap_autocorr_lag1` | float | Exploratory | Lag-1 autocorrelation of consecutive idle pause durations. |
| | `T_vendor_to_website_lag_s`| float | B8 Only | Latency (seconds) between the final vendor response packet and the first website request packet. |
| **V (Volume)** | `V_up_down_ratio` | float | Primary | Ratio of outbound (upload) bytes to inbound (download) bytes on website flows: $B_{\text{out}} / (B_{\text{in}} + \epsilon)$. |
| | `V_upload_burst_share`| float | Primary | Fraction of website upload bursts where upstream bytes > downstream bytes. |
| **C (Connections)**| `C_new_flows_per_min` | float | Primary | Rate of new website flow initiations per minute: $N_{\text{flows}} / (L_{\text{duration\_s}} / 60)$. |
| | `C_max_concurrent` | int | Primary | Maximum instantaneous number of simultaneously active website flows. |
| | `C_quic_share` | float | Control | Fraction of website flows utilizing QUIC (HTTP/3) transport (sanity check). |

#### Frozen Primary B6 Feature Set & Resolution of the Feature-Count Constraint
- **Constraint & Rationale:** Blueprint §6.2 and Handover Step 6 require $\le 6$ standardized features for the primary Logistic Regression model to maintain adequate degrees of freedom ($N_{\text{train}} \approx 70\text{--}80$ sessions across grouped splits) and prevent coefficient instability under cluster bootstrap.
- **Explicit Resolution (Approved Pre-Registered Primary Model `B6_core6`):**
  The primary $B6$ model is frozen to **exactly six standardized primary features** ($2T + 2V + 2C$):
  1. $T$: `T_idle_gap_median`
  2. $T$: `T_burst_rate`
  3. $V$: `V_up_down_ratio`
  4. $V$: `V_upload_burst_share`
  5. $C$: `C_new_flows_per_min`
  6. $C$: `C_max_concurrent`
- **Methodological Guarantees:**
  - Selected purely a priori based on domain coverage and mathematical interpretability (central tendency and frequency of interaction, volume asymmetry and burstiness, connection birth rate and concurrency).
  - Selected **without** any reference to study session outcomes or empirical performance.
  - Model parameters: $L_2$ Logistic Regression, $C=1.0$, `solver='lbfgs'`, no tuning.
  - **No 8-feature Logistic Regression model will be fitted as a primary or secondary model.**
- **Random Forest Secondary Check:**
  - Uses the **exact same six core features** as the primary model.
  - Hyperparameters: 500 trees, `max_features='sqrt'`, fixed seed `20261106`, no tuning.
  - Serves strictly as an algorithmic consistency check, **never the headline model**.
- **Role of Remaining T/V/C Candidates:**
  - Higher-order moments (`T_idle_gap_cv`, `T_idle_gap_entropy`), exploratory features (`T_gap_autocorr_lag1`), and control ratios (`C_quic_share`) are reserved strictly for pre-specified family dropout and sensitivity analyses. They are never silently added to the primary model.

---

### Shortcut, Control, and Diagnostic Families

| Family | Column Name | Role | Description |
|---|---|---|---|
| **A (Vendor)** | `A_vendor_present` | Shortcut B1 | Binary flag (0/1): presence of Gemini API (`generativelanguage.googleapis.com`) or Datadog telemetry. |
| | `A_vendor_bytes` | Shortcut B1 | Total bytes exchanged with agent vendor endpoints. |
| **H (Handshake)**| `H_ja4_mode` | Design Check B2 | Modal JA4 TLS ClientHello fingerprint string on website flows. |
| | `H_ja4_n_distinct` | Design Check B2 | Count of unique JA4 fingerprints on website flows. |
| **D (Destinations)**| `D_dest_count` | Shortcut B3 | Number of distinct destination IP/host endpoints. |
| | `D_search_present` | Shortcut B3 | Binary flag (0/1): presence of Google omnibox search suggestions (`F2`). |
| **L (Length)** | `L_duration_s` | Control B4 | Total observation window length in seconds ($t_{\text{end}} - t_{\text{start}}$). Never a behavioural feature. |
| | `L_total_bytes` | Control B4 | Total bytes across all flows in session window. |
| | `L_n_flows` | Control B4 | Total flow count across all flow classes in window. |
| **Q (Diagnostics)**| `Q_background_bytes`| Monitor | Total bytes attributed to `os_background` (Spotify, OS telemetry, Edge news feed). **Never in any model.** |
| | `Q_gvt1_bytes` | Monitor | Chrome component updater bytes (`edgedl.me.gvt1.com`, `F1`). **Never in any model.** |
| | `Q_edge_present` | Monitor | Binary flag: heavy MSN/Edge news feed presence (S0044, S0068, S0081). **Never in any model.** |

---

## 4. Session Exclusions & Protocol

### Primary Exclusion: S0062
- **Session:** `S0062` (Participant `P03`, Task `T1`, round 2).
- **Defect:** Window duration is $0.007\text{ s}$ due to premature ENTER press; task execution occurred after the END marker.
- **Primary Analysis Policy:** Excluded from primary analysis dataset ($N = 91$).
- **Sensitivity Analysis Policy:** Retained in sensitivity analysis by recomputing its window boundaries from Chrome NetLog's first and last request timestamps ($N = 92$).
- **Ingestion Integrity:** `sessions.csv` is preserved strictly read-only. The exclusion flag (`excluded=1`) is applied via the analysis pipeline without modifying the raw ledger.
