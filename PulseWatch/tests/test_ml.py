import pytest
from datetime import datetime, timedelta
import numpy as np
from app.ml.anomaly_detector import AnomalyDetector, RootCauseAnalyzer
from app.ml.evaluator import MetricsEvaluator


class TestAnomalyDetector:
    def test_isolation_forest_detection(self):
        """Test IsolationForest anomaly detection"""
        detector = AnomalyDetector(method="isolation_forest", min_samples=20)
        
        # Normal data
        normal_values = [50 + np.random.normal(0, 5) for _ in range(100)]
        
        # Normal point
        result = detector.detect("test_metric", 52.0, normal_values[-99:])
        assert not result.is_anomaly
        
        # Anomalous point
        result = detector.detect("test_metric", 100.0, normal_values)
        assert result.is_anomaly
        assert 0 <= result.confidence_score <= 1

    def test_zscore_detection(self):
        """Test Z-Score anomaly detection"""
        detector = AnomalyDetector(method="z_score", z_score_threshold=2.0)
        
        # Normal data with mean=50, std=5
        normal_values = [50 + np.random.normal(0, 5) for _ in range(50)]
        
        # Normal point (within 2 std)
        result = detector.detect("test_metric", 52.0, normal_values)
        assert not result.is_anomaly
        
        # Anomalous point (>2 std away)
        result = detector.detect("test_metric", 100.0, normal_values)
        assert result.is_anomaly
        assert result.z_score is not None

    def test_insufficient_samples(self):
        """Test behavior with insufficient data"""
        detector = AnomalyDetector(min_samples=50)
        
        few_values = [50, 51, 52]
        result = detector.detect("test_metric", 100.0, few_values)
        
        assert not result.is_anomaly
        assert result.confidence_score == 0.0


class TestRootCauseAnalyzer:
    def test_correlation_detection(self):
        """Test root cause correlation"""
        analyzer = RootCauseAnalyzer(correlation_threshold=0.7)
        
        # Create correlated metrics
        primary = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        correlated = primary * 2 + np.random.normal(0, 0.1, 10)  # Highly correlated
        uncorrelated = np.random.normal(5, 2, 10)
        
        metric_values = {
            "primary_metric": primary.tolist(),
            "correlated_metric": correlated.tolist(),
            "uncorrelated_metric": uncorrelated.tolist(),
        }
        
        correlated_metrics, confidence = analyzer.analyze("primary_metric", metric_values)
        
        assert "correlated_metric" in correlated_metrics
        assert confidence > 0.7

    def test_no_correlation(self):
        """Test when no metrics are correlated"""
        analyzer = RootCauseAnalyzer(correlation_threshold=0.9)
        
        metric_values = {
            "metric1": [1, 2, 3, 4, 5],
            "metric2": [10, 20, 30, 40, 50],
        }
        
        correlated, confidence = analyzer.analyze("metric1", metric_values)
        assert len(correlated) == 0


class TestMetricsEvaluator:
    def test_precision_calculation(self):
        """Test precision metric"""
        evaluator = MetricsEvaluator()
        
        y_true = np.array([1, 0, 1, 0, 1, 0, 1, 0])
        y_pred = np.array([1, 0, 1, 1, 1, 0, 0, 0])
        
        metrics = evaluator.calculate_metrics(y_true, y_pred)
        
        # TP=3, FP=1, so precision=3/4=0.75
        assert metrics.precision == 0.75
        assert metrics.true_positives == 3
        assert metrics.false_positives == 1

    def test_recall_calculation(self):
        """Test recall metric"""
        evaluator = MetricsEvaluator()
        
        y_true = np.array([1, 0, 1, 0, 1, 0, 1, 0])
        y_pred = np.array([1, 0, 1, 1, 1, 0, 0, 0])
        
        metrics = evaluator.calculate_metrics(y_true, y_pred)
        
        # TP=3, FN=1, so recall=3/4=0.75
        assert metrics.recall == 0.75
        assert metrics.false_negatives == 1

    def test_f1_score_calculation(self):
        """Test F1 score"""
        evaluator = MetricsEvaluator()
        
        y_true = np.array([1, 1, 1, 1, 0, 0, 0, 0])
        y_pred = np.array([1, 1, 0, 0, 0, 0, 1, 1])
        
        metrics = evaluator.calculate_metrics(y_true, y_pred)
        
        # TP=2, FP=2, FN=2
        # Precision = 2/4 = 0.5, Recall = 2/4 = 0.5
        # F1 = 2 * (0.5 * 0.5) / (0.5 + 0.5) = 0.5
        assert metrics.f1_score == pytest.approx(0.5, abs=0.01)

    def test_perfect_detection(self):
        """Test perfect detection scenario"""
        evaluator = MetricsEvaluator()
        
        y_true = np.array([1, 1, 0, 0, 1, 0])
        y_pred = np.array([1, 1, 0, 0, 1, 0])
        
        metrics = evaluator.calculate_metrics(y_true, y_pred)
        
        assert metrics.precision == 1.0
        assert metrics.recall == 1.0
        assert metrics.f1_score == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
