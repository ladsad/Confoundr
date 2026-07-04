import pandas as pd
import numpy as np

from ..base import BaseCheck
from ..schemas import CheckContext, CheckResult, CheckStatus, Severity


class ConfounderAuditCheck(BaseCheck):
    """
    Identifies potential measured confounders in the dataset.
    A variable is a potential confounder if it correlates significantly 
    with both the treatment variable and the target variable.
    """
    
    def __init__(self, correlation_threshold: float = 0.20):
        self.correlation_threshold = correlation_threshold
        
    @property
    def name(self) -> str:
        return "Confounder Audit"
        
    @property
    def default_severity(self) -> Severity:
        return Severity.MEDIUM

    def run(self, context: CheckContext) -> CheckResult:
        df = context.df
        target_col = context.target_col
        treatment_col = context.treatment_col
        
        if target_col not in df.columns:
            return self._create_result(CheckStatus.ERROR, f"Target column '{target_col}' not found.")
        if not treatment_col or treatment_col not in df.columns:
            return self._create_result(CheckStatus.ERROR, "Treatment column not specified or not found in dataframe.")
            
        features = context.feature_cols
        if not features:
            features = [c for c in df.columns if c not in [target_col, treatment_col, context.time_col]]
            
        numeric_df = df[features + [target_col, treatment_col]].select_dtypes(include=[np.number])
        if target_col not in numeric_df.columns or treatment_col not in numeric_df.columns:
            return self._create_result(
                CheckStatus.ERROR, 
                "Target and treatment columns must be numeric (or label encoded) for the v0.1 correlation scan."
            )
            
        potential_confounders = []
        correlations = {}
        
        for feature in features:
            if feature in numeric_df.columns:
                corr_target = numeric_df[feature].corr(numeric_df[target_col])
                corr_treatment = numeric_df[feature].corr(numeric_df[treatment_col])
                
                correlations[feature] = {
                    "corr_target": round(corr_target, 4) if pd.notna(corr_target) else None,
                    "corr_treatment": round(corr_treatment, 4) if pd.notna(corr_treatment) else None
                }
                
                if (pd.notna(corr_target) and abs(corr_target) > self.correlation_threshold and 
                    pd.notna(corr_treatment) and abs(corr_treatment) > self.correlation_threshold):
                    potential_confounders.append({
                        "feature": feature,
                        "corr_target": round(corr_target, 4),
                        "corr_treatment": round(corr_treatment, 4)
                    })
                    
        if potential_confounders:
            features_str = ", ".join([item['feature'] for item in potential_confounders])
            explanation = (f"Found {len(potential_confounders)} potential measured confounders "
                           f"(correlating > {self.correlation_threshold} with both target and treatment). "
                           f"Ensure these are controlled for in your causal model: {features_str}")
            return self._create_result(
                status=CheckStatus.FAIL,
                explanation=explanation,
                evidence={"potential_confounders": potential_confounders, "all_correlations": correlations}
            )
            
        return self._create_result(
            status=CheckStatus.PASS,
            explanation=f"No strong measured confounders found (threshold > {self.correlation_threshold}).",
            evidence={"all_correlations": correlations}
        )
