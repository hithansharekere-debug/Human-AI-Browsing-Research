"""Tests temporal window extraction and synthetic feature calculation."""

import numpy as np
import pandas as pd
import pytest
from src.pipeline.window_extraction import WindowExtractor
from src.pipeline.feature_engineering import FeatureExtractor
from src.pipeline.flow_classification import FlowClassifier
from src.pipeline.statistics import compute_cliffs_delta, adjust_p_values_fdr_bh


def test_window_bounds_generation():
    extractor = WindowExtractor(default_window_seconds=30.0, step_seconds=30.0, min_session_duration_seconds=30.0)
    windows = extractor.generate_window_bounds(session_id="SESSION_H_001", total_duration_seconds=125.0)

    # 125 seconds / 30 seconds = 4 complete windows (0-30, 30-60, 60-90, 90-120)
    assert len(windows) == 4
    assert windows[0].start_time_seconds == 0.0
    assert windows[0].end_time_seconds == 30.0
    assert windows[3].start_time_seconds == 90.0
    assert windows[3].end_time_seconds == 120.0


def test_feature_extractor_quiescent():
    fe = FeatureExtractor()
    empty_df = pd.DataFrame()
    feats = fe.compute_window_features("SESSION_H_001", 0, empty_df, 30.0)

    assert feats["is_quiescent"] is True
    assert feats["flow_count"] == 0
    assert feats["bytes_out_total"] == 0.0
    assert feats["idle_ratio"] == 1.0


def test_feature_extractor_synthetic_flows():
    fe = FeatureExtractor(idle_threshold_seconds=1.0)
    synthetic_flows = pd.DataFrame([
        {
            "bidirectional_first_seen_ms": 1000.0,
            "bidirectional_last_seen_ms": 2500.0,
            "bidirectional_duration_ms": 1500.0,
            "src2dst_bytes": 1024,
            "dst2src_bytes": 8192,
            "src2dst_packets": 10,
            "dst2src_packets": 20,
            "dst_port": 443,
        },
        {
            "bidirectional_first_seen_ms": 4000.0,
            "bidirectional_last_seen_ms": 5000.0,
            "bidirectional_duration_ms": 1000.0,
            "src2dst_bytes": 2048,
            "dst2src_bytes": 16384,
            "src2dst_packets": 15,
            "dst2src_packets": 30,
            "dst_port": 443,
        },
    ])
    feats = fe.compute_window_features("SESSION_A_001", 0, synthetic_flows, 30.0)

    assert feats["flow_count"] == 2
    assert feats["bytes_out_total"] == 3072.0
    assert feats["bytes_in_total"] == 24576.0
    assert feats["pkt_count_out"] == 25
    assert feats["concurrency_peak"] >= 1
    assert feats["burst_count"] == 2  # Separated by > 1s idle gap


def test_cliffs_delta_and_fdr():
    x = np.array([10, 12, 14, 15, 18])
    y = np.array([1, 2, 3, 4, 5])
    delta = compute_cliffs_delta(x, y)
    assert delta == 1.0  # Completely separated

    raw_p = [0.01, 0.04, 0.03, 0.20]
    adj_p = adjust_p_values_fdr_bh(raw_p)
    assert len(adj_p) == 4
    assert all(0.0 <= p <= 1.0 for p in adj_p)
    assert adj_p[0] <= adj_p[3]
