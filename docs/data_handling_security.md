# Data Handling, Privacy, and Security Protocol

## 1. Physical & Logical Storage Boundaries

1. **External Ingestion Only**:
   - The raw dataset provided by Person A resides exclusively on an external, write-protected storage path (e.g., local external drive or dedicated read-only filesystem mount).
   - Under no circumstances should raw `.pcap`, `.pcapng`, or un-anonymized capture archives be copied, committed, or moved into this repository.

2. **No Repository Data Blobs**:
   - All directories inside the repository (`data/`, `raw/`, `results/`, `output/`) are subject to strict exclusion via `.gitignore`.
   - Only `.gitkeep` and schema/specification files are retained under version control.

## 2. Privacy & Network Egress Shielding (Anonymization Policy)

Network traces captured at client egress can contain sensitive participant data, external endpoints, and internal network architecture details. To safeguard privacy and prevent accidental leaks:

1. **IP & Hardware Address Scrubbing**:
   - Source IP addresses, client MAC addresses, and specific internal gateway subnets must never appear in pipeline console logs, debug messages, tabular exports, or visualization labels.
   - Any required network endpoint analysis must use salted cryptographic hashing (e.g., `HMAC-SHA256(ip, salt)` with an ephemeral run salt) or categorical abstraction (e.g., `local_egress`, `remote_endpoint_cluster_K`).

2. **Zero Payload Logging**:
   - Packet payload inspection is strictly out of scope. Feature extraction is restricted to layer-3/layer-4 transport headers, packet inter-arrival times, packet lengths, directionality, and flow duration.
   - HTTP/HTTPS payload bodies, query parameters, cookies, and bearer tokens must never be logged, stored, or inspected.

3. **Participant Identity De-coupling**:
   - Session identifiers are standardized as blinded keys: `SESSION_[H|A]_[0-9]{3}` (e.g., `SESSION_H_014` for Human, `SESSION_A_089` for AI).
   - Mapping between participant identities and session IDs is maintained exclusively by Person A in an offline, air-gapped key file.

## 3. Data Integrity & Verification

1. **Cryptographic Checksumming**:
   - Prior to pipeline execution, Person A delivers an immutable manifest file (`manifest.sha256`) containing SHA-256 hashes for every session archive.
   - The `dataset_verification` module verifies every file against this manifest before granting read access.
   - Any hash mismatch or timestamp irregularity immediately halts pipeline execution.

2. **Read-Only Ingestion**:
   - All file handles accessing Person A's dataset are opened with strict read-only flags (`mode="rb"`).
   - The pipeline writes results exclusively to the project's designated output paths (`results/` or `output/`), never back to the source directory.

## 4. Secret & Credential Management

- This research project uses zero external API keys or remote telemetry credentials.
- No secrets, tokens, or environment files (`.env`) are permitted in version control.
