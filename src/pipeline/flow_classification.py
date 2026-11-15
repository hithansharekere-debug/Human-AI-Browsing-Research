"""Flow Classification & Filtering Module.

Role: Person B (Analysis Lead)
Filters out background operating system telemetry, local discovery protocols,
and classifies application-level web traffic in adherence with features/flow_rules.yaml.
"""

from __future__ import annotations

import fnmatch
import ipaddress
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import pandas as pd
import yaml

logger = logging.getLogger("human_ai_egress.flow_classification")


class FlowClassifier:
    """Classifies egress network flows and filters non-web background noise."""

    def __init__(self, rules_path: Optional[Path] = None) -> None:
        """Initializes FlowClassifier with flow rules configuration.

        Args:
            rules_path: Path to features/flow_rules.yaml.
        """
        self.rules: Dict[str, Any] = {}
        if rules_path and rules_path.exists():
            with open(rules_path, "r", encoding="utf-8") as f:
                self.rules = yaml.safe_load(f) or {}
            logger.info("Loaded flow rules from: %s", rules_path)
        else:
            logger.debug("No flow rules specified; using default rule set.")

        self._init_rule_indices()

    def _init_rule_indices(self) -> None:
        """Parses and indexes domain lists, IP sets, and port exclusions."""
        classification_cfg = self.rules.get("flow_classification", {})
        self.match_order: List[str] = classification_cfg.get(
            "match_order", ["vendor", "search", "os_background", "website"]
        )
        self.default_class: str = classification_cfg.get("default_class", "unknown")
        classes_cfg = classification_cfg.get("classes", {})

        # Domain pattern sets by class
        self.class_domain_patterns: Dict[str, List[str]] = {}
        self.class_ips: Dict[str, Set[str]] = {}

        for cls_name in self.match_order:
            cls_info = classes_cfg.get(cls_name, {})
            patterns = [d.lower() for d in cls_info.get("domains", [])]
            self.class_domain_patterns[cls_name] = patterns
            self.class_ips[cls_name] = set(cls_info.get("ip_addresses", []))

        # LAN exclusion rules
        lan_cfg = self.rules.get("lan_traffic_exclusions", {})
        self.lan_name_patterns: List[str] = [
            p.lower() for p in lan_cfg.get("excluded_name_patterns", [])
        ]
        self.lan_ip_literals: Set[str] = set(lan_cfg.get("excluded_ip_ranges", []))

        # Port-based LAN exclusions
        self.lan_ports: Set[int] = {5353, 1900, 5355, 137, 138, 139, 445, 67, 68, 123}
        for port_entry in lan_cfg.get("excluded_ports", []):
            if "port" in port_entry:
                self.lan_ports.add(int(port_entry["port"]))
            if "ports" in port_entry:
                for p in port_entry["ports"]:
                    self.lan_ports.add(int(p))

        # Unresolved domains (must remain unassigned/unknown)
        self.unresolved_domains: Set[str] = {
            item.get("name", "").lower()
            for item in self.rules.get("unresolved_domains", [])
            if "name" in item
        }

    def is_lan_traffic(self, row: pd.Series) -> bool:
        """Determines if a flow or packet is strictly LAN-local traffic.

        Covers mDNS (*.local, Android.local), NetBIOS, SSDP, LLMNR, WPAD,
        and local broadcast/multicast endpoints.
        """
        # 1. Check ports
        dst_port = int(row.get("dst_port", 0) or 0)
        src_port = int(row.get("src_port", 0) or 0)
        if dst_port in self.lan_ports or src_port in self.lan_ports:
            return True

        # 2. Check destination / source IP addresses
        dst_ip = str(row.get("dst_ip", "")).strip().lower()
        src_ip = str(row.get("src_ip", "")).strip().lower()
        for ip_val in [dst_ip, src_ip]:
            if not ip_val:
                continue
            if ip_val in self.lan_ip_literals:
                return True
            if ip_val.startswith("224.") or ip_val.startswith("127.") or ip_val == "::1":
                return True
            if ip_val.startswith("ff0") or ip_val.startswith("fe80"):
                return True

        # 3. Check hostname / SNI / DNS query name
        server_name = self._extract_hostname(row)
        if server_name:
            # Single-label or explicitly excluded LAN names
            if "." not in server_name or server_name in ("cal", "wpad", "wpad.domain.name"):
                return True
            for pat in self.lan_name_patterns:
                if fnmatch.fnmatch(server_name, pat):
                    return True

        return False

    def filter_lan_traffic(self, df_flows: pd.DataFrame) -> pd.DataFrame:
        """Filters out all LAN-only packets and flows before processing."""
        if df_flows.empty:
            return df_flows

        mask_lan = df_flows.apply(self.is_lan_traffic, axis=1)
        dropped_count = mask_lan.sum()
        if dropped_count > 0:
            logger.debug("Filtered %d LAN-only / local discovery flows.", dropped_count)

        return df_flows.loc[~mask_lan].copy()

    def filter_background_traffic(self, df_flows: pd.DataFrame) -> pd.DataFrame:
        """Legacy helper: filters LAN/background noise."""
        return self.filter_lan_traffic(df_flows)

    def classify_flow_domain(self, row: pd.Series) -> str:
        """Classifies a flow into vendor, search, os_background, website, or unknown.

        Strict matching precedence:
        1. LAN check -> if LAN, returns 'lan_excluded'
        2. vendor (A)
        3. search (D)
        4. os_background
        5. website
        Default: unknown
        """
        if self.is_lan_traffic(row):
            return "lan_excluded"

        hostname = self._extract_hostname(row)
        dst_ip = str(row.get("dst_ip", "")).strip().lower()

        # Check explicit unresolved domains first -> they must fall through to unknown
        if hostname:
            for unres in self.unresolved_domains:
                if hostname == unres or hostname.endswith("." + unres):
                    return "unknown"

        # Sequential evaluation by match order
        for cls_name in self.match_order:
            # Check IP match
            if dst_ip and dst_ip in self.class_ips.get(cls_name, set()):
                return cls_name

            # Check domain pattern match
            if hostname:
                patterns = self.class_domain_patterns.get(cls_name, [])
                for pat in patterns:
                    if self._match_domain_pattern(hostname, pat):
                        return cls_name

        return self.default_class

    def assign_traffic_category(self, row: pd.Series) -> str:
        """Legacy helper assigning broad transport protocol category."""
        dst_port = int(row.get("dst_port", 0) or 0)
        src_port = int(row.get("src_port", 0) or 0)
        protocol = str(row.get("protocol", "")).upper()

        target_port = dst_port if dst_port not in (0, None) else src_port

        if target_port in (443, 8443):
            if "UDP" in protocol:
                return "QUIC_HTTP3"
            return "HTTPS"
        elif target_port in (80, 8080):
            return "HTTP"
        elif target_port in (53, 853):
            return "DNS"
        else:
            return "OTHER_WEB"

    def classify_flows(self, df_flows: pd.DataFrame) -> pd.DataFrame:
        """Applies classification categories to all flows in DataFrame.

        Augments DataFrame with:
        - 'flow_class': 'vendor', 'search', 'os_background', 'website', 'unknown'
        - 'traffic_category': 'HTTPS', 'HTTP', 'QUIC_HTTP3', 'DNS', 'OTHER_WEB'
        """
        if df_flows.empty:
            res = df_flows.copy()
            res["flow_class"] = pd.Series(dtype=str)
            res["traffic_category"] = pd.Series(dtype=str)
            return res

        df = df_flows.copy()
        df["flow_class"] = df.apply(self.classify_flow_domain, axis=1)
        df["traffic_category"] = df.apply(self.assign_traffic_category, axis=1)
        return df

    def classify_domain(self, domain: str) -> str:
        """Helper to classify a domain name directly."""
        cls = self.classify_flow_domain(pd.Series({"requested_server_name": domain}))
        if cls == "lan_excluded":
            return "excluded"
        return cls

    @staticmethod
    def _extract_hostname(row: pd.Series) -> str:
        """Extracts SNI, requested_server_name, or DNS name from row."""
        for field in [
            "requested_server_name",
            "server_name",
            "sni",
            "dns_query_name",
            "hostname",
            "domain",
        ]:
            val = row.get(field, None)
            if val and isinstance(val, str) and val.strip():
                return val.strip().lower()
        return ""

    @staticmethod
    def _match_domain_pattern(hostname: str, pattern: str) -> bool:
        """Matches a domain against a pattern like '*.spotify.com' or 'spotify.com'."""
        hostname = hostname.lower()
        pattern = pattern.lower()

        if pattern.startswith("*."):
            root_domain = pattern[2:]
            return hostname == root_domain or hostname.endswith("." + root_domain)
        else:
            return hostname == pattern or hostname.endswith("." + pattern)
