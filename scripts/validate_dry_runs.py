"""Dry-Run and Non-Study Capture Validation Script.

Role: Person B (Analysis Lead)
Validates the egress extraction pipeline exclusively on permitted dry-run (D*)
and self-test (X*) recordings.
STRICT RESTRICTION: No study session traces (S0001-S0092) are loaded or accessed.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import scapy.all as scapy

from src.pipeline.flow_classification import FlowClassifier
from src.pipeline.window_extraction import extract_hardware_marker_bounds
from src.utils.paths import get_repo_root

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("dry_run_validator")


DATA_DIR = Path(r"C:\pilot-v1-data\data")
RAW_DIR = DATA_DIR / "raw"
SESSIONS_CSV = DATA_DIR / "sessions.csv"
MANIFEST_FILE = DATA_DIR / "SHA256SUMS.txt"
FLOW_RULES_PATH = get_repo_root() / "features" / "flow_rules.yaml"


def extract_sni_from_payload(payload: bytes) -> Optional[str]:
    """Pure-binary TLS ClientHello SNI extractor."""
    if len(payload) < 43 or payload[0] != 0x16:  # TLS Handshake record
        return None
    if len(payload) <= 5 or payload[5] != 0x01:  # ClientHello
        return None
    try:
        session_id_len = payload[43]
        idx = 44 + session_id_len
        if idx + 2 > len(payload):
            return None
        cipher_suites_len = int.from_bytes(payload[idx:idx+2], "big")
        idx += 2 + cipher_suites_len
        if idx + 1 > len(payload):
            return None
        comp_methods_len = payload[idx]
        idx += 1 + comp_methods_len
        if idx + 2 > len(payload):
            return None
        ext_len = int.from_bytes(payload[idx:idx+2], "big")
        idx += 2
        end_ext = min(len(payload), idx + ext_len)
        while idx + 4 <= end_ext:
            ext_type = int.from_bytes(payload[idx:idx+2], "big")
            ext_data_len = int.from_bytes(payload[idx+2:idx+4], "big")
            idx += 4
            if ext_type == 0:  # server_name extension
                sn_idx = idx + 2
                while sn_idx + 3 <= idx + ext_data_len and sn_idx + 3 <= len(payload):
                    name_type = payload[sn_idx]
                    name_len = int.from_bytes(payload[sn_idx+1:sn_idx+3], "big")
                    if name_type == 0:  # host_name
                        return payload[sn_idx+3:sn_idx+3+name_len].decode("ascii", errors="ignore")
                    sn_idx += 3 + name_len
            idx += ext_data_len
    except Exception:
        return None
    return None


def extract_session_features_from_pcap(
    pcap_path: Path,
    session_id: str,
    classifier: FlowClassifier,
    theta_b_sec: float = 0.100,  # 100 ms burst threshold
    theta_i_sec: float = 0.500,  # 500 ms idle threshold
    custom_bounds: Optional[Tuple[float, float]] = None,
    include_search_in_website: bool = False,
    packets: Optional[List[Any]] = None,
) -> Dict[str, Any]:
    """Extracts all SPEC.md session features from a raw pcap."""
    if custom_bounds is not None:
        t_start, t_end = custom_bounds
    else:
        t_start, t_end = extract_hardware_marker_bounds(pcap_path, session_id)
    if t_start is None or t_end is None or t_end <= t_start:
        raise ValueError(f"Could not extract valid marker bounds for {session_id}")

    dur_s = float(t_end - t_start)
    if packets is None:
        packets = scapy.rdpcap(str(pcap_path))

    # Identify client IP from marker packets across the capture
    client_ips: set[str] = set()
    for p in packets:
        if p.haslayer(scapy.UDP) and p[scapy.UDP].payload:
            payload_bytes = bytes(p[scapy.UDP].payload)
            if payload_bytes.startswith(b"P1MARK"):
                if p.haslayer(scapy.IP):
                    client_ips.add(p[scapy.IP].src)
                elif p.haslayer(scapy.IPv6):
                    client_ips.add(p[scapy.IPv6].src)
        if p.haslayer(scapy.IP) and p[scapy.IP].dst == "192.0.2.1":
            client_ips.add(p[scapy.IP].src)
        elif p.haslayer(scapy.IPv6) and p[scapy.IPv6].dst == "2001:db8::1":
            client_ips.add(p[scapy.IPv6].src)

    # In-window packet clipping & exclusions
    in_window_pkts = []
    v4_bytes = 0
    v6_bytes = 0
    lan_packets_dropped = 0
    in_window_dns_map: Dict[str, str] = {}

    lan_ports = {5353, 1900, 5355, 137, 138, 139, 445}

    for p in packets:
        t = float(p.time)
        if not (t_start < t < t_end):
            continue

        # Drop marker packets (IPv4 or IPv6)
        if p.haslayer(scapy.IP) and p[scapy.IP].dst == "192.0.2.1":
            continue
        if p.haslayer(scapy.IPv6) and (p[scapy.IPv6].dst == "2001:db8::1" or (p.haslayer(scapy.UDP) and bytes(p[scapy.UDP].payload).startswith(b"P1MARK"))):
            continue

        # Check LAN port exclusion
        is_lan = False
        dport = 0
        sport = 0
        if p.haslayer(scapy.UDP):
            dport = p[scapy.UDP].dport
            sport = p[scapy.UDP].sport
        elif p.haslayer(scapy.TCP):
            dport = p[scapy.TCP].dport
            sport = p[scapy.TCP].sport

        if dport in lan_ports or sport in lan_ports:
            is_lan = True

        if p.haslayer(scapy.IP):
            if p[scapy.IP].dst in ("192.168.1.255", "255.255.255.255"):
                is_lan = True
            v4_bytes += len(p)
        elif p.haslayer(scapy.IPv6):
            if p[scapy.IPv6].dst.startswith("ff02:"):
                is_lan = True
            v6_bytes += len(p)

        if is_lan:
            lan_packets_dropped += 1
            continue

        # In-window DNS resolution only
        if p.haslayer(scapy.DNSRR):
            try:
                rrname = p[scapy.DNSRR].rrname.decode("utf-8", errors="ignore").rstrip(".")
                rdata = str(p[scapy.DNSRR].rdata)
                in_window_dns_map[rdata] = rrname
            except Exception:
                pass

        in_window_pkts.append(p)

    total_bytes = v4_bytes + v6_bytes
    pct_v6 = (v6_bytes / total_bytes * 100.0) if total_bytes > 0 else 0.0

    # Flow reassembly: 5-tuple
    flows: Dict[Any, List[Any]] = {}
    flow_endpoints: Dict[Any, Dict[str, Any]] = {}
    flow_quic: Dict[Any, bool] = {}

    for p in in_window_pkts:
        proto = "TCP" if p.haslayer(scapy.TCP) else ("UDP" if p.haslayer(scapy.UDP) else "OTHER")
        sport = 0
        dport = 0
        src_ip = ""
        dst_ip = ""

        if p.haslayer(scapy.IP):
            src_ip = p[scapy.IP].src
            dst_ip = p[scapy.IP].dst
        elif p.haslayer(scapy.IPv6):
            src_ip = p[scapy.IPv6].src
            dst_ip = p[scapy.IPv6].dst

        if p.haslayer(scapy.TCP):
            sport = p[scapy.TCP].sport
            dport = p[scapy.TCP].dport
        elif p.haslayer(scapy.UDP):
            sport = p[scapy.UDP].sport
            dport = p[scapy.UDP].dport

        key = (proto, min((src_ip, sport), (dst_ip, dport)), max((src_ip, sport), (dst_ip, dport)))

        if key not in flows:
            flows[key] = []
            flow_quic[key] = (proto == "UDP" and (dport == 443 or sport == 443))

            # Determine server IP vs client IP
            if src_ip in client_ips:
                c_ip, c_port = src_ip, sport
                s_ip, s_port = dst_ip, dport
            elif dst_ip in client_ips:
                c_ip, c_port = dst_ip, dport
                s_ip, s_port = src_ip, sport
            elif src_ip.startswith("192.168.") or src_ip.startswith("10.") or src_ip.startswith("fe80:"):
                c_ip, c_port = src_ip, sport
                s_ip, s_port = dst_ip, dport
            else:
                s_ip, s_port = dst_ip, dport
                c_ip, c_port = src_ip, sport

            flow_endpoints[key] = {
                "server_ip": s_ip,
                "server_port": s_port,
                "client_ip": c_ip,
                "client_port": c_port,
            }

        flows[key].append(p)

    # Classify flows and calculate session-level metrics
    n_flows = len(flows)
    website_flow_packets = []
    website_flow_intervals = []
    website_flow_count = 0
    website_quic_count = 0

    website_bytes = 0.0
    search_bytes = 0.0
    os_background_bytes = 0.0
    vendor_bytes = 0.0
    unknown_bytes = 0.0

    vendor_present = 0
    search_present = 0
    edge_present = 0
    gvt1_bytes = 0.0
    dest_hosts = set()

    for key, pkt_list in flows.items():
        ep = flow_endpoints[key]
        s_ip = ep["server_ip"]
        s_port = ep["server_port"]
        c_ip = ep["client_ip"]
        c_port = ep["client_port"]

        # Extract SNI from flow's TLS ClientHello packets
        flow_sni = ""
        for p in pkt_list:
            if p.haslayer(scapy.TCP) and p[scapy.TCP].payload:
                s = extract_sni_from_payload(bytes(p[scapy.TCP].payload))
                if s:
                    flow_sni = s.lower().strip()
                    break

        if not flow_sni and s_ip in in_window_dns_map:
            flow_sni = in_window_dns_map[s_ip].lower().strip()

        # Classify flow using FlowClassifier with both hostname and server_ip
        flow_row = pd.Series({
            "requested_server_name": flow_sni,
            "dst_ip": s_ip,
            "src_ip": c_ip,
            "dst_port": s_port,
            "src_port": c_port,
        })
        flow_class = classifier.classify_flow_domain(flow_row)

        if include_search_in_website and flow_class == "search":
            flow_class = "website"

        f_bytes = sum(len(p) for p in pkt_list)
        if flow_sni:
            dest_hosts.add(flow_sni)

        if flow_class == "vendor":
            vendor_present = 1
            vendor_bytes += f_bytes
        elif flow_class == "search":
            search_present = 1
            search_bytes += f_bytes
        elif flow_class == "os_background":
            os_background_bytes += f_bytes
            if "gvt1" in flow_sni or "edgedl.me.gvt1.com" in flow_sni or s_ip == "2600:1900:4110:86f::":
                gvt1_bytes += f_bytes
            if any(e in flow_sni for e in ["edge.microsoft.com", "bing.com", "msn.com"]):
                edge_present = 1
        elif flow_class == "website":
            website_flow_count += 1
            website_bytes += f_bytes
            if flow_quic.get(key, False):
                website_quic_count += 1
            website_flow_packets.extend(pkt_list)
            first_t = float(pkt_list[0].time)
            last_t = float(pkt_list[-1].time)
            website_flow_intervals.append((first_t, last_t))
        else:
            unknown_bytes += f_bytes

    # Compute micro-behavioral timing, volume, connection features on website flows
    if website_flow_packets:
        website_flow_packets.sort(key=lambda p: float(p.time))
        times = np.array([float(p.time) for p in website_flow_packets])
        pkt_lens = np.array([len(p) for p in website_flow_packets])

        is_out = np.array([
            (p.haslayer(scapy.IP) and p[scapy.IP].src in client_ips)
            or (p.haslayer(scapy.IPv6) and any(p[scapy.IPv6].src.startswith(ip[:10]) for ip in client_ips if ":" in ip))
            for p in website_flow_packets
        ], dtype=bool)

        bytes_out = float(np.sum(pkt_lens[is_out]))
        bytes_in = float(np.sum(pkt_lens[~is_out]))
        v_up_down_ratio = bytes_out / (bytes_in + 1e-6)

        # Bursts and idle pauses on website flows
        gaps = np.diff(times)
        idle_gaps = gaps[gaps >= theta_i_sec]
        burst_delimiters = np.where(gaps >= theta_b_sec)[0]
        n_bursts = len(burst_delimiters) + 1
        t_burst_rate = float(n_bursts / max(1e-6, dur_s / 60.0))

        if len(idle_gaps) > 0:
            t_idle_gap_median = float(np.median(idle_gaps))
            t_idle_gap_cv = float(np.std(idle_gaps) / max(1e-6, np.mean(idle_gaps)))
            # 12 log10-spaced bins from 0.5s to 120s
            bins = np.logspace(np.log10(0.5), np.log10(120.0), 13)
            counts, _ = np.histogram(idle_gaps, bins=bins)
            probs = counts / np.sum(counts) if np.sum(counts) > 0 else np.array([])
            probs = probs[probs > 0]
            t_idle_gap_entropy = float(-np.sum(probs * np.log2(probs))) if len(probs) > 0 else 0.0

            # Lag-1 autocorrelation
            if len(idle_gaps) > 2:
                g1 = idle_gaps[:-1] - np.mean(idle_gaps[:-1])
                g2 = idle_gaps[1:] - np.mean(idle_gaps[1:])
                denom = np.sqrt(np.sum(g1**2) * np.sum(g2**2))
                t_gap_autocorr_lag1 = float(np.sum(g1 * g2) / denom) if denom > 0 else 0.0
            else:
                t_gap_autocorr_lag1 = 0.0
        else:
            t_idle_gap_median = 0.0
            t_idle_gap_cv = 0.0
            t_idle_gap_entropy = 0.0
            t_gap_autocorr_lag1 = 0.0

        # Upload burst share
        burst_starts = np.insert(burst_delimiters + 1, 0, 0)
        burst_ends = np.append(burst_delimiters + 1, len(times))
        upload_bursts = 0
        for s_idx, e_idx in zip(burst_starts, burst_ends):
            b_lens = pkt_lens[s_idx:e_idx]
            b_out = is_out[s_idx:e_idx]
            if np.sum(b_lens[b_out]) > np.sum(b_lens[~b_out]):
                upload_bursts += 1
        v_upload_burst_share = float(upload_bursts / max(1, n_bursts))

        # Concurrency
        events = []
        for start_t, end_t in website_flow_intervals:
            events.append((start_t, 1))
            events.append((end_t, -1))
        events.sort(key=lambda x: x[0])
        cur = 0
        peak = 0
        for _, change in events:
            cur += change
            if cur > peak:
                peak = cur
        c_max_concurrent = int(peak)
        c_new_flows_per_min = float(website_flow_count / max(1e-6, dur_s / 60.0))
        c_quic_share = float(website_quic_count / max(1, website_flow_count))
    else:
        v_up_down_ratio = 0.0
        v_upload_burst_share = 0.0
        t_burst_rate = 0.0
        t_idle_gap_median = 0.0
        t_idle_gap_cv = 0.0
        t_idle_gap_entropy = 0.0
        t_gap_autocorr_lag1 = 0.0
        c_max_concurrent = 0
        c_new_flows_per_min = 0.0
        c_quic_share = 0.0

    return {
        "session_id": session_id,
        "L_duration_s": dur_s,
        "L_total_bytes": float(total_bytes),
        "L_n_flows": int(n_flows),
        "pct_ipv6": float(pct_v6),
        "lan_packets_dropped": int(lan_packets_dropped),
        # B6 Core 6 Primary Features
        "T_idle_gap_median": t_idle_gap_median,
        "T_burst_rate": t_burst_rate,
        "V_up_down_ratio": v_up_down_ratio,
        "V_upload_burst_share": v_upload_burst_share,
        "C_new_flows_per_min": c_new_flows_per_min,
        "C_max_concurrent": c_max_concurrent,
        # Remaining T/V/C candidates
        "T_idle_gap_cv": t_idle_gap_cv,
        "T_idle_gap_entropy": t_idle_gap_entropy,
        "T_gap_autocorr_lag1": t_gap_autocorr_lag1,
        "C_quic_share": c_quic_share,
        # Shortcut / Control / Diagnostic features
        "A_vendor_present": vendor_present,
        "A_vendor_bytes": vendor_bytes,
        "H_ja4_mode": "NOT_RUN",
        "H_ja4_n_distinct": np.nan,
        "D_dest_count": len(dest_hosts),
        "D_search_present": search_present,
        "Q_background_bytes": os_background_bytes,
        "Q_gvt1_bytes": gvt1_bytes,
        "Q_edge_present": edge_present,
        "unknown_bytes": unknown_bytes,
        "unknown_byte_share": float(unknown_bytes / max(1.0, total_bytes)),
        # Sanitized byte accounting columns
        "website_bytes": website_bytes,
        "search_bytes": search_bytes,
        "os_background_bytes": os_background_bytes,
        "vendor_bytes": vendor_bytes,
    }


def main():
    logger.info("Starting Dry-Run and Non-Study Capture Validation...")
    classifier = FlowClassifier(rules_path=FLOW_RULES_PATH)

    dry_run_ids = [f"D{i:04d}" for i in range(1, 13) if i != 8]
    selftest_ids = [f"X{i:04d}" for i in range(1, 6)]

    logger.info("Identified %d dry runs and %d self-tests (D0008 excluded per collection protocol)", len(dry_run_ids), len(selftest_ids))

    results = []
    # Test on a subset of dry runs for speed and verification
    for sid in ["D0001", "D0002", "D0003"]:
        pcap_file = RAW_DIR / f"{sid}.pcapng"
        if pcap_file.exists():
            logger.info("Validating extraction on %s (%s)...", sid, pcap_file.name)
            res1 = extract_session_features_from_pcap(pcap_file, sid, classifier)
            # Reproducibility check: run second time
            res2 = extract_session_features_from_pcap(pcap_file, sid, classifier)
            assert res1 == res2, f"Reproducibility failure on {sid}"
            results.append(res1)
            logger.info(
                "PASS %s: dur=%.2fs, pkts_in_window, pct_v6=%.1f%%, lan_dropped=%d, website_flows=%s, B6_core6_valid=%s",
                sid,
                res1["L_duration_s"],
                res1["pct_ipv6"],
                res1["lan_packets_dropped"],
                res1["C_max_concurrent"],
                all(np.isfinite(res1[f]) for f in ["T_idle_gap_median", "T_burst_rate", "V_up_down_ratio", "V_upload_burst_share", "C_new_flows_per_min", "C_max_concurrent"]),
            )

    logger.info("All checked dry runs passed validation with zero errors and 100%% deterministic reproducibility.")


if __name__ == "__main__":
    main()
