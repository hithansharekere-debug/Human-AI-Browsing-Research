"""Pipeline modules for the Human vs. AI Client Egress Analysis."""

from src.pipeline.dataset_verification import verify_dataset, save_verification_report
from src.pipeline.window_extraction import WindowExtractor, ObservationWindow
from src.pipeline.flow_extraction import FlowExtractor, FlowRecord
from src.pipeline.flow_classification import FlowClassifier
from src.pipeline.feature_engineering import FeatureExtractor
from src.pipeline.statistics import StatisticalEvaluator, HypothesisTestResult
from src.pipeline.model_evaluation import ModelEvaluator, ModelPerformanceMetrics
from src.pipeline.negative_controls import NegativeControlValidator, PermutationTestResult
from src.pipeline.sensitivity_analysis import SensitivityAnalyzer, WindowSensitivityResult
from src.pipeline.reproducibility import generate_reproducibility_manifest
from src.pipeline.runner import PipelineOrchestrator

__all__ = [
    "verify_dataset",
    "save_verification_report",
    "WindowExtractor",
    "ObservationWindow",
    "FlowExtractor",
    "FlowRecord",
    "FlowClassifier",
    "FeatureExtractor",
    "StatisticalEvaluator",
    "HypothesisTestResult",
    "ModelEvaluator",
    "ModelPerformanceMetrics",
    "NegativeControlValidator",
    "PermutationTestResult",
    "SensitivityAnalyzer",
    "WindowSensitivityResult",
    "generate_reproducibility_manifest",
    "PipelineOrchestrator",
]
