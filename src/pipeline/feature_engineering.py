"""Feature Engineering Module.

Role: Person B (Analysis Lead)
Calculates volumetric, temporal, concurrency, and burstiness egress features
per observation window as formally defined in features/SPEC.md.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger("human_ai_egress.feature_engineering")


class FeatureExtractor:
    """Extracts egress statistical features according to features/SPEC.md."""

    def __init__(
        self,
        idle_threshold_seconds: float = 1.0,
        epsilon: float = 1e-6,
    ) -> None:
        """Initializes FeatureExtractor.

        Args:
            idle_threshold_seconds: Minimum silent gap in seconds to define an idle pause.
            epsilon: Small constant to avoid zero-division in ratios.
        """
        self.idle_threshold_sec = idle_threshold_seconds
        self.epsilon = epsilon

    def compute_window_features(
        self,
        session_id: str,
        window_index: int,
        df_window_flows: pd.DataFrame,
        window_duration_seconds: float = 30.0,
    ) -> Dict[str, Any]:
        """Extracts the full feature vector for a single temporal observation window.

        Args:
            session_id: Blinded session identifier.
            window_index: Sequential integer index of the window.
            df_window_flows: Flows active within this window.
            window_duration_seconds: Nominal duration of observation window.

        Returns:
            Dictionary mapping feature names (F01..F20) to scalar values.
        """
        features: Dict[str, Any] = {
            "session_id": session_id,
            "window_index": window_index,
            "window_duration_s": window_duration_seconds,
            "is_quiescent": df_window_flows.empty,
        }

        if df_window_flows.empty:
            # Zero-fill for completely quiescent windows
            features.update({
                "flow_count": 0,
                "bytes_out_total": 0.0,
                "bytes_in_total": 0.0,
                "bytes_ratio_out_in": 0.0,
                "pkt_count_out": 0,
                "pkt_count_in": 0,
                "iat_mean_out": 0.0,
                "iat_std_out": 0.0,
                "iat_skew_out": 0.0,
                "iat_p50_out": 0.0,
                "iat_p95_out": 0.0,
                "flow_duration_mean": 0.0,
                "flow_duration_p90": 0.0,
                "concurrency_peak": 0,
                "concurrency_mean": 0.0,
                "burst_count": 0,
                "burst_duration_mean": 0.0,
                "idle_duration_mean": window_duration_seconds * 1000.0,
                "idle_ratio": 1.0,
                "tls_sni_entropy": 0.0,
            })
            return features

        # F01 - F06: Volumetric Features
        flow_count = len(df_window_flows)
        bytes_out = float(df_window_flows.get("src2dst_bytes", pd.Series([0])).sum())
        bytes_in = float(df_window_flows.get("dst2src_bytes", pd.Series([0])).sum())
        pkt_out = int(df_window_flows.get("src2dst_packets", pd.Series([0])).sum())
        pkt_in = int(df_window_flows.get("dst2src_packets", pd.Series([0])).sum())
        bytes_ratio = bytes_out / (bytes_in + self.epsilon)

        features["flow_count"] = flow_count
        features["bytes_out_total"] = bytes_out
        features["bytes_in_total"] = bytes_in
        features["bytes_ratio_out_in"] = bytes_ratio
        features["pkt_count_out"] = pkt_out
        features["pkt_count_in"] = pkt_in

        # F07 - F11: Outbound Timing Inter-Arrivals (from flow timestamps if packet-level unavailable)
        first_seens = np.sort(df_window_flows["bidirectional_first_seen_ms"].to_numpy())
        if len(first_seens) > 1:
            iats = np.diff(first_seens)
            features["iat_mean_out"] = float(np.mean(iats))
            features["iat_std_out"] = float(np.std(iats))
            features["iat_skew_out"] = float(stats.skew(iats)) if len(iats) > 2 else 0.0
            features["iat_p50_out"] = float(np.percentile(iats, 50))
            features["iat_p95_out"] = float(np.percentile(iats, 95))
        else:
            features["iat_mean_out"] = 0.0
            features["iat_std_out"] = 0.0
            features["iat_skew_out"] = 0.0
            features["iat_p50_out"] = 0.0
            features["iat_p95_out"] = 0.0

        # F12 - F13: Flow Durations
        durations = df_window_flows.get("bidirectional_duration_ms", pd.Series([0])).to_numpy()
        features["flow_duration_mean"] = float(np.mean(durations)) if len(durations) > 0 else 0.0
        features["flow_duration_p90"] = float(np.percentile(durations, 90)) if len(durations) > 0 else 0.0

        # F14 - F15: Concurrency Peak and Mean
        concurrency_metrics = self._calculate_flow_concurrency(df_window_flows)
        features["concurrency_peak"] = concurrency_metrics["concurrency_peak"]
        features["concurrency_mean"] = concurrency_metrics["concurrency_mean"]

        # F16 - F19: Burst and Pause Dynamics
        burst_metrics = self._calculate_burst_metrics(first_seens, window_duration_seconds)
        features.update(burst_metrics)

        # F20: Entropy of flow protocol / port targets
        features["tls_sni_entropy"] = self._calculate_shannon_entropy(df_window_flows)

        return features

    def _calculate_flow_concurrency(self, df_flows: pd.DataFrame) -> Dict[str, Any]:
        """Calculates instantaneous peak and time-weighted mean active flows."""
        if df_flows.empty or "bidirectional_first_seen_ms" not in df_flows.columns:
            return {"concurrency_peak": 0, "concurrency_mean": 0.0}

        events: List[tuple[float, int]] = []
        for _, row in df_flows.iterrows():
            t_start = row.get("bidirectional_first_seen_ms", 0.0)
            t_end = row.get("bidirectional_last_seen_ms", t_start)
            events.append((t_start, 1))
            events.append((t_end, -1))

        # Sort events by time
        events.sort(key=lambda x: x[0])

        active = 0
        peak = 0
        active_counts: List[int] = []

        for _, change in events:
            active += change
            if active > peak:
                peak = active
            active_counts.append(max(0, active))

        mean_concurrency = float(np.mean(active_counts)) if active_counts else 0.0
        return {"concurrency_peak": peak, "concurrency_mean": mean_concurrency}

    def _calculate_burst_metrics(
        self,
        sorted_timestamps_ms: np.ndarray,
        window_duration_seconds: float,
    ) -> Dict[str, Any]:
        """Identifies bursts separated by idle periods > idle_threshold."""
        if len(sorted_timestamps_ms) <= 1:
            return {
                "burst_count": 1 if len(sorted_timestamps_ms) == 1 else 0,
                "burst_duration_mean": 0.0,
                "idle_duration_mean": 0.0,
                "idle_ratio": 0.0,
            }

        idle_threshold_ms = self.idle_threshold_sec * 1000.0
        gaps = np.diff(sorted_timestamps_ms)
        idle_gaps = gaps[gaps >= idle_threshold_ms]

        burst_count = len(idle_gaps) + 1
        idle_duration_mean = float(np.mean(idle_gaps)) if len(idle_gaps) > 0 else 0.0
        total_idle_ms = float(np.sum(idle_gaps)) if len(idle_gaps) > 0 else 0.0
        window_ms = window_duration_seconds * 1000.0
        idle_ratio = min(1.0, total_idle_ms / max(self.epsilon, window_ms))

        return {
            "burst_count": burst_count,
            "burst_duration_mean": float(window_ms - total_idle_ms) / max(1, burst_count),
            "idle_duration_mean": idle_duration_mean,
            "idle_ratio": idle_ratio,
        }

    def _calculate_shannon_entropy(self, df_flows: pd.DataFrame) -> float:
        """Computes Shannon entropy over port/protocol distribution."""
        if df_flows.empty or "dst_port" not in df_flows.columns:
            return 0.0
        counts = df_flows["dst_port"].value_counts().to_numpy()
        probs = counts / np.sum(counts)
        return float(stats.entropy(probs, base=2))
