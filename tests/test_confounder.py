import pandas as pd
import numpy as np
from confoundr.schemas import CheckContext, CheckStatus
from confoundr.checks.confounder import ConfounderAuditCheck


def test_confounder_audit_pass():
    np.random.seed(42)
    # Independent variables
    df = pd.DataFrame({
        "feature_1": np.random.randn(100),
        "treatment": np.random.randint(0, 2, 100),
        "target": np.random.randn(100)
    })
    
    context = CheckContext(df=df, target_col="target", treatment_col="treatment")
    check = ConfounderAuditCheck()
    result = check.run(context)
    
    assert result.status == CheckStatus.PASS
    assert len(result.evidence.get("potential_confounders", [])) == 0


def test_confounder_audit_fail():
    np.random.seed(42)
    confounder = np.random.randn(100)
    # Confounder strongly influences both treatment and target
    treatment = (confounder > 0).astype(int)
    target = confounder * 2.0 + np.random.randn(100)
    
    df = pd.DataFrame({
        "safe_feature": np.random.randn(100),
        "hidden_confounder": confounder,
        "treatment": treatment,
        "target": target
    })
    
    context = CheckContext(df=df, target_col="target", treatment_col="treatment")
    check = ConfounderAuditCheck(correlation_threshold=0.3)
    result = check.run(context)
    
    assert result.status == CheckStatus.FAIL
    assert len(result.evidence["potential_confounders"]) == 1
    assert result.evidence["potential_confounders"][0]["feature"] == "hidden_confounder"
