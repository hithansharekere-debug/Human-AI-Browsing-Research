"""Verifies module importability across src package."""

import pytest


def test_import_pipeline_modules():
    import src.utils.logging_config
    import src.utils.paths
    import src.pipeline.dataset_verification
    import src.pipeline.window_extraction
    import src.pipeline.flow_extraction
    import src.pipeline.flow_classification
    import src.pipeline.feature_engineering
    import src.pipeline.statistics
    import src.pipeline.model_evaluation
    import src.pipeline.negative_controls
    import src.pipeline.sensitivity_analysis
    import src.pipeline.reproducibility
    import src.pipeline.runner

    assert True
