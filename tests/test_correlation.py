import pytest
import numpy as np
from app.ml import RootCauseAnalyzer


def test_correlation_analysis():
    analyzer = RootCauseAnalyzer(correlation_threshold=0.7)
    
    # Generate correlated metrics data
    x = np.linspace(0, 10, 50)
    primary = x + np.random.normal(0, 0.1, 50)
    correlated = 2 * x + np.random.normal(0, 0.2, 50)
    uncorrelated = np.sin(x) + np.random.normal(0, 0.5, 50)
    
    metrics_data = {
        "primary": list(primary),
        "correlated": list(correlated),
        "uncorrelated": list(uncorrelated),
    }
    
    correlated_names, confidence = analyzer.analyze("primary", metrics_data)
    
    assert "correlated" in correlated_names
    assert "uncorrelated" not in correlated_names
