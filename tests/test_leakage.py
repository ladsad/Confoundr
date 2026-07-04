import pandas as pd
import numpy as np
import pytest

from confoundr.schemas import CheckContext, CheckStatus
from confoundr.checks.leakage import TargetLeakageCheck


def test_target_leakage_detector_pass():
    # Create dataset with no leakage
    np.random.seed(42)
    df = pd.DataFrame({
        "feature_1": np.random.randn(100),
        "feature_2": np.random.randn(100),
        "target": np.random.randn(100) # completely independent
    })
    
    context = CheckContext(df=df, target_col="target")
    check = TargetLeakageCheck(correlation_threshold=0.8)
    result = check.run(context)
    
    assert result.status == CheckStatus.PASS
    assert result.is_passed() is True
    assert "No features found with correlation higher" in result.explanation


def test_target_leakage_detector_fail():
    # Create dataset with known leakage
    np.random.seed(42)
    target = np.random.randn(100)
    # feature_leaky is highly correlated with target
    feature_leaky = target + np.random.randn(100) * 0.1 
    
    df = pd.DataFrame({
        "feature_safe": np.random.randn(100),
        "feature_leaky": feature_leaky,
        "target": target
    })
    
    context = CheckContext(df=df, target_col="target")
    check = TargetLeakageCheck(correlation_threshold=0.8)
    result = check.run(context)
    
    assert result.status == CheckStatus.FAIL
    assert result.is_passed() is False
    assert "feature_leaky" in result.explanation
    assert len(result.evidence["leaky_features"]) == 1
    assert result.evidence["leaky_features"][0]["feature"] == "feature_leaky"


def test_target_leakage_detector_missing_target():
    df = pd.DataFrame({
        "feature_1": np.random.randn(100),
    })
    
    context = CheckContext(df=df, target_col="target")
    check = TargetLeakageCheck()
    result = check.run(context)
    
    assert result.status == CheckStatus.ERROR
    assert "not found" in result.explanation
