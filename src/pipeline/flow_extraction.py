"""Flow Extraction Module.

Role: Person B (Analysis Lead)
Reconstructs bidirectional network flows from raw pcap traces using the
nfstream framework or stream parsers, adhering to zero-payload inspection rules.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

logger = logging.getLogger("human_ai_egress.flow_extraction")


@dataclass(frozen=True)
class FlowRecord:
    """Standardized representation of a reconstructed bidirectional network flow."""
    flow_id: str
    session_id: str
    protocol: str
    src_port: int
    dst_port: int
    bidirectional_first_seen_ms: float
    bidirectional_last_seen_ms: float
    bidirectional_duration_ms: float
    bidirectional_packets: int
    bidirectional_bytes: int
    src2dst_packets: int
    src2dst_bytes: int
    dst2src_packets: int
    dst2src_bytes: int


class FlowExtractor:
    """Manages bidirectional flow reassembly and egress flow extraction."""

    def __init__(
        self,
        idle_timeout_seconds: float = 15.0,
        active_timeout_seconds: float = 120.0,
        accounting_mode: int = 0,
        strip_payload: bool = True,
    ) -> None:
        """Initializes FlowExtractor with protocol accounting rules.

        Args:
            idle_timeout_seconds: Inactivity timeout before terminating a flow.
            active_timeout_seconds: Maximum flow duration before forced expiration.
            accounting_mode: Accounting detail level for nfstream.
            strip_payload: Whether to exclude layer-7 payload strings.
        """
        self.idle_timeout = idle_timeout_seconds
        self.active_timeout = active_timeout_seconds
        self.accounting_mode = accounting_mode
        self.strip_payload = strip_payload

    def extract_flows_from_pcap(
        self,
        pcap_path: Path,
        session_id: str,
    ) -> pd.DataFrame:
        """Extracts bidirectional flows from an external PCAP file.

        Args:
            pcap_path: Path to external read-only PCAP file.
            session_id: Blinded session identifier.

        Returns:
            pandas DataFrame of extracted flows without raw IP addresses or payload.
        """
        if not pcap_path.exists():
            raise FileNotFoundError(f"PCAP file does not exist: {pcap_path}")

        logger.info("Extracting flows for session %s from external trace...", session_id)

        try:
            from nfstream import NFStreamer  # Deferred import to ensure clean environment loading
            streamer = NFStreamer(
                source=str(pcap_path),
                idle_timeout=int(self.idle_timeout),
                active_timeout=int(self.active_timeout),
                accounting_mode=self.accounting_mode,
            )

            flow_rows: List[Dict[str, Any]] = []
            for idx, flow in enumerate(streamer):
                flow_rows.append({
                    "flow_id": f"{session_id}_f{idx}",
                    "session_id": session_id,
                    "protocol": getattr(flow, "protocol", "UNKNOWN"),
                    "src_port": getattr(flow, "src_port", 0),
                    "dst_port": getattr(flow, "dst_port", 0),
                    "bidirectional_first_seen_ms": getattr(flow, "bidirectional_first_seen_ms", 0.0),
                    "bidirectional_last_seen_ms": getattr(flow, "bidirectional_last_seen_ms", 0.0),
                    "bidirectional_duration_ms": getattr(flow, "bidirectional_duration_ms", 0.0),
                    "bidirectional_packets": getattr(flow, "bidirectional_packets", 0),
                    "bidirectional_bytes": getattr(flow, "bidirectional_bytes", 0),
                    "src2dst_packets": getattr(flow, "src2dst_packets", 0),
                    "src2dst_bytes": getattr(flow, "src2dst_bytes", 0),
                    "dst2src_packets": getattr(flow, "dst2src_packets", 0),
                    "dst2src_bytes": getattr(flow, "dst2src_bytes", 0),
                })

            df = pd.DataFrame(flow_rows)
            logger.info("Successfully extracted %d flows for session %s.", len(df), session_id)
            return df

        except ImportError:
            logger.warning("nfstream is not installed. Returning empty schema DataFrame.")
            return self._empty_flow_dataframe()
        except Exception as exc:
            logger.exception("Error extracting flows from %s: %s", pcap_path, exc)
            raise

    @staticmethod
    def _empty_flow_dataframe() -> pd.DataFrame:
        """Returns empty DataFrame with standard flow schema."""
        return pd.DataFrame(
            columns=[
                "flow_id",
                "session_id",
                "protocol",
                "src_port",
                "dst_port",
                "bidirectional_first_seen_ms",
                "bidirectional_last_seen_ms",
                "bidirectional_duration_ms",
                "bidirectional_packets",
                "bidirectional_bytes",
                "src2dst_packets",
                "src2dst_bytes",
                "dst2src_packets",
                "dst2src_bytes",
            ]
        )
