import pandas as pd
import numpy as np
from confoundr.schemas import CheckContext, CheckStatus
from confoundr.checks.positivity import PositivityCheck


def test_positivity_check_pass():
    np.random.seed(42)
    # Randomized treatment (perfect overlap)
    df = pd.DataFrame({
        "feature_1": np.random.randn(200),
        "feature_2": np.random.randn(200),
        "treatment": np.random.randint(0, 2, 200),
        "target": np.random.randn(200)
    })
    
    context = CheckContext(df=df, target_col="target", treatment_col="treatment")
    check = PositivityCheck()
    result = check.run(context)
    
    assert result.status == CheckStatus.PASS
    assert result.evidence["overlap_ratio"] > 0.5


def test_positivity_check_fail():
    np.random.seed(42)
    # Treatment is perfectly separated by feature_1
    feature_1 = np.random.randn(200)
    treatment = (feature_1 > 0).astype(int)
    
    df = pd.DataFrame({
        "feature_1": feature_1,
        "treatment": treatment,
        "target": np.random.randn(200)
    })
    
    context = CheckContext(df=df, target_col="target", treatment_col="treatment")
    check = PositivityCheck(overlap_threshold=0.05)
    result = check.run(context)
    
    assert result.status == CheckStatus.FAIL
    assert result.evidence["overlap_ratio"] < 0.05
