"""Window Extraction Module.

Role: Person B (Analysis Lead)
Segments continuous session packet captures or flow series into discrete,
non-overlapping observation windows (e.g. 30-second intervals) for micro-behavioral
and temporal analysis.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
import pandas as pd

logger = logging.getLogger("human_ai_egress.window_extraction")


@dataclass(frozen=True)
class ObservationWindow:
    """Represents a discrete temporal window within a browsing session."""
    session_id: str
    window_index: int
    start_time_seconds: float
    end_time_seconds: float
    duration_seconds: float
    is_quiescent: bool = False


class WindowExtractor:
    """Extracts non-overlapping and sliding temporal observation windows."""

    def __init__(
        self,
        default_window_seconds: float = 30.0,
        step_seconds: Optional[float] = None,
        min_session_duration_seconds: float = 30.0,
    ) -> None:
        """Initializes the window extractor.

        Args:
            default_window_seconds: Duration of each observation window in seconds.
            step_seconds: Step size between window starts. Defaults to default_window_seconds
                          (non-overlapping).
            min_session_duration_seconds: Minimum duration threshold for valid session analysis.
        """
        self.window_duration = float(default_window_seconds)
        self.step_size = float(step_seconds if step_seconds is not None else default_window_seconds)
        self.min_duration = float(min_session_duration_seconds)

    def generate_window_bounds(
        self,
        session_id: str,
        total_duration_seconds: float,
    ) -> List[ObservationWindow]:
        """Calculates window boundary intervals for a session duration.

        Args:
            session_id: Blinded session identifier.
            total_duration_seconds: Total length of capture session in seconds.

        Returns:
            List of ObservationWindow dataclasses.
        """
        if total_duration_seconds < self.min_duration:
            logger.warning(
                "Session %s duration (%.1fs) below minimum threshold (%.1fs). Skipping windowing.",
                session_id,
                total_duration_seconds,
                self.min_duration,
            )
            return []

        windows: List[ObservationWindow] = []
        current_start = 0.0
        window_idx = 0

        while current_start + self.window_duration <= total_duration_seconds:
            current_end = current_start + self.window_duration
            windows.append(
                ObservationWindow(
                    session_id=session_id,
                    window_index=window_idx,
                    start_time_seconds=current_start,
                    end_time_seconds=current_end,
                    duration_seconds=self.window_duration,
                    is_quiescent=False,
                )
            )
            current_start += self.step_size
            window_idx += 1

        logger.debug(
            "Extracted %d windows (Tw=%.1fs, step=%.1fs) for session %s.",
            len(windows),
            self.window_duration,
            self.step_size,
            session_id,
        )
        return windows

    def slice_dataframe_by_window(
        self,
        df: pd.DataFrame,
        time_col: str,
        window: ObservationWindow,
    ) -> pd.DataFrame:
        """Slices a timestamped DataFrame to entries falling within the window.

        Args:
            df: Input DataFrame containing packet or event records.
            time_col: Name of relative timestamp column (in seconds).
            window: Target ObservationWindow.

        Returns:
            Sub-DataFrame filtered to window boundaries.
        """
        if df.empty or time_col not in df.columns:
            return pd.DataFrame(columns=df.columns)

        mask = (df[time_col] >= window.start_time_seconds) & (df[time_col] < window.end_time_seconds)
        return df.loc[mask].copy()


def extract_hardware_marker_bounds(
    pcap_path: Path,
    session_id: str,
    marker_ip: Optional[str] = None,
) -> Tuple[Optional[float], Optional[float]]:
    """Extracts hardware UDP marker boundary timestamps from a pcap trace.

    According to features/SPEC.md:
    - Start marker: UDP packet to marker_ip (IPv4 '192.0.2.1' or IPv6 '2001:db8::1')
      with payload starting with 'P1MARK START <session_id>'
    - End marker: UDP packet to marker_ip with payload starting with 'P1MARK END <session_id>'

    Args:
        pcap_path: Path to the raw .pcapng or .pcap trace.
        session_id: Session identifier (e.g. 'D0001', 'X0001', 'S0001').
        marker_ip: Hardware marker destination IP. If None, matches either
                   '192.0.2.1' or '2001:db8::1'.

    Returns:
        Tuple of (t_start, t_end) in epoch seconds, or None if marker missing.
    """
    try:
        import scapy.all as scapy
    except ImportError:
        logger.error("scapy is required for marker boundary extraction.")
        return None, None

    if not pcap_path.exists():
        logger.error("Trace file does not exist: %s", pcap_path)
        return None, None

    t_start: Optional[float] = None
    t_end: Optional[float] = None

    start_token = f"P1MARK START {session_id}".encode("ascii")
    end_token = f"P1MARK END {session_id}".encode("ascii")
    valid_marker_ips = {marker_ip} if marker_ip is not None else {"192.0.2.1", "2001:db8::1"}

    try:
        packets = scapy.rdpcap(str(pcap_path))
        for p in packets:
            if not p.haslayer(scapy.UDP):
                continue

            dst = None
            if p.haslayer(scapy.IP):
                dst = p[scapy.IP].dst
            elif p.haslayer(scapy.IPv6):
                dst = p[scapy.IPv6].dst

            payload = bytes(p[scapy.UDP].payload) if p[scapy.UDP].payload else b""
            is_marker_dest = dst in valid_marker_ips if dst else False

            if is_marker_dest or payload.startswith(b"P1MARK"):
                if payload.startswith(start_token):
                    t_start = float(p.time)
                elif payload.startswith(end_token):
                    t_end = float(p.time)
                    if t_start is not None:
                        break  # Found both markers
    except Exception as exc:
        logger.exception("Error extracting markers from %s: %s", pcap_path, exc)
        return None, None

    return t_start, t_end


def extract_client_ips_from_packets(
    packets: Sequence[Any],
    marker_ips: Sequence[str] = ("192.0.2.1", "2001:db8::1"),
) -> set[str]:
    """Dynamically extracts client IP addresses that emitted marker packets.

    Supports both IPv4 and IPv6 without hardcoded assumptions about client addresses.

    Args:
        packets: Iterable of Scapy packet objects.
        marker_ips: Recognized marker destination IP addresses.

    Returns:
        Set of client IP strings found in marker packet source headers.
    """
    try:
        import scapy.all as scapy
    except ImportError:
        return set()

    marker_set = set(marker_ips)
    client_ips: set[str] = set()

    for p in packets:
        if not p.haslayer(scapy.UDP):
            continue

        payload = bytes(p[scapy.UDP].payload) if p[scapy.UDP].payload else b""
        is_p1mark = payload.startswith(b"P1MARK")

        if p.haslayer(scapy.IP):
            if p[scapy.IP].dst in marker_set or is_p1mark:
                client_ips.add(str(p[scapy.IP].src))
        elif p.haslayer(scapy.IPv6):
            if p[scapy.IPv6].dst in marker_set or is_p1mark:
                client_ips.add(str(p[scapy.IPv6].src))

    return client_ips

